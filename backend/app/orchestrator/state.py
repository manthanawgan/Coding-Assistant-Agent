from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime


class AgentState(TypedDict):
    task_id: str
    user_id: str
    repository_id: str
    task: Dict[str, Any]
    repository: Dict[str, Any]
    user: Dict[str, Any]
    status: str
    current_agent: Optional[str]
    progress: int
    research_results: Optional[Dict[str, Any]]
    context: Optional[Dict[str, Any]]
    changes: List[Dict[str, Any]]
    test_results: Optional[Dict[str, Any]]
    security_results: Optional[Dict[str, Any]]
    pr_results: Optional[Dict[str, Any]]
    logs: List[Dict[str, Any]]
    error_message: Optional[str]
    iteration_count: int
    human_approval_required: bool
    human_approved: bool
    created_at: datetime
    updated_at: datetime


def create_initial_state(task_id: str, user_id: str, repository_id: str, task: Dict, repository: Dict, user: Dict) -> AgentState:
    return {
        "task_id": task_id,
        "user_id": user_id,
        "repository_id": repository_id,
        "task": task,
        "repository": repository,
        "user": user,
        "status": "queued",
        "current_agent": None,
        "progress": 0,
        "research_results": None,
        "context": None,
        "changes": [],
        "test_results": None,
        "security_results": None,
        "pr_results": None,
        "logs": [],
        "error_message": None,
        "iteration_count": 0,
        "human_approval_required": False,
        "human_approved": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


def add_log(state: AgentState, log: Dict[str, Any]) -> AgentState:
    state["logs"].append(log)
    return state


def update_progress(state: AgentState, agent: str, progress: int) -> AgentState:
    state["current_agent"] = agent
    state["progress"] = progress
    state["updated_at"] = datetime.utcnow()
    return state
