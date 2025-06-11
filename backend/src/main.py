# main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 1. Импортируем обе функции: для инициализации и для закрытия
from src.redis_client import init_redis_pool, close_redis_pool
from src.config import settings
from src.routers.task_router import router as tasks_router
from src.routers.user_router import router as user_router
from src.auth.auth_router import router as auth_router

# 2. Создаем асинхронный контекстный менеджер для управления жизненным циклом
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application starts, initialize Redis pool...")
    await init_redis_pool()
    print("Redis pool successfully initialized.")

    yield

    print("Application stops, close Redis pool...")
    await close_redis_pool()
    print("Redis pool successfully closed.")


# 3. Подключаем lifespan к нашему приложению FastAPI
app = FastAPI(lifespan=lifespan)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.get("/")
def read_root():
    return {"message": "Hello!"}

app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(user_router)