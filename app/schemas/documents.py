from pydantic import BaseModel, Field


class DocumentIngestResponse(BaseModel):
    document_id: str
    filename: str
    chunks_indexed: int


class SampleIngestResponse(BaseModel):
    documents_ingested: int
    chunks_indexed: int
