from typing import List, Optional
from sqlalchemy.orm import Session
from repository.task_repository import TaskRepository
from dto.task import Task, TaskCreate, TaskUpdate

class TaskService:
    def __init__(self, db: Session):
        self.repository = TaskRepository(db)

    def create_task(self, task_data: TaskCreate, user_id: int) -> Task:
        return self.repository.create_task(task_data, user_id)

    def get_task(self, task_id: int) -> Optional[Task]:
        return self.repository.get_task(task_id)

    def get_user_tasks(self, user_id: int) -> List[Task]:
        return self.repository.get_user_tasks(user_id)

    def update_task(self, task_id: int, task_data: TaskUpdate) -> Optional[Task]:
        return self.repository.update_task(task_id, task_data)

    def delete_task(self, task_id: int) -> bool:
        return self.repository.delete_task(task_id)
