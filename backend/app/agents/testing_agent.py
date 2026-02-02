from app.agents.base import BaseAgent
from app.config.settings import settings
from app.config.logging import logger
from app.sandbox.docker_runner import DockerSandbox
from app.services.test_detector import TestDetector


class TestingAgent(BaseAgent):
    name = "testing_agent"

    def __init__(self):
        super().__init__()
        self.docker = DockerSandbox()
        self.test_detector = TestDetector()

    async def execute(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        await self.log("Starting testing phase", level="info")

        repo_path = task_context.get("repo_path")
        changes = task_context.get("changes", [])

        test_results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "coverage": None,
            "details": []
        }

        if not repo_path:
            await self.log("No repository path provided", level="warning")
            return {"status": "success", "test_results": test_results}

        try:
            test_info = await self.test_detector.detect(repo_path)
            await self.log(f"Detected test framework: {test_info.get('framework', 'unknown')}", level="info")

            if test_info.get("run_command"):
                result = await self.docker.run_in_docker(
                    command=f"cd {repo_path} && {test_info['run_command']}",
                    timeout=settings.TEST_TIMEOUT
                )

                test_results["details"].append({
                    "command": test_info["run_command"],
                    "exit_code": result.get("exit_code", -1),
                    "output": result.get("stdout", "") + result.get("stderr", "")
                })

                test_results["tests_run"] = 1
                if result.get("exit_code", -1) == 0:
                    test_results["tests_passed"] = 1
                else:
                    test_results["tests_failed"] = 1

            await self.log(f"Tests completed: {test_results}", level="info")

        except Exception as e:
            await self.log(f"Testing failed: {e}", level="error")
            return {
                "status": "failed",
                "error": str(e),
                "test_results": test_results
            }

        return {
            "status": "success",
            "test_results": test_results,
            "passed": test_results["tests_failed"] == 0
        }
