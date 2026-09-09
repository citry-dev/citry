"""Select one compiled ownership module before Citry is imported."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "benchmarks/results/performance-render/ownership-module-build.json"


class Finder:
    """Redirect only citry.ownership to the qualified experiment artifact."""

    def __init__(self, artifact: Path) -> None:
        self.artifact = artifact

    def find_spec(self, fullname: str, _path: Any = None, _target: Any = None) -> Any:
        if fullname == "citry.ownership":
            return importlib.util.spec_from_file_location(fullname, self.artifact)
        return None


def install(changed: bool) -> dict[str, Any]:
    """Verify build inputs and choose the module before any ownership objects exist."""
    if "citry.ownership" in sys.modules:
        raise RuntimeError("The ownership experiment must be selected before importing Citry")
    report = json.loads(REPORT.read_text())
    if report["returncode"]:
        raise RuntimeError("The ownership module build did not succeed")
    source = ROOT / "packages/py/citry/citry/ownership.py"
    if hashlib.sha256(source.read_bytes()).hexdigest() != report["source_sha256"]:
        raise RuntimeError("Ownership source changed after the experiment build")
    artifact = Path(report["artifact"])
    if hashlib.sha256(artifact.read_bytes()).hexdigest() != report["artifact_sha256"]:
        raise RuntimeError("The compiled ownership artifact changed after the build")
    if changed:
        sys.meta_path.insert(0, Finder(artifact))
    return report
