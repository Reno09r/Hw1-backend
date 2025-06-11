import asyncio
from datetime import datetime

from sqlalchemy import select
from celery_app import celery_app
from src.models.user import User
from src.models.task import Task

from .database import get_db_session

import asyncio
from datetime import datetime

from sqlalchemy import select
from celery_app import celery_app
from src.models.user import User
from src.models.task import Task

from .database import get_db_session

async def get_user_tasks_and_notify_async(user_id: int, username: str):
    """
    Получает задачи пользователя и "уведомляет" его, логируя процесс.
    """
    session = await get_db_session()
    try:
        # Получаем активные задачи
        stmt_active_tasks = (
            select(Task)
            .where(Task.user_id == user_id, Task.completed == False)
        )
        result_active_tasks = await session.execute(stmt_active_tasks)
        active_tasks = result_active_tasks.scalars().all()


        notification_message = f"Hello, {username}! You have {len(active_tasks)} active tasks."
        if active_tasks:
            task_titles = [f"'{t.title}'" for t in active_tasks]
            notification_message += f" They are: {', '.join(task_titles)}."
        else:
            notification_message += " Great job!"

        print(f"--> Sending notification to {username} (ID: {user_id})...")
        print(f"    Message: {notification_message}")

        await asyncio.sleep(0.1) 

        print(f"<-- Notification for {username} (ID: {user_id}) confirmed as sent.")

        return True 

    except Exception as e:
        print(f"[ERROR] in get_user_tasks_and_notify_async for user {user_id}: {e}")
        raise
    finally:
        await session.close()

@celery_app.task(name='tasks.notify_user_about_tasks', bind=True)
def notify_user_about_tasks(self):
    current_loop = None
    try:
        async def _run_notifications():
            nonlocal current_loop
            current_loop = asyncio.get_running_loop()

            all_users_data = []
            session = await get_db_session()
            try:
                result = await session.execute(select(User.id, User.username))
                all_users_data = result.all()
            finally:
                await session.close()

            if not all_users_data:
                print("No users found to notify.")
                return

            print(f"Starting notification process for {len(all_users_data)} users...")

            notification_coroutines = [
                get_user_tasks_and_notify_async(user_id, username)
                for user_id, username in all_users_data
            ]
            
            results = await asyncio.gather(*notification_coroutines, return_exceptions=True)
            
            successful_notifications = 0
            failed_notifications = 0
            for i, res in enumerate(results):
                user_id, username = all_users_data[i]
                if isinstance(res, Exception):
                    print(f"[SUMMARY] Failed to notify {username} (ID: {user_id}).")
                    failed_notifications += 1
                elif res: # Проверяем, что вернулось True
                    successful_notifications += 1
            
            print("---") # Разделитель для лога
            print("Finished processing notifications for all users.")
            print(f"Summary: {successful_notifications} successful, {failed_notifications} failed.")
            # --- КОНЕЦ УЛУЧШЕННОЙ ЧАСТИ ---

        asyncio.run(_run_notifications())
    except Exception as e:
        print(f"Error in Celery task {self.request.id}: {e}")
        raise
    
    return "User task notification cycle completed."