from pathlib import Path

import asyncpg
from fastapi import APIRouter, Depends, File, UploadFile

from app.api.dependencies import db_dep, settings_dep
from app.core.config import Settings
from app.core.errors import AppError
from app.schemas.documents import DocumentIngestResponse, SampleIngestResponse
from app.services.chunking_service import ChunkingService
from app.services.document_loader import DocumentLoader
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore

router = APIRouter(prefix="/documents", tags=["documents"])


async def ingest_text(
    filename: str,
    text: str,
    conn: asyncpg.Connection,
    settings: Settings,
    metadata: dict,
) -> DocumentIngestResponse:
    chunker = ChunkingService(
        max_chars=settings.max_chunk_chars,
        overlap_chars=settings.chunk_overlap_chars,
    )

    chunks = chunker.chunk_markdown(text)

    if not chunks:
        raise AppError(f"No text chunks were generated for {filename}", status_code=400)

    # NVIDIA nv-embedcode-7b-v1 needs input_type="passage" when indexing documents.
    embeddings = await EmbeddingService(settings).embed_many(
        [chunk.content for chunk in chunks],
        input_type="passage",
    )

    store = VectorStore(conn)

    # Use one transaction so document + chunks are inserted atomically.
    async with conn.transaction():
        document_id = await store.create_document(filename, metadata)
        count = await store.add_chunks(
            document_id=document_id,
            filename=filename,
            chunks=chunks,
            embeddings=embeddings,
            base_metadata=metadata,
        )

    return DocumentIngestResponse(
        document_id=document_id,
        filename=filename,
        chunks_indexed=count,
    )


@router.post("/upload", response_model=DocumentIngestResponse)
async def upload_document(
    file: UploadFile = File(...),
    conn: asyncpg.Connection = Depends(db_dep),
    settings: Settings = Depends(settings_dep),
) -> DocumentIngestResponse:
    if not file.filename:
        raise AppError("File name is required", status_code=400)

    suffix = Path(file.filename).suffix.lower()

    if suffix not in {".md", ".txt"}:
        raise AppError("Only .md and .txt files are supported in this MVP", status_code=400)

    raw = await file.read()

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AppError("Uploaded file must be UTF-8 encoded", status_code=400) from exc

    metadata = {
        "document_type": "procedure",
        "department": "operations",
        "source_uri": f"upload://{file.filename}",
    }

    return await ingest_text(
        filename=file.filename,
        text=text,
        conn=conn,
        settings=settings,
        metadata=metadata,
    )


@router.post("/ingest-sample", response_model=SampleIngestResponse)
async def ingest_sample_documents(
    conn: asyncpg.Connection = Depends(db_dep),
    settings: Settings = Depends(settings_dep),
) -> SampleIngestResponse:
    loader = DocumentLoader()
    docs = loader.iter_sample_docs("sample_docs")

    if not docs:
        raise AppError("No sample documents found in sample_docs/", status_code=404)

    total_chunks = 0
    documents_ingested = 0

    for path in docs:
        metadata = infer_metadata(path.name)
        text = loader.load_file(path)

        result = await ingest_text(
            filename=path.name,
            text=text,
            conn=conn,
            settings=settings,
            metadata=metadata,
        )

        documents_ingested += 1
        total_chunks += result.chunks_indexed

    return SampleIngestResponse(
        documents_ingested=documents_ingested,
        chunks_indexed=total_chunks,
    )


def infer_metadata(filename: str) -> dict:
    lower_name = filename.lower()

    if "safety" in lower_name:
        return {
            "document_type": "safety_procedure",
            "department": "safety",
            "source_uri": f"sample_docs/{filename}",
        }

    if "maintenance" in lower_name:
        return {
            "document_type": "maintenance_procedure",
            "department": "maintenance",
            "source_uri": f"sample_docs/{filename}",
        }

    if "it_" in lower_name:
        return {
            "document_type": "it_outage_procedure",
            "department": "it_operations",
            "source_uri": f"sample_docs/{filename}",
        }

    if "incident" in lower_name:
        return {
            "document_type": "incident_response",
            "department": "operations_control",
            "source_uri": f"sample_docs/{filename}",
        }

    if "handover" in lower_name:
        return {
            "document_type": "shift_handover",
            "department": "operations",
            "source_uri": f"sample_docs/{filename}",
        }

    return {
        "document_type": "procedure",
        "department": "operations",
        "source_uri": f"sample_docs/{filename}",
    }