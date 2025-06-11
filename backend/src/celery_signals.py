# src/celery_signals.py

from celery.signals import worker_process_init, worker_process_shutdown
# Импортируем новые, специфичные для Celery, синхронные функции
from .database import setup_celery_db_engine, dispose_celery_db_engine

# asyncio больше не нужен
# import asyncio

@worker_process_init.connect
def init_worker(**kwargs):
    """
    Сигнал, который срабатывает при запуске воркера.
    Инициализируем СИНХРОННЫЙ движок БД для Celery.
    """
    print("Celery worker process initializing sync DB engine via signal...")
    setup_celery_db_engine()

@worker_process_shutdown.connect
def shutdown_worker(**kwargs):
    """
    Сигнал, который срабатывает при завершении работы воркера.
    Корректно закрываем СИНХРОННЫЙ пул соединений.
    """
    print("Celery worker process shutting down sync DB engine via signal...")
    # Просто вызываем синхронную функцию
    dispose_celery_db_engine()