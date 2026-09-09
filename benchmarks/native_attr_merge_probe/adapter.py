"""Use a standalone native merge loop while keeping live Python normalizers."""

from __future__ import annotations

import importlib.machinery
import importlib.util
from pathlib import Path
from typing import Any

from citry import attrs, nodes

ROOT = Path(__file__).resolve().parent
ARTIFACT = ROOT / "target/release/libcitry_native_attr_merge_probe.dylib"
spec = importlib.util.spec_from_file_location(
    "citry_native_attr_merge_probe",
    ARTIFACT,
    loader=importlib.machinery.ExtensionFileLoader("citry_native_attr_merge_probe", str(ARTIFACT)),
)
if spec is None or spec.loader is None:
    raise RuntimeError("Cannot load the attribute merge probe")
NATIVE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(NATIVE)
ORIGINAL = attrs._merge_resolved_attrs
HELPERS = (attrs._html_attr_identity, attrs._exact_html_attr_identity, attrs._uncached_html_attr_identity)


def merge(items: Any) -> dict[str, Any]:
    """Fall back before merging if keys or helper identities are unsupported."""
    if (
        attrs._html_attr_identity is HELPERS[0]
        and attrs._exact_html_attr_identity is HELPERS[1]
        and attrs._uncached_html_attr_identity is HELPERS[2]
    ):
        result = NATIVE.merge(items, attrs)
        if result is not None:
            return result
    return ORIGINAL(items)


def install(changed: bool) -> None:
    """Switch the value-layer helper and its node alias together."""
    attrs._merge_resolved_attrs = merge if changed else ORIGINAL
    nodes._merge_resolved_attrs = attrs._merge_resolved_attrs
