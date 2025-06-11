# src/services/task_service.py

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis 
from redis.exceptions import RedisError # <-- ИЗМЕНЕНИЕ
import json

from src.repository.task_repository import TaskRepository
from src.dto.task import Task, TaskCreate, TaskUpdate

CACHE_EXPIRATION_SECONDS = int(timedelta(minutes=20).total_seconds())

class TaskService:
    def __init__(self, db: AsyncSession, redis_client: redis.Redis):
        self.repository = TaskRepository(db)
        self.redis_client = redis_client

    def _get_user_tasks_cache_key(self, user_id: int) -> str:
        return f"user:{user_id}:tasks"
        
    async def _clear_user_tasks_cache(self, user_id: int):
        cache_key = self._get_user_tasks_cache_key(user_id)
        try:
            await self.redis_client.delete(cache_key)
        except RedisError as e: # <-- ИЗМЕНЕНИЕ
            print(f"Failed to clear Redis cache for key {cache_key}: {e}")

    # ... (методы create, update, delete остаются с той же логикой инвалидации) ...
    async def create_task(self, task_data: TaskCreate, user_id: int) -> Task:
        if task_data.due_date and task_data.due_date < datetime.utcnow():
            raise ValueError("Due date cannot be in the past")
        new_task = await self.repository.create_task(task_data, user_id)
        await self._clear_user_tasks_cache(user_id)
        return new_task

    async def get_task(self, task_id: int) -> Optional[Task]:
        return await self.repository.get_task(task_id)


    async def get_user_tasks(self, user_id: int) -> List[Task]:
        cache_key = self._get_user_tasks_cache_key(user_id)
        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                tasks_list = json.loads(cached_data)
                return [Task.model_validate(task_data) for task_data in tasks_list]
        except (RedisError, json.JSONDecodeError) as e: # <-- ИЗМЕНЕНИЕ
            print(f"Redis cache read failed for key {cache_key}: {e}")
        
        orm_tasks = await self.repository.get_user_tasks(user_id)
        pydantic_tasks = [Task.model_validate(orm_task, from_attributes=True) for orm_task in orm_tasks]

        try:
            tasks_json_to_cache = json.dumps([task.model_dump(mode='json') for task in pydantic_tasks])
            await self.redis_client.setex(cache_key, CACHE_EXPIRATION_SECONDS, tasks_json_to_cache)
        except RedisError as e: # <-- ИЗМЕНЕНИЕ
            print(f"Redis cache write failed for key {cache_key}: {e}")
            
        return pydantic_tasks

    async def update_task(self, task_id: int, task_data: TaskUpdate) -> Optional[Task]:
        if task_data.due_date and task_data.due_date < datetime.utcnow():
            raise ValueError("Due date cannot be in the past")
        task_to_update = await self.repository.get_task(task_id)
        if not task_to_update:
            return None
        updated_task = await self.repository.update_task(task_id, task_data)
        await self._clear_user_tasks_cache(task_to_update.user_id)
        return updated_task

    async def delete_task(self, task_id: int) -> bool:
        task_to_delete = await self.repository.get_task(task_id)
        if not task_to_delete:
            return False
        is_deleted = await self.repository.delete_task(task_id)
        if is_deleted:
            await self._clear_user_tasks_cache(task_to_delete.user_id)
        return is_deleted