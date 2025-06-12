# dependencies.py

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis # <-- ИЗМЕНЕНИЕ

from src.database import get_db
from src.services.user_service import UserService
from src.services.task_service import TaskService
from src.redis_client import get_redis_client
from src.repository.chat_repository import ChatRepository
from src.services.chat_service import ChatService
from src.services.a2a_client import get_a2a_client_service, A2AClientService

def get_user_service(db_session: AsyncSession = Depends(get_db)):
    return UserService(db_session)

def get_task_service(
    db_session: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client) # <-- Тип теперь из redis.asyncio
):
    """
    Внедряет сессию БД и асинхронный клиент Redis в TaskService.
    """
    return TaskService(db=db_session, redis_client=redis_client)

def get_chat_repository(db: AsyncSession = Depends(get_db)) -> ChatRepository:
    return ChatRepository(db)

def get_chat_service(
    repo: ChatRepository = Depends(get_chat_repository),
    a2a_client: A2AClientService = Depends(get_a2a_client_service)
) -> ChatService:
    return ChatService(repo, a2a_client)
