# src/repositories/chat_repository.py
from typing import List, Optional # Добавляем Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import asc, desc # Добавляем desc
from src.models.chat import ChatMessage, MessageSenderType

class ChatRepository:
    def __init__(self, db: AsyncSession): # В реальном приложении сессия должна передаваться в каждый метод
        self._db = db # Используем _db для хранения сессии переданной при инициализации

    @property
    def db(self) -> AsyncSession: # Свойство для получения сессии
        return self._db # Здесь должна быть логика получения сессии из пула/менеджера контекста

    async def create_message(self, session_id: str, user_id: int, sender_type: MessageSenderType, content: str) -> ChatMessage:
        # В реальном приложении вы бы получали сессию здесь, например:
        # async with self.db_session_manager.get_session() as session:
        #     db_message = ChatMessage(...)
        #     session.add(db_message)
        #     await session.commit()
        #     await session.refresh(db_message)
        # Для простоты текущего примера, предполагаем, что self.db уже активная сессия
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

    async def get_messages_by_session_id(self, session_id: str, limit: Optional[int] = None) -> List[ChatMessage]:
        # Аналогично, сессия должна быть получена здесь
        # async with self.db_session_manager.get_session() as session:
        # ...
        if limit:
            # Получаем последние N сообщений, сортируя по убыванию timestamp, затем разворачиваем для хронологического порядка
            stmt = (
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .order_by(desc(ChatMessage.timestamp)) # Сначала последние
                .limit(limit)
            )
            result = await self.db.execute(stmt)
            messages = result.scalars().all()
            return list(reversed(messages)) # Разворачиваем, чтобы были в хронологическом порядке (старые -> новые)
        else:
            # Получаем все сообщения в хронологическом порядке
            stmt = (
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .order_by(asc(ChatMessage.timestamp))
            )
            result = await self.db.execute(stmt)
            return result.scalars().all()