from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.session import get_db
from app.db.models import User, PullRequest, Task
from app.core.auth.jwt import get_current_user
from app.api.v1.schemas.pr import (
    PullRequestResponse, PullRequestDetailResponse, PRReviewRequest
)

router = APIRouter()


@router.get("", response_model=List[PullRequestResponse])
async def list_pull_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(PullRequest).where(
            (PullRequest.user_id == current_user.id) |
            (PullRequest.task.has(Task.user_id == current_user.id))
        ).order_by(PullRequest.created_at.desc())
    )
    prs = result.scalars().all()
    return prs


@router.get("/{pr_id}", response_model=PullRequestDetailResponse)
async def get_pull_request(
    pr_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(PullRequest).where(PullRequest.id == pr_id)
    )
    pr = result.scalar_one_or_none()

    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")

    task_result = await db.execute(
        select(Task).where(Task.id == pr.task_id)
    )
    task = task_result.scalar_one_or_none()

    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return PullRequestDetailResponse(
        **{
            k: v for k, v in pr.__dict__.items()
            if k not in ["_sa_instance_state"]
        }
    )


@router.post("/{pr_id}/review")
async def review_pull_request(
    pr_id: str,
    review: PRReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(PullRequest).where(PullRequest.id == pr_id)
    )
    pr = result.scalar_one_or_none()

    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")

    task_result = await db.execute(
        select(Task).where(Task.id == pr.task_id)
    )
    task = task_result.scalar_one_or_none()

    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if review.action == "approve":
        pr.human_review_status = "approved"
        pr.status = "approved"
        message = "Pull request approved"
    elif review.action == "request_changes":
        pr.human_review_status = "changes_requested"
        pr.status = "changes_requested"
        pr.human_review_comments = str(review.comments)
        message = "Changes requested"
    elif review.action == "reject":
        pr.human_review_status = "rejected"
        pr.status = "closed"
        message = "Pull request rejected"
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    await db.commit()

    return {"message": message, "status": pr.status}
