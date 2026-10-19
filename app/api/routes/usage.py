from fastapi import APIRouter, Depends
import asyncpg
from app.api.dependencies import db_dep, user_email_dep

router = APIRouter(prefix='/usage', tags=['usage'])


@router.get('/me')
async def my_usage(
    conn: asyncpg.Connection = Depends(db_dep),
    user_email: str = Depends(user_email_dep),
):
    row = await conn.fetchrow(
        """SELECT COUNT(*)::int AS queries,
                  COALESCE(SUM(total_tokens), 0)::bigint AS tokens,
                  COALESCE(SUM(estimated_cost_usd), 0)::float8 AS cost,
                  ROUND(AVG(latency_ms))::int AS avg_latency_ms,
                  MAX(created_at) AS last_active
           FROM query_logs WHERE user_email=$1""",
        user_email,
    )
    recent = await conn.fetch(
        """SELECT id, question, created_at, latency_ms, total_tokens
           FROM query_logs WHERE user_email=$1
           ORDER BY created_at DESC LIMIT 20""",
        user_email,
    )
    return {
        'queries': row['queries'], 'tokens': int(row['tokens']),
        'estimated_cost_usd': float(row['cost']),
        'avg_latency_ms': row['avg_latency_ms'],
        'last_active': row['last_active'].isoformat() if row['last_active'] else None,
        'recent': [
            {'id': str(r['id']), 'question': r['question'],
             'created_at': r['created_at'].isoformat(),
             'latency_ms': r['latency_ms'], 'total_tokens': r['total_tokens']}
            for r in recent
        ],
    }
