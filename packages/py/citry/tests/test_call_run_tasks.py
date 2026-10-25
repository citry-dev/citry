"""
One render-queue task per call run: a ``c-for`` loop's ``simple = "vue"`` rows render in one task.

A call run is the rows one ``<c-for>`` places at one component call site.
The loop records such rows in one ``_DeferredRun``, with one
``_DeferredRunRow`` at each row's position in the parts list, and the
render queue gives adjacent rows one task (``_RunTask``), which renders
them in order. This runs on every interpreter, on both render paths.

``tests/test_call_run_order.py`` locks the order of callbacks and hooks on
both paths, and the rest of the suite locks the output bytes. This file
checks what those cannot show:

- that the run tasks really place the rows, because byte equality alone
  would pass if every loop quietly fell back to one task per row;
- the early exits and list edits that no page in ``test_call_run_order.py``
  reaches. The position-gone cases check the error and calls directly.
  The cases under "Cases compared with one task per row" render the page
  a second time with one task per row, because Citry has no switch for
  run tasks: no loop qualifies for a run (``ForNode._call_run_class``
  returns None). They compare the output or error and the calls the two
  renders made;
- what user code sees when a public route hands it a render whose rows
  are not placed yet.
"""

from __future__ import annotations

import itertools
from typing import TYPE_CHECKING, Any

import pytest

from citry import Citry, Component
from citry import component_render as cr
from citry._vue.capture import _validate_prepared_render
from citry.citry_render import CitryRender, DeferredComponent, _DeferredRun, _DeferredRunRow
from citry.extension import Extension
from citry.nodes import ForNode
from citry.util.html import Markup

from .test_native_render_rows import build_board, make_rows

if TYPE_CHECKING:
    from collections.abc import Callable


class _RunCounts:
    """Count the run tasks, their ordinary-path exits, the rows they placed, and the rows given their own task."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.tasks = 0
        self.rows_placed = 0
        self.ordinary_exits = 0
        self.own_tasks = 0
        run_rows = cr._run_rows
        place_run_part = cr._place_run_part
        render_leaf = cr._render_simple_vue_leaf

        def counting_run_rows(task: Any) -> Any:
            self.tasks += 1
            result = run_rows(task)
            self.ordinary_exits += result is not None and result[0] == cr._RUN_EXIT_ORDINARY
            return result

        def counting_place(*args: Any) -> bool:
            placed = place_run_part(*args)
            # The ordinary-path exit places a deferred component, not a record.
            self.rows_placed += placed and type(args[3]) is not DeferredComponent
            return placed

        def counting_leaf(element: Any, parent_context: Any) -> Any:
            # Every deferred component passes through here; only rows count.
            self.own_tasks += element.comp_cls.simple == "vue"
            return render_leaf(element, parent_context)

        monkeypatch.setattr(cr, "_run_rows", counting_run_rows)
        monkeypatch.setattr(cr, "_place_run_part", counting_place)
        monkeypatch.setattr(cr, "_render_simple_vue_leaf", counting_leaf)


@pytest.mark.parametrize("in_root", [False, True], ids=["child_rows", "root_rows"])
def test_run_tasks_place_every_row_of_the_board(
    render_path: str, monkeypatch: pytest.MonkeyPatch, *, in_root: bool
) -> None:
    # The board at 140 rows: five phases of 28 rows (child_rows), or one
    # loop in the page's own template (root_rows). Each loop must become
    # one run task that places all its rows; a row given its own task means
    # a loop fell back.
    del render_path  # the fixture switches the render path
    counts = _RunCounts(monkeypatch)
    html = build_board(make_rows(140), phase_size=28, in_root=in_root).render().serialize()
    assert (counts.tasks, counts.rows_placed, counts.ordinary_exits, counts.own_tasks) == (
        1 if in_root else 5,
        140,
        0,
        0,
    )
    assert html.count("<article") == 140


# ---------------------------------------------------------------------------
# The test page
# ---------------------------------------------------------------------------

_ROW_TEMPLATE = """
    <p>{{ key }}</p>
"""

_ROW_WITH_LEAF_TEMPLATE = """
    <p>{{ key }}<c-Leaf c-key="key" /></p>
"""

_LIST_PAGE = """
    <main>
      <c-Row
        c-for="key in keys"
        #c-key="key"
        c-key="key"
      />
    </main>
"""

_FILL_PAGE = """
    <main>
      <c-Holder>
        <c-Row
          c-for="key in keys"
          #c-key="key"
          c-key="key"
        />
      </c-Holder>
    </main>
"""

_NESTED_TEMPLATE_PAGE = """
    <main>
      <c-Holder c-body='<c-Row c-for="key in keys" #c-key="key" c-key="key" />' />
    </main>
"""


class _PageCase:
    """
    Build a page whose loop places one row per key, and record the calls it makes.

    Each call of ``build`` makes a new engine with its own id counter, so
    two renders of the page mint the same ids.

    Args:
        page_template: One of the page templates above. ``_FILL_PAGE`` puts
            the loop in a fill of ``Holder``; ``_NESTED_TEMPLATE_PAGE``
            passes it to ``Holder`` as a nested template.
        keys: ``keys(case)`` returns the loop's iterable; it may run code
            between rows, and reach the row class as ``case.row_class``.
        on_row: Runs in each row's ``template_data`` as
            ``on_row(row_class, key)``.
        holder_template: ``Holder``'s template.
        holder_data: ``Holder``'s ``template_data(kwargs, slots)``.
        leaf_extra: Returns what ``Leaf`` prints after its key, as
            ``leaf_extra(kwargs)``; rows call ``Leaf`` only when it is given.
        extensions: Extension classes for the engine.
        boundary: Give the page an ``on_render`` that replaces its output
            when anything inside it raised.

    """

    def __init__(
        self,
        page_template: str = _LIST_PAGE,
        *,
        keys: Callable[[_PageCase], Any] = lambda _case: ["k0", "k1", "k2"],
        on_row: Callable[[Any, str], None] | None = None,
        holder_template: str = """
            <div><c-slot /></div>
        """,
        holder_data: Callable[[Any, Any], dict[str, Any]] | None = None,
        leaf_extra: Callable[[Any], object] | None = None,
        extensions: tuple[type[Extension], ...] = (),
        boundary: bool = False,
    ) -> None:
        self.page_template = page_template
        self.keys = keys
        self.on_row = on_row
        self.holder_template = holder_template
        self.holder_data = holder_data
        self.leaf_extra = leaf_extra
        self.extensions = extensions
        self.boundary = boundary
        self.calls: list[str] = []
        self.row_class: type[Component] | None = None

    def build(self) -> type[Component]:
        """Define the page's components on a new engine and return the page class."""
        counter = itertools.count()
        engine = Citry(autodiscover=False, extensions=list(self.extensions), id_generator=lambda: f"r{next(counter)}")
        engine.set_mounted_prefix("/citry")
        case = self
        case.calls = []

        class Row(Component):
            citry = engine
            simple = "vue"

            class Kwargs:
                key: str

            @staticmethod
            def template_data(kwargs: Any, _slots: Any) -> dict[str, Any]:
                case.calls.append(f"row {kwargs.key}")
                if case.on_row is not None:
                    case.on_row(Row, kwargs.key)
                return {"key": kwargs.key}

            template = _ROW_TEMPLATE if case.leaf_extra is None else _ROW_WITH_LEAF_TEMPLATE

        case.row_class = Row

        class Leaf(Component):
            citry = engine

            def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
                case.calls.append(f"leaf {kwargs['key']}")
                return {"key": kwargs["key"], "extra": "" if case.leaf_extra is None else case.leaf_extra(kwargs)}

            template = """
                <span>{{ key }}{{ extra }}</span>
            """

        class Holder(Component):
            citry = engine

            def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
                return {} if case.holder_data is None else case.holder_data(kwargs, slots)

            template = case.holder_template

        class Page(Component):
            citry = engine

            def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
                return {"keys": case.keys(case)}

            def on_render(self) -> Any:
                _result, error = yield
                if error is not None and case.boundary:
                    case.calls.append(f"boundary {type(error).__name__}")
                    return Markup("<p>recovered</p>")
                return None

            template = case.page_template

        return Page

    def render(self) -> tuple[object, list[str]]:
        """Render and serialize the page; return the HTML or the error, and the calls."""
        page = self.build()
        try:
            result: object = page().render().serialize(deps_strategy="fragment")
        except Exception as error:  # noqa: BLE001 - compared between the two renders
            result = (type(error).__name__, str(error))
        return result, self.calls


def _render_with_and_without_runs(
    case: _PageCase, monkeypatch: pytest.MonkeyPatch
) -> tuple[tuple[object, list[str]], tuple[object, list[str]], _RunCounts]:
    """
    Render ``case`` with run tasks and with one task per row; return both results and the first render's run counts.

    The second render makes no loop qualify for a run, which leaves the
    render queue with one task per row.
    """
    with monkeypatch.context() as patch:
        counts = _RunCounts(patch)
        with_runs = case.render()
    with monkeypatch.context() as patch:
        patch.setattr(ForNode, "_call_run_class", lambda _self, _context: None)
        without_runs = case.render()
    return with_runs, without_runs, counts


# ---------------------------------------------------------------------------
# A row's position gone from the parts list
# ---------------------------------------------------------------------------


def test_a_row_whose_position_is_gone_raises_past_every_boundary(
    render_path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # User code took the rows out of the parts list after the scan, before
    # row 0 was placed. A row's own task replaces its part after the row
    # rendered, outside the settle loop's error handling, so its
    # RuntimeError skips the on_render boundary. The run
    # task keeps that: row 0's callback runs once, then the same error
    # leaves the render.
    del render_path  # the fixture switches the render path
    run_rows = cr._run_rows

    def take_rows_out(task: Any) -> Any:
        task.parts[:] = ["gone" if type(part) is _DeferredRunRow else part for part in task.parts]
        return run_rows(task)

    monkeypatch.setattr(cr, "_run_rows", take_rows_out)
    case = _PageCase(boundary=True)
    result, calls = case.render()
    assert result == ("RuntimeError", "deferred part vanished from its .parts list before resolution")
    assert calls == ["row k0"]


def test_a_row_on_the_ordinary_path_whose_position_is_gone_raises_after_its_render(
    render_path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Row k0 defines a component with messages, so the i18n extension sends
    # row k1 down the ordinary component path. When k1's position is gone
    # by then, the replace after k1's render raises, as a row's own task's
    # replace does, past the boundary.
    del render_path  # the fixture switches the render path

    def define_messages(row_class: Any, key: str) -> None:
        if key != "k0":
            return

        class Messages(Component):
            citry = row_class.citry

            class I18n:
                messages_locale = "en-US"

            template = """
                <p>m</p>
            """
            messages = """
                hello = Hello
            """

    place_run_part = cr._place_run_part

    def drop_row(parts: list[Any], index: int, row: Any, new: Any) -> bool:
        # The ordinary-path exit places the row's deferred component; take
        # the row out of the list just before it does.
        if type(new) is DeferredComponent:
            parts[:] = ["gone" if part is row else part for part in parts]
        return place_run_part(parts, index, row, new)

    monkeypatch.setattr(cr, "_place_run_part", drop_row)
    case = _PageCase(keys=lambda _case: ["k0", "k1"], on_row=define_messages, boundary=True)
    result, calls = case.render()
    assert result == ("RuntimeError", "deferred part vanished from its .parts list before resolution")
    assert calls == ["row k0", "row k1"]


# ---------------------------------------------------------------------------
# Cases compared with one task per row
# ---------------------------------------------------------------------------


def _break_admission(row_class: Any, key: str) -> None:
    # A template_data that is not a static method makes the class fail
    # admission for every later row.
    if key == "k0":
        row_class.template_data = lambda _self, kwargs, _slots: {"key": kwargs.key}


def _messages_then_raise(row_class: Any, key: str) -> None:
    # Row k0 sends the later rows down the ordinary component path, where
    # row k1 raises.
    if key == "k0":

        class Messages(Component):
            citry = row_class.citry

            class I18n:
                messages_locale = "en-US"

            template = """
                <p>m</p>
            """
            messages = """
                hello = Hello
            """

    elif key == "k1":
        raise ValueError("row k1 failed")


def _keys_that_turn_row_into_a_selector(case: _PageCase) -> Any:
    # Code that runs between the loop's rows: before row k1 the class turns
    # into a dynamic selector, so k1 leaves the run, and row k0's task
    # rejects the class when it renders.
    yield "k0"
    row_class = case.row_class
    assert row_class is not None
    row_class._citry_dynamic_selector = True
    yield "k1"
    yield "k2"


def _hook_edit(edit: Callable[[list[Any]], None]) -> type[Extension]:
    """Build an extension whose ``on_slot_rendered`` applies ``edit`` to the list that holds the loop's rows."""

    class EditRows(Extension):
        name = "edit_unplaced_rows"

        def on_slot_rendered(self, ctx: Any) -> None:
            if isinstance(ctx.result, CitryRender):
                rows_list = _list_holding_rows(ctx.result)
                if rows_list is not None:
                    edit(rows_list)

    return EditRows


def _list_holding_rows(render: CitryRender) -> list[Any] | None:
    """Return the parts list inside ``render`` that holds the loop's unplaced rows."""
    pending = [render]
    while pending:
        current = pending.pop()
        if any(type(part) in {_DeferredRunRow, DeferredComponent} for part in current.parts):
            return current.parts
        pending.extend(part for part in current.parts if isinstance(part, CitryRender))
    return None


def _reverse(parts: list[Any]) -> None:
    parts.reverse()


def _delete_middle(parts: list[Any]) -> None:
    del parts[1]


def _repeat_first(parts: list[Any]) -> None:
    parts.insert(1, parts[0])


@pytest.mark.parametrize(
    ("edit", "expected"),
    [
        (_reverse, ["row k2", "row k1", "row k0"]),
        (_delete_middle, ["row k0", "row k2"]),
        # A row repeated in the list renders at both positions.
        (_repeat_first, ["row k0", "row k0", "row k1", "row k2"]),
    ],
    ids=["reverse", "delete_middle", "repeat_first"],
)
def test_a_hook_that_edits_the_unplaced_rows_gets_the_same_render(
    render_path: str, monkeypatch: pytest.MonkeyPatch, edit: Callable[[list[Any]], None], expected: list[str]
) -> None:
    # on_slot_rendered receives the fill's render before the queue places
    # its rows, and may reorder, drop or repeat entries of the rows' list.
    # Each row has its own object in the list, so the run task renders and
    # places exactly the rows one task per row would, in the same order.
    del render_path  # the fixture switches the render path
    case = _PageCase(_FILL_PAGE, extensions=(_hook_edit(edit),))
    with_runs, without_runs, counts = _render_with_and_without_runs(case, monkeypatch)
    assert with_runs == without_runs
    assert with_runs[1] == expected
    assert counts.tasks >= 1


def test_a_row_list_printed_again_after_its_first_row_renders_raises_before_rendering_a_row_twice(
    render_path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Holder keeps the fill's render, and row k0's child Leaf prints a copy
    # of it after k0 was placed. The copy holds the same placeholders for
    # k1 and k2, which the first scan already queued, so queueing them from
    # Leaf's output raises before any row renders twice, as with one task
    # per row.
    del render_path  # the fixture switches the render path
    kept: list[CitryRender] = []

    def holder_data(_kwargs: Any, slots: Any) -> dict[str, Any]:
        fill = slots["default"]()
        # One per render, so the second render starts from its own fill.
        kept[:] = [fill]
        return {"fill": fill}

    def leaf_extra(_kwargs: Any) -> object:
        if not kept:
            return ""
        fill = kept.pop()
        return CitryRender(parts=list(fill.parts), context=fill.context)

    case = _PageCase(
        _FILL_PAGE,
        holder_template="""
            <div>{{ fill }}</div>
        """,
        holder_data=holder_data,
        leaf_extra=leaf_extra,
    )
    with_runs, without_runs, counts = _render_with_and_without_runs(case, monkeypatch)
    assert with_runs == without_runs
    assert with_runs == (
        (
            "RuntimeError",
            "An error occurred while rendering components Page > Row > Leaf:\nThis content is printed in more "
            "than one place, but the components inside it have not rendered yet, so each would render twice. "
            "To show it in several places, pass the slot itself instead of calling it, or a component element "
            "such as MyComponent() instead of MyComponent().render(): each place that prints a slot or an "
            "element renders its own copy. In an on_render hook, place the output the hook received only once.",
        ),
        ["row k0", "leaf k0"],
    )
    assert counts.tasks >= 1


_CHANGING_CASES: dict[str, tuple[dict[str, Any], list[str]]] = {
    "breaks_admission": ({"on_row": _break_admission}, ["row k0"]),
    "ordinary_row_raises_under_boundary": (
        {"on_row": _messages_then_raise, "boundary": True},
        ["row k0", "row k1", "boundary ValueError"],
    ),
    "becomes_selector_mid_walk": ({"keys": _keys_that_turn_row_into_a_selector}, []),
}


@pytest.mark.parametrize("name", sorted(_CHANGING_CASES))
def test_rows_that_change_what_later_rows_do_render_as_with_one_task_per_row(
    render_path: str, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    # Each case changes the class or the engine while the rows render, and
    # must reach the same output or error after the same calls as one task
    # per row.
    del render_path  # the fixture switches the render path
    options, expected_calls = _CHANGING_CASES[name]
    with_runs, without_runs, counts = _render_with_and_without_runs(_PageCase(**options), monkeypatch)
    assert with_runs == without_runs
    assert with_runs[1] == expected_calls
    assert counts.tasks >= 1


def test_a_parts_list_edited_before_its_rows_are_placed_still_places_each_row(
    render_path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # User code inserts a part before the rows, so each row's remembered
    # index is off by one. A row's own task then finds its deferred
    # component by identity; the run task finds its row the same way.
    del render_path  # the fixture switches the render path
    edited: set[int] = set()
    run_rows = cr._run_rows
    replace_in_parts = cr._replace_in_parts

    def shift_rows(task: Any) -> Any:
        if id(task.parts) not in edited:
            edited.add(id(task.parts))
            task.parts.insert(0, "")
        return run_rows(task)

    def shift_deferred(parts: list[Any], index: int, target: object, new: Any) -> None:
        # With one task per row, the same edit, made before the first row is placed.
        if type(target) is DeferredComponent and id(parts) not in edited:
            edited.add(id(parts))
            parts.insert(0, "")
        replace_in_parts(parts, index, target, new)

    monkeypatch.setattr(cr, "_run_rows", shift_rows)
    monkeypatch.setattr(cr, "_replace_in_parts", shift_deferred)
    with_runs, without_runs, counts = _render_with_and_without_runs(_PageCase(), monkeypatch)
    assert with_runs == without_runs
    assert with_runs[1] == ["row k0", "row k1", "row k2"]
    assert str(with_runs[0]).count("<p") == 3
    assert len(edited) == 2
    assert counts.tasks == 1


# ---------------------------------------------------------------------------
# Public routes that can hold a render whose rows are not placed yet
# ---------------------------------------------------------------------------
#
# A render's parts list holds one _DeferredRunRow at each row's position
# until the render queue places the rows. Three public routes hand user
# code such a render before the queue reaches it: calling a
# template-defined slot, the on_slot_rendered hook, and a nested template
# passed as a kwarg. Each test checks what that code can see: one object
# per row, and str() raising the same error an unplaced deferred component
# raises.

_UNPLACED_ERROR = "unresolved DeferredComponent at serialize(); render() must process the queue first"


def _describe_unplaced(render: CitryRender) -> tuple[int, int, str]:
    """Return how many positions hold an unplaced row, how many objects sit there, and what ``str()`` raises."""
    rows_list = _list_holding_rows(render) or []
    rows = [part for part in rows_list if type(part) in {_DeferredRunRow, DeferredComponent}]
    try:
        str(render)
    except RuntimeError as error:
        raised = str(error)
    else:
        raised = "nothing"
    return len(rows), len({id(row) for row in rows}), raised


def test_a_slot_called_from_template_data_holds_the_unplaced_rows(render_path: str) -> None:
    del render_path  # the fixture switches the render path
    seen: list[tuple[int, int, str]] = []

    def holder_data(_kwargs: Any, slots: Any) -> dict[str, Any]:
        seen.append(_describe_unplaced(slots["default"]()))
        return {}

    result, _calls = _PageCase(_FILL_PAGE, holder_data=holder_data).render()
    assert seen == [(3, 3, _UNPLACED_ERROR)]
    assert str(result).count("<p") == 3


def test_on_slot_rendered_sees_the_unplaced_rows(render_path: str) -> None:
    del render_path  # the fixture switches the render path
    seen: list[tuple[int, int, str]] = []

    class Watch(Extension):
        name = "watch_unplaced_rows"

        def on_slot_rendered(self, ctx: Any) -> None:
            if isinstance(ctx.result, CitryRender):
                seen.append(_describe_unplaced(ctx.result))

    result, _calls = _PageCase(_FILL_PAGE, extensions=(Watch,)).render()
    assert seen == [(3, 3, _UNPLACED_ERROR)]
    assert str(result).count("<p") == 3


def test_a_nested_template_kwarg_holds_the_unplaced_rows(render_path: str) -> None:
    del render_path  # the fixture switches the render path
    seen: list[tuple[int, int, str]] = []

    def holder_data(kwargs: Any, _slots: Any) -> dict[str, Any]:
        seen.append(_describe_unplaced(kwargs["body"]))
        return {"body": kwargs["body"]}

    result, _calls = _PageCase(
        _NESTED_TEMPLATE_PAGE,
        holder_template="""
            <div>{{ body }}</div>
        """,
        holder_data=holder_data,
    ).render()
    assert seen == [(3, 3, _UNPLACED_ERROR)]
    assert str(result).count("<p") == 3


def test_a_leftover_row_is_an_unresolved_part_of_a_prepared_render() -> None:
    # A run's row left in a render the Vue path prepares gets the same
    # message as a leftover deferred component. This check does not depend
    # on the render path.
    page = _PageCase().build()
    run = _DeferredRun(page.citry.get("row"), page(), {}, None)
    row = _DeferredRunRow(run, 0)
    render = CitryRender(parts=[row], context=cr.CitryContext(variables={}), render_target="prepared")
    with pytest.raises(TypeError, match="prepared Vue rendering contains an unresolved runtime part"):
        _validate_prepared_render(render)
    assert repr(row) == "_DeferredRunRow(_DeferredRun(Row, rows=0), index=0)"
