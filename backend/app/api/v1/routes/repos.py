from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.session import get_db
from app.db.models import User, Repository
from app.core.auth.jwt import get_current_user
from app.api.v1.schemas.repo import RepositoryResponse, GitHubRepositoryResponse
from app.services.github_service import create_github_service

router = APIRouter()


@router.get("", response_model=List[RepositoryResponse])
async def list_repositories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Repository).where(Repository.owner_id == current_user.id)
    )
    repos = result.scalars().all()
    return repos


@router.get("/github", response_model=List[GitHubRepositoryResponse])
async def fetch_github_repos(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.github_access_token:
        raise HTTPException(status_code=400, detail="No GitHub access token")

    github = create_github_service(current_user.github_access_token)
    repos = await github.get_user_repos()

    github_repos = []
    for repo in repos:
        github_repos.append(GitHubRepositoryResponse(
            id=repo["id"],
            name=repo["name"],
            full_name=repo["full_name"],
            description=repo.get("description"),
            language=repo.get("language"),
            private=repo["private"],
            default_branch=repo.get("default_branch", "main"),
            html_url=repo["html_url"]
        ))

    return github_repos


@router.post("/github/{repo_full_name}/sync")
async def sync_repository(
    repo_full_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.github_access_token:
        raise HTTPException(status_code=400, detail="No GitHub access token")

    github = create_github_service(current_user.github_access_token)

    try:
        owner, repo_name = repo_full_name.split("/")
        repo_info = await github.get_repo(owner, repo_name)

        result = await db.execute(
            select(Repository).where(
                Repository.owner_id == current_user.id,
                Repository.github_repo_id == repo_info["id"]
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.language = repo_info.get("language")
            existing.description = repo_info.get("description")
            await db.commit()
            return {"message": "Repository updated", "repository": existing}
        else:
            repo = Repository(
                owner_id=current_user.id,
                github_repo_id=repo_info["id"],
                name=repo_info["name"],
                full_name=repo_info["full_name"],
                description=repo_info.get("description"),
                language=repo_info.get("language"),
                private=repo_info["private"],
                clone_url=repo_info["clone_url"],
                default_branch=repo_info.get("default_branch", "main")
            )
            db.add(repo)
            await db.commit()
            await db.refresh(repo)
            return {"message": "Repository synced", "repository": repo}

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{repo_id}", response_model=RepositoryResponse)
async def get_repository(
    repo_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Repository).where(
            Repository.id == repo_id,
            Repository.owner_id == current_user.id
        )
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo
