import re


def tokenize(text: str) -> set[str]:
    return set(re.findall(r'[a-zA-Z0-9_]+', text.lower()))


class SimpleReranker:
    def rerank(self, question: str, chunks: list[dict]) -> list[dict]:
        q_tokens = tokenize(question)
        for chunk in chunks:
            c_tokens = tokenize(chunk['content'])
            overlap = len(q_tokens & c_tokens) / max(len(q_tokens), 1)
            vector_score = float(chunk['similarity'])
            chunk['rerank_score'] = round(0.75 * vector_score + 0.25 * overlap, 6)
        return sorted(chunks, key=lambda x: x['rerank_score'], reverse=True)
