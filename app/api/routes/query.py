from fastapi import APIRouter, Depends
import asyncpg
from app.api.dependencies import db_dep, settings_dep
from app.core.config import Settings
from app.schemas.query import QueryRequest, QueryResponse
from app.services.rag_service import RagService

router = APIRouter(prefix='/query', tags=['query'])


@router.post('', response_model=QueryResponse)
async def query_rag(
    payload: QueryRequest,
    conn: asyncpg.Connection = Depends(db_dep),
    settings: Settings = Depends(settings_dep),
) -> QueryResponse:
    service = RagService(conn, settings)
    result = await service.answer(payload.question, payload.top_k, payload.filters)
    return QueryResponse(**result)
