from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Task(BaseModel):
    id: int
    title: str
    description: str
    completed: bool
    due_date: Optional[datetime] = None
    updated_at: datetime

class TaskCreate(BaseModel):
    title: str
    description: str
    due_date: Optional[datetime] = None

class TaskUpdate(BaseModel):
    title: str
    description: str
    completed: bool
    due_date: Optional[datetime] = None