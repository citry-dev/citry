"""Check fresh payload classes when only constructor compilation is reused."""

from __future__ import annotations

import argparse
import gc
import hashlib
import itertools
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from compile_probe import ROOT, constructor_code, ids, install, provide_module, scenario


def census(changed: bool) -> dict[str, Any]:
    """Collect one discarded render in a fresh process, outside all timing."""
    install(changed)
    ids._id_base = 123456
    module = scenario()
    data = module.gen_render_data()
    for _ in range(6):
        module.render(data)
    gc.collect()
    previous_debug = gc.get_debug()
    previous_enabled = gc.isenabled()
    try:
        # Keep unreachable objects until the census; ordinary timing never does this.
        gc.disable()
        ids._id_counter = itertools.count()
        output = module.render(data)
        digest = hashlib.sha256(output.encode()).hexdigest()
        del output
        gc.set_debug(gc.DEBUG_SAVEALL)
        collected = gc.collect()
        counts = Counter(type(value).__module__ + "." + type(value).__qualname__ for value in gc.garbage)
        classes = [
            {"module": value.__module__, "name": value.__qualname__, "fields": value.__dict__.get("_fields")}
            for value in gc.garbage
            if isinstance(value, type)
        ]
        garbage_ids = {id(value) for value in gc.garbage}
        pending = [value for value in gc.garbage if isinstance(value, type)]
        reached = set()
        while pending:
            value = pending.pop()
            if id(value) in reached:
                continue
            reached.add(id(value))
            pending.extend(child for child in gc.get_referents(value) if id(child) in garbage_ids)
        return {
            "unreachable": collected,
            "saved_objects": len(gc.garbage),
            "types": dict(counts.most_common()),
            "classes": classes,
            "objects_reachable_from_classes_within_garbage": len(reached),
            "html_digest": digest,
            "python": sys.version,
        }
    finally:
        gc.set_debug(previous_debug)
        gc.garbage.clear()
        if previous_enabled:
            gc.enable()
        install(changed=False)


def counterexamples(changed: bool) -> dict[str, Any]:
    """Compare class identity and later payloads after an earlier class edit."""
    constructor_code.cache_clear()
    install(changed)
    try:
        first = provide_module.make_provided({"value": 1})
        second = provide_module.make_provided({"value": 2})
        same_type = type(first) is type(second)
        type(first).value = 999
        third = provide_module.make_provided({"value": 3})
        return {"same_type": same_type, "later_attribute": third.value, "later_tuple_item": third[0]}
    finally:
        # Keep each observation independent of prior constructor-cache contents.
        constructor_code.cache_clear()
        install(changed=False)


def main() -> None:
    """Retain diagnostic observations separately from adoption measurements."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gc-worker", choices=("reference", "candidate"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.gc_worker:
        print(json.dumps(census(args.gc_worker == "candidate")))
        return
    if args.output is None:
        parser.error("The parent requires --output")
    observations = {}
    for variant in ("reference", "candidate"):
        result = subprocess.run(
            [sys.executable, __file__, "--gc-worker", variant],
            cwd=ROOT,
            env={**os.environ, "PYTHONHASHSEED": "20260914"},
            capture_output=True,
            text=True,
            check=True,
        )
        observations[variant] = json.loads(result.stdout)
    examples = {name: counterexamples(name == "candidate") for name in ("reference", "candidate")}
    if observations["reference"]["html_digest"] != observations["candidate"]["html_digest"]:
        raise RuntimeError("Constructor-code reuse changed diagnostic HTML")
    if examples["reference"] != examples["candidate"]:
        raise RuntimeError("Constructor-code reuse changed class identity or edit isolation")
    report = {
        "production_qualified": False,
        "census": observations,
        "identity_and_class_edit_checks": examples,
        "hashes": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (Path(__file__).resolve(), Path(__file__).with_name("compile_probe.py"))
        },
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
