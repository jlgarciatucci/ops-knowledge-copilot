# Architecture

Ops Knowledge Copilot is a production-style RAG application with a decoupled frontend and backend.

## Components

- **Streamlit frontend**: chat UI, document upload, source display, feedback form.
- **FastAPI backend**: REST API for ingestion, query, feedback, health and metrics.
- **Supabase Postgres + pgvector**: stores documents, chunks, embeddings, query logs and feedback.
- **NVIDIA NIM**: generates embeddings using `nvidia/nv-embedcode-7b-v1`.
- **Google Gemini Flash**: generates final grounded answers.
- **Render**: hosts the FastAPI backend.

## Request flow

```mermaid
sequenceDiagram
    participant User
    participant UI as Streamlit
    participant API as FastAPI
    participant NIM as NVIDIA NIM
    participant DB as Supabase pgvector
    participant Gemini as Gemini Flash

    User->>UI: Ask question
    UI->>API: POST /query
    API->>NIM: Embed question
    NIM-->>API: 4096-dim vector
    API->>DB: Vector similarity search + metadata filters
    DB-->>API: Top-k chunks
    API->>API: Rerank + build prompt
    API->>Gemini: Generate answer
    Gemini-->>API: Answer + token usage
    API->>DB: Log observability
    API-->>UI: Answer + citations + metrics
    UI-->>User: Chat answer
```

## Production design principles

- API routes remain thin.
- RAG orchestration is handled by `RagService`.
- Providers are configurable through environment variables.
- No secrets are committed to the repo.
- Source citations are returned with every answer.
- Observability and feedback are part of the core workflow.
