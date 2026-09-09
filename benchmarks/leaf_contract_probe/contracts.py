"""Check selected icon output, ownership and explicit input restrictions."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmarks.leaf_contract_probe import adapter  # noqa: E402
from benchmarks.ownership_journal_probe.probe import scenario  # noqa: E402
from benchmarks.render_structure_probe.census import canonical, digest  # noqa: E402
from benchmarks.template_function_probe.contracts import CustomText, HtmlObject  # noqa: E402

import citry.util.id as ids  # noqa: E402
from citry import Component, Const, component_render  # noqa: E402
from citry.ownership import OwnershipGraph  # noqa: E402
from citry.util.html import Markup  # noqa: E402


def main() -> None:
    """Compare full values in memory and retain compact evidence for this bounded case."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=("reuse", "contract"), default="contract")
    args = parser.parse_args()
    module = scenario()

    class Host(Component):
        citry = module.app
        template = """
<div><c-heroicons c-bind="icon" /></div>
"""

    class SlotHost(Component):
        citry = module.app
        template = """
<c-heroicons name="home">body</c-heroicons>
"""

    class RepeatHost(Component):
        citry = module.app
        template = """
<div><c-heroicons c-for="icon in icons" c-bind="icon" /></div>
"""

    original_render = component_render._render_one
    original_finalize = component_render._finalize
    original_snapshot = OwnershipGraph.snapshot
    original_fail = OwnershipGraph.fail_invocation
    snapshots = []

    def snapshot(graph: Any) -> Any:
        result = original_snapshot(graph)
        snapshots.append(canonical(result))
        return result

    def fail(graph: Any, invocation: Any) -> Any:
        result = original_fail(graph, invocation)
        snapshots.append(canonical(original_snapshot(graph)))
        return result

    OwnershipGraph.fail_invocation = fail
    OwnershipGraph.snapshot = snapshot

    def run(call: Any, enabled: bool, *, configure: bool = True) -> tuple[str, list[Any]]:
        if configure:
            component_render._render_one = original_render
            component_render._finalize = original_finalize
            adapter.install(module, enabled, variant=args.variant)
        ids._id_base = 123456
        ids._id_counter = itertools.count()
        snapshots.clear()
        output = call()
        return output, list(snapshots)

    compared = {}
    data = module.gen_render_data()
    for label, values in (("large", data), ("one_output", {**data, "outputs": data["outputs"][:1]})):
        for repeat in range(2):
            expected = run(lambda values=values: module.render(values), enabled=False)
            actual = run(lambda values=values: module.render(values), enabled=True)
            if actual != expected or len(actual[1]) != 4:
                raise AssertionError(f"Full page HTML/ownership mismatch: {label}/{repeat}")
            compared[f"{label}_{repeat}"] = {"html": digest(actual[0]), "snapshots": [digest(x) for x in actual[1]]}
    values = [
        {"name": "home"},
        {"name": Const(Const("plus")), "size": Const(18)},
        {"name": "home", "variant": "solid", "color": "red", "viewbox": "0 0 30 30"},
        {"name": "home", "attrs": {"title": "'\"<>&", "aria-hidden": False, "width": 0}},
        {"name": "home", "attrs": {"class": ["a", {"b": True}], "style": {"color": "red"}}},
    ]
    expected_icons = [run(lambda inputs=inputs: str(Host(icon=inputs)), enabled=False) for inputs in values]
    for index, inputs in enumerate(values):
        expected = expected_icons[index]
        actual = run(lambda inputs=inputs: str(Host(icon=inputs)), enabled=True, configure=index == 0)
        if actual != expected:
            raise AssertionError(f"Icon HTML/ownership mismatch: {index}")
        compared[f"icon_{index}"] = {"html": actual[0], "snapshots": [digest(x) for x in actual[1]]}
    # Repeated calls inside one root must replay detached output with fresh IDs.
    original_lookup = adapter.pure_body_lookup
    reuse_hits = []

    def lookup(*arguments: Any) -> Any:
        result = original_lookup(*arguments)
        reuse_hits.append(result is not None and result[1] is not None)
        return result

    adapter.pure_body_lookup = lookup
    repeated_inputs = [{"name": "home", "attrs": {"title": "same"}}] * 2 + [
        {"name": "home", "attrs": {"title": "different"}},
    ]
    expected = run(lambda: str(RepeatHost(icons=repeated_inputs)), enabled=False)
    actual = run(lambda: str(RepeatHost(icons=repeated_inputs)), enabled=True)
    adapter.pure_body_lookup = original_lookup
    if actual != expected or reuse_hits != [False, True, False]:
        raise AssertionError("Repeated icons did not retain output/ownership and expected body reuse")
    compared["repeated_icons"] = {
        "html": actual[0],
        "snapshots": [digest(x) for x in actual[1]],
        "cache_hits": reuse_hits,
    }
    # Both engines still reject schema errors and the application's invalid variant.
    errors = {}
    for label, inputs in (
        ("variant", {"name": "home", "variant": "bad"}),
        ("unknown_kwarg", {"name": "home", "unknown": 1}),
    ):
        kinds = []
        failures = []
        for enabled in (False, True):
            try:
                run(lambda inputs=inputs: str(Host(icon=inputs)), enabled)
            except (TypeError, ValueError) as error:
                kinds.append(type(error).__name__)
                failures.append((list(snapshots), next(ids._id_counter)))
            else:
                raise AssertionError(f"Invalid input accepted: {label}")
        if failures[0] != failures[1]:
            raise AssertionError(f"Failed ownership or ID consumption changed: {label}")
        if len(set(kinds)) != 1:
            raise AssertionError(f"Error class changed: {label}")
        errors[label] = kinds
    cycle = []
    cycle.append(cycle)
    rejected = {}
    invalid = {
        "markup": {"class": Markup("safe")},
        "html_callback": {"title": HtmlObject()},
        "subclass": {"class": CustomText("a")},
        "cycle": {"class": cycle},
        "alpine": {"x-data": "{}"},
        "events": {"@click": "go()"},
        "client_props": {"$c-props": {}},
        "unknown_attribute": {"data-custom": "a"},
        "non_string_key": {1: "a"},
        "component_value": {"title": Host(icon={"name": "home"})},
    }
    for label, attrs in invalid.items():
        try:
            run(lambda attrs=attrs: str(Host(icon={"name": "home", "attrs": attrs})), enabled=True)
        except (TypeError, ValueError) as error:
            rejected[label] = type(error).__name__
        else:
            raise AssertionError(f"Unsupported attributes accepted: {label}")
    try:
        run(lambda: str(SlotHost()), enabled=True)
    except TypeError as error:
        rejected["slots"] = type(error).__name__
    else:
        raise AssertionError("Supplied slots accepted")
    for label, call in (
        ("direct_root", lambda: str(module.HeroIcon(name="home"))),
        ("render_globals", lambda: str(Host(icon={"name": "home"}).render(template_globals={"global_value": 1}))),
    ):
        try:
            run(call, enabled=True)
        except TypeError as error:
            rejected[label] = type(error).__name__
        else:
            raise AssertionError(f"Unsupported mode accepted: {label}")
    # Mutating caller data between renders must remain visible without input mutation.
    inputs = {"name": "home", "attrs": {"title": "first"}}
    first = run(lambda inputs=inputs: str(Host(icon=inputs)), enabled=True)[0]
    inputs["attrs"]["title"] = "second"
    second = run(lambda inputs=inputs: str(Host(icon=inputs)), enabled=True, configure=False)[0]
    if first == second or inputs["attrs"] != {"title": "second"}:
        raise AssertionError("Stale output or mutated caller input")
    component_render._render_one = original_render
    component_render._finalize = original_finalize
    OwnershipGraph.snapshot = original_snapshot
    OwnershipGraph.fail_invocation = original_fail
    paths = [
        Path(__file__),
        Path(adapter.__file__),
        Path(__file__).with_name("plan.md"),
        ROOT / "benchmarks/template_function_probe/runtime.py",
    ]
    print(
        json.dumps(
            {
                "variant": args.variant,
                "compared": compared,
                "errors": errors,
                "rejected": rejected,
                "mutable_input": "passed",
                "hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
