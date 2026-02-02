from app.agents.base import BaseAgent
from app.config.settings import settings
from app.config.logging import logger
from app.services.llm_router import llm_router


class CodingAgent(BaseAgent):
    name = "coding_agent"

    async def execute(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        await self.log("Starting coding phase", level="info")

        task = task_context.get("task", {})
        prompt = task.get("prompt", "")
        context = task_context.get("context", {})

        changes = []

        try:
            generated_code = await llm_router.generate_code(prompt, str(context))

            changes.append({
                "file": "generated.py",
                "content": generated_code,
                "description": "Generated code based on task"
            })

            await self.log(f"Generated {len(changes)} file(s)", level="info")

        except Exception as e:
            await self.log(f"Coding failed: {e}", level="error")
            return {
                "status": "failed",
                "error": str(e),
                "changes": []
            }

        return {
            "status": "success",
            "changes": changes,
            "message": "Code generation complete"
        }
