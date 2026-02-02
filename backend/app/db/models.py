from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    github_id = Column(Integer, unique=True, nullable=False, index=True)
    github_login = Column(String(255), nullable=False)
    github_avatar_url = Column(Text)
    github_access_token = Column(Text)
    email = Column(String(255))
    name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    repositories = relationship("Repository", back_populates="owner", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    pull_requests = relationship("PullRequest", back_populates="user", cascade="all, delete-orphan")


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    github_repo_id = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    full_name = Column(String(512), nullable=False)
    description = Column(Text)
    language = Column(String(100))
    private = Column(Boolean, default=False)
    clone_url = Column(Text)
    default_branch = Column(String(100), default="main")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="repositories")
    tasks = relationship("Task", back_populates="repository", cascade="all, delete-orphan")
    pull_requests = relationship("PullRequest", back_populates="repository", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"))
    title = Column(String(500), nullable=False)
    description = Column(Text)
    prompt = Column(Text, nullable=False)
    status = Column(String(50), default="queued")
    priority = Column(String(20), default="normal")
    current_agent = Column(String(100))
    progress = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    user = relationship("User", back_populates="tasks")
    repository = relationship("Repository", back_populates="tasks")
    checkpoints = relationship("TaskCheckpoint", back_populates="task", cascade="all, delete-orphan")
    logs = relationship("TaskLog", back_populates="task", cascade="all, delete-orphan")
    pull_requests = relationship("PullRequest", back_populates="task", cascade="all, delete-orphan")


class TaskCheckpoint(Base):
    __tablename__ = "task_checkpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"))
    checkpoint_id = Column(String(255), nullable=False)
    node_name = Column(String(100))
    state = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="checkpoints")


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"))
    github_pr_id = Column(Integer)
    github_number = Column(Integer)
    title = Column(String(500))
    description = Column(Text)
    branch_name = Column(String(255))
    status = Column(String(50), default="pending")
    diff_summary = Column(JSON)
    test_results = Column(JSON)
    security_scan_results = Column(JSON)
    human_review_status = Column(String(50), default="pending")
    human_review_comments = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    task = relationship("Task", back_populates="pull_requests")
    user = relationship("User", back_populates="pull_requests")
    repository = relationship("Repository", back_populates="pull_requests")


class TaskLog(Base):
    __tablename__ = "task_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"))
    level = Column(String(20), default="info")
    agent = Column(String(100))
    message = Column(Text, nullable=False)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="logs")
