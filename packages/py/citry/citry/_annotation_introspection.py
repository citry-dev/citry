"""Read class annotations consistently across Citry's supported Python versions."""

from __future__ import annotations

import inspect
import sys
from importlib import import_module
from typing import Any, cast

from citry._class_introspection import _static_class_dict


def _own_annotations(cls: type) -> dict[str, object]:
    """Return one class's own annotations without evaluating stored strings."""
    namespace = _static_class_dict(cls)
    stored = namespace.get("__annotations__")
    if type(stored) is dict:
        return cast("dict[str, object]", stored.copy())

    if sys.version_info < (3, 14):
        return cast("dict[str, object]", inspect.get_annotations(cls, eval_str=False))

    # Consumers such as dataclass may already have materialized the deferred
    # mapping. Reuse that exact snapshot rather than invoking it a second time.
    cached = namespace.get("__annotations_cache__")
    if type(cached) is dict:
        return cast("dict[str, object]", cached.copy())

    # Python 3.14 stores authored annotations behind a deferred function. The
    # ForwardRef format preserves unresolved names while retaining types that
    # can be resolved from the declaration's original namespace.
    annotationlib = cast("Any", import_module("annotationlib"))
    annotations = annotationlib.get_annotations(cls, format=annotationlib.Format.FORWARDREF)
    return cast("dict[str, object]", annotations)


__all__: list[str] = []
