"""Tests for structured Citry UI API validation and Markdown rendering."""

from __future__ import annotations

from pathlib import Path

import pytest

from docs_site._internal.config_loading import DocsConfigError
from docs_site._internal.project import load_docs_project
from docs_site._internal.ui_library_reference import (
    compose_ui_library_source,
    load_ui_api_reference,
    render_ui_api_reference,
)


def _valid_reference() -> str:
    return """\
schema_version: 1
family: widget
components:
  - CWidget
inputs:
  - id: cwidget-server
    component: CWidget
    channel: server
    column_widths: [fit, 11rem, 7rem, auto]
    entries:
      - id: tone
        name: tone
        type:
          display: quiet | loud
          interfaces:
            - CWidgetTone
        default:
          kind: literal
          value: quiet
        effect: Selects the presentation tone.
  - id: cwidget-client
    component: CWidget
    channel: client
    entries:
      - id: tone
        name: tone
        type:
          display: quiet | loud
          interfaces:
            - CWidgetTone
        omitted: Uses the server input.
        effect: Reactively controls presentation.
slots:
  - id: cwidget
    component: CWidget
    entries:
      - id: default
        name: default
        required: true
        data:
          display: "{active: bool}"
          interfaces:
            - CWidgetDefaultSlotData
        fallback: none
events: []
methods: []
attributes:
  - id: cwidget
    component: CWidget
    entries:
      - id: data-tone
        name: data-tone
        element: root
        type: quiet | loud
        meaning: Effective presentation tone.
selectors:
  - id: cwidget
    component: CWidget
    entries:
      - id: root
        anchor: widget-selector-root
        selector: '[data-citry-ui-part="widget"]'
        element: Root div
        purpose: Stable styling hook.
css:
  - id: cwidget
    component: CWidget
    entries:
      - id: foreground
        name: --cui-widget-foreground
        type: color | currentColor
        purpose: Widget text.
        default: currentColor
interfaces:
  - id: input-types
    kind: aliases
    entries:
      - id: cwidget-tone
        name: CWidgetTone
        definition: Literal["quiet", "loud"]
  - id: cwidget-default-slot-data
    kind: record
    name: CWidgetDefaultSlotData
    entries:
      - id: active
        name: active
        type: bool
        meaning: Whether the widget is active.
translations:
  - id: cwidget-translations
    component: CWidget
    entries:
      - id: label
        key: citry-ui-widget-label
        purpose: Names the widget.
        variables: None
        override: label input
        updates: $c-tr updates aria-label.
"""


def _write_reference(tmp_path: Path, source: str | None = None) -> Path:
    path = tmp_path / "api.yml"
    path.write_text(source or _valid_reference(), encoding="utf-8")
    return path


def test_every_catalogued_ui_family_has_a_valid_composable_reference() -> None:
    project = load_docs_project()

    for projection in project.ui_library.projections:
        source = project.runtime.repo_root / projection.source
        composed = compose_ui_library_source(source, family=projection.family)

        assert "## API reference" in composed


def test_structured_reference_renders_the_fixed_api_shape(tmp_path: Path) -> None:
    reference = load_ui_api_reference(_write_reference(tmp_path), expected_family="widget")

    rendered = render_ui_api_reference(reference)

    headings = tuple(line for line in rendered.splitlines() if line.startswith("### "))
    assert headings == (
        "### Inputs",
        "### Slots",
        "### Events",
        "### Methods",
        "### CSS",
        "### Attributes",
        "### Selectors",
        "### Interfaces",
        "### Translation keys",
    )
    assert "The reference below lists" not in rendered
    assert "#### CWidget server inputs" in rendered
    assert "#### CWidget client inputs" in rendered
    assert "| Input | Type | Omitted behavior | Effect |" in rendered
    assert "tabs" not in rendered
    assert "<code>quiet &#124; loud</code>" in rendered
    assert "<code>color &#124; currentColor</code>" in rendered
    assert r"\|" not in rendered
    assert "ui-api-table--fit-column-1" in rendered
    assert "ui-api-table--width-column-2" in rendered
    assert "--ui-api-column-2-width: 11rem" in rendered
    assert '<span id="widget-selector-root"></span>' in rendered
    assert '<span id="widget-input-cwidget-server-tone"></span>`tone`' in rendered
    assert "[`CWidgetTone`](#widget-interface-cwidget-tone)" in rendered
    assert '<span id="widget-interface-cwidget-default-slot-data"></span>' in rendered
    assert '<span id="widget-translation-cwidget-translations-label"></span>' in rendered
    assert "| Key | Purpose | Variables | Override | Browser updates |" in rendered
    assert rendered.count("### Methods\n\n-\n") == 1


def test_structured_reference_rejects_unknown_fields(tmp_path: Path) -> None:
    source = _valid_reference().replace("family: widget\n", "family: widget\ntypo: true\n", 1)

    with pytest.raises(DocsConfigError, match="Additional properties are not allowed"):
        load_ui_api_reference(_write_reference(tmp_path, source), expected_family="widget")


def test_structured_reference_rejects_invalid_column_widths(tmp_path: Path) -> None:
    source = _valid_reference().replace(
        "column_widths: [fit, 11rem, 7rem, auto]",
        "column_widths: [fit, wide, auto]",
        1,
    )

    with pytest.raises(DocsConfigError, match="column_widths"):
        load_ui_api_reference(_write_reference(tmp_path, source), expected_family="widget")


def test_structured_reference_rejects_unresolved_interfaces(tmp_path: Path) -> None:
    source = _valid_reference().replace("CWidgetTone\n", "CMissingTone\n", 1)

    with pytest.raises(DocsConfigError, match="unknown interface 'CMissingTone'"):
        load_ui_api_reference(_write_reference(tmp_path, source), expected_family="widget")


def test_structured_reference_rejects_duplicate_entry_ids(tmp_path: Path) -> None:
    source = _valid_reference().replace(
        "        effect: Selects the presentation tone.\n",
        "        effect: Selects the presentation tone.\n"
        "      - id: tone\n"
        "        name: other_tone\n"
        "        type: str\n"
        "        default:\n"
        "          kind: literal\n"
        "          value: quiet\n"
        "        effect: Duplicates the stable row identity.\n",
        1,
    )

    with pytest.raises(DocsConfigError, match="duplicate entry id 'tone'"):
        load_ui_api_reference(_write_reference(tmp_path, source), expected_family="widget")


def test_component_page_composition_appends_structured_reference(tmp_path: Path) -> None:
    guide = tmp_path / "api.md"
    guide.write_text("# Widget\n\n## Use Widget\n\nExample.\n", encoding="utf-8")
    _write_reference(tmp_path)

    composed = compose_ui_library_source(guide, family="widget")

    assert composed.startswith("# Widget\n\n## Use Widget")
    assert composed.count("## API reference") == 1
    assert composed.index("## Use Widget") < composed.index("## API reference")


def test_component_page_composition_rejects_a_manual_structured_reference(tmp_path: Path) -> None:
    guide = tmp_path / "api.md"
    guide.write_text("# Widget\n\n## Use Widget\n\nExample.\n\n## API reference\n", encoding="utf-8")
    _write_reference(tmp_path)

    with pytest.raises(DocsConfigError, match=r"leave API reference generation to api\.yml"):
        compose_ui_library_source(guide, family="widget")


def test_component_page_composition_requires_structured_api_data(tmp_path: Path) -> None:
    guide = tmp_path / "api.md"
    guide.write_text("# Widget\n\n## Use Widget\n\nExample.\n", encoding="utf-8")

    with pytest.raises(DocsConfigError, match=r"requires sibling api\.yml"):
        compose_ui_library_source(guide, family="widget")
