from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class PRStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    MERGED = "merged"
    CLOSED = "closed"


class PRReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class PullRequestResponse(BaseModel):
    id: str
    task_id: str
    github_number: Optional[int]
    title: Optional[str]
    description: Optional[str]
    branch_name: str
    status: PRStatus
    human_review_status: PRReviewStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PullRequestDetailResponse(PullRequestResponse):
    repository_id: str
    user_id: Optional[str]
    github_pr_id: Optional[int]
    diff_summary: Optional[Dict[str, Any]]
    test_results: Optional[Dict[str, Any]]
    security_scan_results: Optional[Dict[str, Any]]
    human_review_comments: Optional[str]


class PRReviewRequest(BaseModel):
    action: str
    comments: Optional[List[Dict[str, str]]] = None


class DiffFile(BaseModel):
    filename: str
    status: str
    additions: int
    deletions: int
    patch: Optional[str]


class DiffSummary(BaseModel):
    files_changed: int
    additions: int
    deletions: int
    files: List[DiffFile]
