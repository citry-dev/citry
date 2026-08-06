"""
Runtime site configuration as a plain object (replaces Django ``settings.py``).

The django-components docs site read paths and product policy from Django
settings. Citry has no Django, so checkout and deployment paths live on this
plain dataclass. Maintainer-facing identity, catalogs, and policy live in the
manifests beside ``docs_site/README.md`` and are loaded into ``DocsProject``.

Values that differ per environment (the public URL, a subpath for fork/preview
deploys) come from environment variables so a deploy can set them without
editing code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# This file lives at <repo>/docs_site/_internal/config.py, so the docs-site dir is
# two levels up and the repo root is one level above that.
_DOCS_SITE_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _DOCS_SITE_DIR.parent


# Maintainer-facing configuration files. Runtime path/env configuration stays in
# this module; product policy and ordered catalogs live in these files.
@dataclass
class DocsConfig:
    """Paths and URLs the docs build reads. One instance is created below."""

    # Where the docs-site project lives, and the repo it documents.
    base_dir: Path = _DOCS_SITE_DIR
    repo_root: Path | None = None

    # Markdown source pages, runnable examples, and where the site is written.
    content_dir: Path | None = None
    examples_dir: Path | None = None
    site_dir: Path | None = None

    # The committed per-version doc snapshots (versions/<version>/ + versions.json),
    # the config that says which tags `build-all` rebuilds, and how many of the
    # newest releases a deploy publishes (0 = all).
    versions_dir: Path | None = None
    versions_config: Path | None = None
    settings_config: Path | None = None
    reference_config: Path | None = None
    ui_library_config: Path | None = None
    redirects_config: Path | None = None
    people_sources_config: Path | None = None

    # Public site URL (drives canonical / Open Graph / sitemap URLs). A deploy
    # overrides it; the default points at the project's site (citry.dev).
    # Empty means use ``settings.yml``'s public URL. Deploys may override it.
    site_url: str = field(default_factory=lambda: os.environ.get("DOCS_SITE_URL", ""))

    # Subpath prefix for project-Pages / fork-preview deploys (e.g. "/citry").
    # Empty for a root deploy.
    base_path: str = field(default_factory=lambda: os.environ.get("DOCS_BASE_PATH", "").rstrip("/"))

    # Google Search Console ownership token, rendered as a
    # <meta name="google-site-verification"> in every page head. Empty by default;
    # a deploy sets DOCS_GOOGLE_SITE_VERIFICATION to turn it on.
    google_site_verification: str = field(default_factory=lambda: os.environ.get("DOCS_GOOGLE_SITE_VERIFICATION", ""))

    def __post_init__(self) -> None:
        """Rebase every implicit path when ``base_dir`` or ``repo_root`` changes."""
        repo_root = self.repo_root or self.base_dir.parent
        self.repo_root = repo_root
        defaults = {
            "content_dir": self.base_dir / "content",
            "examples_dir": self.base_dir / "examples",
            "site_dir": repo_root / "site",
            "versions_dir": self.base_dir / "versions",
            "versions_config": self.base_dir / "docs_versions.yml",
            "settings_config": self.base_dir / "settings.yml",
            "reference_config": self.base_dir / "reference.yml",
            "ui_library_config": self.base_dir / "ui_library.yml",
            "redirects_config": self.base_dir / "redirects.yml",
            "people_sources_config": self.base_dir / "people_sources.yml",
        }
        for name, value in defaults.items():
            if getattr(self, name) is None:
                setattr(self, name, value)

    @property
    def site_name(self) -> str:
        """Compatibility view of the manifest-backed site name."""
        from docs_site._internal.settings import load_site_settings  # noqa: PLC0415

        return load_site_settings(self.settings_config).name

    @property
    def default_description(self) -> str:
        """Compatibility view of the manifest-backed description fallback."""
        from docs_site._internal.settings import load_site_settings  # noqa: PLC0415

        return load_site_settings(self.settings_config).default_description

    @property
    def publish_window(self) -> int:
        """Compatibility view of the manifest-backed version publication policy."""
        from docs_site._internal.bootstrap import load_versions_config  # noqa: PLC0415

        return load_versions_config(self.versions_config).publish_window


# The default instance the build and dev server use.
config = DocsConfig()
