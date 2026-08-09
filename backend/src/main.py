"""PyRoboSimulator backend API server."""

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import Settings
from db.session import get_db
from routers import auth, health, results, simulations, visualization
from services.health import check_cache, check_database
from services.monitoring import PrometheusMiddleware, metrics_endpoint

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifespan: startup and shutdown."""
    logger.info("PyRoboSimulator backend starting...")
    yield
    logger.info("PyRoboSimulator backend shutting down...")


app = FastAPI(
    title="PyRoboSimulator API",
    description="AI-native world simulation platform for robots and autonomous systems",
    version="0.1.0",
    lifespan=lifespan,
)

# Middleware stack
app.add_middleware(PrometheusMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}


@app.get("/ready", tags=["Health"])
async def readiness_check(
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Readiness probe for Kubernetes: actually checks database and cache
    connectivity rather than unconditionally reporting ready."""
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


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint."""
    return await metrics_endpoint()


# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions."""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1", tags=["Auth"])
app.include_router(simulations.router, prefix="/api/v1")
app.include_router(results.router, prefix="/api/v1")
app.include_router(visualization.router)  # WebSocket routes (no prefix)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
