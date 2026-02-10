from pydantic import BaseModel
from typing import List, Optional, Dict


class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Message]] = []

class ChatResponse(BaseModel):
    response: str
    thoughts: Optional[List[str]] = []
    metadata: Optional[Dict] = {}