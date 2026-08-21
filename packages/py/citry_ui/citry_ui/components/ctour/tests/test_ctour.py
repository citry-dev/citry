from __future__ import annotations

import inspect
import re
from dataclasses import fields
from pathlib import Path
from typing import get_type_hints

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CTour, CTourStep
from citry_ui.components._anchored_layer import ANCHORED_LAYER_RUNTIME_DEPENDENCY
from citry_ui.components._dialog_controller import DIALOG_CONTROLLER_RUNTIME_DEPENDENCY
from citry_ui.quality.asset_sources import read_component_source_css


def _render(source: str, *, css: bool = False) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = f"<main>{source}</main>{'<c-css />' if css else ''}"

    return str(Page())


def _render_client(source: str) -> str:
    app = Citry(
        autodiscover=False,
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US",),
                "catalogs": ("citry_ui_i18n",),
            }
        },
    )
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = f'<c-i18n tag="main" c-client="True">{source}</c-i18n>'

    return str(Page())


def _tour(*steps: str, attrs: str = "") -> str:
    return f'<c-CTour id="guide" {attrs}><c-fill name="default">{"".join(steps)}</c-fill></c-CTour>'


def _step(value: str, body: str = "Body", *, attrs: str = "", title: str = "Title") -> str:
    return (
        f'<c-CTourStep value="{value}" {attrs}><c-fill name="title">{title}</c-fill>'
        f'<c-fill name="default">{body}</c-fill></c-CTourStep>'
    )


def _tag(html: str, part: str, index: int = 0) -> str:
    matches = re.findall(rf'<[^>]+data-citry-ui-part="{part}"[^>]*>', html)
    assert len(matches) > index
    return matches[index]


def test_public_schema_aliases_dependencies_and_registration_are_exact() -> None:
    assert [item.name for item in fields(CTour.Kwargs)] == [
        "id",
        "open",
        "active",
        "dismissible",
        "close_on_escape",
        "close_on_outside",
        "skippable",
        "scroll",
        "missing_target",
        "size",
        "close_label",
        "previous_label",
        "next_label",
        "finish_label",
        "skip_label",
        "progress_label",
        "class_",
        "style",
        "attrs",
    ]
    assert [item.name for item in fields(CTour.Slots)] == ["default", "activator", "close"]
    assert [item.name for item in fields(CTourStep.Kwargs)] == [
        "value",
        "target_id",
        "placement",
        "arrow",
        "describe",
        "class_",
        "style",
        "attrs",
    ]
    assert [item.name for item in fields(CTourStep.Slots)] == ["title", "default", "media"]
    tour_hints = get_type_hints(CTour.Kwargs)
    step_hints = get_type_hints(CTourStep.Kwargs)
    assert tour_hints["scroll"] == citry_ui.CTourScroll
    assert tour_hints["missing_target"] == citry_ui.CTourMissingTarget
    assert step_hints["placement"] == citry_ui.CTourPlacement
    assert CTour.Dependencies.js == [ANCHORED_LAYER_RUNTIME_DEPENDENCY, DIALOG_CONTROLLER_RUNTIME_DEPENDENCY]
    assert CTour in citry_ui.COMPONENTS
    assert CTourStep in citry_ui.COMPONENTS


def test_default_tour_is_server_rendered_native_dialog_with_modal_anatomy() -> None:
    html = _render(_tour(_step("welcome")))
    root = _tag(html, "tour")
    dialog = _tag(html, "dialog")
    panel = _tag(html, "panel")

    assert 'id="guide"' in root
    assert 'data-active="0"' in root
    assert 'data-value="welcome"' in root
    assert 'data-size="md"' in root
    assert "data-open" not in root
    assert dialog.startswith("<dialog")
    assert 'id="guide-dialog"' in dialog
    assert 'aria-modal="true"' in dialog
    assert 'aria-labelledby="guide-title-0"' in dialog
    assert "aria-describedby" not in dialog
    assert "data-current" in panel
    assert "hidden" not in panel
    assert "inert" not in panel
    for part in ("spotlight", "surface", "title", "description", "footer", "progress", "actions", "close"):
        assert f'data-citry-ui-part="{part}"' in html
    assert 'type="button"' in html
    assert "Step \u20681\u2069 of \u20681\u2069" in html


def test_initial_open_active_target_and_description_are_exact() -> None:
    html = _render(
        _tour(
            _step("intro"),
            _step(
                "save",
                attrs='target_id="save-button" placement="inline-end" c-describe="True"',
                title="Save",
            ),
            attrs='c-open="True" c-active="1" size="lg" scroll="smooth" missing_target="close"',
        )
    )
    root = _tag(html, "tour")
    dialog = _tag(html, "dialog")
    second = _tag(html, "panel", 1)

    assert "data-open" in root
    assert 'data-active="1"' in root
    assert 'data-value="save"' in root
    assert 'data-size="lg"' in root
    assert "open" in dialog
    assert 'aria-labelledby="guide-title-1"' in dialog
    assert 'aria-describedby="guide-description-1"' in dialog
    assert 'data-target-id="save-button"' in second
    assert 'data-placement="inline-end"' in second
    assert 'data-describe="true"' in second
    assert _tag(html, "panel", 0).count("hidden") == 1


def test_slots_receive_stable_step_data_and_custom_close_renders() -> None:
    html = _render(
        '<c-CTour><c-fill name="close">X</c-fill><c-fill name="default">'
        '<c-CTourStep value="profile"><c-fill name="title" data="{ index, total, value }">'
        '{{ index }}:{{ total }}:{{ value }}</c-fill><c-fill name="media" data="{ value }">'
        'M{{ value }}</c-fill><c-fill name="default" data="{ index }">B{{ index }}</c-fill>'
        "</c-CTourStep></c-fill></c-CTour>"
    )
    assert "0:1:profile" in html
    assert "Mprofile" in html
    assert "B0" in html
    assert re.search(r'data-citry-tour-action="close"[^>]*>.*?X.*?</button>', html, re.DOTALL)
    assert 'data-citry-ui-part="media"' in html


def test_activator_contract_and_root_step_styling_merge() -> None:
    html = _render(
        "<c-CTour id=\"styled\" c-class_=\"['brand']\" c-style=\"{'--cui-tour-width':'22rem'}\" "
        "c-attrs=\"{'data-test':'tour','class':'extra'}\">"
        '<c-fill name="activator" data="{ activator_attrs }"><button c-bind="activator_attrs">Begin</button></c-fill>'
        '<c-fill name="default"><c-CTourStep value="one" c-class_="[\'step-extra\']" '
        "c-attrs=\"{'data-test-step':'one'}\"><c-fill name=\"title\">One</c-fill>"
        '<c-fill name="default">Body</c-fill></c-CTourStep></c-fill></c-CTour>'
    )
    root = _tag(html, "tour")
    panel = _tag(html, "panel")
    assert all(token in root for token in ("cui-tour", "brand", "extra", 'data-test="tour"'))
    assert "--cui-tour-width: 22rem" in root
    assert all(token in panel for token in ("cui-tour__panel", "step-extra", 'data-test-step="one"'))
    assert re.search(
        r'<button aria-haspopup="dialog" aria-controls="styled-dialog" aria-expanded="false" '
        r'data-citry-tour-trigger="">Begin</button>',
        html,
    )


def test_default_labels_register_catalog_bindings_and_overrides_do_not() -> None:
    default_html = _render_client(_tour(_step("one")))
    assert default_html.count("data-citry-i18n-binding=") == 6
    for key in ("close", "previous", "next", "finish", "skip", "progress"):
        assert f"citry-ui-tour-{key}" in default_html

    custom_html = _render_client(
        _tour(
            _step("one"),
            attrs=(
                'close_label="Dismiss" previous_label="Back" next_label="Forward" '
                'finish_label="Done" skip_label="Later" progress_label="Stage {current}/{total}"'
            ),
        )
    )
    for text in ("Dismiss", "Back", "Forward", "Done", "Later", "Stage 1/1"):
        assert text in custom_html
    for key in ("close", "previous", "next", "finish", "skip", "progress"):
        assert f"citry-ui-tour-{key}" not in custom_html


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("<c-CTour />", "requires 1 slot"),
        (_tour("<p>Loose</p>" + _step("one")), "only CTourStep declarations"),
        (_tour(_step("one") + _step("one")), "duplicated"),
        (_tour(_step("one"), attrs='c-active="1"'), "outside its 1 Steps"),
        (_tour(_step("one"), attrs='c-active="-1"'), "nonnegative integer"),
        (_tour(_step("one"), attrs='scroll="instant"'), "scroll must be one of"),
        (_tour(_step("one"), attrs='missing_target="wait"'), "missing_target must be one of"),
        (_tour(_step("one"), attrs='size="xl"'), "size must be one of"),
        (_tour(_step("one", attrs='placement="center"')), "placement must be one of"),
        (_tour(_step("one", attrs='target_id="bad id"')), "cannot contain ASCII whitespace"),
        (_tour(_step("one"), attrs='progress_label="Step"'), "must contain {current} and {total}"),
    ],
)
def test_invalid_structure_and_values_fail_closed(source: str, message: str) -> None:
    with pytest.raises((SyntaxError, TypeError, ValueError), match=re.escape(message)):
        _render(source)


def test_step_outside_tour_and_direct_nested_tour_fail() -> None:
    with pytest.raises(ValueError, match="directly inside CTour"):
        _render(_step("loose"))
    with pytest.raises(ValueError, match="Nested CTour"):
        _render(_tour(_tour(_step("nested")) + _step("outer")))


@pytest.mark.parametrize(
    "source",
    [
        _tour(_step("one"), attrs="c-attrs=\"{'data-open':True}\""),
        _tour(_step("one"), attrs="c-attrs=\"{'x-html':'unsafe'}\""),
        _tour(_step("one", attrs="c-attrs=\"{'hidden':True}\"")),
        _tour(_step("one", attrs="c-attrs=\"{':data-value':'shadow'}\"")),
    ],
)
def test_owned_attrs_and_replacing_directives_are_rejected(source: str) -> None:
    with pytest.raises(ValueError, match="cannot"):
        _render(source)


def test_runtime_contract_covers_state_geometry_cleanup_and_reasoned_callbacks() -> None:
    source = (Path(__file__).parents[1] / "runtime.source.js").read_text(encoding="utf8")
    for token in (
        "onOpenChange",
        "onActiveChange",
        "missing-target",
        "ResizeObserver",
        "MutationObserver",
        "scrollIntoView",
        "getElementById",
        "requestAnimationFrame",
        "controller.cleanup({handoff: true})",
        'dialog.addEventListener("keydown", onKeyDown)',
        'host.removeEventListener("click", onClick)',
    ):
        assert token in source
    assert "querySelector(data.target" not in source
    assert "innerHTML" not in source


def test_css_exposes_public_variables_and_environment_rules() -> None:
    css = read_component_source_css("ctour")
    for token in (
        "--cui-tour-width",
        "--cui-tour-backdrop-color",
        "--cui-tour-spotlight-padding",
        "--cui-tour-focus-color",
        "::backdrop",
        "100vmax",
        "prefers-reduced-motion",
        "forced-colors",
        "@media print",
    ):
        assert token in css


def test_messages_are_the_final_component_class_member() -> None:
    source = inspect.getsource(CTour)
    assert source.rfind("\n    messages =") > source.rfind("\n    css_file =")
    assert "\n    def " not in source[source.rfind("\n    messages =") :]
    assert CTour.I18n.messages_locale == "en-US"
    for key in ("close", "previous", "next", "finish", "skip", "progress"):
        assert f"citry-ui-tour-{key} =" in CTour.messages
