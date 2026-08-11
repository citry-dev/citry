"""Runtime access to the generated Citry diagnostic catalog."""

from __future__ import annotations

from dataclasses import dataclass
from string import Formatter
from typing import TYPE_CHECKING, Any, cast

from citry._diagnostic_catalog import DIAGNOSTICS, DOCUMENTATION_BASE_URL

if TYPE_CHECKING:
    from collections.abc import Mapping


@dataclass(frozen=True, slots=True)
class DiagnosticDefinition:
    """One immutable, catalog-backed Citry diagnostic definition."""

    code: str
    title: str
    summary: str
    default_severity: str
    configurable_severity: bool
    surfaces: tuple[str, ...]
    parameters: Mapping[str, str]
    messages: Mapping[str, str]
    documentation_path: str


def diagnostic_definition(code: str) -> DiagnosticDefinition:
    """Return the catalog entry for one Citry-owned diagnostic code."""
    try:
        raw = cast("Mapping[str, Any]", DIAGNOSTICS[code])
    except KeyError:
        msg = f"Unknown Citry diagnostic code: {code!r}"
        raise KeyError(msg) from None
    return DiagnosticDefinition(
        code=raw["code"],
        title=raw["title"],
        summary=raw["summary"],
        default_severity=raw["defaultSeverity"],
        configurable_severity=raw.get("configurableSeverity", False),
        surfaces=tuple(raw["surfaces"]),
        parameters=raw["parameters"],
        messages=raw["messages"],
        documentation_path=raw["documentationPath"],
    )


def render_diagnostic(code: str, *, variant: str = "default", **parameters: Any) -> str:
    """Render one catalog message while rejecting missing or stray parameters."""
    definition = diagnostic_definition(code)
    try:
        template = definition.messages[variant]
    except KeyError:
        msg = f"Unknown message variant {variant!r} for diagnostic {code!r}"
        raise KeyError(msg) from None
    expected = {name for _, name, _, _ in Formatter().parse(template) if name is not None}
    supplied = set(parameters)
    if supplied != expected:
        missing = sorted(expected - supplied)
        extra = sorted(supplied - expected)
        details = []
        if missing:
            details.append(f"missing {', '.join(missing)}")
        if extra:
            details.append(f"unexpected {', '.join(extra)}")
        msg = f"Invalid parameters for diagnostic {code!r} ({variant}): {'; '.join(details)}"
        raise TypeError(msg)
    return template.format(**parameters)


def diagnostic_documentation_url(code: str) -> str:
    """Return the canonical public documentation URL for one catalog code."""
    return f"{DOCUMENTATION_BASE_URL}{diagnostic_definition(code).documentation_path}"


__all__ = [
    "DiagnosticDefinition",
    "diagnostic_definition",
    "diagnostic_documentation_url",
    "render_diagnostic",
]
