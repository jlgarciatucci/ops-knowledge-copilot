from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
    app_name: str = 'Ops Knowledge Copilot'
    environment: str = 'local'
    database_url: str = 'postgresql://rag_user:rag_password@localhost:5432/ops_rag'
    database_ssl: bool = False
    embedding_provider: str = 'local'
    chat_provider: str = 'local'
    nvidia_api_key: str | None = None
    nvidia_base_url: str = 'https://integrate.api.nvidia.com/v1'
    nvidia_embedding_model: str = 'nvidia/nv-embedcode-7b-v1'
    gemini_api_key: str | None = None
    gemini_base_url: str = 'https://generativelanguage.googleapis.com/v1beta'
    gemini_chat_model: str = 'gemini-2.0-flash'
    openai_api_key: str | None = None
    openai_chat_model: str = 'gpt-4o-mini'
    openai_embedding_model: str = 'text-embedding-3-small'
    embedding_dim: int = 4096
    top_k_default: int = Field(default=5, ge=1, le=20)
    max_chunk_chars: int = Field(default=1800, ge=500)
    chunk_overlap_chars: int = Field(default=250, ge=0)
    log_level: str = 'INFO'
    enable_cost_tracking: bool = True
    enable_groundedness_check: bool = True
    cors_origins: str = '*'
    api_public_base_url: str | None = None
    # Share only between the trusted Streamlit server and FastAPI.
    # Required whenever user identity/usage tracking is enabled.
    frontend_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
