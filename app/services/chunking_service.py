import re
from dataclasses import dataclass


@dataclass
class TextChunk:
    content: str
    section: str | None
    chunk_index: int


class ChunkingService:
    def __init__(self, max_chars: int = 1800, overlap_chars: int = 250):
        self.max_chars = max_chars
        self.overlap_chars = overlap_chars

    def chunk_markdown(self, text: str) -> list[TextChunk]:
        sections = self._split_sections(text)
        chunks: list[TextChunk] = []
        for section_title, section_text in sections:
            chunks.extend(self._chunk_section(section_title, section_text, len(chunks)))
        return chunks

    def _split_sections(self, text: str) -> list[tuple[str | None, str]]:
        parts = re.split(r'(?m)^(#{1,3}\s+.+)$', text)
        if len(parts) == 1:
            return [(None, text.strip())]
        sections: list[tuple[str | None, str]] = []
        preamble = parts[0].strip()
        if preamble:
            sections.append((None, preamble))
        for i in range(1, len(parts), 2):
            title = parts[i].replace('#', '').strip()
            body = parts[i + 1].strip() if i + 1 < len(parts) else ''
            if body:
                sections.append((title, f'{parts[i]}\n\n{body}'))
        return sections

    def _chunk_section(self, title: str | None, content: str, start_index: int) -> list[TextChunk]:
        if len(content) <= self.max_chars:
            return [TextChunk(content=content, section=title, chunk_index=start_index)]
        chunks: list[TextChunk] = []
        pos = 0
        idx = start_index
        while pos < len(content):
            end = min(pos + self.max_chars, len(content))
            if end < len(content):
                boundary = content.rfind('\n', pos, end)
                if boundary > pos + self.max_chars // 2:
                    end = boundary
            chunk_text = content[pos:end].strip()
            if chunk_text:
                chunks.append(TextChunk(content=chunk_text, section=title, chunk_index=idx))
                idx += 1
            if end >= len(content):
                break
            pos = max(0, end - self.overlap_chars)
        return chunks
