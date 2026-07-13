from pathlib import Path


class LocalProvider:
    """Reads standards documents from the local filesystem."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    async def get_doc(self, path: str) -> str | None:
        full_path = self._root / path
        try:
            return full_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None

    async def list_docs(self, prefix: str = "") -> list[str]:
        search_root = self._root / prefix if prefix else self._root
        if not search_root.exists():
            return []
        return sorted(str(p.relative_to(self._root)) for p in search_root.rglob("*.md"))
