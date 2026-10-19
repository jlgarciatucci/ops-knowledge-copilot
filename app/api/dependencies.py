from collections.abc import AsyncGenerator
import re

import asyncpg
from fastapi import Depends, Header, HTTPException

from app.core.config import Settings, get_settings
from app.db.database import get_pool


async def db_dep() -> AsyncGenerator[asyncpg.Connection, None]:
    pool = get_pool()
    async with pool.acquire() as conn:
        yield conn


def settings_dep(settings: Settings = Depends(get_settings)) -> Settings:
    return settings


def user_email_dep(x_user_email: str | None = Header(default=None)) -> str:
    # Only trusted API-key-authenticated frontend can set this header.
    email = (x_user_email or '').strip().lower()
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email) or len(email) > 254:
        raise HTTPException(status_code=400, detail='Verified user email is required')
    return email
