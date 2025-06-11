# src/redis_client.py
from typing import Optional
import redis.asyncio as redis # <-- ГЛАВНОЕ ИЗМЕНЕНИЕ
from src.config import settings

# Определяем переменную для хранения клиента Redis.
redis_client: Optional[redis.Redis] = None

async def init_redis_pool():
    """
    Инициализирует пул соединений Redis.
    Вызывается при старте FastAPI приложения.
    """
    global redis_client
    redis_client = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True
    )

async def close_redis_pool():
    """
    Закрывает пул соединений Redis.
    Вызывается при завершении работы FastAPI приложения.
    """
    if redis_client:
        await redis_client.close()

async def get_redis_client() -> redis.Redis:
    """
    Зависимость (dependency) для получения экземпляра клиента redis.asyncio.
    """
    if redis_client is None:
        raise RuntimeError("Redis client has not been initialized. Call init_redis_pool on startup.")
    return redis_client