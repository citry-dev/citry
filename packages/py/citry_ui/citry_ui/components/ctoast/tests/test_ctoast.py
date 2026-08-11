"""Server contract tests for CToastRegion."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import get_type_hints

import pytest

import citry_ui
from citry import Citry


def _app() -> Citry:
    app = Citry(autodiscover=False)
    app.set_mounted_prefix("/citry")
    app.register_library(citry_ui)
    return app


def _render(**kwargs) -> str:
    app = _app()
    return citry_ui.CToastRegion(**kwargs).render(citry=app).serialize(deps_strategy="fragment")


def test_toast_region_renders_semantic_queue_and_form_safe_controls() -> None:
    html = _render(
        id="notices",
        label="Application notifications",
        placement="block-start-start",
        limit=2,
        items=(
            citry_ui.CToastMessage(
                id="saved",
                title="Saved",
                description="Field note synchronized.",
                intent="success",
                action_label="Undo",
            ),
            citry_ui.CToastMessage(
                id="offline",
                title="Offline",
                priority="assertive",
                duration_ms=0,
            ),
            citry_ui.CToastMessage(id="queued", title="Queued"),
        ),
    )

    assert '<section class="cui-toast-region" id="notices"' in html
    assert 'role="region"' in html
    assert 'aria-label="Application notifications"' in html
    assert html.count('aria-live="polite"') == 1
    assert html.count('aria-live="assertive"') == 1
    assert html.count('data-citry-ui-part="toast"') == 2
    assert 'data-citry-toast-id="saved"' in html
    assert 'data-citry-toast-id="queued"' not in html
    assert 'aria-describedby="notices-description-0"' in html
    assert html.count('type="button"') == 3


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("label", " "),
        ("placement", "center"),
        ("limit", 0),
        ("limit", 11),
        ("duration_ms", 999),
        ("duration_ms", True),
        ("pause_on_hover", 1),
        ("items", "not a sequence"),
        ("id", "bad id"),
    ],
)
def test_toast_region_rejects_invalid_server_inputs(name: str, value: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        _render(**{name: value})


@pytest.mark.parametrize(
    "message",
    [
        citry_ui.CToastMessage(id="", title="Title"),
        citry_ui.CToastMessage(id="bad id", title="Title"),
        citry_ui.CToastMessage(id="bad\0id", title="Title"),
        citry_ui.CToastMessage(id="item", title=""),
        citry_ui.CToastMessage(id="item", title="Title", intent="urgent"),
        citry_ui.CToastMessage(id="item", title="Title", priority="medium"),
        citry_ui.CToastMessage(id="item", title="Title", duration_ms=12),
        citry_ui.CToastMessage(id="item", title="Title", dismissible=1),
    ],
)
def test_toast_region_rejects_invalid_message_records(message: citry_ui.CToastMessage) -> None:
    with pytest.raises((TypeError, ValueError)):
        _render(items=(message,))


def test_toast_region_rejects_duplicate_ids_after_canonicalization() -> None:
    with pytest.raises(ValueError, match="unique canonical ids"):
        _render(
            items=(
                citry_ui.CToastMessage(id="same", title="First"),
                citry_ui.CToastMessage(id="same", title="Second"),
            )
        )


@pytest.mark.parametrize(
    "attribute",
    [
        "id",
        "role",
        "tabindex",
        "aria-live",
        "aria-hidden",
        "inert",
        "data-placement",
        "x-html",
        "x-ignore",
        ":role",
        "x-bind:aria-label",
    ],
)
def test_toast_region_rejects_owned_static_and_dynamic_attrs(attribute: str) -> None:
    with pytest.raises(ValueError, match="CToastRegion attrs"):
        _render(attrs={attribute: "consumer"})


def test_toast_region_merges_unrelated_attrs_class_and_style() -> None:
    html = _render(
        class_=["brand-notices", {"ready": True}],
        style={"--cui-toast-width": "28rem"},
        attrs={"data-workflow": "sync", "@click": "clicked = true"},
    )

    assert 'class="cui-toast-region brand-notices ready"' in html
    assert "--cui-toast-width: 28rem" in html
    assert 'data-workflow="sync"' in html
    assert '@click="clicked = true"' in html


def test_toast_strings_are_plain_canonical_and_escaped() -> None:
    html = _render(
        items=(
            citry_ui.CToastMessage(
                id="safe",
                title='<img src=x onerror="evil">\r\nSaved',
                description="A\rB",
                action_label="<strong>Undo</strong>",
            ),
        )
    )

    assert "&lt;img src=x onerror=&#34;evil&#34;&gt;\nSaved" in html
    assert "A\nB" in html
    assert "&lt;strong&gt;Undo&lt;/strong&gt;" in html
    assert "<img" not in html


class _OneShotMessages(Sequence[citry_ui.CToastMessage]):
    def __init__(self) -> None:
        self.iterations = 0
        self._items = (citry_ui.CToastMessage(id="once", title="Read once"),)

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, index):
        return self._items[index]

    def __iter__(self) -> Iterator[citry_ui.CToastMessage]:
        self.iterations += 1
        if self.iterations > 1:
            raise AssertionError("items was consumed more than once")
        return iter(self._items)


def test_toast_region_uses_one_message_snapshot_for_html_and_client_data() -> None:
    messages = _OneShotMessages()
    html = _render(items=messages)

    assert messages.iterations == 1
    assert 'data-citry-toast-id="once"' in html


def test_toast_public_types_are_runtime_introspectable() -> None:
    hints = get_type_hints(citry_ui.CToastRegion.Kwargs)
    assert hints["placement"] == citry_ui.CToastPlacement
    assert hints["items"] == Sequence[citry_ui.CToastMessage]
    assert citry_ui.CToastMessage(id="saved", title="Saved").dismissible is True
