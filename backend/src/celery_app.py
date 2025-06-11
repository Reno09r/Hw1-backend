# src/celery_app.py
from celery import Celery
from celery.schedules import crontab
from src.config import settings

celery_app = Celery(
    'tasks',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['src.tasks'] 
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    'notify-users-every-10-seconds': {
        'task': 'tasks.notify_user_about_tasks',
        'schedule': 15.0,
    },
}