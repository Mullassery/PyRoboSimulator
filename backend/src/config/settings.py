"""Application settings & configuration."""

from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/pyrobosim_dev"
    DATABASE_POOL_MIN_SIZE: int = 5
    DATABASE_POOL_MAX_SIZE: int = 20
    DATABASE_POOL_RECYCLE: int = 3600

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_POOL_MIN_SIZE: int = 5
    REDIS_POOL_MAX_SIZE: int = 50

    # Authentication
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    # Simulation
    MAX_AGENTS: int = 1_000_000
    MAX_SIMULATION_DURATION: int = 3600
    DEFAULT_TIMESTEP: float = 0.016

    # Monitoring
    PROMETHEUS_PORT: int = 8001
    JAEGER_ENABLED: bool = False
    JAEGER_HOST: str = "localhost"
    JAEGER_PORT: int = 6831

    class Config:
        """Pydantic settings config."""

        env_file = "../config/.env"
        case_sensitive = True
