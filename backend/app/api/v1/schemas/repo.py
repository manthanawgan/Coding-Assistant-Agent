from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class RepositoryResponse(BaseModel):
    id: str
    name: str
    full_name: str
    description: Optional[str]
    language: Optional[str]
    private: bool
    default_branch: str
    created_at: datetime

    class Config:
        from_attributes = True


class RepositoryDetailResponse(RepositoryResponse):
    owner_id: str
    github_repo_id: int
    clone_url: Optional[str]


class GitHubRepositoryResponse(BaseModel):
    id: int
    name: str
    full_name: str
    description: Optional[str]
    language: Optional[str]
    private: bool
    default_branch: str
    html_url: str
