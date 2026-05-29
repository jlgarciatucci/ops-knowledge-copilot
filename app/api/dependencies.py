from fastapi import Depends
import asyncpg
from app.core.config import Settings, get_settings
from app.db.database import get_db


def settings_dep() -> Settings:
    return get_settings()


async def db_dep() -> asyncpg.Connection:
    async for conn in get_db():
        return conn
    raise RuntimeError('Database connection unavailable')
