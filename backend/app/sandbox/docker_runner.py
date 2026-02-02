import docker
from typing import Dict, Any, Optional, List
from pathlib import Path
import asyncio
import uuid

from app.config.settings import settings
from app.config.logging import logger


class DockerSandbox:
    def __init__(self):
        self.client = docker.from_env()
        self.container_prefix = "coding-assistant"

    async def create_container(
        self,
        image: str = "python:3.11-slim",
        workdir: str = "/app",
        network_disabled: bool = True
    ) -> str:
        container_name = f"{self.container_prefix}-{uuid.uuid4().hex[:8]}"
        try:
            container = self.client.containers.create(
                image=image,
                name=container_name,
                working_dir=workdir,
                detach=True,
                tty=True,
                volumes={
                    str(Path.cwd() / "repo_cache"): {"bind": "/repo_cache", "mode": "ro"}
                },
                command="sleep infinity",
                network_disabled=network_disabled
            )
            return container.id
        except Exception as e:
            logger.error(f"Failed to create container: {e}")
            raise

    async def exec_command(
        self,
        container_id: str,
        command: str,
        timeout: int = 600
    ) -> Dict[str, Any]:
        try:
            container = self.client.containers.get(container_id)
            exec_result = container.exec_run(
                cmd=command,
                workdir="/repo_cache",
                stdout=True,
                stderr=True,
                demux=True,
                timeout=timeout
            )
            return {
                "exit_code": exec_result.exit_code,
                "stdout": exec_result.output[0].decode() if exec_result.output[0] else "",
                "stderr": exec_result.output[1].decode() if exec_result.output[1] else ""
            }
        except Exception as e:
            logger.error(f"Failed to exec command: {e}")
            return {"exit_code": -1, "stdout": "", "stderr": str(e)}

    async def run_tests(
        self,
        container_id: str,
        test_command: str
    ) -> Dict[str, Any]:
        return await self.exec_command(container_id, test_command)

    async def cleanup(self, container_id: str):
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=5)
            container.remove(force=True)
            logger.info(f"Cleaned up container {container_id}")
        except Exception as e:
            logger.error(f"Failed to cleanup container: {e}")

    async def run_in_docker(
        self,
        command: str,
        image: str = "python:3.11-slim",
        timeout: int = 600
    ) -> Dict[str, Any]:
        container_id = None
        try:
            container_id = await self.create_container(image)
            result = await self.exec_command(container_id, command, timeout)
            return result
        finally:
            if container_id:
                await self.cleanup(container_id)
