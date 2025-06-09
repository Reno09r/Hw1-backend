from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.repository.task_repository import TaskRepository
from src.dto.task import Task, TaskCreate, TaskUpdate

class TaskService:
    def __init__(self, db: AsyncSession):
        self.repository = TaskRepository(db)

    async def create_task(self, task_data: TaskCreate, user_id: int) -> Task:
        return await self.repository.create_task(task_data, user_id)

    async def get_task(self, task_id: int) -> Optional[Task]:
        return await self.repository.get_task(task_id)

    async def get_user_tasks(self, user_id: int) -> List[Task]:
        return await self.repository.get_user_tasks(user_id)

    async def update_task(self, task_id: int, task_data: TaskUpdate) -> Optional[Task]:
        return await self.repository.update_task(task_id, task_data)

    async def delete_task(self, task_id: int) -> bool:
        return await self.repository.delete_task(task_id)
