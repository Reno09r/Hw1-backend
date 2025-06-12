# src/services/chat_service.py
import uuid
from typing import List, Optional # Добавляем Optional
from src.repository.chat_repository import ChatRepository
from src.services.a2a_client import A2AClientService
from src.dto.chat import ChatMessageCreate, ChatMessageResponse, ChatSessionResponse
from src.models.chat import MessageSenderType, ChatMessage as ChatMessageModel

class ChatService:
    def __init__(self, repository: ChatRepository, a2a_client: A2AClientService):
        self.repository = repository
        self.a2a_client = a2a_client

    async def process_user_message(self, user_id: int, message_data: ChatMessageCreate) -> ChatSessionResponse:
        session_id = message_data.session_id or str(uuid.uuid4())

        await self.repository.create_message(
            session_id=session_id,
            user_id=user_id,
            sender_type=MessageSenderType.USER,
            content=message_data.content
        )

        # Получаем историю сообщений, включая только что добавленное (последние N)
        # в хронологическом порядке (старые -> новые)
        chat_history_models: List[ChatMessageModel] = await self.repository.get_messages_by_session_id(session_id, limit=10)
        
        formatted_conversation_lines = []
        for msg in chat_history_models: # Теперь сообщения уже в хронологическом порядке
            sender_prefix = "User" if msg.sender_type == MessageSenderType.USER else "Agent"
            formatted_conversation_lines.append(f"{sender_prefix}: {msg.content}")
        
        full_conversation_text = "\n".join(formatted_conversation_lines)
        
        agent_response_text = await self.a2a_client.send_message_to_manager(
            conversation_text=full_conversation_text
        )

        await self.repository.create_message(
            session_id=session_id,
            user_id=user_id, 
            sender_type=MessageSenderType.AGENT,
            content=agent_response_text
        )
        
        return await self.get_chat_history(session_id)

    async def get_chat_history(self, session_id: str) -> ChatSessionResponse:
        # Тут можно тоже добавить limit, если история может быть очень большой для отображения
        messages = await self.repository.get_messages_by_session_id(session_id)
        return ChatSessionResponse(
            session_id=session_id,
            messages=[ChatMessageResponse.model_validate(msg) for msg in messages]
        )