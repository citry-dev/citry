"""
The docs version tree: the manifest, the per-version build stamp, and aliases.

Built doc versions live under ``versions/<version>/`` (committed to the repo),
beside a ``versions.json`` manifest and redirect stubs for aliases like
``latest/``. This module is the thin layer the build and assemble steps use to
read and write that tree:

- ``load_manifest`` / ``update_manifest`` read and merge ``versions.json`` using
  the vendored mike ``Versions`` model, which also gives the version ordering
  (``dev`` sorts above releases).
- ``write_build_info`` writes the per-version ``_build_info.json`` stamp that
  records how a version was built.
- ``materialize_alias`` rebuilds ``<alias>/`` as ``<meta refresh>`` redirect
  stubs mirroring every page of the target version (the vendored mike template).
  Redirect stubs keep the committed tree small and cross-platform.

The layout mirrors what gets mounted at ``/v/`` on the deployed site, so the
version picker's manifest lookup and the alias redirects resolve the same on
disk as in production.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from docs_site._internal._vendor.mike_versions import Versions

# Stamped into every _build_info.json. Bump when the builder's output format
# changes in a way that warrants rebuilding historical versions.
DOCS_BUILDER_VERSION = "1.0.0"

MANIFEST_NAME = "versions.json"
BUILD_INFO_NAME = "_build_info.json"

# ``builder_version`` value stamped into a version imported verbatim from an older
# published docs tree (e.g. a prior mike/gh-pages deploy) rather than built by this
# builder. A frozen import is historical HTML kept as-is: the version guards
# confirm it exists (dir, stamp, manifest entry, alias) but do not re-check its
# internal links or require a homepage, since those are whatever the old deploy
# shipped. Citry has no imported versions yet, so nothing is frozen today.
IMPORTED_BUILDER_VERSION = "imported-ghpages"

# Vendored mike redirect template (one stub per aliased page).
_REDIRECT_TEMPLATE = Path(__file__).resolve().parent / "_vendor" / "mike_redirect.html"


def is_frozen_import(version_dir: Path) -> bool:
    """
    True if ``version_dir`` was imported verbatim from an older published docs
    tree - its ``_build_info.json`` carries ``IMPORTED_BUILDER_VERSION`` - rather
    than built by this builder. A frozen import is historical HTML the builder
    never regenerates, so the version guards check that it exists but not that its
    internal links resolve or that it has a homepage.
    """
    stamp = version_dir / BUILD_INFO_NAME
    if not stamp.is_file():
        return False
    try:
        data = json.loads(stamp.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return data.get("builder_version") == IMPORTED_BUILDER_VERSION


def select_published_versions(versions: Versions, window: int) -> list[str]:
    """
    The newest ``window`` release versions (newest-first), or all of them when
    ``window`` <= 0. ``dev`` is excluded (a deploy publishes it separately).

    A deploy uses this to publish a bounded subset of the committed tree: the
    full tree stays committed for reproducibility, but a Pages site is size-capped.
    """
    releases = [str(v.version) for v in versions if str(v.version) != "dev"]
    return releases[:window] if window and window > 0 else releases


# How many of the newest versions stay crawlable and self-indexed. Every older
# version's /v/<version>/ tree is set to noindex in the assembled site and
# disallowed in robots.txt. Two (the current release plus the one before it) lets
# a reader still reach the previous release's docs while search engines index
# only the current one.
KEEP_INDEXED_VERSIONS = 2


def select_indexed_versions(versions: Versions, keep_recent: int = KEEP_INDEXED_VERSIONS) -> list[str]:
    """
    The versions that stay crawlable and self-indexed (newest-first): the newest
    ``keep_recent`` plus whatever the ``latest`` alias points at.

    Every other version the manifest lists is an old version, whose mounted
    ``/v/<version>/`` tree the deploy sets to noindex and the root build disallows
    in robots.txt. This is the one shared definition of "current versus old" that
    both of those steps read, so they can never disagree on which versions to hide.
    ``keep_recent`` <= 0 keeps every version (none is treated as old).

    ``dev`` is always kept (never treated as old) but does not consume one of the
    ``keep_recent`` release slots. The robots step reads the committed manifest
    (which includes ``dev``) while the noindex step reads the mounted manifest
    (which excludes it, see ``select_published_versions``); counting ``dev`` as a
    slot would make those two views pick different "old" sets, so it is excluded
    from the count on both sides.
    """
    ordered = [str(info.version) for info in versions]  # newest-first (Versions.__iter__)
    if not ordered:
        return []
    if keep_recent <= 0:
        return list(ordered)
    releases = [v for v in ordered if v != "dev"]
    kept = {v for v in ordered if v == "dev"} | set(releases[:keep_recent])
    # The latest alias must stay crawlable even if it points at an older release.
    latest = versions.find("latest")
    if latest:
        kept.add(str(latest[0]))
    # Return in newest-first order (the input order), deduped by the kept set.
    return [v for v in ordered if v in kept]


def load_manifest(versions_root: Path) -> Versions:
    """Read ``versions_root/versions.json`` into a ``Versions``; empty if absent."""
    manifest = versions_root / MANIFEST_NAME
    if manifest.is_file():
        return Versions.loads(manifest.read_text(encoding="utf-8"))
    return Versions()


def write_manifest(versions_root: Path, versions: Versions) -> None:
    """Write ``versions`` to ``versions_root/versions.json`` (newest-first, pretty)."""
    versions_root.mkdir(parents=True, exist_ok=True)
    (versions_root / MANIFEST_NAME).write_text(versions.dumps() + "\n", encoding="utf-8")


def update_manifest(
    versions_root: Path,
    version: str,
    *,
    title: str | None = None,
    aliases: tuple[str, ...] = (),
) -> Versions:
    """
    Add or update ``version`` (with ``aliases``) in the manifest and write it.

    An alias like ``latest`` is moved off whatever version previously held it onto
    this one, which is exactly what a new release wants.
    """
    versions = load_manifest(versions_root)
    versions.add(version, title=title, aliases=list(aliases), update_aliases=True)
    write_manifest(versions_root, versions)
    return versions


def git_head_sha(repo_root: Path) -> str:
    """Current ``HEAD`` commit SHA, or "" if git is unavailable (a best-effort stamp)."""
    try:
        out = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],  # noqa: S607
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return ""
    return out.stdout.strip()


def write_build_info(
    version_dir: Path,
    *,
    version: str,
    source_sha: str,
    source_tag: str | None = None,
    builder_version: str = DOCS_BUILDER_VERSION,
    built_at: str | None = None,
) -> dict[str, str]:
    """
    Write ``version_dir/_build_info.json`` recording how this version was built.

    The stamp lets a rebuild compare ``source_sha`` against the tag's commit and
    skip the work when they match. Returns the written payload (handy for tests).
    """
    info = {
        "version": version,
        "source_sha": source_sha,
        "source_tag": source_tag if source_tag is not None else version,
        "built_at": built_at if built_at is not None else datetime.now(UTC).isoformat(),
        "builder_version": builder_version,
    }
    version_dir.mkdir(parents=True, exist_ok=True)
    (version_dir / BUILD_INFO_NAME).write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    return info


def render_redirect(href: str) -> str:
    """Render the vendored mike redirect stub pointing at ``href``."""
    return _REDIRECT_TEMPLATE.read_text(encoding="utf-8").replace("{{href}}", href)


def materialize_alias(versions_root: Path, alias: str, target_version: str) -> int:
    """
    Rebuild ``versions_root/<alias>/`` as redirect stubs mirroring every ``.html``
    page under ``versions_root/<target_version>/``. Returns the redirect count.

    The alias dir is cleared first, so an alias that moves (e.g. ``latest`` from an
    old release to a new one) leaves no stale redirects behind. Each stub points at
    the matching page with a relative href, so it resolves whether the tree is
    served from the repo or from the deploy artifact.
    """
    target_dir = versions_root / target_version
    alias_dir = versions_root / alias
    if alias_dir.exists():
        shutil.rmtree(alias_dir)

    count = 0
    for html in sorted(target_dir.rglob("*.html")):
        rel = html.relative_to(target_dir)
        dest = alias_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        href = os.path.relpath(html, dest.parent).replace(os.sep, "/")
        dest.write_text(render_redirect(href), encoding="utf-8")
        count += 1
    return count
