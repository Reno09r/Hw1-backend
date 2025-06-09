from fastapi import Depends
from src.database import get_db
from sqlalchemy.orm import Session
from src.services.user_service import UserService

def get_user_service(db_session = Depends(get_db)):
    return UserService(db_session)

