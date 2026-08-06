from __future__ import annotations

import re

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CButton, CForm


def _render(value: object) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = "{{ value }}"

        def template_data(self, kwargs, slots):
            return {"value": value}

    return str(Page())


def test_form_renders_direct_native_inputs_and_private_first_legend() -> None:
    html = _render(
        CForm(
            id="observation-form",
            action="/observations",
            method="post",
            enctype="multipart/form-data",
            target="results",
            autocomplete="off",
            novalidate=True,
            class_="observation-form",
            style={"--cui-form-gap": "0.5rem"},
            attrs={"data-workflow": "observation"},
            slots={"default": "Fields"},
        )
    )
    form = re.search(r'<form[^>]+id="observation-form"[^>]*>', html)

    assert form is not None
    assert 'action="/observations"' in form.group(0)
    assert 'method="post"' in form.group(0)
    assert 'enctype="multipart/form-data"' in form.group(0)
    assert 'target="results"' in form.group(0)
    assert 'autocomplete="off"' in form.group(0)
    assert " novalidate" in form.group(0)
    assert "observation-form" in form.group(0)
    assert "--cui-form-gap: 0.5rem;" in form.group(0)
    assert 'data-workflow="observation"' in form.group(0)
    fieldset_start = html.index('<fieldset class="cui-form__fieldset"')
    legend_start = html.index('<legend hidden aria-hidden="true"></legend>', fieldset_start)
    fields_start = html.index("Fields", legend_start)
    assert fieldset_start < legend_start < fields_start


def test_form_preserves_explicit_empty_action_and_target() -> None:
    html = _render(CForm(action="", target="", slots={"default": "Fields"}))
    form = re.search(r"<form[^>]*>", html)

    assert form is not None
    assert 'action=""' in form.group(0)
    assert 'target=""' in form.group(0)


@pytest.mark.parametrize(
    ("kwargs", "exception", "message"),
    [
        ({"id": ""}, ValueError, "CForm id"),
        ({"action": 1}, TypeError, "CForm action"),
        ({"method": "put"}, ValueError, "CForm method"),
        ({"enctype": "application/json"}, ValueError, "CForm enctype"),
        ({"target": 1}, TypeError, "CForm target"),
        ({"autocomplete": "email"}, ValueError, "CForm autocomplete"),
        ({"disabled": 1}, TypeError, "CForm disabled"),
        ({"readonly": 1}, TypeError, "CForm readonly"),
        ({"submitting": 1}, TypeError, "CForm submitting"),
        ({"novalidate": 1}, TypeError, "CForm novalidate"),
        ({"attrs": {"action": "/other"}}, ValueError, "owned attribute"),
        ({"attrs": {"METHOD": "post"}}, ValueError, "owned attribute"),
        ({"attrs": {"data-submitting": "false"}}, ValueError, "owned attribute"),
    ],
)
def test_form_rejects_invalid_or_ambiguous_server_inputs(kwargs, exception, message) -> None:
    with pytest.raises(exception, match=message):
        _render(CForm(**kwargs, slots={"default": "Fields"}))


def test_form_cannot_be_nested() -> None:
    inner = CForm(slots={"default": "Inner"})
    outer = CForm(slots={"default": inner})

    with pytest.raises(ValueError, match="cannot be nested"):
        _render(outer)


def test_disabled_form_is_reflected_by_descendant_button_without_javascript() -> None:
    html = _render(
        CForm(
            disabled=True,
            slots={
                "default": CButton(
                    type="submit",
                    slots={"default": "Submit observation"},
                )
            },
        )
    )
    button = re.search(r'<button class="cui-button"[^>]*>', html)

    assert button is not None
    assert " disabled" in button.group(0)
    assert " data-disabled" in button.group(0)
    assert 'aria-disabled="true"' in button.group(0)

    link_html = _render(
        CForm(
            disabled=True,
            slots={"default": CButton(href="/help", slots={"default": "Help"})},
        )
    )
    link = re.search(r'<a class="cui-button"[^>]*>', link_html)

    assert link is not None
    assert " href=" not in link.group(0)
    assert 'tabindex="-1"' in link.group(0)
    assert " data-disabled" in link.group(0)
    assert 'aria-disabled="true"' in link.group(0)
