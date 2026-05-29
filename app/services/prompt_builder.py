class PromptBuilder:
    def build(self, question: str, chunks: list[dict]) -> str:
        context_blocks = []
        for i, chunk in enumerate(chunks, start=1):
            context_blocks.append(
                f"[SOURCE {i}]\n"
                f"Document: {chunk['filename']}\n"
                f"Section: {chunk.get('section') or 'Unknown'}\n"
                f"Chunk ID: {chunk['chunk_id']}\n"
                f"Content:\n{chunk['content']}"
            )
        context = '\n\n---\n\n'.join(context_blocks)
        return f"""
You are an operations knowledge assistant.

Answer the user question using only the provided context.
If the context does not contain enough evidence, say exactly:
"I do not have enough information in the provided documents to answer this question."

Return a concise operational answer. Mention the most relevant source sections.

Context:
{context}

Question:
{question}
""".strip()
