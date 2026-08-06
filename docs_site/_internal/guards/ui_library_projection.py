"""Check component-owned Citry UI pages and reject obsolete public copies."""

from __future__ import annotations

from typing import TYPE_CHECKING

from docs_site._internal.guards.base import GuardResult
from docs_site._internal.project import current_docs_project
from docs_site._internal.ui_library_projection import ui_library_source_path
from docs_site._internal.ui_library_reference import (
    compose_ui_library_source,
    ui_library_reference_path,
)
from docs_site._internal.ui_previews import UiPreviewError, discover_ui_previews

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext

_GUARD = "ui_library_projection"


def _component_guide_problem(source: str) -> str:
    if "<c-example" in source or "/examples/" in source:
        return "component pages must use component-owned source instead of the Examples surface"
    return ""


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    project = ctx.project or current_docs_project()
    projections = project.ui_library.projections
    sources_ready = True
    for projection in projections:
        source = ui_library_source_path(projection, repo_root=ctx.repo_root)
        source_label = projection.source.as_posix()
        if not source.is_file():
            sources_ready = False
            yield GuardResult.error(
                guard=_GUARD,
                message=f"Component-owned API source is missing for {projection.family!r}",
                source=source_label,
            )
            continue
        source_text = source.read_text(encoding="utf-8")
        problem = _component_guide_problem(source_text)
        if not problem:
            try:
                compose_ui_library_source(source, family=projection.family)
            except (OSError, UnicodeError, ValueError) as error:
                reference = ui_library_reference_path(source)
                yield GuardResult.error(
                    guard=_GUARD,
                    message=f"Citry UI API data is invalid for {projection.family!r}: {error}.",
                    source=reference.relative_to(ctx.repo_root).as_posix()
                    if reference.is_relative_to(ctx.repo_root)
                    else str(reference),
                )
                continue
        if problem:
            yield GuardResult.error(
                guard=_GUARD,
                message=f"Component page is incomplete for {projection.family!r}: {problem}.",
                source=source_label,
            )

    if sources_ready:
        try:
            discover_ui_previews(project.ui_library, repo_root=ctx.repo_root)
        except UiPreviewError as error:
            yield GuardResult.error(
                guard=_GUARD,
                message=f"Citry UI preview declaration is invalid: {error}",
                source=project.runtime.ui_library_config.relative_to(ctx.repo_root).as_posix()
                if project.runtime.ui_library_config.is_relative_to(ctx.repo_root)
                else str(project.runtime.ui_library_config),
            )

    target_dir = ctx.content_dir / "ui-library" / "components"
    if target_dir.is_dir():
        for target in sorted(target_dir.glob("*.md")):
            yield GuardResult.error(
                guard=_GUARD,
                message="Obsolete Citry UI page copy; the catalog renders component api.md sources directly",
                source=target.relative_to(ctx.content_dir).as_posix(),
            )
