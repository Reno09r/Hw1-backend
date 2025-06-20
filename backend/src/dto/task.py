from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Task(BaseModel):
    id: int
    title: str
    description: str
    completed: bool

class TaskCreate(BaseModel):
    title: str
    description: str

class TaskUpdate(BaseModel):
    title: str
    description: str
    completed: bool