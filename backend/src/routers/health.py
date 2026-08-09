"""Health check endpoints."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import Settings
from db.session import get_db
from services.health import check_cache, check_database

router = APIRouter()
settings = Settings()


@router.get("/health")
async def health():
    """Liveness check: is the process up and serving requests."""
    return {
        "status": "ok",
        "version": "0.1.0",
        "environment": "development" if settings.DEBUG else "production",
    }


@router.get("/ready")
async def readiness(
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Readiness probe for Kubernetes deployment.

    Actually checks database and cache connectivity rather than
    unconditionally reporting ready -- a pod should not receive traffic
    if either dependency is unreachable.
    """
    database_ok = await check_database(db)
    cache_ok = await check_cache()
    ready = database_ok and cache_ok

    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "ready": ready,
        "database": "ok" if database_ok else "unavailable",
        "cache": "ok" if cache_ok else "unavailable",
    }
