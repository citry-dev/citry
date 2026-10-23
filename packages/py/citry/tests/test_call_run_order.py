"""
Lock the order in which one render calls user code and extension hooks.

Each case builds a small page whose ``simple="vue"`` rows come from a
``c-for`` loop, renders it, serializes it, and records every call the page
makes into user code and into the extensions' hooks, in the order the calls
happen. The test compares that record with the one observed on today's
renderer and stored in ``fixtures/call_run_order.json``.

The record is the contract any faster render path has to keep: the same
user callbacks and hooks, called the same number of times, in the same
order, seeing the same execution frame, with the same error at the end. A
change that reorders one row's callbacks, calls a hook once more, or loses
part of an error chain fails here even when the HTML stays the same.
Every case runs on both render paths (the ``render_path`` fixture): the
native one, where Rust reads the rows, and the Python one.

``CASES`` names every case, says what it changes on the page, and gives a
one-line summary of its record: the rows and child components whose data
methods ran, in order, and how the case ended. The test checks the summary
too, so it stays true.

Each line of a record is one of these, in call order:

- ``id``: one call of the engine's render-id generator;
- ``Row a1: Kwargs, template_data (no frame), js_data (no frame)``: the
  calls made for one row, in order. ``Kwargs`` means Citry built the row's
  inputs (the data class's ``__post_init__`` ran). Each data method names
  its execution frame: the slot fill call Citry was rendering when the
  method ran, directly or through a child component, as
  ``citry._vue.direct.active_execution()`` returns it. Frames are numbered
  in order of first appearance; ``no frame`` means outside any fill;
- ``hook on_component_data RowList: DependenciesExtension, EventsExtension,
  I18nExtension``: one hook called for one component, by each extension in
  call order. The component is left out when the hook's context names
  none, as for ``on_dependencies``. A merge line names two components,
  ``RowList into Pair``: the one whose template wrote the merged part, and
  the one it merges into;
- a standalone event, such as ``Row.TemplateData built for a 1`` or
  ``key str a1`` (a key object turned into text).

Consecutive calls on one subject share a line, which keeps the file short
without losing any call or its position. A hook called twice in a row
shows each extension twice on its line.

The hooks are recorded with ``sys.setprofile``, which sees each hook
function start without replacing it. Replacing the hook methods would
change the page: serialization checks that the built-in hooks are the
original functions, and stops hydrating the page when one is replaced.

To record the JSON file again after a deliberate change, run this from
``packages/py/citry``::

    uv run --no-sync python -m tests.test_call_run_order --write

It also prints each case's summary line; paste any changed line into
``CASES``. A changed record is a changed
contract: say in the pull request why the order had to change.
"""

from __future__ import annotations

import contextvars
import dataclasses
import inspect
import itertools
import json
import logging
import os
import re
import subprocess
import sys
import threading
import time
import traceback
from contextlib import contextmanager
from pathlib import Path
from types import CodeType, FrameType
from typing import TYPE_CHECKING, Any

import pytest

from citry import Citry, Component, ComponentLike
from citry._vue import direct
from citry._vue.leaf_program import LeafProgramNode
from citry._vue.serialization import hydration_admission
from citry.extension import Extension
from citry.util.html import Markup
from citry.util.logger import _ensure_trace_level, logger

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

# Stands for "no value" when a context variable is missing from a context.
_UNSET = object()

# Strict CSP needs a nonce; a fixed one keeps the case the same between runs.
NONCE = "orderlogfixednonce"

# Each loop case is serialized as the hydrated document and as static HTML.
LOOP_OUTPUTS: dict[str, dict[str, Any]] = {
    "hydrated": {},
    "static": {"deps_strategy": "simple"},
}
# The page cases add every other output kind ``serialize()`` offers, because
# each one calls its own hooks.
PAGE_OUTPUTS: dict[str, dict[str, Any]] = {
    "hydrated": {},
    "ssr_false": {"ssr": False},
    "static": {"deps_strategy": "simple"},
    "fragment": {"deps_strategy": "fragment"},
    "hydration_declined": {"deps_position": "append"},
    "csp": {"security_csp": "strict", "csp_nonce": NONCE},
}


# ---------------------------------------------------------------------------
# Recording
# ---------------------------------------------------------------------------


class _Recorder:
    """Collect the calls one case makes, in order."""

    def __init__(self) -> None:
        self.entries: list[str] = []
        self._frames: list[object] = []
        # Who the last entry's calls were made on, while more calls can join it.
        self._last_subject: str | None = None

    def add(self, entry: str) -> None:
        """Record an event that stands alone, such as one call of the id generator."""
        self.entries.append(entry)
        self._last_subject = None

    def call(self, subject: str, call: str) -> None:
        """Record one call made on ``subject``, on the same line as the calls just before it on that subject."""
        # Consecutive calls on one subject share a line, in call order, which
        # keeps the record short without losing any call or its position.
        if self._last_subject == subject:
            self.entries[-1] += f", {call}"
            return
        self.entries.append(f"{subject}: {call}")
        self._last_subject = subject

    def callback(self, subject: str, method: str) -> None:
        """Record a user data method or hook, with the execution frame it ran in."""
        # The frame shows which slot fill call a callback ran inside; a
        # renderer that ran a row outside the fill its tag sits in would
        # show a different label.
        self.call(subject, f"{method} ({self._frame_label()})")

    def hook(self, hook: str, subject: str, extension: str) -> None:
        """Record one extension's call of a hook, made for the component named in ``subject``."""
        self.call(f"hook {hook}{subject}", extension)

    def take(self) -> list[str]:
        taken = list(self.entries)
        self.entries.clear()
        self._last_subject = None
        return taken

    def _frame_label(self) -> str:
        frame = direct.active_execution()
        if frame is None:
            return "no frame"
        # Compared by identity: two equal frames are still two separate fill calls.
        for index, seen in enumerate(self._frames):
            if seen is frame:
                return f"frame {index}"
        self._frames.append(frame)
        return f"frame {len(self._frames) - 1}"


# Code flags of functions whose frame starts again on every resume.
_RESUMABLE = inspect.CO_GENERATOR | inspect.CO_COROUTINE | inspect.CO_ASYNC_GENERATOR

# The manager calls ``on_serialize`` through a private method, which the
# dependencies extension overrides without calling ``on_serialize`` at all, so
# that private method is the serialize hook call to record.
_HOOK_ALIASES = {"_on_serialize_internal": "on_serialize"}


def _hook_labels(engine: Citry) -> dict[CodeType, tuple[str, str]]:
    """Map the code of every hook this engine's extensions define to its hook name and class name."""
    labels: dict[CodeType, tuple[str, str]] = {}
    for extension in engine.extensions._extensions:
        for owner in type(extension).__mro__:
            # The base class's hooks do nothing of their own, or only pass the
            # call on to an overriding hook, which is recorded itself.
            if owner in {Extension, object}:
                continue
            for name, value in vars(owner).items():
                if name not in _HOOK_ALIASES and not (
                    name.startswith("on_") or name in {"prepare_browser_render", "browser_plugin"}
                ):
                    continue
                function = getattr(value, "__func__", value)
                code = getattr(function, "__code__", None)
                if not isinstance(code, CodeType):
                    continue
                label = (_HOOK_ALIASES.get(name, name), owner.__name__)
                # The profiler sees code, not names: a generator or coroutine
                # would log each resume, and one function under two names would
                # get one label. Neither happens today, so fail loudly if a hook
                # starts to.
                assert not code.co_flags & _RESUMABLE, f"{label} is a generator or coroutine"
                assert labels.get(code, label) == label, f"{label} shares its code with {labels[code]}"
                labels[code] = label
    return labels


def _hook_subject(frame: FrameType) -> str:
    """Name the component a hook was called for, read from its context argument."""
    code = frame.f_code
    # A hook takes ``(self, ctx)``; ``browser_plugin`` takes only ``self``.
    if code.co_argcount < 2:
        return ""
    ctx = frame.f_locals.get(code.co_varnames[1])
    # A merge names both sides: the component whose template wrote the
    # merged part (for a slot fill, the one that wrote the fill), and the
    # component it merges into.
    child_context = getattr(ctx, "child_context", None)
    if child_context is not None:
        child = type(getattr(child_context, "component", None)).__name__
        parent = type(getattr(getattr(ctx, "parent_context", None), "component", None)).__name__
        return f" {child} into {parent}"
    component = getattr(ctx, "component", None)
    if component is not None:
        return f" {type(component).__name__}"
    component_class = getattr(ctx, "component_class", None)
    if isinstance(component_class, type):
        return f" {component_class.__name__}"
    return ""


@contextmanager
def _recording_hooks(engine: Citry, recorder: _Recorder) -> Iterator[None]:
    """Record each extension hook call made on this thread while the block runs."""
    labels = _hook_labels(engine)

    def profile(frame: FrameType, event: str, _arg: object) -> None:
        # "call" also fires when a generator resumes; _hook_labels rejects generators.
        if event == "call":
            label = labels.get(frame.f_code)
            if label is not None:
                recorder.hook(label[0], _hook_subject(frame), label[1])

    previous = sys.getprofile()
    sys.setprofile(profile)
    try:
        yield
    finally:
        sys.setprofile(previous)


@contextmanager
def _collecting_trace(*, enabled: bool) -> Iterator[list[str]]:
    """Collect Citry's TRACE log lines while the block runs, when the case asks for them."""
    lines: list[str] = []
    if not enabled:
        yield lines
        return

    class Collect(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            lines.append(_portable(record.getMessage()))

    handler = Collect(level=1)
    previous_level = logger.level
    logger.addHandler(handler)
    logger.setLevel(_ensure_trace_level())
    try:
        yield lines
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)


# A class id is the class name plus a hash of its import path, and the
# import path depends on how pytest imported this file.
_CLASS_ID = re.compile(r"\b([A-Z][A-Za-z]*)_[0-9a-f]{6}\b")


def _portable(text: str) -> str:
    """Remove what differs between checkouts and platforms: this file's path and class id hashes."""
    # A KeyError's text is the repr of its message, which doubles backslashes on Windows.
    for path in (__file__, __file__.replace("\\", "\\\\")):
        text = text.replace(path, "<this file>")
    return _CLASS_ID.sub(r"\1_<hash>", text)


def _text(error: BaseException) -> str:
    try:
        return _portable(str(error))
    except Exception as failure:  # noqa: BLE001 - a message that cannot be made is itself the record
        return f"<str() raised {type(failure).__name__}>"


def _error_record(error: BaseException) -> dict[str, Any]:
    """Describe an error by what a caller can see: type, text, component path, innermost frame and chain."""
    chain: list[str] = []
    current = error
    # Follow the cause, else the context, and mark a context Python does not
    # print because ``raise ... from None`` set ``__suppress_context__``. Six
    # links are more than any case makes, and keep a cycle from looping.
    while len(chain) < 6:
        if current.__cause__ is not None:
            current, link = current.__cause__, "cause"
        elif current.__context__ is not None:
            link = "context (hidden)" if current.__suppress_context__ else "context"
            current = current.__context__
        else:
            break
        chain.append(f"{link} {type(current).__name__}: {_text(current)}")
    return {
        "type": type(error).__name__,
        "message": _text(error),
        "components": getattr(error, "_components", None),
        "innermost": traceback.extract_tb(error.__traceback__)[-1].name,
        "nesting_limit": getattr(error, "_citry_nesting_limit", None),
        "chain": chain,
    }


# ---------------------------------------------------------------------------
# The pages
# ---------------------------------------------------------------------------

# The list component's template per case; every other case uses "default".
_LIST_TEMPLATES = {
    "default": """
        <section>
          <c-Row
            c-for="row in rows"
            #c-key="row['key']"
            c-row="row"
          />
        </section>
    """,
    "two_runs_with_sibling": """
        <section>
          <c-Row
            c-for="row in rows[:2]"
            #c-key="row['key']"
            c-row="row"
          />
          <c-Plain label="between" />
          <c-Row
            c-for="row in rows[2:]"
            #c-key="row['key']"
            c-row="row"
          />
        </section>
    """,
    "run_in_slot_fill": """
        <section>
          <c-Wrapper>
            <c-Row
              c-for="row in rows"
              #c-key="row['key']"
              c-row="row"
            />
          </c-Wrapper>
        </section>
    """,
    # The inner loop is an attribute value inside single quotes, so its tag
    # stays on one line. Card prints the nested template twice, so its rows
    # render once for each print.
    "nested_template_printed_twice": """
        <section>
          <c-Card c-body='<c-Row c-for="row in rows" #c-key="row" c-row="row" />' />
        </section>
    """,
    "nested_runs": """
        <section>
          <div c-for="group in [rows[:2], rows[2:]]">
            <c-Row
              c-for="row in group"
              #c-key="row['key']"
              c-row="row"
            />
          </div>
        </section>
    """,
    "ordinary_run_beside_rows": """
        <section>
          <c-Plain
            c-for="row in rows[:2]"
            #c-key="row['key']"
            c-label="row['title']"
          />
          <c-Row
            c-for="row in rows[2:]"
            #c-key="row['key']"
            c-row="row"
          />
        </section>
    """,
    "leaf_components_beside_rows": """
        <section>
          <c-Plain label="first" />
          <c-Plain label="second" />
          <c-Row
            c-for="row in rows"
            #c-key="row['key']"
            c-row="row"
          />
          <c-Plain label="third" />
        </section>
    """,
}
_LIST_TEMPLATES["run_in_slot_fill_rows_call_child"] = _LIST_TEMPLATES["run_in_slot_fill"]
_LIST_TEMPLATES["rows_in_two_fills"] = """
    <section>
      <c-Pair>
        <c-fill name="default">
          <c-Row
            c-for="row in rows[:2]"
            #c-key="row['key']"
            c-row="row"
          />
        </c-fill>
        <c-fill name="second">
          <c-Row
            c-for="row in rows[2:]"
            #c-key="row['key']"
            c-row="row"
          />
        </c-fill>
      </c-Pair>
      <c-Wrapper>
        <c-Row
          c-for="row in rows[:1]"
          #c-key="row['key']"
          c-row="row"
        />
      </c-Wrapper>
    </section>
"""

# The cases whose list component has an ``on_render``; the ones in
# _SWALLOWING_CASES replace a failed output with their own.
_ON_RENDER_CASES = {"parent_on_render", "row_lowers_depth_limit_under_boundary", "boundary_swallows_row_error"}
_SWALLOWING_CASES = {"row_lowers_depth_limit_under_boundary", "boundary_swallows_row_error"}
# The cases whose rows call a child component from their template.
_CHILD_CALL_CASES = {"rows_call_child", "child_of_row_raises", "run_in_slot_fill_rows_call_child"}
# The cases that write the rows straight into the page's own template.
_ROOT_CASES = {"rows_in_root", "rows_in_root_outputs"}


@dataclasses.dataclass
class _Case:
    """One built page: its engine, its root class and inputs, and how to serialize it."""

    engine: Citry
    # A component class. Its metaclass makes a call return the element to
    # render, which a static type of the class cannot express.
    page: Any
    rows: list[Any]
    outputs: dict[str, dict[str, Any]]
    # Restarts the id counter on the calling thread, so each render makes the same ids.
    restart_ids: Callable[[], None]
    traced: bool = False


class _BadMessage:
    """An error argument whose text cannot be made: ``str()`` raises while handling another error."""

    def __str__(self) -> str:  # noqa: PLE0307 - it always raises, which is the point
        try:
            raise KeyError("inner")
        except KeyError:
            raise TypeError("the message failed") from None

    def __repr__(self) -> str:
        return "_BadMessage()"


def _build(name: str, recorder: _Recorder) -> _Case:
    """
    Build the page for one case.

    The page is ``RowPage`` > ``RowList`` (rendered on the ordinary
    component path, not as ``simple="vue"``) > a ``c-for`` of four
    ``Row`` components (``simple="vue"``), keyed ``a0`` to ``a3``. Each case
    changes one thing; ``CASES`` lists the cases and the module docstring
    says what the record holds.
    """
    ids = threading.local()

    def restart_ids() -> None:
        ids.counter = itertools.count()

    def make_id() -> str:
        counter = getattr(ids, "counter", None)
        if counter is None:
            counter = ids.counter = itertools.count()
        value = next(counter)
        recorder.add("id")
        # Ids 0 and 1 go to RowPage and RowList, so id 4 is row a2's.
        if name == "id_generator_raises" and value == 4:
            raise LookupError("id generator failed")
        if name == "id_invalid" and value == 4:
            return "not a valid id!"
        return f"r{value}"

    options: dict[str, Any] = {}
    if name == "too_deep":
        options["max_component_depth"] = 2

    class BrowserHook(Extension):
        name = "order_log_browser_hook"

        def prepare_browser_render(self, ctx: Any) -> None:
            return None

    if name == "browser_hook_extension":
        options["extensions"] = [BrowserHook]
    engine = Citry(autodiscover=False, id_generator=make_id, **options)
    # The hydrated document links the page's scripts under the engine's URL
    # prefix; an engine outside a web app has none, and building a URL raises.
    engine.set_mounted_prefix("/citry")
    # Classes and values a callback reaches after the page is built.
    built: dict[str, Any] = {}

    class Mixin:
        marker = 1

    def row_event(kwargs: Any) -> None:
        """Do what this case asks of a row's template_data: raise, or change engine, class or row state."""
        key = kwargs.row["key"] if isinstance(kwargs.row, dict) else None
        if key == "a2":
            if name in {"template_data_raises", "boundary_swallows_row_error"}:
                raise ValueError("row a2 template_data failed")
            if name == "error_message_raises":
                raise ValueError(_BadMessage())
            if name == "keyboard_interrupt":
                raise KeyboardInterrupt("row a2 interrupted")
        if key == "a3" and name == "ordinary_path_row_raises":
            raise ValueError("row a3 failed on the ordinary path")
        if key != "a1":
            return
        if name in {"row_lowers_depth_limit", "row_lowers_depth_limit_under_boundary"}:
            engine.settings = dataclasses.replace(engine.settings, max_component_depth=2)
        elif name in {"row_registers_component_with_messages", "ordinary_path_row_raises"}:
            # A component with messages makes the i18n extension send the
            # later rows down the ordinary component path.
            class Messages(Component):
                citry = engine

                class I18n:
                    messages_locale = "en-US"

                template = """
                    <p>m</p>
                """
                messages = """
                    hello = Hello
                """

            built["messages"] = Messages
        elif name == "row_sets_id_generator":
            other = itertools.count(100)

            def other_id() -> str:
                recorder.add("id other")
                return f"o{next(other)}"

            engine.id_generator = other_id
        elif name == "row_registers_dict_as_component_like":
            ComponentLike.register(dict)
        elif name == "row_makes_class_transparent":
            built["Row"].transparent = True
        elif name == "row_writes_plain_mixin_base":
            Mixin.marker = 2
        elif name == "row_unregisters_class":
            engine.unregister(built["Row"])
        elif name == "row_renders_another_page":
            html = built["InnerPage"](rows=built["inner_rows"]).render().serialize(deps_strategy="simple")
            recorder.add(f"nested render wrote {html.count('<article')} rows")
        elif name == "row_changes_next_row":
            following = built["rows"][2]
            following["title"] = "changed by row a1"
            following["key"] = "changed-key"
            following["attrs"]["data-changed"] = "yes"

    def row_label(kwargs: Any) -> str:
        row = kwargs.row
        return f"Row {row.get('key')}" if isinstance(row, dict) else "Row ?"

    @dataclasses.dataclass
    class RowKwargs:
        row: Any

        def __post_init__(self) -> None:
            key = self.row.get("key") if isinstance(self.row, dict) else None
            recorder.call(f"Row {key}", "Kwargs")
            if name == "kwargs_post_init_raises" and key == "a2":
                raise ValueError("row a2 kwargs failed")

    def row_template_data(kwargs: Any, _slots: Any) -> dict[str, Any]:
        recorder.callback(row_label(kwargs), "template_data")
        row_event(kwargs)
        return {"attrs": kwargs.row["attrs"], "title": kwargs.row["title"]}

    def row_js_data(kwargs: Any, _slots: Any) -> dict[str, Any] | None:
        recorder.callback(row_label(kwargs), "js_data")
        if name == "row_js_data" and kwargs.row.get("key") == "a1":
            return {"note": "x"}
        return None

    def row_css_data(kwargs: Any, _slots: Any) -> dict[str, Any] | None:
        recorder.callback(row_label(kwargs), "css_data")
        if name == "row_css_data" and kwargs.row.get("key") == "a1":
            return {"accent": "red"}
        return None

    @dataclasses.dataclass
    class RowTemplateData:
        attrs: dict[str, Any]
        title: str

        def __post_init__(self) -> None:
            recorder.add(f"Row.TemplateData built for {self.title}")

    @dataclasses.dataclass
    class RowJsData:
        note: str | None = None

        def __post_init__(self) -> None:
            recorder.add("Row.JsData built")

    @dataclasses.dataclass
    class RowCssData:
        accent: str | None = None

        def __post_init__(self) -> None:
            recorder.add("Row.CssData built")

    row_bases: tuple[type, ...] = (Mixin, Component) if name == "row_writes_plain_mixin_base" else (Component,)

    class Row(*row_bases):  # type: ignore[misc]
        citry = engine
        simple = "vue"
        Kwargs = RowKwargs
        if name == "data_schemas":
            TemplateData = RowTemplateData
            JsData = RowJsData
            CssData = RowCssData
        template_data = staticmethod(row_template_data)
        js_data = staticmethod(row_js_data)
        css_data = staticmethod(row_css_data)
        if name in _CHILD_CALL_CASES:
            template = """
                <article c-bind="attrs"><c-Leaf c-label="title" /></article>
            """
        else:
            template = """
                <article c-bind="attrs"><span>{{ title }}</span></article>
            """
        js = """
            $component({data(){return {open: true};}});
        """
        if name == "row_css_data":
            css = """
                article { color: var(--accent); }
            """

    built["Row"] = Row

    class Leaf(Component):
        citry = engine

        class Kwargs:
            label: str

        def template_data(self, kwargs: Any, _slots: Any) -> dict[str, Any]:
            recorder.callback(f"Leaf {kwargs.label}", "template_data")
            if name == "child_of_row_raises" and kwargs.label == "a 1":
                raise ValueError("the child of row a1 failed")
            return {"label": kwargs.label}

        template = """
            <b>{{ label }}</b>
        """

    class Plain(Component):
        citry = engine

        class Kwargs:
            label: str

        def template_data(self, kwargs: Any, _slots: Any) -> dict[str, Any]:
            recorder.callback(f"Plain {kwargs.label}", "template_data")
            return {"label": kwargs.label}

        template = """
            <p>{{ label }}</p>
        """

    class Card(Component):
        citry = engine

        class Kwargs:
            body: Any

        template = """
            <div>{{ body }}</div><aside>{{ body }}</aside>
        """

    class Wrapper(Component):
        citry = engine

        template = """
            <div class="wrap"><c-slot /></div>
        """

    class Pair(Component):
        citry = engine

        template = """
            <div class="pair"><c-slot /><hr /><c-slot name="second" /></div>
        """

    class RowList(Component):
        citry = engine

        class Kwargs:
            rows: list[Any]

        def template_data(self, kwargs: Any, _slots: Any) -> dict[str, Any]:
            recorder.callback("RowList", "template_data")
            return {"rows": kwargs.rows}

        if name in _ON_RENDER_CASES:

            def on_render(self) -> Any:
                recorder.callback("RowList", "on_render before the yield")
                _result, error = yield
                recorder.callback(
                    "RowList", f"on_render after the yield, error {type(error).__name__ if error else None}"
                )
                if error is not None and name in _SWALLOWING_CASES:
                    return Markup(f"<p>recovered from {type(error).__name__}</p>")  # noqa: S704 - an exception class name
                return None

        if name == "component_on_dependencies":

            @classmethod
            def on_dependencies(cls, scripts: list[Any], styles: list[Any]) -> None:
                recorder.callback("RowList", f"on_dependencies with {len(scripts)} scripts")

        template = _LIST_TEMPLATES.get(name, _LIST_TEMPLATES["default"])
        js = """
            $component({data(){return {open: true};}});
        """

    class RowPage(Component):
        citry = engine

        class Kwargs:
            rows: list[Any]

        def template_data(self, kwargs: Any, _slots: Any) -> dict[str, Any]:
            recorder.callback("RowPage", "template_data")
            return {"rows": kwargs.rows}

        if name in _ROOT_CASES:
            template = """
                <html><head></head><body><main>
                  <c-Row
                    c-for="row in rows"
                    #c-key="row['key']"
                    c-row="row"
                  />
                </main></body></html>
            """
        else:
            template = """
                <html><head></head><body><main><c-RowList c-rows="rows" /></main></body></html>
            """

    if name == "row_renders_another_page":

        class InnerPage(Component):
            citry = engine

            class Kwargs:
                rows: list[Any]

            template = """
                <div><c-RowList c-rows="rows" /></div>
            """

        built["InnerPage"] = InnerPage
        built["inner_rows"] = [
            {"key": f"n{index}", "attrs": {"id": f"n-{index}"}, "title": f"n {index}"} for index in range(2)
        ]

    class LoggedKey:
        """A key whose conversion to text is recorded."""

        def __init__(self, value: str) -> None:
            self.value = value

        def __str__(self) -> str:
            recorder.add(f"key str {self.value}")
            return self.value

    class SwapRow(dict[str, Any]):
        """A row whose key, when read for row a1, registers another class under the name Row."""

        def __getitem__(self, key: str) -> Any:
            if key == "key" and dict.__getitem__(self, "key") == "a1" and "swapped" not in built:
                built["swapped"] = True
                recorder.add("swap class")
                # The loop's class keeps a second name, so it stays registered
                # and its rows still render; only the name "Row" moves.
                engine.register(built["Row"], name="RowAlias")
                engine.unregister("Row")

                class OtherRow(Component):
                    citry = engine
                    simple = "vue"
                    Kwargs = RowKwargs
                    template_data = staticmethod(row_template_data)  # type: ignore[assignment]
                    template = """
                        <article c-bind="attrs"><em>{{ title }}</em></article>
                    """

                engine.register(OtherRow, name="Row")
            return dict.__getitem__(self, key)

    rows: list[Any] = [
        {"key": f"a{index}", "attrs": {"id": f"a-{index}"}, "title": f"a {index}"} for index in range(4)
    ]
    if name == "empty_loop":
        rows = []
    if name == "traced_input_fault":
        del rows[2]["key"]
    if name == "key_str_logged":
        for row in rows:
            row["key"] = LoggedKey(row["key"])
    if name == "class_swapped_mid_walk":
        rows = [SwapRow(row) for row in rows]
    built["rows"] = rows
    # The first lookup on an engine creates its built-in components, which
    # calls the class hooks once per built-in. Doing it here keeps that
    # one-time setup out of the render's record.
    engine.get("Row")

    page_case = name in {
        "outputs",
        "nested_runs",
        "ordinary_run_beside_rows",
        "leaf_components_beside_rows",
        "rows_in_root_outputs",
        "component_on_dependencies",
        "browser_hook_extension",
    }
    return _Case(
        engine=engine,
        page=RowPage,
        rows=rows,
        outputs=PAGE_OUTPUTS if page_case else LOOP_OUTPUTS,
        restart_ids=restart_ids,
        traced=name in {"traced", "traced_input_fault"},
    )


def _run_case(name: str) -> dict[str, Any]:
    """Render and serialize one case in a fresh copy of the current context and return its record."""
    # A context variable one case leaves set must fail that case, not the
    # next one, so each case starts from a copy that it alone can change.
    return contextvars.copy_context().run(_record_case, name)


def _record_case(name: str) -> dict[str, Any]:
    recorder = _Recorder()
    case = _build(name, recorder)
    record: dict[str, Any] = {}
    context_before = dict(contextvars.copy_context().items())
    case.restart_ids()
    with _collecting_trace(enabled=case.traced) as trace, _recording_hooks(case.engine, recorder):
        try:
            rendered = case.page(rows=case.rows).render()
        except BaseException as error:  # noqa: BLE001 - KeyboardInterrupt included; the error is the record
            record["render"] = recorder.take()
            record["error"] = _error_record(error)
        else:
            record["render"] = recorder.take()
            for label, options in case.outputs.items():
                try:
                    rendered.serialize(**options)
                except Exception as error:  # noqa: BLE001 - the error is the record
                    record[label] = {"log": recorder.take(), "error": _error_record(error)}
                    continue
                record[label] = {"log": recorder.take()}
                if label == "hydrated":
                    # None when the page hydrated, the reason when it declined, or
                    # "no decision" when serialize recorded none.
                    admission = hydration_admission(rendered)
                    record[label]["declined"] = admission.reason if admission is not None else "no decision"
    if case.traced:
        record["trace"] = trace
    # A render, even one that failed, must reset every context variable it set
    # (the active slot fill call, the value context and the others), or the next
    # render on this thread would start inside the old one.
    context_after = dict(contextvars.copy_context().items())
    record["context_variables_left_changed"] = sorted(
        variable.name
        for variable in context_before.keys() | context_after.keys()
        if context_before.get(variable, _UNSET) is not context_after.get(variable, _UNSET)
    )
    return record


# ---------------------------------------------------------------------------
# The cases and the tests
# ---------------------------------------------------------------------------

# Every case, with what it changes on the page. "Row aN" is the row keyed aN.
CASES: dict[str, tuple[str, str]] = {
    # The page as built, and its loop with no rows.
    "plain": (
        "the page as built",
        "Row a0, Row a1, Row a2, Row a3 -> rendered",
    ),
    "empty_loop": (
        "the loop has no rows",
        "no rows -> rendered",
    ),
    # A row fails partway, so later rows must not run.
    "template_data_raises": (
        "row a2's template_data raises",
        "Row a0, Row a1, Row a2 -> ValueError",
    ),
    "kwargs_post_init_raises": (
        "row a2's Kwargs __post_init__ raises",
        "Row a0, Row a1, Row a2 -> ValueError",
    ),
    "id_generator_raises": (
        "the id generator raises for row a2",
        "Row a0, Row a1 -> LookupError",
    ),
    "id_invalid": (
        "the id generator returns an invalid id for row a2",
        "Row a0, Row a1 -> ValueError",
    ),
    "keyboard_interrupt": (
        "row a2's template_data raises KeyboardInterrupt (no component path is added)",
        "Row a0, Row a1, Row a2 -> KeyboardInterrupt",
    ),
    "error_message_raises": (
        "row a2 raises an error whose str() raises when Citry adds the component path",
        "Row a0, Row a1, Row a2 -> TypeError",
    ),
    # The component depth limit, and on_render boundaries around the loop.
    "too_deep": (
        "the rows sit deeper than max_component_depth",
        "no rows -> RecursionError",
    ),
    "row_lowers_depth_limit": (
        "row a1 lowers max_component_depth, so row a2 is too deep",
        "Row a0, Row a1 -> RecursionError",
    ),
    "row_lowers_depth_limit_under_boundary": (
        "the same, under a RowList.on_render that tries to replace the output",
        "Row a0, Row a1 -> RecursionError",
    ),
    "boundary_swallows_row_error": (
        "row a2 raises and RowList.on_render replaces the output",
        "Row a0, Row a1, Row a2 -> rendered",
    ),
    "parent_on_render": (
        "RowList has an on_render that keeps the output",
        "Row a0, Row a1, Row a2, Row a3 -> rendered",
    ),
    # A row's callback changes engine, class or row state for the rows after it.
    "row_registers_component_with_messages": (
        "row a1 defines a component with messages, so Citry renders rows a2 and a3 as ordinary components",
        "Row a0, Row a1, Row a2, Row a3 -> rendered",
    ),
    "ordinary_path_row_raises": (
        "the same, and row a3 raises on the ordinary path",
        "Row a0, Row a1, Row a2, Row a3 -> ValueError",
    ),
    "row_sets_id_generator": (
        "row a1 replaces the engine's id generator",
        "Row a0, Row a1, Row a2, Row a3 -> rendered",
    ),
    "row_registers_dict_as_component_like": (
        "row a1 calls ComponentLike.register(dict) (runs in its own process)",
        "Row a0, Row a1, Row a2, Row a3 -> rendered",
    ),
    "row_writes_plain_mixin_base": (
        "row a1 writes to a plain mixin base class of Row",
        "Row a0, Row a1, Row a2, Row a3 -> rendered",
    ),
    "row_unregisters_class": (
        "row a1 unregisters Row",
        "Row a0, Row a1 -> KeyError",
    ),
    "row_makes_class_transparent": (
        "row a1 sets Row.transparent, so Citry rejects row a2 as a simple='vue' call",
        "Row a0, Row a1 -> TypeError",
    ),
    "row_renders_another_page": (
        "row a1 renders and serializes another page with a loop of rows",
        "Row a0, Row a1, Row n0, Row n1, Row a1, Row a2, Row a3 -> rendered",
    ),
    "row_changes_next_row": (
        "row a1 changes row a2's dict before row a2 reads it",
        "Row a0, Row a1, Row changed-key, Row a3 -> rendered",
    ),
    "class_swapped_mid_walk": (
        "reading row a1's key registers another class under the name Row",
        "Row a0, Row a1, Row a2, Row a3 -> rendered",
    ),
    "key_str_logged": (
        "each key is an object whose conversion to text is recorded",
        "Row a0, Row a1, Row a2, Row a3 -> rendered",
    ),
    # Rows with browser data, CSS data and data schemas.
    "row_js_data": (
        "row a1's js_data returns a value",
        "Row a0, Row a1, Row a2, Row a3 -> rendered",
    ),
    "row_css_data": (
        "Row has CSS and row a1's css_data returns a value",
        "Row a0, Row a1, Row a2, Row a3 -> rendered",
    ),
    "data_schemas": (
        "Row declares TemplateData, JsData and CssData",
        "Row a0, Row a1, Row a2, Row a3 -> rendered",
    ),
    # Rows that call a child, and loops placed somewhere other than RowList's own body.
    "rows_call_child": (
        "each row's template calls the Leaf component",
        "Row a0, Leaf a 0, Row a1, Leaf a 1, Row a2, Leaf a 2, Row a3, Leaf a 3 -> rendered",
    ),
    "child_of_row_raises": (
        "the Leaf that row a1 calls raises",
        "Row a0, Leaf a 0, Row a1, Leaf a 1 -> ValueError",
    ),
    "run_in_slot_fill": (
        "the loop sits in a slot fill that Wrapper renders",
        "Row a0, Row a1, Row a2, Row a3 -> rendered",
    ),
    "rows_in_two_fills": (
        "the loop is split over two fills of Pair, then a third loop sits in Wrapper's fill",
        "Row a0, Row a1, Row a2, Row a3, Row a0 -> rendered",
    ),
    "run_in_slot_fill_rows_call_child": (
        "the same, with rows that call Leaf",
        "Row a0, Leaf a 0, Row a1, Leaf a 1, Row a2, Leaf a 2, Row a3, Leaf a 3 -> rendered",
    ),
    "nested_template_printed_twice": (
        "the loop sits in a nested template that Card prints twice; each print renders the rows again",
        "Row a0, Row a1, Row a2, Row a3, Row a0, Row a1, Row a2, Row a3 -> rendered",
    ),
    "two_runs_with_sibling": (
        "two loops of Row with a Plain component between them",
        "Row a0, Row a1, Plain between, Row a2, Row a3 -> rendered",
    ),
    "rows_in_root": (
        "the loop sits in the page's own template",
        "Row a0, Row a1, Row a2, Row a3 -> rendered",
    ),
    # TRACE logging, which records its own lines.
    "traced": (
        "the page with Citry's TRACE logging on",
        "Row a0, Row a1, Row a2, Row a3 -> rendered",
    ),
    "traced_input_fault": (
        "row a2 has no key, with TRACE logging on",
        "no rows -> KeyError",
    ),
    # Pages serialized as every output kind, for the hooks serialize calls.
    "outputs": (
        "the page as built, serialized as every output kind",
        "Row a0, Row a1, Row a2, Row a3 -> rendered",
    ),
    "nested_runs": (
        "a loop inside a loop, so one Row tag renders two separate groups of rows",
        "Row a0, Row a1, Row a2, Row a3 -> rendered",
    ),
    "ordinary_run_beside_rows": (
        "a loop of the ordinary Plain component beside a loop of Row",
        "Plain a 0, Plain a 1, Row a2, Row a3 -> rendered",
    ),
    "leaf_components_beside_rows": (
        "ordinary Plain components before and after the loop",
        "Plain first, Plain second, Row a0, Row a1, Row a2, Row a3, Plain third -> rendered",
    ),
    "rows_in_root_outputs": (
        "the loop sits in the page's own template, serialized as every output kind",
        "Row a0, Row a1, Row a2, Row a3 -> rendered",
    ),
    "component_on_dependencies": (
        "RowList defines on_dependencies, which stops hydration",
        "Row a0, Row a1, Row a2, Row a3 -> rendered, hydration declined (custom-hooks)",
    ),
    "browser_hook_extension": (
        "an extra extension defines prepare_browser_render, and Citry declines to hydrate the page",
        "Row a0, Row a1, Row a2, Row a3 -> rendered, hydration declined (compile-error)",
    ),
}

# ComponentLike.register() lasts for the whole process, so this case runs in
# a fresh interpreter and cannot change the tests that run after it.
_OWN_PROCESS_CASES = {"row_registers_dict_as_component_like"}

_EXPECTED_PATH = Path(__file__).parent / "fixtures" / "call_run_order.json"
EXPECTED: dict[str, Any] = json.loads(_EXPECTED_PATH.read_text(encoding="utf-8"))


# The data methods whose subjects the summary lists; RowPage and RowList run in every case.
_SUMMARY_SUBJECTS = ("Row ", "Leaf ", "Plain ")


def _summary(record: dict[str, Any]) -> str:
    """
    Say in one line which rows and child components ran, in order, and how the case ended.

    ``CASES`` holds this line for every case, so a reader can see what a case
    locks without opening the JSON file.
    """
    subjects: list[str] = []
    for entry in record["render"]:
        subject = entry.partition(":")[0]
        # Consecutive calls on one subject count once; a later return to it counts again.
        if subject.startswith(_SUMMARY_SUBJECTS) and (not subjects or subjects[-1] != subject):
            subjects.append(subject)
    ran = ", ".join(subjects) or "no rows"
    if "error" in record:
        return f"{ran} -> {record['error']['type']}"
    failed = [label for label, part in record.items() if isinstance(part, dict) and "error" in part]
    ending = f"serialize failed for {', '.join(failed)}" if failed else "rendered"
    declined = record.get("hydrated", {}).get("declined")
    if declined is not None:
        ending += f", hydration declined ({declined})"
    return f"{ran} -> {ending}"


def _assert_matches(case: str, record: dict[str, Any]) -> None:
    assert _summary(record) == CASES[case][1]
    expected = EXPECTED[case]
    assert list(record) == list(expected)
    # Compared one part at a time, so a failure shows the list that differs.
    for part, value in expected.items():
        assert record[part] == value, f"{case}: {part}"


def _record_in_own_process(case: str, render_path: str = "rust") -> dict[str, Any]:
    """Run one case in a fresh interpreter, for a change that would outlive the test."""
    script = """
import json, sys
from tests.test_call_run_order import _run_case
print(json.dumps(_run_case(sys.argv[1])))
"""
    result = subprocess.run(
        [sys.executable, "-c", script, case],
        cwd=Path(__file__).parents[1],
        capture_output=True,
        text=True,
        check=False,
        # The new interpreter decides its render path from this variable.
        env={**os.environ, "CITRY_NATIVE_RENDER": "1" if render_path == "rust" else "0"},
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.splitlines()[-1])


def test_every_case_has_a_locked_record() -> None:
    assert list(EXPECTED) == list(CASES)


# Cases whose rows never reach the native row read: no rows, an error
# before the first row, rows whose js_data() returns values, rows that call
# children, and a loop that fails on a missing key before any row is read.
_NO_NATIVE_ROWS = {
    "empty_loop",
    "too_deep",
    "data_schemas",
    "rows_call_child",
    "child_of_row_raises",
    "run_in_slot_fill_rows_call_child",
    "traced_input_fault",
}


@pytest.mark.parametrize("case", [case for case in CASES if case not in _OWN_PROCESS_CASES])
def test_render_calls_user_code_and_hooks_in_the_locked_order(
    case: str, render_path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Count the rows Rust reads, so the Rust case cannot pass by quietly
    # taking the Python path.
    read = LeafProgramNode.read_native_row
    rows_read: list[object] = []

    def counting_read(self: LeafProgramNode, variables: dict[str, object]) -> object:
        row = read(self, variables)
        if row is not None:
            rows_read.append(row)
        return row

    monkeypatch.setattr(LeafProgramNode, "read_native_row", counting_read)
    _assert_matches(case, _run_case(case))
    if render_path == "python" or case in _NO_NATIVE_ROWS:
        assert rows_read == []
    else:
        assert rows_read


@pytest.mark.parametrize("case", sorted(_OWN_PROCESS_CASES))
def test_process_wide_change_keeps_the_locked_order(case: str, render_path: str) -> None:
    _assert_matches(case, _record_in_own_process(case, render_path))


def _render_in_two_threads(render_once: Callable[[], dict[str, str]]) -> tuple[list[dict[str, str]], bool]:
    """Start two threads together, let each render three times, and say whether their renders overlapped."""
    outputs: list[dict[str, str]] = []
    spans: dict[int, list[tuple[int, int]]] = {0: [], 1: []}
    errors: list[BaseException] = []
    barrier = threading.Barrier(2)

    def worker(index: int) -> None:
        try:
            barrier.wait()
            for _ in range(3):
                begin = time.perf_counter_ns()
                outputs.append(render_once())
                spans[index].append((begin, time.perf_counter_ns()))
        except BaseException as error:  # noqa: BLE001 - reported by the main thread
            errors.append(error)

    threads = [threading.Thread(target=worker, args=(index,)) for index in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []
    overlapped = any(
        first_begin < second_end and second_begin < first_end
        for first_begin, first_end in spans[0]
        for second_begin, second_end in spans[1]
    )
    return outputs, overlapped


def test_two_threads_rendering_together_write_the_same_html(render_path: str) -> None:
    """
    Two threads render the page at the same time and get the bytes one render gets alone.

    The calls of the two threads interleave, so this case compares only the
    HTML. Each thread restarts its own id counter for every render, which a
    counter shared by both threads could not do. The test also checks that
    the threads' renders really overlapped in time.
    """
    del render_path  # the fixture switches the render path
    recorder = _Recorder()
    case = _build("plain", recorder)

    def render_once() -> dict[str, str]:
        case.restart_ids()
        rendered = case.page(rows=case.rows).render()
        return {label: rendered.serialize(**options) for label, options in LOOP_OUTPUTS.items()}

    alone = render_once()
    # A short switch interval makes the threads trade turns inside a render.
    switch_interval = sys.getswitchinterval()
    sys.setswitchinterval(1e-5)
    try:
        # A few attempts, because two threads that never overlap prove nothing.
        for _attempt in range(5):
            outputs, overlapped = _render_in_two_threads(render_once)
            assert len(outputs) == 6
            assert all(output == alone for output in outputs)
            if overlapped:
                break
        else:
            pytest.fail("the two threads' renders never overlapped in time")
    finally:
        sys.setswitchinterval(switch_interval)


def _write_expected() -> None:
    """Record every case on the current code, write the JSON file, and print each case's summary."""
    records = {case: _record_in_own_process(case) if case in _OWN_PROCESS_CASES else _run_case(case) for case in CASES}
    _EXPECTED_PATH.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for case, record in records.items():
        print(f"{case}: {_summary(record)}")  # noqa: T201 - the summaries go into CASES by hand


if __name__ == "__main__":
    if sys.argv[1:] != ["--write"]:
        sys.exit("usage: python -m tests.test_call_run_order --write")
    _write_expected()
