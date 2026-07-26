"""Regenerate invalid client binding fixtures from the valid worked example."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

FIXTURES = Path(__file__).resolve().parent
BASE = FIXTURES / "component_tag_client_bindings.manifest.json"


def _revision(manifest: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in manifest.items() if key != "revision"}
    canonical = json.dumps(unsigned, separators=(",", ":"), sort_keys=True).encode("utf8")
    return hashlib.sha256(canonical).hexdigest()


def _write(name: str, mutate: Callable[[dict[str, Any]], None]) -> None:
    manifest = copy.deepcopy(json.loads(BASE.read_text(encoding="utf8")))
    mutate(manifest)
    manifest["revision"] = _revision(manifest)
    (FIXTURES / name).write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf8")


def _binding(manifest: dict[str, Any], payload_type: str) -> dict[str, Any]:
    bindings = manifest["graphs"][0]["nestedComponents"][0]["clientBindings"]
    return next(binding for binding in bindings if binding["payload"]["type"] == payload_type)


def _wrong_location_kind(manifest: dict[str, Any]) -> None:
    binding = _binding(manifest, "props")
    location = next(
        location
        for location in manifest["graphs"][0]["sourceLocations"]
        if location["locationId"] == binding["locationId"]
    )
    location["kind"] = "component-call"


def _wrong_expression_type(manifest: dict[str, Any]) -> None:
    _binding(manifest, "props")["payload"]["expression"] = 7


def _wrong_dom_handler_type(manifest: dict[str, Any]) -> None:
    _binding(manifest, "citry-dom-event")["payload"]["handler"] = 7


def _wrong_poll_args_type(manifest: dict[str, Any]) -> None:
    _binding(manifest, "citry-poll")["payload"]["args"] = False


def main() -> None:
    fixtures = {
        "error_client_binding_location_kind.manifest.json": _wrong_location_kind,
        "error_client_binding_expression_type.manifest.json": _wrong_expression_type,
        "error_client_binding_dom_handler_type.manifest.json": _wrong_dom_handler_type,
        "error_client_binding_poll_args_type.manifest.json": _wrong_poll_args_type,
    }
    for name, mutate in fixtures.items():
        _write(name, mutate)


if __name__ == "__main__":
    main()
