"""
Tests for the git-free core of ``docs build-all`` (parity 5b.8 core, 5b.12).

Covers ``docs_site/_internal/bootstrap.py``: config parsing, tag selection, the idempotency
check, and the orchestration loop. The loop is driven with an injected fake
``build_one`` + ``tag_sha``, so no git or worktrees are needed here; the real
worktree machinery is a later integration step, exercised separately.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from docs_site._internal.bootstrap import (
    VersionsConfig,
    bootstrap_versions,
    load_versions_config,
    needs_rebuild,
    select_tags,
    tag_to_version,
)
from docs_site._internal.config import config as docs_config
from docs_site._internal.versioning import load_manifest, write_build_info

# -- config --------------------------------------------------------------------


def test_load_config_parses_yaml(tmp_path: Path) -> None:
    (tmp_path / "docs_versions.yml").write_text(
        'versions:\n  pattern: "^x"\n  exclude: ["0.1.0"]\n  oldest: "0.1.0"\n'
        'aliases:\n  latest: "0.2.0"\npublish:\n  window: 7\nindexing:\n  keep_recent: 3\n',
        encoding="utf-8",
    )

    cfg = load_versions_config(tmp_path / "docs_versions.yml")

    assert cfg.pattern == "^x"
    assert cfg.exclude == ["0.1.0"]
    assert cfg.oldest == "0.1.0"
    assert cfg.latest_alias == "0.2.0"
    assert cfg.publish_window == 7
    assert cfg.index_keep_recent == 3


def test_load_config_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="configuration file does not exist"):
        load_versions_config(tmp_path / "nope.yml")


def test_load_config_empty_yaml_uses_defaults(tmp_path: Path) -> None:
    path = tmp_path / "docs_versions.yml"
    path.write_text("", encoding="utf-8")

    assert load_versions_config(path) == VersionsConfig()


def test_load_config_rejects_duplicate_yaml_keys(tmp_path: Path) -> None:
    path = tmp_path / "docs_versions.yml"
    path.write_text("publish:\n  window: 1\n  window: 2\n", encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate YAML key"):
        load_versions_config(path)


def test_load_config_rejects_non_string_nested_keys(tmp_path: Path) -> None:
    path = tmp_path / "docs_versions.yml"
    path.write_text("versions:\n  1: value\n", encoding="utf-8")

    with pytest.raises(ValueError, match="mapping with string keys"):
        load_versions_config(path)


@pytest.mark.parametrize(
    "text",
    [
        'versions:\n  pattern: "   "\n',
        'versions:\n  include: ["   "]\n',
        'versions:\n  exclude: ["   "]\n',
        'versions:\n  include: [" 1.0.0"]\n',
        'versions:\n  exclude: ["1.0.0 "]\n',
    ],
)
def test_load_config_rejects_whitespace_only_strings(tmp_path: Path, text: str) -> None:
    path = tmp_path / "docs_versions.yml"
    path.write_text(text, encoding="utf-8")

    with pytest.raises(ValueError, match=r"versions\.(?:pattern|include|exclude)"):
        load_versions_config(path)


def test_repo_config_parses_and_sets_a_floor() -> None:
    # The committed docs_versions.yml must parse, set a floor, and be the single
    # source of truth the DocsConfig reads the publish window from.
    cfg = load_versions_config(docs_config.versions_config)

    assert cfg.pattern
    assert cfg.oldest
    assert cfg.publish_window == docs_config.publish_window
    assert cfg.index_keep_recent == 2


@pytest.mark.parametrize(
    ("text", "field"),
    [
        ("unexpected:\n  value: 1\n", "unexpected"),
        ("versions:\n  unknown: 1\n", "versions.unknown"),
        ("aliases:\n  unknown: 1\n", "aliases.unknown"),
        ("publish:\n  unknown: 1\n", "publish.unknown"),
        ("indexing:\n  unknown: 1\n", "indexing.unknown"),
    ],
)
def test_load_config_rejects_unknown_tables_and_keys(tmp_path: Path, text: str, field: str) -> None:
    path = tmp_path / "docs_versions.yml"
    path.write_text(text, encoding="utf-8")

    with pytest.raises(ValueError, match=field):
        load_versions_config(path)


@pytest.mark.parametrize(
    ("text", "field"),
    [
        ('versions: "nope"\n', "versions"),
        ("versions:\n  pattern: 1\n", "versions.pattern"),
        ('versions:\n  include: "1.0.0"\n', "versions.include"),
        ("versions:\n  include: [1]\n", "versions.include"),
        ("versions:\n  exclude: [false]\n", "versions.exclude"),
        ("versions:\n  oldest: 1\n", "versions.oldest"),
        ("versions:\n  newest: false\n", "versions.newest"),
        ("aliases:\n  latest: 1\n", "aliases.latest"),
        ('publish:\n  window: "1"\n', "publish.window"),
        ("publish:\n  window: true\n", "publish.window"),
        ('indexing:\n  keep_recent: "2"\n', "indexing.keep_recent"),
        ("indexing:\n  keep_recent: false\n", "indexing.keep_recent"),
    ],
)
def test_load_config_rejects_wrong_types(tmp_path: Path, text: str, field: str) -> None:
    path = tmp_path / "docs_versions.yml"
    path.write_text(text, encoding="utf-8")

    with pytest.raises(ValueError, match=field):
        load_versions_config(path)


def test_load_config_rejects_invalid_pattern(tmp_path: Path) -> None:
    path = tmp_path / "docs_versions.yml"
    path.write_text('versions:\n  pattern: "["\n', encoding="utf-8")

    with pytest.raises(ValueError, match=r"versions\.pattern"):
        load_versions_config(path)


@pytest.mark.parametrize(
    ("section", "key"),
    [("publish", "window"), ("indexing", "keep_recent")],
)
def test_load_config_rejects_negative_counts(tmp_path: Path, section: str, key: str) -> None:
    path = tmp_path / "docs_versions.yml"
    path.write_text(f"{section}:\n  {key}: -1\n", encoding="utf-8")

    with pytest.raises(ValueError, match=rf"{section}\.{key}"):
        load_versions_config(path)


def test_load_config_rejects_include_exclude_overlap(tmp_path: Path) -> None:
    path = tmp_path / "docs_versions.yml"
    path.write_text(
        'versions:\n  include: ["nightly", "1.0.0"]\n  exclude: ["1.0.0"]\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=r"both versions\.include and versions\.exclude"):
        load_versions_config(path)


@pytest.mark.parametrize("field", ["include", "exclude"])
def test_load_config_rejects_multi_segment_tag_identifiers(tmp_path: Path, field: str) -> None:
    path = tmp_path / "docs_versions.yml"
    path.write_text(f'versions:\n  {field}: ["feature/foo"]\n', encoding="utf-8")

    with pytest.raises(ValueError, match=rf"versions\.{field}\[0\].*single segment"):
        load_versions_config(path)


@pytest.mark.parametrize("field", ["oldest", "newest"])
@pytest.mark.parametrize("value", ["1.0", "v1.0.0", "nightly", "../1.0.0"])
def test_load_config_rejects_malformed_version_bounds(tmp_path: Path, field: str, value: str) -> None:
    path = tmp_path / "docs_versions.yml"
    path.write_text(f'versions:\n  {field}: "{value}"\n', encoding="utf-8")

    with pytest.raises(ValueError, match=rf"versions\.{field}"):
        load_versions_config(path)


def test_load_config_rejects_reversed_version_bounds(tmp_path: Path) -> None:
    path = tmp_path / "docs_versions.yml"
    path.write_text('versions:\n  oldest: "2.0.0"\n  newest: "1.0.0"\n', encoding="utf-8")

    with pytest.raises(ValueError, match=r"oldest.*newest"):
        load_versions_config(path)


@pytest.mark.parametrize("latest", ["1.0", "v1.0.0", "latest", "../1.0.0"])
def test_load_config_rejects_invalid_latest_alias_target(tmp_path: Path, latest: str) -> None:
    path = tmp_path / "docs_versions.yml"
    path.write_text(f'aliases:\n  latest: "{latest}"\n', encoding="utf-8")

    with pytest.raises(ValueError, match=r"aliases\.latest"):
        load_versions_config(path)


# -- tag selection -------------------------------------------------------------


def test_tag_to_version_strips_leading_v() -> None:
    assert tag_to_version("v0.2.0") == "0.2.0"
    assert tag_to_version("0.2.0") == "0.2.0"


def test_select_tags_filters_bounds_excludes_and_sorts() -> None:
    cfg = VersionsConfig(exclude=["0.1.1"], oldest="0.1.0", newest="0.3.0")
    tags = ["0.0.9", "0.1.0", "0.1.1", "0.2.0", "0.3.0", "0.4.0", "random", "v0.2.5"]
    # 0.0.9 below oldest, 0.4.0 above newest, 0.1.1 excluded, "random" no match;
    # v0.2.5 is kept and sorted by its parsed version (between 0.3.0 and 0.2.0).
    assert select_tags(tags, cfg) == ["0.3.0", "v0.2.5", "0.2.0", "0.1.0"]


def test_select_tags_rejects_a_pattern_selected_multi_segment_tag() -> None:
    with pytest.raises(ValueError, match=r"selected tag.*single segment"):
        select_tags(["feature/foo"], VersionsConfig(pattern=".*"))


def test_select_tags_include_bypasses_pattern() -> None:
    cfg = VersionsConfig(include=["nightly"], oldest="")
    out = select_tags(["0.2.0", "nightly", "not-listed"], cfg)

    assert "nightly" in out  # kept despite not matching the version pattern
    assert "not-listed" not in out
    assert out[0] == "nightly"  # a non-release label sorts above releases


# -- idempotency ---------------------------------------------------------------


def test_needs_rebuild_when_dir_or_stamp_absent(tmp_path: Path) -> None:
    assert needs_rebuild(tmp_path / "missing", "abc")  # no dir
    (tmp_path / "0.2.0").mkdir()
    assert needs_rebuild(tmp_path / "0.2.0", "abc")  # dir but no stamp


def test_needs_rebuild_compares_source_sha(tmp_path: Path) -> None:
    write_build_info(tmp_path, version="0.2.0", source_sha="abc123")

    assert not needs_rebuild(tmp_path, "abc123")  # same commit -> skip
    assert needs_rebuild(tmp_path, "different")  # different commit -> rebuild


# -- orchestration -------------------------------------------------------------


def _fake_build_one(shas, no_builder=()):
    """A build_one that writes a fake snapshot + stamp instead of touching git."""

    def build_one(tag: str, version: str, version_dir: Path) -> str:
        if version in no_builder:
            return "skipped_no_builder"
        version_dir.mkdir(parents=True, exist_ok=True)
        (version_dir / "index.html").write_text("<html>built</html>", encoding="utf-8")
        write_build_info(version_dir, version=version, source_sha=shas[tag])
        return "built"

    return build_one


def test_bootstrap_builds_selected_and_writes_manifest(tmp_path: Path) -> None:
    cfg = VersionsConfig(oldest="0.1.0")
    tags = ["0.0.9", "0.1.0", "0.2.0"]  # 0.0.9 is below the floor
    shas = {t: f"sha-{t}" for t in tags}

    out = bootstrap_versions(
        cfg, versions_root=tmp_path, all_tags=tags, tag_sha=lambda t: shas[t], build_one=_fake_build_one(shas)
    )
    assert out.built == ["0.2.0", "0.1.0"]  # newest-first, 0.0.9 skipped below the floor

    versions = load_manifest(tmp_path)
    assert [str(v.version) for v in versions] == ["0.2.0", "0.1.0"]
    # `latest` defaults to the newest built version and is materialized as redirects.
    assert versions["0.2.0"].aliases == {"latest"}
    assert (tmp_path / "latest" / "index.html").is_file()


def test_bootstrap_second_run_is_idempotent(tmp_path: Path) -> None:
    cfg = VersionsConfig(oldest="0.1.0")
    tags = ["0.1.0", "0.2.0"]
    shas = {t: f"sha-{t}" for t in tags}

    def run():
        return bootstrap_versions(
            cfg, versions_root=tmp_path, all_tags=tags, tag_sha=lambda t: shas[t], build_one=_fake_build_one(shas)
        )

    run()
    out2 = run()

    assert out2.built == []
    assert sorted(out2.skipped_up_to_date) == ["0.1.0", "0.2.0"]


def test_bootstrap_records_failure_without_aborting(tmp_path: Path) -> None:
    cfg = VersionsConfig(oldest="0.1.0")
    tags = ["0.1.0", "0.2.0"]
    shas = {t: f"sha-{t}" for t in tags}

    def build_one(tag: str, version: str, version_dir: Path) -> str:
        if version == "0.2.0":
            raise RuntimeError("boom")
        version_dir.mkdir(parents=True, exist_ok=True)
        (version_dir / "index.html").write_text("x", encoding="utf-8")
        write_build_info(version_dir, version=version, source_sha=shas[tag])
        return "built"

    out = bootstrap_versions(
        cfg, versions_root=tmp_path, all_tags=tags, tag_sha=lambda t: shas[t], build_one=build_one
    )

    assert out.failed == ["0.2.0"]
    assert out.built == ["0.1.0"]  # the other tag still built
    # The manifest is rebuilt from disk, so it lists only what actually built.
    assert [str(v.version) for v in load_manifest(tmp_path)] == ["0.1.0"]


def test_bootstrap_skips_tags_without_builder(tmp_path: Path) -> None:
    cfg = VersionsConfig(oldest="0.1.0")
    tags = ["0.1.0", "0.2.0"]
    shas = {t: f"sha-{t}" for t in tags}

    out = bootstrap_versions(
        cfg,
        versions_root=tmp_path,
        all_tags=tags,
        tag_sha=lambda t: shas[t],
        build_one=_fake_build_one(shas, no_builder={"0.1.0"}),
    )

    assert out.skipped_no_builder == ["0.1.0"]
    assert out.built == ["0.2.0"]
