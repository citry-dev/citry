"""
The git-free core of ``docs build-all``: version config, tag selection, and the
rebuild loop.

``build-all`` rebuilds many doc versions in one shot. It is the bootstrap /
disaster-recovery command, not part of a normal release: it walks the git tags
selected by ``docs_versions.yml``, checks each one out, runs a per-version build
against it, and finally rewrites ``versions.json`` from whatever version dirs end
up on disk. Day to day you never run it; each release builds a single version.
See the command table and the "build-all" note in ``docs/design/docs_site.md``
(parity rows 5b.8 / 5b.12 in ``docs/design/docs_site_parity_audit.md``).

This module holds the pieces that do not touch git, so they are unit-testable on
their own:

- ``VersionsConfig`` + ``load_versions_config`` read ``docs_versions.yml``.
- ``select_tags`` applies the pattern / include / exclude / oldest / newest rules
  and returns the tags newest-first.
- ``needs_rebuild`` is the idempotency check: it compares a version dir's build
  stamp against the tag's commit so an unchanged version is skipped.
- ``bootstrap_versions`` is the rebuild loop. Its git side effects are injected as
  two callables (``tag_sha`` and ``build_one``), so tests drive the whole loop
  with fakes. A later integration step supplies the real git-worktree machinery
  and wires this core into the command line.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from packaging.version import InvalidVersion
from packaging.version import Version as Pep440Version

from docs_site._internal._vendor.mike_versions import Version, Versions
from docs_site._internal.config_loading import DocsConfigError, load_yaml, require_mapping
from docs_site._internal.versioning import BUILD_INFO_NAME, materialize_alias, write_manifest

_TABLE_KEYS = {
    "versions": frozenset({"pattern", "include", "exclude", "oldest", "newest"}),
    "aliases": frozenset({"latest"}),
    "publish": frozenset({"window"}),
    "indexing": frozenset({"keep_recent"}),
}
_RELEASE_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


@dataclass
class VersionsConfig:
    """Validated version-selection, publication, and crawl policy."""

    pattern: str = r"^v?\d+\.\d+\.\d+$"
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    oldest: str = ""
    newest: str = ""
    latest_alias: str = ""  # which version `latest/` points at ("" = newest built)
    publish_window: int = 0  # how many newest releases a deploy publishes (0 = all)
    index_keep_recent: int = 2  # newest releases that remain crawlable (0 = all)


def load_versions_config(path: Path) -> VersionsConfig:
    """
    Read and strictly validate ``docs_versions.yml``.

    A missing file or omitted setting uses the dataclass default. Present values
    must match the documented schema so a typo cannot silently change release or
    crawler policy.
    """
    if not path.is_file():
        return VersionsConfig()
    loaded = load_yaml(path)
    if loaded is None:
        return VersionsConfig()
    data = dict(require_mapping(loaded, str(path)))
    try:
        return _load_versions_data(data)
    except DocsConfigError as exc:
        raise DocsConfigError(f"{path}: {exc}") from exc


def _load_versions_data(data: dict[str, object]) -> VersionsConfig:
    """Validate already parsed version configuration data."""
    _validate_keys(data, allowed=frozenset(_TABLE_KEYS), owner="top level")
    tables = {name: _read_table(data, name) for name in _TABLE_KEYS}
    for name, table in tables.items():
        _validate_keys(table, allowed=_TABLE_KEYS[name], owner=name)

    versions = tables["versions"]
    aliases = tables["aliases"]
    publish = tables["publish"]
    indexing = tables["indexing"]
    defaults = VersionsConfig()
    pattern = _read_string(versions, "pattern", owner="versions", default=defaults.pattern)
    try:
        re.compile(pattern)
    except re.error as error:
        msg = f"versions.pattern is not a valid regular expression: {error}"
        raise DocsConfigError(msg) from error

    include = _read_string_list(versions, "include", owner="versions")
    exclude = _read_string_list(versions, "exclude", owner="versions")
    overlap = sorted(set(include) & set(exclude))
    if overlap:
        msg = f"tags cannot appear in both versions.include and versions.exclude: {', '.join(overlap)}"
        raise DocsConfigError(msg)

    oldest = _read_string(versions, "oldest", owner="versions", default="")
    newest = _read_string(versions, "newest", owner="versions", default="")
    oldest_version = _parse_release_version(oldest, "versions.oldest") if oldest else None
    newest_version = _parse_release_version(newest, "versions.newest") if newest else None
    if oldest_version is not None and newest_version is not None and oldest_version > newest_version:
        msg = "versions.oldest must not be newer than versions.newest"
        raise DocsConfigError(msg)

    latest_alias = _read_string(aliases, "latest", owner="aliases", default="")
    if latest_alias:
        _parse_release_version(latest_alias, "aliases.latest")

    return VersionsConfig(
        pattern=pattern,
        include=include,
        exclude=exclude,
        oldest=oldest,
        newest=newest,
        latest_alias=latest_alias,
        publish_window=_read_non_negative_int(publish, "window", owner="publish", default=0),
        index_keep_recent=_read_non_negative_int(
            indexing,
            "keep_recent",
            owner="indexing",
            default=defaults.index_keep_recent,
        ),
    )


def _validate_keys(data: dict[str, object], *, allowed: frozenset[str], owner: str) -> None:
    """Reject unknown keys in a settings table."""
    unknown = sorted(set(data) - allowed)
    if unknown:
        prefix = "" if owner == "top level" else f"{owner}."
        msg = f"unknown {owner} setting(s): {', '.join(prefix + key for key in unknown)}"
        raise DocsConfigError(msg)


def _read_table(data: dict[str, object], name: str) -> dict[str, object]:
    """Return one optional YAML mapping with an exact mapping type."""
    value = data.get(name, {})
    if not isinstance(value, dict):
        msg = f"{name} must be a mapping"
        raise DocsConfigError(msg)
    return value


def _read_string(data: dict[str, object], key: str, *, owner: str, default: str) -> str:
    """Read an optional string setting without coercion."""
    value = data.get(key, default)
    if not isinstance(value, str):
        msg = f"{owner}.{key} must be a string"
        raise DocsConfigError(msg)
    if key == "pattern" and not value:
        msg = f"{owner}.{key} must not be empty"
        raise DocsConfigError(msg)
    return value


def _read_string_list(data: dict[str, object], key: str, *, owner: str) -> list[str]:
    """Read an optional list of unique, non-empty strings."""
    value = data.get(key, [])
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        msg = f"{owner}.{key} must be a list of non-empty strings"
        raise DocsConfigError(msg)
    if len(value) != len(set(value)):
        msg = f"{owner}.{key} must not contain duplicate tags"
        raise DocsConfigError(msg)
    return list(value)


def _read_non_negative_int(data: dict[str, object], key: str, *, owner: str, default: int) -> int:
    """Read an integer count, rejecting booleans and negative values."""
    value = data.get(key, default)
    if type(value) is not int:  # bool is an int subclass but not a valid policy count
        msg = f"{owner}.{key} must be an integer"
        raise DocsConfigError(msg)
    if value < 0:
        msg = f"{owner}.{key} must not be negative"
        raise DocsConfigError(msg)
    return value


def _parse_release_version(value: str, field_name: str) -> Pep440Version:
    """Validate a canonical, full three-part release version."""
    if not _RELEASE_VERSION_RE.fullmatch(value):
        msg = f"{field_name} must be empty or a full major.minor.patch version"
        raise DocsConfigError(msg)
    try:
        return Pep440Version(value)
    except InvalidVersion as error:
        msg = f"{field_name} is not a valid version: {value!r}"
        raise DocsConfigError(msg) from error


def tag_to_version(tag: str) -> str:
    """Canonical version string for a tag (strip a single leading ``v``)."""
    return tag.removeprefix("v")


def _lv(tag: str) -> Version:
    """Parse a tag into a comparable version, used for the oldest/newest bounds and the sort."""
    return Version(tag_to_version(tag))


def select_tags(all_tags: list[str], config: VersionsConfig) -> list[str]:
    """
    Filter ``all_tags`` by the config and return them newest-first.

    Pattern-matched tags are held to the oldest/newest bounds. ``include`` entries
    that are real tags are always kept, bypassing both the pattern and the bounds.
    """
    excluded = set(config.exclude)
    rx = re.compile(config.pattern)

    matched = [t for t in all_tags if t not in excluded and rx.match(t)]
    if config.oldest:
        matched = [t for t in matched if _lv(t) >= _lv(config.oldest)]
    if config.newest:
        matched = [t for t in matched if _lv(t) <= _lv(config.newest)]

    extras = [t for t in config.include if t in all_tags and t not in excluded]
    # Remove duplicates while keeping first-seen order, then sort newest-first.
    result = list(dict.fromkeys(matched + extras))
    result.sort(key=_lv, reverse=True)
    return result


def needs_rebuild(version_dir: Path, expected_sha: str) -> bool:
    """
    True when ``version_dir`` is missing, unstamped, or was built from a different
    commit than ``expected_sha``.

    This is the idempotency check: it lets a second ``build-all`` run skip every
    version that is already built from the current tag.
    """
    stamp = version_dir / BUILD_INFO_NAME
    if not stamp.is_file():
        return True
    try:
        data = json.loads(stamp.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return True
    return data.get("source_sha") != expected_sha


@dataclass
class BootstrapOutcome:
    """What ``bootstrap_versions`` did, split by result so the caller can report it."""

    built: list[str] = field(default_factory=list)
    skipped_up_to_date: list[str] = field(default_factory=list)
    skipped_no_builder: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)


# build_one(tag, version, version_dir) -> "built" | "skipped_no_builder". It raises
# on a real build failure, which bootstrap_versions catches and records per tag.
BuildOne = Callable[[str, str, Path], str]


def bootstrap_versions(
    config: VersionsConfig,
    *,
    versions_root: Path,
    all_tags: list[str],
    tag_sha: Callable[[str], str],
    build_one: BuildOne,
    log: Callable[[str], None] = lambda _msg: None,
) -> BootstrapOutcome:
    """
    Walk the selected tags, rebuild the stale ones, then rewrite the manifest once.

    A single bad tag is recorded and skipped, never fatal, so one broken version
    does not sink the whole run. The manifest is rebuilt at the end from whatever
    version dirs exist on disk, so it always reflects the full, consistent set
    rather than a half-finished state, and the ``latest`` alias is materialized as
    redirect stubs pointing at its target version.
    """
    outcome = BootstrapOutcome()
    selected = select_tags(all_tags, config)
    log(f"Selected {len(selected)} tag(s): {', '.join(selected) or '(none)'}")

    for tag in selected:
        version = tag_to_version(tag)
        version_dir = versions_root / version
        if not needs_rebuild(version_dir, tag_sha(tag)):
            outcome.skipped_up_to_date.append(version)
            log(f"  = {version}: up to date, skipping")
            continue
        try:
            status = build_one(tag, version, version_dir)
        except Exception as e:  # noqa: BLE001 - one bad tag must not abort the whole walk
            outcome.failed.append(version)
            log(f"  ! {version}: build failed: {type(e).__name__}: {e}")
            continue
        if status == "skipped_no_builder":
            outcome.skipped_no_builder.append(version)
        else:
            outcome.built.append(version)
            log(f"  + {version}: built")

    _rewrite_manifest(versions_root, config, log)
    return outcome


def _rewrite_manifest(versions_root: Path, config: VersionsConfig, log: Callable[[str], None]) -> None:
    """Rebuild versions.json from the on-disk, stamped version dirs and re-point ``latest``."""
    version_dirs = (
        sorted(d.name for d in versions_root.iterdir() if d.is_dir() and (d / BUILD_INFO_NAME).is_file())
        if versions_root.is_dir()
        else []
    )

    versions = Versions()
    for name in version_dirs:
        versions.add(name)

    # Resolve the `latest` alias target: the explicit config value, else the newest
    # built version (the manifest's first entry by the version ordering).
    latest = config.latest_alias
    if not latest and len(versions):
        latest = str(next(iter(versions)).version)

    if latest and latest in version_dirs:
        versions.add(latest, aliases=["latest"], update_aliases=True)
        n = materialize_alias(versions_root, "latest", latest)
        log(f"latest/ -> {latest} ({n} redirects)")
    elif latest:
        log(f"WARNING: latest alias target {latest!r} has no built version dir; skipping alias")

    write_manifest(versions_root, versions)
    log(f"Wrote manifest with {len(versions)} version(s)")
