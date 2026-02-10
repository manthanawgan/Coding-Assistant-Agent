from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Coding Assistant Agent"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-1.5-pro"
    MAX_TOKENS: int = 8192
    TEMPERATURE: float = 0.7
    
    ALLOWED_ORIGINS: list = ["http://localhost:3000"]
    
    USE_DOCKER: bool = True
    EXECUTION_TIMEOUT: int = 30  #secs
    MAX_FILE_SIZE: int = 1024 * 1024  #1mb
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()