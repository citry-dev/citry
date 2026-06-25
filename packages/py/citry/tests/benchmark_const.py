"""
Benchmarks for the Const optimization (citry/constness.py).

Reproduces the measurements recorded in docs/design/constness.md section 13
(the results table) and section 14.5 (the slot-layout profile that parked
slot-boundary folding). Each scenario renders the same component twice, once
with Const-marked inputs and once with plain inputs, and reports the
speedup.

Run from the repository root:

    .venv/bin/python packages/py/citry/tests/benchmark_const.py
    .venv/bin/python packages/py/citry/tests/benchmark_const.py --profile

IMPORTANT: build the Rust extension in release mode first
(`uv run maturin develop --release` in packages/py/citry_core). The default
debug build makes the serialize step ~12x slower and skews every
"render + serialize" number (see docs/codebase.md, "Build the Python
package").

Not collected by pytest (the filename does not match ``test_*``); this is a
script, not a test, because timings depend on the machine and would make
flaky assertions.
"""

import argparse
import cProfile
import pstats
import re
import timeit

from citry import Citry, Component, Const

# How many renders per timing. Large enough to amortize noise, small enough
# to keep the whole script under ~30 seconds.
ITERATIONS = 3000

_CID_RE = re.compile(r' data-cid-\w+=""')


def _strip_ids(html: str) -> str:
    """Remove the per-render component-id markers so outputs can be compared."""
    return _CID_RE.sub("", html)


def _measure(label: str, render_const, render_plain) -> None:
    """Time both variants (after a warmup render) and print the comparison."""
    # Outputs must match, or the comparison is meaningless. str() serializes
    # a CitryRender, so this works for render-only variants too.
    assert _strip_ids(str(render_const())) == _strip_ids(str(render_plain())), f"{label}: outputs differ"

    t_plain = timeit.timeit(render_plain, number=ITERATIONS)
    t_const = timeit.timeit(render_const, number=ITERATIONS)
    per_plain = t_plain / ITERATIONS * 1e6
    per_const = t_const / ITERATIONS * 1e6
    print(
        f"  {label:<24} plain {per_plain:7.1f} us | const {per_const:7.1f} us"
        f" | {t_plain / t_const:.2f}x ({(1 - t_const / t_plain) * 100:.0f}% less)"
    )


def scenario_expression_heavy() -> None:
    """30 const expressions + 5 const ifs + 1 dynamic expression (section 13 row 1)."""
    c = Citry()
    cells = "".join(
        f'<c-if cond="show{i}"><td>{{{{ col{i} }}}}</td></c-if>' if i % 6 == 0 else f"<td>{{{{ col{i} }}}}</td>"
        for i in range(30)
    )

    class Grid(Component):
        citry = c
        template = f"<table><tr>{cells}<td>{{{{ body }}}}</td></tr></table>"

        def template_data(self, kwargs, slots):
            return dict(kwargs)

    const_kwargs = {f"col{i}": Const(f"v{i}") for i in range(30)}
    const_kwargs.update({f"show{i}": Const(True) for i in range(0, 30, 6)})  # noqa: FBT003
    plain_kwargs = {k: (v.__wrapped__ if hasattr(v, "__wrapped__") else v) for k, v in const_kwargs.items()}

    print("Expression-heavy grid:")
    _measure(
        "render + serialize",
        lambda: Grid(body="row", **const_kwargs).render().serialize(),
        lambda: Grid(body="row", **plain_kwargs).render().serialize(),
    )
    _measure(
        "render only",
        lambda: Grid(body="row", **const_kwargs).render(),
        lambda: Grid(body="row", **plain_kwargs).render(),
    )


def scenario_small_card() -> None:
    """4 const expressions + 1 const if + 1 dynamic expression (section 13 row 2)."""
    c = Citry()

    class Card(Component):
        citry = c
        template = (
            '<div class="card"><h2>{{ title }}</h2>'
            '<c-if cond="cols > 2"><div class="wide">{{ subtitle }} ({{ cols }} columns)</div></c-if>'
            '<c-else><div class="narrow">{{ subtitle }}</div></c-else>'
            "<p>{{ body }}</p><span>{{ footer }}</span></div>"
        )

        def template_data(self, kwargs, slots):
            return dict(kwargs)

    const_kwargs = {"title": Const("Dashboard"), "subtitle": Const("Stats"), "cols": Const(3), "footer": Const("(c)")}
    plain_kwargs = {"title": "Dashboard", "subtitle": "Stats", "cols": 3, "footer": "(c)"}

    print("Small card:")
    _measure(
        "render + serialize",
        lambda: Card(body="row", **const_kwargs).render().serialize(),
        lambda: Card(body="row", **plain_kwargs).render().serialize(),
    )
    _measure(
        "render only",
        lambda: Card(body="row", **const_kwargs).render(),
        lambda: Card(body="row", **plain_kwargs).render(),
    )


def scenario_unrolled_nav() -> None:
    """A const 20-link loop that fully unrolls, plus 1 dynamic expression (section 13 row 3)."""
    c = Citry()

    class Nav(Component):
        citry = c
        template = (
            '<nav><c-for each="item in links"><a c-href="item">{{ item }}</a></c-for></nav>'
            "<main>{{ body }}</main>"
        )

        def template_data(self, kwargs, slots):
            return dict(kwargs)

    links = [f"/page/{i}" for i in range(20)]

    print("Nav with const 20-link loop (unrolls):")
    _measure(
        "render + serialize",
        lambda: Nav(links=Const(links), body="text").render().serialize(),
        lambda: Nav(links=list(links), body="text").render().serialize(),
    )


def _build_slot_layout() -> tuple[Citry, type[Component], dict, dict]:
    """The slot-heavy layout page used in section 13 and the section 14.5 profile."""
    c = Citry()

    class Layout(Component):
        citry = c
        template = (
            '<div class="layout"><aside><c-slot name="sidebar" /></aside>'
            '<main><c-slot name="main" /></main></div>'
        )

    class CardC(Component):
        citry = c
        template = '<div class="card"><h2><c-slot name="title" /></h2><c-slot name="body" /></div>'

    class Page(Component):
        citry = c
        template = (
            "<c-Layout>"
            '<c-fill name="sidebar"><nav><c-for each="link in links">'
            '<a c-href="link">{{ link }}</a></c-for></nav></c-fill>'
            '<c-fill name="main"><c-CardC>'
            '<c-fill name="title">{{ heading }} ({{ section }})</c-fill>'
            '<c-fill name="body"><p>{{ body_text }}</p></c-fill>'
            "</c-CardC></c-fill>"
            "</c-Layout>"
        )

        def template_data(self, kwargs, slots):
            return dict(kwargs)

    links = [f"/p/{i}" for i in range(10)]
    const_kwargs = {"links": Const(links), "heading": Const("Dashboard"), "section": Const("admin")}
    plain_kwargs = {"links": list(links), "heading": "Dashboard", "section": "admin"}
    return c, Page, const_kwargs, plain_kwargs


def scenario_slot_layout() -> None:
    """Layout + card with four slot sites; const fills fold inside (section 13 row 4)."""
    _, page_cls, const_kwargs, plain_kwargs = _build_slot_layout()

    print("Slot-heavy layout (layout + card, 4 slot sites):")
    _measure(
        "render + serialize",
        lambda: page_cls(body_text="live", **const_kwargs).render().serialize(),
        lambda: page_cls(body_text="live", **plain_kwargs).render().serialize(),
    )
    _measure(
        "render only",
        lambda: page_cls(body_text="live", **const_kwargs).render(),
        lambda: page_cls(body_text="live", **plain_kwargs).render(),
    )


def profile_slot_layout() -> None:
    """The section 14.5 breakdown: where the slot-heavy render spends its time."""
    _, page_cls, const_kwargs, _ = _build_slot_layout()
    page_cls(body_text="x", **const_kwargs).render().serialize()  # warm the caches

    profiler = cProfile.Profile()
    profiler.enable()
    for _ in range(2000):
        page_cls(body_text="x", **const_kwargs).render().serialize()
    profiler.disable()

    stats = pstats.Stats(profiler)
    total = stats.total_tt
    print(f"\nProfile (const inputs, 2000 renders, total {total * 1e3:.0f} ms):")
    interesting = {
        ("nodes/__init__", "render"): "node render (per node kind, by line)",
        ("nodes/__init__", "_collect_slots"): "fill collection",
        ("component_render", "_render_one"): "single component render",
        ("component", "_create_instance"): "component instance creation",
        ("serialize", "serialize_render"): "serialization",
        ("extension", "on_slot_rendered"): "on_slot_rendered dispatch",
        ("slots", "__call__"): "slot (fill) invocation",
    }
    for (filename, lineno, funcname), (_cc, ncalls, _tt, cumtime, _callers) in sorted(
        stats.stats.items(), key=lambda kv: -kv[1][3]
    ):
        for (file_part, name), label in interesting.items():
            if file_part in filename and funcname == name:
                print(
                    f"  {label:<34} {funcname}@{lineno:<5} calls={ncalls:<6}"
                    f" cum={cumtime * 1e3:7.1f} ms ({cumtime / total * 100:4.1f}%)"
                )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", action="store_true", help="also print the slot-layout profile (section 14.5)")
    args = parser.parse_args()

    print(f"({ITERATIONS} renders per timing; remember: release build of the Rust extension!)\n")
    scenario_expression_heavy()
    scenario_small_card()
    scenario_unrolled_nav()
    scenario_slot_layout()
    if args.profile:
        profile_slot_layout()


if __name__ == "__main__":
    main()
