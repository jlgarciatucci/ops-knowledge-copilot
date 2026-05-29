# Interview Talking Points

## 60-second explanation

I built Ops Knowledge Copilot as a production-style RAG application. It has a Streamlit chat frontend, a FastAPI backend, Supabase Postgres with pgvector, NVIDIA NIM embeddings using `nv-embedcode-7b-v1`, and Gemini Flash for answer generation. The backend handles document ingestion, chunking, semantic retrieval, reranking, prompt construction, source citations, observability and feedback.

The sample domain is operational procedures, but the architecture is domain-independent. It could be adapted to airline operations, engineering manuals, safety procedures, IT support, maintenance knowledge bases or internal company documentation.

## Why this project is credible

- It is not a notebook.
- It has a deployed app architecture.
- It separates frontend, backend, database and model providers.
- It uses real API boundaries.
- It stores observability and feedback.
- It uses metadata filtering and source citations.

## How to explain the provider choices

I used NVIDIA NIM for embeddings because it demonstrates integration with modern hosted AI infrastructure and a specialized embedding model. I used Gemini Flash for chat because it is fast and practical for a free or low-cost portfolio demo. Supabase gives me a managed Postgres database with pgvector, which is ideal for demonstrating vector search without running my own database server.

## How to explain the pgvector dimension decision

NV-EmbedCode uses high-dimensional embeddings, so I store them as `VECTOR(4096)`. For this small portfolio dataset I use exact cosine search instead of an ANN index. In production, if the dataset grew, I would consider dimensionality reduction, an embedding model with fewer dimensions, a high-dimensional indexing strategy, or a dedicated vector database depending on latency, recall and cost requirements.
