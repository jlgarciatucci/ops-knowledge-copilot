from fastapi import APIRouter
from app.db.database import get_db_pool

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    try:
        pool = get_db_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")

        return {
            "status": "ok",
            "api": "running",
            "database": "connected"
        }

    except Exception as exc:
        return {
            "status": "degraded",
            "api": "running",
            "database": "error",
            "error": str(exc)
        }