from pathlib import Path
from unittest.mock import AsyncMock

from policybot.fetcher import fetch_docs
from policybot.providers.local import LocalProvider


async def test_fetch_docs_returns_contents(tmp_path: Path) -> None:
    (tmp_path / "python.md").write_text("# Python")
    (tmp_path / "typescript.md").write_text("# TypeScript")
    provider = LocalProvider(tmp_path)
    docs = await fetch_docs(provider, ["python.md", "typescript.md"])
    assert docs == {"python.md": "# Python", "typescript.md": "# TypeScript"}


async def test_fetch_docs_skips_missing() -> None:
    provider = AsyncMock()
    provider.get_doc = AsyncMock(side_effect=lambda p: None if p == "missing.md" else "content")
    docs = await fetch_docs(provider, ["existing.md", "missing.md"])
    assert "existing.md" in docs
    assert "missing.md" not in docs


async def test_fetch_docs_empty_list() -> None:
    provider = LocalProvider(Path("."))
    docs = await fetch_docs(provider, [])
    assert docs == {}


async def test_fetch_docs_all_missing() -> None:
    provider = AsyncMock()
    provider.get_doc = AsyncMock(return_value=None)
    docs = await fetch_docs(provider, ["a.md", "b.md"])
    assert docs == {}


async def test_fetch_docs_concurrent(tmp_path: Path) -> None:
    call_count = 0

    class CountingProvider:
        async def get_doc(self, path: str) -> str | None:
            nonlocal call_count
            call_count += 1
            return f"content of {path}"

        async def list_docs(self, prefix: str = "") -> list[str]:
            return []

    provider = CountingProvider()
    paths = [f"doc_{i}.md" for i in range(10)]
    docs = await fetch_docs(provider, paths)
    assert call_count == 10
    assert len(docs) == 10


async def test_fetch_docs_real_standards(repo_root: Path) -> None:
    provider = LocalProvider(repo_root)
    docs = await fetch_docs(provider, ["standards/python.md", "standards/typescript.md"])
    assert "standards/python.md" in docs
    assert "standards/typescript.md" in docs
    assert len(docs["standards/python.md"]) > 100
