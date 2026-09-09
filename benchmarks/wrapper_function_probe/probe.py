"""Compare wrapper output and record the work omitted by the changed contract."""

from __future__ import annotations

import difflib
import gzip
import hashlib
import itertools
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

from benchmarks.ownership_journal_probe.probe import scenario  # noqa: E402
from benchmarks.render_structure_probe.census import canonical, digest  # noqa: E402
from benchmarks.wrapper_function_probe.adapter import installed  # noqa: E402

import citry.util.id as ids  # noqa: E402
from citry import component_render as runtime  # noqa: E402
from citry._protocol.client_graph import validate_manifest  # noqa: E402
from citry.ownership import OwnershipGraph  # noqa: E402


def content_projection(output: str, names: dict[str, str]) -> tuple[str, list[Any]]:
    """Compare application HTML and dependency payloads; graph equality is not claimed."""
    manifests = []

    def remove_graph(match: re.Match[str]) -> str:
        wire = json.loads(match[1])
        if validate_manifest(wire) is not None:
            raise AssertionError("Invalid emitted browser graph")
        manifests.append(wire)
        return ""

    output = re.sub(
        r'<script type="application/json" data-citry-graph>(.*?)</script>', remove_graph, output, flags=re.DOTALL
    )
    for wire in manifests:
        output = output.replace(wire["revision"], "normalized-graph-revision")
    output = re.sub(r"<!--citry:g1:[^>]*-->", "", output)
    output = re.sub(r' data-cid(?:-[a-z0-9]+)?(?:="[^"]*")?', "", output)
    output = re.sub(r'(?: data-citry-root)(?:="[^"]*")?', "", output)
    for render_id, name in names.items():
        output = output.replace(render_id, name)
    return output, manifests


def observe(module: Any, call: Any, enabled: bool) -> dict[str, Any]:
    """Measure operation counts outside timing and retain raw relationship snapshots."""
    snapshots = []
    original_snapshot = OwnershipGraph.snapshot
    original_render = runtime._render_one
    calls: Counter[str] = Counter()
    candidate_counts: dict[str, int] = {}

    def snapshot(graph: Any) -> Any:
        result = original_snapshot(graph)
        snapshots.append(result)
        return result

    def render(element: Any, parent: Any = None, provides: Any = None) -> Any:
        calls[element.comp_cls.__name__] += 1
        return original_render(element, parent, provides)

    ids._id_base = 123456
    ids._id_counter = itertools.count()
    OwnershipGraph.snapshot = snapshot
    runtime._render_one = render
    try:
        with installed(module, enabled, candidate_counts):
            output = call()
        generated = next(ids._id_counter)
    finally:
        OwnershipGraph.snapshot = original_snapshot
        runtime._render_one = original_render
    names = {}
    counts: Counter[str] = Counter()
    for snapshot_value in snapshots:
        for row in snapshot_value.logical_instances:
            if row.render_id not in names:
                counts[row.class_id] += 1
                names[row.render_id] = f"render_{row.class_id}_{counts[row.class_id]}"
    projected, manifests = content_projection(output, names)
    return {
        "raw_html": output,
        "names": names,
        "projected_html": projected,
        "projected_digest": digest(projected),
        "bytes": len(output.encode()),
        "generated_ids": generated,
        "component_calls": dict(calls),
        "candidate_counts": candidate_counts,
        "snapshots": [canonical(s) for s in snapshots],
        "browser_manifests": manifests,
        "snapshot_counts": [{key: len(getattr(s, key)) for key in s.__dataclass_fields__} for s in snapshots],
        "browser_graph_counts": [
            {key: len(value) for key, value in graph.items() if isinstance(value, list)}
            for wire in manifests
            for graph in wire["graphs"]
        ],
    }


def compare(reference: dict[str, Any], candidate: dict[str, Any]) -> None:
    """Require full projected content and unchanged nonselected component execution counts."""
    if reference["projected_html"] != candidate["projected_html"]:
        Path("/tmp/wrapper-function-content.diff").write_text(  # noqa: S108
            "".join(
                difflib.unified_diff(
                    reference["projected_html"].splitlines(keepends=True),
                    candidate["projected_html"].splitlines(keepends=True),
                )
            )
        )
        raise AssertionError("Application output differs; see /tmp/wrapper-function-content.diff")
    expected = dict(reference["component_calls"])
    selected = expected.pop("Button")
    if candidate["component_calls"] != expected:
        raise AssertionError("Unexpected nonselected component execution counts")
    if candidate["candidate_counts"] != {"callbacks": selected, "outlets": selected}:
        raise AssertionError("Wrapper did not replace every selected call and outlet")
    if reference["generated_ids"] - candidate["generated_ids"] != selected:
        raise AssertionError("Unexpected generated identity count")


def main() -> None:
    module = scenario()
    data = module.gen_render_data()
    results = []
    for label, inputs in (("large", data), ("one_output", {**data, "outputs": data["outputs"][:1]})):
        reference = observe(module, lambda inputs=inputs: module.render(inputs), enabled=False)
        candidate = observe(module, lambda inputs=inputs: module.render(inputs), enabled=True)
        compare(reference, candidate)
        for row in (reference, candidate):
            row.pop("raw_html")
            row.pop("names")
            row.pop("projected_html")
        results.append({"case": label, "reference": reference, "candidate": candidate})
    raw = []
    for case in results:
        for variant in ("reference", "candidate"):
            row = case[variant]
            snapshots = row.pop("snapshots")
            row["snapshot_digests"] = [digest(snapshot) for snapshot in snapshots]
            raw.append(
                {
                    "case": case["case"],
                    "variant": variant,
                    "snapshots": snapshots,
                    "browser_manifests": row.pop("browser_manifests"),
                }
            )
    archive = ROOT / "benchmarks/results/repeat-render/wrapper-function-snapshots.json.gz"
    archive.write_bytes(gzip.compress(json.dumps(raw, separators=(",", ":")).encode(), mtime=0))
    paths = [
        Path(__file__),
        Path(__file__).with_name("adapter.py"),
        Path(__file__).with_name("plan.md"),
        ROOT / "benchmarks/leaf_contract_probe/adapter.py",
        ROOT / "benchmarks/template_function_probe/runtime.py",
        ROOT / "packages/py/citry/tests/test_benchmark_citry.py",
    ]
    print(
        json.dumps(
            {
                "diagnostic_only": True,
                "graph_equality_not_claimed": True,
                "snapshot_archive": {
                    "path": str(archive.relative_to(ROOT)),
                    "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                },
                "cases": results,
                "hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
