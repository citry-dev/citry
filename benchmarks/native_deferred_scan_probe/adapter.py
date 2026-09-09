"""Discover deferred tasks through one isolated native traversal per scan."""

from __future__ import annotations

import importlib.machinery
import importlib.util
from pathlib import Path
from typing import Any

from markupsafe import Markup

from citry import citry_render as renders
from citry import component_render as components

ROOT = Path(__file__).resolve().parent
ARTIFACT = ROOT / "target/release/libcitry_native_deferred_scan_probe.dylib"
spec = importlib.util.spec_from_file_location(
    "citry_native_deferred_scan_probe",
    ARTIFACT,
    loader=importlib.machinery.ExtensionFileLoader("citry_native_deferred_scan_probe", str(ARTIFACT)),
)
if spec is None or spec.loader is None:
    raise RuntimeError("Cannot load the deferred scan probe")
NATIVE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(NATIVE)
ORIGINAL = components._scan_deferred
REGION_BASE = renders._PhysicalRegion
TYPES = (
    renders.CitryRender,
    renders.DeferredComponent,
    renders.PhysicalRegionPart,
    renders.PhysicalRegionRender,
    renders.Placeholder,
    components._DeferredComponentPosition,
    components._RenderTask,
    components._ContextMergeTask,
    Markup,
)
MROS = tuple((cls, cls.__mro__) for cls in TYPES)
ALIASES = {
    name: getattr(components, name)
    for name in (
        "CitryRender",
        "DeferredComponent",
        "_DeferredComponentPosition",
        "_RenderTask",
        "_ContextMergeTask",
        "_scan_deferred_parts",
        "unwrap_physical_region",
    )
}
DESCRIPTORS = tuple(
    (cls, name, getattr(cls, name))
    for cls, names in (
        (components._DeferredComponentPosition, ("__new__", "__init__")),
        (components._RenderTask, ("__new__", "__init__")),
        (components._ContextMergeTask, ("__new__", "__init__")),
        (renders.Placeholder, ("__getattribute__",)),
        (Markup, ("__getattribute__",)),
        (renders.CitryRender, ("__getattribute__", "parts", "context")),
        (renders.PhysicalRegionPart, ("__getattribute__", "part")),
        (renders.PhysicalRegionRender, ("__getattribute__", "part", "parts", "context")),
    )
    for name in names
)


def scan(render: Any) -> Any:
    """Use the original scan when helpers or admitted object layouts have changed."""
    if (
        renders._PhysicalRegion is REGION_BASE
        and all(cls.__mro__ is original for cls, original in MROS)
        and all(getattr(components, name) is original for name, original in ALIASES.items())
        and all(getattr(cls, name) is original for cls, name, original in DESCRIPTORS)
    ):
        result = NATIVE.scan(render, TYPES)
        if result is not None:
            return result
    return ORIGINAL(render)


def install(changed: bool) -> None:
    """Select the current-tree scanner without changing render objects or their lists."""
    components._scan_deferred = scan if changed else ORIGINAL
