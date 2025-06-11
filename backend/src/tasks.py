# src/tasks.py

import time
import json
import redis # <-- Используем синхронный клиент redis
from sqlalchemy import select

from .celery_app import celery_app
from .models.user import User
from .models.task import Task
from .database import get_sync_db_session, Session
from .config import settings # <-- Импортируем settings

# ... (вспомогательная функция get_user_tasks_and_notify_sync остается без изменений) ...

def get_user_tasks_and_notify_sync(session: Session, user_id: int, username: str):
    try:
        stmt_active_tasks = (
            select(Task)
            .where(Task.user_id == user_id, Task.completed == False)
        )
        result_active_tasks = session.execute(stmt_active_tasks)
        active_tasks = result_active_tasks.scalars().all()

        notification_message = f"Hello, {username}! You have {len(active_tasks)} active tasks."
        if active_tasks:
            task_titles = [f"'{t.title}'" for t in active_tasks]
            notification_message += f" They are: {', '.join(task_titles)}."
        else:
            notification_message += " Great job!"
        
        # Возвращаем само сообщение для отправки
        return notification_message

    except Exception as e:
        print(f"[ERROR] in get_user_tasks_and_notify_sync for user {user_id}: {e}")
        return None


@celery_app.task(name='tasks.notify_user_about_tasks', bind=True)
def notify_user_about_tasks(self):
    """
    Синхронная задача Celery. Теперь она публикует результат в Redis.
    """
    print(f"Starting sync task {self.request.id}...")
    
    # Создаем синхронный клиент Redis специально для этой задачи
    redis_client = redis.from_url(settings.redis_url)

    with get_sync_db_session() as session:
        try:
            result = session.execute(select(User.id, User.username))
            all_users_data = result.all()

            if not all_users_data:
                return "No users found."

            print(f"Starting notification process for {len(all_users_data)} users...")
            
            successful_notifications = 0
            failed_publications = 0

            for user_id, username in all_users_data:
                # 1. Получаем текст сообщения
                message_text = get_user_tasks_and_notify_sync(session, user_id, username)

                if message_text:
                    # 2. Формируем payload для Redis
                    payload = json.dumps({
                        "user_id": user_id,
                        "message": message_text
                    })
                    # 3. Публикуем в канал 'notifications'
                    redis_client.publish("notifications", payload)
                    print(f"Published notification for user {user_id} to Redis.")
                    successful_notifications += 1
                else:
                    failed_publications += 1

            summary = f"Finished. Published: {successful_notifications}, Failed: {failed_publications}."
            print("---")
            print(summary)
            return summary

        except Exception as e:
            print(f"Critical error in Celery task {self.request.id}: {e}")
            raise
        finally:
            # Закрываем клиент Redis
            redis_client.close()