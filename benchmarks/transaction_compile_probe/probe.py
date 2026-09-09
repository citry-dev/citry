"""Measure native compilation of existing component transaction functions."""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import inspect
import itertools
import json
import os
import statistics
import subprocess
import sys
import sysconfig
import textwrap
import time
from importlib.machinery import ExtensionFileLoader
from pathlib import Path
from shutil import which
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

from benchmarks.ownership_journal_probe.probe import scenario  # noqa: E402

import citry.component_render as runtime  # noqa: E402
import citry.util.id as ids  # noqa: E402
from citry import component, nodes  # noqa: E402
from citry.ownership import OwnershipGraph  # noqa: E402

TARGETS = (
    ("render_one", runtime, runtime, "_render_one", "render-one"),
    ("initialize", component, component.Component, "__init__", "construction"),
    ("construct", component, component.ComponentMeta, "_create_instance", "construction"),
    ("inputs", nodes, nodes.ComponentNode, "_resolve_inputs", "inputs"),
)


def generate(build_root: Path) -> dict[str, Any]:
    """Extract the current functions without changing their statements or types."""
    build_root.mkdir(parents=True, exist_ok=True)
    sources = {}
    for name, module, owner, method, _ in TARGETS:
        function = getattr(owner, method)
        original = textwrap.dedent(inspect.getsource(function))
        tree = ast.parse(original)
        definition = tree.body[0]
        if not isinstance(definition, ast.FunctionDef):
            raise TypeError(f"Expected function source for {name}")
        definition.name = "native_candidate"
        definition.decorator_list = []
        globals_used = sorted(
            {
                item.id
                for item in ast.walk(definition)
                if isinstance(item, ast.Name) and item.id in module.__dict__ and not item.id.startswith("__")
            }
        )
        # Imports preserve the original helper and type objects. Refresh these
        # bindings outside each timed render, just before selecting a candidate.
        source = (
            "from __future__ import annotations\n"
            f"from {module.__name__} import ({', '.join(globals_used)})\n\n" + ast.unparse(tree) + "\n"
        )
        path = build_root / f"transaction_{name}.py"
        path.write_text(source)
        sources[name] = {
            "original_sha256": hashlib.sha256(original.encode()).hexdigest(),
            "generated_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "globals": globals_used,
        }
    setup = """from setuptools import setup
from Cython.Build import cythonize
import Cython
import setuptools
print(f"Cython={Cython.__version__} setuptools={setuptools.__version__}")
setup(ext_modules=cythonize(
    ["transaction_render_one.py", "transaction_initialize.py", "transaction_construct.py", "transaction_inputs.py"],
    compiler_directives={"language_level": 3, "annotation_typing": False, "binding": True, "infer_types": False},
))
"""
    (build_root / "setup.py").write_text(setup)
    return sources


def prepare(build_root: Path, *, build: bool, tool_root: Path) -> tuple[list[Any], dict[str, Any]]:
    """Build or load isolated extension modules and return reversible switches."""
    build_root = build_root.resolve()
    manifest = build_root / "build.json"
    if build:
        sources = generate(build_root)
        env = dict(os.environ, PYTHONPATH=os.pathsep.join((str(tool_root), str(ROOT))))
        result = subprocess.run(
            [sys.executable, "setup.py", "build_ext", "--inplace"],
            cwd=build_root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        (build_root / "build.log").write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(f"Cython build failed; see {build_root / 'build.log'}")
        artifacts = {}
        for name, *_ in TARGETS:
            path = build_root / f"transaction_{name}{sysconfig.get_config_var('EXT_SUFFIX')}"
            artifacts[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest.write_text(
            json.dumps(
                {
                    "python": sys.version,
                    "sources": sources,
                    "artifact_sha256": artifacts,
                    "compiler_directives": {
                        "language_level": 3,
                        "annotation_typing": False,
                        "binding": True,
                        "infer_types": False,
                    },
                },
                indent=2,
            )
            + "\n"
        )
    metadata = json.loads(manifest.read_text())
    sys.path.insert(0, str(build_root))
    switches = []
    artifacts = {}
    for name, module, owner, method, group in TARGETS:
        native = importlib.import_module(f"transaction_{name}")
        native_path = Path(native.__file__).resolve()
        if native_path.parent != build_root or not isinstance(native.__loader__, ExtensionFileLoader):
            raise RuntimeError("The experiment requires compiled extensions from the requested build directory")
        generated_path = build_root / f"transaction_{name}.py"
        if hashlib.sha256(generated_path.read_bytes()).hexdigest() != metadata["sources"][name]["generated_sha256"]:
            raise RuntimeError(f"Generated source changed since build: {name}")
        digest = hashlib.sha256(native_path.read_bytes()).hexdigest()
        if digest != metadata["artifact_sha256"].get(native_path.name):
            raise RuntimeError(f"Compiled artifact changed since build: {name}")
        original = getattr(owner, method)
        source_hash = hashlib.sha256(textwrap.dedent(inspect.getsource(original)).encode()).hexdigest()
        if source_hash != metadata["sources"][name]["original_sha256"]:
            raise RuntimeError(f"Source changed since build: {name}")
        switches.append(
            (
                module,
                owner,
                method,
                group,
                original,
                native.native_candidate,
                native,
                metadata["sources"][name]["globals"],
            )
        )
        artifacts[Path(native.__file__).name] = hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest()
    metadata["artifact_sha256"] = artifacts
    metadata["build_log"] = (build_root / "build.log").read_text()
    return switches, metadata


def main() -> None:
    """Compare complete renders; compilation and import stay outside timing."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--build-root", type=Path, required=True)
    parser.add_argument("--tool-root", type=Path, required=True)
    parser.add_argument("--case", choices=("render-one", "construction", "inputs", "all"), required=True)
    parser.add_argument("--pairs", type=int, default=60)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.pairs < 1:
        parser.error("--pairs must be positive")
    switches, metadata = prepare(args.build_root, build=args.build, tool_root=args.tool_root)

    def switch(candidate: bool) -> None:
        for module, owner, method, group, original, compiled, native, names in switches:
            native.__dict__.update({name: module.__dict__[name] for name in names})
            setattr(owner, method, compiled if candidate and args.case in (group, "all") else original)

    scenario_module = scenario()
    data = scenario_module.gen_render_data()
    original_snapshot = OwnershipGraph.snapshot
    traces = {}
    observations = []
    try:
        for candidate in (False, True):
            switch(candidate)
            for _ in range(6):
                scenario_module.render(data)
            captured = []

            def capture(graph: Any, captured: list[Any] = captured) -> Any:
                value = original_snapshot(graph)
                captured.append(value)
                return value

            OwnershipGraph.snapshot = capture
            ids._id_counter = itertools.count()
            scenario_module.render(data)
            OwnershipGraph.snapshot = original_snapshot
            traces[candidate] = captured
        if traces[False] != traces[True]:
            raise RuntimeError("Native compilation changed ownership snapshots")
        # Prove the selected native methods execute in a separate untimed render.
        switch(candidate=True)
        native_calls = {}
        for _, owner, method, group, _, compiled, _, _ in switches:
            if args.case not in (group, "all"):
                continue
            native_calls[method] = 0

            def counted(*args: Any, _method: str = method, _compiled: Any = compiled, **kwargs: Any) -> Any:
                native_calls[_method] += 1
                return _compiled(*args, **kwargs)

            setattr(owner, method, counted)
        ids._id_counter = itertools.count()
        scenario_module.render(data)
        for pair in range(args.pairs):
            outputs = {}
            for candidate in (False, True) if pair % 2 == 0 else (True, False):
                switch(candidate)
                ids._id_counter = itertools.count()
                start = time.perf_counter_ns()
                outputs[candidate] = scenario_module.render(data)
                elapsed = (time.perf_counter_ns() - start) / 1_000_000
                observations.append({"pair": pair, "candidate": candidate, "ms": elapsed})
            if outputs[False] != outputs[True]:
                raise RuntimeError(f"Native compilation changed HTML in pair {pair}")
    finally:
        OwnershipGraph.snapshot = original_snapshot
        switch(candidate=False)
    savings = []
    for pair in range(args.pairs):
        values = {row["candidate"]: row["ms"] for row in observations if row["pair"] == pair}
        savings.append(values[False] - values[True])
    git = which("git")
    if git is None:
        raise RuntimeError("Recording the experiment requires git")
    report = {
        "case": args.case,
        "runtime_python": sys.version,
        "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "native_calls_in_untimed_render": native_calls,
        "revision": subprocess.check_output([git, "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "build": metadata,
        "pairs": args.pairs,
        "snapshots_compared": len(traces[True]),
        "snapshots_equal": True,
        "all_pairs_html_equal": True,
        "output_bytes": len(outputs[True].encode()),
        "median_paired_saving_ms": statistics.median(savings),
        "favorable_pairs": sum(value > 0 for value in savings),
        "medians_ms": {
            str(candidate): statistics.median(row["ms"] for row in observations if row["candidate"] == candidate)
            for candidate in (False, True)
        },
        "observations": observations,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key not in ("build", "observations")}, indent=2))


if __name__ == "__main__":
    main()
