"""
The ``citry-docs`` command line: ``build`` and ``serve``.

These mirror the two upstream management commands. ``build`` writes the static
site to disk; ``serve`` runs the development server (live render, auto-reload).
Run via ``python -m docs_site <command>``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from docs_site.build import build_site


def main(argv: list[str] | None = None) -> int:
    """Parse ``argv`` and run the chosen subcommand; returns a process exit code."""
    parser = argparse.ArgumentParser(prog="citry-docs", description="Build and serve the Citry documentation site.")
    sub = parser.add_subparsers(dest="command", required=True)

    build_parser = sub.add_parser("build", help="Build the static site to disk.")
    build_parser.add_argument(
        "-o", "--output", type=Path, default=None, help="Output directory (default: <repo>/site)."
    )

    serve_parser = sub.add_parser("serve", help="Run the development server (live render, auto-reload).")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1).")
    serve_parser.add_argument("-p", "--port", type=int, default=8000, help="Bind port (default: 8000).")
    serve_parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload on file changes.")

    args = parser.parse_args(argv)

    if args.command == "build":
        return _run_build(args.output)
    return _run_serve(args.host, args.port, reload=not args.no_reload)


def _run_build(output: Path | None) -> int:
    outcome = build_site(output_dir=output)
    print(f"Built {outcome.built} page(s) to {outcome.output_dir} in {outcome.elapsed:.2f}s.")
    if outcome.failed:
        print(f"{outcome.failed} page(s) failed to render:")
        for rel, message in outcome.errors:
            print(f"  - {rel}: {message}")
        return 1
    return 0


def _run_serve(host: str, port: int, *, reload: bool) -> int:
    # uvicorn is a server-only dependency; import it lazily so `build` (and just
    # importing the CLI) does not require it.
    import uvicorn  # noqa: PLC0415

    uvicorn.run("docs_site.serve:app", host=host, port=port, reload=reload)
    return 0
