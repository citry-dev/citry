"""App-selection state shared by the CLI entry point and tooling commands."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module

from citry.citry import Citry


class AppSelectionError(ValueError):
    """An expected ``--app`` validation or import error."""


@dataclass(frozen=True, slots=True)
class CheckAppSelection:
    """An explicit check app spec and its unresolved, loaded, or failed state."""

    spec: str | None = None
    engine: Citry | None = None
    failure: str | None = None


def load_app(spec: str) -> Citry:
    """Resolve ``module:attribute`` without deciding whether failure is fatal."""
    module_path, separator, attribute = spec.partition(":")
    if not separator or not module_path or not attribute:
        msg = "--app must be 'module:attribute', e.g. 'myproject.app:engine'"
        raise AppSelectionError(msg)
    try:
        engine = getattr(import_module(module_path), attribute)
    except (ImportError, AttributeError) as exc:
        msg = f"could not import --app target {spec!r}: {exc}"
        raise AppSelectionError(msg) from exc
    if not isinstance(engine, Citry):
        msg = f"--app target {spec!r} is a {type(engine).__name__}, not a Citry instance"
        raise AppSelectionError(msg)
    return engine


def app_failure_message(exc: BaseException) -> str:
    """Render one app-selection or discovery failure without a traceback."""
    if isinstance(exc, AppSelectionError):
        return str(exc)
    detail = str(exc)
    error_type = type(exc).__name__
    return f"{error_type}: {detail}" if detail else error_type


__all__: list[str] = []
