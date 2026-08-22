"""Authoring and route contracts for Citry UI component previews."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

import pytest

from docs_site._internal.components.ui_demo import UiDemo
from docs_site._internal.project import load_docs_project
from docs_site._internal.ui_library_projection import UiLibraryCatalog, UiLibraryProjection
from docs_site._internal.ui_previews import (
    UiPreview,
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
    assert preview.name == "primary_action"
    assert preview.slug == "primary-action"
    assert preview.name == preview.source.stem
    assert preview.title == "Primary action"
    assert preview.source_open is True
    assert preview.public_path == "/ui-library/components/button/_previews/primary-action/"


def test_discovery_ignores_inline_raw_text_tags_before_a_preview(tmp_path: Path) -> None:
    _write_sources(tmp_path, snippet="preview = 1\npreview\n")
    api = tmp_path / "packages/py/citry_ui/citry_ui/components/cbutton/api.md"
    api.write_text(
        api.read_text(encoding="utf-8").replace(
            "```citry-html",
            "A native `<textarea>` keeps browser behavior.\n\n```citry-html",
            1,
        ),
        encoding="utf-8",
    )

    [preview] = discover_ui_previews(_catalog(), repo_root=tmp_path)

    assert preview.name == "primary_action"
    assert preview.slug == "primary-action"


def test_preview_rejects_a_name_that_does_not_match_its_source_file() -> None:
    with pytest.raises(UiPreviewError, match="must match source filename stem 'controlled_open'"):
        UiPreview(
            family="popover",
            name="controlled-open",
            title="Controlled open",
            source=PurePosixPath("cpopover/snippets/controlled_open.py"),
            public_path="/ui-library/components/popover/_previews/controlled-open/",
        )


def test_textarea_catalog_discovers_every_component_owned_preview() -> None:
    project = load_docs_project()

    slugs = [
        preview.slug
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "textarea"
    ]

    assert slugs == [
        "at-a-glance",
        "compose-textarea",
        "rows-and-resize",
        "variants",
        "sizes",
        "field-states",
        "validation-and-forms",
        "controlled-values",
        "native-text",
        "direction-and-content",
        "theme-customization",
    ]


def test_published_preview_names_match_their_source_filename_stems() -> None:
    project = load_docs_project()
    previews = discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)

    for preview in previews:
        assert preview.name == preview.source.stem
        assert preview.source.name == f"{preview.name}.py"
        assert preview.slug == preview.name.replace("_", "-")


def test_native_select_catalog_discovers_every_component_owned_preview() -> None:
    project = load_docs_project()

    slugs = [
        preview.slug
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "native-select"
    ]

    assert slugs == [
        "at-a-glance",
        "compose-select",
        "options-and-groups",
        "placeholder-and-required",
        "variants",
        "sizes",
        "field-states",
        "controlled-selection",
        "native-picker",
        "theme-customization",
    ]


def test_checkbox_catalog_discovers_every_component_owned_preview() -> None:
    project = load_docs_project()

    slugs = [
        preview.slug
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "checkbox"
    ]

    assert slugs == [
        "at-a-glance",
        "compose-checkbox",
        "configuration",
        "forms-and-validation",
        "controlled-states",
        "indeterminate",
        "field-states",
        "label-and-description",
        "variants-and-sizes",
        "theme-customization",
    ]


def test_alert_catalog_discovers_every_component_owned_preview() -> None:
    project = load_docs_project()

    slugs = [
        preview.slug
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "alert"
    ]

    assert slugs == [
        "at-a-glance",
        "basic-alert",
        "intents",
        "variants",
        "sizes",
        "icons",
        "actions",
        "configure",
        "announcements",
        "customization",
    ]


def test_accordion_catalog_discovers_every_component_owned_preview() -> None:
    project = load_docs_project()

    slugs = [
        preview.slug
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "accordion"
    ]

    assert slugs == [
        "at-a-glance",
        "basic-accordion",
        "controlled-value",
        "expansion-modes",
        "actions",
        "disabled-items",
        "nested-accordion",
        "variants",
        "customization",
    ]


def test_disclosure_catalog_discovers_every_component_owned_preview() -> None:
    project = load_docs_project()

    slugs = [
        preview.slug
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "disclosure"
    ]

    assert slugs == [
        "at-a-glance",
        "basic-disclosure",
        "controlled-open",
        "actions-and-disabled",
        "variants-and-sizes",
        "nested-disclosures",
        "overlays-and-dialogs",
        "forms-and-focus",
        "customization",
    ]


def test_flow_catalog_discovers_every_component_owned_preview() -> None:
    project = load_docs_project()

    slugs = [
        preview.slug
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "flow-layout"
    ]

    assert slugs == [
        "at-a-glance",
        "col-spacing",
        "row-alignment",
        "wrapping",
        "semantic-roots",
        "nested-layouts",
        "customization",
        "direction",
    ]


def test_grid_container_catalog_discovers_every_component_owned_preview() -> None:
    project = load_docs_project()

    slugs = [
        preview.slug
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "grid-container"
    ]

    assert slugs == [
        "at-a-glance",
        "responsive-columns",
        "asymmetric-layout",
        "intrinsic-grid",
        "container-sizes",
        "spacing",
        "semantics-and-nesting",
        "customization",
    ]


def test_badge_catalog_discovers_every_component_owned_preview() -> None:
    project = load_docs_project()

    slugs = [
        preview.slug
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "badge"
    ]

    assert slugs == [
        "at-a-glance",
        "basic-badges",
        "intents",
        "variants",
        "sizes-and-shapes",
        "icons",
        "counts-and-context",
        "positioning",
        "customization",
    ]


def test_divider_catalog_discovers_every_component_owned_preview() -> None:
    project = load_docs_project()

    slugs = [
        preview.slug
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "divider"
    ]

    assert slugs == [
        "at-a-glance",
        "basic-dividers",
        "semantic-and-decorative",
        "orientations",
        "labels",
        "variants-and-sizes",
        "insets",
        "customization",
    ]


def test_avatar_catalog_discovers_every_component_owned_preview() -> None:
    project = load_docs_project()

    slugs = [
        preview.slug
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "avatar"
    ]

    assert slugs == [
        "at-a-glance",
        "images-and-fallbacks",
        "accessible-names",
        "variants-and-sizes",
        "shapes",
        "reactive-sources",
        "composition",
        "customization",
    ]


def test_skeleton_catalog_discovers_every_component_owned_preview() -> None:
    project = load_docs_project()

    slugs = [
        preview.slug
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "skeleton"
    ]

    assert slugs == [
        "at-a-glance",
        "primitives",
        "text-lines",
        "field-note-card",
        "specimen-list",
        "motion",
        "customization",
    ]


def test_toolbar_catalog_discovers_every_component_owned_preview() -> None:
    project = load_docs_project()

    slugs = [
        preview.slug
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "toolbar"
    ]

    assert slugs == [
        "at-a-glance",
        "commands",
        "composition",
        "orientation",
        "variants",
        "disabled",
        "customization",
    ]


def test_file_input_catalog_discovers_every_component_owned_preview() -> None:
    project = load_docs_project()

    slugs = [
        preview.slug
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "file-input"
    ]

    assert slugs == [
        "at-a-glance",
        "field",
        "drop-target",
        "multiple",
        "capture",
        "disabled",
        "customization",
    ]


def test_stepper_catalog_discovers_every_component_owned_preview() -> None:
    project = load_docs_project()

    slugs = [
        preview.slug
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "stepper"
    ]

    assert slugs == [
        "at-a-glance",
        "interactive",
        "nonlinear",
        "states",
        "controlled",
        "presentation",
        "customization",
    ]


def test_splitter_catalog_discovers_every_component_owned_preview() -> None:
    project = load_docs_project()

    slugs = [
        preview.slug
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "splitter"
    ]

    assert slugs == [
        "at-a-glance",
        "multiple",
        "vertical-nested",
        "constraints-keyboard",
        "controlled",
        "disabled",
        "customization",
    ]


def test_tree_catalog_discovers_every_component_owned_preview() -> None:
    project = load_docs_project()

    slugs = [
        preview.slug
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "tree"
    ]

    assert slugs == [
        "at-a-glance",
        "controlled-expansion",
        "single-selection",
        "multiple-selection",
        "keyboard",
        "disabled",
        "customization",
    ]


def test_popover_catalog_discovers_every_component_owned_preview() -> None:
    project = load_docs_project()

    slugs = [
        preview.slug
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "popover"
    ]

    assert slugs == [
        "at-a-glance",
        "moon-inspector",
        "interactive-form",
        "controlled-open",
        "dismissal",
        "placements",
        "nested-popovers",
        "customization",
        "responsive-content",
    ]


def test_menu_catalog_discovers_every_component_owned_preview() -> None:
    project = load_docs_project()

    slugs = [
        preview.slug
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "menu"
    ]

    assert slugs == [
        "at-a-glance",
        "commands-and-links",
        "item-content",
        "controlled-open",
        "choices",
        "groups-and-separators",
        "submenus",
        "keyboard-and-typeahead",
        "disabled-and-forms",
        "placement-and-rtl",
        "sizes",
        "customization",
        "lifecycle",
    ]


def test_drawer_catalog_discovers_every_component_owned_preview() -> None:
    project = load_docs_project()

    slugs = [
        preview.slug
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "drawer"
    ]

    assert slugs == [
        "at-a-glance",
        "edit-field-note",
        "bottom-sheet",
        "configuration",
        "controlled-drawer",
        "long-content",
        "drawer-form",
        "nested-layers",
        "explicit-completion",
        "customization",
    ]


def test_toast_catalog_discovers_every_component_owned_preview() -> None:
    project = load_docs_project()

    slugs = [
        preview.slug
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "toast"
    ]

    assert slugs == [
        "at-a-glance",
        "reactive-queue",
        "replacement",
        "timeout-pause",
        "persistent-action",
        "visible-limit",
        "focus-access",
        "modal-pause",
        "placement-rtl",
        "customization",
    ]


def test_progress_catalog_discovers_every_component_owned_preview() -> None:
    project = load_docs_project()

    slugs = [
        preview.slug
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "progress"
    ]

    assert slugs == [
        "at-a-glance",
        "determinate",
        "indeterminate",
        "custom-range",
        "intents",
        "sizes-and-shapes",
        "controlled",
        "busy-region",
        "customization",
    ]


def test_tooltip_catalog_discovers_every_component_owned_preview() -> None:
    project = load_docs_project()

    slugs = [
        preview.slug
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "tooltip"
    ]

    assert slugs == [
        "at-a-glance",
        "moon-labels",
        "formatted-description",
        "live-text",
        "timing",
        "controlled-open",
        "placements",
        "dismissal",
        "customization",
        "responsive-text",
    ]


def test_spinner_catalog_discovers_every_component_owned_preview() -> None:
    project = load_docs_project()

    slugs = [
        preview.slug
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "spinner"
    ]

    assert slugs == [
        "at-a-glance",
        "basic",
        "intents",
        "sizes",
        "inline",
        "controlled",
        "busy-region",
        "delayed",
        "customization",
    ]


def test_radio_catalog_discovers_every_component_owned_preview() -> None:
    project = load_docs_project()

    slugs = [
        preview.slug
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "radio"
    ]

    assert slugs == [
        "at-a-glance",
        "basic",
        "descriptions",
        "controlled",
        "forms",
        "orientation",
        "presentation",
        "field",
        "customization",
    ]


def test_switch_catalog_discovers_every_component_owned_preview() -> None:
    project = load_docs_project()

    slugs = [
        preview.slug
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "switch"
    ]

    assert slugs == [
        "at-a-glance",
        "basic",
        "descriptions",
        "controlled",
        "forms",
        "presentation",
        "field",
        "semantics",
        "customization",
    ]


def test_breadcrumbs_catalog_discovers_every_component_owned_preview() -> None:
    project = load_docs_project()

    slugs = [
        preview.slug
        for preview in discover_ui_previews(project.ui_library, repo_root=project.runtime.repo_root)
        if preview.family == "breadcrumbs"
    ]

    assert slugs == [
        "at-a-glance",
        "basic",
        "current-link",
        "separators",
        "sizes",
        "overflow",
        "item-slot",
        "route-records",
        "customization",
    ]


def test_preview_module_requires_an_explicit_final_preview_expression(
    tmp_path: Path,
) -> None:
    _write_sources(tmp_path, snippet="value = 1\nvalue\n")
    [preview] = discover_ui_previews(_catalog(), repo_root=tmp_path)

    with pytest.raises(UiPreviewError, match="end with the expression `preview`"):
        render_ui_preview_document(preview, repo_root=tmp_path)


def test_preview_document_owns_its_script_under_strict_csp(tmp_path: Path) -> None:
    _write_sources(
        tmp_path,
        snippet="""
from citry import Component

class StrictPreviewDocumentSmoke(Component):
    template = "<p>Strict preview</p>"

preview = StrictPreviewDocumentSmoke()
preview
""".lstrip(),
    )
    [preview] = discover_ui_previews(_catalog(), repo_root=tmp_path)

    html = render_ui_preview_document(
        preview,
        repo_root=tmp_path,
        security_csp="strict",
        csp_nonce="DocsPreviewNonce",
    )

    assert "citry-ui-preview-height" in html
    assert 'nonce="DocsPreviewNonce"' in html


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
