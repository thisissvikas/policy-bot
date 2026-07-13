import base64

import httpx
import pytest
import respx

from policybot.github_client import GitHubClient
from policybot.providers.base import StandardsProvider
from policybot.providers.github import GitHubProvider

BASE = "https://api.github.com"


@pytest.fixture
def gh_client() -> GitHubClient:
    return GitHubClient(token="test-token")


@pytest.fixture
def provider(gh_client: GitHubClient) -> GitHubProvider:
    return GitHubProvider(gh_client, "owner/standards-repo", ref="main")


def test_github_provider_implements_protocol(gh_client: GitHubClient) -> None:
    p = GitHubProvider(gh_client, "owner/repo")
    assert isinstance(p, StandardsProvider)


def test_github_provider_invalid_repo(gh_client: GitHubClient) -> None:
    with pytest.raises(ValueError, match="owner/repo"):
        GitHubProvider(gh_client, "invalid-format")


@respx.mock
async def test_github_provider_get_doc_exists(provider: GitHubProvider) -> None:
    content = "# Python Standards"
    encoded = base64.b64encode(content.encode()).decode()
    respx.get(f"{BASE}/repos/owner/standards-repo/contents/standards/python.md").mock(
        return_value=httpx.Response(200, json={"content": encoded, "encoding": "base64"})
    )
    result = await provider.get_doc("standards/python.md")
    assert result == content


@respx.mock
async def test_github_provider_get_doc_missing(provider: GitHubProvider) -> None:
    respx.get(f"{BASE}/repos/owner/standards-repo/contents/standards/missing.md").mock(
        return_value=httpx.Response(404, json={"message": "Not Found"})
    )
    result = await provider.get_doc("standards/missing.md")
    assert result is None


@respx.mock
async def test_github_provider_list_docs(provider: GitHubProvider) -> None:
    respx.get(f"{BASE}/repos/owner/standards-repo/contents/standards").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"path": "standards/python.md", "type": "file"},
                {"path": "standards/typescript.md", "type": "file"},
            ],
        )
    )
    docs = await provider.list_docs("standards")
    assert "standards/python.md" in docs


@respx.mock
async def test_github_provider_list_docs_empty_prefix(provider: GitHubProvider) -> None:
    respx.get(f"{BASE}/repos/owner/standards-repo/contents/").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"path": "README.md", "type": "file"},
            ],
        )
    )
    docs = await provider.list_docs()
    assert "README.md" in docs
