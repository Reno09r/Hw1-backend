from datetime import datetime
from typing import Optional, Annotated
from pydantic import BaseModel, EmailStr, StringConstraints

class UserBase(BaseModel):
    username: Optional[Annotated[str, StringConstraints(min_length=3, max_length=100)]] = None

class UserCreate(UserBase):
    password: Annotated[str, StringConstraints(min_length=8)]

class UserUpdate(UserBase):
    password: Optional[Annotated[str, StringConstraints(min_length=8)]] = None
    
class UserResponse(UserBase):
    id: int 

class LoginRequest(BaseModel):
    username: str
    password: str

    