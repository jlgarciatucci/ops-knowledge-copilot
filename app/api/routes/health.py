from fastapi import APIRouter, Depends
import asyncpg
from app.api.dependencies import db_dep

router = APIRouter(prefix='/health', tags=['health'])


@router.get('')
async def health(conn: asyncpg.Connection = Depends(db_dep)) -> dict:
    value = await conn.fetchval('SELECT 1')
    return {'status': 'ok', 'database': value == 1}
