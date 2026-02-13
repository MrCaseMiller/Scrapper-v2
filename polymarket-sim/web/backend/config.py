"""Application configuration."""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Supabase (optional with defaults for temp deployments)
    supabase_url: str = "https://placeholder.supabase.co"
    supabase_key: str = "placeholder-key"
    supabase_service_key: str = "placeholder-service-key"

    # Database (optional with SQLite default for temp deployments)
    database_url: str = "sqlite+aiosqlite:///./temp.db"

    # JWT (optional with temp default)
    jwt_secret_key: str = "temp-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Application
    environment: str = "production"
    frontend_url: str = "http://localhost:3000"

    # Portfolio
    default_starting_balance: float = 1000.0

    @field_validator('database_url', mode='before')
    @classmethod
    def validate_database_url(cls, v):
        """Use default if empty or None."""
        if not v:
            return "sqlite+aiosqlite:///./temp.db"
        return v

    @field_validator('supabase_url', mode='before')
    @classmethod
    def validate_supabase_url(cls, v):
        """Use default if empty or None."""
        if not v:
            return "https://placeholder.supabase.co"
        return v

    @field_validator('supabase_key', mode='before')
    @classmethod
    def validate_supabase_key(cls, v):
        """Use default if empty or None."""
        if not v:
            return "placeholder-key"
        return v

    @field_validator('supabase_service_key', mode='before')
    @classmethod
    def validate_supabase_service_key(cls, v):
        """Use default if empty or None."""
        if not v:
            return "placeholder-service-key"
        return v

    @field_validator('jwt_secret_key', mode='before')
    @classmethod
    def validate_jwt_secret_key(cls, v):
        """Use default if empty or None."""
        if not v:
            return "temp-secret-key-change-in-production"
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
