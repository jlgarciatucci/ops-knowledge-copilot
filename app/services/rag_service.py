import time

import asyncpg

from app.core.config import Settings
from app.services.embedding_service import EmbeddingService
from app.services.groundedness_service import GroundednessService
from app.services.llm_service import LLMService
from app.services.observability_service import ObservabilityService
from app.services.prompt_builder import PromptBuilder
from app.services.reranker import SimpleReranker
from app.services.vector_store import VectorStore


class RagService:
    def __init__(self, conn: asyncpg.Connection, settings: Settings):
        self.conn = conn
        self.settings = settings
        self.embedding_service = EmbeddingService(settings)
        self.vector_store = VectorStore(conn)
        self.reranker = SimpleReranker()
        self.prompt_builder = PromptBuilder()
        self.llm_service = LLMService(settings)
        self.groundedness_service = GroundednessService()
        self.observability_service = ObservabilityService(conn)

    async def answer(self, question: str, top_k: int, filters: dict[str, str] | None) -> dict:
        start = time.perf_counter()

        # NVIDIA NV-EmbedCode requires input_type='query' for user questions.
        query_embedding = await self.embedding_service.embed(question, input_type='query')

        retrieved = await self.vector_store.search(query_embedding, top_k=top_k, filters=filters)
        reranked = self.reranker.rerank(question, retrieved)
        prompt = self.prompt_builder.build(question, reranked)
        llm_result = await self.llm_service.generate(prompt, reranked)
        groundedness = (
            self.groundedness_service.score(llm_result.answer, reranked)
            if self.settings.enable_groundedness_check
            else None
        )
        latency_ms = int((time.perf_counter() - start) * 1000)
        query_id = await self.observability_service.log_query(
            question=question,
            answer=llm_result.answer,
            chunks=reranked,
            latency_ms=latency_ms,
            llm=llm_result,
            groundedness_score=groundedness,
        )
        return {
            'query_id': query_id,
            'answer': llm_result.answer,
            'sources': [
                {
                    'chunk_id': str(c['chunk_id']),
                    'document_id': str(c['document_id']),
                    'filename': c['filename'],
                    'section': c.get('section'),
                    'similarity': round(float(c['similarity']), 6),
                    'rerank_score': round(float(c['rerank_score']), 6),
                    'excerpt': c['content'][:350].replace('\n', ' '),
                }
                for c in reranked
            ],
            'observability': {
                'latency_ms': latency_ms,
                'prompt_tokens': llm_result.prompt_tokens,
                'completion_tokens': llm_result.completion_tokens,
                'total_tokens': llm_result.total_tokens,
                'estimated_cost_usd': llm_result.estimated_cost_usd,
                'groundedness_score': groundedness,
                'model_name': llm_result.model_name,
            },
        }
