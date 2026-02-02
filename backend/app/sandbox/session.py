from pathlib import Path
from typing import Dict, Any, List, Optional
import asyncio

from app.config.settings import settings
from app.config.logging import logger


class SandboxSession:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.modifications: Dict[str, str] = {}
        self.original_content: Dict[str, str] = {}

    async def read_file(self, relative_path: str) -> Optional[str]:
        full_path = self.repo_path / relative_path
        if full_path.exists():
            return full_path.read_text(encoding='utf-8')
        return None

    async def write_file(self, relative_path: str, content: str):
        full_path = self.repo_path / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        if full_path.exists():
            self.original_content[relative_path] = full_path.read_text(encoding='utf-8')

        full_path.write_text(content, encoding='utf-8')
        self.modifications[relative_path] = content

    async def edit_file(
        self,
        relative_path: str,
        old_content: str,
        new_content: str
    ) -> bool:
        current = await self.read_file(relative_path)
        if current and old_content in current:
            new_text = current.replace(old_content, new_content)
            await self.write_file(relative_path, new_text)
            return True
        return False

    async def delete_file(self, relative_path: str) -> bool:
        full_path = self.repo_path / relative_path
        if full_path.exists():
            self.original_content[relative_path] = full_path.read_text(encoding='utf-8')
            full_path.unlink()
            self.modifications.pop(relative_path, None)
            return True
        return False

    async def list_files(self, pattern: str = "*") -> List[str]:
        if pattern == "*":
            return [str(p.relative_to(self.repo_path)) for p in self.repo_path.rglob("*") if p.is_file()]
        return [str(p.relative_to(self.repo_path)) for p in self.repo_path.glob(pattern)]

    async def get_modifications(self) -> Dict[str, str]:
        return self.modifications

    async def rollback(self):
        for path, content in self.original_content.items():
            full_path = self.repo_path / path
            full_path.write_text(content, encoding='utf-8')
        self.modifications.clear()
        self.original_content.clear()

    async def commit(self) -> bool:
        import subprocess
        try:
            proc = await asyncio.create_subprocess_exec(
                "git", "add", "-A",
                cwd=str(self.repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()

            proc = await asyncio.create_subprocess_exec(
                "git", "status", "--porcelain",
                cwd=str(self.repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            return len(stdout) > 0
        except Exception as e:
            logger.error(f"Failed to commit changes: {e}")
            return False
