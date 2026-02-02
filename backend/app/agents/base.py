from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.config.logging import logger


class BaseAgent(ABC):
    name: str = "base_agent"

    def __init__(self):
        self.state: Dict[str, Any] = {}

    async def log(self, message: str, level: str = "info", **kwargs):
        logger.info(f"[{self.name}] {message}")
        return {
            "agent": self.name,
            "level": level,
            "message": message,
            "metadata": kwargs
        }

    @abstractmethod
    async def execute(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        pass

    async def can_execute(self, task_context: Dict[str, Any]) -> bool:
        return True

    def set_state(self, key: str, value: Any):
        self.state[key] = value

    def get_state(self, key: str) -> Any:
        return self.state.get(key)
