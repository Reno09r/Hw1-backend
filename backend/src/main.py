from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.routers.task_router import router as tasks_router
from src.routers.user_router import router as user_router
from src.auth.auth_router import router as auth_router
app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем только наш фронтенд
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем конкретные методы
    allow_headers=["*"],  # Разрешаем все заголовки
    expose_headers=["*"]
)

@app.get("/")
def read_root():
    return {"message": f"Hello!"}

app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(user_router)
