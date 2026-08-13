"""Integrity checks for local Image documentation fixtures."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import yaml

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "static/img/ui/image"
SNIPPET_ROOT = Path(__file__).resolve().parents[2] / "packages/py/citry_ui/citry_ui/components/cimage/snippets"


def test_image_fixture_manifest_is_complete_and_content_addressed() -> None:
    manifest = yaml.safe_load((FIXTURE_ROOT / "LICENSE.yml").read_text(encoding="utf-8"))
    entries = manifest["files"]
    documented = {entry["path"] for entry in entries}
    actual = {path.name for path in FIXTURE_ROOT.iterdir() if path.name != "LICENSE.yml"}

    assert manifest["schema_version"] == 1
    assert manifest["license"] == "CC0-1.0"
    assert manifest["provenance"]["source_kind"] == "original generated imagery"
    assert documented == actual
    for entry in entries:
        payload = (FIXTURE_ROOT / entry["path"]).read_bytes()
        assert len(payload) == entry["bytes"]
        assert hashlib.sha256(payload).hexdigest() == entry["sha256"]


def test_image_examples_reference_only_licensed_or_deliberately_missing_local_fixtures() -> None:
    licensed = {
        entry["path"] for entry in yaml.safe_load((FIXTURE_ROOT / "LICENSE.yml").read_text(encoding="utf-8"))["files"]
    }
    references = {
        Path(match).name
        for source in SNIPPET_ROOT.glob("*.py")
        for match in re.findall(r"/static/img/ui/image/[^?'\"\s]+", source.read_text(encoding="utf-8"))
    }
    deliberate_failures = {name for name in references if "missing" in name or "csp-blocked" in name}

    assert references - deliberate_failures == licensed
    assert deliberate_failures == {
        "missing-live-frame.jpg",
        "missing-native-observation.jpg",
        "missing-observation.jpg",
    }
