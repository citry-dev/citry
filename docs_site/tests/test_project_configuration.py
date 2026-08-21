"""Strict-loader coverage for maintainer-facing docs configuration."""

from __future__ import annotations

from pathlib import Path

import pytest

from docs_site._internal.config import DocsConfig
from docs_site._internal.config import config as default_config
from docs_site._internal.config_loading import DocsConfigError
from docs_site._internal.examples import get_example_registry
from docs_site._internal.guards import make_source_context, run_guards
from docs_site._internal.pipeline import render_page
from docs_site._internal.project import current_docs_project, load_docs_project, use_docs_project
from docs_site._internal.redirects import load_redirect_catalog
from docs_site._internal.reference_pages import load_reference_catalog, validate_reference_crossref_keys
from docs_site._internal.settings import load_site_settings
from docs_site._internal.site_nav import load_site_nav
from docs_site._internal.ui_library_projection import load_ui_library_catalog

DOCS_DIR = Path(__file__).resolve().parents[1]


def test_default_project_loads_every_manifest() -> None:
    project = load_docs_project()

    assert project.settings.repository.owner == "citry-dev"
    assert project.settings.repository.full_name == "citry-dev/citry"
    assert project.site_url == "https://citry.dev/"
    assert len(project.reference.categories) == 18
    assert [(group.id, group.label) for group in project.ui_library.groups] == [
        ("actions", "Actions"),
        ("forms-inputs", "Forms and inputs"),
        ("layout", "Layout"),
        ("data-display", "Data display"),
        ("navigation", "Navigation"),
        ("feedback-status", "Feedback and status"),
        ("overlays-disclosure", "Overlays and disclosure"),
    ]
    assert [(projection.family, projection.slug) for projection in project.ui_library.projections] == [
        ("button", "button"),
        ("button-group", "button-group"),
        ("split-button", "split-button"),
        ("toggle", "toggle"),
        ("toolbar", "toolbar"),
        ("field-input", "field-input"),
        ("textarea", "textarea"),
        ("native-select", "native-select"),
        ("checkbox", "checkbox"),
        ("radio", "radio"),
        ("switch", "switch"),
        ("combobox", "combobox"),
        ("listbox", "listbox"),
        ("select", "select"),
        ("multi-select", "multi-select"),
        ("tags-input", "tags-input"),
        ("number-input", "number-input"),
        ("slider", "slider"),
        ("rating", "rating"),
        ("pin-input", "pin-input"),
        ("date-input", "date-input"),
        ("calendar", "calendar"),
        ("date-picker", "date-picker"),
        ("date-range", "date-range"),
        ("time-input", "time-input"),
        ("time-picker", "time-picker"),
        ("editable", "editable"),
        ("file-input", "file-input"),
        ("form", "form"),
        ("flow-layout", "stack-group"),
        ("grid-container", "container-grid"),
        ("scroll-area", "scroll-area"),
        ("divider", "divider"),
        ("splitter", "splitter"),
        ("avatar", "avatar"),
        ("image", "image"),
        ("badge", "badge"),
        ("card", "card"),
        ("carousel", "carousel"),
        ("icon", "icon"),
        ("list", "list"),
        ("timeline", "timeline"),
        ("table", "table"),
        ("tag", "tag"),
        ("tree", "tree"),
        ("breadcrumbs", "breadcrumbs"),
        ("pagination", "pagination"),
        ("stepper", "stepper"),
        ("sidebar", "sidebar"),
        ("tabs", "tabs"),
        ("navigation-menu", "navigation-menu"),
        ("alert", "alert"),
        ("progress", "progress"),
        ("skeleton", "skeleton"),
        ("spinner", "spinner"),
        ("toast", "toast"),
        ("accordion", "accordion"),
        ("disclosure", "disclosure"),
        ("alert-dialog", "alert-dialog"),
        ("dialog", "dialog"),
        ("drawer", "drawer"),
        ("menu", "menu"),
        ("context-menu", "context-menu"),
        ("command-palette", "command-palette"),
        ("popover", "popover"),
        ("tooltip", "tooltip"),
        ("hover-card", "hover-card"),
    ]
    assert project.redirects.redirects == ()
    assert project.versions.index_keep_recent == 2


def test_ui_catalog_groups_drive_sidebar_order_and_breadcrumbs() -> None:
    project = load_docs_project()
    tree = load_site_nav(default_config, project=project)
    area = next(area for area in tree.areas if area.label == "Citry UI")

    assert [(group.label, len(group.items), group.collapsible) for group in area.groups] == [
        ("Get started", 2, False),
        ("Actions", 5, True),
        ("Forms and inputs", 24, True),
        ("Layout", 5, True),
        ("Data display", 11, True),
        ("Navigation", 6, True),
        ("Feedback and status", 5, True),
        ("Overlays and disclosure", 11, True),
    ]
    assert tree.find_breadcrumbs("/ui-library/components/tree/") == [
        ("Citry UI", "/ui-library/"),
        ("Data display", ""),
        ("Tree", ""),
    ]


def test_settings_reject_unknown_root_table(tmp_path: Path) -> None:
    source = (DOCS_DIR / "settings.yml").read_text(encoding="utf-8")
    path = tmp_path / "settings.yml"
    path.write_text(source + "\ntypo:\n  value: true\n", encoding="utf-8")

    with pytest.raises(DocsConfigError, match="unknown key"):
        load_site_settings(path)


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("owner: citry-dev", "owner: evil/citry-dev", "GitHub owner"),
        ("owner: citry-dev", "owner: citry--dev", "GitHub owner"),
        (
            "name: citry",
            f"name: {'x' * 101}",
            "GitHub repository name",
        ),
        (
            "url: https://github.com/citry-dev/citry",
            "url: https://evil.example/prefix/citry-dev/citry",
            "exactly https://github.com/citry-dev/citry",
        ),
        ("edit_branch: main", "edit_branch: ../main", "safe Git branch"),
        (
            "issues_url: https://github.com/citry-dev/citry/issues",
            "issues_url: https://github.com/elsewhere/project/issues",
            "repository.url plus /issues",
        ),
        (
            "path: /getting-started/installation/",
            'path: "/getting-started/installation/?x=1"',
            "safe root-relative",
        ),
        ("feed_path: /blog/feed.xml", "feed_path: /blog/feed.xml#x", "safe root-relative"),
        ("feed_path: /blog/feed.xml", "feed_path: /blog/%2e%2e/feed.xml", "safe root-relative"),
        ("feed_path: /blog/feed.xml", "feed_path: /index.html", "xml path under /blog"),
        (
            "pagefind_path: /pagefind/pagefind.js",
            "pagefind_path: /search/custom.js",
            "end with /pagefind.js",
        ),
        (
            "pagefind_path: /pagefind/pagefind.js",
            "pagefind_path: /%2e%2e/search/pagefind.js",
            "safe root-relative",
        ),
        (
            "pagefind_path: /pagefind/pagefind.js",
            "pagefind_path: /C:/search/pagefind.js",
            "safe root-relative",
        ),
        (
            "pagefind_path: /pagefind/pagefind.js",
            "pagefind_path: /robots.txt/search/pagefind.js",
            "directory segments",
        ),
        ("prefix: concepts", "prefix: ../", "safe relative"),
        (
            "issues_url: https://github.com/citry-dev/citry/issues",
            "issues_url: https://user@example.com/issues",
            "absolute HTTP",
        ),
        (
            "issues_url: https://github.com/citry-dev/citry/issues",
            "issues_url: https://[broken/",
            "valid absolute HTTP",
        ),
    ],
)
def test_settings_reject_unsafe_identity_urls_and_paths(tmp_path: Path, old: str, new: str, message: str) -> None:
    source = (DOCS_DIR / "settings.yml").read_text(encoding="utf-8")
    path = tmp_path / "settings.yml"
    path.write_text(source.replace(old, new, 1), encoding="utf-8")

    with pytest.raises(DocsConfigError, match=message):
        load_site_settings(path)


def test_configuration_loaders_wrap_invalid_utf8_and_yaml_keys(tmp_path: Path) -> None:
    invalid_utf8 = tmp_path / "settings.yml"
    invalid_utf8.write_bytes(b"\xff")
    with pytest.raises(DocsConfigError, match="cannot read YAML"):
        load_site_settings(invalid_utf8)

    unhashable = tmp_path / "reference.yml"
    unhashable.write_text("? [a, b]\n: value\n", encoding="utf-8")
    with pytest.raises(DocsConfigError, match="invalid YAML"):
        load_reference_catalog(unhashable)


@pytest.mark.parametrize(
    "invalid_option",
    [
        "        nested: 2026-08-04\n",
        "        nested:\n          1: value\n",
        "        nested: .nan\n",
        "        nested: &cycle [*cycle]\n",
    ],
)
def test_settings_reject_non_json_markdown_option_values(tmp_path: Path, invalid_option: str) -> None:
    source = (DOCS_DIR / "settings.yml").read_text(encoding="utf-8")
    path = tmp_path / "settings.yml"
    path.write_text(
        source.replace("        repo_url_shorthand: true\n", f"        repo_url_shorthand: true\n{invalid_option}", 1),
        encoding="utf-8",
    )

    with pytest.raises(DocsConfigError, match=r"unsupported value|finite number|cyclic YAML alias"):
        load_site_settings(path)


def test_markdown_config_results_are_deeply_detached(tmp_path: Path) -> None:
    source = (DOCS_DIR / "settings.yml").read_text(encoding="utf-8")
    path = tmp_path / "settings.yml"
    path.write_text(
        source.replace(
            "        repo_url_shorthand: true\n",
            "        repo_url_shorthand: true\n        nested:\n          - items: [one, two]\n",
            1,
        ),
        encoding="utf-8",
    )
    settings = load_site_settings(path)

    first = settings.markdown_pages.configs()
    first["pymdownx.magiclink"]["nested"][0]["items"].append("three")

    assert settings.markdown_pages.configs()["pymdownx.magiclink"]["nested"] == [{"items": ["one", "two"]}]
    frozen = settings.markdown_pages.extension_configs["pymdownx.magiclink"]["nested"]
    with pytest.raises(TypeError):
        frozen[0]["items"] = ("changed",)


def test_reference_rejects_duplicate_yaml_keys(tmp_path: Path) -> None:
    path = tmp_path / "reference.yml"
    path.write_text(
        "categories:\n"
        "  - kind: generated_python\n"
        "    slug: component\n"
        "    slug: duplicate\n"
        "    title: Component\n"
        "    intro: Intro.\n"
        "    symbols: [citry.Component]\n",
        encoding="utf-8",
    )

    with pytest.raises(DocsConfigError, match="duplicate YAML key"):
        load_reference_catalog(path)


def test_reference_rejects_symbol_owned_by_two_pages(tmp_path: Path) -> None:
    path = tmp_path / "reference.yml"
    path.write_text(
        "categories:\n"
        "  - { kind: generated_python, slug: one, title: One, intro: One., symbols: [citry.Component] }\n"
        "  - { kind: generated_python, slug: two, title: Two, intro: Two., symbols: [citry.Component] }\n",
        encoding="utf-8",
    )

    with pytest.raises(DocsConfigError, match="multiple pages"):
        load_reference_catalog(path)


def test_reference_rejects_empty_generated_symbol_list(tmp_path: Path) -> None:
    path = tmp_path / "reference.yml"
    path.write_text(
        "categories:\n  - { kind: generated_python, slug: empty, title: Empty, intro: Empty., symbols: [] }\n",
        encoding="utf-8",
    )

    with pytest.raises(DocsConfigError, match="symbols must not be empty"):
        load_reference_catalog(path)


def test_reference_rejects_unknown_inventory_role(tmp_path: Path) -> None:
    path = tmp_path / "reference.yml"
    path.write_text(
        "categories:\n"
        "  - kind: authored_api\n"
        "    slug: browser\n"
        "    title: Browser\n"
        "    intro: Browser.\n"
        "    source: reference/browser.md\n"
        "    entries:\n"
        "      - { key: Widget, anchor: widget, role: nonsense }\n",
        encoding="utf-8",
    )

    with pytest.raises(DocsConfigError, match="role must be one of"):
        load_reference_catalog(path)


@pytest.mark.parametrize(("field", "value"), [("key", "bad key"), ("aliases", '["bad\\nkey"]')])
def test_reference_rejects_whitespace_in_inventory_keys(tmp_path: Path, field: str, value: str) -> None:
    path = tmp_path / "reference.yml"
    key = value if field == "key" else "Widget"
    aliases = f", aliases: {value}" if field == "aliases" else ""
    path.write_text(
        "categories:\n"
        "  - kind: authored_api\n"
        "    slug: browser\n"
        "    title: Browser\n"
        "    intro: Browser.\n"
        "    source: reference/browser.md\n"
        f"    entries: [{{ key: {key}, anchor: widget, role: 'js:function'{aliases} }}]\n",
        encoding="utf-8",
    )

    with pytest.raises(DocsConfigError, match="single-line inventory key without whitespace"):
        load_reference_catalog(path)


@pytest.mark.parametrize("tag", ["bad tag", "Bad-tag", "bad_tag", "-bad"])
def test_reference_rejects_non_kebab_builtin_tags(tmp_path: Path, tag: str) -> None:
    path = tmp_path / "reference.yml"
    path.write_text(
        "categories:\n"
        "  - kind: authored_builtins\n"
        "    slug: builtins\n"
        "    title: Builtins\n"
        "    intro: Builtins.\n"
        "    source: reference/builtins.md\n"
        f"    tags: [{tag!r}]\n",
        encoding="utf-8",
    )

    with pytest.raises(DocsConfigError, match="tags\\[0\\] must be lowercase kebab-case"):
        load_reference_catalog(path)


def test_reference_rejects_authored_key_matching_generated_short_name(tmp_path: Path) -> None:
    path = tmp_path / "reference.yml"
    path.write_text(
        "categories:\n"
        "  - kind: generated_python\n"
        "    slug: component\n"
        "    title: Component\n"
        "    intro: Component.\n"
        "    symbols: [citry.Component]\n"
        "  - kind: authored_api\n"
        "    slug: browser\n"
        "    title: Browser\n"
        "    intro: Browser.\n"
        "    source: reference/browser.md\n"
        "    entries:\n"
        "      - { key: Component, anchor: component, role: 'js:function' }\n",
        encoding="utf-8",
    )

    with pytest.raises(DocsConfigError, match="authored keys collide"):
        load_reference_catalog(path)


def test_reference_rejects_authored_key_matching_generated_member(tmp_path: Path) -> None:
    path = tmp_path / "reference.yml"
    path.write_text(
        "categories:\n"
        "  - kind: generated_python\n"
        "    slug: component\n"
        "    title: Component\n"
        "    intro: Component.\n"
        "    symbols: [citry.Component]\n"
        "  - kind: authored_api\n"
        "    slug: browser\n"
        "    title: Browser\n"
        "    intro: Browser.\n"
        "    source: reference/browser.md\n"
        "    entries:\n"
        "      - { key: Component.template_data, anchor: component-template-data, role: 'js:function' }\n",
        encoding="utf-8",
    )
    catalog = load_reference_catalog(path)

    with pytest.raises(DocsConfigError, match="authored keys collide"):
        validate_reference_crossref_keys(catalog)


def test_reference_rejects_generated_symbol_that_does_not_resolve(tmp_path: Path) -> None:
    path = tmp_path / "reference.yml"
    path.write_text(
        "categories:\n"
        "  - kind: generated_python\n"
        "    slug: missing\n"
        "    title: Missing\n"
        "    intro: Missing.\n"
        "    symbols: [citry.DoesNotExist]\n",
        encoding="utf-8",
    )
    catalog = load_reference_catalog(path)

    with pytest.raises(DocsConfigError, match="does not resolve"):
        validate_reference_crossref_keys(catalog)


def test_custom_project_runtime_reaches_components_and_example_discovery(tmp_path: Path) -> None:
    (tmp_path / "sample.py").write_text("CUSTOM_RUNTIME_VALUE = 42\n", encoding="utf-8")
    examples = tmp_path / "examples"
    example = examples / "custom_runtime"
    example.mkdir(parents=True)
    (example / "component.py").write_text(
        "from citry import Component\nclass CustomRuntime(Component):\n    template = '<p>custom</p>'\n",
        encoding="utf-8",
    )
    (example / "page.py").write_text(
        "from citry import Component\nclass CustomRuntimePage(Component):\n    template = '<main>custom</main>'\n",
        encoding="utf-8",
    )
    runtime = DocsConfig(repo_root=tmp_path, content_dir=tmp_path, examples_dir=examples)
    project = load_docs_project(runtime)

    rendered = render_page(
        '<c-include-file path="sample.py" />',
        project=project,
        wrap_in_layout=False,
    )
    with use_docs_project(project):
        registry = get_example_registry()

    assert "CUSTOM_RUNTIME_VALUE" in rendered.html
    assert "custom_runtime" in registry


def test_custom_project_is_self_contained_in_guard_context(tmp_path: Path) -> None:
    examples = tmp_path / "examples"
    example = examples / "custom_guard"
    example.mkdir(parents=True)
    (example / "component.py").write_text(
        "from citry import Component\nclass CustomGuard(Component):\n    template = '<p>guard</p>'\n",
        encoding="utf-8",
    )
    (example / "page.py").write_text(
        "from citry import Component\nclass CustomGuardPage(Component):\n    template = '<main>guard</main>'\n",
        encoding="utf-8",
    )
    project = load_docs_project(DocsConfig(repo_root=tmp_path, content_dir=tmp_path, examples_dir=examples))
    ctx = make_source_context(config=project.runtime, project=project)

    def observes_active_project(_ctx):
        assert current_docs_project() is project
        yield from ()

    results, ok = run_guards(ctx, guards=[observes_active_project])

    assert "custom_guard" in ctx.example_registry
    assert results == []
    assert ok


def test_explicit_project_rejects_a_different_runtime(tmp_path: Path) -> None:
    project = load_docs_project(DocsConfig(repo_root=tmp_path))

    with pytest.raises(DocsConfigError, match="does not match"):
        render_page("# Nope", project=project, config=DocsConfig(repo_root=tmp_path / "other"))


@pytest.mark.parametrize(
    ("runtime", "message"),
    [
        (DocsConfig(site_url="https://user@example.com/docs"), "DOCS_SITE_URL"),
        (DocsConfig(site_url="https://example.com:notaport/docs"), "DOCS_SITE_URL"),
        (DocsConfig(base_path='/docs" onclick="x'), "DOCS_BASE_PATH"),
        (DocsConfig(base_path="/docs?preview=1"), "DOCS_BASE_PATH"),
        (DocsConfig(base_path="/%2e%2e/docs"), "DOCS_BASE_PATH"),
        (DocsConfig(base_path="/C:/docs"), "DOCS_BASE_PATH"),
        (DocsConfig(base_path="/"), "DOCS_BASE_PATH"),
        (DocsConfig(base_path="/preview/"), "DOCS_BASE_PATH"),
    ],
)
def test_runtime_overrides_use_the_same_url_and_path_policy(runtime: DocsConfig, message: str) -> None:
    with pytest.raises(DocsConfigError, match=message):
        load_docs_project(runtime)


def test_ui_catalog_rejects_parent_path(tmp_path: Path) -> None:
    path = tmp_path / "ui_library.yml"
    path.write_text(
        "components:\n  - family: button\n    slug: button\n    source: ../button/api.md\n",
        encoding="utf-8",
    )

    with pytest.raises(DocsConfigError, match="safe repository-relative"):
        load_ui_library_catalog(path)


def test_ui_catalog_rejects_legacy_required_headings(tmp_path: Path) -> None:
    path = tmp_path / "ui_library.yml"
    path.write_text(
        "components:\n"
        "  - family: button\n"
        "    slug: button\n"
        "    source: button/api.md\n"
        "    required_headings: ['#### CButton inputs']\n",
        encoding="utf-8",
    )

    with pytest.raises(DocsConfigError, match=r"unknown key.*required_headings"):
        load_ui_library_catalog(path)


def test_ui_catalog_rejects_duplicate_families_across_groups(tmp_path: Path) -> None:
    path = tmp_path / "ui_library.yml"
    component = "      - { family: button, slug: button, source: button/api.md }\n"
    path.write_text(
        "groups:\n"
        "  - id: actions\n"
        "    label: Actions\n"
        "    components:\n"
        f"{component}"
        "  - id: inputs\n"
        "    label: Inputs\n"
        "    components:\n"
        f"{component}",
        encoding="utf-8",
    )

    with pytest.raises(DocsConfigError, match="duplicate family 'button'"):
        load_ui_library_catalog(path)


def test_redirect_catalog_rejects_chains(tmp_path: Path) -> None:
    path = tmp_path / "redirects.yml"
    path.write_text(
        "redirects:\n  - { from: /old/, to: /middle/ }\n  - { from: /middle/, to: /new/ }\n",
        encoding="utf-8",
    )

    with pytest.raises(DocsConfigError, match="collapse chain"):
        load_redirect_catalog(path)
