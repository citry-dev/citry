"""
Decide once, at import, whether Citry renders with its native (Rust) path.

The native render path does some of the work of rendering ``simple = "vue"``
rows, and of writing ordinary components' browser data, in Rust
(``citry_core._rust.native_render``), with output identical to the Python
path. ``docs/design/native_render.md`` describes each part and its
error modes. This module holds the one decision every part reads:

- ``SUPPORTED``: whether this interpreter can run the Rust code at all. It
  is CPython with the GIL, outside Pyodide, with a ``citry_core`` that has
  every name the native path calls. It never changes after import. Template
  nodes build their Rust plans only when it is true, so PyPy, Pyodide and
  free-threaded builds never touch the Rust module.
- ``ACTIVE``: whether renders use the Rust code. It is ``SUPPORTED`` unless
  the environment variable ``CITRY_NATIVE_RENDER`` is ``0``. Every call site
  reads it when it runs, not at import, so tests can switch paths in one
  process; steps after a Rust object exists follow that object, not the
  flag, so a render serializes correctly even if the flag changes in between.

``CITRY_NATIVE_RENDER`` accepts ``1`` (the default) and ``0``. Any other
value warns once and is ignored. CPython with a missing or older module
warns once and takes the Python path; the other unsupported interpreters
take it silently, because that is their documented behavior.
"""

from __future__ import annotations

import os
import sys
import sysconfig
import warnings
from dataclasses import dataclass
from typing import cast

from citry_core import _rust

# An older citry_core has no such submodule; the decision below warns then.
_module: type[_rust.native_render] | None = getattr(_rust, "native_render", None)

_ENV_NAME = "CITRY_NATIVE_RENDER"
# Every name the native path calls. A module that lacks one is older than
# this citry, so using part of it would fail in the middle of a render.
_REQUIRED_NAMES = (
    "_RowPlan",
    "_NativeRow",
    "_RunDigests",
    "_encode_occurrences",
    "_NativeRun",
    "_NativeOccurrence",
    "_CallRunWalkPlan",
    "_LeafJson",
    "_leaf_values_json",
)


@dataclass(frozen=True, slots=True)
class _Decision:
    """The outcome of ``_decide``: the two flags and the warnings to show."""

    supported: bool
    active: bool
    warnings: tuple[str, ...]


def _decide(
    *,
    implementation: str,
    platform: str,
    gil_disabled: object,
    module: object | None,
    env_value: str | None,
) -> _Decision:
    """
    Decide whether the native render path is supported and active.

    A pure function of its inputs, so a test can cover each interpreter and
    setting without running on it.

    Args:
        implementation: ``sys.implementation.name``.
        platform: ``sys.platform``.
        gil_disabled: ``sysconfig.get_config_var("Py_GIL_DISABLED")``.
        module: The imported ``citry_core._rust.native_render``, or None when
            it did not import.
        env_value: The value of ``CITRY_NATIVE_RENDER``, or None when unset.

    Returns:
        The decision, with the text of each warning to show.

    """
    messages: list[str] = []
    # The variable is checked on every interpreter, so a typo is reported
    # even where the Python path would run anyway.
    if env_value is None or env_value == "1":
        requested = True
    elif env_value == "0":
        requested = False
    else:
        requested = True
        messages.append(
            f"{_ENV_NAME}={env_value!r} is not '0' or '1'; the value is ignored and the default "
            "(the native render path where it is supported) holds."
        )
    # PyPy reads every object through a slow emulation layer, Pyodide keeps
    # the Python path by choice, and the Rust code reads dicts and lists
    # without locking them, which is safe only under the GIL. The GIL check
    # uses the build setting, so a free-threaded build stays on the Python
    # path even when importing an extension turned the GIL back on.
    if implementation != "cpython" or platform == "emscripten" or gil_disabled:
        return _Decision(supported=False, active=False, warnings=tuple(messages))
    missing = (
        "citry_core._rust.native_render"
        if module is None
        else next(
            (f"citry_core._rust.native_render.{name}" for name in _REQUIRED_NAMES if not hasattr(module, name)), None
        )
    )
    if missing is not None:
        # citry pins citry-core exactly, so this means an inconsistent
        # install or a stale development build; say how to fix it.
        messages.append(
            f"{missing} is missing, so Citry renders with its slower Python path. "
            "Install the citry-core version this citry requires, or rebuild citry-core."
        )
        return _Decision(supported=False, active=False, warnings=tuple(messages))
    return _Decision(supported=True, active=requested, warnings=tuple(messages))


_decision = _decide(
    implementation=sys.implementation.name,
    platform=sys.platform,
    gil_disabled=sysconfig.get_config_var("Py_GIL_DISABLED"),
    module=_module,
    env_value=os.environ.get(_ENV_NAME),
)


def _warn(decision: _Decision) -> None:
    """Show each of the decision's warnings once, as a ``RuntimeWarning``."""
    for message in decision.warnings:
        warnings.warn(message, RuntimeWarning, stacklevel=3)


_warn(_decision)

SUPPORTED: bool = _decision.supported
ACTIVE: bool = _decision.active
# The Rust module, or None when the interpreter cannot use it. Code that
# holds a Rust object already knows the module exists.
native: type[_rust.native_render] | None = _module if SUPPORTED else None


class _NeverBuilt:
    """Stands in for a Rust class where the module is not used; no object is ever one."""


# The classes of level B1's run object and its rows, for the `type(item) is`
# checks of the code that reads a view or a manifest. They are fixed at
# import like ``native``; where the module is not used they are a class no
# object belongs to, so those checks stay one comparison on every path.
NativeRun: type[_rust.native_render._NativeRun] = cast(
    "type[_rust.native_render._NativeRun]", _NeverBuilt if native is None else native._NativeRun
)
NativeOccurrence: type[_rust.native_render._NativeOccurrence] = cast(
    "type[_rust.native_render._NativeOccurrence]", _NeverBuilt if native is None else native._NativeOccurrence
)
