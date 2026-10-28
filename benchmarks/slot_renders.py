r"""
Compare how long two checkouts take to render pages full of slots.

Citry's body renderer (``_render_body``, the loop that renders a template
body) renders a slot's body itself in two cases: a slot that renders its
own fallback, and a slot given a template fill. That code runs once for
every slot of every render, so a change to it is measured on its own, away
from the large benchmark's other work. Each scenario renders one page
that holds 300 components, each with one slot:

- ``filled``: every component gets a ``<c-fill>``, so every slot renders a
  fill that the page wrote;
- ``fallback``: no component gets a fill, so every slot renders its own body;
- ``chain``: 15 chains of 20 components, each passing the fill it received
  on to the next one's slot with ``<c-fill><c-slot /></c-fill>``.

Each sample runs in a fresh process: it renders the page once to compile
it, then renders it ``--renders`` times and keeps the shortest process CPU
time of one render. The two checkouts alternate, and the side that goes
first alternates too, so a slow stretch on the machine lands on both.
The report gives, per side, the minimum and the median of the samples, and
the change from base to head. Compare the two sides of one run, never
numbers across machines or runs.

Usage (from the repository root, with a release build of ``citry_core``)::

    .venv/bin/python benchmarks/slot_renders.py \
        --base /path/to/base/checkout --head . \
        --scenario filled --native 1 --runs 7 --renders 15

A base checkout needs only the Python package, so
``git archive origin/main packages/py/citry | tar -x -C /tmp/base`` makes
one without a second git worktree. ``--native 1`` or ``0`` sets
``CITRY_NATIVE_RENDER`` for every sample.
Each checkout's ``packages/py/citry`` goes first on ``PYTHONPATH``, so both
sides use this interpreter's ``citry_core``.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# The scenario sizes: 300 components in total in each.
COMPONENTS = 300
CHAIN_LINKS = 20


def _page(scenario: str) -> Any:
    """Build a fresh app and return the page component for `scenario`."""
    # Imported here: the parent process only starts workers, and each worker
    # must import the checkout it was given on `PYTHONPATH`.
    from citry import Citry, Component  # noqa: PLC0415

    app = Citry(autodiscover=False)

    def data(_self: Any, _kwargs: Any, _slots: Any) -> dict[str, Any]:
        return {"n": 1, "items": list(range(COMPONENTS)), "chains": list(range(COMPONENTS // CHAIN_LINKS))}

    def component(name: str, template: str) -> type[Any]:
        return type(name, (Component,), {"citry": app, "template": template, "template_data": data})

    component("Card", '<div class="card"><c-slot>fallback {{ n }}</c-slot></div>')
    for index in range(1, CHAIN_LINKS):
        # Link 0 is the card; every other link passes its fill on.
        inner = "Card" if index == 1 else f"Link{index - 1}"
        component(f"Link{index}", f'<span><c-{inner}><c-fill name="default"><c-slot /></c-fill></c-{inner}></span>')
    templates = {
        "filled": '<c-for each="i in items"><c-Card><c-fill name="default"><b>{{ i }}</b></c-fill></c-Card></c-for>',
        "fallback": '<c-for each="i in items"><c-Card /></c-for>',
        "chain": (
            f'<c-for each="i in chains"><c-Link{CHAIN_LINKS - 1}><c-fill name="default">'
            f"<b>{{{{ i }}}}</b></c-fill></c-Link{CHAIN_LINKS - 1}></c-for>"
        ),
    }
    return component("Page", templates[scenario])


def _worker(scenario: str, renders: int) -> None:
    """Measure one sample in this process and print it as JSON."""
    import citry  # noqa: PLC0415 - imported from the checkout on PYTHONPATH

    page = _page(scenario)
    # The first render compiles every template; it is not measured.
    expected = page().render().serialize(deps_strategy="ignore")
    best = float("inf")
    for _ in range(renders):
        start = time.process_time()
        html = page().render().serialize(deps_strategy="ignore")
        best = min(best, time.process_time() - start)
    # The page must render the same each time, or the samples measure different work.
    if html.count("<b>") != expected.count("<b>"):
        raise SystemExit("the page changed between renders")
    print(json.dumps({"seconds": best, "citry": citry.__file__, "html_length": len(html)}))


def _sample(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    env = {
        **os.environ,
        "PYTHONPATH": os.pathsep.join(filter(None, [str(root / "packages/py/citry"), os.environ.get("PYTHONPATH")])),
        "CITRY_NATIVE_RENDER": args.native,
    }
    command = [sys.executable, __file__, "--worker", "--scenario", args.scenario, "--renders", str(args.renders)]
    # Run from outside both checkouts, so neither one's directory decides what `import citry` finds.
    done = subprocess.run(command, env=env, capture_output=True, text=True, check=False, cwd="/")
    if done.returncode != 0:
        raise SystemExit(f"a sample failed for {root}:\n{done.stderr[-4000:]}")
    sample: dict[str, Any] = json.loads(done.stdout.splitlines()[-1])
    expected_file = (root / "packages/py/citry/citry/__init__.py").resolve()
    if Path(sample["citry"]).resolve() != expected_file:
        raise SystemExit(f"the sample for {root} imported {sample['citry']}, not {expected_file}")
    return sample


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--base", type=Path, help="the checkout to compare against")
    parser.add_argument("--head", type=Path, help="the checkout with the change")
    parser.add_argument("--scenario", choices=["filled", "fallback", "chain"], default="filled")
    parser.add_argument("--native", choices=["0", "1"], default="1", help="the value of CITRY_NATIVE_RENDER")
    parser.add_argument("--runs", type=int, default=7, help="samples per side")
    parser.add_argument("--renders", type=int, default=15, help="measured renders per sample")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        _worker(args.scenario, args.renders)
        return
    if args.base is None or args.head is None:
        parser.error("--base and --head are required")

    # Only the parent checks the build: every worker uses the same `citry_core`.
    sys.path.insert(0, str(Path(__file__).parent))
    from native_build import require_release_build  # noqa: PLC0415

    require_release_build()
    sides = {"base": args.base.resolve(), "head": args.head.resolve()}
    seconds: dict[str, list[float]] = {"base": [], "head": []}
    lengths: dict[str, set[int]] = {"base": set(), "head": set()}
    for run in range(args.runs):
        order = ("base", "head") if run % 2 == 0 else ("head", "base")
        for side in order:
            sample = _sample(sides[side], args)
            seconds[side].append(sample["seconds"])
            lengths[side].add(sample["html_length"])
    if lengths["base"] != lengths["head"]:
        print(f"WARNING: the two sides rendered pages of different lengths: {lengths}")
    print(f"scenario={args.scenario} CITRY_NATIVE_RENDER={args.native} runs={args.runs} renders={args.renders}")
    summary = {side: (min(values), statistics.median(values)) for side, values in seconds.items()}
    for side, (low, middle) in summary.items():
        print(f"{side}: min {low * 1000:.3f} ms, median {middle * 1000:.3f} ms ({sides[side]})")
    (base_min, base_median), (head_min, head_median) = summary["base"], summary["head"]
    print(f"change: min {100 * (head_min / base_min - 1):+.2f}%, median {100 * (head_median / base_median - 1):+.2f}%")


if __name__ == "__main__":
    main()
