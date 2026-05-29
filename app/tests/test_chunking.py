from app.services.chunking_service import ChunkingService


def test_chunking_returns_chunks():
    text = '# Title\n\n## Section A\n\nThis is a test document. ' * 20
    chunks = ChunkingService(max_chars=500, overlap_chars=50).chunk_markdown(text)
    assert chunks
    assert chunks[0].content
