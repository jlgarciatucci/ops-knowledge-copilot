import json
import uuid
import asyncpg


def vector_literal(values: list[float]) -> str:
    return '[' + ','.join(f'{v:.8f}' for v in values) + ']'


class VectorStore:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def create_document(self, filename: str, metadata: dict) -> str:
        row = await self.conn.fetchrow(
            '''
            INSERT INTO documents (filename, document_type, department, source_uri, metadata)
            VALUES ($1, $2, $3, $4, $5::jsonb)
            RETURNING id
            ''',
            filename,
            metadata.get('document_type', 'procedure'),
            metadata.get('department', 'operations'),
            metadata.get('source_uri'),
            json.dumps(metadata),
        )
        return str(row['id'])

    async def add_chunks(self, document_id: str, filename: str, chunks: list, embeddings: list[list[float]], base_metadata: dict) -> int:
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            metadata = dict(base_metadata)
            metadata.update({'filename': filename, 'section': chunk.section, 'chunk_index': chunk.chunk_index})
            await self.conn.execute(
                '''
                INSERT INTO document_chunks (document_id, chunk_index, content, section, metadata, embedding)
                VALUES ($1::uuid, $2, $3, $4, $5::jsonb, $6::vector)
                ''',
                document_id,
                chunk.chunk_index,
                chunk.content,
                chunk.section,
                json.dumps(metadata),
                vector_literal(embedding),
            )
        return len(chunks)

    async def search(self, query_embedding: list[float], top_k: int, filters: dict[str, str] | None = None) -> list[dict]:
        where = []
        args: list = [vector_literal(query_embedding), top_k]
        if filters:
            for key, value in filters.items():
                args.append(value)
                where.append(f"c.metadata->>'{key}' = ${len(args)}")
        where_sql = 'WHERE ' + ' AND '.join(where) if where else ''
        rows = await self.conn.fetch(
            f'''
            SELECT
                c.id AS chunk_id,
                c.document_id,
                d.filename,
                c.content,
                c.section,
                c.metadata,
                1 - (c.embedding <=> $1::vector) AS similarity
            FROM document_chunks c
            JOIN documents d ON d.id = c.document_id
            {where_sql}
            ORDER BY c.embedding <=> $1::vector
            LIMIT $2
            ''',
            *args,
        )
        return [dict(row) for row in rows]
