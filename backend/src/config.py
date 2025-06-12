from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='allow')
    
    database_url: str
    jwt_secret_key: str
    ALGORITHM: str
    
    # Redis settings
    redis_url:str
    CELERY_BROKER_URL:str
    CELERY_RESULT_BACKEND:str
    MANAGER_AGENT_URL:str

settings = Settings()
