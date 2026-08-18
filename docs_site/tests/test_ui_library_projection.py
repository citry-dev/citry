from dataclasses import replace
from pathlib import PurePosixPath

from docs_site._internal.guards import ui_library_projection as projection_guard
from docs_site._internal.guards.base import GuardContext
from docs_site._internal.guards.ui_library_projection import check
from docs_site._internal.project import default_docs_project, use_docs_project
from docs_site._internal.ui_library_projection import (
    UiLibraryCatalog,
    UiLibraryGroup,
    UiLibraryProjection,
    copy_ui_library_api_sources,
    ui_library_nav_groups,
    ui_library_overview_groups,
    ui_library_projection_for_path,
    ui_library_source_path,
    ui_library_source_routes,
)


def _project_with(projection):
    return replace(default_docs_project(), ui_library=UiLibraryCatalog((projection,)))


def _context(tmp_path):
    content = tmp_path / "docs_site" / "content"
    examples = tmp_path / "docs_site" / "examples"
    static = tmp_path / "docs_site" / "static"
    content.mkdir(parents=True)
    examples.mkdir(parents=True)
    static.mkdir(parents=True)
    return GuardContext(
        content_dir=content,
        examples_dir=examples,
        nav_path=content / "_nav.yml",
        static_dir=static,
        repo_root=tmp_path,
    )


def _write_component_guide(
    tmp_path,
    *,
    body="# Widget\n\n## Use Widget\n\nExample.\n",
    relative="package/components/widget/api.md",
):
    source = tmp_path / relative
    source.parent.mkdir(parents=True)
    source.write_text(body, encoding="utf-8")
    source.with_suffix(".yml").write_text(
        "schema_version: 1\n"
        "family: widget\n"
        "components: [CWidget]\n"
        "inputs: []\n"
        "slots: []\n"
        "events: []\n"
        "methods: []\n"
        "css: []\n"
        "attributes: []\n"
        "selectors: []\n"
        "interfaces: []\n"
        "translations: []\n",
        encoding="utf-8",
    )
    return source


def _widget_projection():
    return UiLibraryProjection(
        "widget",
        "widget",
        PurePosixPath("package/components/widget/api.md"),
    )


def test_catalog_keeps_source_and_public_route_ownership_separate(tmp_path):
    projection = UiLibraryProjection(
        "button",
        "button",
        PurePosixPath("package/components/button/api.md"),
    )

    source = ui_library_source_path(projection, repo_root=tmp_path)

    assert source == tmp_path / "package/components/button/api.md"
    assert projection.public_path == "/ui-library/components/button/"


def test_structured_api_source_is_published_beside_the_component_guide(tmp_path):
    source = _write_component_guide(tmp_path)
    output = tmp_path / "site"

    copied = copy_ui_library_api_sources(
        UiLibraryCatalog((_widget_projection(),)),
        repo_root=tmp_path,
        output_dir=output,
    )

    assert copied == 1
    assert (output / "ui-library/components/widget/api.yml").read_bytes() == source.with_suffix(".yml").read_bytes()


def test_projection_guard_rejects_an_obsolete_public_copy(tmp_path):
    context = _context(tmp_path)
    _write_component_guide(tmp_path)
    target = context.content_dir / "ui-library/components/button.md"
    target.parent.mkdir(parents=True)
    target.write_text("stale", encoding="utf-8")

    with use_docs_project(_project_with(_widget_projection())):
        findings = list(check(context))

    assert len(findings) == 1
    assert findings[0].source == "ui-library/components/button.md"
    assert "Obsolete" in findings[0].message


def test_projection_guard_rejects_thin_or_examples_owned_component_docs(tmp_path):
    context = _context(tmp_path)
    _write_component_guide(
        tmp_path,
        body='# Widget\n\n## Use Widget\n\n<c-example name="widget" />\n',
    )

    with use_docs_project(_project_with(_widget_projection())):
        [finding] = check(context)

    assert "component-owned source" in finding.message


def test_projection_guard_applies_registered_guide_requirements_to_synthetic_source(
    tmp_path,
    monkeypatch,
):
    context = _context(tmp_path)
    _write_component_guide(tmp_path)
    monkeypatch.setitem(
        projection_guard._GUIDE_REQUIRED_FRAGMENTS,
        "widget",
        (("required teaching token", "teach the registered synthetic contract"),),
    )

    with use_docs_project(_project_with(_widget_projection())):
        [finding] = check(context)

    assert "registered synthetic contract" in finding.message


def test_projection_guard_rejects_missing_structured_api_data(tmp_path):
    context = _context(tmp_path)
    source = tmp_path / "package/components/widget/api.md"
    source.parent.mkdir(parents=True)
    source.write_text("# Widget\n\n## Use Widget\n\nExample.\n", encoding="utf-8")

    with use_docs_project(_project_with(_widget_projection())):
        [finding] = check(context)

    assert finding.source == "package/components/widget/api.yml"
    assert "requires sibling api.yml" in finding.message


def test_projection_guard_rejects_invalid_structured_api_data(tmp_path):
    context = _context(tmp_path)
    source = _write_component_guide(tmp_path)
    source.with_suffix(".yml").write_text("family: widget\n", encoding="utf-8")

    with use_docs_project(_project_with(_widget_projection())):
        [finding] = check(context)

    assert finding.source == "package/components/widget/api.yml"
    assert "API data is invalid" in finding.message


def test_projection_guard_accepts_a_manifest_defined_new_family(tmp_path):
    context = _context(tmp_path)
    _write_component_guide(tmp_path)

    with use_docs_project(_project_with(_widget_projection())):
        findings = list(check(context))

    assert findings == []


def test_projection_guard_accepts_an_opted_in_preview_catalog(tmp_path):
    context = _context(tmp_path)
    relative = "packages/py/citry_ui/citry_ui/components/cwidget/api.md"
    projection = UiLibraryProjection("widget", "widget", PurePosixPath(relative))
    source = _write_component_guide(
        tmp_path,
        relative=relative,
        body=(
            "# Widget\n\n## Use Widget\n\n"
            '<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cwidget/snippets/first.py" '
            'title="First" />\n\n'
            '<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cwidget/snippets/second.py" '
            'title="Second" />\n'
        ),
    )
    snippets = source.parent / "snippets"
    snippets.mkdir()
    for name in ("first", "second"):
        (snippets / f"{name}.py").write_text("preview = 1\npreview\n", encoding="utf-8")
    (snippets / "catalog.yml").write_text(
        "schema_version: 1\npreviews:\n  - first\n  - second\n",
        encoding="utf-8",
    )

    with use_docs_project(_project_with(projection)):
        findings = list(check(context))

    assert findings == []


def test_projection_guard_applies_registered_preview_requirements_to_synthetic_source(
    tmp_path,
    monkeypatch,
):
    context = _context(tmp_path)
    relative = "packages/py/citry_ui/citry_ui/components/cwidget/api.md"
    projection = UiLibraryProjection("widget", "widget", PurePosixPath(relative))
    source = _write_component_guide(
        tmp_path,
        relative=relative,
        body=(
            "# Widget\n\n## Use Widget\n\n"
            '<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cwidget/snippets/first.py" '
            'title="First" />\n'
        ),
    )
    snippets = source.parent / "snippets"
    snippets.mkdir()
    (snippets / "first.py").write_text("preview = 1\npreview\n", encoding="utf-8")
    monkeypatch.setitem(
        projection_guard._PREVIEW_REQUIRED_FRAGMENTS,
        "widget",
        {"first": (("required preview token", "include the registered synthetic fixture"),)},
    )

    with use_docs_project(_project_with(projection)):
        [finding] = check(context)

    assert finding.source.endswith("snippets/first.py")
    assert "registered synthetic fixture" in finding.message


def test_projection_guard_reports_opted_in_preview_order_at_the_component_guide(tmp_path):
    context = _context(tmp_path)
    relative = "packages/py/citry_ui/citry_ui/components/cwidget/api.md"
    projection = UiLibraryProjection("widget", "widget", PurePosixPath(relative))
    source = _write_component_guide(
        tmp_path,
        relative=relative,
        body=(
            "# Widget\n\n## Use Widget\n\n"
            '<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cwidget/snippets/first.py" '
            'title="First" />\n\n'
            '<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cwidget/snippets/second.py" '
            'title="Second" />\n'
        ),
    )
    snippets = source.parent / "snippets"
    snippets.mkdir()
    for name in ("first", "second"):
        (snippets / f"{name}.py").write_text("preview = 1\npreview\n", encoding="utf-8")
    (snippets / "catalog.yml").write_text(
        "schema_version: 1\npreviews:\n  - second\n  - first\n",
        encoding="utf-8",
    )

    with use_docs_project(_project_with(projection)):
        [finding] = check(context)

    assert finding.source == relative
    assert finding.line == 5
    assert "preview order" in finding.message


def test_projection_guard_rejects_a_manual_api_reference(tmp_path):
    context = _context(tmp_path)
    _write_component_guide(
        tmp_path,
        body="# Widget\n\n## Use Widget\n\nExample.\n\n## API reference\n",
    )

    with use_docs_project(_project_with(_widget_projection())):
        [finding] = check(context)

    assert "leave API reference generation to api.yml" in finding.message


def test_catalog_resolves_source_routes_without_a_content_copy(tmp_path):
    projection = UiLibraryProjection(
        "button",
        "button",
        PurePosixPath("package/components/button/api.md"),
    )
    catalog = UiLibraryCatalog((projection,))

    routes = ui_library_source_routes(catalog, repo_root=tmp_path)

    assert routes == {(tmp_path / "package/components/button/api.md").resolve(): "/ui-library/components/button/"}
    assert ui_library_projection_for_path(catalog, "ui-library/components/button") is projection
    assert ui_library_projection_for_path(catalog, "/ui-library/components/missing/") is None


def test_functional_groups_drive_nav_and_overview_from_the_same_order(tmp_path):
    button = UiLibraryProjection(
        "button",
        "button",
        PurePosixPath("package/components/button/api.md"),
    )
    toggle = UiLibraryProjection(
        "toggle",
        "toggle",
        PurePosixPath("package/components/toggle/api.md"),
    )
    for projection, description in ((button, "Run an action."), (toggle, "Keep a pressed state.")):
        source = tmp_path.joinpath(*projection.source.parts)
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(
            f"---\ntitle: {projection.family.title()}\ndescription: {description}\n---\n",
            encoding="utf-8",
        )
    catalog = UiLibraryCatalog(
        (button, toggle),
        (UiLibraryGroup("actions", "Actions", (button, toggle)),),
    )

    [nav_group] = ui_library_nav_groups(catalog, repo_root=tmp_path)
    [overview_group] = ui_library_overview_groups(catalog, repo_root=tmp_path)

    assert nav_group.label == "Actions"
    assert [item.title for item in nav_group.items] == ["Button", "Toggle"]
    assert nav_group.collapsible
    assert nav_group.section_style
    assert overview_group == {
        "id": "actions",
        "label": "Actions",
        "items": [
            {
                "title": "Button",
                "description": "Run an action.",
                "path": "/ui-library/components/button/",
            },
            {
                "title": "Toggle",
                "description": "Keep a pressed state.",
                "path": "/ui-library/components/toggle/",
            },
        ],
    }
