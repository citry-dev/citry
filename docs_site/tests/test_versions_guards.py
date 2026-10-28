"""
Tests for the version-tree guards (parity rows 5b.13 / 5b.14 / 5b.15), the
guard for links to ``main``, and the guard for shared ``/static/`` files.

These guards validate the committed ``versions/`` tree rather than a single build,
so the fixtures here are small synthetic ``versions/`` trees built with the real
versioning helpers (``write_build_info`` / ``write_manifest`` / ``materialize_alias``)
under ``tmp_path``. The wiring the versions-check command uses
(``make_versions_context``) is exercised against one of those synthetic trees.
"""

from __future__ import annotations

import contextlib
import json
import subprocess
from pathlib import Path

from docs_site._internal._vendor.mike_versions import Versions
from docs_site._internal.guards import (
    VERSION_GUARDS,
    cross_version_link,
    make_versions_context,
    snapshot_main_links,
    snapshot_static_files,
    versions_manifest,
)
from docs_site._internal.guards.base import GuardContext, Severity
from docs_site._internal.snapshot_links import checkout_release_ref, pin_snapshot_links
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


def test_snapshot_main_links_flags_a_link_to_main_and_pinning_clears_it(tmp_path: Path) -> None:
    root = tmp_path / "versions"
    vdir = _make_version(root, "1.0.0", pages=("index.html", "index.md", "logo.png", "api.yml", "events.js"))
    (vdir / "index.html").write_text(
        '<img src="https://raw.githubusercontent.com/citry-dev/citry/main/a.gif">'
        '<a href="https://github.com/citry-dev/citry/edit/main/docs/a.md">edit</a>',
        encoding="utf-8",
    )
    (vdir / "index.md").write_text("intro\n[src](https://github.com/citry-dev/citry/tree/main/benchmarks)\n")
    # A binary file is not read as text, whatever bytes it holds.
    (vdir / "logo.png").write_bytes(b"\x89PNG https://github.com/citry-dev/citry/blob/main/x \xff")
    # Text the rewrite never changes is still checked.
    (vdir / "api.yml").write_text("source: https://github.com/citry-dev/citry/blob/main/api.yml\n")
    js = "fetch('https://raw.githubusercontent.com/citry-dev/citry/main/e.json')\n"
    (vdir / "events.js").write_text(js)
    # The latest/ alias holds redirect stubs and no build stamp, so it is skipped.
    (root / "latest").mkdir()
    (root / "latest" / "index.html").write_text('<a href="https://github.com/citry-dev/citry/blob/main/x">x</a>')

    results = list(snapshot_main_links.check(_versions_ctx(root)))
    assert [(r.source, r.line, r.severity) for r in results] == [
        ("1.0.0/api.yml", 1, Severity.ERROR),
        ("1.0.0/events.js", 1, Severity.ERROR),
        ("1.0.0/index.html", 1, Severity.ERROR),
        ("1.0.0/index.md", 2, Severity.ERROR),
    ]

    # The rewrite changes the pages only, so the script keeps its bytes.
    assert pin_snapshot_links(vdir, "citry@1.0.0") == 2
    assert (vdir / "events.js").read_text() == js
    assert [r.source for r in snapshot_main_links.check(_versions_ctx(root))] == [
        "1.0.0/api.yml",
        "1.0.0/events.js",
    ]
    # The edit link is left on main, where edits are made.
    assert "/edit/main/docs/a.md" in (vdir / "index.html").read_text(encoding="utf-8")


def test_snapshot_main_links_runs_in_versions_check() -> None:
    assert snapshot_main_links.check in VERSION_GUARDS


def test_pin_snapshot_links_keeps_line_endings_and_skips_symlinks(tmp_path: Path) -> None:
    vdir = tmp_path / "1.0.0"
    vdir.mkdir()
    page = vdir / "index.md"
    page.write_bytes(b"a\r\n[x](https://github.com/citry-dev/citry/blob/main/x)\r\n")
    outside = tmp_path / "outside.md"
    outside.write_text("[x](https://github.com/citry-dev/citry/blob/main/x)\n")
    with contextlib.suppress(OSError):  # Windows without the symlink privilege.
        (vdir / "link.md").symlink_to(outside)
    pin_snapshot_links(vdir, "citry@1.0.0")
    assert page.read_bytes() == b"a\r\n[x](https://github.com/citry-dev/citry/blob/citry@1.0.0/x)\r\n"
    # A symlink could lead outside the snapshot, so its target is left alone.
    assert "/blob/main/x" in outside.read_text()


def _git(repo: Path, *args: str) -> str:
    command = ["git", "-C", str(repo), *args]
    return subprocess.run(command, check=True, capture_output=True, text=True).stdout.strip()


def test_checkout_release_ref_uses_the_tag_only_on_its_commit(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "one")
    _git(repo, "tag", "citry@1.0.0")
    assert checkout_release_ref(repo, "1.0.0") == "citry@1.0.0"
    # A later commit is not the release, so the links name that commit.
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "two")
    assert checkout_release_ref(repo, "1.0.0") == _git(repo, "rev-parse", "HEAD")
    # Outside a git checkout there is nothing to name.
    assert checkout_release_ref(tmp_path / "not-a-repo", "1.0.0") == ""


# --- snapshot_static_files ---------------------------------------------------


def _static_ctx(tmp_path: Path, page_html: str, *, present: tuple[str, ...] = (), base_path: str = "") -> GuardContext:
    """A context over one synthetic snapshot page, with ``present`` files under ``static/``."""
    root = tmp_path / "versions"
    vdir = _make_version(root, "1.0.0", pages=("docs/page/index.html",))
    (vdir / "docs" / "page" / "index.html").write_text(page_html, encoding="utf-8")
    static = tmp_path / "static"
    for rel in present:
        (static / rel).parent.mkdir(parents=True, exist_ok=True)
        (static / rel).write_bytes(b"x")
    return GuardContext(
        content_dir=root,
        examples_dir=root,
        nav_path=root / "_nav.yml",
        static_dir=static,
        repo_root=root,
        base_path=base_path,
        versions_dir=root,
    )


def _missing(ctx: GuardContext) -> list[tuple[str | None, str]]:
    """The ``(page, message)`` pairs the guard reports, all of which must be errors."""
    results = list(snapshot_static_files.check(ctx))
    assert all(r.severity is Severity.ERROR for r in results)
    return [(r.source, r.message) for r in results]


def test_snapshot_static_files_flags_a_missing_src(tmp_path: Path) -> None:
    # The second mention of the same path is not reported again.
    ctx = _static_ctx(tmp_path, '<img src="/static/img/chart.png">\n<img src="/static/img/chart.png">')

    [result] = list(snapshot_static_files.check(ctx))

    assert (result.source, result.line) == ("1.0.0/docs/page/index.html", 1)
    assert result.message.startswith("loads /static/img/chart.png, which is missing")
    assert "restore the file" in result.message


def test_snapshot_static_files_passes_when_every_file_exists(tmp_path: Path) -> None:
    page = '<link rel=stylesheet href=/static/css/site.css><img src="/static/img/chart.png">'
    ctx = _static_ctx(tmp_path, page, present=("css/site.css", "img/chart.png"))

    assert _missing(ctx) == []


def test_snapshot_static_files_reads_unquoted_attributes(tmp_path: Path) -> None:
    # Snapshot pages are minified, which drops the quotes around most values.
    ctx = _static_ctx(tmp_path, "<img src=/static/img/chart.png alt=Chart>")

    assert [message.split(",")[0] for _, message in _missing(ctx)] == ["loads /static/img/chart.png"]


def test_snapshot_static_files_checks_every_srcset_candidate(tmp_path: Path) -> None:
    page = (
        "<picture>"
        '<source srcset="/static/img/a-640.avif 640w, /static/img/a-1280.avif 1280w">'
        '<img srcset="/static/img/a,640.jpg 1x,/static/img/a-2x.jpg 2x" src="/static/img/a.jpg">'
        "</picture>"
    )
    ctx = _static_ctx(tmp_path, page, present=("img/a-640.avif", "img/a,640.jpg", "img/a.jpg"))

    # A comma inside a URL stays part of it; only the two files that are gone
    # are reported.
    assert [message.split(",")[0] for _, message in _missing(ctx)] == [
        "loads /static/img/a-1280.avif",
        "loads /static/img/a-2x.jpg",
    ]


def test_snapshot_static_files_ignores_query_strings_and_fragments(tmp_path: Path) -> None:
    page = '<img src="/static/img/plate.png?plate=baseline"><a href="/static/notes.txt#part">notes</a>'
    present_ctx = _static_ctx(tmp_path / "present", page, present=("img/plate.png", "notes.txt"))
    missing_ctx = _static_ctx(tmp_path / "missing", page)

    assert _missing(present_ctx) == []
    assert [message.split(",")[0] for _, message in _missing(missing_ctx)] == [
        "loads /static/img/plate.png",
        "loads /static/notes.txt",
    ]


def test_snapshot_static_files_ignores_paths_shown_in_code(tmp_path: Path) -> None:
    # A code example shows markup as escaped text, prose can name a path, and
    # a script can hold one in a string. The guard reads only attributes, so
    # none of these is checked.
    page = (
        '<pre><code>&lt;link rel="stylesheet" href="/static/print.css"&gt;</code></pre>'
        "<p>Put your styles in <code>/static/print.css</code>.</p>"
        "<script>const style = '/static/print.css';</script>"
    )
    ctx = _static_ctx(tmp_path, page)

    assert _missing(ctx) == []


def test_snapshot_static_files_resolves_relative_paths_into_static(tmp_path: Path) -> None:
    # The page is served at /v/1.0.0/docs/page/, so four ../ steps reach the
    # site root. Three steps stop at /v/, and a browser stays at the root when
    # a path has more steps than folders.
    page = (
        '<img src="../../../../static/img/four.png">'
        '<img src="../../../static/img/three.png">'
        '<img src="../../../../../static/img/five.png">'
        '<img src="chart.png">'
    )
    ctx = _static_ctx(tmp_path, page)

    assert [message.split(",")[0] for _, message in _missing(ctx)] == [
        "loads /static/img/four.png",
        "loads /static/img/five.png",
    ]


def test_snapshot_static_files_skips_other_sites_and_data_uris(tmp_path: Path) -> None:
    page = (
        '<img src="https://citry.dev/static/img/x.png">'
        '<script src="//cdn.example/static/x.js"></script>'
        '<img src="data:image/png;base64,c3RhdGljLw==">'
    )
    ctx = _static_ctx(tmp_path, page)

    assert _missing(ctx) == []


def test_snapshot_static_files_strips_the_deployment_base_path(tmp_path: Path) -> None:
    page = '<img src="/citry/static/img/chart.png"><img src="/citry/static/img/gone.png">'
    ctx = _static_ctx(tmp_path, page, present=("img/chart.png",), base_path="/citry")

    assert [message.split(",")[0] for _, message in _missing(ctx)] == ["loads /static/img/gone.png"]


def test_snapshot_static_files_skips_alias_redirect_dirs(tmp_path: Path) -> None:
    # latest/ has no build stamp; it only redirects into a version folder.
    ctx = _static_ctx(tmp_path, "<p>ok</p>")
    alias = tmp_path / "versions" / "latest"
    alias.mkdir()
    (alias / "index.html").write_text('<img src="/static/img/chart.png">', encoding="utf-8")

    assert _missing(ctx) == []


def test_snapshot_static_files_allows_a_file_a_demo_loads_missing_on_purpose(tmp_path: Path) -> None:
    # The allow list names one file, so another missing file beside it still fails.
    page = '<img src="/static/img/ui/image/missing-native-observation.jpg"><img src="/static/img/ui/image/gone.jpg">'
    ctx = _static_ctx(tmp_path, page)

    assert [message.split(",")[0] for _, message in _missing(ctx)] == ["loads /static/img/ui/image/gone.jpg"]


def test_snapshot_static_files_runs_in_versions_check() -> None:
    assert snapshot_static_files.check in VERSION_GUARDS
