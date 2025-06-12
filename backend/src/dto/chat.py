# src/dto/chat.py
from pydantic import BaseModel
from datetime import datetime
from typing import List

# Используем тот же Enum, что и в модели
from src.models.chat import MessageSenderType 

class ChatMessageBase(BaseModel):
    content: str

class ChatMessageCreate(ChatMessageBase):
    session_id: str | None = None # Может быть None для начала нового чата

class ChatMessageResponse(ChatMessageBase):
    id: int
    session_id: str
    sender_type: MessageSenderType
    timestamp: datetime

    class Config:
        from_attributes = True

class ChatSessionResponse(BaseModel):
    session_id: str
    messages: List[ChatMessageResponse]