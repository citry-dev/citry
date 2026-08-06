"""Console entry point for the Citry language server."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from pygls.cli import start_server

from citry_lsp.server import server

if TYPE_CHECKING:
    from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    """Start stdio by default, or a pygls development transport."""
    start_server(server, list(sys.argv[1:] if argv is None else argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main"]
