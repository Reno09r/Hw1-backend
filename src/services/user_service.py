from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from src.repository.user_repository import UserRepository
from src.dto.user import UserCreate, UserUpdate, UserResponse
from src.models.user import User
from src.auth.security import get_password_hash

class UserService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        if len(user_data.password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if user_data.username and await self.repository.get_by_username(user_data.username):
            raise ValueError("User with this username already exists")

        hashed_password = get_password_hash(user_data.password)
        user_data.password = hashed_password

        user = await self.repository.create(user_data)
        return UserResponse.model_validate(user)

    async def get_user_by_id(self, user_id: int) -> Optional[UserResponse]:
        user = await self.repository.get_by_id(user_id)
        if not user:
            return None
        return UserResponse.model_validate(user)

    async def get_user_by_username(self, username: str) -> Optional[UserResponse]:
        user = await self.repository.get_by_username(username)
        if not user:
            return None
        return UserResponse.model_validate(user)

    async def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[UserResponse]:
        if user_data.password and len(user_data.password) < 8:
            raise ValueError("Password must be at least 8 characters long")


        if user_data.username:
            existing_user = await self.repository.get_by_username(user_data.username)
            if existing_user and existing_user.id != user_id:
                raise ValueError("User with this username already exists")
            
        if user_data.password:
            user_data.password = get_password_hash(user_data.password)

        user = await self.repository.update(user_id, user_data)
        if not user:
            return None
        return UserResponse.model_validate(user)

    async def delete_user(self, user_id: int) -> bool:
        return await self.repository.delete(user_id)

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        users = await self.repository.list_users(skip, limit)
        return [UserResponse.model_validate(user) for user in users]

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Аутентификация пользователя"""
        return await self.repository.authenticate_user(username, password) 