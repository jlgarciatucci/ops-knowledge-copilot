from contextlib import asynccontextmanager
import hmac

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import documents, feedback, health, metrics, query, usage
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
    description='RAG backend with vector search, usage tracking and feedback.',
    version='0.3.0',
    lifespan=lifespan,
)


@app.middleware('http')
async def require_frontend_credential(request: Request, call_next):
    # The API is called server-to-server by Streamlit; browsers never receive this secret.
    public_paths = {'/', '/health', '/openapi.json'}
    if request.url.path not in public_paths and not request.url.path.startswith('/docs'):
        expected = settings.frontend_api_key
        if not expected or not hmac.compare_digest(
            request.headers.get('x-app-key', ''), expected
        ):
            return JSONResponse({'detail': 'Unauthorized'}, status_code=401)
    return await call_next(request)


allowed_origins = [o.strip() for o in settings.cors_origins.split(',') if o.strip()]
app.add_middleware(
    CORSMiddleware, allow_origins=allowed_origins,
    allow_credentials=False, allow_methods=['*'], allow_headers=['*'],
)
app.add_exception_handler(AppError, app_error_handler)
for router in (health.router, documents.router, query.router, feedback.router, metrics.router, usage.router):
    app.include_router(router)


@app.get('/')
async def root():
    return {'name': 'Ops Knowledge Copilot API', 'status': 'running', 'health': '/health'}
