import hashlib
import math
import re
from typing import Literal

import httpx
from openai import AsyncOpenAI

from app.core.config import Settings
from app.core.errors import AppError


EmbeddingInputType = Literal['passage', 'query']


class EmbeddingService:
    """Provider-agnostic embedding service.

    NVIDIA NV-EmbedCode requires `input_type`:
    - passage: for document/chunk indexing
    - query: for user search queries
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.provider = settings.embedding_provider.lower().strip()
        self._openai_client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    async def embed(self, text: str, input_type: EmbeddingInputType = 'passage') -> list[float]:
        vectors = await self.embed_many([text], input_type=input_type)
        return vectors[0]

    async def embed_many(
        self,
        texts: list[str],
        input_type: EmbeddingInputType = 'passage',
    ) -> list[list[float]]:
        if not texts:
            return []

        clean_texts = [self._clean_text(t) for t in texts]

        if self.provider == 'nvidia':
            return await self._embed_many_nvidia(clean_texts, input_type=input_type)
        if self.provider == 'openai':
            return await self._embed_many_openai(clean_texts)
        return [self._local_hash_embedding(t) for t in clean_texts]

    async def _embed_many_nvidia(
        self,
        texts: list[str],
        input_type: EmbeddingInputType = 'passage',
    ) -> list[list[float]]:
        if input_type not in ('passage', 'query'):
            raise AppError("NVIDIA input_type must be either 'passage' or 'query'", status_code=500)
        if not self.settings.nvidia_api_key:
            raise AppError('NVIDIA_API_KEY is required when EMBEDDING_PROVIDER=nvidia', status_code=500)

        url = f"{self.settings.nvidia_base_url.rstrip('/')}/embeddings"
        headers = {
            'Authorization': f'Bearer {self.settings.nvidia_api_key}',
            'Content-Type': 'application/json',
        }
        payload = {
            'model': self.settings.nvidia_embedding_model,
            'input': texts,
            'input_type': input_type,
            'encoding_format': 'float',
        }

        try:
            async with httpx.AsyncClient(timeout=90) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:1000] if exc.response is not None else str(exc)
            raise AppError(
                f'NVIDIA embedding request failed for input_type={input_type}: {detail}',
                status_code=502,
            ) from exc
        except httpx.HTTPError as exc:
            raise AppError(
                f'NVIDIA embedding request failed for input_type={input_type}: {exc}',
                status_code=502,
            ) from exc

        embeddings = [item['embedding'] for item in data.get('data', [])]
        if len(embeddings) != len(texts):
            raise AppError(
                f'NVIDIA embedding response size did not match input size: '
                f'expected {len(texts)}, received {len(embeddings)}',
                status_code=502,
            )
        self._validate_dimensions(embeddings)
        return embeddings

    async def _embed_many_openai(self, texts: list[str]) -> list[list[float]]:
        if not self._openai_client:
            raise AppError('OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai', status_code=500)

        kwargs = {
            'model': self.settings.openai_embedding_model,
            'input': texts,
        }
        # OpenAI text-embedding-3 models support the dimensions parameter.
        # Other providers may not, so this remains OpenAI-only.
        if self.settings.openai_embedding_model.startswith('text-embedding-3'):
            kwargs['dimensions'] = self.settings.embedding_dim

        response = await self._openai_client.embeddings.create(**kwargs)
        embeddings = [item.embedding for item in response.data]
        self._validate_dimensions(embeddings)
        return embeddings

    def _validate_dimensions(self, embeddings: list[list[float]]) -> None:
        expected = self.settings.embedding_dim
        for vector in embeddings:
            if len(vector) != expected:
                raise AppError(
                    f'Embedding dimension mismatch: expected {expected}, received {len(vector)}. '
                    'Update EMBEDDING_DIM and recreate the pgvector schema.',
                    status_code=500,
                )

    def _clean_text(self, text: str) -> str:
        cleaned = (text or '').strip()
        if not cleaned:
            # Avoid sending empty strings to external embedding providers.
            return 'empty document chunk'
        return cleaned

    def _local_hash_embedding(self, text: str) -> list[float]:
        # Deterministic local fallback. Good enough for tests and offline demos.
        dim = self.settings.embedding_dim
        vec = [0.0] * dim
        tokens = re.findall(r'[a-zA-Z0-9_]+', text.lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode('utf-8')).digest()
            idx = int.from_bytes(digest[:4], 'big') % dim
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]
