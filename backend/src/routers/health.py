"""Health check endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    """Health check endpoint for monitoring."""
    return {
        "status": "ok",
        "version": "0.1.0",
        "environment": "development",
    }


@router.get("/ready")
async def readiness():
    """Readiness probe for Kubernetes deployment."""
    return {
        "ready": True,
        "database": "checking...",
        "cache": "checking...",
    }
