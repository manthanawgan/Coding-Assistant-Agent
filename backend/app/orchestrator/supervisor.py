from app.agents.base import BaseAgent
from app.agents.research_agent import ResearchAgent
from app.agents.context_agent import ContextAgent
from app.agents.coding_agent import CodingAgent
from app.agents.testing_agent import TestingAgent
from app.agents.github_agent import GitHubAgent
from app.services.security_scanner import SecurityScanner
from app.config.settings import settings
from app.config.logging import logger


class SupervisorAgent(BaseAgent):
    name = "supervisor"

    def __init__(self):
        super().__init__()
        self.agents = {
            "research": ResearchAgent(),
            "context": ContextAgent(),
            "coding": CodingAgent(),
            "testing": TestingAgent(),
            "github": GitHubAgent()
        }
        self.security_scanner = SecurityScanner()

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        await self.log("Supervisor starting task execution", level="info")

        task_context = {
            "task": state.get("task", {}),
            "repository": state.get("repository", {}),
            "user": state.get("user", {}),
            "repo_path": state.get("repo_path")
        }

        await self.run_agent("research", state, task_context)
        await self.run_agent("context", state, task_context)

        state["progress"] = 50
        await self.run_agent("coding", state, task_context)

        state["progress"] = 70

        test_result = await self.run_agent("testing", state, task_context)
        state["test_results"] = test_result

        if test_result.get("status") == "failed" or not test_result.get("passed", True):
            state["iteration_count"] = state.get("iteration_count", 0) + 1
            if state["iteration_count"] < settings.MAX_ITERATIONS:
                await self.log("Tests failed, retrying coding", level="warning")
                await self.run_agent("coding", state, task_context)
            else:
                state["status"] = "failed"
                state["error_message"] = "Max iterations reached, tests still failing"
                return state

        state["progress"] = 85

        security_result = await self.security_scanner.scan_code(state.get("repo_path"))
        state["security_results"] = security_result

        if not security_result.get("passed"):
            state["status"] = "failed"
            state["error_message"] = "Security scan failed - secrets detected"
            return state

        state["human_approval_required"] = True
        state["progress"] = 95

        await self.log("Task ready for human approval", level="info")

        return state

    async def run_agent(self, agent_name: str, state: Dict, context: Dict) -> Dict:
        agent = self.agents.get(agent_name)
        if not agent:
            await self.log(f"Agent {agent_name} not found", level="error")
            return {"status": "failed", "error": "Agent not found"}

        state["current_agent"] = agent_name
        await self.log(f"Running agent: {agent_name}", level="info")

        try:
            result = await agent.execute(context)
            if result.get("status") == "success":
                await self.log(f"Agent {agent_name} completed successfully", level="info")
            else:
                await self.log(f"Agent {agent_name} failed: {result.get('error')}", level="error")
            return result
        except Exception as e:
            await self.log(f"Agent {agent_name} exception: {e}", level="error")
            return {"status": "failed", "error": str(e)}

    async def create_pr(self, state: Dict[str, Any]) -> Dict[str, Any]:
        if not state.get("human_approved"):
            return {"status": "failed", "error": "Human approval required"}

        github_context = {
            "action": "create_pr",
            "user": state.get("user", {}),
            "repository": state.get("repository", {}),
            "changes": state.get("changes", []),
            "task": state.get("task", {})
        }

        return await self.agents["github"].execute(github_context)

    def get_agents_status(self) -> Dict[str, bool]:
        return {name: agent is not None for name, agent in self.agents.items()}
