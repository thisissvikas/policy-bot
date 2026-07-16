import base64
from typing import Any

import httpx
import structlog

from policybot.models import ReviewComment

log = structlog.get_logger()

GITHUB_API = "https://api.github.com"


class GitHubError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"GitHub API error {status_code}: {message}")


class GitHubClient:
    def __init__(self, token: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=GITHUB_API,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=30.0,
        )

    async def _get(self, path: str, **kwargs: Any) -> Any:
        response = await self._client.get(path, **kwargs)
        if not response.is_success:
            raise GitHubError(response.status_code, response.text[:200])
        return response.json()

    async def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        response = await self._client.get(
            f"/repos/{owner}/{repo}/pulls/{pr_number}",
            headers={"Accept": "application/vnd.github.v3.diff"},
        )
        if not response.is_success:
            raise GitHubError(response.status_code, response.text[:200])
        return response.text

    async def get_pr_files(self, owner: str, repo: str, pr_number: int) -> list[str]:
        files: list[str] = []
        page = 1
        while True:
            data: list[dict[str, Any]] = await self._get(
                f"/repos/{owner}/{repo}/pulls/{pr_number}/files",
                params={"per_page": 100, "page": page},
            )
            files.extend(f["filename"] for f in data)
            if len(data) < 100:
                break
            page += 1
        return files

    async def get_pr_head_sha(self, owner: str, repo: str, pr_number: int) -> str:
        data: dict[str, Any] = await self._get(f"/repos/{owner}/{repo}/pulls/{pr_number}")
        head: dict[str, Any] = data["head"]
        sha: str = head["sha"]
        return sha

    async def get_file_contents(
        self, owner: str, repo: str, path: str, ref: str = "main"
    ) -> str | None:
        try:
            data: dict[str, Any] = await self._get(
                f"/repos/{owner}/{repo}/contents/{path}",
                params={"ref": ref},
            )
        except GitHubError as exc:
            if exc.status_code == 404:
                return None
            raise
        content: str = data.get("content", "")
        encoding: str = data.get("encoding", "")
        if encoding == "base64":
            return base64.b64decode(content).decode("utf-8")
        return content

    async def list_contents(
        self, owner: str, repo: str, path: str = "", ref: str = "main"
    ) -> list[str]:
        try:
            data: list[dict[str, Any]] = await self._get(
                f"/repos/{owner}/{repo}/contents/{path}",
                params={"ref": ref},
            )
        except GitHubError as exc:
            if exc.status_code == 404:
                return []
            raise
        return [item["path"] for item in data if item["type"] == "file"]

    async def create_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        commit_sha: str,
        comments: list[ReviewComment],
        body: str = "",
    ) -> None:
        payload: dict[str, Any] = {
            "commit_id": commit_sha,
            "body": body,
            "event": "COMMENT",
            "comments": [
                {
                    "path": c.path,
                    "line": c.line,
                    "side": c.side,
                    "body": c.body,
                }
                for c in comments
            ],
        }
        response = await self._client.post(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews",
            json=payload,
        )
        if not response.is_success:
            raise GitHubError(response.status_code, response.text[:200])
        log.info("review_posted", pr=pr_number, comments=len(comments))

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "GitHubClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()
