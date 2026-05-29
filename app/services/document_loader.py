from pathlib import Path


class DocumentLoader:
    supported_suffixes = {'.md', '.txt'}

    def load_file(self, path: Path) -> str:
        if path.suffix.lower() not in self.supported_suffixes:
            raise ValueError(f'Unsupported file type: {path.suffix}')
        return path.read_text(encoding='utf-8')

    def iter_sample_docs(self, folder: str = 'sample_docs') -> list[Path]:
        root = Path(folder)
        if not root.exists():
            return []
        return sorted(p for p in root.iterdir() if p.suffix.lower() in self.supported_suffixes)
