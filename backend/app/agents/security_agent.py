from app.agents.base import BaseAgent
from app.config.logging import logger
from app.services.secret_scanner import SecretScanner


class SecurityAgent(BaseAgent):
    name = "security_agent"

    def __init__(self):
        super().__init__()
        self.scanner = SecretScanner()

    async def execute(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        await self.log("Starting security scan", level="info")

        repo_path = task_context.get("repo_path")

        if not repo_path:
            await self.log("No repository path provided", level="warning")
            return {"status": "success", "passed": True, "findings": []}

        try:
            scan_result = await self.scanner.scan_code(repo_path)

            if scan_result.get("passed"):
                await self.log("Security scan passed - no secrets detected", level="info")
            else:
                await self.log(f"Security scan failed - {len(scan_result.get('findings', []))} issues found", level="warning")

            return scan_result

        except Exception as e:
            await self.log(f"Security scan failed: {e}", level="error")
            return {"status": "failed", "error": str(e), "passed": False}
