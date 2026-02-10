import docker
import asyncio
from typing import Dict, Optional
from app.config import get_settings

class CodeExecutor: #for executing code in docker container (still workin on it)
    def __init__(self):
        self.settings = get_settings()
        if self.settings.USE_DOCKER:
            self.client = docker.from_env()
    
    async def execute_python(self, code: str, timeout: Optional[int] = None) -> Dict:
        timeout = timeout or self.settings.EXECUTION_TIMEOUT
        
        if self.settings.USE_DOCKER:
            return await self._execute_in_docker(code, timeout)
        else:
            return await self._execute_local(code, timeout)
    
    async def _execute_in_docker(self, code: str, timeout: int) -> Dict:
        try:
            container = self.client.containers.run(
                "python:3.11-slim",
                f"python -c '{code}'",
                remove=True,
                detach=True,
                mem_limit="128m",
                network_disabled=True  #security: no network access
            )
            
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(container.wait, timeout=timeout),
                    timeout=timeout
                )
                
                logs = container.logs().decode('utf-8')
                
                return {
                    "success": result["StatusCode"] == 0,
                    "output": logs,
                    "exit_code": result["StatusCode"],
                    "error": None if result["StatusCode"] == 0 else logs
                }
                
            except asyncio.TimeoutError:
                container.stop()
                return {
                    "success": False,
                    "output": "",
                    "error": f"Execution timeout after {timeout}s"
                }
                
        except docker.errors.ContainerError as e:
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Execution failed: {str(e)}"
            }
    
    async def _execute_local(self, code: str, timeout: int) -> Dict:  #used claude here...for testing purpose
        """Execute code locally (NOT RECOMMENDED for production)"""
        # WARNING: Only use this for development with trusted code
        try:
            process = await asyncio.create_subprocess_exec(
                'python', '-c', code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            return {
                "success": process.returncode == 0,
                "output": stdout.decode(),
                "exit_code": process.returncode,
                "error": stderr.decode() if process.returncode != 0 else None
            }
            
        except asyncio.TimeoutError:
            process.kill()
            return {
                "success": False,
                "output": "",
                "error": f"Execution timeout after {timeout}s"
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }