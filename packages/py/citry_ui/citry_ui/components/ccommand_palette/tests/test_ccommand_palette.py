"""Server contracts for CCommandPalette."""

from __future__ import annotations

import re
from collections.abc import Iterator, Sequence
from dataclasses import FrozenInstanceError, fields
from typing import get_type_hints

import pytest

from citry import Citry, Component, ComponentLibrary
from citry_ui.components.cbutton import CButton
from citry_ui.components.ccommand_palette import (
    CCommandPalette,
    CCommandPaletteActionDetail,
    CCommandPaletteCommand,
    CCommandPaletteGroup,
    CCommandPaletteItemSlotData,
    CCommandPaletteOpenChangeDetail,
    CCommandPaletteQueryChangeDetail,
    CCommandPaletteSeparator,
)


def _app() -> Citry:
    app = Citry(autodiscover=False)
    app.register_library(ComponentLibrary("citry-ui-command-palette-tests", (CCommandPalette, CButton)))
    return app


def _render(palette: object, *, deps: str = "ignore") -> str:
    app = _app()

    class Page(Component):
        citry = app
        template = """
          <main>{{ palette }}</main>
        """

        def template_data(self, kwargs, slots):
            return {"palette": palette}

    return Page().render().serialize(deps_strategy=deps)


def _basic(**kwargs: object) -> CCommandPalette:
    return CCommandPalette(
        label="Workspace commands",
        entries=(
            CCommandPaletteCommand(
                value="open-settings",
                label="Open settings",
                keywords=("preferences", "configuration"),
                shortcut="Ctrl ,",
            ),
        ),
        **kwargs,
    )


def test_public_exports_records_and_schemas_are_exact() -> None:
    import citry_ui.components.ccommand_palette as family

    assert family.__all__ == [
        "CCommandPalette",
        "CCommandPaletteCommand",
        "CCommandPaletteGroup",
        "CCommandPaletteSeparator",
        "CCommandPaletteEntry",
        "CCommandPaletteIntent",
        "CCommandPaletteSize",
        "CCommandPaletteActionSource",
        "CCommandPaletteActionDetail",
        "CCommandPaletteOpenReason",
        "CCommandPaletteOpenChangeDetail",
        "CCommandPaletteQueryReason",
        "CCommandPaletteQueryChangeDetail",
        "CCommandPaletteItemSlotData",
    ]
    assert [field.name for field in fields(CCommandPaletteCommand)] == [
        "value",
        "label",
        "description",
        "keywords",
        "shortcut",
        "disabled",
        "close_on_action",
        "intent",
    ]
    assert [field.name for field in fields(CCommandPaletteGroup)] == ["label", "commands"]
    assert not fields(CCommandPaletteSeparator)
    assert [field.name for field in fields(CCommandPaletteItemSlotData)] == [
        "value",
        "label",
        "description",
        "keywords",
        "shortcut",
        "disabled",
        "close_on_action",
        "intent",
    ]
    assert [field.name for field in fields(CCommandPalette.Kwargs)] == [
        "entries",
        "label",
        "id",
        "open",
        "query",
        "disabled",
        "loop",
        "close_on_action",
        "size",
        "placeholder",
        "search_label",
        "empty_label",
        "close_label",
        "onOpenChange",
        "onQueryChange",
        "onAction",
        "class_",
        "style",
        "attrs",
        "input_attrs",
    ]
    assert [field.name for field in fields(CCommandPalette.Slots)] == [
        "activator",
        "item_start",
        "item_end",
        "empty",
    ]
    assert list(get_type_hints(CCommandPaletteOpenChangeDetail)) == [
        "reason",
        "controlled",
        "source",
    ]
    assert list(get_type_hints(CCommandPaletteQueryChangeDetail)) == [
        "reason",
        "closeReason",
        "controlled",
        "source",
    ]
    assert list(get_type_hints(CCommandPaletteActionDetail)) == [
        "query",
        "source",
        "item",
        "event",
        "closeOnAction",
    ]
    with pytest.raises(FrozenInstanceError):
        CCommandPaletteCommand("value", "Label").label = "Changed"  # type: ignore[misc]


def test_smallest_palette_renders_complete_disabled_server_anatomy() -> None:
    html = _render(_basic())

    assert "data-citry-command-palette-initialized" not in html
    assert '<div class="cui-command-palette-host" data-citry-command-palette-host' in html
    assert '<dialog class="cui-command-palette"' in html
    assert 'data-citry-ui-part="command-palette"' in html
    assert '<search data-citry-ui-part="command-palette-search">' in html
    assert re.search(
        r'<input[^>]+type="text"[^>]+role="combobox"[^>]+autofocus[^>]+disabled',
        html,
    )
    assert 'role="listbox"' in html
    assert 'role="option"' in html
    assert 'data-value="open-settings"' in html
    assert 'aria-modal="true"' not in html
    assert "preferences" not in html
    assert "configuration" not in html


def test_open_server_fallback_is_visible_but_not_claimed_modal() -> None:
    html = _render(_basic(open=True, query="settled"))
    dialog = re.search(r"<dialog[^>]+>", html)
    assert dialog is not None
    assert " open" in dialog.group(0)
    assert "data-open" in dialog.group(0)
    assert "aria-modal" not in dialog.group(0)
    assert 'value="settled"' in html
    assert 'aria-expanded="true"' in html


def test_supplied_id_is_the_exact_native_dialog_identity() -> None:
    html = _render(_basic(id="owned-palette"))

    assert '<dialog class="cui-command-palette" id="owned-palette"' in html
    assert 'id="owned-palette-dialog"' not in html
    assert 'id="owned-palette-input"' in html


def test_group_separator_and_command_semantics_preserve_order() -> None:
    html = _render(
        CCommandPalette(
            label="Project navigation",
            entries=(
                CCommandPaletteGroup(
                    label="Navigation",
                    commands=(
                        CCommandPaletteCommand("overview", "Overview"),
                        CCommandPaletteCommand("activity", "Activity", disabled=True),
                    ),
                ),
                CCommandPaletteSeparator(),
                CCommandPaletteCommand(
                    "delete",
                    "Delete draft",
                    description="Moves the draft to Trash",
                    intent="danger",
                ),
            ),
        )
    )

    assert html.index("Navigation") < html.index("Overview") < html.index("Activity")
    assert html.index("Activity") < html.index("command-palette-separator") < html.index("Delete draft")
    assert 'role="group"' in html
    assert html.count('role="option"') == 3
    assert html.count('aria-disabled="true"') == 1
    assert 'data-intent="danger"' in html
    assert "Moves the draft to Trash" in html


def test_template_and_python_renderer_slots_receive_frozen_item_data() -> None:
    observed: list[tuple[str, str, bool]] = []

    def start(context: object) -> str:
        data: CCommandPaletteItemSlotData = context.data  # type: ignore[attr-defined,assignment]
        observed.append((data.value, data.label, data.close_on_action))
        return "visual-start"

    html = _render(
        CCommandPalette(
            label="Commands",
            entries=(CCommandPaletteCommand("copy", "Copy ID", close_on_action=False),),
            slots={"item_start": start, "item_end": "visual-end", "empty": "Nothing here"},
        )
    )
    assert observed == [("copy", "Copy ID", False)]
    assert "visual-start" in html
    assert "visual-end" in html
    assert "Nothing here" in html
    assert html.count("data-citry-command-palette-visual") == 3
    assert 'aria-hidden="true"' in html
    assert " inert" in html


def test_activator_slot_receives_owned_dialog_attributes() -> None:
    seen: list[tuple[dict[str, object], bool]] = []

    def activator(context: object) -> CButton:
        attrs = context.data.activator_attrs  # type: ignore[attr-defined]
        seen.append((attrs, context.data.activator_disabled))  # type: ignore[attr-defined]
        return CButton(attrs=attrs, slots={"default": "Open commands"})

    html = _render(_basic(slots={"activator": activator}))
    assert len(seen) == 1
    assert seen[0][0]["aria-haspopup"] == "dialog"
    assert seen[0][0]["aria-expanded"] == "false"
    assert "disabled" not in seen[0][0]
    assert "data-citry-command-palette-trigger" in seen[0][0]
    assert seen[0][1] is False
    assert "Open commands" in html


def test_documented_cbutton_activator_composition_uses_companion_disabled_state() -> None:
    def activator(context: object) -> CButton:
        return CButton(
            disabled=context.data.activator_disabled,  # type: ignore[attr-defined]
            attrs=context.data.activator_attrs,  # type: ignore[attr-defined]
            slots={"default": "Open commands"},
        )

    html = _render(_basic(disabled=True, slots={"activator": activator}))
    assert 'data-citry-command-palette-trigger=""' in html
    assert "Open commands" in html
    assert re.search(r"<button[^>]+disabled", html)


@pytest.mark.parametrize(
    ("entries", "message"),
    [
        ((CCommandPaletteSeparator(), CCommandPaletteCommand("a", "A")), "cannot be first"),
        ((CCommandPaletteCommand("a", "A"), CCommandPaletteSeparator()), "cannot be last"),
        (
            (
                CCommandPaletteCommand("a", "A"),
                CCommandPaletteSeparator(),
                CCommandPaletteSeparator(),
                CCommandPaletteCommand("b", "B"),
            ),
            "cannot be consecutive",
        ),
    ],
)
def test_separator_order_is_validated(
    entries: tuple[CCommandPaletteCommand | CCommandPaletteSeparator, ...],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        _render(CCommandPalette(label="Commands", entries=entries))


def test_groups_are_nonempty_flat_and_commands_are_globally_unique() -> None:
    with pytest.raises(ValueError, match="at least one command"):
        _render(CCommandPalette(label="Commands", entries=(CCommandPaletteGroup("Empty", ()),)))
    with pytest.raises(TypeError, match="only CCommandPaletteCommand"):
        _render(
            CCommandPalette(
                label="Commands",
                entries=(CCommandPaletteGroup("Bad", (CCommandPaletteSeparator(),)),),  # type: ignore[arg-type]
            )
        )
    with pytest.raises(ValueError, match="globally unique"):
        _render(
            CCommandPalette(
                label="Commands",
                entries=(
                    CCommandPaletteCommand("same", "First"),
                    CCommandPaletteGroup("Group", (CCommandPaletteCommand("same", "Second"),)),
                ),
            )
        )


def test_record_sequences_are_snapshotted_once_without_mutable_leaks() -> None:
    class OnePassEntries(Sequence[CCommandPaletteCommand]):
        def __init__(self) -> None:
            self.iterations = 0
            self.values = (CCommandPaletteCommand("one", "One", keywords=("first",)),)

        def __len__(self) -> int:
            return len(self.values)

        def __getitem__(self, index: int) -> CCommandPaletteCommand:
            return self.values[index]

        def __iter__(self) -> Iterator[CCommandPaletteCommand]:
            self.iterations += 1
            if self.iterations > 1:
                raise RuntimeError("entries were consumed twice")
            return iter(self.values)

    entries = OnePassEntries()
    html = _render(CCommandPalette(label="Commands", entries=entries), deps="simple")
    assert entries.iterations == 1
    assert "One" in html


def test_command_ceiling_is_enforced() -> None:
    entries = tuple(CCommandPaletteCommand(f"value-{index}", f"Value {index}") for index in range(501))
    with pytest.raises(ValueError, match="at most 500"):
        _render(CCommandPalette(label="Commands", entries=entries))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"label": "   "},
        {"query": "bad\0query"},
        {"size": "xl"},
        {"disabled": 1},
        {"loop": "yes"},
        {"close_on_action": None},
    ],
)
def test_root_strings_choices_and_booleans_are_validated(kwargs: dict[str, object]) -> None:
    with pytest.raises((TypeError, ValueError)):
        _render(_basic(**kwargs))


@pytest.mark.parametrize(
    "command",
    [
        CCommandPaletteCommand("", "Label"),
        CCommandPaletteCommand("value", "   "),
        CCommandPaletteCommand("value", "Label", description="\n"),
        CCommandPaletteCommand("value", "Label", keywords=("",)),
        CCommandPaletteCommand("value", "Label", intent="warning"),  # type: ignore[arg-type]
        CCommandPaletteCommand("value", "Label", disabled=1),  # type: ignore[arg-type]
    ],
)
def test_command_fields_are_plain_and_typed(command: CCommandPaletteCommand) -> None:
    with pytest.raises((TypeError, ValueError)):
        _render(CCommandPalette(label="Commands", entries=(command,)))


@pytest.mark.parametrize(
    ("destination", "attrs"),
    [
        ("attrs", {"aria-label": "forged"}),
        ("attrs", {"open": True}),
        ("attrs", {"x-bind": "{}"}),
        ("attrs", {"@cancel": "x"}),
        ("attrs", {"data-cid-forged": "x"}),
        ("input_attrs", {"value": "forged"}),
        ("input_attrs", {"name": "query"}),
        ("input_attrs", {":aria-controls": "forged"}),
        ("input_attrs", {"@input": "x"}),
        ("input_attrs", {"oninput": "x"}),
    ],
)
def test_owned_attrs_directives_markers_events_and_forms_are_rejected(
    destination: str,
    attrs: dict[str, object],
) -> None:
    with pytest.raises(ValueError, match="CCommandPalette"):
        _render(_basic(**{destination: attrs}))


def test_safe_attrs_land_on_exact_destinations() -> None:
    html = _render(
        _basic(
            class_="command-dialog",
            style={"inline-size": "32rem"},
            attrs={"dir": "rtl", "data-testid": "palette"},
            input_attrs={"class": "command-search", "inputmode": "search", "enterkeyhint": "go"},
        )
    )
    dialog = re.search(r"<dialog[^>]+>", html)
    search = re.search(r"<input[^>]+command-search[^>]+>", html)
    assert dialog is not None
    assert search is not None
    assert 'class="cui-command-palette command-dialog"' in dialog.group(0)
    assert 'style="inline-size: 32rem;"' in dialog.group(0)
    assert 'dir="rtl"' in dialog.group(0)
    assert 'data-testid="palette"' in dialog.group(0)
    assert 'inputmode="search"' in search.group(0)
    assert 'enterkeyhint="go"' in search.group(0)


def test_visual_slots_reject_detectable_interaction_but_allow_decorative_images() -> None:
    app = _app()

    class InteractiveButton(Component):
        citry = app
        template = '<button type="button">Act</button>'

    class InteractiveLink(Component):
        citry = app
        template = '<a href="/next">Next</a>'

    class MeaningfulImage(Component):
        citry = app
        template = '<img src="/icon.png" alt="Meaningful">'

    class DecorativeImage(Component):
        citry = app
        template = '<img src="/icon.png" alt="">'

    with pytest.raises(ValueError, match="cannot contain interactive content"):
        _render(_basic(slots={"item_start": InteractiveButton()}))
    with pytest.raises(ValueError, match="cannot contain interactive content"):
        _render(_basic(slots={"empty": InteractiveLink()}))
    with pytest.raises(ValueError, match="cannot contain interactive content"):
        _render(_basic(slots={"item_end": MeaningfulImage()}))
    html = _render(_basic(slots={"item_start": DecorativeImage()}))
    assert "/icon.png" in html


def test_dependencies_emit_each_private_helper_once() -> None:
    html = _render(_basic(), deps="simple")
    assert html.count("citry-ui:dialog-controller-runtime") >= 1
    assert html.count("citry-ui:active-descendant-runtime") >= 1
    assert html.count("citry-ui:anchored-layer-runtime") >= 1
    assert html.count("CCommandPalette private runtime dependency did not load") == 1
