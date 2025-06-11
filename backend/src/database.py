# src/database.py (модифицированный для возможного использования в Celery)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings
import asyncio 

_ENGINES = {} 

def get_async_engine():
    """
    Возвращает или создает движок SQLAlchemy AsyncEngine, ассоциированный
    с текущим event loop'ом. Это важно для Celery с prefork,
    где каждый воркер-процесс может иметь свой собственный event loop.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError: # No running event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop not in _ENGINES:
        print(f"Creating new SQLAlchemy AsyncEngine for event loop: {id(loop)}")
        _ENGINES[loop] = create_async_engine(
            settings.database_url.replace('postgresql://', 'postgresql+asyncpg://'),
            echo=True, # Отключите echo=True для продакшена в Celery, будет много логов
            pool_size=settings.DB_POOL_SIZE_CELERY if hasattr(settings, 'DB_POOL_SIZE_CELERY') else 2, # Меньший пул для Celery воркеров
            max_overflow=settings.DB_MAX_OVERFLOW_CELERY if hasattr(settings, 'DB_MAX_OVERFLOW_CELERY') else 3,

        )
    return _ENGINES[loop]

async def dispose_engine_for_loop(loop_to_dispose):
    """Закрывает движок, ассоциированный с данным event loop'ом."""
    if loop_to_dispose in _ENGINES:
        print(f"Disposing SQLAlchemy AsyncEngine for event loop: {id(loop_to_dispose)}")
        engine_to_dispose = _ENGINES.pop(loop_to_dispose)
        await engine_to_dispose.dispose()

async def get_db_session() -> AsyncSession:
    """
    Возвращает новую асинхронную сессию SQLAlchemy, используя движок,
    ассоциированный с текущим event loop'ом.
    """
    current_engine = get_async_engine()

    session = AsyncSession(bind=current_engine, expire_on_commit=False)
    return session

fastapi_engine = create_async_engine(
    settings.database_url.replace('postgresql://', 'postgresql+asyncpg://'),
    echo=settings.DB_ECHO if hasattr(settings, 'DB_ECHO') else True, # Предположим, echo настраивается
    pool_size=settings.DB_POOL_SIZE_FASTAPI if hasattr(settings, 'DB_POOL_SIZE_FASTAPI') else 5,
    max_overflow=settings.DB_MAX_OVERFLOW_FASTAPI if hasattr(settings, 'DB_MAX_OVERFLOW_FASTAPI') else 10
)
fastapi_async_sessionmaker = sessionmaker(
    fastapi_engine, class_=AsyncSession, expire_on_commit=False
)
async def get_db(): # FastAPI dependency
    async with fastapi_async_sessionmaker() as session:
        yield session

Base = declarative_base()