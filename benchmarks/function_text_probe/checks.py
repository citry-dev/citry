"""Check direct function emission against complete output and relationships from iteration 66."""

from __future__ import annotations

import hashlib
import io
import json
import sys
from collections import Counter
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

from benchmarks.composed_function_probe import contracts, probe  # noqa: E402
from benchmarks.composed_function_probe.adapter import installed as composed_installed  # noqa: E402
from benchmarks.function_text_probe.adapter import installed  # noqa: E402
from benchmarks.ownership_journal_probe.probe import scenario  # noqa: E402

from citry import Component  # noqa: E402
from citry.citry_render import CitryRender  # noqa: E402


def observe(module: Any, call: Any, enabled: bool) -> dict[str, Any]:
    """Keep the existing relationship observer around either immediate implementation."""
    with patch.object(probe, "installed", lambda m, _v, counts=None: installed(m, enabled, counts)):
        return probe.observe(module, call, "immediate")


def same(control: dict[str, Any], candidate: dict[str, Any]) -> None:
    """Require framework metadata as well as visible HTML and all captured relationships."""
    for key in ("raw_html", "snapshots", "candidate_counts", "component_calls", "generated_ids"):
        if control[key] != candidate[key]:
            raise AssertionError(f"Direct function emission changed {key}")


def main() -> None:
    module = scenario()
    data = module.gen_render_data()
    full_cases = {}
    for label, inputs in (("large", data), ("one_output", {**data, "outputs": data["outputs"][:1]})):
        control = observe(module, lambda inputs=inputs: module.render(inputs), enabled=False)
        candidate = observe(module, lambda inputs=inputs: module.render(inputs), enabled=True)
        same(control, candidate)
        expected = (
            {"Button": 114, "Icon": 40, "HeroIcon": 41, "outlets": 154, "svg_replays": 32}
            if label == "large"
            else {"Button": 19, "Icon": 22, "HeroIcon": 23, "outlets": 41, "svg_replays": 17}
        )
        if candidate["candidate_counts"] != expected:
            raise AssertionError("Function activation changed")
        full_cases[label] = {"raw_html_and_snapshots_equal": True, "counts": expected, "bytes": candidate["bytes"]}

    class ProbeChild(Component):
        citry = module.app
        name = "probe-child"

        class Kwargs:
            value: str

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"value": kwargs.value}

        template = """
<b>{{ value }}</b>
"""
        js = """
window.__functionTextChild = true;
"""

    class LoopHost(Component):
        citry = module.app

        class Kwargs:
            values: list

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"values": kwargs.values}

        template = """
<c-Button>
    <c-for each="value in values">
        <c-probe-child c-value="value" />
        <c-Icon name="home">{{ value }}</c-Icon>
    </c-for>
    <c-empty>empty</c-empty>
</c-Button>
"""

    class TransparentHost(Component):
        citry = module.app
        transparent = True
        template = """
<c-Button>text<c-probe-child value="child" /></c-Button>
"""

    class MixedHost(Component):
        citry = module.app

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"foreign": ProbeChild(value="already rendered").render()}

        template = """
<c-Button>{{ foreign }}<c-probe-child value="deferred child" /></c-Button>
"""

    class ReplaceHost(Component):
        citry = module.app
        name = "replace-host"

        def on_render(self) -> Any:
            yield
            return "<p>replacement</p>"

        template = """
<c-Button><c-probe-child value="retired child" /><c-slot /></c-Button>
"""

    class ReplaceRoot(Component):
        citry = module.app
        template = """
<c-replace-host><i>supplied slot content</i></c-replace-host>
"""

    class InvalidInput(Component):
        citry = module.app

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"value": object()}

        template = """
<c-Button c-attrs="value" />
"""

    class PartialFailure(Component):
        citry = module.app

        def on_render(self) -> Any:
            _, error = yield
            return "<p>recovered</p>" if error is not None else None

        template = """
<c-Button><c-probe-child value="not executed" />{{ 1 / 0 }}</c-Button>
"""

    class RecoveredChild(Component):
        citry = module.app
        name = "recovered-child"

        def on_render(self) -> Any:
            _, error = yield
            return "<i>recovered child</i>" if error is not None else None

        template = """
{{ 1 / 0 }}
"""

    taints = []

    class TaintedHost(Component):
        citry = module.app

        def on_render(self) -> Any:
            result, error = yield
            if error is not None:
                raise error
            taints.append(result.context._error_tainted)

        template = """
<c-Button><c-Icon name="home"><c-recovered-child /></c-Icon></c-Button>
"""

    special = {}
    for label, call in (
        ("empty_loop", lambda: str(LoopHost(values=[]))),
        ("loop_with_children_and_dependencies", lambda: str(LoopHost(values=["one<&", "two"]))),
        ("changed_loop", lambda: str(LoopHost(values=["changed"]))),
        ("transparent_caller", lambda: str(TransparentHost())),
        ("completed_and_deferred_children", lambda: str(MixedHost())),
        ("replace_caller_output_with_child_and_slot", lambda: str(ReplaceRoot())),
        ("partial_failure", lambda: str(PartialFailure())),
        ("child_error_taint", lambda: str(TaintedHost())),
    ):
        control, candidate = observe(module, call, enabled=False), observe(module, call, enabled=True)
        same(control, candidate)
        special[label] = {"raw_html_and_snapshots_equal": True, "counts": candidate["candidate_counts"]}
    if taints != [True, True]:
        raise AssertionError("Recovered child error did not reach the caller's cache-taint state")
    invalid = []
    for enabled in (False, True):
        with installed(module, enabled):
            try:
                str(InvalidInput())
            except TypeError as error:
                invalid.append(str(error))
            else:
                raise AssertionError("Expected unsupported input rejection")
    if len(invalid) != 2 or invalid[0] != invalid[1]:
        raise AssertionError("Invalid-input error text changed")

    # Reuse broad input, slot, callback-order and cleanup cases without editing their source.
    def mode(m: Any, variant: str, counts: dict[str, int] | None = None) -> Any:
        return (
            installed(m, enabled=True, counts=counts)
            if variant == "immediate"
            else composed_installed(m, variant, counts)
        )

    captured = io.StringIO()
    with patch.object(contracts, "installed", mode), patch.object(probe, "installed", mode), redirect_stdout(captured):
        contracts.main()
    construction_counts = {}
    original_init = CitryRender.__init__
    count: Counter[str] = Counter()

    def constructed(result: CitryRender, *values: Any, **kwargs: Any) -> None:
        original_init(result, *values, **kwargs)
        count[type(result).__name__] += 1

    for enabled in (False, True):
        count.clear()
        with patch.object(CitryRender, "__init__", constructed):
            observe(module, lambda: module.render(data), enabled)
        construction_counts["candidate" if enabled else "control"] = dict(count)
    paths = [*Path(__file__).parent.glob("*.py"), Path(__file__).with_name("plan.md")]
    paths.extend((ROOT / "benchmarks/composed_function_probe").glob("*.py"))
    report = {
        "qualification_only": True,
        "full_cases": full_cases,
        "special_cases": special,
        "error_taints": taints,
        "invalid_input_errors": invalid,
        "constructor_counts": construction_counts,
        "reused_contracts": json.loads(captured.getvalue()),
        "reused_contract_modes": "immediate uses direct emission; other modes retain iteration 66 implementations",
        "hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
