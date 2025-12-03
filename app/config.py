"""Application configuration."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://pat_user:pat_password@localhost:5432/pat_db"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Application
    DEBUG: bool = False
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Token
    TOKEN_PREFIX: str = "pat_"
    TOKEN_LENGTH: int = 32
    TOKEN_PREFIX_DISPLAY_LENGTH: int = 8
    
    # FCS
    DEFAULT_FCS_FILE: str = "data/0000123456_1234567_AML_ClearLLab10C_TTube.fcs"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
