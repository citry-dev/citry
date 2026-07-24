"""
The ``citry-docs`` command line.

- ``build``: write the static site to disk.
- ``serve``: run the development server (live render, auto-reload).
- ``build-check``: build to a throwaway directory and run the post-build guards
  (the CI gate). Fails on any error, or on any warning under ``--strict``.
- ``serve-built``: build the real static site and serve it over plain HTTP, so
  you can preview exactly what gets deployed.
- ``assemble``: assemble the multi-version deploy artifact (current version at
  the root, committed snapshots under ``/v/``).
- ``versions-check``: validate the committed ``versions/`` tree (manifest,
  aliases, build stamps, cross-version links) without building.
- ``build-all``: bootstrap / disaster-recovery rebuild of every version selected
  by ``docs_versions.toml`` (walks the git tags in throwaway worktrees).

Run via ``python -m docs_site <command>``.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from docs_site._internal.build import build_site

if TYPE_CHECKING:
    from collections.abc import Callable


def main(argv: list[str] | None = None) -> int:
    """Parse ``argv`` and run the chosen subcommand; returns a process exit code."""
    parser = argparse.ArgumentParser(prog="citry-docs", description="Build and serve the Citry documentation site.")
    sub = parser.add_subparsers(dest="command", required=True)

    build_parser = sub.add_parser("build", help="Build the static site to disk.")
    build_parser.add_argument(
        "-o", "--output", type=Path, default=None, help="Output directory (default: <repo>/site)."
    )
    build_parser.add_argument("--no-minify", action="store_true", help="Skip the final HTML-shrinking pass.")
    build_parser.add_argument("--no-search", action="store_true", help="Skip building the search index.")
    build_parser.add_argument("--no-social-cards", action="store_true", help="Skip per-page social-card generation.")
    build_parser.add_argument(
        "--docs-version", default="", help="Build a version snapshot into versions/<version>/ instead of the root."
    )
    build_parser.add_argument("--alias", default="", help="Materialize an alias (e.g. 'latest') for --docs-version.")

    serve_parser = sub.add_parser("serve", help="Run the development server (live render, auto-reload).")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1).")
    serve_parser.add_argument("-p", "--port", type=int, default=8000, help="Bind port (default: 8000).")
    serve_parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload on file changes.")

    check_parser = sub.add_parser("build-check", help="Build to a temp dir and run the post-build guards.")
    check_parser.add_argument("--strict", action="store_true", help="Also fail on warnings, not just errors.")

    sb_parser = sub.add_parser("serve-built", help="Build the static site and serve it over plain HTTP.")
    sb_parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1).")
    sb_parser.add_argument("-p", "--port", type=int, default=8000, help="Bind port (default: 8000).")

    asm_parser = sub.add_parser("assemble", help="Assemble the multi-version deploy artifact (current + /v/).")
    asm_parser.add_argument("-o", "--output", type=Path, default=None, help="Output directory (default: <repo>/site).")
    asm_parser.add_argument(
        "--no-build", action="store_true", help="Only mount versions/* into an existing build; skip the current build."
    )

    vc_parser = sub.add_parser(
        "versions-check", help="Validate the committed versions/ tree (manifest, aliases, stamps, links)."
    )
    vc_parser.add_argument("--strict", action="store_true", help="Also fail on warnings, not just errors.")
    vc_parser.add_argument(
        "--versions-dir", type=Path, default=None, help="Version tree to check (default: docs_site/versions)."
    )

    ba_parser = sub.add_parser(
        "build-all", help="Rebuild every version selected by docs_versions.toml into versions/ (bootstrap)."
    )
    ba_parser.add_argument(
        "--config", type=Path, default=None, help="Path to docs_versions.toml (default: docs_site/docs_versions.toml)."
    )
    ba_parser.add_argument(
        "--versions-dir", type=Path, default=None, help="Output root (default: docs_site/versions)."
    )
    ba_parser.add_argument(
        "--dry-run", action="store_true", help="List selected tags + rebuild status without building anything."
    )

    args = parser.parse_args(argv)

    if args.command == "build":
        return _run_build(
            args.output,
            minify=not args.no_minify,
            search=not args.no_search,
            social_cards=not args.no_social_cards,
            docs_version=args.docs_version,
            alias=args.alias,
        )
    if args.command == "build-check":
        return _run_build_check(strict=args.strict)
    if args.command == "serve-built":
        return _run_serve_built(args.host, args.port)
    if args.command == "assemble":
        return _run_assemble(args.output, build=not args.no_build)
    if args.command == "versions-check":
        return _run_versions_check(strict=args.strict, versions_dir=args.versions_dir)
    if args.command == "build-all":
        return _run_build_all(args.versions_dir, args.config, dry_run=args.dry_run)
    return _run_serve(args.host, args.port, reload=not args.no_reload)


def _run_build(
    output: Path | None, *, minify: bool, search: bool, social_cards: bool, docs_version: str = "", alias: str = ""
) -> int:
    outcome = build_site(
        output_dir=output,
        minify=minify,
        search=search,
        social_cards=social_cards,
        docs_version=docs_version,
        alias=alias,
    )
    label = f" (version {docs_version})" if docs_version else ""
    print(f"Built {outcome.built} page(s){label} to {outcome.output_dir} in {outcome.elapsed:.2f}s.")
    print(
        f"  reference: {outcome.reference} page(s), releases: {outcome.releases}, "
        f"examples: {outcome.examples}, minified: {outcome.minified}"
    )
    if search and not outcome.search_ok:
        print(f"  search index: {outcome.search_message}")
    if social_cards:
        placed = outcome.social_cards_placed
        print(
            f"  social cards: {placed} placed" + (f" (skipped: {outcome.social_cards_skipped})" if not placed else "")
        )
    if outcome.failed:
        print(f"{outcome.failed} page(s) failed to render:")
        for rel, message in outcome.errors:
            print(f"  - {rel}: {message}")
        return 1
    return 0


def _run_build_check(*, strict: bool) -> int:
    # Imported here so a plain `build` does not pull in lxml (a guard dependency).
    from docs_site._internal.config import config as default_config  # noqa: PLC0415
    from docs_site._internal.guards import format_report, make_context, run_guards  # noqa: PLC0415

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "site"
        outcome = build_site(output_dir=out)
        if outcome.failed:
            print(f"{outcome.failed} page(s) failed to render:")
            for rel, message in outcome.errors:
                print(f"  - {rel}: {message}")
            return 1
        if not outcome.search_ok:
            print(f"Search index failed: {outcome.search_message}")
            return 1
        results, ok = run_guards(make_context(out, config=default_config), strict=strict)

    print(format_report(results))
    return 0 if ok else 1


def _run_assemble(output: Path | None, *, build: bool) -> int:
    from docs_site._internal.assemble import assemble_site  # noqa: PLC0415 - keeps `build` lean

    outcome = assemble_site(output_dir=output, build=build)
    if outcome.failed:
        print(f"{outcome.failed} page(s) failed to render:")
        for rel, message in outcome.errors:
            print(f"  - {rel}: {message}")
        return 1
    if outcome.search_ok is False:
        print(f"Search index failed: {outcome.search_message}")
        return 1
    print(f"Assembled deploy artifact at {outcome.output_dir}.")
    print(f"  versions mounted under /v/: {', '.join(outcome.published) or '(none)'}")
    print(f"  root version picker enabled on {outcome.picker_pages} page(s)")
    return 0


def _run_versions_check(*, strict: bool, versions_dir: Path | None) -> int:
    # Imported here so a plain `build` does not pull in lxml (a guard dependency).
    from docs_site._internal.config import config as default_config  # noqa: PLC0415
    from docs_site._internal.guards import (  # noqa: PLC0415
        VERSION_GUARDS,
        format_report,
        make_versions_context,
        run_guards,
    )

    root = versions_dir if versions_dir is not None else default_config.versions_dir
    if not root.is_dir():
        # No committed version tree yet (pre-bootstrap) is a valid, passing state.
        print(f"No version tree at {root} - nothing to check.")
        return 0

    results, ok = run_guards(make_versions_context(root), strict=strict, guards=VERSION_GUARDS)
    print(format_report(results))
    return 0 if ok else 1


# Monorepo release tags are package-scoped (e.g. ``citry@0.2.0``); the docs version
# is the part after this prefix. Only the docs package's own tags are stripped, so a
# sibling package's tag (e.g. ``citry-core@1.3.0``) keeps its prefix and then fails
# the version pattern instead of being mistaken for a docs version.
_DOCS_TAG_PREFIX = "citry@"


def _normalize_tag(tag: str) -> str:
    """The docs version identifier for a raw git tag (drop the ``citry@`` package prefix)."""
    return tag.removeprefix(_DOCS_TAG_PREFIX)


def _git(repo_root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run ``git -C <repo_root> <args>`` and capture its output."""
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],  # noqa: S607 - `git` from PATH is fine for a dev/CI tool
        capture_output=True,
        text=True,
        check=check,
    )


def _tag_sha(repo_root: Path, ref: str) -> str:
    """The commit a tag points at (``^{commit}`` dereferences an annotated tag)."""
    return _git(repo_root, "rev-parse", f"{ref}^{{commit}}").stdout.strip()


def _git_tag_ref_map(repo_root: Path) -> dict[str, str]:
    """
    Map each docs version identifier to the raw git tag ref it came from.

    ``build-all`` works in docs version strings (``0.2.0``), but git needs the real
    package-scoped ref (``citry@0.2.0``), so this keeps the mapping back. A raised
    ``CalledProcessError`` / ``FileNotFoundError`` means git is unavailable or
    ``repo_root`` is not a checkout; the caller turns that into a clean message.
    """
    raw = [line for line in _git(repo_root, "tag").stdout.splitlines() if line.strip()]
    return {_normalize_tag(tag): tag for tag in raw}


def _has_docs_builder(docs_dir: Path) -> bool:
    """Whether a checkout contains either the flat or the ``_internal`` builder layout."""
    has_versioning = (docs_dir / "versioning.py").is_file() or (docs_dir / "_internal" / "versioning.py").is_file()
    return (docs_dir / "__main__.py").is_file() and has_versioning


def _make_build_one(repo_root: Path, ref_map: dict[str, str]) -> Callable[[str, str, Path], str]:
    """
    Build one version by checking its tag out in a throwaway git worktree.

    Returns ``"skipped_no_builder"`` for a tag whose checkout predates the docs
    builder (there is nothing to run), ``"built"`` on success, and raises on a real
    build failure so ``bootstrap_versions`` records it against that one tag. The
    worktree is always removed, even on failure.
    """

    def build_one(tag: str, version: str, version_dir: Path) -> str:
        ref = ref_map[tag]
        tmp_parent = Path(tempfile.mkdtemp(prefix="citry-docs-wt-"))
        worktree = tmp_parent / version
        try:
            _git(repo_root, "worktree", "add", "--detach", str(worktree), ref)
            wt_docs = worktree / "docs_site"
            # Only tags whose checkout ships the docs builder can be rebuilt; older
            # tags predate docs_site and are skipped (rebuilding historical versions
            # is a deferred decision).
            if not _has_docs_builder(wt_docs):
                return "skipped_no_builder"
            # `uv run --project <worktree>` resolves that checkout's own dependencies
            # (an old tag may pin different ones), and cwd=<worktree> lets
            # `python -m docs_site` import the builder from the checkout.
            proc = subprocess.run(
                [  # noqa: S607 - `uv` from PATH is fine for a dev/CI tool
                    "uv",
                    "run",
                    "--project",
                    str(worktree),
                    "python",
                    "-m",
                    "docs_site",
                    "build",
                    "--docs-version",
                    version,
                    "--no-search",
                    "--no-social-cards",
                    "-o",
                    str(version_dir),
                ],
                cwd=str(worktree),
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.returncode != 0:
                msg = (proc.stderr or proc.stdout)[-600:]
                raise RuntimeError(f"docs build exited {proc.returncode}: {msg}")
            return "built"
        finally:
            # Always unregister and delete the worktree, even on failure.
            _git(repo_root, "worktree", "remove", "--force", str(worktree), check=False)
            shutil.rmtree(tmp_parent, ignore_errors=True)

    return build_one


def _run_build_all(
    versions_dir: Path | None, config_path: Path | None, *, dry_run: bool, repo_root: Path | None = None
) -> int:
    from docs_site._internal import bootstrap  # noqa: PLC0415
    from docs_site._internal.config import config as default_config  # noqa: PLC0415

    repo = repo_root if repo_root is not None else default_config.repo_root
    versions_root = versions_dir if versions_dir is not None else default_config.versions_dir
    cfg_path = config_path if config_path is not None else default_config.versions_config
    config = bootstrap.load_versions_config(cfg_path)

    try:
        ref_map = _git_tag_ref_map(repo)
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
        print(f"build-all needs a git checkout with tags ({repo}): {e}")
        return 1

    all_tags = sorted(ref_map)
    if not all_tags:
        print("No git tags found; nothing to build.")
        return 0

    def tag_sha(tag: str) -> str:
        return _tag_sha(repo, ref_map[tag])

    if dry_run:
        selected = bootstrap.select_tags(all_tags, config)
        print(f"Would consider {len(selected)} version(s) (newest first):")
        for tag in selected:
            version = bootstrap.tag_to_version(tag)
            stale = bootstrap.needs_rebuild(versions_root / version, tag_sha(tag))
            print(f"  {version:<12} {'BUILD' if stale else 'up-to-date'}")
        return 0

    # A previous interrupted run can leave a dangling worktree registration that
    # blocks re-adding the same path; clear those first.
    _git(repo, "worktree", "prune", check=False)
    outcome = bootstrap.bootstrap_versions(
        config,
        versions_root=versions_root,
        all_tags=all_tags,
        tag_sha=tag_sha,
        build_one=_make_build_one(repo, ref_map),
        log=print,
    )

    print(
        f"Done: {len(outcome.built)} built, {len(outcome.skipped_up_to_date)} up-to-date, "
        f"{len(outcome.skipped_no_builder)} skipped (no builder), {len(outcome.failed)} failed"
    )
    if outcome.skipped_no_builder:
        print("Skipped (predate the docs builder): " + ", ".join(outcome.skipped_no_builder))
    if outcome.failed:
        print("Failed: " + ", ".join(outcome.failed))
        return 1
    return 0


def _run_serve_built(host: str, port: int) -> int:
    # Stdlib HTTP server, so a built-site preview needs no extra dependency.
    import contextlib  # noqa: PLC0415
    import functools  # noqa: PLC0415
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer  # noqa: PLC0415

    outcome = build_site()
    print(f"Built {outcome.built} page(s) to {outcome.output_dir}.")
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(outcome.output_dir))
    server = ThreadingHTTPServer((host, port), handler)
    print(f"Serving {outcome.output_dir} at http://{host}:{port}/ (Ctrl+C to stop)")
    with contextlib.suppress(KeyboardInterrupt):
        server.serve_forever()
    return 0


def _run_serve(host: str, port: int, *, reload: bool) -> int:
    # uvicorn is a server-only dependency; import it lazily so `build` (and just
    # importing the CLI) does not require it.
    import uvicorn  # noqa: PLC0415

    uvicorn.run("docs_site._internal.serve:app", host=host, port=port, reload=reload)
    return 0
