"""
Tests for the git-free core of ``docs build-all`` (parity 5b.8 core, 5b.12).

Covers ``docs_site/_internal/bootstrap.py``: config parsing, tag selection, the idempotency
check, and the orchestration loop. The loop is driven with an injected fake
``build_one`` + ``tag_sha``, so no git or worktrees are needed here; the real
worktree machinery is a later integration step, exercised separately.
"""

from __future__ import annotations

from pathlib import Path

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


def test_load_config_parses_toml(tmp_path: Path) -> None:
    (tmp_path / "docs_versions.toml").write_text(
        '[versions]\npattern = "^x"\nexclude = ["0.1.0"]\noldest = "0.1.0"\n'
        '[aliases]\nlatest = "0.2.0"\n[publish]\nwindow = 7\n',
        encoding="utf-8",
    )

    cfg = load_versions_config(tmp_path / "docs_versions.toml")

    assert cfg.pattern == "^x"
    assert cfg.exclude == ["0.1.0"]
    assert cfg.oldest == "0.1.0"
    assert cfg.latest_alias == "0.2.0"
    assert cfg.publish_window == 7


def test_load_config_missing_file_uses_defaults(tmp_path: Path) -> None:
    cfg = load_versions_config(tmp_path / "nope.toml")

    assert cfg.pattern  # a default pattern is always present
    assert cfg.exclude == []
    assert cfg.publish_window == 0


def test_repo_config_parses_and_sets_a_floor() -> None:
    # The committed docs_versions.toml must parse, set a floor, and be the single
    # source of truth the DocsConfig reads the publish window from.
    cfg = load_versions_config(docs_config.versions_config)

    assert cfg.pattern
    assert cfg.oldest
    assert cfg.publish_window == docs_config.publish_window


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
