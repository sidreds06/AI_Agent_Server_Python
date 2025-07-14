from pydantic import BaseModel
from typing import List, Literal

class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatTurn] = []
    uid: str = None

class SummaryRequest(BaseModel):
    messages: List[dict]