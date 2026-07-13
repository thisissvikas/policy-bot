from typing import Protocol, runtime_checkable


@runtime_checkable
class StandardsProvider(Protocol):
    async def get_doc(self, path: str) -> str | None:
        """Return the content of a standards doc, or None if not found."""
        ...

    async def list_docs(self, prefix: str = "") -> list[str]:
        """List available doc paths, optionally filtered by prefix."""
        ...
