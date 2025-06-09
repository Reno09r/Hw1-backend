from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config import settings

# Создаем асинхронный движок базы данных
engine = create_async_engine(
    settings.database_url.replace('postgresql://', 'postgresql+asyncpg://'),
    echo=True,
    pool_size=5,
    max_overflow=10
)

# Создаем фабрику асинхронных сессий
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Создаем базовый класс для моделей
Base = declarative_base()

async def init_db():
    """Асинхронная функция для создания таблиц"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """Dependency для получения асинхронной сессии базы данных"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()