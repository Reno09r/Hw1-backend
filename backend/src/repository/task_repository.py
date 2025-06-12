from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.task import Task
from src.dto.task import TaskCreate, TaskUpdate

class TaskRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(self, task_data: TaskCreate, user_id: int) -> Task:
        db_task = Task(
            title=task_data.title,
            description=task_data.description,
            completed=False,
            user_id=user_id
        )
        self.db.add(db_task)
        await self.db.commit()
        await self.db.refresh(db_task)
        return db_task

    async def get_task(self, task_id: int) -> Optional[Task]:
        result = await self.db.execute(select(Task).filter(Task.id == task_id))
        return result.scalar_one_or_none()

    async def get_user_tasks(self, user_id: int) -> List[Task]:
        result = await self.db.execute(select(Task).filter(Task.user_id == user_id))
        return result.scalars().all()

    async def update_task(self, task_id: int, task_data: TaskUpdate) -> Optional[Task]:
        task = await self.get_task(task_id)
        if task:
            for key, value in task_data.dict(exclude_unset=True).items():
                setattr(task, key, value)
            await self.db.commit()
            await self.db.refresh(task)
        return task

    async def delete_task(self, task_id: int) -> bool:
        task = await self.get_task(task_id)
        if task:
            await self.db.delete(task)
            await self.db.commit()
            return True
        return False
