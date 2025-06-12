import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base

class MessageSenderType(enum.Enum):
    USER = "user"
    AGENT = "agent"

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False) # UUID для группировки сообщений в один диалог
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sender_type = Column(Enum(MessageSenderType), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")