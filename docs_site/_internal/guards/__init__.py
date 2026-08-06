"""
Docs-site guard suite.

Runs every guard against one shared ``GuardContext``, collects the results, and
decides the outcome from their severities:

- any error            -> fail
- any warning + strict -> fail
- otherwise            -> pass

Each guard is a small module exposing ``check(ctx) -> Iterator[GuardResult]``.
The shared ``SiteIndex`` (built once) backs every post-build guard. ``make_context``
assembles the context from the site config and a built output directory.
"""

from __future__ import annotations

from contextlib import nullcontext
from typing import TYPE_CHECKING

from docs_site._internal.config import config as default_config
from docs_site._internal.examples import get_example_registry
from docs_site._internal.guards import (
    alt_text,
    anchor,
    api_symbols,
    asset,
    authored_reference,
    blog,
    blog_feed,
    builtin_tags,
    code_lang,
    component_fence,
    cross_version_link,
    example_contract,
    fence_validator,
    frontmatter,
    headings,
    html_wellformed,
    internal_link,
    json_ld,
    lexer_alias,
    live_code,
    nav,
    redirect_target,
    rendered_css,
    rendered_markdown,
    single_h1,
    snippet_path,
    ui_library_projection,
    versions_manifest,
)
from docs_site._internal.guards.base import GuardContext, GuardResult, Severity
from docs_site._internal.guards.site_index import SiteIndex
from docs_site._internal.project import use_docs_project

if TYPE_CHECKING:
    from pathlib import Path

    from docs_site._internal.config import DocsConfig
    from docs_site._internal.guards.base import Guard
    from docs_site._internal.project import DocsProject

__all__ = [
    "GUARDS",
    "POST_BUILD_GUARDS",
    "SOURCE_GUARDS",
    "VERSION_GUARDS",
    "GuardContext",
    "GuardResult",
    "Severity",
    "SiteIndex",
    "format_report",
    "make_context",
    "make_source_context",
    "make_versions_context",
    "run_guards",
]

# Guards in run order: source scans first (cheapest, no build needed), then the
# post-build checks that read the SiteIndex.
SOURCE_GUARDS: list[Guard] = [
    fence_validator.check,
    lexer_alias.check,
    live_code.check,
    code_lang.check,
    component_fence.check,
    snippet_path.check,
    ui_library_projection.check,
    blog.check,
    nav.check,
    frontmatter.check,
    example_contract.check,
    builtin_tags.check,
    authored_reference.check,
    api_symbols.check,
]

POST_BUILD_GUARDS: list[Guard] = [
    internal_link.check,
    blog_feed.check,
    anchor.check,
    asset.check,
    html_wellformed.check,
    rendered_css.check,
    rendered_markdown.check,
    single_h1.check,
    alt_text.check,
    headings.check,
    json_ld.check,
    redirect_target.check,
]

GUARDS: list[Guard] = [*SOURCE_GUARDS, *POST_BUILD_GUARDS]

# Guards for the committed docs_site/versions/ tree. They run separately (via
# make_versions_context + run_guards(..., guards=VERSION_GUARDS)), not as part of
# the per-build suite above. Each reads ctx.versions_dir and no-ops when it is
# unset, so it stays harmless even if added to GUARDS by mistake.
VERSION_GUARDS: list[Guard] = [
    versions_manifest.check,
    cross_version_link.check,
]


def make_context(build_dir: Path, *, config: DocsConfig, project: DocsProject | None = None) -> GuardContext:
    """Assemble a ``GuardContext`` for the guard suite over a built site."""
    examples_dir = project.runtime.examples_dir if project is not None else config.examples_dir
    return GuardContext(
        content_dir=config.content_dir,
        examples_dir=config.examples_dir,
        nav_path=config.content_dir / "_nav.yml",
        static_dir=config.base_dir / "static",
        repo_root=config.repo_root,
        base_path=config.base_path,
        site_index=SiteIndex(build_dir),
        example_registry=get_example_registry(examples_dir),
        project=project,
    )


def make_source_context(*, config: DocsConfig, project: DocsProject | None = None) -> GuardContext:
    """Assemble a guard context that is safe to use before rendering starts."""
    examples_dir = project.runtime.examples_dir if project is not None else config.examples_dir
    return GuardContext(
        content_dir=config.content_dir,
        examples_dir=config.examples_dir,
        nav_path=config.content_dir / "_nav.yml",
        static_dir=config.base_dir / "static",
        repo_root=config.repo_root,
        base_path=config.base_path,
        example_registry=get_example_registry(examples_dir),
        project=project,
    )


def make_versions_context(versions_root: Path | None = None) -> GuardContext:
    """
    Assemble a ``GuardContext`` for the version guards (``VERSION_GUARDS``).

    Only ``versions_dir`` is meaningful to those guards; the content and static
    paths are filled from the site config to satisfy the dataclass and go unused.
    With no argument it points at the committed ``versions/`` tree.
    """
    root = versions_root if versions_root is not None else default_config.versions_dir
    return GuardContext(
        content_dir=default_config.content_dir,
        examples_dir=default_config.examples_dir,
        nav_path=default_config.content_dir / "_nav.yml",
        static_dir=default_config.base_dir / "static",
        repo_root=default_config.repo_root,
        base_path=default_config.base_path,
        versions_dir=root,
    )


def run_guards(
    ctx: GuardContext, *, strict: bool = False, guards: list[Guard] | None = None
) -> tuple[list[GuardResult], bool]:
    """
    Run every guard (default ``GUARDS``) and return ``(results, ok)``.

    ``ok`` is False if any error was produced, or, under ``strict``, any warning.
    A guard that raises is itself reported as an error, so one broken guard cannot
    silently pass the suite.
    """
    results: list[GuardResult] = []
    project_scope = use_docs_project(ctx.project) if ctx.project is not None else nullcontext()
    with project_scope:
        for guard in guards if guards is not None else GUARDS:
            try:
                results.extend(guard(ctx))
            except Exception as e:  # noqa: BLE001 - a broken guard must fail loudly, not pass silently
                results.append(
                    GuardResult.error(
                        guard=getattr(guard, "__module__", "unknown").rsplit(".", 1)[-1],
                        message=f"Guard crashed: {type(e).__name__}: {e}",
                    )
                )

    has_error = any(r.severity is Severity.ERROR for r in results)
    has_warning = any(r.severity is Severity.WARNING for r in results)
    ok = not has_error and not (strict and has_warning)
    return results, ok


def format_report(results: list[GuardResult]) -> str:
    """Render guard results as a human-readable, severity-grouped report."""
    if not results:
        return "All guards passed (no findings)."

    order = [Severity.ERROR, Severity.WARNING, Severity.INFO]
    lines: list[str] = []
    for severity in order:
        group = [r for r in results if r.severity is severity]
        if not group:
            continue
        lines.append(f"{severity.value.upper()}S ({len(group)}):")
        for r in sorted(group, key=lambda x: (x.guard, x.source or "", x.line or 0)):
            loc = r.source or "-"
            if r.line:
                loc = f"{loc}:{r.line}"
            lines.append(f"  [{r.guard}] {loc}")
            lines.append(f"      {r.message}")
    counts = {s: sum(1 for r in results if r.severity is s) for s in order}
    lines.append("")
    lines.append(
        f"Totals: {counts[Severity.ERROR]} errors, {counts[Severity.WARNING]} warnings, {counts[Severity.INFO]} info"
    )
    return "\n".join(lines)
