"""
Check that templates at the logic nesting limit render within a fixed Python frame budget.

The nesting limit lets a template nest 256 of Citry's logic
levels: control-flow tags and attributes, slots, fills and component tags.
This test confirms that this leaves room for the application around Citry.
A web framework, middleware, a view and a test runner already sit on the
Python stack when Citry renders, so each fixture starts 200 frames deep,
then lowers Python's recursion limit to allow only 500 more frames. Under
that limit Citry renders the fixture twice and serializes it. That leaves
at least 300 frames below Python's default limit of 1,000.

The fixtures run without Vue, with Vue, and with the i18n extension; the
events extension is on in all of them, as it is by default. Two fixtures
also run ``citry check`` on the Python render path, once at the limit
under the low limit, compared with a check at depth 128 under the normal
one (see `CHECKED_FIXTURES` for why only two). The language server's half is
``packages/py/citry_lsp/tests/test_frame_budget.py``.

Several handlers in Citry catch ``RecursionError`` and quietly do less, so a
run that merely finishes proves little. Each fixture's output under the low
limit must equal its output under the normal limit, its innermost level
must render, and the cached component must replay from the cache.

The test also measures how many frames a render needs: the deepest stack at
the limit may be at most 20 frames above the deepest stack at depth 8, or,
with Vue, at depth 128 (see `VUE_COMPARISON_DEPTH`), plus the fixed cost of
copying the first levels of the data Vue receives (`VUE_DIRECT_JSON_FRAMES`).
A chain of four components that pass a slot on may cost at most 12 frames
per extra component. It prints every number, so the measured margin is on
record in the CI log.

Each render path runs in its own subprocess, so the lowered recursion limit
never reaches the pytest process, and in its own test file, so CI runs the
two paths on separate workers. The Rust path takes about a minute and a
half and the Python path, which also runs ``citry check``, about six
minutes, so they are qualification tests that run only on Linux, in
the version-matrix jobs and, for the Check workflow's Python, in Check's
qualification phase: frame counts depend on the Python version, not the
operating system.
The fast local gate does not run them; set
``CITRY_FRAME_BUDGET_ANY_OS=1`` to run them on another system.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from citry import Citry, Component
from citry._app_selection import CheckAppSelection
from citry._checker import check_project
from citry._vue.json_data import _DIRECT_JSON_DEPTH
from citry_core import _rust

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import FrameType

# The logic nesting limit, read from the parser so the two cannot disagree.
LOGIC_LIMIT = _rust.template_parser._MAX_LOGIC_NESTING
# Frames the application holds below Citry when it renders.
HOST_FRAMES = 200
# Frames Citry's own work may use above the host.
BUDGET = 500
SHALLOW = 8
ALLOWED_GROWTH = 20
# Extra frames allowed for each component a passed-on slot goes through.
FRAMES_PER_HOP = 12
# In a component that uses Vue, Citry's code that builds the browser data runs
# up to `_INLINE_WALK_FRAMES` (128) frames of nested walks directly before
# it hands deeper ones to `citry._walk.run`, which keeps them on a list
# instead of the call stack. A template reaches that fixed cost somewhere
# between depth 64 and 128, so with Vue the peak at the limit is compared
# with the peak at this depth instead of at `SHALLOW`.
VUE_COMPARISON_DEPTH = 128
# The data a Vue component sends the browser is copied with direct calls
# for its first `_DIRECT_JSON_DEPTH` (32) levels, and with a loop below
# that, so it is another fixed cost. Some fixtures' data only gets that deep
# between `VUE_COMPARISON_DEPTH` and the limit, so with Vue the deepest
# stack may grow by that many frames more. On 3.11 each of those levels is
# two frames, because a comprehension runs in a frame of its own there.
VUE_DIRECT_JSON_FRAMES = _DIRECT_JSON_DEPTH * (2 if sys.version_info < (3, 12) else 1)


# The two test files mark their test with this.
only_in_linux_jobs = pytest.mark.skipif(
    sys.platform != "linux" and os.environ.get("CITRY_FRAME_BUDGET_ANY_OS") != "1",
    reason="frame counts depend on the Python version, not the OS, so only the Linux jobs run this",
)


def _for_tags(depth: int) -> tuple[str, str]:
    """Nested `<c-for>` tags that each bind their own name, with a `<c-empty>` after each."""
    opens = "".join(f'<c-for each="x{level} in items">' for level in range(depth))
    return opens, "</c-for><c-empty>none</c-empty>" * depth


def _nest(depth: int, open_tag: str, inner: str, close_tag: str) -> str:
    return open_tag * depth + inner + close_tag * depth


def _cycle(depth: int, steps: list[tuple[str, str]], inner: str) -> str:
    """Nest `depth` levels, taking each level's open and close tags from `steps` in turn."""
    chosen = [steps[level % len(steps)] for level in range(depth)]
    return "".join(open_tag for open_tag, _ in chosen) + inner + "".join(close for _, close in reversed(chosen))


# Each fixture builds a template nested `depth` logic levels deep. Every
# condition reads `flag` from the template data: a constant one, such as
# `cond="True"`, is decided when the component compiles, and its tag is
# removed before any render. Some steps hold two logic levels, so they
# repeat half as many times.
FIXTURES: dict[str, Callable[[int], str]] = {
    "if_elif_else_tags": lambda d: _nest(
        d,
        '<c-if cond="not flag">no</c-if><c-elif cond="flag">',
        "{{ n }}",
        "</c-elif><c-else>else</c-else>",
    ),
    "for_and_empty_tags": lambda d: "{{ n }}".join(_for_tags(d)),
    "every_shorthand": lambda d: "".join(
        f'<p c-if="not flag">a</p><div c-elif="flag"><p c-for="y{level} in items">' for level in range(d // 2)
    )
    + "{{ n }}"
    + "</p><p c-empty>none</p></div><p c-else>b</p>" * (d // 2),
    "component_tags": lambda d: _cycle(
        d,
        [
            ("<c-Card>", "</c-Card>"),
            ('<c-component is="Card">', "</c-component>"),
            ('<c-element is="section">', "</c-element>"),
            ('<c-provide key="k" a="1">', "</c-provide>"),
        ],
        "{{ n }}",
    ),
    "slot_defaults": lambda d: "".join(f'<c-slot name="s{level}">' for level in range(d))
    + "{{ n }}"
    + "</c-slot>" * d,
    "fills": lambda d: _nest(d // 2, '<c-Card><c-fill name="default">', "{{ n }}", "</c-fill></c-Card>"),
    "simple_component_slots": lambda d: _nest(d, "<c-Label>", "{{ n }}", "</c-Label>"),
    # The plan names `{{ slots.x }}`; a template reads slots through its
    # data, so `Show` passes its fill to the template as `content`.
    "fills_shown_by_expression": lambda d: _nest(d, "<c-Show>", "{{ n }}", "</c-Show>"),
    # One `<c-Row />` per level, so the row count shows how many rendered.
    "components_in_loops": lambda d: "".join(f'<c-for each="x{level} in items"><c-Row />' for level in range(d - 1))
    + "<c-Row />"
    + "</c-for>" * (d - 1),
    # A loop whose body is one keyed `simple="vue"` component: with Vue,
    # Citry renders it as a call run, one call per row, at the limit.
    "call_run_at_the_bottom": lambda d: _nest(
        d - 2,
        '<c-if cond="flag">',
        '<c-for each="k in keys"><c-VueRow #c-key="k" /></c-for>',
        "</c-if>",
    ),
    "template_in_an_attribute": lambda d: "<c-Titled c-title='"
    + _nest(d - 1, '<c-if cond="flag">', "<b>{{ n }}</b>", "</c-if>")
    + "' />",
    # These two nest inside the component's own template, built at `depth`.
    "pure_component": lambda _d: "<c-PureLeaf /><c-PureLeaf />",
    "cached_component": lambda _d: "<c-Cached />",
    "plain_elements": lambda d: _nest(2 * d, "<div>", "{{ n }}", "</div>"),
}


def _innermost_rendered(fixture: str, html: str, depth: int) -> bool:
    """Whether the innermost level of `fixture` made it into `html`."""
    if fixture == "components_in_loops":
        return html.count("row</li>") == depth
    if fixture == "call_run_at_the_bottom":
        return html.count("vue row</li>") == len(_KEYS)
    return "deepest" in html


_KEYS = (1, 2, 3)
# Counts `Cached.template_data` calls, so a test can see whether the second
# render came from the cache or rendered again. Only one app renders at a
# time, so `_measure` clears it before each run.
_CACHED_CALLS: list[int] = [0]


def _app(*, i18n: bool) -> Citry:
    # The events extension is on by default, so every variant has it.
    if i18n:
        return Citry(
            autodiscover=False,
            extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US",)}},
        )
    return Citry(autodiscover=False)


def _data(self: Component, kwargs: Any, slots: Any) -> dict[str, Any]:
    return {"flag": True, "n": "deepest", "items": [1], "keys": list(_KEYS)}


def _cached_data(self: Component, kwargs: Any, slots: Any) -> dict[str, Any]:
    # A cache hit skips this, so the count shows whether the cache replayed.
    _CACHED_CALLS[0] += 1
    return _data(self, kwargs, slots)


def _show_data(self: Component, kwargs: Any, slots: Any) -> dict[str, Any]:
    # The fill renders where the template prints this value.
    return {"content": slots["default"]}


def _build(fixture: str, depth: int, *, variant: str) -> tuple[Citry, type[Component]]:
    """Build a fresh app whose `Page` component renders `fixture` at `depth`."""
    app = _app(i18n=variant == "i18n")
    uses_vue = variant == "vue"
    js = {"js": "$component({});"} if uses_vue else {}

    def component(name: str, template: str, **attrs: Any) -> None:
        type(name, (Component,), {"citry": app, "template": template, "__module__": __name__, **attrs})

    component("Card", "<section><c-slot /></section>")
    component("Label", "<span><c-slot /></span>", simple=True)
    component("Row", "<li>row</li>")
    component("VueRow", "<li>vue row</li>", simple="vue")
    component("Titled", "<h1>{{ title }}</h1>")
    component("Show", "<div>{{ content }}</div>", template_data=_show_data)
    component("PureLeaf", _nest(depth, '<c-if cond="flag">', "{{ n }}", "</c-if>"), pure=True, template_data=_data)
    component("CacheChild", "<b>c</b>", **js)
    component(
        "Cached",
        _nest(depth - 1, '<c-if cond="flag">', "<p>{{ n }}<c-CacheChild /></p>", "</c-if>"),
        Cache=type("Cache", (), {"enabled": True}),
        template_data=_cached_data,
        **js,
    )
    page = type(
        "Page",
        (Component,),
        {"citry": app, "template": FIXTURES[fixture](depth), "template_data": _data, "__module__": __name__, **js},
    )
    return app, page


def _fill_chain(depth: int, links: int, *, uses_vue: bool) -> tuple[Citry, type[Component]]:
    """
    Build a chain of `links` components that each pass their default slot on.

    Every template nests to `depth` logic levels, and the page writes its
    fill body at that depth too.
    """
    app = Citry(autodiscover=False)
    js = {"js": "$component({});"} if uses_vue else {}
    for index in range(links):
        if index == 0:
            template = _nest(depth - 1, '<c-if cond="flag">', "<c-slot />", "</c-if>")
        else:
            # The component and its fill are two levels, and the slot inside
            # the fill is the third.
            inner = f'<c-Link{index - 1}><c-fill name="default"><c-slot /></c-fill></c-Link{index - 1}>'
            template = _nest(depth - 3, '<c-if cond="flag">', inner, "</c-if>")
        type(
            f"Link{index}",
            (Component,),
            {"citry": app, "template": template, "template_data": _data, "__module__": __name__, **js},
        )
    page_template = _nest(
        depth - 2,
        '<c-if cond="flag">',
        f'<c-Link{links - 1}><c-fill name="default">{{{{ n }}}}</c-fill></c-Link{links - 1}>',
        "</c-if>",
    )
    page = type(
        "Page",
        (Component,),
        {"citry": app, "template": page_template, "template_data": _data, "__module__": __name__, **js},
    )
    return app, page


# Ids that differ between two apps in one process: a render id is "c" and
# eight letters or digits from a process-wide counter, and each Vue app's
# element id is random hex. Each distinct id gets a number by first
# appearance, so which part refers to which stays visible. A nine-letter
# word that starts with "c", such as "component", matches too; it gets the
# same number in both outputs, so it cannot hide a difference.
_COUNTED_IDS = re.compile(r"\b(?:c[0-9a-z]{8}|[0-9a-f]{32})\b")


def _normalize(text: str) -> str:
    numbered: dict[str, str] = {}
    return _COUNTED_IDS.sub(lambda match: numbered.setdefault(match.group(0), f"ID{len(numbered)}"), text)


def _render_twice(page: type[Component]) -> list[str]:
    # The first render compiles the template and runs the extension hooks;
    # the second uses what the first one stored. Both are numbered in one
    # pass, so an id they share keeps its number.
    first, second = (page().render().serialize() for _ in range(2))
    return _normalize(first + "\x00" + second).split("\x00")


def _check(fixture: str, depth: int) -> list[str]:
    """
    Run ``citry check`` on `fixture` at `depth`, and return its findings without numbers.

    The app holds only the page and the `Card` the fill fixture needs, and
    the innermost `{{ n }}` becomes a name the page does not define, so the
    check has the same findings at any depth: one for that name, found only
    if the check reaches the innermost level. Line and column numbers differ
    between depths, so every number in a message is dropped.
    """
    app = Citry(autodiscover=False)
    type("Card", (Component,), {"citry": app, "template": "<section><c-slot /></section>", "__module__": __name__})
    template = FIXTURES[fixture](depth).replace("{{ n }}", "{{ undefined_at_the_bottom }}")
    type("Page", (Component,), {"citry": app, "template": template, "__module__": __name__})
    with tempfile.TemporaryDirectory() as root:
        report = check_project(CheckAppSelection(spec="app:engine", engine=app), Path(root))
    return sorted(re.sub(r"\d+", "N", f"{finding.code}: {finding.message}") for finding in report.findings)


def _check_under_the_low_limit(fixture: str) -> dict[str, Any]:
    """
    Check `fixture` at the limit under the low limit, and compare with a normal check at depth 128.

    A check at the limit takes tens of seconds (#384), so it runs once,
    under the low limit, and is compared with a check at the comparison
    depth under the normal limit, which takes an eighth of the time.
    """
    expected = _check(fixture, VUE_COMPARISON_DEPTH)
    try:
        low = _with_host_stack(lambda: _check(fixture, LOGIC_LIMIT))
    except RecursionError as error:
        return {"error": f"RecursionError: {error}"}
    return {"same_findings": low == expected, "findings": low}


def _stack_depth() -> int:
    depth = 0
    frame: FrameType | None = sys._getframe(1)
    while frame is not None:
        depth += 1
        frame = frame.f_back
    return depth


def _with_host_stack(work: Callable[[], Any]) -> Any:
    """Run `work` with `HOST_FRAMES` frames below it and `BUDGET` frames of room above."""

    def descend() -> Any:
        if _stack_depth() < HOST_FRAMES:
            return descend()
        limit = sys.getrecursionlimit()
        sys.setrecursionlimit(_stack_depth() + BUDGET)
        try:
            return work()
        finally:
            sys.setrecursionlimit(limit)

    return descend()


def _peak_frames(work: Callable[[], object]) -> int:
    """Return the deepest stack `work` reaches, counted from where it starts."""
    base = _stack_depth()
    peak = 0

    def profile(frame: FrameType, event: str, arg: object) -> None:
        nonlocal peak
        if event != "call":
            return
        depth = 0
        current: FrameType | None = frame
        while current is not None:
            depth += 1
            current = current.f_back
        peak = max(peak, depth)

    sys.setprofile(profile)
    try:
        work()
    finally:
        sys.setprofile(None)
    return peak - base


def _measure(
    fixture: str,
    build: Callable[[int], tuple[Citry, type[Component]]],
    *,
    uses_vue: bool,
    expects_innermost: bool = True,
) -> dict[str, Any]:
    """Run one fixture under the normal and the low limit, and measure its frames."""

    def run(depth: int) -> dict[str, Any]:
        _CACHED_CALLS[0] = 0
        _app, page = build(depth)
        html = _render_twice(page)
        return {
            "html": html,
            # 1 when the second render came from the cache, as it should.
            "cached_renders": _CACHED_CALLS[0],
        }

    normal = run(LOGIC_LIMIT)
    try:
        low = _with_host_stack(lambda: run(LOGIC_LIMIT))
    except RecursionError as error:
        return {"error": f"RecursionError: {error}"}
    comparison_depth = VUE_COMPARISON_DEPTH if uses_vue else SHALLOW
    return {
        "same_output": low == normal,
        "innermost_rendered": all(_innermost_rendered(fixture, html, LOGIC_LIMIT) for html in normal["html"]),
        # Past about 128 nested elements, the server HTML of a component
        # that uses Vue leaves the deepest part for Vue to build in the
        # browser, so its innermost text is only expected without Vue.
        "expects_innermost": expects_innermost,
        "cached_renders": normal["cached_renders"],
        "comparison_depth": comparison_depth,
        "uses_vue": uses_vue,
        "comparison_peak": _peak_frames(lambda: _render_twice(build(comparison_depth)[1])),
        "deep_peak": _peak_frames(lambda: _render_twice(build(LOGIC_LIMIT)[1])),
    }


VARIANTS = ("html", "vue", "i18n")
# `citry check` reads the parsed tree from the Rust extension, which copies
# a node's whole subtree each time Python reads its body (#384), so a check
# at the limit takes tens of seconds even for these two fixtures; each runs
# once at the limit (see `_check_under_the_low_limit`). The check walkers'
# frame use at other shapes is covered at depth 128 by
# test_check_depth_frames.py.
CHECKED_FIXTURES = ("plain_elements", "fills")


def _worker(*, run_check: bool) -> None:
    """Measure every fixture in this process and print the results as JSON."""
    results: dict[str, Any] = {}
    for fixture in FIXTURES:
        for variant in VARIANTS:
            results[f"{fixture}[{variant}]"] = _measure(
                fixture,
                lambda depth, fixture=fixture, variant=variant: _build(fixture, depth, variant=variant),
                uses_vue=variant == "vue",
                expects_innermost=variant != "vue",
            )
    for uses_vue in (False, True):
        for links in (1, 4):
            results[f"fill_chain[{links}, {'vue' if uses_vue else 'html'}]"] = _measure(
                "fill_chain",
                lambda depth, links=links, uses_vue=uses_vue: _fill_chain(depth, links, uses_vue=uses_vue),
                uses_vue=uses_vue,
                expects_innermost=not uses_vue,
            )
    if run_check:
        # `citry check` reads the template, not the render path or the
        # app's options, so one run on one path covers each fixture.
        for fixture in CHECKED_FIXTURES:
            results[f"check:{fixture}"] = _check_under_the_low_limit(fixture)
    print(json.dumps(results))  # noqa: T201 - the parent test reads this


def check_render_path(render_path: str) -> None:
    """
    Run every fixture on one render path in a subprocess, and check the results.

    ``test_frame_budget_rust.py`` and ``test_frame_budget_python.py`` each
    call this for their path, so CI runs the two on separate workers.
    """
    result = subprocess.run(
        [sys.executable, __file__, "--check" if render_path == "python" else "--no-check"],
        capture_output=True,
        text=True,
        timeout=1800,
        check=False,
        env={**os.environ, "CITRY_NATIVE_RENDER": "1" if render_path == "rust" else "0"},
    )
    assert result.returncode == 0, result.stderr[-4000:]
    results: dict[str, Any] = json.loads(result.stdout.splitlines()[-1])
    for name, numbers in results.items():
        print(name, numbers)  # noqa: T201 - the measured margins stay in the CI log
    over_budget = {name: numbers["error"] for name, numbers in results.items() if "error" in numbers}
    assert not over_budget, over_budget
    checks = {name: results.pop(name) for name in list(results) if name.startswith("check:")}
    assert bool(checks) == (render_path == "python"), sorted(checks)
    for name, entry in checks.items():
        assert entry["same_findings"], f"{name}: findings at {LOGIC_LIMIT} differ from depth {VUE_COMPARISON_DEPTH}"
        # The name at the innermost level is reported, so the check read it all.
        assert any("undefined_at_the_bottom" in finding for finding in entry["findings"]), entry["findings"]
    changed = [name for name, numbers in results.items() if not numbers["same_output"]]
    assert not changed, f"output changed under the low recursion limit: {changed}"
    missing = [
        name for name, numbers in results.items() if numbers["expects_innermost"] and not numbers["innermost_rendered"]
    ]
    assert not missing, f"the innermost level did not render: {missing}"
    not_replayed = [
        name
        for name, numbers in results.items()
        if name.startswith("cached_component") and numbers["cached_renders"] != 1
    ]
    assert not not_replayed, f"the cached component rendered again instead of replaying: {not_replayed}"
    grew = {
        name: (numbers["comparison_depth"], numbers["comparison_peak"], numbers["deep_peak"])
        for name, numbers in results.items()
        if numbers["deep_peak"] - numbers["comparison_peak"]
        > ALLOWED_GROWTH + (VUE_DIRECT_JSON_FRAMES if numbers["uses_vue"] else 0)
    }
    assert not grew, f"(depth compared, frames there, frames at {LOGIC_LIMIT}): {grew}"
    for variant in ("html", "vue"):
        hops = results[f"fill_chain[4, {variant}]"]["deep_peak"] - results[f"fill_chain[1, {variant}]"]["deep_peak"]
        assert hops <= 3 * FRAMES_PER_HOP, f"{variant}: a chain of four costs {hops} frames more than a chain of one"


if __name__ == "__main__":
    _worker(run_check=sys.argv[1:] == ["--check"])
