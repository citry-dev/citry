from pathlib import PurePosixPath

from docs_site._internal.guards.base import GuardContext
from docs_site._internal.guards.ui_library_projection import check
from docs_site._internal.ui_library_projection import (
    UiLibraryProjection,
    projection_paths,
    sync_ui_library_docs,
)


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


def test_projection_paths_keep_source_and_public_route_ownership_separate(tmp_path):
    projection = UiLibraryProjection(
        "button",
        PurePosixPath("package/components/button/api.md"),
        PurePosixPath("ui-library/components/button.md"),
    )

    source, target = projection_paths(
        projection,
        repo_root=tmp_path,
        content_dir=tmp_path / "content",
    )

    assert source == tmp_path / "package/components/button/api.md"
    assert target == tmp_path / "content/ui-library/components/button.md"


def test_projection_guard_reports_stale_public_copy(tmp_path, monkeypatch):
    context = _context(tmp_path)
    source = tmp_path / "package/components/button/api.md"
    target = context.content_dir / "ui-library/components/button.md"
    source.parent.mkdir(parents=True)
    target.parent.mkdir(parents=True)
    source.write_text("source", encoding="utf-8")
    target.write_text("stale", encoding="utf-8")
    projection = UiLibraryProjection(
        "button",
        PurePosixPath("package/components/button/api.md"),
        PurePosixPath("ui-library/components/button.md"),
    )
    monkeypatch.setattr(
        "docs_site._internal.guards.ui_library_projection.UI_LIBRARY_PROJECTIONS",
        (projection,),
    )

    findings = list(check(context))

    assert len(findings) == 1
    assert findings[0].source == "ui-library/components/button.md"
    assert "differs" in findings[0].message


def test_projection_guard_rejects_thin_or_examples_owned_component_docs(tmp_path, monkeypatch):
    context = _context(tmp_path)
    source = tmp_path / "package/components/button/api.md"
    target = context.content_dir / "ui-library/components/button.md"
    source.parent.mkdir(parents=True)
    target.parent.mkdir(parents=True)
    content = '# Button\n\n## Use Button\n\n<c-example name="button" />\n\n## API reference\n'
    source.write_text(content, encoding="utf-8")
    target.write_text(content, encoding="utf-8")
    projection = UiLibraryProjection(
        "button",
        PurePosixPath("package/components/button/api.md"),
        PurePosixPath("ui-library/components/button.md"),
    )
    monkeypatch.setattr(
        "docs_site._internal.guards.ui_library_projection.UI_LIBRARY_PROJECTIONS",
        (projection,),
    )

    [finding] = check(context)

    assert "component-owned source" in finding.message


def test_projection_guard_rejects_out_of_order_api_categories(tmp_path, monkeypatch):
    context = _context(tmp_path)
    source = tmp_path / "package/components/button/api.md"
    target = context.content_dir / "ui-library/components/button.md"
    source.parent.mkdir(parents=True)
    headings = (
        "### Slots",
        "### Inputs",
        "### Events",
        "### Methods",
        "### Attributes",
        "### Selectors",
        "### CSS",
        "### Interfaces",
        "#### CButton server inputs",
        "#### CButton client inputs",
        "#### CButton slots",
        "#### CButton events",
        "#### CButton attributes",
        "#### CButton selectors",
        "#### CButton CSS variables",
    )
    content = "# Button\n\n## Use Button\n\nExample.\n\n## API reference\n\n" + "\n\n".join(headings) + "\n"
    source.write_text(content, encoding="utf-8")
    target.parent.mkdir(parents=True)
    target.write_text(content, encoding="utf-8")
    projection = UiLibraryProjection(
        "button",
        PurePosixPath("package/components/button/api.md"),
        PurePosixPath("ui-library/components/button.md"),
    )
    monkeypatch.setattr(
        "docs_site._internal.guards.ui_library_projection.UI_LIBRARY_PROJECTIONS",
        (projection,),
    )

    [finding] = check(context)

    assert "categories must follow" in finding.message


def test_projection_guard_rejects_conceptual_sections_inside_api_reference(tmp_path, monkeypatch):
    context = _context(tmp_path)
    source = tmp_path / "package/components/button/api.md"
    target = context.content_dir / "ui-library/components/button.md"
    source.parent.mkdir(parents=True)
    headings = (
        "### Inputs",
        "#### CButton server inputs",
        "#### CButton client inputs",
        "### Slots",
        "#### CButton slots",
        "### Events",
        "#### CButton events",
        "### Methods",
        "### Accessibility",
        "### Attributes",
        "#### CButton attributes",
        "### Selectors",
        "#### CButton selectors",
        "### CSS",
        "#### CButton CSS variables",
        "### Interfaces",
    )
    content = "# Button\n\n## Use Button\n\nExample.\n\n## API reference\n\n" + "\n\n".join(headings) + "\n"
    source.write_text(content, encoding="utf-8")
    target.parent.mkdir(parents=True)
    target.write_text(content, encoding="utf-8")
    projection = UiLibraryProjection(
        "button",
        PurePosixPath("package/components/button/api.md"),
        PurePosixPath("ui-library/components/button.md"),
    )
    monkeypatch.setattr(
        "docs_site._internal.guards.ui_library_projection.UI_LIBRARY_PROJECTIONS",
        (projection,),
    )

    [finding] = check(context)

    assert "must contain only" in finding.message


def test_sync_writes_exact_source_bytes(tmp_path, monkeypatch):
    context = _context(tmp_path)
    source = tmp_path / "package/components/button/api.md"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"# Button\n")
    projection = UiLibraryProjection(
        "button",
        PurePosixPath("package/components/button/api.md"),
        PurePosixPath("ui-library/components/button.md"),
    )
    monkeypatch.setattr(
        "docs_site._internal.ui_library_projection.UI_LIBRARY_PROJECTIONS",
        (projection,),
    )

    written = sync_ui_library_docs(
        repo_root=tmp_path,
        content_dir=context.content_dir,
    )

    assert written == [context.content_dir / "ui-library/components/button.md"]
    assert written[0].read_bytes() == b"# Button\n"
