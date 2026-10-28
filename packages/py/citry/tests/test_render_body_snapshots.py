"""
Rendering a body produces the same output, structure and errors as before.

The body renderer walks a template's nodes with an explicit stack instead
of calling itself once per ``<c-if>``, ``<c-for>``, or ``<c-slot>`` that
renders its own fallback. These snapshots lock what rendering produced
before each of those changes: the control-flow fixtures were recorded on
1b64f7102, and the slot fixtures on 05b95e7a8. For each
fixture, on both render paths, they hold:

- the serialized HTML;
- the nested structure of the render result: which ``CitryRender`` and
  other parts hold which, written by ``_structure`` below;
- for the slot fixtures, the same in a component that uses Vue (its host
  HTML and browser data block), what an ``on_slot_rendered`` hook sees,
  and the output of a cached component's replay and of development mode;
- the error text for an expression that fails three levels deep, and the
  nodes that add their template position as the error passes out, also
  for errors raised inside nested fallbacks and by the slot hook.

Run with ``CITRY_UPDATE_RENDER_SNAPSHOTS=1`` to record them again; the file
is ``render_body_snapshots.json`` next to this one.
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

from citry import Citry, Component, Extension, component_render
from citry.citry_render import _VALUE_CONTEXT, CitryRender

if TYPE_CHECKING:
    from collections.abc import Callable

SNAPSHOT_FILE = Path(__file__).with_name("render_body_snapshots.json")
UPDATE = os.environ.get("CITRY_UPDATE_RENDER_SNAPSHOTS") == "1"

# Every condition and loop reads the template data. A constant one, such as
# `cond="1"`, is computed once when the component compiles, and the body
# renderer never sees it.

# How deep the nested fixtures go: deep enough that every level is a frame
# of the walk, shallow enough that the recorded structure stays readable.
DEPTH = 8


def _nest(open_tag: str, inner: str, close_tag: str, depth: int = DEPTH) -> str:
    return open_tag * depth + inner + close_tag * depth


def _nest_fallbacks(depth: int, inner: str) -> str:
    """`depth` nested `<c-slot>` tags, each with its own name, that nobody fills."""
    return "".join(f'<c-slot name="s{level}">' for level in range(depth)) + inner + "</c-slot>" * depth


def _structure(part: Any) -> Any:
    """Write a render part's nesting as plain data: type names and children."""
    if isinstance(part, str):
        return part
    if isinstance(part, CitryRender):
        return [type(part).__name__, [_structure(child) for child in part.parts]]
    return type(part).__name__


def _render_root(template: str, data: dict[str, Any], extra: Callable[[Citry], None] | None = None) -> Any:
    app = Citry()
    if extra is not None:
        extra(app)

    class Root(Component):
        citry = app

        def template_data(self, kwargs, slots):
            return dict(data)

    Root.template = template
    return Root().render()


def _children(app: Citry) -> None:
    """Register the small components the fixtures place."""

    class Card(Component):
        citry = app
        template = '<section class="card"><c-slot name="title">no title</c-slot><c-slot>{{ body }}</c-slot></section>'

        def template_data(self, kwargs, slots):
            return {"body": kwargs.get("body", "default body")}

    class Row(Component):
        citry = app
        template = "<li>{{ label }}</li>"

        def template_data(self, kwargs, slots):
            return {"label": kwargs.get("label", "?")}

    class Label(Component):
        citry = app
        simple = True
        template = "<span>{{ text }}<c-slot /></span>"

    class Holder(Component):
        citry = app
        template = "<div>{{ body }}</div>"

        def template_data(self, kwargs, slots):
            return {"body": kwargs.get("body")}

    class Wrap(Component):
        citry = app
        template = '<div class="wrap"><c-slot name="x"><i>wrap fallback</i></c-slot></div>'

    class PureFallbacks(Component):
        citry = app
        pure = True
        template = _nest_fallbacks(3, "<b>pure</b>")

    class CachedFallbacks(Component):
        citry = app
        template = _nest_fallbacks(3, "<b>cached</b><c-Row />")

        class Cache:
            enabled = True

    del Card, Row, Label, Holder, Wrap, PureFallbacks, CachedFallbacks


FIXTURES: dict[str, tuple[str, dict[str, Any]]] = {
    "if_elif_else": (
        _nest(
            '<c-if cond="n > 5">',
            "{{ n }}",
            '</c-if><c-elif cond="n > 2">mid</c-elif><c-else>low</c-else>',
        ),
        {"n": 7},
    ),
    "if_falls_to_else": (
        _nest('<c-if cond="flag"><b>', "{{ n }}", "</b></c-if><c-else>none</c-else>"),
        {"n": 1, "flag": False},
    ),
    "for_with_empty": (
        # Each level binds its own name, because a loop may not shadow one.
        "".join(f'<c-for each="x{level} in items">' for level in range(DEPTH))
        + "{{ x0 }}{{ x7 }}"
        + "</c-for><c-empty>empty</c-empty>" * DEPTH,
        {"items": [1, 2]},
    ),
    "for_empty_branch": (
        '<c-for each="x in items">{{ x }}</c-for><c-empty>' + _nest("<i>", "nothing", "</i>") + "</c-empty>",
        {"items": []},
    ),
    "shorthand_forms": (
        _nest(
            '<div c-if="flag">',
            '<p c-for="x in items">{{ x }}</p><p c-empty>none</p>',
            '</div><span c-elif="other">o</span><span c-else>e</span>',
        ),
        {"flag": True, "other": False, "items": ["a", "b"]},
    ),
    "mixed_elements_and_logic": (
        _nest('<c-if cond="flag"><ul>', '<c-for each="x in items"><li>{{ x }}</li></c-for>', "</ul></c-if>"),
        {"flag": True, "items": [1, 2, 3]},
    ),
    "components_with_slots_and_fills": (
        _nest(
            '<c-Card body="b"><c-fill name="title">T</c-fill><c-fill name="default">',
            "{{ n }}",
            "</c-fill></c-Card>",
        ),
        {"flag": True, "n": 3},
    ),
    "component_default_slot_content": (
        _nest('<c-if cond="flag"><c-Card body="inner">', "", "</c-Card></c-if>"),
        {"flag": True},
    ),
    "simple_component_slot_outlet": (
        _nest('<c-Label text="t">', "{{ n }}", "</c-Label>"),
        {"flag": True, "n": 4},
    ),
    "call_run_rows": (
        _nest('<c-if cond="flag"><ul>', '<c-Row c-for="k in keys" c-key="k" label="row" />', "</ul></c-if>"),
        {"flag": True, "keys": [1, 2, 3]},
    ),
    "template_in_attribute": (
        "<c-Holder c-body='" + _nest('<c-if cond="flag"><b>', "{{ n }}", "</b></c-if>") + "' />",
        {"flag": True, "n": 5},
    ),
    "dynamic_component_and_element": (
        _nest(
            '<c-if cond="flag">', '<c-component is="card" body="dyn" /><c-element c-is="tag">x</c-element>', "</c-if>"
        ),
        {"flag": True, "tag": "em"},
    ),
    "provide_and_inject": (
        _nest('<c-if cond="flag">', '<c-provide key="theme" mode="dark">{{ n }}</c-provide>', "</c-if>"),
        {"flag": True, "n": 6},
    ),
    # A `<c-slot>` that gets no fill renders its own body, its fallback.
    "fallback_one_level": (_nest_fallbacks(1, "{{ n }}"), {"n": 1}),
    "fallbacks_three_levels": (_nest_fallbacks(3, "<p>{{ n }}</p>"), {"n": 3}),
    "fallbacks_eight_levels": (
        _nest_fallbacks(DEPTH, '<c-if cond="flag">{{ n }}</c-if><c-Row label="in" />'),
        {"flag": True, "n": 8},
    ),
    "fallback_next_to_a_filled_slot": (
        _nest_fallbacks(3, '<c-Card body="b"><c-fill name="title">T</c-fill></c-Card>'),
        {},
    ),
    "fallback_shown_by_a_fill": (
        _nest_fallbacks(2, '<c-Wrap><c-fill name="x" fallback="original">[{{ original }}]</c-fill></c-Wrap>'),
        {},
    ),
    "fallback_with_slot_data": (
        '<c-slot name="outer" c-item="n"><c-slot name="inner" label="x">{{ n }}</c-slot></c-slot>',
        {"n": 2},
    ),
    "fallbacks_in_loops": (
        _nest_fallbacks(2, '<c-for each="x in items"><c-slot name="row">{{ x }}</c-slot></c-for>'),
        {"items": [1, 2]},
    ),
    "fallbacks_in_pure_and_cached_components": ("<c-PureFallbacks /><c-CachedFallbacks />", {}),
}

# A body made only of HTML, expressions and control flow renders through a
# Vue leaf program, which evaluates it without the body renderer. One child
# component in the body turns that off, so these copies render through the
# body renderer and its `IfNode` and `ForNode` steps.
_GENERAL_RENDERER_COPIES = (
    "if_elif_else",
    "if_falls_to_else",
    "for_with_empty",
    "shorthand_forms",
    "mixed_elements_and_logic",
)
for _name in _GENERAL_RENDERER_COPIES:
    _template, _data = FIXTURES[_name]
    FIXTURES[f"{_name}_with_component"] = ('<c-Row label="r" />' + _template, _data)

# An expression that fails three levels below the root, inside an `<c-if>`,
# a `<c-for>` and an element, so each level's template position is added to
# the error as it passes through.
ERROR_TEMPLATE = (
    '<main><c-Row label="r" /><c-if cond="flag"><c-for each="x in items">'
    '<p class="row">{{ x.missing }}</p></c-for></c-if></main>'
)


def _load() -> dict[str, Any]:
    if SNAPSHOT_FILE.exists():
        return json.loads(SNAPSHOT_FILE.read_text())
    return {}


def _check(key: str, observed: Any) -> None:
    """Compare `observed` with the recorded snapshot, or record it when updating."""
    snapshots = _load()
    if UPDATE:
        snapshots[key] = observed
        SNAPSHOT_FILE.write_text(json.dumps(snapshots, indent=1, sort_keys=True) + "\n")
        return
    assert key in snapshots, f"no snapshot for {key}; record with CITRY_UPDATE_RENDER_SNAPSHOTS=1"
    assert observed == snapshots[key]


@pytest.mark.parametrize("name", FIXTURES)
def test_render_output_and_structure_match_the_snapshot(name: str, render_path: str) -> None:
    template, data = FIXTURES[name]
    rendered = _render_root(template, data, _children)
    _check(
        f"{name}/{render_path}",
        {"html": rendered.serialize(deps_strategy="ignore"), "structure": _structure(rendered)},
    )


def test_an_error_three_levels_deep_matches_the_snapshot(render_path: str, monkeypatch: pytest.MonkeyPatch) -> None:
    # Only the innermost node's snippet shows in the text, so the nodes that
    # add their position on the way out are recorded too, in order.
    attached: list[str] = []
    original = component_render._attach_template_position

    def spy(err: Exception, node: object, context: object) -> None:
        attached.append(type(node).__name__)
        original(err, node, context)  # type: ignore[arg-type]

    monkeypatch.setattr(component_render, "_attach_template_position", spy)
    with pytest.raises(Exception) as caught:  # noqa: PT011 - the recorded text is what is compared
        _render_root(ERROR_TEMPLATE, {"items": [1], "flag": True}, _children).serialize(deps_strategy="ignore")
    # The error names the template's origin, this file's absolute path, which
    # differs between checkouts; the snapshot stores a placeholder for it.
    text = str(caught.value).replace(str(Path(__file__)), "<this test file>")
    _check(
        f"error/{render_path}",
        {"type": type(caught.value).__name__, "text": text, "attached": attached},
    )


# The slot fixtures also render in a component that uses Vue, where each
# fallback records which template wrote it in the browser data. The data
# block's ids are random or counted per process, so each distinct id becomes
# a numbered placeholder in the order it first appears; which id is which
# stays visible.
SLOT_FIXTURES = tuple(name for name in FIXTURES if "fallback" in name)
_VUE_DATA_BLOCK = re.compile(
    r'<script type="application/json" data-citry-vue-document="[^"]*">(.*?)</script>', re.DOTALL
)
# A counted id is "c" and eight letters or digits, at least one a digit,
# so a word such as "component" stays as it is.
_IDS = re.compile(r"\b(?:citryOccurrence[0-9a-f]+|[0-9a-f]{32}|c(?=[0-9a-z]{0,7}[0-9])[0-9a-z]{8})\b")


def _number_ids(text: str) -> str:
    numbered: dict[str, str] = {}
    return _IDS.sub(lambda match: numbered.setdefault(match.group(0), f"ID{len(numbered)}"), text)


def _vue_parts(page: str) -> dict[str, str]:
    """
    Return a Vue page's host HTML and browser data block, with ids numbered.

    Both are numbered in one pass, so an id the host and the data share, such
    as the app's element id, gets the same number in each.
    """
    block = _VUE_DATA_BLOCK.search(page)
    assert block is not None
    host, data = _number_ids(page[: page.index("<script")] + "\x00" + block.group(1)).split("\x00")
    return {"html": host, "data": data}


def _render_vue_root(template: str, data: dict[str, Any], extra: Callable[[Citry], None] | None = None) -> str:
    app = Citry()
    if extra is not None:
        extra(app)

    class Root(Component):
        citry = app
        js = """
            $component({});
        """

        def template_data(self, kwargs, slots):
            return dict(data)

    Root.template = template
    return Root().render().serialize()


@pytest.mark.parametrize("name", SLOT_FIXTURES)
def test_slot_fallbacks_with_vue_match_the_snapshot(name: str, render_path: str) -> None:
    template, data = FIXTURES[name]
    page = _render_vue_root(template, data, _children)
    _check(f"vue/{name}/{render_path}", _vue_parts(page))


class _SlotLog(Extension):
    """Record each slot the `on_slot_rendered` hook sees, and keep its result."""

    name = "slot_log"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.seen: list[list[Any]] = []

    def on_slot_rendered(self, ctx: Any) -> None:
        self.seen.append([ctx.slot_name, ctx.slot_is_required, _structure(ctx.result)])


@pytest.mark.parametrize("uses_vue", [False, True], ids=["html", "vue"])
@pytest.mark.parametrize("name", SLOT_FIXTURES)
def test_the_slot_hook_sees_the_same_fallbacks(name: str, uses_vue: bool, render_path: str) -> None:
    template, data = FIXTURES[name]
    app = Citry(extensions=[_SlotLog])
    _children(app)

    class Root(Component):
        citry = app

        def template_data(self, kwargs, slots):
            return dict(data)

    Root.template = template
    if uses_vue:
        Root.js = """
            $component({});
        """
    root = Root
    page = root().render().serialize() if uses_vue else root().render().serialize(deps_strategy="ignore")
    log = app.extensions.get_extension("slot_log")
    assert isinstance(log, _SlotLog)
    observed: dict[str, Any] = {"seen": log.seen}
    if uses_vue:
        observed |= _vue_parts(page)
    else:
        observed["html"] = page
    _check(f"hook/{name}/{'vue' if uses_vue else 'html'}/{render_path}", observed)


def test_a_cached_component_replays_its_fallbacks_the_same_way(render_path: str) -> None:
    # The first render records the cache artifact and the second replays it.
    app = Citry()
    _children(app)

    class Root(Component):
        citry = app
        template = "<c-CachedFallbacks /><c-CachedFallbacks />"

    first = Root().render().serialize(deps_strategy="ignore")
    second = Root().render().serialize(deps_strategy="ignore")
    # Component ids come from counters that earlier renders in the process
    # have moved on, and a replay makes some of its own, so each distinct id
    # is numbered by where it first appears.
    # Numbered in one pass, so an id the two renders share keeps its number.
    first, second = _number_cids(first + "\x00" + second).split("\x00")
    _check(f"cached_replay/{render_path}", {"first": first, "second": second})


def _number_cids(html: str) -> str:
    numbered: dict[str, str] = {}
    return re.sub(
        r"data-cid-([0-9a-z]+)",
        lambda match: "data-cid-" + numbered.setdefault(match.group(1), f"ID{len(numbered)}"),
        html,
    )


def test_fallbacks_render_the_same_way_in_development_mode(render_path: str) -> None:
    # Development mode installs Citry's development extensions, which also
    # look at each slot's result.
    app = Citry(mode="development")
    _children(app)

    class Root(Component):
        citry = app
        template = _nest_fallbacks(3, '<p>{{ n }}</p><c-Card body="b" />')

        def template_data(self, kwargs, slots):
            return {"n": 3}

    _check(f"development/{render_path}", {"html": Root().render().serialize(deps_strategy="ignore")})


def _paused_fallbacks() -> int:
    """Count slot fallbacks whose steps are paused, still holding their scopes."""
    # An exact type check, because `isinstance` reads `__class__`, and on a
    # lazy object such as Django's `staticfiles_storage` that builds the
    # object, which raises when Django's settings leave it unconfigured. A
    # generator type cannot be subclassed, so nothing is missed.
    return sum(
        1
        for value in gc.get_objects()
        if type(value) is types.GeneratorType
        and value.gi_code.co_qualname == "SlotNode._slot_steps"
        and value.gi_frame is not None
    )


def _assert_no_fallback_is_left_paused() -> None:
    """
    Check that an error finished every slot fallback it passed through.

    A fallback left paused still holds its scopes. It is only finished when
    the error's traceback is freed, and then quietly, so the check runs
    while the caller still holds the error.
    """
    assert _paused_fallbacks() == 0
    assert _VALUE_CONTEXT.get() is None


# An expression that fails inside three nested fallbacks, so each one adds
# its slot to the error's component path on the way out.
FALLBACK_ERROR_TEMPLATE = '<c-Row label="r" />' + _nest_fallbacks(3, "<p>{{ x.missing }}</p>")


def _render_failing(template: str, data: dict[str, Any], *, uses_vue: bool) -> str:
    if uses_vue:
        return _render_vue_root(template, data, _children)
    return _render_root(template, data, _children).serialize(deps_strategy="ignore")


def _recorded_error(err: BaseException) -> dict[str, Any]:
    return {
        "type": type(err).__name__,
        "text": _number_ids(str(err).replace(str(Path(__file__)), "<this test file>")),
        "cause": repr(err.__cause__),
        "context": type(err.__context__).__name__,
        "suppress_context": err.__suppress_context__,
    }


@pytest.mark.parametrize("uses_vue", [False, True], ids=["html", "vue"])
def test_an_error_inside_three_fallbacks_matches_the_snapshot(
    uses_vue: bool, render_path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    attached: list[str] = []
    original = component_render._attach_template_position

    def spy(err: Exception, node: object, context: object) -> None:
        attached.append(type(node).__name__)
        original(err, node, context)  # type: ignore[arg-type]

    monkeypatch.setattr(component_render, "_attach_template_position", spy)
    with pytest.raises(Exception) as caught:  # noqa: PT011 - the recorded text is what is compared
        _render_failing(FALLBACK_ERROR_TEMPLATE, {"x": 1}, uses_vue=uses_vue)
    _assert_no_fallback_is_left_paused()
    _check(
        f"fallback_error/{'vue' if uses_vue else 'html'}/{render_path}",
        _recorded_error(caught.value) | {"attached": attached},
    )


def _empty_next() -> object:
    # A template function that calls `next()` on an empty iterator.
    return next(iter(()))


@pytest.mark.parametrize("uses_vue", [False, True], ids=["html", "vue"])
def test_a_stop_iteration_inside_fallbacks_matches_the_snapshot(
    uses_vue: bool, render_path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Python turns a StopIteration that leaves a generator into a
    # RuntimeError, and the slots' error frames are generators, so what comes
    # out, and which slots it names, is recorded rather than assumed.
    template = '<c-Row label="r" />' + _nest_fallbacks(3, "<p>{{ stop() }}</p>")
    with pytest.raises(Exception) as caught:  # noqa: PT011 - the recorded type is what is compared
        _render_failing(template, {"stop": _empty_next}, uses_vue=uses_vue)
    _assert_no_fallback_is_left_paused()
    _check(f"stop_iteration/{'vue' if uses_vue else 'html'}/{render_path}", _recorded_error(caught.value))


def test_a_keyboard_interrupt_inside_fallbacks_passes_through(
    render_path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    def interrupt() -> object:
        raise KeyboardInterrupt

    template = '<c-Row label="r" />' + _nest_fallbacks(3, "<p>{{ interrupt() }}</p>")
    with pytest.raises(KeyboardInterrupt) as caught:
        _render_failing(template, {"interrupt": interrupt}, uses_vue=False)
    # A KeyboardInterrupt is not an Exception, so no slot adds itself to it.
    assert not hasattr(caught.value, "_components")
    _assert_no_fallback_is_left_paused()


class _FailingSlotHook(Extension):
    """An `on_slot_rendered` hook that fails on the innermost fallback."""

    name = "failing_slot_hook"
    error: type[Exception] = ValueError

    def on_slot_rendered(self, ctx: Any) -> None:
        if ctx.slot_name == "s2":
            raise type(self).error("the hook failed")


class _StoppingSlotHook(_FailingSlotHook):
    """A hook that raises StopIteration while it handles a KeyError, so the error has a context."""

    name = "stopping_slot_hook"
    error = StopIteration

    def on_slot_rendered(self, ctx: Any) -> None:
        if ctx.slot_name == "s2":
            try:
                {}["missing"]
            except KeyError:
                raise StopIteration("the hook failed")  # noqa: B904 - the KeyError stays as the context


@pytest.mark.parametrize("hook", [_FailingSlotHook, _StoppingSlotHook], ids=["value_error", "stop_iteration"])
def test_an_error_from_the_slot_hook_matches_the_snapshot(
    hook: type[_FailingSlotHook], render_path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The hook runs after the fallback's body, still inside the slot, so the
    # slot is on the error's component path.
    app = Citry(extensions=[hook])
    _children(app)

    class Root(Component):
        citry = app
        template = _nest_fallbacks(3, "<p>x</p>")

    with pytest.raises(Exception) as caught:  # noqa: PT011 - the recorded type is what is compared
        Root().render().serialize(deps_strategy="ignore")
    _assert_no_fallback_is_left_paused()
    key = "hook_error" if hook is _FailingSlotHook else "hook_stop_iteration"
    _check(f"{key}/{render_path}", _recorded_error(caught.value))


def _paused_at_yield(handle: Callable[[BaseException], BaseException | None]) -> Any:
    """A body generator paused at its `yield`, which passes a thrown error to `handle`."""

    def bodies() -> Any:
        try:
            yield ([], None)
        except BaseException as err:
            replacement = handle(err)
            if replacement is not None:
                raise replacement from err

    generator = bodies()
    next(generator)
    return generator


def test_throwing_into_body_steps_returns_the_error_that_comes_out() -> None:
    err = KeyError("inner")
    # Raised again unchanged.
    assert component_render._throw_into(_paused_at_yield(lambda e: e), err) is err
    # Replaced by another error.
    replacement = component_render._throw_into(_paused_at_yield(lambda _e: ValueError("other")), err)
    assert type(replacement) is ValueError
    assert replacement.__cause__ is err
    # Swallowed: the generator ends instead of raising.
    swallowed = component_render._throw_into(_paused_at_yield(lambda _e: None), err)
    assert type(swallowed) is RuntimeError
    assert swallowed.__cause__ is err
    # Yields again: also dropped, and the generator is closed.
    left: list[str] = []

    def yields_again() -> Any:
        try:
            yield ([], None)
        except KeyError:
            try:
                yield ([], None)
            finally:
                left.append("closed")

    again = yields_again()
    next(again)
    assert type(component_render._throw_into(again, err)) is RuntimeError
    assert left == ["closed"]
    # A KeyboardInterrupt passes through like any other error.
    interrupt = KeyboardInterrupt()
    assert component_render._throw_into(_paused_at_yield(lambda e: e), interrupt) is interrupt
