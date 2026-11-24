"""
``actions.Dispatch`` refuses event names the page already listens for.

The server refuses them when it builds the action, and the browser runtime
refuses them again before it fires the event. The runtime's list is a copy
that the generator writes, so these tests also check the copy matches.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest
from scripts import generate_html_attribute_values as generator
from scripts.generate_html_attribute_values import (
    CLIENT_BEGIN,
    CLIENT_END,
    CLIENT_PATH,
    render_client_event_names,
)

from citry._html_attribute_values import DOM_EVENT_NAMES
from citry.ext.events import actions

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    "name",
    [
        "click",
        "submit",
        "input",
        "change",
        "keydown",
        "focus",
        # Fired at `document` and `window`, which a bubbling event reaches.
        "message",
        "hashchange",
        "domcontentloaded",
    ],
)
def test_dispatch_refuses_a_standard_dom_event_name(name: str) -> None:
    with pytest.raises(ValueError, match="is a standard DOM event name"):
        actions.Dispatch(name)


@pytest.mark.parametrize("name", ["Click", "SUBMIT", "keyDown", "DOMContentLoaded"])
def test_dispatch_refuses_a_standard_name_in_any_ascii_letter_case(name: str) -> None:
    with pytest.raises(ValueError, match="is a standard DOM event name"):
        actions.Dispatch(name)


@pytest.mark.parametrize(
    ("name", "prefix"),
    [
        ("citry:ready", "citry:"),
        ("Citry:ready", "citry:"),
        ("vue:mounted", "vue:"),
        ("vnode-mounted", "vnode-"),
        ("VNode-Updated", "vnode-"),
    ],
)
def test_dispatch_refuses_a_reserved_prefix_in_any_ascii_letter_case(name: str, prefix: str) -> None:
    with pytest.raises(ValueError, match=f"starts with '{prefix}'"):
        actions.Dispatch(name)


@pytest.mark.parametrize(
    "name",
    [
        "MyCard:submit",
        "order-saved",
        "saved",
        "update:modelValue",
        "onClick",
        # A browser matches event names by exact code units, so none of these
        # reaches a `click` or `keydown` listener.
        " click",
        "click ",
        # A Cyrillic es in place of the Latin c, and the Kelvin sign in place of K.
        chr(0x0441) + "lick",
        chr(0x212A) + "eydown",
    ],
)
def test_dispatch_accepts_a_custom_name(name: str) -> None:
    assert actions.Dispatch(name).name == name


def test_the_refusal_message_names_the_fix() -> None:
    with pytest.raises(ValueError, match=r"'click' is a standard DOM event name.*'MyCard:submit'"):
        actions.Dispatch("click")


def _client() -> str:
    return CLIENT_PATH.read_text(encoding="utf-8")


def test_the_browser_runtime_carries_the_same_event_names() -> None:
    client = _client()
    start = client.index(CLIENT_BEGIN)
    end = client.index(CLIENT_END) + len(CLIENT_END)
    # An exact match also catches a hand edit that keeps the same names.
    assert client[start:end] == render_client_event_names(DOM_EVENT_NAMES), (
        "Run `python scripts/generate_html_attribute_values.py --client-only`, then"
        " `pnpm --dir packages/js/citry-client run build`."
    )


def test_the_browser_runtime_carries_the_same_prefixes() -> None:
    match = re.search(r"const reservedEventPrefixes = \[([^\]]*)\];", _client())
    assert match is not None
    prefixes = tuple(re.findall(r'"([^"]*)"', match.group(1)))
    assert prefixes == actions.RESERVED_EVENT_PREFIXES


def test_the_shipped_runtime_holds_the_check() -> None:
    # The page loads the minified build, not client.js; a stale build would
    # ship without the browser half of the check.
    runtime = (CLIENT_PATH.parent / "runtime.js").read_text(encoding="utf-8")
    assert "refused to dispatch" in runtime
    assert '"domcontentloaded"' in runtime


def test_write_client_event_names_replaces_only_the_marked_lines(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = tmp_path / "client.js"
    client.write_text(f"before\n{CLIENT_BEGIN}  stale\n{CLIENT_END}after\n", encoding="utf-8")
    monkeypatch.setattr(generator, "CLIENT_PATH", client)
    generator.write_client_event_names(frozenset({"click", "abort"}))
    block = '  const standardEventNames = new Set([\n    "abort", "click",\n  ]);\n'
    assert client.read_text(encoding="utf-8") == f"before\n{CLIENT_BEGIN}{block}{CLIENT_END}after\n"


def test_write_client_event_names_stops_without_the_markers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client = tmp_path / "client.js"
    client.write_text("no markers here\n", encoding="utf-8")
    monkeypatch.setattr(generator, "ROOT", tmp_path)
    monkeypatch.setattr(generator, "CLIENT_PATH", client)
    with pytest.raises(SystemExit, match="lacks the DOM_EVENT_NAMES markers"):
        generator.write_client_event_names(frozenset({"click"}))
    assert client.read_text(encoding="utf-8") == "no markers here\n"
