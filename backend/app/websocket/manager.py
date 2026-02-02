import json
from typing import Dict, Set, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime
import asyncio

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.task_connections: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
        self.active_connections[task_id].add(websocket)
        if task_id not in self.task_connections:
            self.task_connections[task_id] = set()
        self.task_connections[task_id].add("websocket")

    def disconnect(self, websocket: WebSocket, task_id: str):
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
                if task_id in self.task_connections:
                    del self.task_connections[task_id]

    async def send_message(self, task_id: str, message: dict):
        if task_id in self.active_connections:
            message_json = json.dumps(message)
            for connection in list(self.active_connections[task_id]):
                try:
                    await connection.send_text(message_json)
                except Exception:
                    self.active_connections[task_id].discard(connection)

    async def send_log(self, task_id: str, log: dict):
        await self.send_message(task_id, {"type": "log", "data": log})

    async def send_status(self, task_id: str, status: dict):
        await self.send_message(task_id, {"type": "status", "data": status})

    async def send_diff(self, task_id: str, diff: dict):
        await self.send_message(task_id, {"type": "diff", "data": diff})

    async def send_approval_request(self, task_id: str):
        await self.send_message(task_id, {"type": "approval_required", "data": {
            "task_id": task_id,
            "message": "Human approval required before creating PR"
        }})

    async def send_pr_created(self, task_id: str, pr_data: dict):
        await self.send_message(task_id, {"type": "pr_created", "data": pr_data})


websocket_manager = ConnectionManager()


@router.websocket("/tasks/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await websocket_manager.connect(websocket, task_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, task_id)
