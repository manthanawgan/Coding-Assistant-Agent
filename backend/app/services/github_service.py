import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.config.settings import settings
from app.config.logging import logger


class GitHubService:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def get_user_repos(self, page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user/repos",
                headers=self.headers,
                params={"page": page, "per_page": per_page, "sort": "updated"}
            )
            response.raise_for_status()
            return response.json()

    async def get_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def create_branch(self, owner: str, repo: str, branch_name: str, from_sha: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            ref = f"refs/heads/{branch_name}"
            response = await client.post(
                f"https://api.github.com/repos/{owner}/{repo}/git/refs",
                headers=self.headers,
                json={
                    "ref": ref,
                    "sha": from_sha
                }
            )
            response.raise_for_status()
            return response.json()

    async def get_file_content(self, owner: str, repo: str, path: str, branch: str = "main") -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
                headers=self.headers,
                params={"ref": branch}
            )
            response.raise_for_status()
            return response.json()

    async def create_or_update_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: str,
        sha: Optional[str] = None
    ) -> Dict[str, Any]:
        import base64
        async with httpx.AsyncClient() as client:
            payload = {
                "message": message,
                "content": base64.b64encode(content.encode()).decode(),
                "branch": branch,
            }
            if sha:
                payload["sha"] = sha
            response = await client.put(
                f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str = "main"
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.github.com/repos/{owner}/{repo}/pulls",
                headers=self.headers,
                json={
                    "title": title,
                    "body": body,
                    "head": head,
                    "base": base
                }
            )
            response.raise_for_status()
            return response.json()

    async def get_default_branch(self, owner: str, repo: str) -> str:
        repo_info = await self.get_repo(owner, repo)
        return repo_info.get("default_branch", "main")

    async def get_branch_ref(self, owner: str, repo: str, branch: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{branch}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_pull_request(self, owner: str, repo: str, pull_number: int) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_pull_request_files(self, owner: str, repo: str, pull_number: int) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/files",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()


def create_github_service(access_token: str) -> GitHubService:
    return GitHubService(access_token)
