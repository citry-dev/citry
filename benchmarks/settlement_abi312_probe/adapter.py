"""Choose three compiled modules before any Citry imports occur."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "benchmarks/results/repeat-render/settlement-abi312-build.json"


class Finder:
    """Preserve normal submodule discovery beneath the compiled node package."""

    def __init__(self, modules: dict[str, Any]) -> None:
        self.modules = modules

    def find_spec(self, fullname: str, _path: Any = None, _target: Any = None) -> Any:
        metadata = self.modules.get(fullname)
        if metadata is None:
            return None
        if fullname == "citry.nodes":
            return importlib.util.spec_from_file_location(
                fullname,
                metadata["artifact"],
                submodule_search_locations=[str(ROOT / "packages/py/citry/citry/nodes")],
            )
        return importlib.util.spec_from_file_location(fullname, metadata["artifact"])


def install(changed: bool) -> dict[str, Any]:
    """Reject stale inputs and choose all three modules as one variant."""
    if changed and sys.version_info < (3, 12):
        raise RuntimeError("This experimental ABI target requires CPython 3.12 or newer")
    if any(name == "citry" or name.startswith("citry.") for name in sys.modules):
        raise RuntimeError("Choose the experiment before importing Citry")
    report = json.loads(REPORT.read_text())
    if report["returncode"]:
        raise RuntimeError("The three-module build did not succeed")
    for metadata in report["modules"].values():
        if hashlib.sha256((ROOT / metadata["source"]).read_bytes()).hexdigest() != metadata["source_sha256"]:
            raise RuntimeError("Production source changed after compilation")
        if hashlib.sha256(Path(metadata["artifact"]).read_bytes()).hexdigest() != metadata["artifact_sha256"]:
            raise RuntimeError("Compiled module changed after the build")
    if changed:
        sys.meta_path.insert(0, Finder(report["modules"]))
    return report
