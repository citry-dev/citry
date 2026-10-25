"""
Level B2 of the native render path: Rust writes the JSON of ordinary components' leaf data.

A leaf program is a component template compiled into one reusable program
with no component or slot nodes; its leaf data is the values that program
sends to the browser. On the precompile path, assembly asks Rust
(``native_leaf_json.take``) to write each leaf value's JSON, stores a
placeholder under each key, and the manifest encoder writes Rust's JSON
there. Anything Rust cannot write exactly makes it return a reason, and
Python converts that leaf as it does without Rust.

This file checks:

- page cases on both paths in this process (``render_both`` in
  ``tests/_render_paths.py``), comparing the bytes or the error, with the
  leaves Rust wrote and the reason of each leaf it left to Python, so a
  silent decline cannot pass. Leaf programs turn their data into text,
  ints and bools first, so the declines a page reaches are a lone
  surrogate in text and an int past Python's digit limit in an attribute;
- that on a 140-row board shaped like the benchmark page, Rust writes all
  four ordinary leaves;
- Rust's JSON against Python's for hand-written values and a seeded random
  set, written through the manifest encoder exactly as a page writes them;
- each decline reason and each encoder refusal, by calling Rust directly;
- the placeholder, the garbage collector and reference counts.
"""

from __future__ import annotations

import copy
import gc
import json
import math
import pickle
import random
import struct
import sys
from decimal import Decimal
from enum import IntEnum
from typing import TYPE_CHECKING, Any, cast

import pytest

from citry import Citry, Component, Const
from citry._vue import events, native_leaf_json, native_render
from citry._vue.json_data import _json_plain
from citry._vue.native_leaf_json import PLACEHOLDER
from citry._vue.serialization import _script_json
from citry.extension import Extension
from citry.secret import Secret
from citry.util.html import Markup

from ._render_paths import NONCE, render_both

if TYPE_CHECKING:
    from types import FrameType

pytestmark = pytest.mark.skipif(not native_render.SUPPORTED, reason="this interpreter takes the Python render path")

# The outputs each page case serializes. Static HTML has no manifest, so it
# never reaches the leaf JSON writer; it is here to show that.
OUTPUTS: dict[str, dict[str, Any]] = {
    "hydrated": {},
    "ssr_false": {"ssr": False},
    "static": {"deps_strategy": "simple"},
    "fragment": {"deps_strategy": "fragment"},
    "hydration_declined": {"deps_position": "append"},
    "csp": {"security_csp": "strict", "csp_nonce": NONCE},
}

# Page text that needs most kinds of JSON escape: quotes, a backslash, `<`
# and `</script>`, control characters, non-ASCII, an astral character and
# U+2028. DEL is left to the direct checks below: a hydrated page with DEL
# in its text fails the Vue render parity phase's parse check on both paths,
# which is outside this level.
AWKWARD_TEXT = 'Say "hi" \\ <b> </script> tab\there\nline caf\u00e9 \U0001f600 sep\u2028end'


INFO_TEMPLATE = """
    <section
      c-data-title="title"
      c-data-count="count"
      c-hidden="count == 0"
    >
      <h2>{{ title }}</h2>
      <p c-for="item in items">{{ item }}</p>
    </section>
"""


def _engine(**options: Any) -> Citry:
    engine = Citry(autodiscover=False, secret="native-render-test-secret", **options)  # noqa: S106
    # The hydrated document links the page's scripts under the engine's URL prefix.
    engine.set_mounted_prefix("/citry")
    return engine


def _info_class(engine: Citry, *, body: str | None = None, server_data: Any = None) -> type[Component]:
    """An ordinary component whose template compiles into one leaf program."""
    # A class body cannot read a function argument it also assigns, so the
    # template is chosen here.
    chosen_template = body or INFO_TEMPLATE

    class Info(Component):
        citry = engine

        class Kwargs:
            title: object
            count: object

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"title": kwargs.title, "count": kwargs.count, "items": ["one", "<two>", AWKWARD_TEXT]}

        if server_data is not None:

            def js_data(self, kwargs: Any, slots: Any) -> Any:
                return server_data(kwargs)

        template = chosen_template
        js = """
            $component({});
        """

    return Info


def _serialize_all(page: Any, outputs: dict[str, dict[str, Any]] = OUTPUTS) -> dict[str, object]:
    """Serialize ``page`` once per output; an output that raises records its error."""
    result: dict[str, object] = {}
    for label, options in outputs.items():
        try:
            result[label] = page().render().serialize(**options)
        except Exception as error:  # noqa: BLE001 - compared between the paths
            result[label] = f"{type(error).__name__}: {error}"
    return result


def _page_with_infos(
    titles: list[object],
    *,
    engine: Citry | None = None,
    info: type[Component] | None = None,
    extra_body: str = "",
    page_data: dict[str, Any] | None = None,
) -> type[Component]:
    """
    A page that calls ``Info`` once per title, each title read from the page's data.

    ``info``, when given, is a component class the caller already registered
    on ``engine``; without one, the default ``Info`` is registered.
    """
    owner = engine if engine is not None else _engine()
    if info is None:
        _info_class(owner)
    calls = "".join(f'<c-Info c-title="titles[{index}]" c-count="{index}" />' for index in range(len(titles)))

    class Page(Component):
        citry = owner

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"titles": titles, **(page_data or {})}

        template = f"""
            <html><head></head><body><main>{calls}{extra_body}</main></body></html>
        """

    return Page


def _pages(result: object) -> dict[str, str]:
    """Return the outputs of a run that must succeed, checking each is a page, not an error."""
    pages = cast("dict[str, str]", result)
    for label, page in pages.items():
        assert page.lstrip().startswith("<"), (label, page[:200])
    return pages


# Every output with a manifest assembles once, so each writes every leaf.
_MANIFEST_OUTPUTS = len(OUTPUTS) - 1


def test_plain_text_attributes_and_a_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    page = _page_with_infos([AWKWARD_TEXT])
    rust, _python = render_both(
        lambda: _serialize_all(page),
        monkeypatch,
        leaves=(_MANIFEST_OUTPUTS, ()),
    )
    _pages(rust.result)


def test_calls_that_share_one_definition(monkeypatch: pytest.MonkeyPatch) -> None:
    # The first call attaches its leaf where the definition is built, the
    # other two where they reuse it, so both places that ask Rust run.
    page = _page_with_infos(["a", AWKWARD_TEXT, "c"])
    rust, _python = render_both(
        lambda: _serialize_all(page),
        monkeypatch,
        leaves=(3 * _MANIFEST_OUTPUTS, ()),
    )
    _pages(rust.result)


def test_a_lone_surrogate_in_text_is_left_to_python(monkeypatch: pytest.MonkeyPatch) -> None:
    # The one decline a page reaches: text with no UTF-8 form. Rust writes
    # the other two leaves, and Python converts the second, in one manifest.
    # Every output except static asks Rust for all three leaves; all but
    # ssr_false then fail on the surrogate when they write the HTML, the
    # same way on both paths, so two outputs are enough.
    outputs = {"ssr_false": {"ssr": False}, "hydrated": {}}
    page = _page_with_infos(["a", "lone \ud800 surrogate", "c"])
    rust, _python = render_both(
        lambda: _serialize_all(page, outputs),
        monkeypatch,
    )
    assert rust.leaves_written == 2 * len(outputs)
    assert rust.leaf_declines == ("not_utf8",) * len(outputs)
    assert "\\ud800" in cast("dict[str, str]", rust.result)["ssr_false"]


def test_an_int_past_the_digit_limit_in_an_attribute_is_left_to_python(monkeypatch: pytest.MonkeyPatch) -> None:
    # The other decline a page reaches: an attribute keeps an int that has no
    # text under Python's digit limit, so Rust declines it (big_int) and
    # Python's JSON writer raises its own error, as without Rust.
    engine = _engine()
    info = _info_class(engine, body='<p c-data-n="title">x</p>')
    page = _page_with_infos([10**5000], engine=engine, info=info)
    rust, _python = render_both(
        lambda: _serialize_all(page, {"ssr_false": {"ssr": False}}),
        monkeypatch,
        leaves=(0, ("big_int",)),
    )
    assert "Exceeds the limit" in cast("dict[str, str]", rust.result)["ssr_false"]


def _row_page(titles: list[object]) -> Any:
    """A page that places one ``simple = "vue"`` row per title in a loop."""
    engine = _engine()

    class Row(Component):
        citry = engine
        simple = "vue"

        class Kwargs:
            row: dict

        template = """
            <li c-data-key="row['key']">{{ row['title'] }}</li>
        """
        js = """
            $component({data(){return {open: true};}});
        """

    rows = [{"key": f"k{index}", "title": title} for index, title in enumerate(titles)]
    return _page_with_infos(
        [],
        engine=engine,
        info=Row,
        extra_body="""<ul><c-Row c-for="row in rows" #c-key="row['key']" c-row="row" /></ul>""",
        page_data={"rows": rows},
    )


def test_rust_writes_the_leaf_of_a_row_it_did_not_read(monkeypatch: pytest.MonkeyPatch) -> None:
    # An int outside 64 bits makes Rust decline the row itself (level A), so
    # the row records a Python leaf, whose text Rust then writes (level B2).
    page = _row_page([2**64 + index for index in range(3)])
    rust, _python = render_both(
        lambda: _serialize_all(page, {"hydrated": {}}),
        monkeypatch,
        rows_read=0,
        leaves=(3, ()),
    )
    _pages(rust.result)


def test_leaf_json_made_before_the_flag_changes_is_still_written(monkeypatch: pytest.MonkeyPatch) -> None:
    # The manifest writer follows the _LeafJson that assembly made, not the
    # flag, so switching the flag off after assembly changes nothing.
    page = _page_with_infos(["a", AWKWARD_TEXT])
    assemble = events.assemble_typed_render

    def assemble_then_switch_off(*args: Any, **kwargs: Any) -> Any:
        assembly = assemble(*args, **kwargs)
        native_render.ACTIVE = False
        return assembly

    def switched() -> object:
        monkeypatch.setattr(events, "assemble_typed_render", assemble_then_switch_off)
        try:
            return _serialize_all(page, {"hydrated": {}})
        finally:
            monkeypatch.setattr(events, "assemble_typed_render", assemble)

    rust, python = render_both(switched, monkeypatch, leaves=(2, ()))
    assert _pages(rust.result) == _pages(python.result)


def test_a_leaf_beside_a_run_of_rust_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = _engine()

    class Row(Component):
        citry = engine
        simple = "vue"

        class Kwargs:
            row: dict

        template = """
            <li c-data-key="row['key']">{{ row['title'] }}</li>
        """
        js = """
            $component({data(){return {open: true};}});
        """

    rows = [{"key": f"k{index}", "title": f"Row {index} <x>"} for index in range(6)]
    page = _page_with_infos(
        ["beside"],
        engine=engine,
        extra_body="""<ul><c-Row c-for="row in rows" #c-key="row['key']" c-row="row" /></ul>""",
        page_data={"rows": rows},
    )
    rust, _python = render_both(
        lambda: _serialize_all(page, {"hydrated": {}, "ssr_false": {"ssr": False}}),
        monkeypatch,
        rows_read=12,
        leaves=(2, ()),
    )
    _pages(rust.result)


def test_a_leaf_with_js_data(monkeypatch: pytest.MonkeyPatch) -> None:
    # serverData is not empty, so the encoder writes it through Python.
    engine = _engine()
    info = _info_class(
        engine, server_data=lambda kwargs: {"title": kwargs.title, "nested": {"z": [1, 2.5], "a": None}}
    )
    page = _page_with_infos(["a", "b"], engine=engine, info=info)
    rust, _python = render_both(
        lambda: _serialize_all(page),
        monkeypatch,
        leaves=(2 * _MANIFEST_OUTPUTS, ()),
    )
    _pages(rust.result)


def test_a_secret_in_js_data_keeps_pythons_refusal(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = _engine()
    info = _info_class(engine, server_data=lambda _kwargs: {"token": Secret("hidden")})
    page = _page_with_infos(["a"], engine=engine, info=info)
    rust, _python = render_both(
        lambda: _serialize_all(page),
        monkeypatch,
        leaves=(0, ()),
    )
    assert 'Info.js_data()["token"] holds a citry.Secret' in str(cast("dict[str, str]", rust.result)["hydrated"])


@pytest.mark.parametrize(
    "template",
    [
        "<p>{{ title }}</p>",
        '<p c-data-title="title">x</p>',
        "<p c-bind=\"{'data-title': title}\">x</p>",
    ],
    ids=["text", "attribute", "spread"],
)
def test_a_secret_in_the_leaf_gets_the_same_result(monkeypatch: pytest.MonkeyPatch, template: str) -> None:
    # The leaf program writes a Secret as its masked text before assembly
    # sees the data, so Rust writes text and never meets the Secret itself.
    engine = _engine()
    info = _info_class(engine, body=template)
    page = _page_with_infos([Secret("hidden")], engine=engine, info=info)
    rust, _python = render_both(lambda: _serialize_all(page), monkeypatch, leaves=(_MANIFEST_OUTPUTS, ()))
    assert "hidden" not in "".join(_pages(rust.result).values())


def test_a_markup_value_keeps_the_leaf_path_out(monkeypatch: pytest.MonkeyPatch) -> None:
    # Trusted HTML sends the occurrence down another path, so B2 never sees it.
    engine = _engine()
    info = _info_class(engine, body="<p>{{ title }}</p>")
    page = _page_with_infos([Markup("<b>bold</b>")], engine=engine, info=info)
    rust, _python = render_both(
        lambda: _serialize_all(page),
        monkeypatch,
        leaves=(0, ()),
    )
    _pages(rust.result)


class _NoInput:
    """An Events handler input with one optional field."""

    note: str = ""


def test_an_events_component_leaf(monkeypatch: pytest.MonkeyPatch) -> None:
    # The Events extension adds eventContext to the item, which the encoder
    # writes through Python beside Rust's JSON.
    engine = _engine()

    class Counter(Component):
        citry = engine

        class Kwargs:
            count: int

        class State(Kwargs):
            pass

        class Events:
            def bump(self, data: _NoInput, state: Any) -> Any:
                return Counter(count=state.count + 1)  # type: ignore[call-arg]

        template = """
            <form @c-submit.prevent="bump"><p>{{ count }}</p></form>
        """

    class Page(Component):
        citry = engine

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"count": 3}

        template = """
            <html><head></head><body><c-Counter c-count="count" /></body></html>
        """

    rust, _python = render_both(
        lambda: _serialize_all(Page, {"hydrated": {}, "ssr_false": {"ssr": False}}),
        monkeypatch,
        leaves=(2, ()),
    )
    assert '"eventContext":' in _pages(rust.result)["hydrated"]


def test_development_mode_writes_leaves_in_rust(monkeypatch: pytest.MonkeyPatch) -> None:
    # Development mode needs every row's HTML, but leaf JSON changes no HTML.
    engine = _engine(mode="development")
    page = _page_with_infos(["a"], engine=engine)
    rust, _python = render_both(
        lambda: _serialize_all(page, {"hydrated": {}}),
        monkeypatch,
        leaves=(1, ()),
    )
    _pages(rust.result)


class _BrowserHook(Extension):
    """An extension with a browser hook, which keeps the page off the precompile path."""

    name = "native_leaf_json_browser_hook"

    def prepare_browser_render(self, ctx: Any) -> None:
        return None


def test_a_browser_hook_keeps_leaves_in_python(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = _engine(extensions=[_BrowserHook])
    page = _page_with_infos(["a"], engine=engine)
    rust, _python = render_both(
        lambda: _serialize_all(page, {"hydrated": {}}),
        monkeypatch,
        leaves=(0, ()),
    )
    _pages(rust.result)


# ---------------------------------------------------------------------------
# The board
# ---------------------------------------------------------------------------


def _build_board(row_count: int, phase_size: int) -> Any:
    """
    A page shaped like the benchmark board.

    ``ProjectInfo`` and three ``NotePanel`` tabs are ordinary components whose
    templates are leaf programs, holding lists that grow with the row count;
    the phases place ``simple = "vue"`` rows, which Rust reads.
    """
    engine = _engine()
    rng = random.Random(11)  # noqa: S311 - reproducible test data

    class Output(Component):
        citry = engine
        simple = "vue"

        class Kwargs:
            row: dict

        template = """
            <article c-data-row-id="row['id']">{{ row['title'] }}</article>
        """
        js = """
            $component({data(){return {open: true};}});
        """

    class Phase(Component):
        citry = engine

        class Kwargs:
            phase: dict

        template = """
            <section c-data-phase-id="phase['id']">
              <c-Output
                c-for="row in phase['rows']"
                #c-key="row['id']"
                c-row="row"
              />
            </section>
        """

    class ProjectInfo(Component):
        citry = engine

        class Kwargs:
            state: dict

        template = """
            <section id="project-info">
              <td>{{ state['project']['organization'] }}</td>
              <c-if cond="state['tags']">
                <span c-for="tag in state['tags']">{{ tag }}</span>
              </c-if>
              <c-else>
                <p>No tags</p>
              </c-else>
              <article
                c-for="role in state['roles']"
                c-data-role-id="role['id']"
              >
                <span>{{ role['name'] }}</span>
              </article>
            </section>
        """

    class NotePanel(Component):
        citry = engine

        class Kwargs:
            tab: dict

        def js_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"tab_id": kwargs.tab["id"]}

        template = """
            <section c-id="tab['id']">
              <h2>{{ tab['title'] }}</h2>
              <article
                c-for="note in tab['notes']"
                c-data-note-id="note['id']"
              >
                <p>{{ note['text'] }}</p>
                <span c-for="comment in note['comments']">{{ comment }}</span>
              </article>
            </section>
        """

    rows = [{"id": f"output-{index}", "title": f"Output {index} <caf\u00e9>"} for index in range(row_count)]
    state = {
        "project": {"organization": "Acme & Co"},
        "tags": [f"tag-{index}" for index in range(row_count // 20)],
        "roles": [{"id": f"role-{index}", "name": f"Role {index}"} for index in range(row_count // 10)],
        "note_tabs": [
            {
                "id": f"notes-{tab}",
                "title": f"Notes {tab}",
                "notes": [
                    {
                        "id": f"n{tab}-{index}",
                        "text": f"Note {index} \u00b7 {rng.random():.3f}",
                        "comments": [f"c{n}" for n in range(rng.randrange(3))],
                    }
                    for index in range(row_count // 10)
                ],
            }
            for tab in (1, 2, 3)
        ],
        "phases": [
            {"id": f"phase-{start}", "rows": rows[start : start + phase_size]}
            for start in range(0, row_count, phase_size)
        ],
    }

    class Board(Component):
        citry = engine

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"state": state}

        template = """
            <html><head></head><body><main>
              <c-ProjectInfo c-state="state" />
              <c-NotePanel
                c-for="tab in state['note_tabs']"
                #c-key="tab['id']"
                c-tab="tab"
              />
              <c-Phase
                c-for="phase in state['phases']"
                #c-key="phase['id']"
                c-phase="phase"
              />
            </main></body></html>
        """

    return Board


def test_rust_writes_every_ordinary_leaf_of_the_board(monkeypatch: pytest.MonkeyPatch) -> None:
    # The board at 140 rows in five phases of 28, like the benchmark board:
    # ProjectInfo and the three note tabs are its four ordinary leaves.
    board = _build_board(140, 28)
    rust, _python = render_both(
        lambda: board().render().serialize(),
        monkeypatch,
        rows_read=140,
        rows_rebuilt=0,
        leaves=(4, ()),
    )
    assert cast("str", rust.result).lstrip().startswith("<")


# ---------------------------------------------------------------------------
# Rust's JSON against Python's
# ---------------------------------------------------------------------------

_native = cast("Any", native_render.native)
_ID = "citryOccurrenceLeaf"


def _item(prepared: object, **extra: object) -> dict[str, object]:
    """An ordinary occurrence's manifest item, as the manifest builder makes it."""
    return {
        "definitionId": "definition",
        "id": _ID,
        "parentId": "citryOccurrenceParent",
        "placementKey": "citryPlacementKey",
        "preparedData": prepared,
        "renderId": "c1",
        "serverData": {},
        "typeKey": "Info_abc123",
        **extra,
    }


def _both(values: dict[str, object], **extra: object) -> tuple[str, str]:
    """
    Write one leaf's item through Rust and through Python.

    Rust's side is what a page gets: the ``_LeafJson``, a placeholder under each
    key, and the manifest encoder. Python's side is what the page gets
    without Rust: ``_json_plain`` of each value, then ``_script_json``.
    """
    leaf_json = _native._leaf_values_json(values, PLACEHOLDER)
    assert type(leaf_json) is not str, leaf_json
    assert len(leaf_json) == len(values)
    placeholders = {"calls": {}, **dict.fromkeys(values, PLACEHOLDER)}
    rust = _native._encode_occurrences([_item(placeholders, **extra)], {_ID: leaf_json}, _script_json)
    copied = {"calls": {}, **{key: _json_plain(value) for key, value in values.items()}}
    python = "[" + _script_json(_item(copied, **extra)) + "]"
    return rust, python


_SHARED = [1, "two"]

HAND_WRITTEN: list[object] = [
    None,
    True,
    False,
    0,
    -1,
    2**63 - 1,
    -(2**63),
    2**53 + 1,
    0.0,
    -0.0,
    0.1,
    0.30000000000000004,
    1e16,
    1e22,
    1e-7,
    5e-324,
    1.7976931348623157e308,
    123456789012345680.0,
    2.5,
    "",
    AWKWARD_TEXT + " \x7f",
    "".join(chr(code) for code in range(0x20)),
    '/ & > < = " \\',
    "\u2028\u2029\ufeff\uffff\U00010000\U0010ffff",
    [],
    {},
    (),
    (1, (2, ("three",))),
    [_SHARED, _SHARED, {"same": _SHARED}],
    # Keys whose order differs between UTF-16 and code points: Python
    # sorts by code point, so U+FFFF comes before U+10000.
    {"\U00010000": 1, "\uffff": 2, "a": 3, "B": 4, "": 5, "\u00e9": 6, "<k>": 7},
    {"z": {"y": [{"x": None}], "a": [True, 1.5, "s"]}, "a": []},
]


@pytest.mark.parametrize("value", HAND_WRITTEN, ids=range(len(HAND_WRITTEN)))
def test_rust_writes_each_hand_written_value_as_python_does(value: object) -> None:
    rust, python = _both({"citryValue0": value})
    assert rust == python


def test_rust_writes_nesting_200_deep_as_python_does() -> None:
    value: object = "bottom"
    for _ in range(200):
        value = [value]
    rust, python = _both({"citryDeep": value})
    assert rust == python


def _random_text(rng: random.Random) -> str:
    """Text drawn from ASCII, the rest of the BMP and astral planes, without surrogates."""
    characters = []
    for _ in range(rng.randrange(8)):
        pick = rng.random()
        if pick < 0.5:
            code = rng.randrange(0x80)
        elif pick < 0.8:
            code = rng.choice([rng.randrange(0x80, 0xD800), rng.randrange(0xE000, 0x10000)])
        else:
            code = rng.randrange(0x10000, 0x110000)
        characters.append(chr(code))
    return "".join(characters)


def _random_float(rng: random.Random) -> float:
    """A float from random bits, so every exponent and odd digit string appears."""
    while True:
        number = cast("float", struct.unpack("<d", rng.getrandbits(64).to_bytes(8, "little"))[0])
        if math.isfinite(number):
            return number


def _random_value(rng: random.Random, depth: int = 0) -> object:
    kind = rng.randrange(9 if depth < 4 else 5)
    if kind == 0:
        return rng.choice([None, True, False])
    if kind == 1:
        return rng.choice([rng.randrange(-1000, 1000), rng.randrange(-(2**63), 2**63)])
    if kind == 2:
        return rng.choice([_random_float(rng), rng.uniform(-1e6, 1e6), float(rng.randrange(-100, 100))])
    if kind in (3, 4):
        return _random_text(rng)
    if kind in (5, 6):
        items = [_random_value(rng, depth + 1) for _ in range(rng.randrange(4))]
        return items if kind == 5 else tuple(items)
    return {_random_text(rng): _random_value(rng, depth + 1) for _ in range(rng.randrange(5))}


def test_rust_writes_random_values_as_python_does() -> None:
    rng = random.Random(20261023)  # noqa: S311 - reproducible test data
    for _ in range(300):
        values = {f"citryValue{index}": _random_value(rng) for index in range(rng.randrange(1, 4))}
        rust, python = _both(values)
        assert rust == python, values


def test_the_item_keeps_every_other_entry_as_python_writes_it() -> None:
    # An Events item carries eventContext, and a field may be a str subclass
    # or hold a lone surrogate; the encoder writes each through Python.
    class Text(str):
        __slots__ = ()

    rust, python = _both(
        {"citryText0": "x"},
        eventContext={"stateToken": "t<", "publicState": {"b": 1, "a": [2.5]}},
        renderId=Text("c9"),
        typeKey="T\ud800",
        serverData={"tab": "one"},
        parentId=None,
    )
    assert rust == python


# ---------------------------------------------------------------------------
# Declines and refusals, called directly (most no page reaches)
# ---------------------------------------------------------------------------


class _Text(str):
    __slots__ = ()


class _Dict(dict):  # type: ignore[type-arg]
    pass


class _List(list):  # type: ignore[type-arg]
    pass


class _Float(float):
    pass


class _Level(IntEnum):
    ONE = 1


def _cyclic_list() -> list[object]:
    value: list[object] = [1]
    value.append(value)
    return value


def _cyclic_dict() -> dict[str, object]:
    value: dict[str, object] = {"a": 1}
    value["self"] = value
    return value


def _too_deep() -> object:
    value: object = 1
    for _ in range(201):
        value = [value]
    return value


DECLINES: list[tuple[str, object, str]] = [
    ("str_subclass", _Text("a"), "not_plain"),
    ("dict_subclass", _Dict(a=1), "not_plain"),
    ("list_subclass", _List([1]), "not_plain"),
    ("float_subclass", _Float(1.5), "not_plain"),
    ("int_enum", _Level.ONE, "not_plain"),
    ("set", {1}, "not_plain"),
    ("bytes", b"x", "not_plain"),
    ("decimal", Decimal("1.5"), "not_plain"),
    ("markup", Markup("<b>x</b>"), "not_plain"),
    ("secret", Secret("hidden"), "not_plain"),
    ("const", Const("x"), "not_plain"),
    ("int_key", {1: "x"}, "not_plain"),
    ("str_subclass_key", {_Text("k"): "x"}, "not_plain"),
    ("nested_object", [1, {"a": object()}], "not_plain"),
    ("nan", math.nan, "non_finite"),
    ("inf", [math.inf], "non_finite"),
    ("minus_inf", {"a": -math.inf}, "non_finite"),
    ("above_i64", 2**63, "big_int"),
    ("below_i64", [-(2**63) - 1], "big_int"),
    ("surrogate", "a\ud800", "not_utf8"),
    ("surrogate_key", {"\udfff": 1}, "not_utf8"),
    ("cyclic_list", _cyclic_list(), "cycle"),
    ("cyclic_dict", _cyclic_dict(), "cycle"),
    ("too_deep", _too_deep(), "too_deep"),
]


@pytest.mark.parametrize(
    ("value", "reason"), [(value, reason) for _, value, reason in DECLINES], ids=[case[0] for case in DECLINES]
)
def test_rust_declines_what_it_cannot_write_exactly(value: object, reason: str) -> None:
    # Python's own conversion then runs for the leaf, with its own result or error.
    assert native_leaf_json.take({"citryValue0": "fine", "citryValue1": value}) == reason


@pytest.mark.parametrize(
    ("values", "reason"),
    [
        ([("citryText0", "x")], "not_plain"),
        (_Dict(citryText0="x"), "not_plain"),
        ({1: "x"}, "not_plain"),
        ({_Text("citryText0"): "x"}, "not_plain"),
        ({"citry\ud800": "x"}, "not_utf8"),
    ],
    ids=["not_a_dict", "dict_subclass", "int_key", "str_subclass_key", "surrogate_key"],
)
def test_rust_declines_leaf_data_of_another_shape(values: object, reason: str) -> None:
    assert _native._leaf_values_json(values, PLACEHOLDER) == reason


@pytest.mark.parametrize("key", ["opaqueHtml", "calls"])
def test_keys_whose_values_other_code_reads_stay_in_python(key: str) -> None:
    assert native_leaf_json.take({"citryText0": "x", key: {}}) == "value_read_key"


def test_a_secret_declines_and_python_keeps_its_refusal() -> None:
    values: dict[str, object] = {"citryText0": Secret("hidden")}
    assert native_leaf_json.take(values) == "not_plain"
    with pytest.raises(TypeError, match=r"must not contain a citry\.Secret; read the value on the server instead"):
        _json_plain(values["citryText0"])


def test_python_and_rust_both_write_deep_data_under_a_low_recursion_limit() -> None:
    # Rust has its own depth limit (200), and Python's conversion uses a
    # bounded number of frames, so a low recursion limit stops neither.
    value: object = "bottom"
    for _ in range(150):
        value = [value]
    limit = sys.getrecursionlimit()
    sys.setrecursionlimit(len(_frame_stack()) + 100)
    try:
        plain = _json_plain(value)
        leaf_json = _native._leaf_values_json({"citryDeep": value}, PLACEHOLDER)
    finally:
        sys.setrecursionlimit(limit)
    assert plain == value
    assert len(leaf_json) == 1


def _frame_stack() -> list[object]:
    """Return the frames on the current stack, to set a recursion limit just above them."""
    frames: list[object] = []
    frame: FrameType | None = sys._getframe()
    while frame is not None:
        frames.append(frame)
        frame = frame.f_back
    return frames


def test_the_encoder_refuses_a_leaf_item_assembly_never_makes() -> None:
    leaf_json = _native._leaf_values_json({"citryText0": "x"}, PLACEHOLDER)
    with pytest.raises(ValueError, match="preparedData is not a dict"):
        _native._encode_occurrences([_item(["x"])], {_ID: leaf_json}, _script_json)
    with pytest.raises(ValueError, match="placeholder has no JSON for its key"):
        _native._encode_occurrences([_item({"citryText1": PLACEHOLDER})], {_ID: leaf_json}, _script_json)
    with pytest.raises(ValueError, match="not a _NativeRow or _LeafJson"):
        _native._encode_occurrences([_item({})], {_ID: object()}, _script_json)
    with pytest.raises(ValueError, match="fallback did not return a str"):
        _native._encode_occurrences([_item({}, serverData={"a": 1})], {_ID: leaf_json}, lambda _value: 1)
    # A value Rust wrote with no placeholder would drop part of the leaf.
    with pytest.raises(ValueError, match="does not hold a placeholder for every value"):
        _native._encode_occurrences([_item({"calls": {}})], {_ID: leaf_json}, _script_json)
    with pytest.raises(ValueError, match="does not hold a placeholder for every value"):
        _native._encode_occurrences([{"id": _ID}], {_ID: leaf_json}, _script_json)
    # json.dumps would write an int key as quoted text; assembly never makes one.
    with pytest.raises(ValueError, match="item key is not a str"):
        _native._encode_occurrences([_item({1: "x", 2: "y"})], {_ID: leaf_json}, cast("Any", _script_json))


def test_an_item_written_without_rusts_json_fails_loudly() -> None:
    # The placeholder is no JSON value, so a writer that skips Rust's JSON
    # raises instead of sending the browser something wrong.
    with pytest.raises(TypeError, match="not JSON serializable"):
        _native._encode_occurrences([_item({"citryText0": PLACEHOLDER})], {}, _script_json)
    with pytest.raises(TypeError, match="not JSON serializable"):
        json.dumps(PLACEHOLDER)


def test_the_placeholder_survives_copy_and_pickle_as_the_same_object() -> None:
    assert copy.copy(PLACEHOLDER) is PLACEHOLDER
    assert copy.deepcopy({"k": PLACEHOLDER})["k"] is PLACEHOLDER
    assert pickle.loads(pickle.dumps(PLACEHOLDER)) is PLACEHOLDER  # noqa: S301 - our own bytes
    assert repr(PLACEHOLDER) == "<leaf JSON written by Rust>"


def test_the_leaf_json_holds_no_python_value_and_is_not_tracked() -> None:
    # It keeps only Rust strings and the placeholder, so it can be in no
    # reference cycle, and the collector does not need to track it.
    value = ["kept", {"a": 1}]
    values_refs = sys.getrefcount(value)
    placeholder_refs = sys.getrefcount(PLACEHOLDER)
    leaf_json = _native._leaf_values_json({"citryValue0": value}, PLACEHOLDER)
    assert sys.getrefcount(value) == values_refs
    assert not gc.is_tracked(leaf_json)
    del leaf_json
    assert sys.getrefcount(PLACEHOLDER) == placeholder_refs
