import json
import asyncpg
from app.services.llm_service import LLMResult


class ObservabilityService:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def log_query(self, question: str, answer: str, chunks: list[dict], latency_ms: int, llm: LLMResult, groundedness_score: float | None) -> str:
        chunk_ids = [str(c['chunk_id']) for c in chunks]
        row = await self.conn.fetchrow(
            '''
            INSERT INTO query_logs (
                question, answer, retrieved_chunk_ids, latency_ms,
                prompt_tokens, completion_tokens, total_tokens,
                estimated_cost_usd, groundedness_score, model_name, metadata
            )
            VALUES ($1, $2, $3::uuid[], $4, $5, $6, $7, $8, $9, $10, $11::jsonb)
            RETURNING id
            ''',
            question,
            answer,
            chunk_ids,
            latency_ms,
            llm.prompt_tokens,
            llm.completion_tokens,
            llm.total_tokens,
            llm.estimated_cost_usd,
            groundedness_score,
            llm.model_name,
            json.dumps({'source_count': len(chunks)}),
        )
        return str(row['id'])
