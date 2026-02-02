import asyncio
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.session import get_db
from app.db.models import User, Task, Repository, TaskLog
from app.core.auth.jwt import get_current_user
from app.api.v1.schemas.task import (
    TaskCreate, TaskResponse, TaskDetailResponse, TaskWithLogsResponse,
    TaskStatus, TaskApprovalRequest
)
from app.orchestrator.state import create_initial_state
from app.orchestrator.graph import workflow
from app.websocket.manager import websocket_manager
from app.config.logging import logger

router = APIRouter()


async def run_workflow(task_id: str, user_id: str, repo_id: str):
    async with AsyncSession.begin() as db:
        task_result = await db.execute(select(Task).where(Task.id == task_id))
        task = task_result.scalar_one_or_none()

        repo_result = await db.execute(select(Repository).where(Repository.id == repo_id))
        repo = repo_result.scalar_one_or_none()

        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()

        if not all([task, repo, user]):
            return

        initial_state = create_initial_state(
            task_id=str(task.id),
            user_id=str(user.id),
            repository_id=str(repo.id),
            task={
                "id": str(task.id),
                "title": task.title,
                "description": task.description,
                "prompt": task.prompt
            },
            repository={
                "id": str(repo.id),
                "full_name": repo.full_name,
                "default_branch": repo.default_branch
            },
            user={
                "id": str(user.id),
                "github_id": user.github_id,
                "github_login": user.github_login,
                "github_access_token": user.github_access_token
            }
        )

        task.status = "running"
        await db.commit()

        try:
            final_state = await workflow.ainvoke(initial_state)

            task.status = final_state.get("status", "completed")
            task.progress = final_state.get("progress", 100)
            task.current_agent = final_state.get("current_agent")
            task.error_message = final_state.get("error_message")

            if task.status == "completed":
                task.completed_at = __import__('datetime').datetime.utcnow()

            await db.commit()

            await websocket_manager.send_status(task_id, {
                "status": task.status,
                "progress": task.progress,
                "current_agent": task.current_agent
            })

        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            task.status = "failed"
            task.error_message = str(e)
            await db.commit()

            await websocket_manager.send_status(task_id, {
                "status": "failed",
                "error": str(e)
            })


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo_result = await db.execute(
        select(Repository).where(
            Repository.id == task_data.repository_id,
            Repository.owner_id == current_user.id
        )
    )
    repo = repo_result.scalar_one_or_none()

    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    task = Task(
        user_id=current_user.id,
        repository_id=repo.id,
        title=task_data.title,
        description=task_data.description,
        prompt=task_data.prompt,
        priority=task_data.priority.value,
        status="queued"
    )

    db.add(task)
    await db.commit()
    await db.refresh(task)

    asyncio.create_task(run_workflow(str(task.id), str(current_user.id), str(repo.id)))

    return task


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    status_filter: TaskStatus = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Task).where(Task.user_id == current_user.id)
    if status_filter:
        query = query.where(Task.status == status_filter.value)

    result = await db.execute(query.order_by(Task.created_at.desc()))
    tasks = result.scalars().all()
    return tasks


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.user_id == current_user.id
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    repo_result = await db.execute(
        select(Repository).where(Repository.id == task.repository_id)
    )
    repo = repo_result.scalar_one_or_none()

    return TaskDetailResponse(
        **{
            k: v for k, v in task.__dict__.items()
            if k not in ["_sa_instance_state"]
        },
        repository=repo
    )


@router.get("/{task_id}/logs", response_model=List[TaskLog])
async def get_task_logs(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(TaskLog).where(
            TaskLog.task_id == task_id,
            Task.task_id.in_(select(Task.id).where(Task.user_id == current_user.id))
        ).order_by(TaskLog.created_at)
    )
    logs = result.scalars().all()
    return logs


@router.post("/{task_id}/approve")
async def approve_task(
    task_id: str,
    approval: TaskApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.user_id == current_user.id
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if not approval.approved:
        task.status = "paused"
        task.error_message = approval.comments or "Changes requested by human"
        await db.commit()
        return {"message": "Task paused", "status": task.status}

    task.status = "running"
    task.progress = 95
    await db.commit()

    await websocket_manager.send_approval_request(task_id)

    return {"message": "Task approved, PR creation initiated", "status": task.status}
