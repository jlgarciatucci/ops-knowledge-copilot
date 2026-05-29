import re


class GroundednessService:
    def score(self, answer: str, chunks: list[dict]) -> float:
        answer_tokens = set(re.findall(r'[a-zA-Z0-9_]+', answer.lower()))
        context_tokens = set()
        for chunk in chunks:
            context_tokens.update(re.findall(r'[a-zA-Z0-9_]+', chunk['content'].lower()))
        if not answer_tokens:
            return 0.0
        useful = {t for t in answer_tokens if len(t) > 3}
        if not useful:
            return 0.0
        return round(len(useful & context_tokens) / len(useful), 3)
