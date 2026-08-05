"""Immutable, preflighted docs-project configuration for one command run."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from functools import cache, wraps
from typing import TYPE_CHECKING, Any

import markdown

from docs_site._internal.bootstrap import VersionsConfig, load_versions_config
from docs_site._internal.config import DocsConfig
from docs_site._internal.config import config as default_config
from docs_site._internal.config_loading import DocsConfigError
from docs_site._internal.redirects import RedirectCatalog, load_redirect_catalog
from docs_site._internal.reference_pages import (
    ReferenceCatalog,
    load_reference_catalog,
    validate_reference_crossref_keys,
)
from docs_site._internal.settings import (
    SiteSettings,
    load_site_settings,
    validate_absolute_url,
    validate_root_path,
)
from docs_site._internal.ui_library_projection import UiLibraryCatalog, load_ui_library_catalog

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from docs_site._internal.settings import MarkdownProfile


@dataclass(frozen=True, slots=True)
class DocsProject:
    """All runtime inputs and maintainer policy validated for one command boundary."""

    runtime: DocsConfig
    settings: SiteSettings
    reference: ReferenceCatalog
    ui_library: UiLibraryCatalog
    redirects: RedirectCatalog
    versions: VersionsConfig

    @property
    def site_url(self) -> str:
        return self.runtime.site_url or self.settings.public_url


_CURRENT_PROJECT: ContextVar[DocsProject | None] = ContextVar("docs_project", default=None)


def load_docs_project(runtime: DocsConfig | None = None) -> DocsProject:
    """Load every declaration and instantiate Markdown profiles as a preflight."""
    runtime = replace(runtime or default_config)
    settings = load_site_settings(runtime.settings_config)
    _validate_runtime(runtime, settings)
    if not runtime.versions_config.is_file():
        raise DocsConfigError(f"docs configuration file does not exist: {runtime.versions_config}")
    _validate_markdown_profile(settings.markdown_pages, settings=settings)
    _validate_markdown_profile(settings.markdown_docstrings, settings=settings)
    project = DocsProject(
        runtime=runtime,
        settings=settings,
        reference=load_reference_catalog(runtime.reference_config),
        ui_library=load_ui_library_catalog(runtime.ui_library_config),
        redirects=load_redirect_catalog(runtime.redirects_config),
        versions=load_versions_config(runtime.versions_config),
    )
    validate_reference_crossref_keys(project.reference)
    return project


@cache
def default_docs_project() -> DocsProject:
    """The default project for standalone component/helper use."""
    return load_docs_project(default_config)


def current_docs_project() -> DocsProject:
    """Return the render-scoped project, falling back to the validated default."""
    return _CURRENT_PROJECT.get() or default_docs_project()


@contextmanager
def use_docs_project(project: DocsProject) -> Iterator[None]:
    """Make ``project`` available to nested components and reference helpers."""
    token = _CURRENT_PROJECT.set(project)
    try:
        yield
    finally:
        _CURRENT_PROJECT.reset(token)


def docs_project_scope(func: Callable[..., Any]) -> Callable[..., Any]:
    """Ensure a helper and every nested component share one loaded project."""

    @wraps(func)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        explicit_project = kwargs.get("project")
        explicit_config = kwargs.get("config")
        ambient_project = _CURRENT_PROJECT.get()
        project = explicit_project or ambient_project
        if project is None:
            project = load_docs_project(explicit_config)
        elif explicit_config is not None and explicit_config != project.runtime:
            raise DocsConfigError("explicit docs config does not match the active DocsProject runtime")
        kwargs["project"] = project
        kwargs["config"] = project.runtime
        with use_docs_project(project):
            return func(*args, **kwargs)

    return wrapped


def _validate_markdown_profile(profile: MarkdownProfile, *, settings: SiteSettings) -> None:
    configs = materialize_markdown_configs(profile, settings=settings)
    markdown.Markdown(extensions=list(profile.extensions), extension_configs=configs)


def materialize_markdown_configs(profile: MarkdownProfile, *, settings: SiteSettings) -> dict[str, Any]:
    """Return mutable profile options with runtime-owned repository identity applied."""
    configs = profile.configs()
    magiclink = configs.get("pymdownx.magiclink")
    if magiclink is not None:
        magiclink.update(user=settings.repository.owner, repo=settings.repository.name)
    return configs


def _validate_runtime(runtime: DocsConfig, settings: SiteSettings) -> None:
    site_url = runtime.site_url or settings.public_url
    validate_absolute_url(site_url, "DOCS_SITE_URL")
    if runtime.base_path:
        validate_root_path(runtime.base_path, "DOCS_BASE_PATH")
        if runtime.base_path == "/" or runtime.base_path.endswith("/"):
            raise DocsConfigError("DOCS_BASE_PATH must not be / or end with /")
