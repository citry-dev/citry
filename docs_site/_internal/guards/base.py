"""
Core types for the docs-site guard suite.

A guard is a plain function ``(GuardContext) -> Iterator[GuardResult]``. The
harness (in ``__init__.py``) runs every registered guard, collects the results,
and decides the exit code from their severities. Each guard reads what it needs
from one shared ``GuardContext`` so the suite does its work once.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from docs_site._internal.examples import ExampleInfo
    from docs_site._internal.guards.site_index import SiteIndex


class Severity(Enum):
    """How a guard result affects the build outcome."""

    ERROR = "error"  # fails every build
    WARNING = "warning"  # fails only under --strict
    INFO = "info"  # never fails; informational only


@dataclass(frozen=True)
class GuardResult:
    """One finding from a guard: what, how serious, and where."""

    guard: str  # the guard name, e.g. "internal_link"
    severity: Severity
    message: str
    source: str | None = None  # the file or page the issue is on (for the report)
    line: int | None = None

    @classmethod
    def error(cls, guard: str, message: str, source: str | None = None, line: int | None = None) -> GuardResult:
        return cls(guard=guard, severity=Severity.ERROR, message=message, source=source, line=line)

    @classmethod
    def warning(cls, guard: str, message: str, source: str | None = None, line: int | None = None) -> GuardResult:
        return cls(guard=guard, severity=Severity.WARNING, message=message, source=source, line=line)

    @classmethod
    def info(cls, guard: str, message: str, source: str | None = None, line: int | None = None) -> GuardResult:
        return cls(guard=guard, severity=Severity.INFO, message=message, source=source, line=line)


@dataclass
class GuardContext:
    """Everything the guards need, assembled once before the suite runs."""

    content_dir: Path  # docs_site/content (markdown source)
    examples_dir: Path  # docs_site/examples (runnable examples)
    nav_path: Path  # content/_nav.yml
    static_dir: Path  # docs_site/static (source of /static/* assets)
    repo_root: Path  # the repo root, for resolving --8<-- snippet includes
    # Post-build index of the rendered site. None during source-only runs.
    site_index: SiteIndex | None = None
    # name -> ExampleInfo, from the example autodiscovery registry.
    example_registry: dict[str, ExampleInfo] | None = None
    # Root of the committed version tree (versions/<v>/ + versions.json). Set only
    # for the version guards (VERSION_GUARDS); None for the per-build suite.
    versions_dir: Path | None = None


# A guard is a function that yields zero or more results for a given context.
Guard = Callable[["GuardContext"], Iterator[GuardResult]]
