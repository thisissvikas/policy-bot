from policybot.github_client import GitHubClient


class GitHubProvider:
    """Fetches standards documents from a GitHub repository."""

    def __init__(self, client: GitHubClient, repo: str, ref: str = "main") -> None:
        parts = repo.split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid repo format '{repo}', expected 'owner/repo'")
        self._client = client
        self._owner, self._repo = parts[0], parts[1]
        self._ref = ref

    async def get_doc(self, path: str) -> str | None:
        return await self._client.get_file_contents(self._owner, self._repo, path, ref=self._ref)

    async def list_docs(self, prefix: str = "") -> list[str]:
        return await self._client.list_contents(self._owner, self._repo, path=prefix, ref=self._ref)
