from pathlib import Path
from fastapi import APIRouter, Depends, File, UploadFile
import asyncpg
from app.api.dependencies import db_dep, settings_dep
from app.core.config import Settings
from app.core.errors import AppError
from app.schemas.documents import DocumentIngestResponse, SampleIngestResponse
from app.services.chunking_service import ChunkingService
from app.services.document_loader import DocumentLoader
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore

router = APIRouter(prefix='/documents', tags=['documents'])


async def ingest_text(filename: str, text: str, conn: asyncpg.Connection, settings: Settings, metadata: dict) -> DocumentIngestResponse:
    chunker = ChunkingService(settings.max_chunk_chars, settings.chunk_overlap_chars)
    chunks = chunker.chunk_markdown(text)
    embeddings = await EmbeddingService(settings).embed_many([c.content for c in chunks])
    store = VectorStore(conn)
    document_id = await store.create_document(filename, metadata)
    count = await store.add_chunks(document_id, filename, chunks, embeddings, metadata)
    return DocumentIngestResponse(document_id=document_id, filename=filename, chunks_indexed=count)


@router.post('/upload', response_model=DocumentIngestResponse)
async def upload_document(
    file: UploadFile = File(...),
    conn: asyncpg.Connection = Depends(db_dep),
    settings: Settings = Depends(settings_dep),
) -> DocumentIngestResponse:
    if not file.filename:
        raise AppError('File name is required', status_code=400)
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {'.md', '.txt'}:
        raise AppError('Only .md and .txt files are supported in this MVP', status_code=400)
    raw = await file.read()
    text = raw.decode('utf-8')
    metadata = {'document_type': 'procedure', 'department': 'operations', 'source_uri': f'upload://{file.filename}'}
    return await ingest_text(file.filename, text, conn, settings, metadata)


@router.post('/ingest-sample', response_model=SampleIngestResponse)
async def ingest_sample_documents(
    conn: asyncpg.Connection = Depends(db_dep),
    settings: Settings = Depends(settings_dep),
) -> SampleIngestResponse:
    loader = DocumentLoader()
    docs = loader.iter_sample_docs('sample_docs')
    total_chunks = 0
    for path in docs:
        metadata = infer_metadata(path.name)
        text = loader.load_file(path)
        result = await ingest_text(path.name, text, conn, settings, metadata)
        total_chunks += result.chunks_indexed
    return SampleIngestResponse(documents_ingested=len(docs), chunks_indexed=total_chunks)


def infer_metadata(filename: str) -> dict:
    if 'safety' in filename:
        return {'document_type': 'safety_procedure', 'department': 'safety', 'source_uri': f'sample_docs/{filename}'}
    if 'maintenance' in filename:
        return {'document_type': 'maintenance_procedure', 'department': 'maintenance', 'source_uri': f'sample_docs/{filename}'}
    if 'it_' in filename:
        return {'document_type': 'it_outage_procedure', 'department': 'it_operations', 'source_uri': f'sample_docs/{filename}'}
    if 'incident' in filename:
        return {'document_type': 'incident_response', 'department': 'operations_control', 'source_uri': f'sample_docs/{filename}'}
    if 'handover' in filename:
        return {'document_type': 'shift_handover', 'department': 'operations', 'source_uri': f'sample_docs/{filename}'}
    return {'document_type': 'procedure', 'department': 'operations', 'source_uri': f'sample_docs/{filename}'}
