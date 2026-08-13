"""Private authoritative bytes for resources served by Citry routes."""

from __future__ import annotations

from dataclasses import dataclass

from citry.util.routing import RouteResponse


@dataclass(frozen=True, slots=True)
class _OwnedResource:
    """One URL and the exact response body Citry owns at that URL."""

    url: str
    content: str | bytes
    content_type: str
    headers: tuple[tuple[str, str], ...] = ()

    @property
    def body(self) -> bytes:
        """Return the bytes sent by every Citry web adapter."""
        return self.content.encode() if isinstance(self.content, str) else self.content

    def response(self) -> RouteResponse:
        """Build the route response without changing the content representation."""
        return RouteResponse(content=self.content, content_type=self.content_type, headers=self.headers)
