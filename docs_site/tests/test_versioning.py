"""Tests for the docs version tree: manifest ordering, build stamp, aliases."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from docs_site._internal.config_loading import DocsConfigError
from docs_site._internal.versioning import (
    BUILD_INFO_NAME,
    load_manifest,
    materialize_alias,
    select_indexed_versions,
    update_manifest,
    write_build_info,
)


def _four_versions(root: Path) -> None:
    """A manifest with four releases, ``latest`` on the newest (newest-first: 1.3.0..1.0.0)."""
    update_manifest(root, "1.0.0")
    update_manifest(root, "1.1.0")
    update_manifest(root, "1.2.0")
    update_manifest(root, "1.3.0", aliases=("latest",))


def test_select_indexed_versions_keeps_newest_two_plus_latest(tmp_path: Path) -> None:
    _four_versions(tmp_path)
    versions = load_manifest(tmp_path)

    # The newest two stay indexed; the older two fall out.
    assert select_indexed_versions(versions, keep_recent=2) == ["1.3.0", "1.2.0"]
    # keep_recent tunes the window; 0 keeps everything (nothing is "old").
    assert select_indexed_versions(versions, keep_recent=1) == ["1.3.0"]
    assert select_indexed_versions(versions, keep_recent=0) == ["1.3.0", "1.2.0", "1.1.0", "1.0.0"]
    assert select_indexed_versions(load_manifest(tmp_path / "missing"), keep_recent=2) == []


def test_select_indexed_versions_keeps_the_latest_alias_target(tmp_path: Path) -> None:
    # latest deliberately points at the oldest release: it must stay indexed on
    # top of the newest two, so a reader following /latest/ never hits noindex.
    update_manifest(tmp_path, "1.0.0", aliases=("latest",))
    update_manifest(tmp_path, "1.1.0")
    update_manifest(tmp_path, "1.2.0")
    update_manifest(tmp_path, "1.3.0")

    assert select_indexed_versions(load_manifest(tmp_path), keep_recent=2) == ["1.3.0", "1.2.0", "1.0.0"]


def test_select_indexed_versions_keeps_dev_without_consuming_a_release_slot(tmp_path: Path) -> None:
    # A committed dev snapshot stays indexed but must not push a real release out
    # of the newest-two window: robots reads the committed manifest (with dev) and
    # the noindex pass reads the mounted one (dev excluded), so if dev ate a slot
    # the two would disagree on which release is "old". dev is kept plus the newest
    # two releases (1.3.0, 1.2.0), not just the newest one.
    for v in ("1.0.0", "1.1.0", "1.2.0", "1.3.0"):
        update_manifest(tmp_path, v)
    update_manifest(tmp_path, "1.3.0", aliases=("latest",))
    update_manifest(tmp_path, "dev")

    assert select_indexed_versions(load_manifest(tmp_path), keep_recent=2) == ["dev", "1.3.0", "1.2.0"]


def test_manifest_orders_dev_above_releases(tmp_path: Path) -> None:
    update_manifest(tmp_path, "1.0.0")
    update_manifest(tmp_path, "1.1.0", aliases=("latest",))
    update_manifest(tmp_path, "dev")

    versions = load_manifest(tmp_path)

    assert [str(v.version) for v in versions] == ["dev", "1.1.0", "1.0.0"]
    assert versions.find("latest") == ("1.1.0", "latest")


def test_alias_moves_onto_the_newer_version(tmp_path: Path) -> None:
    update_manifest(tmp_path, "1.0.0", aliases=("latest",))
    update_manifest(tmp_path, "2.0.0", aliases=("latest",))

    versions = load_manifest(tmp_path)

    assert versions.find("latest") == ("2.0.0", "latest")
    assert "latest" not in versions["1.0.0"].aliases


def test_write_build_info_records_the_build(tmp_path: Path) -> None:
    info = write_build_info(tmp_path / "1.0.0", version="1.0.0", source_sha="abc123")

    assert info["version"] == "1.0.0"
    assert info["source_sha"] == "abc123"
    on_disk = json.loads((tmp_path / "1.0.0" / BUILD_INFO_NAME).read_text(encoding="utf-8"))
    assert on_disk["builder_version"]


def test_materialize_alias_writes_relative_redirects(tmp_path: Path) -> None:
    (tmp_path / "1.0.0" / "foo").mkdir(parents=True)
    (tmp_path / "1.0.0" / "index.html").write_text("home", encoding="utf-8")
    (tmp_path / "1.0.0" / "foo" / "index.html").write_text("foo", encoding="utf-8")

    count = materialize_alias(tmp_path, "latest", "1.0.0")

    assert count == 2
    stub = (tmp_path / "latest" / "foo" / "index.html").read_text(encoding="utf-8")
    assert "../../1.0.0/foo/index.html" in stub  # a relative href into the version tree


def test_materialize_alias_clears_stale_redirects(tmp_path: Path) -> None:
    for v in ("1.0.0", "2.0.0"):
        (tmp_path / v).mkdir()
        (tmp_path / v / "index.html").write_text(v, encoding="utf-8")
    materialize_alias(tmp_path, "latest", "1.0.0")
    (tmp_path / "latest" / "stale.html").write_text("old", encoding="utf-8")

    materialize_alias(tmp_path, "latest", "2.0.0")  # re-point the alias

    assert not (tmp_path / "latest" / "stale.html").exists()  # the stale stub was cleared
    assert "2.0.0/index.html" in (tmp_path / "latest" / "index.html").read_text(encoding="utf-8")


@pytest.mark.parametrize("alias", ["../content", "/absolute", "nested/latest"])
def test_materialize_alias_rejects_path_traversal_without_deleting_sources(tmp_path: Path, alias: str) -> None:
    versions = tmp_path / "versions"
    target = versions / "1.0.0"
    target.mkdir(parents=True)
    (target / "index.html").write_text("target", encoding="utf-8")
    source = tmp_path / "content"
    source.mkdir()
    sentinel = source / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(DocsConfigError, match="single segment"):
        materialize_alias(versions, alias, "1.0.0")

    assert sentinel.read_text(encoding="utf-8") == "keep"
    assert (target / "index.html").read_text(encoding="utf-8") == "target"


def test_materialize_alias_rejects_its_target_and_other_versions(tmp_path: Path) -> None:
    for version in ("1.0.0", "2.0.0"):
        version_dir = tmp_path / version
        version_dir.mkdir()
        (version_dir / "index.html").write_text(version, encoding="utf-8")
        write_build_info(version_dir, version=version, source_sha="abc")
        update_manifest(tmp_path, version)

    with pytest.raises(DocsConfigError, match="differ from its target"):
        materialize_alias(tmp_path, "1.0.0", "1.0.0")
    with pytest.raises(DocsConfigError, match=r"versions\.json"):
        materialize_alias(tmp_path, "2.0.0", "1.0.0")

    assert (tmp_path / "1.0.0" / "index.html").read_text(encoding="utf-8") == "1.0.0"
    assert (tmp_path / "2.0.0" / "index.html").read_text(encoding="utf-8") == "2.0.0"


def test_materialize_alias_checks_target_before_clearing_existing_alias(tmp_path: Path) -> None:
    alias = tmp_path / "latest"
    alias.mkdir()
    sentinel = alias / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(DocsConfigError, match="target directory does not exist"):
        materialize_alias(tmp_path, "latest", "1.0.0")

    assert sentinel.read_text(encoding="utf-8") == "keep"
