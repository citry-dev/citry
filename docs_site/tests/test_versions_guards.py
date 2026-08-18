"""
Tests for the version-tree guards (parity rows 5b.13 / 5b.14 / 5b.15).

These guards validate the committed ``versions/`` tree rather than a single build,
so the fixtures here are small synthetic ``versions/`` trees built with the real
versioning helpers (``write_build_info`` / ``write_manifest`` / ``materialize_alias``)
under ``tmp_path``. The wiring the versions-check command uses
(``make_versions_context``) is exercised against one of those synthetic trees.
"""

from __future__ import annotations

import json
from pathlib import Path

from docs_site._internal._vendor.mike_versions import Versions
from docs_site._internal.guards import cross_version_link, make_versions_context, versions_manifest
from docs_site._internal.guards.base import GuardContext, Severity
from docs_site._internal.versioning import (
    BUILD_INFO_NAME,
    DOCS_BUILDER_VERSION,
    IMPORTED_BUILDER_VERSION,
    materialize_alias,
    write_build_info,
    write_manifest,
)

_PAGE = "<html><body>hi</body></html>"


def _make_version(
    root: Path,
    version: str,
    *,
    pages: tuple[str, ...] = ("index.html",),
    builder_version: str = DOCS_BUILDER_VERSION,
) -> Path:
    """Create a built version dir: a ``_build_info.json`` stamp plus the given pages."""
    vdir = root / version
    write_build_info(vdir, version=version, source_sha="deadbeef", builder_version=builder_version)
    for rel in pages:
        page = vdir / rel
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(_PAGE, encoding="utf-8")
    return vdir


def _write_versions(root: Path, entries: list[tuple[str, tuple[str, ...]]]) -> None:
    """Write a ``versions.json`` manifest from ``(version, aliases)`` entries."""
    versions = Versions()
    for version, aliases in entries:
        versions.add(version, aliases=list(aliases), update_aliases=True)
    write_manifest(root, versions)


def _versions_ctx(root: Path) -> GuardContext:
    """A GuardContext whose ``versions_dir`` points at ``root``; other paths go unused."""
    return GuardContext(
        content_dir=root,
        examples_dir=root,
        nav_path=root / "_nav.yml",
        static_dir=root,
        repo_root=root,
        versions_dir=root,
    )


def _errors(results: list) -> list:
    return [r for r in results if r.severity is Severity.ERROR]


def test_clean_two_version_tree_passes(tmp_path: Path) -> None:
    root = tmp_path / "versions"
    _make_version(root, "0.1.0")
    _make_version(root, "0.2.0")
    _write_versions(root, [("0.1.0", ()), ("0.2.0", ())])

    assert list(versions_manifest.check(_versions_ctx(root))) == []


def test_malformed_snapshot_site_routes_errors(tmp_path: Path) -> None:
    root = tmp_path / "versions"
    vdir = _make_version(root, "0.1.0")
    stamp = vdir / BUILD_INFO_NAME
    data = json.loads(stamp.read_text(encoding="utf-8"))
    data["site_routes"] = ["blog/*"]
    stamp.write_text(json.dumps(data), encoding="utf-8")
    _write_versions(root, [("0.1.0", ())])

    errors = _errors(list(versions_manifest.check(_versions_ctx(root))))

    assert len(errors) == 1
    assert "site_routes" in errors[0].message


def test_orphan_dir_without_manifest_entry_errors(tmp_path: Path) -> None:
    # A stamped version dir that the manifest does not list is an orphan.
    root = tmp_path / "versions"
    _make_version(root, "0.1.0")
    _make_version(root, "0.9.0")
    _write_versions(root, [("0.1.0", ())])

    errors = _errors(list(versions_manifest.check(_versions_ctx(root))))

    assert len(errors) == 1
    assert errors[0].source == "0.9.0"
    assert "not listed in versions.json" in errors[0].message


def test_manifest_entry_without_dir_errors(tmp_path: Path) -> None:
    # The other direction: a manifest entry with no version dir on disk.
    root = tmp_path / "versions"
    _make_version(root, "0.1.0")
    _write_versions(root, [("0.1.0", ()), ("0.2.0", ())])

    errors = _errors(list(versions_manifest.check(_versions_ctx(root))))

    assert len(errors) == 1
    assert errors[0].source == "0.2.0"
    assert "0.2.0/ does not exist" in errors[0].message


def test_version_dir_missing_build_info_errors(tmp_path: Path) -> None:
    # A dir with a homepage but no build stamp is half-built.
    root = tmp_path / "versions"
    vdir = root / "0.1.0"
    vdir.mkdir(parents=True)
    (vdir / "index.html").write_text(_PAGE, encoding="utf-8")
    _write_versions(root, [("0.1.0", ())])

    errors = _errors(list(versions_manifest.check(_versions_ctx(root))))

    assert len(errors) == 1
    assert "half-built: no _build_info.json" in errors[0].message


def test_build_info_missing_required_field_errors(tmp_path: Path) -> None:
    # A build stamp missing a required field (here source_sha) is rejected.
    root = tmp_path / "versions"
    vdir = root / "0.1.0"
    vdir.mkdir(parents=True)
    (vdir / "index.html").write_text(_PAGE, encoding="utf-8")
    (vdir / BUILD_INFO_NAME).write_text(
        json.dumps({"version": "0.1.0", "built_at": "t", "builder_version": "1.0.0"}), encoding="utf-8"
    )
    _write_versions(root, [("0.1.0", ())])

    errors = _errors(list(versions_manifest.check(_versions_ctx(root))))

    assert len(errors) == 1
    assert "missing field(s): source_sha" in errors[0].message


def test_build_info_version_mismatch_errors(tmp_path: Path) -> None:
    # A stamp whose own `version` field does not name its directory is a mislabeled
    # build: here 0.1.0/ carries a stamp recording version 9.9.9.
    root = tmp_path / "versions"
    vdir = root / "0.1.0"
    vdir.mkdir(parents=True)
    (vdir / "index.html").write_text(_PAGE, encoding="utf-8")
    write_build_info(vdir, version="9.9.9", source_sha="deadbeef")
    _write_versions(root, [("0.1.0", ())])

    errors = _errors(list(versions_manifest.check(_versions_ctx(root))))

    assert len(errors) == 1
    assert errors[0].source == "0.1.0"
    assert "records version '9.9.9'" in errors[0].message
    assert "the directory is '0.1.0'" in errors[0].message


def test_valid_alias_passes(tmp_path: Path) -> None:
    root = tmp_path / "versions"
    _make_version(root, "0.1.0")
    _write_versions(root, [("0.1.0", ("latest",))])
    materialize_alias(root, "latest", "0.1.0")

    assert list(versions_manifest.check(_versions_ctx(root))) == []


def test_alias_without_index_errors(tmp_path: Path) -> None:
    root = tmp_path / "versions"
    _make_version(root, "0.1.0")
    _write_versions(root, [("0.1.0", ("latest",))])
    (root / "latest").mkdir()  # alias dir exists but carries no redirect stub

    errors = _errors(list(versions_manifest.check(_versions_ctx(root))))

    assert len(errors) == 1
    assert "Alias latest/ has no index.html redirect" in errors[0].message


def test_alias_wrong_redirect_target_errors(tmp_path: Path) -> None:
    # The manifest says latest -> 0.2.0, but the stub still redirects to 0.1.0.
    root = tmp_path / "versions"
    _make_version(root, "0.1.0")
    _make_version(root, "0.2.0")
    _write_versions(root, [("0.1.0", ()), ("0.2.0", ("latest",))])
    materialize_alias(root, "latest", "0.1.0")

    errors = _errors(list(versions_manifest.check(_versions_ctx(root))))

    assert len(errors) == 1
    assert "does not redirect to its manifest target '0.2.0'" in errors[0].message


def test_cross_version_link_valid_passes(tmp_path: Path) -> None:
    # In the committed tree a cross-version link is a relative path (../<other>/..),
    # which the guard resolves against one index of the whole tree.
    root = tmp_path / "versions"
    _make_version(root, "0.1.0", pages=("index.html", "concepts/index.html"))
    _make_version(root, "0.2.0")
    (root / "0.2.0" / "index.html").write_text(
        '<html><body><a href="../0.1.0/concepts/">old concepts</a></body></html>', encoding="utf-8"
    )
    _write_versions(root, [("0.1.0", ()), ("0.2.0", ())])

    assert list(cross_version_link.check(_versions_ctx(root))) == []


def test_cross_version_link_skips_isolated_previews_and_structured_api_assets(tmp_path: Path) -> None:
    root = tmp_path / "versions"
    _make_version(
        root,
        "0.4.0",
        pages=(
            "index.html",
            "ui-library/components/widget/index.html",
            "ui-library/components/widget/_previews/navigation/index.html",
        ),
    )
    component = root / "0.4.0/ui-library/components/widget"
    (component / "index.html").write_text(
        '<html><body><a href="api.yml">structured API</a></body></html>',
        encoding="utf-8",
    )
    (component / "api.yml").write_text("schema_version: 1\n", encoding="utf-8")
    (component / "_previews/navigation/index.html").write_text(
        '<html><body><a href="/fictional-app-route">demo navigation</a></body></html>',
        encoding="utf-8",
    )
    _write_versions(root, [("0.4.0", ())])

    assert list(cross_version_link.check(_versions_ctx(root))) == []


def test_cross_version_link_broken_errors(tmp_path: Path) -> None:
    root = tmp_path / "versions"
    _make_version(root, "0.1.0")
    _make_version(root, "0.2.0")
    (root / "0.2.0" / "index.html").write_text(
        '<html><body><a href="../0.1.0/missing/">gone</a></body></html>', encoding="utf-8"
    )
    _write_versions(root, [("0.1.0", ()), ("0.2.0", ())])

    errors = _errors(list(cross_version_link.check(_versions_ctx(root))))

    assert len(errors) == 1
    assert errors[0].source == "0.2.0/index.html"
    assert "../0.1.0/missing/" in errors[0].message
    assert "target not found on disk" in errors[0].message


def test_cross_version_absolute_version_link_is_checked(tmp_path: Path) -> None:
    root = tmp_path / "versions"
    _make_version(root, "0.1.0")
    _make_version(root, "0.2.0")
    (root / "0.2.0" / "index.html").write_text(
        '<html><body><a href="/v/0.1.0/missing/">abs</a></body></html>', encoding="utf-8"
    )
    _write_versions(root, [("0.1.0", ()), ("0.2.0", ())])

    errors = _errors(list(cross_version_link.check(_versions_ctx(root))))

    assert len(errors) == 1
    assert "/v/0.1.0/missing/" in errors[0].message


def test_cross_version_absolute_version_link_can_resolve(tmp_path: Path) -> None:
    root = tmp_path / "versions"
    _make_version(root, "0.1.0", pages=("index.html", "concepts/index.html"))
    _make_version(root, "0.2.0")
    (root / "0.2.0" / "index.html").write_text(
        '<html><body><a href="/v/0.1.0/concepts/">abs</a></body></html>', encoding="utf-8"
    )
    _write_versions(root, [("0.1.0", ()), ("0.2.0", ())])

    assert list(cross_version_link.check(_versions_ctx(root))) == []


def test_cross_version_root_link_requires_site_scope(tmp_path: Path) -> None:
    root = tmp_path / "versions"
    _make_version(root, "0.2.0")
    (root / "0.2.0" / "index.html").write_text(
        '<html><body><a href="/guide/">escaped</a></body></html>', encoding="utf-8"
    )
    (root / "_nav.yml").write_text(
        "areas:\n  - label: Docs\n    items: [{ title: Guide, path: /guide/ }]\n",
        encoding="utf-8",
    )
    _write_versions(root, [("0.2.0", ())])

    errors = _errors(list(cross_version_link.check(_versions_ctx(root))))

    assert len(errors) == 1
    assert "escapes its snapshot" in errors[0].message


def test_cross_version_root_link_allows_declared_site_scope(tmp_path: Path) -> None:
    root = tmp_path / "versions"
    _make_version(root, "0.2.0")
    (root / "0.2.0" / "index.html").write_text(
        '<html><body><a href="/blog/a-post/">site</a></body></html>', encoding="utf-8"
    )
    (root / "_nav.yml").write_text(
        "areas:\n  - label: Blog\n    source: blog\n    scope: site\n    entry: { title: All posts, path: /blog/ }\n",
        encoding="utf-8",
    )
    _write_versions(root, [("0.2.0", ())])

    assert list(cross_version_link.check(_versions_ctx(root))) == []


def test_cross_version_links_strip_the_deployment_base_path(tmp_path: Path) -> None:
    root = tmp_path / "versions"
    _make_version(root, "0.2.0", pages=("index.html", "guide/index.html"))
    (root / "0.2.0" / "index.html").write_text(
        '<html><body><a href="/citry/v/0.2.0/guide/">guide</a><a href="/citry/blog/a-post/">site</a></body></html>',
        encoding="utf-8",
    )
    (root / "_nav.yml").write_text(
        "areas:\n"
        "  - label: Docs\n"
        "    items: [{ title: Guide, path: /guide/ }]\n"
        "  - label: Blog\n"
        "    source: blog\n"
        "    scope: site\n"
        "    entry: { title: All posts, path: /blog/ }\n",
        encoding="utf-8",
    )
    _write_versions(root, [("0.2.0", ())])
    context = _versions_ctx(root)
    context.base_path = "/citry"

    assert list(cross_version_link.check(context)) == []


def test_cross_version_uses_the_snapshot_scope_manifest(tmp_path: Path) -> None:
    root = tmp_path / "versions"
    _make_version(root, "0.2.0")
    write_build_info(
        root / "0.2.0",
        version="0.2.0",
        source_sha="deadbeef",
        site_routes=("/old-site/*",),
    )
    (root / "0.2.0" / "index.html").write_text(
        '<html><body><a href="/old-site/post/">historical site</a>'
        '<a href="/blog/post/">new site only</a></body></html>',
        encoding="utf-8",
    )
    (root / "_nav.yml").write_text(
        "areas:\n"
        "  - label: Old\n"
        "    items: [{ title: Old, path: /old-site/ }]\n"
        "  - label: Blog\n"
        "    source: blog\n"
        "    scope: site\n"
        "    entry: { title: All posts, path: /blog/ }\n",
        encoding="utf-8",
    )
    _write_versions(root, [("0.2.0", ())])

    errors = _errors(list(cross_version_link.check(_versions_ctx(root))))

    assert len(errors) == 1
    assert "/blog/post/" in errors[0].message


def test_frozen_import_skips_link_and_homepage_checks(tmp_path: Path) -> None:
    # A frozen import (stamped with IMPORTED_BUILDER_VERSION) is historical HTML we
    # never rebuild: the guards confirm it exists but do not require a homepage or
    # link-check it, so a missing index.html and a dead internal link are both fine.
    root = tmp_path / "versions"
    vdir = root / "0.1.0"
    write_build_info(vdir, version="0.1.0", source_sha="deadbeef", builder_version=IMPORTED_BUILDER_VERSION)
    page = vdir / "guide" / "index.html"
    page.parent.mkdir(parents=True)
    page.write_text('<html><body><a href="../../nope/">dead</a></body></html>', encoding="utf-8")
    _write_versions(root, [("0.1.0", ())])

    assert list(versions_manifest.check(_versions_ctx(root))) == []
    assert list(cross_version_link.check(_versions_ctx(root))) == []


def test_make_versions_context_flags_a_synthetic_orphan(tmp_path: Path) -> None:
    # Exercises the make_versions_context wiring the versions-check command uses,
    # pointed at a synthetic tree (not the committed one) whose manifest lists a
    # version with no dir on disk - the shape an unreleased version left in the
    # manifest would take. The guard must flag it.
    root = tmp_path / "versions"
    _make_version(root, "0.1.0")
    _write_versions(root, [("0.1.0", ()), ("0.9.0", ())])  # 0.9.0 has no dir

    errors = _errors(list(versions_manifest.check(make_versions_context(root))))

    assert any(r.source == "0.9.0" and "does not exist" in r.message for r in errors)
