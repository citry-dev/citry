"""Reject release wheels that exceed one explicit compressed-size cap."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


def verify(wheels: Sequence[Path], *, max_bytes: int) -> list[dict[str, int | str]]:
    """Return a checked size record for each wheel."""
    if not wheels:
        raise ValueError("at least one wheel is required")
    report: list[dict[str, int | str]] = []
    for wheel in sorted(wheels):
        if not wheel.is_file() or wheel.suffix != ".whl":
            raise ValueError(f"expected a built wheel, got {wheel}")
        size = wheel.stat().st_size
        if size > max_bytes:
            raise ValueError(f"{wheel.name} is {size} bytes; the release cap is {max_bytes} bytes")
        report.append({"wheel": wheel.name, "bytes": size, "maxBytes": max_bytes})
    return report


def main(argv: Sequence[str] | None = None) -> int:
    """Check command-line wheel paths and print one JSON report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", nargs="+", type=Path)
    parser.add_argument("--max-bytes", type=int, required=True)
    args = parser.parse_args(argv)
    if args.max_bytes <= 0:
        parser.error("--max-bytes must be positive")
    try:
        report = verify(args.wheel, max_bytes=args.max_bytes)
    except ValueError as error:
        parser.exit(1, f"wheel-size verification failed: {error}\n")
    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
