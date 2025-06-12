# src/services/chat_service.py
import uuid
from typing import List
from src.repository.chat_repository import ChatRepository
from src.services.a2a_client import A2AClientService
from src.dto.chat import ChatMessageCreate, ChatMessageResponse, ChatSessionResponse
from src.models.chat import MessageSenderType

class ChatService:
    def __init__(self, repository: ChatRepository, a2a_client: A2AClientService):
        self.repository = repository
        self.a2a_client = a2a_client

    async def process_user_message(self, user_id: int, message_data: ChatMessageCreate) -> ChatSessionResponse:
        session_id = message_data.session_id or str(uuid.uuid4())

        # 1. Сохраняем сообщение пользователя
        await self.repository.create_message(
            session_id=session_id,
            user_id=user_id,
            sender_type=MessageSenderType.USER,
            content=message_data.content
        )

        agent_response_text = await self.a2a_client.send_message_to_manager(
            message_data.content
        )

        # 3. Сохраняем ответ агента
        await self.repository.create_message(
            session_id=session_id,
            user_id=user_id, # Ответ привязан к тому же пользователю
            sender_type=MessageSenderType.AGENT,
            content=agent_response_text
        )
        
        # 4. Возвращаем всю историю чата для этой сессии
        return await self.get_chat_history(session_id)


    async def get_chat_history(self, session_id: str) -> ChatSessionResponse:
        messages = await self.repository.get_messages_by_session_id(session_id)
        return ChatSessionResponse(
            session_id=session_id,
            messages=[ChatMessageResponse.model_validate(msg) for msg in messages]
        )