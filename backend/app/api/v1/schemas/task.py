from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TaskCreate(BaseModel):
    repository_id: str
    title: str
    description: Optional[str] = None
    prompt: str = Field(..., description="The coding task description in natural language")
    priority: TaskPriority = TaskPriority.NORMAL


class TaskResponse(BaseModel):
    id: str
    user_id: str
    repository_id: str
    title: str
    description: Optional[str]
    prompt: str
    status: TaskStatus
    priority: TaskPriority
    current_agent: Optional[str]
    progress: int
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class TaskDetailResponse(TaskResponse):
    repository: RepositoryResponse


class TaskWithLogsResponse(TaskResponse):
    logs: List["TaskLogResponse"] = []


class TaskLogResponse(BaseModel):
    id: str
    level: str
    agent: Optional[str]
    message: str
    metadata: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class TaskApprovalRequest(BaseModel):
    approved: bool
    comments: Optional[str] = None


class TaskApprovalResponse(BaseModel):
    task_id: str
    status: str
    message: str
