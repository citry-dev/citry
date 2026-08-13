"""Tests for the static-site build (walk content -> write clean-URL HTML)."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest
import yaml

from docs_site._internal.build import BuildOutcome, _is_unsafe_output, _replace_output_directory, build_site
from docs_site._internal.config import DocsConfig
from docs_site._internal.config import config as default_config
from docs_site._internal.config_loading import DocsConfigError
from docs_site._internal.pagefind import PagefindOutcome
from docs_site._internal.pipeline import render_page
from docs_site._internal.project import load_docs_project
from docs_site._internal.versioning import materialize_alias, update_manifest


def _default_declarations() -> dict[str, Path]:
    return {
        name: getattr(default_config, name)
        for name in (
            "settings_config",
            "reference_config",
            "ui_library_config",
            "redirects_config",
            "versions_config",
            "people_sources_config",
        )
    }


def _write_blog(content: Path) -> Path:
    """Write a small valid Blog and return its dated post source."""
    nav = content / "_nav.yml"
    if not nav.exists():
        nav.write_text(
            "areas:\n"
            "  - label: Blog\n"
            "    source: blog\n"
            "    scope: site\n"
            "    entry: { title: All posts, path: /blog/ }\n",
            encoding="utf-8",
        )
    blog = content / "blog"
    blog.mkdir()
    (blog / "index.md").write_text(
        "---\ntitle: Blog\ndescription: News from Citry.\n---\n\n<c-blog-list />\n",
        encoding="utf-8",
    )
    post = blog / "2026-07-27-first-post.md"
    post.write_text(
        "---\n"
        "title: First post\n"
        "description: The first Blog post.\n"
        "date: 2026-07-27T09:00:00+02:00\n"
        "updated: 2026-07-27T10:00:00+02:00\n"
        "author: Citry maintainers\n"
        "author_url: https://github.com/citry-dev\n"
        "tags: Citry, project news\n"
        "---\n\n"
        "Opening paragraph.\n\n## Details\n\nDurable guidance lives in [the guide](../guide.md).\n",
        encoding="utf-8",
    )
    return post


def _config(tmp_path: Path) -> tuple[DocsConfig, Path, Path]:
    content = tmp_path / "content"
    content.mkdir()
    out = tmp_path / "site"
    return DocsConfig(content_dir=content, site_dir=out, repo_root=tmp_path), content, out


def test_output_safety_rejects_source_ancestors_and_descendants(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    docs = repo / "docs_site"
    content = docs / "content"
    examples = docs / "examples"
    versions = docs / "versions"
    for directory in (content, examples, versions):
        directory.mkdir(parents=True, exist_ok=True)
    config = DocsConfig(
        base_dir=docs,
        repo_root=repo,
        content_dir=content,
        examples_dir=examples,
        versions_dir=versions,
        site_dir=repo / "site",
    )

    for unsafe in (
        tmp_path,
        repo,
        docs,
        content,
        content / "nested",
        examples,
        versions,
        versions / "existing",
    ):
        assert _is_unsafe_output(unsafe, content, config)

    assert not _is_unsafe_output(repo / "site", content, config)
    assert not _is_unsafe_output(versions / "1.0.0", content, config, docs_version="1.0.0")


@pytest.mark.parametrize("target_kind", ["file", "symlink"])
def test_staged_publish_rejects_non_directory_targets(tmp_path: Path, target_kind: str) -> None:
    staged = tmp_path / "staged"
    staged.mkdir()
    (staged / "new.txt").write_text("new", encoding="utf-8")
    target = tmp_path / "target"
    if target_kind == "file":
        target.write_text("known good", encoding="utf-8")
    else:
        actual = tmp_path / "actual"
        actual.mkdir()
        (actual / "keep.txt").write_text("known good", encoding="utf-8")
        target.symlink_to(actual, target_is_directory=True)

    with pytest.raises(ValueError, match="output target must be a directory"):
        _replace_output_directory(staged, target)

    assert (staged / "new.txt").read_text(encoding="utf-8") == "new"
    if target_kind == "file":
        assert target.read_text(encoding="utf-8") == "known good"
    else:
        assert target.is_symlink()
        assert (target / "keep.txt").read_text(encoding="utf-8") == "known good"
    assert not list(tmp_path.glob(".target.backup-*"))


@pytest.mark.parametrize("base_path", ["/", "/preview/"])
def test_invalid_base_path_fails_before_existing_output_is_cleared(tmp_path: Path, base_path: str) -> None:
    config, content, out = _config(tmp_path)
    config.base_path = base_path
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    out.mkdir()
    sentinel = out / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(DocsConfigError, match="DOCS_BASE_PATH"):
        build_site(config=config, minify=False, search=False, social_cards=False)

    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_build_rejects_symlink_output_without_touching_its_target(tmp_path: Path) -> None:
    config, content, _out = _config(tmp_path)
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    actual = tmp_path / "actual-output"
    actual.mkdir()
    sentinel = actual / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")
    linked = tmp_path / "linked-output"
    linked.symlink_to(actual, target_is_directory=True)

    with pytest.raises(ValueError, match="symlink output"):
        build_site(config=config, output_dir=linked, minify=False, search=False, social_cards=False)

    assert linked.is_symlink()
    assert sentinel.read_text(encoding="utf-8") == "keep"


@pytest.mark.parametrize(
    ("docs_version", "alias"),
    [
        ("../_internal", ""),
        ("/absolute", ""),
        ("1.0.0/child", ""),
        ("1.0.0", "../content"),
        ("1.0.0", "/absolute"),
        ("1.0.0", "nested/latest"),
    ],
)
def test_version_identifiers_fail_before_existing_output_is_cleared(
    tmp_path: Path,
    docs_version: str,
    alias: str,
) -> None:
    config, content, out = _config(tmp_path)
    config.versions_dir = tmp_path / "versions"
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    out.mkdir()
    sentinel = out / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(DocsConfigError, match="single segment"):
        build_site(
            config=config,
            output_dir=out,
            docs_version=docs_version,
            alias=alias,
            minify=False,
            search=False,
            social_cards=False,
        )

    assert sentinel.read_text(encoding="utf-8") == "keep"


@pytest.mark.parametrize("alias", ["1.0.0", "2.0.0"])
def test_alias_version_collision_fails_before_snapshot_output_is_cleared(tmp_path: Path, alias: str) -> None:
    config, content, _out = _config(tmp_path)
    versions = tmp_path / "versions"
    config.versions_dir = versions
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    target = versions / "1.0.0"
    target.mkdir(parents=True)
    sentinel = target / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")
    update_manifest(versions, "2.0.0")

    with pytest.raises(DocsConfigError, match=r"target version|versions\.json"):
        build_site(
            config=config,
            docs_version="1.0.0",
            alias=alias,
            minify=False,
            search=False,
            social_cards=False,
        )

    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_docs_version_cannot_overwrite_an_existing_alias(tmp_path: Path) -> None:
    config, content, _out = _config(tmp_path)
    versions = tmp_path / "versions"
    config.versions_dir = versions
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    alias_dir = versions / "latest"
    alias_dir.mkdir(parents=True)
    sentinel = alias_dir / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")
    update_manifest(versions, "1.0.0", aliases=("latest",))

    with pytest.raises(DocsConfigError, match="existing alias"):
        build_site(
            config=config,
            docs_version="latest",
            minify=False,
            search=False,
            social_cards=False,
        )

    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_custom_version_output_requires_a_detached_build_before_clearing(tmp_path: Path) -> None:
    config, content, _out = _config(tmp_path)
    config.versions_dir = tmp_path / "versions"
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    custom = tmp_path / "custom"
    custom.mkdir()
    sentinel = custom / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(DocsConfigError, match="custom docs-version output"):
        build_site(
            config=config,
            output_dir=custom,
            docs_version="1.0.0",
            minify=False,
            search=False,
            social_cards=False,
        )

    assert sentinel.read_text(encoding="utf-8") == "keep"


@pytest.mark.parametrize(
    ("docs_version", "alias"),
    [("", ""), ("1.0.0", "latest")],
)
def test_detached_version_build_rejects_missing_version_or_alias_before_clearing(
    tmp_path: Path,
    docs_version: str,
    alias: str,
) -> None:
    config, content, out = _config(tmp_path)
    config.versions_dir = tmp_path / "versions"
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    out.mkdir()
    sentinel = out / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(DocsConfigError, match=r"requires docs_version|cannot materialize an alias"):
        build_site(
            config=config,
            output_dir=out,
            docs_version=docs_version,
            alias=alias,
            update_versions_manifest=False,
            minify=False,
            search=False,
            social_cards=False,
        )

    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_detached_version_build_supports_a_custom_output_without_manifest_mutation(tmp_path: Path) -> None:
    config, content, _out = _config(tmp_path)
    config.versions_dir = tmp_path / "versions"
    (content / "_nav.yml").write_text(
        "areas:\n  - label: Docs\n    items: [{ title: Docs, path: /docs/ }]\n",
        encoding="utf-8",
    )
    (content / "docs.md").write_text("---\ntitle: Docs\n---\n\n# Docs\n", encoding="utf-8")
    custom = tmp_path / "custom"

    outcome = build_site(
        config=config,
        output_dir=custom,
        docs_version="1.0.0",
        update_versions_manifest=False,
        minify=False,
        search=False,
        social_cards=False,
    )

    assert outcome.failed == 0
    assert (custom / "docs" / "index.html").is_file()
    assert not (config.versions_dir / "versions.json").exists()


def test_build_writes_clean_urls(tmp_path: Path) -> None:
    config, content, out = _config(tmp_path)
    (content / "index.md").write_text("---\ntitle: Home\n---\n\nHome page.\n", encoding="utf-8")
    (content / "guide").mkdir()
    (content / "guide" / "intro.md").write_text("# Intro\n\nIntro body.\n", encoding="utf-8")

    # minify=False so the doctype assert below sees the rendered markup, not
    # the shrunk form (the default build lowercases <!doctype> and drops quotes).
    outcome = build_site(config=config, minify=False)

    assert outcome.built == 2
    assert outcome.failed == 0
    # index.md -> /  ; guide/intro.md -> /guide/intro/
    assert (out / "index.html").is_file()
    intro = out / "guide" / "intro" / "index.html"
    assert intro.is_file()
    assert "Intro body." in intro.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in intro.read_text(encoding="utf-8")


def test_build_copies_non_markdown_assets(tmp_path: Path) -> None:
    config, content, out = _config(tmp_path)
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    (content / "img").mkdir()
    (content / "img" / "logo.svg").write_text("<svg></svg>", encoding="utf-8")

    build_site(config=config)

    assert (out / "img" / "logo.svg").read_text(encoding="utf-8") == "<svg></svg>"


def test_build_copies_static_assets(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    static_css = tmp_path / "static" / "css"
    static_css.mkdir(parents=True)
    (static_css / "site.css").write_text("body{}", encoding="utf-8")
    # base_dir points at tmp so the build finds tmp/static.
    config = DocsConfig(
        content_dir=content,
        site_dir=tmp_path / "site",
        repo_root=tmp_path,
        base_dir=tmp_path,
        **_default_declarations(),
    )

    build_site(config=config)

    assert (config.site_dir / "static" / "css" / "site.css").read_text(encoding="utf-8") == "body{}"


def test_redirect_cannot_overwrite_an_orphan_authored_page(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "_nav.yml").write_text(
        "areas:\n  - label: Docs\n    items: [{ title: Home, path: / }]\n",
        encoding="utf-8",
    )
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    (content / "orphan.md").write_text("# Orphan\n", encoding="utf-8")
    redirects = tmp_path / "redirects.yml"
    redirects.write_text("redirects:\n  - { from: /orphan/, to: / }\n", encoding="utf-8")
    output = tmp_path / "site"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")
    cfg = DocsConfig(
        content_dir=content,
        site_dir=output,
        redirects_config=redirects,
    )

    with pytest.raises(DocsConfigError, match="collides"):
        build_site(config=cfg, minify=False, search=False, social_cards=False)

    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_ui_projection_preflight_preserves_existing_output(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "_nav.yml").write_text(
        "areas:\n"
        "  - label: UI\n"
        "    items: [{ title: Home, path: / }]\n"
        "    groups:\n"
        "      - label: Components\n"
        "        source: ui_library\n",
        encoding="utf-8",
    )
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    (tmp_path / "button.md").write_text("---\ntitle: Button\n---\n\n# Button\n", encoding="utf-8")
    ui_manifest = tmp_path / "ui_library.yml"
    ui_manifest.write_text(
        "components:\n  - family: button\n    slug: button\n    source: button.md\n",
        encoding="utf-8",
    )
    output = tmp_path / "site"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")
    cfg = DocsConfig(
        repo_root=tmp_path,
        content_dir=content,
        site_dir=output,
        ui_library_config=ui_manifest,
    )

    with pytest.raises(DocsConfigError, match="title and description"):
        build_site(config=cfg, minify=False, search=False, social_cards=False)

    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_build_renders_ui_library_source_directly_to_its_catalog_route(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "_nav.yml").write_text(
        "areas:\n"
        "  - label: UI\n"
        "    items: [{ title: Home, path: / }]\n"
        "    groups:\n"
        "      - label: Components\n"
        "        source: ui_library\n",
        encoding="utf-8",
    )
    (content / "index.md").write_text("---\ntitle: Home\ndescription: Home.\n---\n\n# Home\n", encoding="utf-8")
    source = tmp_path / "packages/py/citry_ui/citry_ui/components/button/api.md"
    source.parent.mkdir(parents=True)
    source.write_text(
        "---\ntitle: Button\ndescription: Button docs.\n---\n\n"
        "# Button\n\n## Use Button\n\nDirect source marker.\n\n"
        '<c-ui-demo path="packages/py/citry_ui/citry_ui/components/button/snippets/build_preview.py" '
        'title="Build preview" />\n',
        encoding="utf-8",
    )
    source.with_suffix(".yml").write_text(
        "schema_version: 1\n"
        "family: button\n"
        "components: [CButton]\n"
        "inputs: []\n"
        "slots: []\n"
        "events: []\n"
        "methods: []\n"
        "attributes: []\n"
        "selectors: []\n"
        "css: []\n"
        "interfaces: []\n"
        "translations: []\n",
        encoding="utf-8",
    )
    snippet = tmp_path / "packages/py/citry_ui/citry_ui/components/button/snippets/build_preview.py"
    snippet.parent.mkdir(parents=True, exist_ok=True)
    snippet.write_text(
        "from citry import Component\n\n"
        "class BuildPreviewSmoke(Component):\n"
        "    template = '<button>Rendered build preview</button>'\n"
        "    css = '''\n"
        "      button {\n"
        "        color: green;\n"
        "      }\n"
        "    '''\n\n"
        "preview_controls = (\n"
        "    {\n"
        "        'name': 'tone',\n"
        "        'label': 'Tone',\n"
        "        'type': 'select',\n"
        "        'default': 'quiet',\n"
        "        'options': (('quiet', 'Quiet'), ('bold', 'Bold')),\n"
        "    },\n"
        "    {\n"
        "        'name': 'disabled',\n"
        "        'label': 'Disabled',\n"
        "        'type': 'checkbox',\n"
        "        'default': False,\n"
        "    },\n"
        ")\n\n"
        "preview = BuildPreviewSmoke()\n"
        "preview\n",
        encoding="utf-8",
    )
    ui_manifest = tmp_path / "ui_library.yml"
    ui_manifest.write_text(
        "components:\n"
        "  - family: button\n"
        "    slug: button\n"
        "    source: packages/py/citry_ui/citry_ui/components/button/api.md\n",
        encoding="utf-8",
    )
    output = tmp_path / "site"
    cfg = DocsConfig(
        repo_root=tmp_path,
        content_dir=content,
        site_dir=output,
        ui_library_config=ui_manifest,
    )

    outcome = build_site(config=cfg, minify=False, search=False, social_cards=False)

    page = output / "ui-library/components/button/index.html"
    companion = output / "ui-library/components/button/index.md"
    assert outcome.failed == 0
    assert outcome.ui_library == 1
    assert outcome.ui_previews == 1
    assert "Direct source marker." in page.read_text(encoding="utf-8")
    page_source = page.read_text(encoding="utf-8")
    companion_source = companion.read_text(encoding="utf-8")
    assert 'src="/ui-library/components/button/_previews/build-preview/"' in page_source
    assert 'title="Build preview rendered preview"' in page_source
    assert 'sandbox="allow-forms allow-scripts"' in page_source
    assert 'class="example-demo-frame--theme-sync"' in page_source
    assert 'loading="lazy"' in page_source
    assert page_source.index("data-ui-preview-controls") < page_source.index("data-ui-preview-frame")
    assert page_source.index("data-ui-preview-frame") < page_source.index("citry-ui-demo__source")
    assert "Customize example" in page_source
    assert 'aria-label="Build preview controls"' in page_source
    assert '<option value="quiet" selected>Quiet</option>' in page_source
    assert 'name="disabled"' in page_source
    assert "Show code" in page_source
    assert "BuildPreviewSmoke" in page_source
    assert "data-citry-live-code" not in page_source
    assert "Try live" not in page_source
    assert "/static/playground/live_code.js" not in page_source
    assert "Direct source marker." in companion_source
    assert "## API reference" in companion_source
    assert "### Interfaces" in companion_source
    assert "[Open the rendered preview](/ui-library/components/button/_previews/build-preview/)" in companion_source
    assert "class BuildPreviewSmoke(Component):" in companion_source
    preview_page = output / "ui-library/components/button/_previews/build-preview/index.html"
    preview_source = preview_page.read_text(encoding="utf-8")
    assert "Rendered build preview" in preview_source
    assert "color: green" in preview_source
    assert 'content="noindex,nofollow"' in preview_source
    assert 'type: "citry-ui-preview-height"' in preview_source
    assert 'type === "citry-ui-preview-theme"' in preview_source
    assert 'type === "citry-ui-preview-controls"' in preview_source
    assert 'new CustomEvent("citry-ui-preview-controls"' in preview_source
    assert "font-size: 87.5%" in preview_source
    assert "new ResizeObserver(publish)" in preview_source
    assert not (output / "ui-library/components/button/_previews/build-preview/index.md").exists()
    assert all(record.url != "ui-library/components/button/_previews/build-preview/" for record in outcome.records)
    llms_full = (output / "llms-full.txt").read_text(encoding="utf-8")
    assert "class BuildPreviewSmoke(Component):" in llms_full
    assert "<iframe" not in llms_full
    assert not (content / "ui-library/components/button.md").exists()
    assert any(record.source_md == source for record in outcome.records)


def test_custom_repository_identity_reaches_every_generated_surface(tmp_path: Path) -> None:
    settings_source = default_config.settings_config.read_text(encoding="utf-8")
    settings_path = tmp_path / "settings.yml"
    settings_path.write_text(
        settings_source.replace("owner: citry-dev", "owner: acme", 1)
        .replace("name: citry", "name: widgets", 1)
        .replace(
            "url: https://github.com/citry-dev/citry",
            "url: https://github.com/acme/widgets",
            1,
        )
        .replace(
            "issues_url: https://github.com/citry-dev/citry/issues",
            "issues_url: https://github.com/acme/widgets/issues",
            1,
        )
        .replace(
            "sponsors_url: https://github.com/sponsors/JuroOravec",
            "sponsors_url: https://github.com/sponsors/acme",
            1,
        ),
        encoding="utf-8",
    )
    cfg = DocsConfig(
        site_dir=tmp_path / "site",
        settings_config=settings_path,
        site_url="https://docs.acme.test/widgets/",
    )
    project = load_docs_project(cfg)

    outcome = build_site(
        project=project,
        minify=False,
        search=False,
        social_cards=False,
    )
    direct = render_page(
        "Repository: [{{ repo_full_name }}]({{ repo_url }}). Issue #123.",
        project=project,
        wrap_in_layout=False,
    ).html
    home = (outcome.output_dir / "index.html").read_text(encoding="utf-8")
    authored = (outcome.output_dir / "concepts" / "components" / "index.html").read_text(encoding="utf-8")
    generated = (outcome.output_dir / "reference" / "component" / "index.html").read_text(encoding="utf-8")
    not_found = (outcome.output_dir / "404.html").read_text(encoding="utf-8")
    contributing = (outcome.output_dir / "community" / "contributing" / "index.html").read_text(encoding="utf-8")

    assert outcome.failed == 0
    assert "https://github.com/acme/widgets" in home
    assert "https://github.com/acme/widgets/edit/main/docs_site/content/concepts/components.md" in authored
    assert "https://github.com/acme/widgets/blob/main/packages/py/citry/citry/component.py" in generated
    assert "https://github.com/acme/widgets/issues" in not_found
    assert "https://github.com/sponsors/acme" in contributing
    assert "https://github.com/sponsors/JuroOravec" not in contributing
    assert 'data-search-site-target="docs.acme.test/widgets"' in authored
    assert '<a href="https://github.com/acme/widgets">acme/widgets</a>' in direct
    assert "https://github.com/acme/widgets/issues/123" in direct


def test_custom_pagefind_path_configures_the_generated_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, content, _out = _config(tmp_path)
    (content / "index.md").write_text("---\ntitle: Home\n---\n\nHome.\n", encoding="utf-8")
    settings_path = tmp_path / "settings.yml"
    settings_path.write_text(
        default_config.settings_config.read_text(encoding="utf-8").replace(
            "/pagefind/pagefind.js",
            "/custom-search/pagefind.js",
            1,
        ),
        encoding="utf-8",
    )
    config.settings_config = settings_path
    called_with: list[str] = []

    def fake_pagefind(_output_dir: Path, output_subdir: str) -> PagefindOutcome:
        called_with.append(output_subdir)
        return PagefindOutcome(ok=True, message="built")

    monkeypatch.setattr("docs_site._internal.build.run_pagefind", fake_pagefind)

    outcome = build_site(config=config, minify=False, search=True, social_cards=False)

    assert outcome.search_ok
    assert called_with == ["custom-search"]
    home = (config.site_dir / "index.html").read_text(encoding="utf-8")
    assert 'data-pagefind-path="/custom-search/pagefind.js"' in home


@pytest.mark.parametrize(
    "pagefind_path",
    [
        "/static/pagefind.js",
        "/Static/pagefind.js",
        "/meta/pagefind.js",
        "/Meta/pagefind.js",
        "/og/pagefind.js",
        "/citry/pagefind.js",
        "/v/pagefind.js",
        "/Docs/pagefind.js",
    ],
)
def test_pagefind_output_collision_fails_before_existing_output_is_cleared(
    tmp_path: Path,
    pagefind_path: str,
) -> None:
    config, content, out = _config(tmp_path)
    (content / "index.md").write_text("---\ntitle: Home\n---\n\nHome.\n", encoding="utf-8")
    (content / "docs.md").write_text("---\ntitle: Docs\n---\n\nDocs.\n", encoding="utf-8")
    settings_path = tmp_path / "settings.yml"
    settings_path.write_text(
        default_config.settings_config.read_text(encoding="utf-8").replace(
            "/pagefind/pagefind.js",
            pagefind_path,
            1,
        ),
        encoding="utf-8",
    )
    config.settings_config = settings_path
    out.mkdir()
    sentinel = out / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(DocsConfigError, match=r"search\.pagefind_path collides"):
        build_site(config=config, minify=False, search=True, social_cards=False)

    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_build_records_failures_without_aborting(tmp_path: Path, monkeypatch) -> None:
    config, content, out = _config(tmp_path)
    (content / "ok.md").write_text("# Fine\n", encoding="utf-8")
    (content / "bad.md").write_text("BOOM\n", encoding="utf-8")

    # Make rendering raise for one page; the build must record it and still
    # produce the other. (Once Pass 1 expands the custom <c-*> tags, a bad tag is a
    # real source of this; here we drive the mechanism directly.)
    import docs_site._internal.build as build_mod

    real_render = build_mod.render_page

    def fake_render(source, **kwargs):
        if "BOOM" in source:
            raise RuntimeError("kaboom")
        return real_render(source, **kwargs)

    monkeypatch.setattr(build_mod, "render_page", fake_render)

    outcome = build_site(config=config)

    assert outcome.built == 1
    assert outcome.failed == 1
    assert (out / "ok" / "index.html").is_file()
    assert outcome.errors
    assert outcome.errors[0][0] == "bad.md"


def test_failed_version_build_preserves_snapshot_manifest_and_alias(tmp_path: Path, monkeypatch) -> None:
    config, content, _out = _config(tmp_path)
    versions = tmp_path / "versions"
    config.versions_dir = versions
    (content / "_nav.yml").write_text(
        "areas:\n  - label: Docs\n    items: [{ title: Fine, path: /ok/ }]\n",
        encoding="utf-8",
    )
    (content / "ok.md").write_text("# Fine\n", encoding="utf-8")
    (content / "bad.md").write_text("BOOM\n", encoding="utf-8")

    snapshot = versions / "1.0.0"
    snapshot.mkdir(parents=True)
    (snapshot / "index.html").write_text("old snapshot", encoding="utf-8")
    (snapshot / "keep.txt").write_text("keep", encoding="utf-8")
    update_manifest(versions, "1.0.0", aliases=("latest",))
    materialize_alias(versions, "latest", "1.0.0")
    original_files = {path.relative_to(versions): path.read_bytes() for path in versions.rglob("*") if path.is_file()}

    import docs_site._internal.build as build_mod

    real_render = build_mod.render_page

    def fake_render(source, **kwargs):
        if "BOOM" in source:
            raise RuntimeError("kaboom")
        return real_render(source, **kwargs)

    monkeypatch.setattr(build_mod, "render_page", fake_render)

    outcome = build_site(
        config=config,
        docs_version="1.0.0",
        alias="latest",
        minify=False,
        search=False,
        social_cards=False,
    )

    assert outcome.failed == 1
    assert outcome.output_dir == snapshot.resolve()
    assert {
        path.relative_to(versions): path.read_bytes() for path in versions.rglob("*") if path.is_file()
    } == original_files


def test_build_writes_404_and_runtime(tmp_path: Path) -> None:
    config, content, out = _config(tmp_path)
    (content / "index.md").write_text("# Home\n", encoding="utf-8")

    outcome = build_site(config=config)

    not_found = out / "404.html"
    assert outcome.not_found
    assert not_found.is_file()
    text = not_found.read_text(encoding="utf-8")
    assert "Page not found" in text
    assert "noindex" in text  # the 404 must not be indexed

    # The 404 offers three ways forward. The search trigger opens the same modal
    # search.js wires on every [data-search-open]; substrings only, since the
    # minifier drops attribute quotes and reorders attributes.
    assert "data-search-open" in text
    assert "djc-notfound__search" in text
    assert "Search the documentation" in text
    # The four popular destinations (real built pages the internal_link guard checks).
    assert "/getting-started/installation/" in text
    assert "/getting-started/your-first-component/" in text
    assert "/concepts/components/" in text
    assert "/reference/" in text
    # And a link to report a page that has moved.
    assert "https://github.com/citry-dev/citry/issues" in text

    # The client runtime is written where pages reference it (/citry/citry.js).
    runtime = out / "citry" / "citry.js"
    assert outcome.runtime == runtime
    assert runtime.is_file()
    assert runtime.stat().st_size > 0
    events_runtime = out / "citry" / "ext" / "events" / "runtime.js"
    assert events_runtime.is_file()
    assert events_runtime.stat().st_size > 0


def test_build_records_doc_pages(tmp_path: Path) -> None:
    config, content, _out = _config(tmp_path)
    (content / "index.md").write_text(
        "---\ntitle: Home\ndescription: The home page.\n---\n\n# Home\n", encoding="utf-8"
    )

    outcome = build_site(config=config)

    by_url = {r.url: r for r in outcome.records}
    assert "" in by_url  # the home page's clean URL is ""
    home = by_url[""]
    assert home.is_doc_page
    assert home.title == "Home"
    assert home.description == "The home page."
    assert home.source_md is not None


def test_build_minifies_by_default(tmp_path: Path) -> None:
    config, content, _out = _config(tmp_path)
    (content / "index.md").write_text("# Home\n\nA paragraph with     many     spaces.\n", encoding="utf-8")

    small = build_site(config=config, output_dir=tmp_path / "small", minify=True)
    large = build_site(config=config, output_dir=tmp_path / "large", minify=False)

    assert small.minified > 0
    assert large.minified == 0
    small_html = (tmp_path / "small" / "index.html").read_text(encoding="utf-8")
    large_html = (tmp_path / "large" / "index.html").read_text(encoding="utf-8")
    assert len(small_html) < len(large_html)


def test_build_generates_social_cards_from_a_running_event_loop(tmp_path: Path) -> None:
    # Regression: the social-card step drives Playwright's *sync* API, which
    # refuses to start when an asyncio event loop is already running in the
    # calling thread. That happens when a host app builds from within async code,
    # and in this suite when the browser e2e tests run first and leave their
    # session-scoped sync-Playwright fixture (and its loop) open on the main
    # thread. The render must run in its own thread and succeed regardless.
    pytest.importorskip("playwright")
    content = tmp_path / "content"
    content.mkdir()
    (content / "index.md").write_text("---\ntitle: Loop card\n---\n\n# Loop card\n", encoding="utf-8")
    # A fresh base_dir means an empty OG cache, so a card is actually rendered
    # this run (not copied from a prior run's cache) and the sync-Playwright path
    # is exercised under the running loop.
    config = DocsConfig(
        content_dir=content,
        site_dir=tmp_path / "site",
        repo_root=tmp_path,
        base_dir=tmp_path,
        **_default_declarations(),
    )

    async def _build() -> BuildOutcome:
        # A loop is now running in the calling thread: the failure condition.
        return build_site(config=config, social_cards=True)

    def _build_in_fresh_loop() -> BuildOutcome:
        # Start the loop in a fresh thread. A brand-new thread has no running loop,
        # so asyncio.run works here even when the pytest main thread already holds a
        # sync-Playwright loop open (as it does once the e2e tests have run), which
        # is what makes this reproduce the bug in any test order.
        return asyncio.run(_build())

    with ThreadPoolExecutor(max_workers=1) as pool:
        outcome = pool.submit(_build_in_fresh_loop).result()

    # The build must not raise "Sync API inside the asyncio loop"; when a browser
    # is available the card is rendered and placed from within the running loop.
    if not outcome.social_cards_skipped:
        assert outcome.social_cards_placed >= 1


def test_build_writes_md_companions(tmp_path: Path) -> None:
    # site_url is pinned so the companion `url:` is env-stable (independent of
    # DOCS_SITE_URL); everything else mirrors the clean-URL build test.
    content = tmp_path / "content"
    content.mkdir()
    out = tmp_path / "site"
    config = DocsConfig(content_dir=content, site_dir=out, repo_root=tmp_path, site_url="https://citry.dev/")
    (content / "index.md").write_text(
        "---\ntitle: Home\ndescription: The home page.\n---\n\nHome page.\n", encoding="utf-8"
    )
    (content / "guide").mkdir()
    (content / "guide" / "intro.md").write_text("# Intro\n\nIntro body.\n", encoding="utf-8")

    outcome = build_site(config=config, minify=False, search=False, social_cards=False)

    # One `.md` companion per built content page, beside its index.html.
    assert outcome.built == 2
    assert outcome.companions == 2

    # guide/intro.md serves at /guide/intro/, so its companion sits at
    # guide/intro/index.md. Its front matter carries the title (taken from the
    # H1), the resolved canonical, and the description (this page sets none in
    # front matter, so it is derived from the first paragraph); the body is the
    # expanded markdown.
    companion = out / "guide" / "intro" / "index.md"
    assert companion.is_file()
    assert companion.read_text(encoding="utf-8") == (
        '---\ntitle: Intro\nurl: https://citry.dev/guide/intro/\ndescription: "Intro body."\n---\n'
        "# Intro\n\nIntro body.\n"
    )

    # The home page's companion sits at the site root, and its front matter also
    # carries the (quoted) description from the page's own front matter.
    home_companion = out / "index.md"
    assert home_companion.is_file()
    assert home_companion.read_text(encoding="utf-8") == (
        '---\ntitle: Home\nurl: https://citry.dev/\ndescription: "The home page."\n---\nHome page.'
    )


def test_build_expands_snippets_in_markdown_outputs(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    out = tmp_path / "site"
    config = DocsConfig(
        base_dir=tmp_path,
        content_dir=content,
        site_dir=out,
        repo_root=tmp_path,
        site_url="https://citry.dev/",
        **_default_declarations(),
    )
    (content / "_nav.yml").write_text(
        "areas:\n  - label: Docs\n    items:\n      - { title: Home, path: / }\n",
        encoding="utf-8",
    )
    (tmp_path / "snippet.py").write_text(
        "# --8<-- [start:example]\nclass IncludedFromSnippet:\n    pass\n# --8<-- [end:example]\n",
        encoding="utf-8",
    )
    (content / "index.md").write_text(
        '---\ntitle: Home\n---\n\n```citry\n--8<-- "snippet.py:example"\n```\n',
        encoding="utf-8",
    )

    outcome = build_site(config=config, minify=False, search=False, social_cards=False)

    assert outcome.failed == 0
    for output in (out / "index.md", out / "llms-full.txt"):
        text = output.read_text(encoding="utf-8")
        assert "class IncludedFromSnippet:" in text
        assert '--8<-- "snippet.py:example"' not in text


def test_build_projects_base_path_in_markdown_outputs(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    out = tmp_path / "site"
    config = DocsConfig(
        base_dir=tmp_path,
        base_path="/citry",
        content_dir=content,
        site_dir=out,
        repo_root=tmp_path,
        site_url="https://owner.github.io/citry/",
        **_default_declarations(),
    )
    (content / "_nav.yml").write_text(
        "areas:\n  - label: Docs\n    items:\n      - { title: Home, path: / }\n",
        encoding="utf-8",
    )
    (content / "index.md").write_text(
        "# Home\n\n"
        "[Guide](/guide/?view=all#part)\n\n"
        "[Guide reference]: /guide/reference/\n\n"
        '<a href="/guide/raw/">Raw link</a>\n\n'
        '<img src="/static/image.png">\n\n'
        "```markdown\n[Literal](/guide/)\n```\n",
        encoding="utf-8",
    )

    outcome = build_site(config=config, minify=False, search=False, social_cards=False)

    assert outcome.failed == 0
    for output in (out / "index.md", out / "llms-full.txt"):
        text = output.read_text(encoding="utf-8")
        assert "[Guide](/citry/guide/?view=all#part)" in text
        assert "[Guide reference]: /citry/guide/reference/" in text
        assert '<a href="/citry/guide/raw/">Raw link</a>' in text
        assert 'src="/citry/static/image.png"' in text
        assert "[Literal](/guide/)" in text


def test_build_publishes_blog_at_stable_routes_with_feed_and_companions(tmp_path: Path) -> None:
    config, content, out = _config(tmp_path)
    config.site_url = "https://citry.dev/"
    (content / "guide.md").write_text("# Guide\n", encoding="utf-8")
    source = _write_blog(content)

    outcome = build_site(config=config, minify=False, search=False, social_cards=False)

    assert outcome.failed == 0
    assert outcome.blog_posts == 1
    assert outcome.blog_feed
    assert (out / "blog" / "index.html").is_file()
    post_html = out / "blog" / "first-post" / "index.html"
    assert post_html.is_file()
    assert not (out / "blog" / "2026-07-27-first-post").exists()
    html = post_html.read_text(encoding="utf-8")
    assert "First post" in html
    assert 'href="../../guide/"' in html
    assert 'type="application/atom+xml"' in html

    companion = (out / "blog" / "first-post" / "index.md").read_text(encoding="utf-8")
    assert "url: https://citry.dev/blog/first-post/" in companion
    assert 'date: "2026-07-27T09:00:00+02:00"' in companion
    assert 'updated: "2026-07-27T10:00:00+02:00"' in companion
    assert 'author: "Citry maintainers"' in companion
    assert '  - "project news"' in companion

    record = next(record for record in outcome.records if record.url == "blog/first-post/")
    assert record.source_md == source
    assert record.editorial_updated is not None
    assert record.editorial_updated.isoformat() == "2026-07-27T10:00:00+02:00"

    feed = ET.parse(out / "blog" / "feed.xml").getroot()  # noqa: S314 - parses our serializer output
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entry = feed.find("atom:entry", ns)
    assert entry is not None
    assert entry.findtext("atom:title", namespaces=ns) == "First post"
    assert entry.find("atom:link", ns).attrib["href"] == "https://citry.dev/blog/first-post/"


def test_blog_feed_collision_fails_before_existing_output_is_cleared(tmp_path: Path) -> None:
    config, content, out = _config(tmp_path)
    _write_blog(content)
    (content / "blog" / "feed.xml").write_text("authored collision", encoding="utf-8")
    out.mkdir()
    sentinel = out / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(DocsConfigError, match=r"blog\.feed_path collides"):
        build_site(config=config, minify=False, search=False, social_cards=False)

    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_blog_feed_rejects_a_redirect_source_collision(tmp_path: Path) -> None:
    config, content, _out = _config(tmp_path)
    _write_blog(content)
    settings_path = tmp_path / "settings.yml"
    settings_path.write_text(
        default_config.settings_config.read_text(encoding="utf-8").replace(
            "/blog/feed.xml",
            "/blog/legacy.xml",
            1,
        ),
        encoding="utf-8",
    )
    redirects_path = tmp_path / "redirects.yml"
    redirects_path.write_text(
        "redirects:\n  - { from: /blog/legacy.xml/, to: /blog/ }\n",
        encoding="utf-8",
    )
    config.settings_config = settings_path
    config.redirects_config = redirects_path

    with pytest.raises(DocsConfigError, match=r"blog\.feed_path collides"):
        build_site(config=config, minify=False, search=False, social_cards=False)


def test_blog_feed_rejects_a_descendant_redirect_before_clearing_output(tmp_path: Path) -> None:
    config, content, out = _config(tmp_path)
    _write_blog(content)
    redirects_path = tmp_path / "redirects.yml"
    redirects_path.write_text(
        "redirects:\n  - { from: /blog/feed.xml/legacy/, to: /blog/ }\n",
        encoding="utf-8",
    )
    config.redirects_config = redirects_path
    out.mkdir()
    sentinel = out / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(DocsConfigError, match=r"blog\.feed_path collides"):
        build_site(config=config, minify=False, search=False, social_cards=False)

    assert sentinel.read_text(encoding="utf-8") == "keep"


@pytest.mark.parametrize(
    "feed_path",
    [
        "/blog/index.html/feed.xml",
        "/blog/index.md/feed.xml",
    ],
)
def test_blog_feed_rejects_generated_file_ancestor_collisions(tmp_path: Path, feed_path: str) -> None:
    config, content, out = _config(tmp_path)
    _write_blog(content)
    settings_path = tmp_path / "settings.yml"
    settings_path.write_text(
        default_config.settings_config.read_text(encoding="utf-8").replace(
            "/blog/feed.xml",
            feed_path,
            1,
        ),
        encoding="utf-8",
    )
    config.settings_config = settings_path
    out.mkdir()
    sentinel = out / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(DocsConfigError, match=r"blog\.feed_path collides"):
        build_site(config=config, minify=False, search=False, social_cards=False)

    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_blog_feed_rejects_a_copied_asset_ancestor_before_clearing_output(tmp_path: Path) -> None:
    config, content, out = _config(tmp_path)
    _write_blog(content)
    (content / "blog" / "logo.svg").write_text("<svg/>", encoding="utf-8")
    settings_path = tmp_path / "settings.yml"
    settings_path.write_text(
        default_config.settings_config.read_text(encoding="utf-8").replace(
            "/blog/feed.xml",
            "/blog/logo.svg/feed.xml",
            1,
        ),
        encoding="utf-8",
    )
    config.settings_config = settings_path
    out.mkdir()
    sentinel = out / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(DocsConfigError, match=r"blog\.feed_path collides"):
        build_site(config=config, minify=False, search=False, social_cards=False)

    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_blog_feed_rejects_a_unicode_normalization_asset_collision(tmp_path: Path) -> None:
    config, content, out = _config(tmp_path)
    _write_blog(content)
    (content / "blog" / "caf\N{LATIN SMALL LETTER E WITH ACUTE}.xml").write_text(
        "authored asset",
        encoding="utf-8",
    )
    decomposed = "cafe\N{COMBINING ACUTE ACCENT}.xml"
    settings_path = tmp_path / "settings.yml"
    settings_path.write_text(
        default_config.settings_config.read_text(encoding="utf-8").replace(
            "/blog/feed.xml",
            f"/blog/{decomposed}",
            1,
        ),
        encoding="utf-8",
    )
    config.settings_config = settings_path
    out.mkdir()
    sentinel = out / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(DocsConfigError, match=r"blog\.feed_path collides"):
        build_site(config=config, minify=False, search=False, social_cards=False)

    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_blog_feed_and_pagefind_output_may_not_overlap(tmp_path: Path) -> None:
    config, content, out = _config(tmp_path)
    _write_blog(content)
    settings_path = tmp_path / "settings.yml"
    settings_path.write_text(
        default_config.settings_config.read_text(encoding="utf-8")
        .replace("/pagefind/pagefind.js", "/blog/search/pagefind.js", 1)
        .replace("/blog/feed.xml", "/blog/search/pagefind.js/feed.xml", 1),
        encoding="utf-8",
    )
    config.settings_config = settings_path
    out.mkdir()
    sentinel = out / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(DocsConfigError, match=r"blog\.feed_path collides"):
        build_site(config=config, minify=False, search=False, social_cards=False)

    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_blog_companion_quotes_catalog_metadata_as_valid_yaml(tmp_path: Path) -> None:
    config, content, out = _config(tmp_path)
    config.site_url = "https://citry.dev/"
    source = _write_blog(content)
    authored = source.read_text(encoding="utf-8")
    authored = authored.replace("title: First post", 'title: "Migration: lessons learned"')
    authored = authored.replace(
        "description: The first Blog post.",
        r"""description: 'A path C:\tmp and a "quote".' """,
    )
    source.write_text(authored, encoding="utf-8")

    outcome = build_site(config=config, minify=False, search=False, social_cards=False)

    assert outcome.failed == 0
    companion = (out / "blog" / "first-post" / "index.md").read_text(encoding="utf-8")
    metadata = yaml.safe_load(companion.split("---", 2)[1])
    assert metadata["title"] == "Migration: lessons learned"
    assert metadata["description"] == 'A path C:\\tmp and a "quote".'


def test_version_build_excludes_blog_without_validating_current_posts(tmp_path: Path) -> None:
    config, content, out = _config(tmp_path)
    config.versions_dir = tmp_path / "versions"
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    (content / "_nav.yml").write_text(
        "areas:\n"
        "  - label: Docs\n"
        "    items:\n"
        "      - { title: Home, path: / }\n"
        "  - label: Blog\n"
        "    source: blog\n"
        "    scope: site\n"
        "    entry: { title: All posts, path: /blog/ }\n",
        encoding="utf-8",
    )
    _write_blog(content).write_text("invalid current Blog source", encoding="utf-8")

    outcome = build_site(
        config=config,
        output_dir=out,
        docs_version="1.0.0",
        minify=False,
        search=False,
        social_cards=False,
        update_versions_manifest=False,
    )

    assert outcome.failed == 0
    assert outcome.blog_posts == 0
    assert not outcome.blog_feed
    assert outcome.reference == 0
    assert outcome.releases == 0
    assert not (out / "objects.inv").exists()
    assert not (out / "blog").exists()
    home = (out / "index.html").read_text(encoding="utf-8")
    assert 'href="/blog/"' in home


def test_omitted_scope_rejects_a_site_only_generated_source(tmp_path: Path) -> None:
    config, content, out = _config(tmp_path)
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    (content / "_nav.yml").write_text(
        "areas:\n  - label: Docs\n    items: [{ title: Home, path: / }]\n  - label: Blog\n    source: blog\n",
        encoding="utf-8",
    )
    _write_blog(content).write_text("invalid current Blog source", encoding="utf-8")

    with pytest.raises(ValueError, match="must use scope 'site'"):
        build_site(
            config=config,
            output_dir=out,
            docs_version="1.0.0",
            minify=False,
            search=False,
            social_cards=False,
            update_versions_manifest=False,
        )


def test_scope_drives_snapshot_pages_assets_links_and_picker(tmp_path: Path) -> None:
    config, content, out = _config(tmp_path)
    config.base_path = "/citry"
    config.versions_dir = tmp_path / "versions"
    guide = content / "guide"
    news = content / "news"
    blog = content / "blog"
    guide.mkdir()
    news.mkdir()
    blog.mkdir()
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    (guide / "a.md").write_text(
        "# A\n\n"
        "[B](/guide/b/)\n\n"
        "[News clean](/news/)\n\n"
        "[News source](../news/index.md)\n\n"
        "[Blog source](../blog/2026-07-27-first-post.md)\n\n"
        "![Versioned asset](diagram.svg)\n\n"
        "![Site asset](../news/logo.svg)\n",
        encoding="utf-8",
    )
    (guide / "b.md").write_text("# B\n", encoding="utf-8")
    (guide / "diagram.svg").write_text("<svg>guide</svg>", encoding="utf-8")
    (news / "index.md").write_text("# News\n", encoding="utf-8")
    (news / "draft.md").write_text("<c-this-must-not-render />\n", encoding="utf-8")
    (news / "logo.svg").write_text("<svg>news</svg>", encoding="utf-8")
    (blog / "index.md").write_text("invalid current Blog index", encoding="utf-8")
    (blog / "2026-07-27-first-post.md").write_text("invalid current Blog post", encoding="utf-8")
    (content / "_nav.yml").write_text(
        "areas:\n"
        "  - label: Docs\n"
        "    scope: versioned\n"
        "    items: [{ title: Home, path: / }]\n"
        "    groups:\n"
        "      - label: Guides\n"
        "        items:\n"
        "          - { title: A, path: /guide/a/ }\n"
        "          - { title: B, path: /guide/b/ }\n"
        "  - label: News\n"
        "    scope: site\n"
        "    items: [{ title: News, path: /news/ }]\n"
        "  - label: Blog\n"
        "    source: blog\n"
        "    scope: site\n"
        "    entry: { title: All posts, path: /blog/ }\n",
        encoding="utf-8",
    )

    outcome = build_site(
        config=config,
        output_dir=out,
        docs_version="1.2.3",
        minify=False,
        search=False,
        social_cards=False,
        update_versions_manifest=False,
    )

    assert outcome.failed == 0
    assert (out / "guide" / "a" / "index.html").is_file()
    assert (out / "guide" / "diagram.svg").is_file()
    assert not (out / "news").exists()
    html = (out / "guide" / "a" / "index.html").read_text(encoding="utf-8")
    assert 'href="/citry/v/1.2.3/"' in html
    assert 'href="/citry/v/1.2.3/guide/b/"' in html
    assert 'href="/citry/news/"' in html
    assert 'href="/citry/blog/first-post/"' in html
    assert 'href="/news/"' not in html
    assert 'src="../diagram.svg"' in html
    assert 'src="/citry/news/logo.svg"' in html
    assert "djc-version-picker" in html
    not_found = (out / "404.html").read_text(encoding="utf-8")
    assert 'href="/citry/v/1.2.3/getting-started/installation/"' in not_found

    (blog / "index.md").write_text("# Blog\n\n<c-blog-list />\n", encoding="utf-8")
    (blog / "2026-07-27-first-post.md").write_text(
        "---\n"
        "title: First post\n"
        "description: A post.\n"
        "date: 2026-07-27T09:00:00+02:00\n"
        "author: Citry maintainers\n"
        "---\n\nBody.\n",
        encoding="utf-8",
    )
    root_out = tmp_path / "root-site"
    root = build_site(
        config=config,
        output_dir=root_out,
        minify=False,
        search=False,
        social_cards=False,
    )
    assert root.failed == 1  # the deliberately invalid unnaved News draft is read at the root
    news_html = (root_out / "news" / "index.html").read_text(encoding="utf-8")
    assert "djc-version-picker" not in news_html


def test_site_scoped_playground_is_built_only_at_the_root(tmp_path: Path) -> None:
    config, content, root_out = _config(tmp_path)
    config.versions_dir = tmp_path / "versions"
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    (content / "playground.md").write_text(
        "---\ntitle: Try Citry\nlayout: playground\n---\n\nHelp.\n",
        encoding="utf-8",
    )
    (content / "_nav.yml").write_text(
        "areas:\n"
        "  - label: Docs\n"
        "    scope: versioned\n"
        "    items: [{ title: Home, path: / }]\n"
        "  - label: Try it\n"
        "    scope: site\n"
        "    items: [{ title: Playground, path: /playground/ }]\n",
        encoding="utf-8",
    )

    root = build_site(
        config=config,
        output_dir=root_out,
        minify=False,
        search=False,
        social_cards=False,
    )
    snapshot_out = config.versions_dir / "1.2.3"
    snapshot = build_site(
        config=config,
        output_dir=snapshot_out,
        docs_version="1.2.3",
        minify=False,
        search=False,
        social_cards=False,
        update_versions_manifest=False,
    )

    assert root.failed == 0
    assert snapshot.failed == 0
    assert (root_out / "playground" / "index.html").is_file()
    assert not (snapshot_out / "playground").exists()
    snapshot_home = (snapshot_out / "index.html").read_text(encoding="utf-8")
    assert 'href="/playground/"' in snapshot_home
    assert 'href="/v/1.2.3/playground/"' not in snapshot_home


def test_site_scoped_landing_gets_a_version_snapshot_home_redirect(tmp_path: Path) -> None:
    config, content, out = _config(tmp_path)
    config.versions_dir = tmp_path / "versions"
    (content / "index.md").write_text("# Project landing\n", encoding="utf-8")
    (content / "guide.md").write_text("# Versioned guide\n", encoding="utf-8")
    (content / "_nav.yml").write_text(
        "home:\n"
        "  title: Project\n"
        "  path: /\n"
        "  scope: site\n"
        "areas:\n"
        "  - label: Docs\n"
        "    items:\n"
        "      - { title: Guide, path: /guide/ }\n",
        encoding="utf-8",
    )

    outcome = build_site(
        config=config,
        output_dir=out,
        docs_version="1.2.3",
        minify=False,
        search=False,
        social_cards=False,
        update_versions_manifest=False,
    )

    assert outcome.failed == 0
    assert (out / "guide" / "index.html").is_file()
    home = (out / "index.html").read_text(encoding="utf-8")
    assert 'content="0; url=guide/"' in home
    assert 'href="guide/"' in home
    assert "https://citry.dev/v/1.2.3/guide/" in home


def test_build_records_a_blog_post_render_failure(tmp_path: Path, monkeypatch) -> None:
    config, content, out = _config(tmp_path)
    post = _write_blog(content)
    post.write_text(post.read_text(encoding="utf-8").replace("Opening paragraph.", "BOOM"), encoding="utf-8")

    import docs_site._internal.build as build_mod

    real_render = build_mod.render_page

    def fake_render(source, **kwargs):
        if "BOOM" in source:
            raise RuntimeError("post failed")
        return real_render(source, **kwargs)

    monkeypatch.setattr(build_mod, "render_page", fake_render)

    outcome = build_site(config=config, minify=False, search=False, social_cards=False)

    assert outcome.failed == 1
    assert outcome.blog_posts == 0
    assert outcome.errors == [("blog/2026-07-27-first-post.md", "RuntimeError: post failed")]
    assert not (out / "blog" / "first-post" / "index.html").exists()


def test_build_refuses_unsafe_output(tmp_path: Path) -> None:
    config, content, _out = _config(tmp_path)
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    # Clearing the content dir itself would delete the sources.
    with pytest.raises(ValueError, match="unsafe output"):
        build_site(config=config, output_dir=content)
