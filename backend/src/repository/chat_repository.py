# src/repositories/chat_repository.py
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import asc
from src.models.chat import ChatMessage, MessageSenderType

class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_message(self, session_id: str, user_id: int, sender_type: MessageSenderType, content: str) -> ChatMessage:
        db_message = ChatMessage(
            session_id=session_id,
            user_id=user_id,
            sender_type=sender_type,
            content=content
        )
        self.db.add(db_message)
        await self.db.commit()
        await self.db.refresh(db_message)
        return db_message

    async def get_messages_by_session_id(self, session_id: str) -> List[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(asc(ChatMessage.timestamp))
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()