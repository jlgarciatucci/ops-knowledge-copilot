from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import documents, feedback, health, metrics, query
from app.core.config import get_settings
from app.core.errors import AppError, app_error_handler
from app.core.logging import configure_logging
from app.db.database import close_db_pool, init_db_pool


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    await init_db_pool()
    yield
    await close_db_pool()


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description='Production-style RAG backend with FastAPI, Supabase/Postgres pgvector, observability and feedback.',
    version='0.2.0',
    lifespan=lifespan,
)

allowed_origins = [origin.strip() for origin in settings.cors_origins.split(',') if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.add_exception_handler(AppError, app_error_handler)
app.include_router(health.router)
app.include_router(documents.router)
app.include_router(query.router)
app.include_router(feedback.router)
app.include_router(metrics.router)

@app.get("/")
async def root():
    return {
        "name": "Ops Knowledge Copilot API",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }
