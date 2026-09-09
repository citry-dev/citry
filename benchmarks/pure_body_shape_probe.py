"""Count live nodes reaching pure-body reuse after constant precomputation."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

import citry.component_render as runtime  # noqa: E402
import citry.util.id as ids  # noqa: E402
from benchmarks.ownership_journal_probe.probe import scenario  # noqa: E402


def main() -> None:
    """Observe one warm render; these counts do not measure optimization savings."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    module = scenario()
    data = module.gen_render_data()
    for _ in range(6):
        module.render(data)
    ids._id_counter = itertools.count()
    expected = module.render(data)
    original_lookup = runtime.pure_body_lookup
    original_capture = runtime._render_and_capture_pure_body
    lookups: Counter[tuple[str, int, int, bool]] = Counter()
    captures: Counter[tuple[str, int]] = Counter()

    def lookup(cls: Any, body: Any, variables: Any, used_vars: Any) -> Any:
        result = original_lookup(cls, body, variables, used_vars)
        live_nodes = sum(not isinstance(item, str) for item in body)
        hit = result is not None and result[1] is not None
        lookups[(cls.__name__, len(body), live_nodes, hit)] += 1
        return result

    def capture(body: Any, context: Any, component: Any) -> Any:
        result = original_capture(body, context, component)
        captures[(type(component).__name__, result[2])] += 1
        return result

    runtime.pure_body_lookup = lookup
    runtime._render_and_capture_pure_body = capture
    try:
        ids._id_counter = itertools.count()
        actual = module.render(data)
    finally:
        runtime.pure_body_lookup = original_lookup
        runtime._render_and_capture_pure_body = original_capture
    if actual != expected or not lookups:
        raise RuntimeError("The diagnostic changed HTML or reached no pure-body lookup")
    report = {
        "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),  # noqa: S607
        "html_equal": True,
        "timing_measured": False,
        "lookups": [
            {"class": cls, "body_items": size, "live_nodes": live, "cache_hit": hit, "calls": calls}
            for (cls, size, live, hit), calls in sorted(lookups.items())
        ],
        "captures": [
            {"class": cls, "cached_node_count": count, "calls": calls}
            for (cls, count), calls in sorted(captures.items())
        ],
        "hashes": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                Path(__file__).resolve(),
                Path(runtime.__file__),
                ROOT / "packages/py/citry/citry/_pure.py",
                ROOT / "packages/py/citry/tests/test_benchmark_citry.py",
            )
        },
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
