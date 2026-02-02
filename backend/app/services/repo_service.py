import os
import shutil
import asyncio
import httpx
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.config.settings import settings
from app.config.logging import logger


class RepoService:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.cache_dir = Path(settings.REPO_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_repo_cache_path(self, repo_full_name: str) -> Path:
        safe_name = repo_full_name.replace("/", "_")
        return self.cache_dir / safe_name

    async def clone_or_pull(self, repo_full_name: str, branch: str = "main") -> Path:
        cache_path = self.get_repo_cache_path(repo_full_name)
        github = __import__('app.services.github_service', fromlist=['GitHubService']).GitHubService(self.access_token)

        if cache_path.exists():
            shutil.rmtree(cache_path)

        cache_path.mkdir(parents=True, exist_ok=True)

        import subprocess
        repo_url = f"https://x-access-token:{self.access_token}@github.com/{repo_full_name}.git"
        proc = await asyncio.create_subprocess_exec(
            "git", "clone", "-b", branch, repo_url, str(cache_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise Exception(f"Git clone failed: {stderr.decode()}")

        return cache_path

    async def list_files(self, repo_full_name: str, path: str = ".") -> List[Dict[str, Any]]:
        cache_path = self.get_repo_cache_path(repo_full_name)
        if not cache_path.exists():
            cache_path = await self.clone_or_pull(repo_full_name)

        full_path = cache_path / path
        if not full_path.exists():
            return []

        files = []
        for item in full_path.iterdir():
            stat = item.stat()
            files.append({
                "name": item.name,
                "path": str(item.relative_to(cache_path)),
                "is_dir": item.is_dir(),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        return files

    async def read_file(self, repo_full_name: str, file_path: str) -> Optional[str]:
        cache_path = self.get_repo_cache_path(repo_full_name)
        if not cache_path.exists():
            cache_path = await self.clone_or_pull(repo_full_name)

        full_path = cache_path / file_path
        if not full_path.exists() or not full_path.is_file():
            return None

        return full_path.read_text(encoding='utf-8')

    async def detect_language(self, repo_full_name: str) -> Optional[str]:
        cache_path = self.get_repo_cache_path(repo_full_name)
        if not cache_path.exists():
            cache_path = await self.clone_or_pull(repo_full_name)

        extensions = {}
        for item in cache_path.rglob("*"):
            if item.is_file() and not item.name.startswith("."):
                ext = item.suffix.lower()
                if ext:
                    extensions[ext] = extensions.get(ext, 0) + 1

        lang_map = {
            ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
            ".go": "Go", ".java": "Java", ".rs": "Rust", ".rb": "Ruby",
            ".php": "PHP", ".cpp": "C++", ".c": "C", ".h": "C"
        }

        if extensions:
            top_ext = max(extensions, key=extensions.get)
            return lang_map.get(top_ext, "Unknown")

        return "Unknown"

    async def detect_test_framework(self, repo_full_name: str) -> Optional[str]:
        cache_path = self.get_repo_cache_path(repo_full_name)
        if not cache_path.exists():
            cache_path = await self.clone_or_pull(repo_full_name)

        test_indicators = {
            "pytest": ["pytest.ini", "pyproject.toml", "setup.py"],
            "jest": ["package.json", "jest.config.js"],
            "mocha": ["package.json"],
            "go_test": ["*_test.go"],
            "junit": ["pom.xml", "build.gradle"],
        }

        for framework, indicators in test_indicators.items():
            for indicator in indicators:
                if "*" in indicator:
                    matches = list(cache_path.glob(indicator))
                    if matches:
                        return framework
                else:
                    if (cache_path / indicator).exists():
                        return framework

        return None

    async def get_file_diff(self, repo_full_name: str, base_branch: str = "main") -> Dict[str, Any]:
        import subprocess
        cache_path = self.get_repo_cache_path(repo_full_name)

        try:
            proc = await asyncio.create_subprocess_exec(
                "git", "diff", "--stat", base_branch,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cache_path)
            )
            stdout, _ = await proc.communicate()

            result = {
                "files_changed": 0,
                "additions": 0,
                "deletions": 0,
                "files": []
            }

            if proc.returncode == 0:
                for line in stdout.decode().strip().split("\n"):
                    if line:
                        parts = line.split()
                        if len(parts) >= 4:
                            result["files_changed"] += 1
                            result["additions"] += int(parts[1].replace('+', '0'))
                            result["deletions"] += int(parts[2].replace('-', '0'))

            return result
        except Exception as e:
            logger.error(f"Failed to get git diff: {e}")
            return {"files_changed": 0, "additions": 0, "deletions": 0, "files": []}
