from pathlib import Path

from policybot.providers.base import StandardsProvider
from policybot.providers.local import LocalProvider


def test_local_provider_implements_protocol(tmp_path: Path) -> None:
    provider = LocalProvider(tmp_path)
    assert isinstance(provider, StandardsProvider)


async def test_local_provider_get_doc_exists(tmp_path: Path) -> None:
    (tmp_path / "standards").mkdir()
    (tmp_path / "standards" / "python.md").write_text("# Python")
    provider = LocalProvider(tmp_path)
    content = await provider.get_doc("standards/python.md")
    assert content == "# Python"


async def test_local_provider_get_doc_missing(tmp_path: Path) -> None:
    provider = LocalProvider(tmp_path)
    result = await provider.get_doc("does/not/exist.md")
    assert result is None


async def test_local_provider_list_docs(tmp_path: Path) -> None:
    (tmp_path / "standards").mkdir()
    (tmp_path / "standards" / "a.md").write_text("A")
    (tmp_path / "standards" / "b.md").write_text("B")
    (tmp_path / "standards" / "not_md.txt").write_text("txt")
    provider = LocalProvider(tmp_path)
    docs = await provider.list_docs()
    assert "standards/a.md" in docs
    assert "standards/b.md" in docs
    assert "standards/not_md.txt" not in docs


async def test_local_provider_list_docs_with_prefix(tmp_path: Path) -> None:
    (tmp_path / "standards").mkdir()
    (tmp_path / "adrs").mkdir()
    (tmp_path / "standards" / "python.md").write_text("py")
    (tmp_path / "adrs" / "ADR-001.md").write_text("adr")
    provider = LocalProvider(tmp_path)
    docs = await provider.list_docs("standards")
    assert "standards/python.md" in docs
    assert not any("adrs" in d for d in docs)


async def test_local_provider_list_docs_missing_prefix(tmp_path: Path) -> None:
    provider = LocalProvider(tmp_path)
    docs = await provider.list_docs("nonexistent")
    assert docs == []


def test_local_provider_uses_real_standards(repo_root: Path) -> None:
    provider = LocalProvider(repo_root)
    assert isinstance(provider, StandardsProvider)


async def test_local_provider_real_standards_exist(repo_root: Path) -> None:
    provider = LocalProvider(repo_root)
    content = await provider.get_doc("standards/python.md")
    assert content is not None
    assert "Error Handling" in content


async def test_local_provider_get_doc_encoding(tmp_path: Path) -> None:
    (tmp_path / "unicode.md").write_text("# Héllo Wörld 🐍", encoding="utf-8")
    provider = LocalProvider(tmp_path)
    content = await provider.get_doc("unicode.md")
    assert content is not None
    assert "🐍" in content
