"""Print a reproducible, scope-limited baseline for protocol runtime work."""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import importlib.util
import json
import platform
import statistics
import subprocess
import sys
import timeit
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCOPE = (
    ".github/workflows/py--citry--publish.yml",
    ".github/workflows/py--tests-cross-browser.yml",
    ".github/workflows/py--tests.yml",
    ".github/workflows/repo--check.yml",
    "benchmarks/client_scenario.py",
    "docs/agent/INDEX.md",
    "docs/codebase.md",
    "docs/design/protocol_runtime_ownership.md",
    "package.json",
    "packages/js/citry-client",
    "packages/protocol",
    "packages/py/citry/citry/ext/dependencies/client/citry.js",
    "packages/py/citry/citry/ext/events",
    "packages/py/citry/citry/ownership_manifest.py",
    "packages/py/citry/citry",
    "packages/py/citry/LICENSE",
    "packages/py/citry/pyproject.toml",
    "packages/py/citry/tests/e2e/test_client_graph_corpus_e2e.py",
    "packages/py/citry/tests/e2e/test_events_applier_e2e.py",
    "packages/py/citry/tests/e2e/test_events_transport_e2e.py",
    "packages/py/citry/tests/test_client_graph_conformance.py",
    "packages/py/citry/tests/test_client_graph_protocol_package.py",
    "packages/py/citry/tests/test_distribution_artifacts.py",
    "packages/py/citry/tests/test_events_conformance.py",
    "packages/py/citry/tests/test_events_protocol_package.py",
    "packages/py/citry/tests/test_ownership_manifest.py",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
    "scripts/check.py",
    "scripts/protocol_runtime_baseline.py",
    "scripts/verify_citry_distribution.py",
)
SCHEMAS = (
    "packages/protocol/client_graph/v1/manifest.schema.json",
    "packages/protocol/events/v1/call.schema.json",
    "packages/protocol/events/v1/descriptor.schema.json",
    "packages/protocol/events/v1/manifest.schema.json",
    "packages/protocol/events/v1/result.schema.json",
)
BUNDLES = (
    "packages/py/citry/citry/ext/dependencies/client/citry.js",
    "packages/py/citry/citry/ext/events/client/citry-events.js",
)


def _run(*args: str, check: bool = True) -> bytes:
    completed = subprocess.run(
        args,
        cwd=ROOT,
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    return completed.stdout


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _git_identity(path: str, revision: str) -> str | None:
    completed = subprocess.run(
        ("git", "rev-parse", f"{revision}:{path}"),
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def _scoped_files(include_details: bool) -> dict[str, Any]:
    paths = sorted(
        path
        for path in _run("git", "ls-files", "--cached", "--others", "--exclude-standard", "--", *SCOPE)
        .decode()
        .splitlines()
        if path
    )
    identities: list[dict[str, str | None]] = []
    digest_input = bytearray()
    for path in paths:
        absolute = ROOT / path
        worktree = _sha256(absolute.read_bytes()) if absolute.is_file() else None
        item = {
            "path": path,
            "worktreeSha256": worktree,
            "indexBlob": _git_identity(path, ""),
            "headBlob": _git_identity(path, "HEAD"),
        }
        identities.append(item)
        digest_input.extend(json.dumps(item, sort_keys=True, separators=(",", ":")).encode())
        digest_input.append(0)
    status = _run("git", "status", "--porcelain=v1", "-z", "--", *SCOPE)
    result: dict[str, Any] = {
        "pathCount": len(paths),
        "statusSha256": _sha256(status),
        "contentIdentitySha256": _sha256(bytes(digest_input)),
    }
    if include_details:
        result["files"] = identities
    return result


def _tree_digest(relative: str) -> str:
    digest_input = bytearray()
    labels = sorted(
        label
        for label in _run("git", "ls-files", "--cached", "--others", "--exclude-standard", "--", relative)
        .decode()
        .splitlines()
        if label
    )
    for label in labels:
        path = ROOT / label
        digest_input.extend(label.encode())
        digest_input.append(0)
        digest_input.extend(hashlib.sha256(path.read_bytes()).digest())
    return _sha256(bytes(digest_input))


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        msg = f"Cannot load {path}"
        raise RuntimeError(msg)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _timings() -> dict[str, Any]:
    scenario = _load_module("protocol_baseline_client_scenario", ROOT / "benchmarks/client_scenario.py")
    result: dict[str, Any] = {"repeat": 7}
    for count, number in ((25, 10), (325, 5)):
        workload = scenario.build_client_scenario(count)
        samples = timeit.repeat(workload.document, repeat=7, number=number)
        sizes = scenario.payload_sizes(workload.document())
        result[f"graphDocument{count}"] = {
            "numberPerSample": number,
            "medianMilliseconds": statistics.median(samples) * 1000 / number,
            "sizes": {
                "graphRaw": sizes.graph_raw,
                "graphGzip": sizes.graph_gzip,
                "documentRaw": sizes.document_raw,
                "documentGzip": sizes.document_gzip,
            },
        }

    conformance = _load_module(
        "protocol_baseline_events_conformance",
        ROOT / "packages/py/citry/tests/test_events_conformance.py",
    )
    engine, counter = conformance._conformance_surface()
    instance_id, class_id, token, _values = conformance._render_live_instance(counter)
    entry = next(item for item in conformance.INDEX if item["call"] == "data_only.call.json")
    single, kwargs = conformance._arrange_call(
        entry,
        conformance._load(entry, "call"),
        comp_cls=counter,
        instance_id=instance_id,
        class_id=class_id,
        token=token,
    )
    dispatcher = conformance.EventsDispatcher()
    context = conformance.TransportContext(transport="protocol-baseline", citry=engine)

    def measure(envelope: dict[str, Any], number: int) -> float:
        def dispatch() -> None:
            dispatcher.dispatch(copy.deepcopy(envelope), context, **kwargs)

        samples = timeit.repeat(dispatch, repeat=7, number=number)
        return statistics.median(samples) * 1_000_000 / number

    batch = copy.deepcopy(single)
    batch["requestId"] = "protocol-baseline-batch"
    batch["calls"] = [copy.deepcopy(single["calls"][0]) for _ in range(16)]
    result["eventsSingleDispatch"] = {"numberPerSample": 200, "medianMicroseconds": measure(single, 200)}
    result["events16Dispatch"] = {"numberPerSample": 100, "medianMicroseconds": measure(batch, 100)}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--details", action="store_true", help="Include every scoped path and content identity.")
    parser.add_argument("--timings", action="store_true", help="Run the bounded local timing comparison.")
    args = parser.parse_args()

    bundle_bytes = [(ROOT / path).read_bytes() for path in BUNDLES]
    combined = b"".join(bundle_bytes)
    data: dict[str, Any] = {
        "format": "citry-protocol-runtime-baseline/1",
        "repository": {
            "commit": _run("git", "rev-parse", "HEAD").decode().strip(),
            "branch": _run("git", "branch", "--show-current").decode().strip(),
            "scope": list(SCOPE),
            **_scoped_files(args.details),
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "node": _run("node", "--version").decode().strip(),
            "pnpm": _run("pnpm", "--version").decode().strip(),
        },
        "schemas": {
            path: _sha256(
                json.dumps(
                    json.loads((ROOT / path).read_text(encoding="utf-8")), sort_keys=True, separators=(",", ":")
                ).encode()
            )
            for path in SCHEMAS
        },
        "testTrees": {
            "clientGraph": _tree_digest("packages/protocol/client_graph/v1/tests"),
            "events": _tree_digest("packages/protocol/events/v1/tests"),
        },
        "bundles": {
            path: {"sha256": _sha256(value), "rawBytes": len(value)}
            for path, value in zip(BUNDLES, bundle_bytes, strict=True)
        },
        "combinedBundle": {
            "rawBytes": len(combined),
            "gzipBytes": len(gzip.compress(combined, mtime=0)),
        },
    }
    if args.timings:
        data["timings"] = _timings()
    json.dump(data, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
