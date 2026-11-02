"""Console entry point for the Citry language server."""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING

from citry_lsp.server import server

if TYPE_CHECKING:
    from collections.abc import Sequence

# Editors start the server as a child process and talk to it over stdin and
# stdout, so stdio is the only transport the command offers. A network
# listener would accept requests from other local programs and web pages,
# and those requests can make the server load project code.
_STDIO_ONLY = "this command runs over stdio only and accepts no options except --help"


def _parser() -> argparse.ArgumentParser:
    # A fixed `prog` keeps the usage line the same for `citry-lsp` and for
    # `python -m citry_lsp`, which is how the VS Code extension starts it.
    return argparse.ArgumentParser(
        prog="citry-lsp",
        description=(
            "Start the Citry language server over stdio. Your editor starts this command and "
            "talks to it through standard input and output."
        ),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Start the Citry language server over stdio."""
    parser = _parser()
    # Collect unknown arguments rather than letting argparse reject them, so
    # every one, including a transport option such as `--tcp`, gets the same
    # message saying why the command takes none.
    _, unknown = parser.parse_known_args(list(sys.argv[1:] if argv is None else argv))
    if unknown:
        # `parser.error` prints the usage line and exits with status 2.
        parser.error(f"{_STDIO_ONLY}; unrecognized arguments: {' '.join(unknown)}")
    server.start_io()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main"]
