"""Compare render lifetimes and retained closure scopes without automatic GC."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from weakref import ref

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmarks.settlement_state_probe.adapter import install  # noqa: E402


def worker(changed: bool) -> dict[str, object]:
    """Keep diagnostic references weak until after the automatic-lifetime check."""
    install(changed)
    from citry import Citry, Component  # noqa: PLC0415

    c = Citry()

    class Child(Component):
        citry = c
        template = """
            <c-slot />
        """

    class Page(Component):
        citry = c
        template = """
            <c-child>body</c-child>
        """

    # Warm the fixture and finish earlier collections before observing one render.
    str(Page())
    gc.collect()
    gc.disable()
    result = Page().render()
    component = ref(result.context.component)
    graph = ref(result.context.ownership)
    del result
    alive_before = {"component": component() is not None, "graph": graph() is not None}
    gc.set_debug(gc.DEBUG_SAVEALL)
    collected = gc.collect()
    types = Counter(f"{type(item).__module__}.{type(item).__qualname__}" for item in gc.garbage)
    scopes = [item for item in gc.garbage if type(item).__name__ == "__pyx_scope_struct___settle_render"]
    scope_relations = []
    for scope in scopes:
        children = gc.get_referents(scope)
        callbacks = [item for item in children if type(item).__name__ == "cython_function_or_method"]
        scope_relations.append(
            {
                "callbacks": len(callbacks),
                "callbacks_referencing_scope": sum(
                    any(value is scope for value in gc.get_referents(callback)) for callback in callbacks
                ),
                "retains_render": any(type(item).__name__ == "CitryRender" for item in children),
            }
        )
    return {
        "candidate": changed,
        "alive_before_explicit_collection": alive_before,
        "weakrefs_cleared_after_collection": component() is None and graph() is None,
        "collected": collected,
        "unreachable_types": dict(sorted(types.items())),
        "settlement_scope_relations": scope_relations,
    }


def main() -> None:
    """Archive both observations without treating collection counts as timings."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=("reference", "candidate"))
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(args.worker == "candidate")))
        return
    report = {}
    for variant in ("reference", "candidate"):
        result = subprocess.run(
            [sys.executable, __file__, "--worker", variant], cwd=ROOT, capture_output=True, text=True, check=True
        )
        report[variant] = json.loads(result.stdout)
    report["hashes"] = {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (Path(__file__), Path(__file__).with_name("adapter.py"))
    }
    report["build"] = json.loads((ROOT / "benchmarks/results/repeat-render/settlement-state-build.json").read_text())
    (ROOT / "benchmarks/results/repeat-render/settlement-state-lifetime.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps({variant: report[variant] for variant in ("reference", "candidate")}, indent=2))


if __name__ == "__main__":
    main()
