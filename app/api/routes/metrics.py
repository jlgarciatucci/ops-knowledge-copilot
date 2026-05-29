from fastapi import APIRouter, Depends
import asyncpg
from app.api.dependencies import db_dep
from app.core.errors import AppError
from app.schemas.metrics import QueryMetrics

router = APIRouter(prefix='/metrics', tags=['metrics'])


@router.get('/{query_id}', response_model=QueryMetrics)
async def get_query_metrics(query_id: str, conn: asyncpg.Connection = Depends(db_dep)) -> QueryMetrics:
    row = await conn.fetchrow(
        '''
        SELECT id, question, latency_ms, prompt_tokens, completion_tokens, total_tokens,
               estimated_cost_usd, groundedness_score, model_name
        FROM query_logs
        WHERE id = $1::uuid
        ''',
        query_id,
    )
    if not row:
        raise AppError('query_id not found', status_code=404)
    return QueryMetrics(
        query_id=str(row['id']),
        question=row['question'],
        latency_ms=row['latency_ms'],
        prompt_tokens=row['prompt_tokens'],
        completion_tokens=row['completion_tokens'],
        total_tokens=row['total_tokens'],
        estimated_cost_usd=float(row['estimated_cost_usd'] or 0),
        groundedness_score=float(row['groundedness_score']) if row['groundedness_score'] is not None else None,
        model_name=row['model_name'],
    )
