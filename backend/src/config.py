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
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    
    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


settings = Settings()
