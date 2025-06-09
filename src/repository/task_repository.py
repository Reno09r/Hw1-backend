from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.task import Task
from src.dto.task import TaskCreate, TaskUpdate

class TaskRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def create_task(self, task_data: TaskCreate, user_id: int) -> Task:
        db_task = Task(
            title=task_data.title,
            description=task_data.description,
            user_id=user_id
        )
        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)
        return db_task

    def get_task(self, task_id: int) -> Optional[Task]:
        return self.db.query(Task).filter(Task.id == task_id).first()

    def get_user_tasks(self, user_id: int) -> List[Task]:
        return self.db.query(Task).filter(Task.user_id == user_id).all()

    def update_task(self, task_id: int, task_data: TaskUpdate) -> Optional[Task]:
        task = self.get_task(task_id)
        if task:
            for key, value in task_data.dict(exclude_unset=True).items():
                setattr(task, key, value)
            self.db.commit()
            self.db.refresh(task)
        return task

    def delete_task(self, task_id: int) -> bool:
        task = self.get_task(task_id)
        if task:
            self.db.delete(task)
            self.db.commit()
            return True
        return False
