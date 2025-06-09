#!/bin/sh

# Применяем миграции
alembic upgrade head

# Запускаем приложение
uvicorn src.main:app --host 0.0.0.0 --port 8001