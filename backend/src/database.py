# =========================================================================
# === АСИНХРОННАЯ ЧАСТЬ (ДЛЯ FASTAPI) ==========
# =========================================================================

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings
import asyncio

engine = None

def setup_db_engine():
    """
    Инициализирует AsyncEngine. Эта функция будет вызвана один раз
    при старте каждого процесса-воркера Celery.
    """
    global engine
    if engine is None:
        print("--- Initializing SQLAlchemy AsyncEngine for Celery worker ---")
        engine = create_async_engine(
            settings.database_url.replace('postgresql://', 'postgresql+asyncpg://'),
            pool_size=settings.DB_POOL_SIZE_CELERY if hasattr(settings, 'DB_POOL_SIZE_CELERY') else 5,
            max_overflow=settings.DB_MAX_OVERFLOW_CELERY if hasattr(settings, 'DB_MAX_OVERFLOW_CELERY') else 10,
        )

async def dispose_db_engine():
    """
    Закрывает пул соединений движка. Будет вызвана при остановке
    каждого процесса-воркера Celery.
    """
    global engine
    if engine:
        print("--- Disposing SQLAlchemy AsyncEngine for Celery worker ---")
        await engine.dispose()
        engine = None

async def get_db_session() -> AsyncSession:
    """
    Возвращает новую асинхронную сессию, используя единый движок процесса.
    """
    if engine is None:
        setup_db_engine()
        
    session = AsyncSession(bind=engine, expire_on_commit=False)
    return session

fastapi_engine = create_async_engine(
    settings.database_url.replace('postgresql://', 'postgresql+asyncpg://'),
    echo=settings.DB_ECHO if hasattr(settings, 'DB_ECHO') else True,
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

# =========================================================================
# === СИНХРОННАЯ ЧАСТЬ (ТОЛЬКО ДЛЯ CELERY) ====================
# =========================================================================
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

SYNC_DATABASE_URL = settings.database_url.replace("+asyncpg", "+psycopg2")

sync_engine = create_engine(SYNC_DATABASE_URL)

SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

@contextmanager
def get_sync_db_session() -> Session:
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()

def setup_celery_db_engine():
    """Инициализация. Движок уже создан, так что просто выводим сообщение."""
    print("--- SQLAlchemy SyncEngine is ready for Celery worker ---")
    pass

def dispose_celery_db_engine():
    """Закрытие пула соединений синхронного движка."""
    print("--- Disposing SQLAlchemy SyncEngine for Celery worker ---")
    if sync_engine:
        sync_engine.dispose()