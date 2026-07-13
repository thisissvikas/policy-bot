import base64
import json

import httpx
import pytest
import respx

from policybot.github_client import GitHubClient, GitHubError
from policybot.models import ReviewComment

BASE = "https://api.github.com"


@pytest.fixture
def client() -> GitHubClient:
    return GitHubClient(token="test-token")


@respx.mock
async def test_get_pr_diff(client: GitHubClient) -> None:
    respx.get(f"{BASE}/repos/owner/repo/pulls/1").mock(
        return_value=httpx.Response(200, text="--- a/file.py\n+++ b/file.py\n+x = 1\n")
    )
    diff = await client.get_pr_diff("owner", "repo", 1)
    assert "+x = 1" in diff


@respx.mock
async def test_get_pr_diff_error(client: GitHubClient) -> None:
    respx.get(f"{BASE}/repos/owner/repo/pulls/99").mock(
        return_value=httpx.Response(404, json={"message": "Not Found"})
    )
    with pytest.raises(GitHubError) as exc_info:
        await client.get_pr_diff("owner", "repo", 99)
    assert exc_info.value.status_code == 404


@respx.mock
async def test_get_pr_files(client: GitHubClient) -> None:
    respx.get(f"{BASE}/repos/owner/repo/pulls/1/files").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"filename": "app/service.py"},
                {"filename": "app/views.py"},
            ],
        )
    )
    files = await client.get_pr_files("owner", "repo", 1)
    assert files == ["app/service.py", "app/views.py"]


@respx.mock
async def test_get_pr_head_sha(client: GitHubClient) -> None:
    respx.get(f"{BASE}/repos/owner/repo/pulls/1").mock(
        return_value=httpx.Response(200, json={"head": {"sha": "abc123def"}})
    )
    sha = await client.get_pr_head_sha("owner", "repo", 1)
    assert sha == "abc123def"


@respx.mock
async def test_get_file_contents_base64(client: GitHubClient) -> None:
    content = "# Python Standards"
    encoded = base64.b64encode(content.encode()).decode()
    respx.get(f"{BASE}/repos/owner/repo/contents/standards/python.md").mock(
        return_value=httpx.Response(
            200,
            json={
                "content": encoded,
                "encoding": "base64",
            },
        )
    )
    result = await client.get_file_contents("owner", "repo", "standards/python.md")
    assert result == content


@respx.mock
async def test_get_file_contents_not_found(client: GitHubClient) -> None:
    respx.get(f"{BASE}/repos/owner/repo/contents/missing.md").mock(
        return_value=httpx.Response(404, json={"message": "Not Found"})
    )
    result = await client.get_file_contents("owner", "repo", "missing.md")
    assert result is None


@respx.mock
async def test_get_file_contents_server_error(client: GitHubClient) -> None:
    respx.get(f"{BASE}/repos/owner/repo/contents/file.md").mock(
        return_value=httpx.Response(500, json={"message": "Internal Server Error"})
    )
    with pytest.raises(GitHubError) as exc_info:
        await client.get_file_contents("owner", "repo", "file.md")
    assert exc_info.value.status_code == 500


@respx.mock
async def test_list_contents(client: GitHubClient) -> None:
    respx.get(f"{BASE}/repos/owner/repo/contents/standards").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"path": "standards/python.md", "type": "file"},
                {"path": "standards/typescript.md", "type": "file"},
                {"path": "standards/subdir", "type": "dir"},
            ],
        )
    )
    files = await client.list_contents("owner", "repo", "standards")
    assert "standards/python.md" in files
    assert "standards/typescript.md" in files
    assert "standards/subdir" not in files


@respx.mock
async def test_create_review(client: GitHubClient) -> None:
    route = respx.post(f"{BASE}/repos/owner/repo/pulls/1/reviews").mock(
        return_value=httpx.Response(200, json={"id": 1})
    )
    await client.create_review(
        owner="owner",
        repo="repo",
        pr_number=1,
        commit_sha="abc123",
        comments=[ReviewComment(path="app.py", line=10, body="violation")],
    )
    assert route.called
    request_body = json.loads(route.calls[0].request.content)
    assert request_body["commit_id"] == "abc123"
    assert request_body["event"] == "COMMENT"
    assert len(request_body["comments"]) == 1
    assert request_body["comments"][0]["path"] == "app.py"


@respx.mock
async def test_create_review_error(client: GitHubClient) -> None:
    respx.post(f"{BASE}/repos/owner/repo/pulls/1/reviews").mock(
        return_value=httpx.Response(422, json={"message": "Validation Failed"})
    )
    with pytest.raises(GitHubError) as exc_info:
        await client.create_review(
            owner="owner",
            repo="repo",
            pr_number=1,
            commit_sha="abc123",
            comments=[ReviewComment(path="app.py", line=1, body="test")],
        )
    assert exc_info.value.status_code == 422


async def test_client_context_manager() -> None:
    async with GitHubClient(token="test") as client:
        assert client is not None
    # No exception = context manager works


async def test_close() -> None:
    client = GitHubClient(token="test")
    await client.close()
