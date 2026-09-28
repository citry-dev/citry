from __future__ import annotations

import re
from dataclasses import fields

import pytest
from markupsafe import Markup

import citry_ui
from citry import Citry, Component
from citry_ui import CSpinner
from citry_ui.quality.asset_sources import read_component_source_css


def _render(spinner: object, *, include_css: bool = False, static_fallback: bool = False) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <main>{{ spinner }}</main>{{ css }}
        """

        def template_data(self, kwargs, slots):
            return {
                "spinner": spinner,
                "css": app.get("css")() if include_css else "",
            }

    page = Page()
    return page.render().serialize(security_javascript="omit") if static_fallback else str(page)


def test_spinner_schema_stays_compact_and_indeterminate():
    assert [field.name for field in fields(CSpinner.Kwargs)] == [
        "label",
        "intent",
        "size",
        "class_",
        "style",
        "attrs",
    ]
    assert fields(CSpinner.Slots) == ()


def test_spinner_renders_one_labelled_unfocusable_progressbar():
    html = _render(CSpinner(label="Charting star field"), static_fallback=True)
    root = re.search(r'<span[^>]+data-citry-ui-part="spinner"[^>]*>', html)

    assert root is not None
    assert 'role="progressbar"' in root.group(0)
    assert 'aria-label="Charting star field"' in root.group(0)
    assert 'data-intent="primary"' in root.group(0)
    assert 'data-size="md"' in root.group(0)
    assert "tabindex" not in root.group(0)
    assert "aria-valuenow" not in root.group(0)
    assert "</span>" in html


def test_spinner_merges_root_styling_and_metadata():
    html = _render(
        CSpinner(
            label="Aligning telescope",
            intent="success",
            size="lg",
            class_=["orbit", {"active": True}],
            style={"--cui-spinner-size": "40px"},
            attrs={"id": "alignment", "class": "from-attrs", "aria-describedby": "alignment-help"},
        ),
        static_fallback=True,
    )
    root = re.search(r'<span[^>]+data-citry-ui-part="spinner"[^>]*>', html)

    assert root is not None
    assert 'class="cui-spinner from-attrs orbit active"' in root.group(0)
    assert 'style="--cui-spinner-size: 40px;"' in root.group(0)
    assert 'id="alignment"' in root.group(0)
    assert 'aria-describedby="alignment-help"' in root.group(0)
    assert 'data-intent="success"' in root.group(0)
    assert 'data-size="lg"' in root.group(0)


@pytest.mark.parametrize(
    ("kwargs", "error", "match"),
    [
        ({"label": ""}, ValueError, "label must be non-empty"),
        ({"label": 4}, TypeError, "label must be a string"),
        ({"label": "Task", "intent": "info"}, ValueError, "intent must be one of"),
        ({"label": "Task", "size": "xl"}, ValueError, "size must be one of"),
        ({"label": "Task", "attrs": []}, TypeError, "attrs must be a mapping"),
    ],
)
def test_invalid_server_inputs_fail_deterministically(kwargs, error, match):
    with pytest.raises(error, match=match):
        _render(CSpinner(**kwargs))


@pytest.mark.parametrize(
    "attribute",
    [
        "role",
        "tabindex",
        "contenteditable",
        "aria-hidden",
        "aria-label",
        "aria-valuenow",
        "aria-valuemin",
        "aria-valuemax",
        "aria-valuetext",
        "data-citry-ui-part",
        "data-intent",
        "data-size",
        "data-citry-morph",
        "data-cev-action",
        "data-cid",
    ],
)
def test_spinner_rejects_owned_and_runtime_attributes(attribute):
    with pytest.raises(ValueError, match="cannot"):
        _render(CSpinner(label="Task", attrs={attribute: "consumer"}))


@pytest.mark.parametrize(
    "attribute",
    [
        ":role",
        "v-bind:aria-label",
        ".tabindex",
        "v-bind",
        "v-if",
        "V-IF",
        "v-for",
        "v-html",
        "v-text",
        "v-model",
        "@click",
        "#default",
    ],
)
def test_spinner_rejects_vue_directives(attribute):
    with pytest.raises(ValueError, match=re.escape(f"CSpinner attrs cannot contain the Vue directive {attribute!r}")):
        _render(CSpinner(label="Task", attrs={attribute: "consumer"}))


def test_spinner_attrs_without_vue_syntax_stay_ordinary_attributes():
    html = _render(CSpinner(label="Task", attrs={"x-data": "task", "title": "Busy"}), static_fallback=True)
    assert 'x-data="task"' in html
    assert 'title="Busy"' in html


def test_choices_and_label_are_detrusted_before_rendering():
    with pytest.raises(ValueError, match="intent must be one of"):
        _render(CSpinner(label="Task", intent=Markup('primary" onfocus="evil')))
    html = _render(CSpinner(label=Markup('Aligning "Vega"')), static_fallback=True)
    assert 'aria-label="Aligning &#34;Vega&#34;"' in html


def test_css_exposes_spinner_and_environment_contract():
    css = read_component_source_css("cspinner")

    for variable in ("color", "track-color", "size", "thickness", "duration"):
        assert f"--_cui-spinner-{variable}: var(" in css
        assert f"--cui-spinner-{variable}" in css
    assert "@keyframes cui-spinner-rotate" in css
    assert "prefers-reduced-motion: reduce" in css
    assert "forced-colors: active" in css
    assert "@media print" in css
