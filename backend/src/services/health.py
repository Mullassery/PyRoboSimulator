"""Real connectivity checks for readiness probes.

Both the top-level `/ready` (main.py) and `/api/v1/ready` (routers/health.py)
endpoints delegate here so there is exactly one real implementation of
"is the database/cache actually reachable" instead of two independent stubs.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from services.cache import get_redis_client


async def check_database(db: AsyncSession) -> bool:
    """Check database connectivity by running a trivial query.

    Args:
        db: An active database session (see `db.session.get_db`).

    Returns:
        True if the database responded, False otherwise.
    """
    try:
        await db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def check_cache() -> bool:
    """Check Redis connectivity via PING.

    Returns:
        True if Redis responded, False otherwise.
    """
    try:
        client = await get_redis_client()
        return bool(await client.ping())
    except Exception:
        return False
