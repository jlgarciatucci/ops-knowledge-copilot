import ssl

import asyncpg

from app.core.config import get_settings

_pool: asyncpg.Pool | None = None


async def init_db_pool() -> None:
    global _pool

    if _pool is not None:
        return

    settings = get_settings()

    # Supabase Session Pooler requires SSL.
    # For this portfolio/demo deployment on Render, we disable certificate
    # verification because the pooler can expose a self-signed/intermediate
    # certificate chain that asyncpg rejects in some environments.
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

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