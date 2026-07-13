import asyncio

import structlog

from policybot.providers.base import StandardsProvider

log = structlog.get_logger()


async def fetch_docs(
    provider: StandardsProvider,
    doc_paths: list[str],
) -> dict[str, str]:
    """Fetch multiple docs concurrently. Missing docs are skipped with a warning."""
    if not doc_paths:
        return {}

    async def _fetch(path: str) -> tuple[str, str | None]:
        content = await provider.get_doc(path)
        if content is None:
            log.warning("doc_not_found", path=path)
        return path, content

    results = await asyncio.gather(*(_fetch(p) for p in doc_paths))
    return {path: content for path, content in results if content is not None}
