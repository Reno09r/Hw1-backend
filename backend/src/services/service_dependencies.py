# dependencies.py

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis # <-- ИЗМЕНЕНИЕ

from src.database import get_db
from src.services.user_service import UserService
from src.services.task_service import TaskService
from src.redis_client import get_redis_client

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