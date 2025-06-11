# src/tasks.py

import time # Вместо asyncio
from sqlalchemy import select

from .celery_app import celery_app
from .models.user import User
from .models.task import Task
# Импортируем синхронные Session и новый get_sync_db_session
from .database import get_sync_db_session, Session

# 1. Вспомогательная функция стала синхронной
def get_user_tasks_and_notify_sync(session: Session, user_id: int, username: str):
    try:
        stmt_active_tasks = (
            select(Task)
            .where(Task.user_id == user_id, Task.completed == False)
        )
        # 2. Обычный вызов execute без await
        result_active_tasks = session.execute(stmt_active_tasks)
        active_tasks = result_active_tasks.scalars().all()

        notification_message = f"Hello, {username}! You have {len(active_tasks)} active tasks."
        if active_tasks:
            task_titles = [f"'{t.title}'" for t in active_tasks]
            notification_message += f" They are: {', '.join(task_titles)}."
        else:
            notification_message += " Great job!"

        print(f"--> Sending notification to {username} (ID: {user_id})...")
        print(f"    Message: {notification_message}")
        # 3. Используем time.sleep вместо asyncio.sleep
        time.sleep(0.1) 
        print(f"<-- Notification for {username} (ID: {user_id}) confirmed as sent.")
        return True 

    except Exception as e:
        print(f"[ERROR] in get_user_tasks_and_notify_sync for user {user_id}: {e}")
        return False


# 4. Сама задача стала полностью синхронной
@celery_app.task(name='tasks.notify_user_about_tasks', bind=True)
def notify_user_about_tasks(self):
    """
    Полностью синхронная задача Celery для уведомления пользователей.
    """
    print(f"Starting sync task {self.request.id}...")
    
    # 5. Используем обычный `with` с нашим новым синхронным контекстным менеджером
    with get_sync_db_session() as session:
        try:
            result = session.execute(select(User.id, User.username))
            all_users_data = result.all()

            if not all_users_data:
                return "No users found."

            print(f"Starting notification process for {len(all_users_data)} users...")
            
            successful_notifications = 0
            failed_notifications = 0

            for user_id, username in all_users_data:
                # 6. Вызываем синхронную вспомогательную функцию
                res = get_user_tasks_and_notify_sync(session, user_id, username)
                if res is True:
                    successful_notifications += 1
                else:
                    failed_notifications += 1

            summary = f"Finished. Successful: {successful_notifications}, Failed: {failed_notifications}."
            print("---")
            print(summary)
            return summary

        except Exception as e:
            print(f"Critical error in Celery task {self.request.id}: {e}")
            raise