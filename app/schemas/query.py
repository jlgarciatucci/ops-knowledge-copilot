from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    filters: dict[str, str] | None = None


class SourceCitation(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    section: str | None = None
    similarity: float
    rerank_score: float
    excerpt: str


class ObservabilityPayload(BaseModel):
    latency_ms: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    groundedness_score: float | None
    model_name: str


class QueryResponse(BaseModel):
    query_id: str
    answer: str
    sources: list[SourceCitation]
    observability: ObservabilityPayload
