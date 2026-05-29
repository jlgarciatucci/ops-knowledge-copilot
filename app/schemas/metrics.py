from pydantic import BaseModel


class QueryMetrics(BaseModel):
    query_id: str
    question: str
    latency_ms: int | None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    groundedness_score: float | None
    model_name: str | None
