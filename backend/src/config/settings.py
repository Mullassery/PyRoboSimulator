"""Application settings & configuration."""

from pathlib import Path
from typing import List

from pydantic import model_validator
from pydantic_settings import BaseSettings

# settings.py lives at backend/src/config/settings.py while the environment
# file lives at backend/config/.env. Resolve it relative to this file instead
# of the process working directory, so loading settings works no matter where
# the app (or the test suite) is launched from.
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / "config" / ".env"

# Placeholder values shipped in this module and backend/config/.env.example.
# Startup refuses these so a misconfigured deployment fails loudly instead of
# signing tokens with a publicly-known key.
_WEAK_SECRET_KEYS = {
    "change-me-in-production",
    "change-me-in-production-use-strong-random-string",
}


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

    @model_validator(mode="after")
    def _reject_weak_secret_key(self) -> "Settings":
        """Fail startup if SECRET_KEY is left at a known weak default."""
        if self.SECRET_KEY.strip() in _WEAK_SECRET_KEYS:
            raise ValueError(
                "SECRET_KEY is set to a known weak default value; set a "
                "strong, unique SECRET_KEY in backend/config/.env"
            )
        return self

    class Config:
        """Pydantic settings config."""

        env_file = str(_ENV_FILE)
        case_sensitive = True
