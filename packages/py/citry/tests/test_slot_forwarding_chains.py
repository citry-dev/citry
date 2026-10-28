"""
A fill passed on through a chain of components renders the same output, structure and errors as before.

A chain is a row of components where each one hands the fill it received
to the next one's slot with ``<c-fill name="default"><c-slot /></c-fill>``.
These snapshots lock what such chains rendered before the body renderer
learned to render a passed template fill on its own stack (#299). They were
recorded on e1c370f9e. Both render paths must match the same recording.
For each fixture they hold:

- the serialized HTML, and for a component that uses Vue its host HTML and
  browser data block;
- the nested structure of the render result (which ``CitryRender`` and
  other parts hold which, written by ``_structure`` below);
- what an ``on_slot_rendered`` hook sees at every link, and the output when
  the hook replaces a slot's result;
- the error text for an error raised inside the deepest fill, or while
  its slot data is bound, with the component path and template position it
  carries, and the nodes that add their template position as the error
  passes out.

The last tests check which fills the body renderer leaves to a ``Slot``
call: every fill while code has replaced one of the methods that call
runs, and a fill that is a ``Slot`` subclass.

Run with ``CITRY_UPDATE_RENDER_SNAPSHOTS=1`` to record them again; the file
is ``slot_forwarding_chains_snapshots.json`` next to this one.
"""

from __future__ import annotations

import gc
import json
import os
import re
import types
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from markupsafe import Markup

from citry import Citry, Component, Extension, component_render, nodes
from citry._vue.direct import active_execution
from citry.citry_render import _VALUE_CONTEXT, CitryRender
from citry.slots import Slot

if TYPE_CHECKING:
    from collections.abc import Callable

SNAPSHOT_FILE = Path(__file__).with_name("slot_forwarding_chains_snapshots.json")
UPDATE = os.environ.get("CITRY_UPDATE_RENDER_SNAPSHOTS") == "1"

# The chain lengths every plain fixture renders: one link (no forwarding),
# a short chain, and one long enough that a per-link cost would show.
CHAIN_LENGTHS = (1, 3, 21)


def _forward(index: int, fill_attrs: str = "", slot: str = "<c-slot />") -> str:
    """The template of link `index`: pass the received fill on to link `index - 1`."""
    return (
        f'<span class="l{index}"><c-Link{index - 1}><c-fill name="default"{fill_attrs}>'
        f"{slot}</c-fill></c-Link{index - 1}></span>"
    )


# Each shape is `(innermost link's template, template of link i > 0, the
# page's fill)`. The page renders the last link with its fill, so the fill
# passes through every link before link 0's `<c-slot>` renders it.
SHAPES: dict[str, tuple[str, Callable[[int], str], str]] = {
    "plain": (
        '<p class="l0"><c-slot>no fill</c-slot></p>',
        _forward,
        '<c-fill name="default"><b>{{ n }}</b></c-fill>',
    ),
    # Link 0 passes each loop row as slot data, and every link passes the
    # row it received on, so each row reaches the page's fill.
    "scoped_rows": (
        '<ul><c-for each="row in rows"><li><c-slot c-row="row" /></li></c-for></ul>',
        lambda i: _forward(i, ' data="d"', '<c-slot c-row="d.row" />'),
        '<c-fill name="default" data="d">row {{ d.row }}</c-fill>',
    ),
    # Every link's fill prints the fallback it was given inside its own
    # slot's fallback, and the page's fill prints the last one.
    "fallbacks": (
        "<c-slot>base fallback</c-slot>",
        lambda i: _forward(i, ' fallback="fb"', "<c-slot>[{{ fb }}]</c-slot>"),
        '<c-fill name="default" fallback="fb">({{ fb }})</c-fill>',
    ),
    # Link 0 provides around its slot, and every link provides both around
    # the next link and inside its forwarding fill, at the slot it forwards.
    "provides": (
        '<c-provide key="site" v="link0"><c-slot /></c-provide>',
        lambda i: (
            f'<c-provide key="k{i}" v="{i}"><c-Link{i - 1}><c-fill name="default">'
            f'<c-provide key="hop" v="{i}"><c-slot /></c-provide>'
            f"</c-fill></c-Link{i - 1}></c-provide>"
        ),
        '<c-fill name="default"><c-Inj /></c-fill>',
    ),
    # The page's fill holds a component with a fill of its own, which goes
    # through a second, shorter chain.
    "nested_fills": (
        '<p class="l0"><c-slot>no fill</c-slot></p>',
        _forward,
        '<c-fill name="default">outer <c-Link1><c-fill name="default">inner {{ n }}</c-fill></c-Link1></c-fill>',
    ),
    "empty_fill": (
        '<p class="l0"><c-slot>no fill</c-slot></p>',
        _forward,
        '<c-fill name="default"></c-fill>',
    ),
    # Link 1 shows the fill it received through an expression instead of a
    # `<c-slot>`, so the chain mixes both ways of passing a fill on.
    "expression_link": (
        '<p class="l0"><c-slot>no fill</c-slot></p>',
        lambda i: _forward(i, "", "{{ content }}" if i == 1 else "<c-slot />"),
        '<c-fill name="default"><b>{{ n }}</b></c-fill>',
    ),
}


def _data(self: Component, kwargs: Any, slots: Any) -> dict[str, Any]:
    return {"n": "deepest", "rows": [1, 2, 3], "content": slots.get("default")}


def _inj_data(self: Component, kwargs: Any, slots: Any) -> dict[str, Any]:
    # Every key any link provides, so the snapshot shows which ones reach
    # the component inside the page's fill.
    keys = ["page", "site", "hop", *(f"k{index}" for index in range(max(CHAIN_LENGTHS)))]
    seen = {key: getattr(self.inject(key, None), "v", None) for key in keys}
    return {"seen": {key: value for key, value in seen.items() if value is not None}}


def _app(
    shape: str, links: int, *, uses_vue: bool, extensions: list[Any] | None = None
) -> tuple[Citry, type[Component], dict[str, type[Component]]]:
    """Build a chain of `links` components in a fresh app, and the page that fills it."""
    app = Citry(extensions=extensions or [])
    js = {"js": "$component({});"} if uses_vue else {}
    innermost, forward, page_fill = SHAPES[shape]

    def component(name: str, template: str, **attrs: Any) -> type[Component]:
        return type(
            name,
            (Component,),
            {"citry": app, "template": template, "template_data": _data, "__module__": __name__, **js, **attrs},
        )

    component("Inj", "<em>{{ seen }}</em>", template_data=_inj_data)
    chain = {
        f"Link{index}": component(f"Link{index}", innermost if index == 0 else forward(index))
        for index in range(links)
    }
    last = links - 1
    page_template = page_fill if shape != "nested_fills" or links > 1 else page_fill.replace("Link1", "Link0")
    page = component(
        "Page",
        f'<c-provide key="page" v="p"><c-Link{last}>{page_template}</c-Link{last}></c-provide>',
    )
    return app, page, chain


def _load() -> dict[str, Any]:
    if SNAPSHOT_FILE.exists():
        return json.loads(SNAPSHOT_FILE.read_text())
    return {}


def _check(key: str, observed: Any) -> None:
    """Compare `observed` with the recorded snapshot, or record it when updating."""
    snapshots = _load()
    if UPDATE:
        snapshots[key] = observed
        # One snapshot per line, so a change shows as a change to that line.
        lines = (
            f"{json.dumps(name)}: {json.dumps(value, sort_keys=True)}" for name, value in sorted(snapshots.items())
        )
        SNAPSHOT_FILE.write_text("{\n" + ",\n".join(lines) + "\n}\n")
        return
    assert key in snapshots, f"no snapshot for {key}; record with CITRY_UPDATE_RENDER_SNAPSHOTS=1"
    assert observed == snapshots[key]


def _structure(part: Any) -> Any:
    """Write a render part's nesting as plain data: type names and children."""
    if isinstance(part, str):
        return part
    if isinstance(part, CitryRender):
        return [type(part).__name__, [_structure(child) for child in part.parts]]
    return type(part).__name__


# Render ids are counted per process, and each Vue app's element id is
# random, so each distinct id becomes a numbered placeholder in the order it
# first appears; which id is which stays visible. A counted id is "c" and
# eight letters or digits, at least one a digit, so a word such as
# "component" stays as it is.
_IDS = re.compile(r"\b(?:citryOccurrence[0-9a-f]+|[0-9a-f]{32}|c(?=[0-9a-z]{0,7}[0-9])[0-9a-z]{8})\b")


def _number_ids(text: str) -> str:
    numbered: dict[str, str] = {}
    return _IDS.sub(lambda match: numbered.setdefault(match.group(0), f"ID{len(numbered)}"), text)


def _observe(page: type[Component], *, uses_vue: bool) -> dict[str, Any]:
    """Render `page` and return its HTML and structure, or its host HTML and data block with Vue."""
    rendered = page().render()
    structure = json.dumps(_structure(rendered))
    if not uses_vue:
        html = rendered.serialize(deps_strategy="ignore")
        html, structure = _number_ids(html + "\x00" + structure).split("\x00")
        return {"html": html, "structure": json.loads(structure)}
    text = rendered.serialize()
    block = re.search(
        r'<script type="application/json" data-citry-vue-document="[^"]*">(.*?)</script>', text, re.DOTALL
    )
    assert block is not None
    # Numbered in one pass, so an id the host and the data share keeps its number.
    host, data, structure = _number_ids(
        text[: text.index("<script")] + "\x00" + block.group(1) + "\x00" + structure
    ).split("\x00")
    return {"html": host, "data": data, "structure": json.loads(structure)}


def _render_page(page: type[Component], *, uses_vue: bool) -> str:
    rendered = page().render()
    return rendered.serialize() if uses_vue else rendered.serialize(deps_strategy="ignore")


def _vue_id(uses_vue: bool) -> str:
    return "vue" if uses_vue else "html"


@pytest.mark.parametrize("uses_vue", [False, True], ids=["html", "vue"])
@pytest.mark.parametrize("links", CHAIN_LENGTHS)
def test_a_forwarded_chain_renders_as_before(links: int, uses_vue: bool, render_path: str) -> None:
    _, page, _chain = _app("plain", links, uses_vue=uses_vue)
    _check(f"plain/{links}/{_vue_id(uses_vue)}", _observe(page, uses_vue=uses_vue))


@pytest.mark.parametrize("uses_vue", [False, True], ids=["html", "vue"])
@pytest.mark.parametrize("shape", [name for name in SHAPES if name != "plain"])
def test_each_chain_shape_renders_as_before(shape: str, uses_vue: bool, render_path: str) -> None:
    _, page, _chain = _app(shape, 3, uses_vue=uses_vue)
    # Some shapes are refused with Vue (a fill that shows the fallback it was
    # given inside another component's slot); the error is recorded then.
    try:
        observed = _observe(page, uses_vue=uses_vue)
    except Exception as err:  # noqa: BLE001 - the recorded error is what is compared
        observed = _recorded_error(err)
    _check(f"{shape}/3/{_vue_id(uses_vue)}", observed)


def test_a_long_chain_of_scoped_rows_renders_as_before(render_path: str) -> None:
    _, page, _chain = _app("scoped_rows", 21, uses_vue=False)
    _check("scoped_rows/21/html", _observe(page, uses_vue=False))


def test_a_python_fill_at_the_end_of_a_chain_renders_as_before(render_path: str) -> None:
    # A fill given from Python is not a template fill, so it takes the
    # `Slot` call at link 0 while the links' own fills do not.
    _, _page, chain = _app("plain", 3, uses_vue=False)
    rendered = chain["Link2"](slots={"default": lambda _ctx: Markup("<b>from python</b>")}).render()
    _check(
        "python_fill/3/html",
        {"html": _number_ids(rendered.serialize(deps_strategy="ignore")), "structure": _structure(rendered)},
    )


class _SlotLog(Extension):
    """Record what the `on_slot_rendered` hook sees at each slot, and keep each result."""

    name = "slot_log"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.seen: list[Any] = []

    def on_slot_rendered(self, ctx: Any) -> Any:
        self.seen.append(
            {
                "component": type(ctx.component).__name__,
                "slot_name": ctx.slot_name,
                "required": ctx.slot_is_required,
                "slot_type": type(ctx.slot).__name__,
                "slot_owner": ctx.slot.component_name,
                "slot_slot_name": ctx.slot.slot_name,
                "slot_position": ctx.slot.source_position,
                "node_position": ctx.slot_node.position,
                "result": _structure(ctx.result),
            }
        )
        return self.replace(ctx)

    def replace(self, ctx: Any) -> Any:
        return None


class _TextSlotHook(_SlotLog):
    """Replace link 0's slot with text, which is escaped."""

    name = "text_slot_hook"

    def replace(self, ctx: Any) -> Any:
        return f"<{type(ctx.component).__name__}>" if type(ctx.component).__name__ == "Link0" else None


class _MarkupSlotHook(_SlotLog):
    """Wrap every link's slot result in trusted HTML that names the link."""

    name = "markup_slot_hook"

    def replace(self, ctx: Any) -> Any:
        # A component class name is a Python identifier, so it holds no markup.
        return Markup(f"<u>{type(ctx.component).__name__}</u>")  # noqa: S704


HOOKS: dict[str, type[_SlotLog]] = {"none": _SlotLog, "text": _TextSlotHook, "markup": _MarkupSlotHook}


def _hook_observation(hook: type[_SlotLog], shape: str, links: int, *, uses_vue: bool) -> dict[str, Any]:
    app, page, _chain = _app(shape, links, uses_vue=uses_vue, extensions=[hook])
    observed = _observe(page, uses_vue=uses_vue)
    log = app.extensions.get_extension(hook.name)
    assert isinstance(log, _SlotLog)
    # The structure and HTML hold the same render ids as the log does not.
    return observed | {"seen": json.loads(_number_ids(json.dumps(log.seen)))}


@pytest.mark.parametrize("uses_vue", [False, True], ids=["html", "vue"])
@pytest.mark.parametrize("links", CHAIN_LENGTHS)
def test_the_slot_hook_sees_every_link_as_before(links: int, uses_vue: bool, render_path: str) -> None:
    observed = _hook_observation(_SlotLog, "plain", links, uses_vue=uses_vue)
    _check(f"hook/none/plain/{links}/{_vue_id(uses_vue)}", observed)


@pytest.mark.parametrize("uses_vue", [False, True], ids=["html", "vue"])
@pytest.mark.parametrize("hook", ["text", "markup"])
def test_a_slot_hook_that_replaces_results_renders_as_before(hook: str, uses_vue: bool, render_path: str) -> None:
    observed = _hook_observation(HOOKS[hook], "plain", 3, uses_vue=uses_vue)
    _check(f"hook/{hook}/plain/3/{_vue_id(uses_vue)}", observed)


@pytest.mark.parametrize("shape", ["scoped_rows", "fallbacks", "provides", "nested_fills", "empty_fill"])
def test_the_slot_hook_sees_each_chain_shape_as_before(shape: str, render_path: str) -> None:
    observed = _hook_observation(_SlotLog, shape, 3, uses_vue=False)
    _check(f"hook/none/{shape}/3/html", observed)


def _paused_slot_steps() -> int:
    """Count slot steps paused at a body, still holding their scopes."""
    # An exact type check: `isinstance` reads `__class__`, which a lazy
    # object may build on access. A generator type cannot be subclassed.
    return sum(
        1
        for value in gc.get_objects()
        if type(value) is types.GeneratorType
        and value.gi_code.co_qualname.startswith("SlotNode.")
        and value.gi_frame is not None
    )


def _assert_nothing_is_left_open() -> None:
    """Check that an error left every slot it passed through, while the caller still holds the error."""
    assert _paused_slot_steps() == 0
    assert _VALUE_CONTEXT.get() is None
    assert active_execution() is None


def _recorded_error(err: BaseException) -> dict[str, Any]:
    return {
        "type": type(err).__name__,
        "text": _number_ids(str(err).replace(str(Path(__file__)), "<this test file>")),
        "args": _number_ids(repr(err.args).replace(str(Path(__file__)), "<this test file>")),
        "components": getattr(err, "_components", None),
        "cause": repr(err.__cause__),
        "context": type(err.__context__).__name__,
        "suppress_context": err.__suppress_context__,
    }


def _boom() -> object:
    raise ValueError("boom in the deepest fill")


def _stop() -> object:
    # A template function that calls `next()` on an empty iterator.
    return next(iter(()))


def _interrupt() -> object:
    raise KeyboardInterrupt


# Each error kind, raised by an expression inside the page's fill, which
# renders at the innermost link's slot.
ERRORS: dict[str, str] = {
    "value_error": "{{ boom() }}",
    "key_error": "{{ empty['missing'] }}",
    "stop_iteration": "{{ stop() }}",
}


def _failing_data(self: Component, kwargs: Any, slots: Any) -> dict[str, Any]:
    return {"boom": _boom, "stop": _stop, "interrupt": _interrupt, "empty": {}}


def _failing_page(expression: str, links: int, *, uses_vue: bool) -> type[Component]:
    _, page, _chain = _app("plain", links, uses_vue=uses_vue)
    page.template = str(page.template).replace("<b>{{ n }}</b>", f"<b>{expression}</b>")
    page.template_data = _failing_data  # type: ignore[method-assign]
    return page


@pytest.mark.parametrize("uses_vue", [False, True], ids=["html", "vue"])
@pytest.mark.parametrize("links", [1, 3, 21])
@pytest.mark.parametrize("kind", ERRORS)
def test_an_error_in_the_deepest_fill_matches_the_snapshot(
    kind: str, links: int, uses_vue: bool, render_path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Only the innermost node's snippet shows in the text, so the nodes that
    # add their position on the way out are recorded too, in order.
    attached: list[str] = []
    original = component_render._attach_template_position

    def spy(err: Exception, node: object, context: object) -> None:
        attached.append(type(node).__name__)
        original(err, node, context)  # type: ignore[arg-type]

    monkeypatch.setattr(component_render, "_attach_template_position", spy)
    page = _failing_page(ERRORS[kind], links, uses_vue=uses_vue)
    with pytest.raises(Exception) as caught:  # noqa: PT011 - the recorded text is what is compared
        _render_page(page, uses_vue=uses_vue)
    _assert_nothing_is_left_open()
    _check(
        f"error/{kind}/{links}/{_vue_id(uses_vue)}",
        _recorded_error(caught.value) | {"attached": attached},
    )


@pytest.mark.parametrize("uses_vue", [False, True], ids=["html", "vue"])
def test_a_keyboard_interrupt_in_the_deepest_fill_passes_through(uses_vue: bool, render_path: str) -> None:
    page = _failing_page("{{ interrupt() }}", 3, uses_vue=uses_vue)
    with pytest.raises(KeyboardInterrupt) as caught:
        page().render()
    # A KeyboardInterrupt is not an Exception, so no slot adds itself to it.
    assert not hasattr(caught.value, "_components")
    _assert_nothing_is_left_open()


class _FailingSlotHook(Extension):
    """An `on_slot_rendered` hook that fails at link 0's slot."""

    name = "failing_slot_hook"

    def on_slot_rendered(self, ctx: Any) -> None:
        if type(ctx.component).__name__ == "Link0":
            raise ValueError("the hook failed")


class _StoppingSlotHook(Extension):
    """A hook that raises StopIteration at link 0 while it handles a KeyError, so the error has a context."""

    name = "stopping_slot_hook"

    def on_slot_rendered(self, ctx: Any) -> None:
        if type(ctx.component).__name__ == "Link0":
            try:
                {}["missing"]
            except KeyError:
                raise StopIteration("the hook failed")  # noqa: B904 - the KeyError stays as the context


@pytest.mark.parametrize("uses_vue", [False, True], ids=["html", "vue"])
@pytest.mark.parametrize("hook", [_FailingSlotHook, _StoppingSlotHook], ids=["value_error", "stop_iteration"])
def test_an_error_from_the_slot_hook_in_a_chain_matches_the_snapshot(
    hook: type[Extension], uses_vue: bool, render_path: str
) -> None:
    # The hook runs after the fill's body, still inside link 0's slot, so the
    # slot is on the error's component path.
    _, page, _chain = _app("plain", 3, uses_vue=uses_vue, extensions=[hook])
    with pytest.raises(Exception) as caught:  # noqa: PT011 - the recorded type is what is compared
        page().render()
    _assert_nothing_is_left_open()
    _check(f"hook_error/{hook.name}/3/{_vue_id(uses_vue)}", _recorded_error(caught.value))


@pytest.mark.parametrize("uses_vue", [False, True], ids=["html", "vue"])
@pytest.mark.parametrize("links", [1, 3])
def test_an_error_binding_the_fill_data_matches_the_snapshot(links: int, uses_vue: bool, render_path: str) -> None:
    # The page's fill reads a slot data field the innermost slot does not
    # pass, so binding the data fails before the fill's body renders.
    _, page, _chain = _app("plain", links, uses_vue=uses_vue)
    page.template = str(page.template).replace(
        '<c-fill name="default"><b>{{ n }}</b></c-fill>',
        '<c-fill name="default" data="{ missing }"><b>{{ missing }}</b></c-fill>',
    )
    with pytest.raises(Exception) as caught:  # noqa: PT011 - the recorded text is what is compared
        _render_page(page, uses_vue=uses_vue)
    _assert_nothing_is_left_open()
    _check(f"error/fill_data/{links}/{_vue_id(uses_vue)}", _recorded_error(caught.value))


def test_a_replaced_slot_call_still_sees_every_fill(render_path: str, monkeypatch: pytest.MonkeyPatch) -> None:
    # While code has replaced `Slot.__call__`, every link calls its fill
    # through it, as every link did before fills joined the running loop.
    called: list[str | None] = []
    original = Slot.__call__

    def spy(self: Slot, *args: Any, **kwargs: Any) -> Any:
        called.append(self.component_name)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Slot, "__call__", spy)
    _, page, _chain = _app("plain", 3, uses_vue=False)
    assert _observe(page, uses_vue=False) == _load()["plain/3/html"]
    # The `<c-provide>` body is a fill too.
    assert called == ["provide", "link0", "link1", "link2"]


def test_a_replaced_template_render_still_sees_every_fill(render_path: str, monkeypatch: pytest.MonkeyPatch) -> None:
    rendered: list[str] = []
    original = nodes._TemplateSlotContent._render

    def spy(self: Any, ctx: Any) -> Any:
        rendered.append(self._component_name)
        return original(self, ctx)

    monkeypatch.setattr(nodes._TemplateSlotContent, "_render", spy)
    _, page, _chain = _app("plain", 3, uses_vue=False)
    assert _observe(page, uses_vue=False) == _load()["plain/3/html"]
    assert rendered == ["provide", "link0", "link1", "link2"]


def test_a_slot_subclass_fill_renders_through_a_slot_call(render_path: str, monkeypatch: pytest.MonkeyPatch) -> None:
    # Only a plain `Slot` is rendered in the running loop; a subclass may
    # change what a call does, so its slot calls it.
    class TaggedSlot(Slot):
        pass

    called: list[str] = []
    original = nodes.SlotNode._render_direct

    def spy(self: Any, context: Any, component: Any, *args: Any) -> Any:
        called.append(type(component).__name__)
        return original(self, context, component, *args)

    monkeypatch.setattr(nodes.SlotNode, "_render_direct", spy)
    _, _page, chain = _app("plain", 3, uses_vue=False)
    html = chain["Link2"](slots={"default": TaggedSlot("from a subclass")}).render().serialize(deps_strategy="ignore")
    assert '<p class="l0" ' in html
    assert "from a subclass</p>" in html
    # Link 2's slot gets the subclass; links 1 and 0 get template fills.
    assert called == ["Link2"]
