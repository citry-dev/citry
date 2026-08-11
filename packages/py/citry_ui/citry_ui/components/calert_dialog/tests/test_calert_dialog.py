from __future__ import annotations

import re
from typing import get_type_hints

import pytest

import citry_ui
from citry import Citry, Component


def _render(source: str, data: dict[str, object] | None = None) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = source

        def template_data(self, kwargs, slots):
            return data or {}

    return str(Page())


_MINIMAL = """
  <c-CAlertDialog id="delete">
    <c-fill name="title">Delete project?</c-fill>
    <c-fill name="description">This cannot be undone.</c-fill>
    <c-fill name="cancel" data="{cancel_attrs, cancel_type}">
      <button c-type="cancel_type" c-bind="cancel_attrs">Keep project</button>
    </c-fill>
    <c-fill name="action" data="{action_attrs, action_type}">
      <button c-type="action_type" c-bind="action_attrs">Delete</button>
    </c-fill>
  </c-CAlertDialog>
"""


def test_server_anatomy_uses_exact_alertdialog_relationships_and_safe_buttons() -> None:
    html = _render(_MINIMAL)
    dialog = re.search(r'<dialog[^>]+data-citry-ui-part="alert-dialog"[^>]*>', html)
    assert dialog is not None
    root = dialog.group(0)
    assert 'id="delete"' in root
    assert 'role="alertdialog"' in root
    assert 'aria-modal="true"' in root
    assert 'aria-labelledby="delete-title"' in root
    assert 'aria-describedby="delete-description"' in root
    assert 'data-size="sm"' in root
    markup = html[html.find('<div class="cui-dialog-host') : html.find("<script")]
    assert 'id="delete-title"' in markup
    assert 'id="delete-description"' in markup
    assert markup.count('type="button"') == 2
    assert 'value="cancel"' in markup
    assert 'value="action"' in markup
    assert "autofocus" in markup
    assert 'data-citry-ui-part="close"' not in markup


def test_activator_and_supplemental_body_render_with_slot_mappings() -> None:
    html = _render(
        """
        <c-CAlertDialog>
          <c-fill name="activator" data="{activator_attrs, activator_type}">
            <button c-type="activator_type" c-bind="activator_attrs">Open prompt</button>
          </c-fill>
          <c-fill name="title">Leave?</c-fill>
          <c-fill name="description">Unsaved edits will be lost.</c-fill>
          <c-fill name="default"><strong>Three fields changed.</strong></c-fill>
          <c-fill name="cancel" data="{cancel_attrs}"><c-CButton c-attrs="cancel_attrs">Stay</c-CButton></c-fill>
          <c-fill name="action" data="{action_attrs}"><c-CButton c-attrs="action_attrs">Leave</c-CButton></c-fill>
        </c-CAlertDialog>
        """
    )
    assert 'aria-haspopup="dialog"' in html
    assert 'aria-expanded="false"' in html
    assert 'data-citry-ui-part="body"' in html
    assert "Three fields changed." in html
    assert html.count("data-citry-dialog-close") >= 2


@pytest.mark.parametrize("missing", ["title", "description", "cancel", "action"])
def test_every_decision_slot_is_required(missing: str) -> None:
    fills = {
        "title": '<c-fill name="title">Title</c-fill>',
        "description": '<c-fill name="description">Message</c-fill>',
        "cancel": '<c-fill name="cancel" data="{cancel_attrs}"><button c-bind="cancel_attrs">Cancel</button></c-fill>',
        "action": '<c-fill name="action" data="{action_attrs}"><button c-bind="action_attrs">Act</button></c-fill>',
    }
    source = (
        "<c-CAlertDialog>" + "".join(value for key, value in fills.items() if key != missing) + "</c-CAlertDialog>"
    )
    with pytest.raises(SyntaxError, match="requires"):
        _render(source)


@pytest.mark.parametrize(
    "attrs",
    [
        {"role": "dialog"},
        {"open": True},
        {"aria-describedby": "other"},
        {":aria-modal": "false"},
        {"x-if": "bad"},
        {"data-citry-private": "bad"},
    ],
)
def test_owned_attrs_are_rejected(attrs: dict[str, object]) -> None:
    source = _MINIMAL.replace('id="delete"', 'c-attrs="attrs"')
    with pytest.raises(ValueError, match="cannot"):
        _render(source, {"attrs": attrs})


def test_invalid_server_configuration_fails() -> None:
    with pytest.raises(ValueError, match="size"):
        _render(_MINIMAL.replace('id="delete"', 'size="full"'))
    with pytest.raises(TypeError, match="close_on_escape"):
        _render(_MINIMAL.replace('id="delete"', 'c-close_on_escape="1"'))


def test_public_types_resolve_and_component_is_registered() -> None:
    hints = get_type_hints(citry_ui.CAlertDialog.Kwargs)
    assert hints["size"] == citry_ui.CAlertDialogSize
    assert hints["scroll"] == citry_ui.CAlertDialogScroll
    assert citry_ui.CAlertDialog in citry_ui.COMPONENTS
