import ssl

import asyncpg

from app.core.config import get_settings

_pool: asyncpg.Pool | None = None


async def init_db_pool() -> None:
    global _pool

    if _pool is not None:
        return

    settings = get_settings()

    ssl_context = ssl.create_default_context()

    _pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=1,
        max_size=5,
        ssl=ssl_context,
    )


async def close_db_pool() -> None:
    global _pool

    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool has not been initialized.")
    return _pool