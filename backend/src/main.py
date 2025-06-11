import asyncio
import json
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# 1. Импортируем обе функции: для инициализации и для закрытия
# Добавляем get_redis_client для использования в listener
from src.redis_client import init_redis_pool, close_redis_pool, get_redis_client
from src.config import settings
from src.routers.task_router import router as tasks_router
from src.routers.user_router import router as user_router
from src.auth.auth_router import router as auth_router

# Новый класс для управления WebSocket-соединениями
class ConnectionManager:
    def __init__(self):
        # Храним активные соединения: {user_id: WebSocket}
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"New WebSocket connection for user: {user_id}")

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"WebSocket connection closed for user: {user_id}")

    async def send_to_user(self, message: str, user_id: int):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)
            print(f"Sent message to user {user_id}: {message}")


manager = ConnectionManager()

# Функция-слушатель для Redis Pub/Sub
async def redis_listener(manager: ConnectionManager):
    redis = await get_redis_client()
    pubsub = redis.pubsub()
    await pubsub.subscribe("notifications")
    print("Subscribed to 'notifications' channel in Redis.")
    while True:
        try:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message.get("type") == "message":
                print(f"Received message from Redis: {message['data']}")
                data = json.loads(message["data"])
                user_id = data.get("user_id")
                notification_message = data.get("message")
                if user_id and notification_message:
                    await manager.send_to_user(notification_message, user_id)
            await asyncio.sleep(0.01)
        except Exception as e:
            print(f"Error in redis_listener: {e}")
            await asyncio.sleep(5) # Пауза перед переподключением

# 2. Обновляем lifespan для запуска слушателя Redis
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application starts, initialize Redis pool...")
    await init_redis_pool()
    print("Redis pool successfully initialized.")

    # Запускаем слушателя Redis в фоновой задаче
    listener_task = asyncio.create_task(redis_listener(manager))
    print("Redis Pub/Sub listener started.")

    yield

    print("Application stops, cancelling listener and closing Redis pool...")
    listener_task.cancel()
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

# Новый WebSocket эндпоинт
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    print(f"User {user_id} connected via WebSocket. Awaiting messages...") # <-- Добавим лог
    try:
        while True:
            # Эта часть нужна, чтобы соединение не обрывалось по таймауту
            # и чтобы корректно обработать закрытие со стороны клиента.
            data = await websocket.receive_text()
            print(f"Received from user {user_id}: {data}") # Логируем, если клиент что-то прислал
    except WebSocketDisconnect:
        print(f"User {user_id} disconnected.") # <-- Лог при отключении
        manager.disconnect(user_id)
    except Exception as e:
        print(f"Error in WebSocket for user {user_id}: {e}") # <-- Лог при других ошибках
        manager.disconnect(user_id)



@app.get("/")
def read_root():
    return {"message": "Hello!"}

app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(user_router)