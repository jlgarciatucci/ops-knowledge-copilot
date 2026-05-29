from collections.abc import AsyncGenerator

import asyncpg
from fastapi import Depends

from app.core.config import Settings, get_settings
from app.db.database import get_pool


async def db_dep() -> AsyncGenerator[asyncpg.Connection, None]:
    pool = get_pool()

    async with pool.acquire() as conn:
        yield conn


def settings_dep(settings: Settings = Depends(get_settings)) -> Settings:
    return settings