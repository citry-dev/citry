from __future__ import annotations

import re
from dataclasses import fields

import pytest
from markupsafe import Markup

import citry_ui
from citry import Citry, Component
from citry_ui import CProgress
from citry_ui.quality.asset_sources import read_component_source_css


def _render(progress: object, *, include_css: bool = False) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <main>{{ progress }}</main>{{ css }}
        """

        def template_data(self, kwargs, slots):
            return {
                "progress": progress,
                "css": app.get("css")() if include_css else "",
            }

    return str(Page())


def test_progress_schema_keeps_native_jobs_direct():
    assert [field.name for field in fields(CProgress.Kwargs)] == [
        "label",
        "value",
        "max",
        "value_text",
        "intent",
        "size",
        "shape",
        "class_",
        "style",
        "attrs",
    ]
    assert fields(CProgress.Slots) == ()


def test_indeterminate_progress_omits_value_and_uses_native_root():
    html = _render(CProgress(label="Contacting archive"))
    root = re.search(r'<progress[^>]+data-citry-ui-part="progress"[^>]*>', html)

    assert root is not None
    assert 'aria-label="Contacting archive"' in root.group(0)
    assert 'max="100.0"' in root.group(0)
    assert 'data-state="indeterminate"' in root.group(0)
    assert " value=" not in root.group(0)
    assert "Contacting archive</progress>" in html
    assert "role=" not in root.group(0)


def test_determinate_custom_range_value_text_and_root_styling():
    html = _render(
        CProgress(
            label="Scanning samples",
            value=6,
            max=10,
            value_text="6 of 10 samples",
            intent="success",
            size="lg",
            shape="pill",
            class_=["scan", {"active": True}],
            style={"--cui-progress-height": "18px"},
            attrs={"id": "scan-progress", "class": "from-attrs", "aria-describedby": "scan-help"},
        )
    )
    root = re.search(r'<progress[^>]+data-citry-ui-part="progress"[^>]*>', html)

    assert root is not None
    assert 'class="cui-progress from-attrs scan active"' in root.group(0)
    assert 'style="--cui-progress-height: 18px;"' in root.group(0)
    assert 'id="scan-progress"' in root.group(0)
    assert 'aria-describedby="scan-help"' in root.group(0)
    assert 'aria-valuetext="6 of 10 samples"' in root.group(0)
    assert 'value="6.0"' in root.group(0)
    assert 'max="10.0"' in root.group(0)
    assert 'data-state="determinate"' in root.group(0)
    assert 'data-intent="success"' in root.group(0)
    assert 'data-size="lg"' in root.group(0)
    assert 'data-shape="pill"' in root.group(0)
    assert "\u2068Scanning samples\u2069: \u20686\u2069 of \u206810\u2069</progress>" in html


@pytest.mark.parametrize(
    ("kwargs", "error", "match"),
    [
        ({"label": ""}, ValueError, "label must be non-empty"),
        ({"label": 4}, TypeError, "label must be a string"),
        ({"label": "Task", "max": 0}, ValueError, "max must be greater than zero"),
        ({"label": "Task", "max": True}, TypeError, "max must be a finite number"),
        ({"label": "Task", "max": float("inf")}, ValueError, "max must be finite"),
        ({"label": "Task", "value": -1}, ValueError, "value must be between"),
        ({"label": "Task", "value": 101}, ValueError, "value must be between"),
        ({"label": "Task", "value": True}, TypeError, "value must be a finite number"),
        ({"label": "Task", "value": float("nan")}, ValueError, "value must be finite"),
        ({"label": "Task", "value_text": ""}, ValueError, "value_text must be non-empty"),
        ({"label": "Task", "intent": "info"}, ValueError, "intent must be one of"),
        ({"label": "Task", "size": "xl"}, ValueError, "size must be one of"),
        ({"label": "Task", "shape": "circle"}, ValueError, "shape must be one of"),
        ({"label": "Task", "attrs": []}, TypeError, "attrs must be a mapping"),
    ],
)
def test_invalid_server_inputs_fail_deterministically(kwargs, error, match):
    with pytest.raises(error, match=match):
        _render(CProgress(**kwargs))


@pytest.mark.parametrize(
    "attribute",
    [
        "value",
        "MAX",
        "min",
        "role",
        "aria-label",
        "aria-valuenow",
        "aria-valuemin",
        "aria-valuemax",
        "aria-valuetext",
        "data-citry-ui-part",
        "data-state",
        "data-intent",
        "data-size",
        "data-shape",
        ":value",
        "x-bind:aria-label",
        "data-citry-morph",
        "data-cev-action",
        "data-cid",
        "x-bind",
        "x-if",
        "x-for",
        "x-teleport",
        "x-ignore",
        "x-html",
        "x-text",
        "x-model",
    ],
)
def test_progress_rejects_owned_runtime_and_structural_attributes(attribute):
    with pytest.raises(ValueError, match="cannot"):
        _render(CProgress(label="Task", attrs={attribute: "consumer"}))


def test_choices_and_labels_are_detrusted_before_rendering():
    with pytest.raises(ValueError, match="intent must be one of"):
        _render(CProgress(label="Task", intent=Markup('primary" onfocus="evil')))
    html = _render(CProgress(label=Markup('Archive "delta"'), value_text=Markup("2 < crates")))
    assert 'aria-label="Archive &#34;delta&#34;"' in html
    assert 'aria-valuetext="2 &lt; crates"' in html


def test_css_exposes_native_track_range_and_environment_contract():
    css = read_component_source_css("cprogress")

    for variable in ("track-color", "range-color", "height", "radius"):
        assert f"--_cui-progress-{variable}: var(" in css
        assert f"--cui-progress-{variable}" in css
    assert "::-webkit-progress-value" in css
    assert "::-moz-progress-bar" in css
    assert ":indeterminate" in css
    assert "prefers-reduced-motion: reduce" in css
    assert "forced-colors: active" in css
