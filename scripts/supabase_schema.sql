-- Run this in Supabase SQL Editor before deploying the API.
-- It enables pgvector and creates the tables used by Ops Knowledge Copilot.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL,
    document_type TEXT DEFAULT 'procedure',
    department TEXT DEFAULT 'operations',
    source_uri TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    section TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding VECTOR(4096) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- NV-EmbedCode returns 4096-dimensional vectors.
-- pgvector can store VECTOR(4096), but standard ANN indexes such as ivfflat/hnsw
-- are limited to lower dimensions for the vector type. For this small portfolio demo,
-- exact cosine search with ORDER BY embedding <=> query is used without an ANN index.
-- For large-scale production, use dimensionality reduction, a lower-dimensional model,
-- external vector DB, or an indexing strategy compatible with high-dimensional vectors.

CREATE INDEX IF NOT EXISTS idx_document_chunks_metadata ON document_chunks USING gin (metadata);
CREATE INDEX IF NOT EXISTS idx_documents_metadata ON documents USING gin (metadata);

CREATE TABLE IF NOT EXISTS query_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question TEXT NOT NULL,
    answer TEXT,
    retrieved_chunk_ids UUID[] DEFAULT '{}',
    latency_ms INT,
    prompt_tokens INT DEFAULT 0,
    completion_tokens INT DEFAULT 0,
    total_tokens INT DEFAULT 0,
    estimated_cost_usd NUMERIC DEFAULT 0,
    groundedness_score NUMERIC,
    model_name TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID REFERENCES query_logs(id) ON DELETE CASCADE,
    rating INT CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
