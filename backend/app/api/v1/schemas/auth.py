from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: str
    github_login: str
    github_avatar_url: Optional[str]
    email: Optional[str]
    name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class GitHubAuthUrlResponse(BaseModel):
    auth_url: str
    state: str
