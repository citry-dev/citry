"""Retain concrete compatibility limits of internal source-field snapshots."""

# ruff: noqa: S101 - executable counterexample assertions

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmarks.source_snapshot_probe import adapter  # noqa: E402

from citry import Citry, Component, ownership  # noqa: E402
from citry.citry_context import CitryContext  # noqa: E402


def run(changed: bool) -> dict[str, Any]:
    """Compare internal record identity and a live source-ID descriptor change."""
    adapter.install(changed)
    graph = ownership.OwnershipGraph()
    graph._initialize_native_storage()
    context = CitryContext(component=SimpleNamespace(id="owner", _citry_class_id="class"))
    graph.record_source_location(
        context, kind=ownership.SourceLocationKind.COMPONENT_CALL, source="x", position=(0, 1)
    )
    internal = adapter.internal_snapshot(graph)
    public = graph.snapshot()
    same_object = internal.source_locations[0] is public.source_locations[0]
    app = Citry()

    class Child(Component):
        citry = app
        template = """
        <p x-data="{}">body</p>
        """

    class Page(Component):
        citry = app
        template = """
        <c-child />
        """

    render = Page().render()
    descriptor = ownership.SourceLocationRecord.id
    ownership.SourceLocationRecord.id = property(lambda record: record[0] + 1000)
    try:
        try:
            render.serialize()
        except RuntimeError as error:
            outcome = str(error)
        else:
            outcome = None
    finally:
        ownership.SourceLocationRecord.id = descriptor
    return {"internal_and_public_record_same_object": same_object, "changed_id_descriptor_error": outcome}


if __name__ == "__main__":
    try:
        reference = run(changed=False)
        candidate = run(changed=True)
        assert reference["internal_and_public_record_same_object"] is True
        assert candidate["internal_and_public_record_same_object"] is False
        assert "dangling source-location reference" in reference["changed_id_descriptor_error"]
        assert candidate["changed_id_descriptor_error"] is None
        print(
            json.dumps(
                {
                    "reference": reference,
                    "candidate": candidate,
                    "production_compatible": False,
                    "hashes": {
                        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in (Path(__file__), Path(adapter.__file__), adapter.ARTIFACT)
                    },
                },
                indent=2,
            )
        )
    finally:
        adapter.install(changed=False)
