# Production Deployment Guide

This project is configured for the following portfolio-friendly production stack:

```text
Streamlit Community Cloud
→ FastAPI API on Render
→ Supabase Postgres + pgvector
→ NVIDIA NIM embeddings: nvidia/nv-embedcode-7b-v1
→ Google Gemini Flash chat model
```

## 1. Supabase database

1. Create a Supabase project.
2. Go to **SQL Editor**.
3. Run `scripts/supabase_schema.sql`.
4. Copy the pooled Postgres connection string.
5. In Render, set:

```env
DATABASE_URL=postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-eu-west-1.pooler.supabase.com:6543/postgres
DATABASE_SSL=true
```

## 2. Important pgvector note for NVIDIA NV-EmbedCode

`nv-embedcode-7b-v1` produces high-dimensional vectors. This project stores them as:

```sql
embedding VECTOR(4096)
```

The demo intentionally uses exact cosine search without an ANN index. This is acceptable for a small portfolio dataset and avoids index-dimension issues. For larger production systems, consider dimensionality reduction, a lower-dimensional embedding model, an external vector database, or an indexing strategy compatible with high-dimensional vectors.

## 3. Render backend

Create a Render web service connected to this GitHub repo.

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Environment variables:

```env
ENVIRONMENT=production
DATABASE_URL=your_supabase_pooler_url
DATABASE_SSL=true
EMBEDDING_PROVIDER=nvidia
NVIDIA_API_KEY=your_nvidia_nim_key
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_EMBEDDING_MODEL=nvidia/nv-embedcode-7b-v1
EMBEDDING_DIM=4096
CHAT_PROVIDER=gemini
GEMINI_API_KEY=your_google_gemini_key
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta
GEMINI_CHAT_MODEL=gemini-2.0-flash
CORS_ORIGINS=*
```

After deployment, verify:

```text
https://your-render-service.onrender.com/health
https://your-render-service.onrender.com/docs
```

## 4. Streamlit frontend

Deploy `streamlit_app.py` to Streamlit Community Cloud.

Add this secret:

```toml
API_BASE_URL = "https://your-render-service.onrender.com"
```

## 5. First production smoke test

1. Open the Streamlit app.
2. Click **Health check**.
3. Click **Ingest sample documents**.
4. Ask:

```text
What should a technician do if abnormal vibration occurs after pump startup?
```

5. Confirm the answer includes sources and observability metadata.
6. Submit feedback.
