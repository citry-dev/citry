"""Authoring and route contracts for Citry UI component previews."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

import pytest

from docs_site._internal.components.ui_demo import UiDemo
from docs_site._internal.ui_library_projection import UiLibraryCatalog, UiLibraryProjection
from docs_site._internal.ui_previews import (
    UiPreviewError,
    discover_ui_previews,
    load_ui_preview_controls,
    render_ui_preview_document,
)


def _catalog() -> UiLibraryCatalog:
    return UiLibraryCatalog(
        (
            UiLibraryProjection(
                family="button",
                slug="button",
                source=PurePosixPath("packages/py/citry_ui/citry_ui/components/cbutton/api.md"),
            ),
        )
    )


def test_ui_demo_owns_its_dom_as_a_citry_template() -> None:
    assert "<figure" in UiDemo.template
    assert "<iframe" in UiDemo.template
    assert "<c-UiDemoControls" in UiDemo.template
    assert "<c-LiveWorkspace" in UiDemo.template
    assert "{{ block }}" not in UiDemo.template


def _write_sources(root: Path, *, snippet: str) -> None:
    component = root / "packages/py/citry_ui/citry_ui/components/cbutton"
    snippets = component / "snippets"
    snippets.mkdir(parents=True)
    (snippets / "primary_action.py").write_text(snippet, encoding="utf-8")
    (component / "api.md").write_text(
        "---\ntitle: Button\ndescription: Button docs.\n---\n\n"
        "```citry-html\n"
        '<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cbutton/snippets/ignored.py" '
        'title="Ignored example" />\n'
        "```\n\n"
        '<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cbutton/snippets/primary_action.py" '
        'title="Primary action" source_open />\n',
        encoding="utf-8",
    )


def test_discovery_ignores_documented_directives_and_derives_private_route(
    tmp_path: Path,
) -> None:
    _write_sources(tmp_path, snippet="preview = 1\npreview\n")

    [preview] = discover_ui_previews(_catalog(), repo_root=tmp_path)

    assert preview.family == "button"
    assert preview.name == "primary-action"
    assert preview.title == "Primary action"
    assert preview.source_open is True
    assert preview.public_path == "/ui-library/components/button/_previews/primary-action/"


def test_preview_module_requires_an_explicit_final_preview_expression(
    tmp_path: Path,
) -> None:
    _write_sources(tmp_path, snippet="value = 1\nvalue\n")
    [preview] = discover_ui_previews(_catalog(), repo_root=tmp_path)

    with pytest.raises(UiPreviewError, match="end with the expression `preview`"):
        render_ui_preview_document(preview, repo_root=tmp_path)


def test_preview_cannot_reach_into_another_component_family(tmp_path: Path) -> None:
    component = tmp_path / "packages/py/citry_ui/citry_ui/components/cbutton"
    component.mkdir(parents=True)
    other = tmp_path / "packages/py/citry_ui/citry_ui/components/cdialog/snippets"
    other.mkdir(parents=True)
    (other / "dialog.py").write_text("preview = 1\npreview\n", encoding="utf-8")
    (component / "api.md").write_text(
        '<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdialog/snippets/dialog.py" '
        'title="Wrong owner" />\n',
        encoding="utf-8",
    )

    with pytest.raises(UiPreviewError, match="may not use a snippet owned by 'cdialog'"):
        discover_ui_previews(_catalog(), repo_root=tmp_path)


def test_preview_controls_accept_explicit_selects_and_checkboxes(tmp_path: Path) -> None:
    _write_sources(
        tmp_path,
        snippet="""
from citry import Component

class PreviewControlsSmoke(Component):
    template = "<p>Preview</p>"

preview_controls = (
    {
        "name": "variant",
        "label": "Variant",
        "type": "select",
        "default": "quiet",
        "options": (("quiet", "Quiet"), ("bold", "Bold")),
    },
    {
        "name": "disabled",
        "label": "Disabled",
        "type": "checkbox",
        "default": False,
    },
)
preview = PreviewControlsSmoke()
preview
""".lstrip(),
    )
    [preview] = discover_ui_previews(_catalog(), repo_root=tmp_path)

    controls = load_ui_preview_controls(preview, repo_root=tmp_path)

    assert [(control.name, control.kind, control.default) for control in controls] == [
        ("variant", "select", "quiet"),
        ("disabled", "checkbox", False),
    ]
    assert [(option.value, option.label) for option in controls[0].options] == [
        ("quiet", "Quiet"),
        ("bold", "Bold"),
    ]


def test_preview_controls_reject_a_select_default_outside_its_options(tmp_path: Path) -> None:
    _write_sources(
        tmp_path,
        snippet="""
from citry import Component

class InvalidPreviewControlsSmoke(Component):
    template = "<p>Preview</p>"

preview_controls = (
    {
        "name": "variant",
        "label": "Variant",
        "type": "select",
        "default": "missing",
        "options": (("quiet", "Quiet"),),
    },
)
preview = InvalidPreviewControlsSmoke()
preview
""".lstrip(),
    )
    [preview] = discover_ui_previews(_catalog(), repo_root=tmp_path)

    with pytest.raises(UiPreviewError, match="default must match one of its option values"):
        load_ui_preview_controls(preview, repo_root=tmp_path)
