"""
The walkers over render output use the same number of Python frames at any template depth.

These walkers read what a render produced: the nested parts of `<c-if>` and
`<c-for>` bodies, slots and child components. A walker that called itself
once per nested layer would use a Python frame per layer (issue #299, part
of #272). Most tests here render the same fixture nested 8 and 128 levels
deep, count how many frames of the walkers under test are on the Python
stack at once, and check that the deep render needs only a few more.
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

import pytest

from citry import Citry, Component
from citry._vue.compiler import definition_compile_input
from citry._vue.prepared import (
    FillClosure,
    Html,
    PreparedSlotOutlet,
    SlotOutlet,
    _component_call_refs,
    _ownership_refs,
    _prepared_slot_outlets,
    _slot_outlets,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from types import CodeType, FrameType

# The walkers this file guards, by source file and function name.
_WALKERS: dict[str, frozenset[str]] = {
    "citry/_vue/document.py": frozenset({"contains_document", "visit"}),
    "citry/_vue/direct_capture.py": frozenset(
        {
            "transform_parts",
            "transform_component",
            "run_members",
            "nested",
            "by_driver",
            "_resume",
            "visit",
            "_authored_markup_only",
            "_authored_vue_syntax",
        }
    ),
    "citry/component_render.py": frozenset({"_capture_pure_part", "_replay_pure_body"}),
    "citry/ext/cache/replay.py": frozenset({"collect_instances", "detach", "build"}),
    "citry/_vue/compiler.py": frozenset({"render_nodes", "render"}),
    "citry/_vue/prepared.py": frozenset(
        {"_component_call_refs", "_ownership_refs", "_slot_outlets", "_prepared_slot_outlets"}
    ),
}

DEPTHS = (8, 128)
# The deep render may use this many more walker frames than the shallow one.
# The Vue assembler runs a few levels directly before it hands deeper ones to
# the walk driver, so the counts differ by a frame or two.
MARGIN = 4


def _is_walker(code: CodeType) -> bool:
    path = code.co_filename.replace("\\", "/")
    return any(path.endswith(suffix) and code.co_name in names for suffix, names in _WALKERS.items())


@contextmanager
def _walker_frames() -> Iterator[dict[str, int]]:
    """Record the most walker frames on the stack at once, and which walkers ran."""
    result: dict[str, int] = {"peak": 0}
    active = 0
    seen: dict[CodeType, bool] = {}

    def profile(frame: FrameType, event: str, _arg: Any) -> None:
        nonlocal active
        if event not in {"call", "return"}:
            return
        code = frame.f_code
        walker = seen.get(code)
        if walker is None:
            walker = seen[code] = _is_walker(code)
        if not walker:
            return
        # A generator walker reports a call each time it resumes and a
        # return each time it yields, so this counts frames on the stack.
        if event == "call":
            active += 1
            result["peak"] = max(result["peak"], active)
            # Count by file and name, since several walkers share a name.
            key = f"{code.co_filename.replace(chr(92), '/').rsplit('citry/', 1)[-1]}:{code.co_name}"
            result[key] = result.get(key, 0) + 1
        else:
            active -= 1

    previous = sys.getprofile()
    sys.setprofile(profile)
    try:
        yield result
    finally:
        sys.setprofile(previous)


def _nested(depth: int, inner: str) -> str:
    # `flag` is template data, so the render path evaluates every level.
    return '<c-if cond="flag">' * depth + inner + "</c-if>" * depth


def _peaks(run: Callable[[int], object], expected: set[str]) -> dict[int, int]:
    peaks: dict[int, int] = {}
    for depth in DEPTHS:
        run(depth)  # the first render compiles and caches; measure the next one
        with _walker_frames() as frames:
            run(depth)
        missing = expected - frames.keys()
        assert not missing, f"the fixture did not reach {sorted(missing)} at depth {depth}"
        peaks[depth] = frames["peak"]
    return peaks


def _assert_flat(peaks: dict[int, int]) -> None:
    print(f"walker frames on the stack at once, by depth: {peaks}")  # noqa: T201 - kept in the test log
    assert peaks[128] <= peaks[8] + MARGIN, peaks


def _vue_page(template: str, *, child_template: str | None = None, **attrs: object) -> type[Component]:
    app = Citry(autodiscover=False)
    namespace: dict[str, object] = {}
    if child_template is not None:

        class Child(Component):
            citry = app
            template = child_template
            js = "$component({});"

        namespace["Child"] = Child

    def template_data(self: Component, kwargs: object, slots: object) -> dict[str, object]:
        return {"flag": True, "value": "v"}

    return type(
        "Page",
        (Component,),
        {"citry": app, "template": template, "js": "$component({});", "template_data": template_data, **attrs},
    )


def test_vue_assembly_walks_deep_bodies_in_constant_frames() -> None:
    pages: dict[int, type[Component]] = {}

    def render(depth: int) -> object:
        # A child component keeps the page off the single-program fast path,
        # so the assembler walks every nested body.
        page = pages.setdefault(
            depth, _vue_page(_nested(depth, "<p>{{ value }}<c-Child /></p>"), child_template="<b>c</b>")
        )
        return page().render().serialize()

    _assert_flat(
        _peaks(render, {"_vue/direct_capture.py:transform_parts", "_vue/direct_capture.py:transform_component"})
    )


def test_vue_document_shell_walks_deep_bodies_in_constant_frames() -> None:
    pages: dict[int, type[Component]] = {}

    def render(depth: int) -> object:
        template = "<!DOCTYPE html><html><head></head><body>" + _nested(depth, "<p>{{ value }}</p>") + "</body></html>"
        page = pages.setdefault(depth, _vue_page(template))
        return page().render().serialize()

    _assert_flat(_peaks(render, {"_vue/document.py:contains_document", "_vue/document.py:visit"}))


def test_ignored_contents_walk_deep_bodies_in_constant_frames() -> None:
    pages: dict[int, type[Component]] = {}

    def render(depth: int) -> object:
        template = "<main><div #c-ignore>" + _nested(depth, "<p>{{ value }}</p>") + "</div><c-Child /></main>"
        page = pages.setdefault(depth, _vue_page(template, child_template="<b>c</b>"))
        return page().render().serialize()

    _assert_flat(_peaks(render, {"_vue/direct_capture.py:visit"}))


def test_v_pre_checks_walk_deep_bodies_in_constant_frames() -> None:
    pages: dict[int, type[Component]] = {}

    def render(depth: int) -> object:
        # Inside a table, `v-pre` contents cannot sit in a block of HTML, so
        # Citry checks them for authored markup and then for Vue syntax.
        # Each `<c-provide>` level is a transparent body both checks enter.
        # `{{ value }}` is a data value, so the markup check fails and the
        # Vue syntax check runs too.
        body = '<c-provide key="k" data="1">' * depth + "{{ value }}" + "</c-provide>" * depth
        template = "<main><table v-pre><tr><td>" + body + "</td></tr></table></main>"
        page = pages.setdefault(depth, _vue_page(template))
        return page().render().serialize()

    _assert_flat(
        _peaks(render, {"_vue/direct_capture.py:_authored_markup_only", "_vue/direct_capture.py:_authored_vue_syntax"})
    )


def test_pure_components_capture_and_replay_deep_bodies_in_constant_frames() -> None:
    def render(depth: int) -> object:
        app = Citry(autodiscover=False)

        class Leaf(Component):
            citry = app
            pure = True
            # Only text inside the bodies, which a pure plan can replay.
            template = _nested(depth, "{{ value }}")

            def template_data(self, kwargs: object, slots: object) -> dict[str, object]:
                return {"flag": True, "value": "v"}

        class Page(Component):
            citry = app
            # The second call replays the plan the first one captured.
            template = "<main><c-Leaf /><c-Leaf /></main>"
            js = "$component({});"

        return Page().render().serialize()

    _assert_flat(_peaks(render, {"component_render.py:_capture_pure_part", "component_render.py:_replay_pure_body"}))


def test_cache_export_and_replay_walk_deep_bodies_in_constant_frames() -> None:
    def render(depth: int) -> object:
        app = Citry(autodiscover=False)

        class Child(Component):
            citry = app
            template = "<b>c</b>"
            js = "$component({});"

        class Cached(Component):
            citry = app

            class Cache:
                enabled = True

            # A child component keeps the body off the single-program fast
            # path, so each nested body is its own frame in the artifact.
            template = _nested(depth, "<p>{{ value }}<c-Child /></p>")
            js = "$component({});"

            def template_data(self, kwargs: object, slots: object) -> dict[str, object]:
                return {"flag": True, "value": "v"}

        class Page(Component):
            citry = app
            template = "<main><c-Cached /></main>"
            js = "$component({});"

        # The first render exports the artifact and the second replays it.
        Page().render().serialize()
        return Page().render().serialize()

    _assert_flat(
        _peaks(
            render,
            {"ext/cache/replay.py:collect_instances", "ext/cache/replay.py:detach", "ext/cache/replay.py:build"},
        )
    )


def test_vue_call_runs_in_deep_bodies_use_constant_frames() -> None:
    pages: dict[int, type[Component]] = {}

    def render(depth: int) -> object:
        # A component rendered once per row is assembled as a call run.
        inner = '<c-for each="item in [1, 2, 3]"><c-Child #c-key="item" /></c-for><c-Child />'
        page = pages.setdefault(depth, _vue_page(_nested(depth, inner), child_template="<b>c</b>"))
        return page().render().serialize()

    _assert_flat(_peaks(render, {"_vue/direct_capture.py:run_members", "_vue/direct_capture.py:transform_parts"}))


@pytest.mark.parametrize("call_run", [False, True], ids=["call", "call-run"])
@pytest.mark.parametrize("chain", [10, 300])
def test_a_deep_component_chain_assembles_within_a_bounded_stack(chain: int, call_run: bool) -> None:
    # Each component wraps the next one in a few `<c-if>` levels. The
    # assembler runs a chain this long directly only up to a fixed number
    # of frames, then hands the rest to the walk driver.
    app = Citry(autodiscover=False)

    def template_data(self: Component, kwargs: object, slots: object) -> dict[str, object]:
        return {"flag": True}

    last: type[Component] | None = None
    for index in range(chain):
        if last is None:
            inner = "<b>end</b>"
        elif call_run:
            # One keyed row, so the child is assembled as a call run.
            inner = f'<c-for each="item in [1]"><c-{last.__name__} #c-key="item" /></c-for>'
        else:
            inner = f"<c-{last.__name__} />"
        last = type(
            f"Link{index}",
            (Component,),
            {
                "citry": app,
                "template": _nested(3, inner),
                "js": "$component({});",
                "template_data": template_data,
            },
        )
    assert last is not None
    with _walker_frames() as frames:
        html = last().render().serialize()
    assert "end</b>" in html
    print(f"walker frames for a chain of {chain}: {frames['peak']}")  # noqa: T201 - kept in the test log
    assert frames["peak"] <= 160, frames["peak"]


@pytest.mark.parametrize("depth", DEPTHS)
def test_prepared_view_walkers_handle_deep_slot_chains(depth: int) -> None:
    fallback: tuple[Any, ...] = (Html("x", "template"),)
    for index in range(depth):
        fallback = (PreparedSlotOutlet(f"citrySlot{index}", f"s{index}", fallback),)
    selected: tuple[Any, ...] = (Html("x", "template"),)
    for index in range(depth):
        closure = FillClosure(f"citrySlot{index}", f"s{index}", None, None, selected)
        selected = (SlotOutlet(f"citrySlot{index}", f"s{index}", "citryOccurrence0", closure),)

    with _walker_frames() as frames:
        compiled = definition_compile_input(fallback)
        assert len(list(_prepared_slot_outlets(fallback))) == depth
        assert len(list(_slot_outlets(selected))) == depth
        assert len(list(_ownership_refs(selected))) == depth
        assert list(_component_call_refs(selected, {}, {}, "citryOccurrence0")) == []
    assert compiled.template.count("<template v-else-if") == depth
    # At most two walker frames are on the stack at once, however long the chain.
    assert frames["peak"] <= 2, frames
