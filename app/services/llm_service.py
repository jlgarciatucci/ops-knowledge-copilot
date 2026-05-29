from dataclasses import dataclass

import httpx
from openai import AsyncOpenAI

from app.core.config import Settings
from app.core.errors import AppError


@dataclass
class LLMResult:
    answer: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model_name: str
    estimated_cost_usd: float


class LLMService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.provider = settings.chat_provider.lower().strip()
        self._openai_client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    async def generate(self, prompt: str, chunks: list[dict]) -> LLMResult:
        if self.provider == 'gemini':
            return await self._generate_gemini(prompt)
        if self.provider == 'openai':
            return await self._generate_openai(prompt)
        return self._generate_local(prompt, chunks)

    async def _generate_gemini(self, prompt: str) -> LLMResult:
        if not self.settings.gemini_api_key:
            raise AppError('GEMINI_API_KEY is required when CHAT_PROVIDER=gemini', status_code=500)

        model = self.settings.gemini_chat_model
        url = f"{self.settings.gemini_base_url.rstrip('/')}/models/{model}:generateContent"
        params = {'key': self.settings.gemini_api_key}
        payload = {
            'contents': [
                {
                    'role': 'user',
                    'parts': [{'text': prompt}],
                }
            ],
            'generationConfig': {
                'temperature': 0.1,
                'topP': 0.8,
                'maxOutputTokens': 900,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=90) as client:
                response = await client.post(url, params=params, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:600] if exc.response is not None else str(exc)
            raise AppError(f'Gemini chat request failed: {detail}', status_code=502) from exc
        except httpx.HTTPError as exc:
            raise AppError(f'Gemini chat request failed: {exc}', status_code=502) from exc

        answer = self._extract_gemini_text(data)
        usage = data.get('usageMetadata', {}) or {}
        prompt_tokens = int(usage.get('promptTokenCount', 0) or len(prompt) // 4)
        completion_tokens = int(usage.get('candidatesTokenCount', 0) or len(answer) // 4)
        total_tokens = int(usage.get('totalTokenCount', prompt_tokens + completion_tokens) or prompt_tokens + completion_tokens)
        return LLMResult(
            answer=answer,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            model_name=model,
            estimated_cost_usd=self._estimate_cost(prompt_tokens, completion_tokens, provider='gemini'),
        )

    def _extract_gemini_text(self, data: dict) -> str:
        candidates = data.get('candidates') or []
        if not candidates:
            return 'I do not have enough information in the provided documents to answer this question.'
        parts = candidates[0].get('content', {}).get('parts', [])
        text_parts = [part.get('text', '') for part in parts if part.get('text')]
        return '\n'.join(text_parts).strip() or 'I do not have enough information in the provided documents to answer this question.'

    async def _generate_openai(self, prompt: str) -> LLMResult:
        if not self._openai_client:
            raise AppError('OPENAI_API_KEY is required when CHAT_PROVIDER=openai', status_code=500)

        response = await self._openai_client.chat.completions.create(
            model=self.settings.openai_chat_model,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.1,
        )
        usage = response.usage
        prompt_tokens = usage.prompt_tokens if usage else len(prompt) // 4
        completion_tokens = usage.completion_tokens if usage else len(response.choices[0].message.content or '') // 4
        total_tokens = usage.total_tokens if usage else prompt_tokens + completion_tokens
        return LLMResult(
            answer=response.choices[0].message.content or '',
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            model_name=self.settings.openai_chat_model,
            estimated_cost_usd=self._estimate_cost(prompt_tokens, completion_tokens, provider='openai'),
        )

    def _generate_local(self, prompt: str, chunks: list[dict]) -> LLMResult:
        answer = self._mock_answer(chunks)
        approx_prompt_tokens = len(prompt) // 4
        approx_completion_tokens = len(answer) // 4
        return LLMResult(
            answer=answer,
            prompt_tokens=approx_prompt_tokens,
            completion_tokens=approx_completion_tokens,
            total_tokens=approx_prompt_tokens + approx_completion_tokens,
            model_name='local-mock-llm',
            estimated_cost_usd=0.0,
        )

    def _mock_answer(self, chunks: list[dict]) -> str:
        if not chunks:
            return 'I do not have enough information in the provided documents to answer this question.'
        best = chunks[0]
        excerpt = best['content'].strip().replace('\n', ' ')
        excerpt = excerpt[:900] + ('...' if len(excerpt) > 900 else '')
        return (
            f"Based on the retrieved operational procedure, the most relevant guidance is in "
            f"'{best['filename']}' / section '{best.get('section') or 'Unknown'}'. "
            f"Relevant excerpt: {excerpt}"
        )

    def _estimate_cost(self, input_tokens: int, output_tokens: int, provider: str) -> float:
        # Approximate demo costs. Free-tier usage may be zero-cost but limits can change.
        if provider == 'gemini':
            return 0.0
        if provider == 'openai':
            input_per_1m = 0.15
            output_per_1m = 0.60
            return round((input_tokens / 1_000_000) * input_per_1m + (output_tokens / 1_000_000) * output_per_1m, 6)
        return 0.0
