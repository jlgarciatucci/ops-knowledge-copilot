from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Ops Knowledge Copilot'
    environment: str = 'local'

    # Database
    # Local Docker example:
    # postgresql://rag_user:rag_password@db:5432/ops_rag
    # Supabase pooler example:
    # postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-eu-west-1.pooler.supabase.com:6543/postgres
    database_url: str = 'postgresql://rag_user:rag_password@localhost:5432/ops_rag'
    database_ssl: bool = False

    # Provider selection
    # Production target for this portfolio repo:
    #   embeddings: NVIDIA NIM nv-embedcode-7b-v1
    #   chat: Google Gemini Flash
    embedding_provider: str = 'local'  # local | nvidia | openai
    chat_provider: str = 'local'       # local | gemini | openai

    # NVIDIA NIM embeddings
    nvidia_api_key: str | None = None
    nvidia_base_url: str = 'https://integrate.api.nvidia.com/v1'
    nvidia_embedding_model: str = 'nvidia/nv-embedcode-7b-v1'

    # Google Gemini chat
    gemini_api_key: str | None = None
    gemini_base_url: str = 'https://generativelanguage.googleapis.com/v1beta'
    gemini_chat_model: str = 'gemini-2.0-flash'

    # Optional OpenAI fallback
    openai_api_key: str | None = None
    openai_chat_model: str = 'gpt-4o-mini'
    openai_embedding_model: str = 'text-embedding-3-small'

    # NV-EmbedCode returns 4096-dimensional vectors.
    # If you change embedding provider/model, update this and recreate the pgvector schema.
    embedding_dim: int = 4096

    top_k_default: int = Field(default=5, ge=1, le=20)
    max_chunk_chars: int = Field(default=1800, ge=500)
    chunk_overlap_chars: int = Field(default=250, ge=0)

    log_level: str = 'INFO'
    enable_cost_tracking: bool = True
    enable_groundedness_check: bool = True
    cors_origins: str = '*'
    api_public_base_url: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
