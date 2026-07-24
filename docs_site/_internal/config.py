"""
Site configuration as a plain object (replaces the Django ``settings.py``).

The django-components docs site read its paths and URLs from Django settings.
Citry has no Django, so the same values live on a plain dataclass loaded once.
Only the keys the build actually reads are kept; Django-only keys (SECRET_KEY,
INSTALLED_APPS, MIDDLEWARE, DATABASES, ...) are dropped.

Values that differ per environment (the public URL, a subpath for fork/preview
deploys) come from environment variables so a deploy can set them without
editing code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from docs_site._internal.bootstrap import load_versions_config

# This file lives at <repo>/docs_site/_internal/config.py, so the docs-site dir is
# two levels up and the repo root is one level above that.
_DOCS_SITE_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _DOCS_SITE_DIR.parent

# The version config the `build-all` walker reads, and the single source of truth
# for the publish window below.
_VERSIONS_CONFIG = _DOCS_SITE_DIR / "docs_versions.toml"


@dataclass
class DocsConfig:
    """Paths and URLs the docs build reads. One instance is created below."""

    # Where the docs-site project lives, and the repo it documents.
    base_dir: Path = _DOCS_SITE_DIR
    repo_root: Path = _REPO_ROOT

    # Markdown source pages, runnable examples, and where the site is written.
    content_dir: Path = field(default_factory=lambda: _DOCS_SITE_DIR / "content")
    examples_dir: Path = field(default_factory=lambda: _DOCS_SITE_DIR / "examples")
    site_dir: Path = field(default_factory=lambda: _REPO_ROOT / "site")

    # The committed per-version doc snapshots (versions/<version>/ + versions.json),
    # the config that says which tags `build-all` rebuilds, and how many of the
    # newest releases a deploy publishes (0 = all). The window is read from that
    # config so the TOML is the only place it is set.
    versions_dir: Path = field(default_factory=lambda: _DOCS_SITE_DIR / "versions")
    versions_config: Path = field(default_factory=lambda: _VERSIONS_CONFIG)
    publish_window: int = field(default_factory=lambda: load_versions_config(_VERSIONS_CONFIG).publish_window)

    # Public site URL (drives canonical / Open Graph / sitemap URLs). A deploy
    # overrides it; the default points at the project's site (citry.dev).
    site_url: str = field(default_factory=lambda: os.environ.get("DOCS_SITE_URL", "https://citry.dev/"))

    # Subpath prefix for project-Pages / fork-preview deploys (e.g. "/citry").
    # Empty for a root deploy.
    base_path: str = field(default_factory=lambda: os.environ.get("DOCS_BASE_PATH", "").rstrip("/"))

    # Google Search Console ownership token, rendered as a
    # <meta name="google-site-verification"> in every page head. Empty by default;
    # a deploy sets DOCS_GOOGLE_SITE_VERIFICATION to turn it on.
    google_site_verification: str = field(default_factory=lambda: os.environ.get("DOCS_GOOGLE_SITE_VERIFICATION", ""))

    # The site name, shown in the page title suffix and Open Graph metadata.
    site_name: str = "Citry"

    # The final fallback for a page's meta description: used when the page sets
    # no front-matter description and its body has no usable first paragraph
    # (see docs_site._internal.frontmatter), so every page's <meta name="description">,
    # og:description, and twitter:description stay non-empty.
    default_description: str = (
        "Citry is a fast, simple, and smart frontend framework for Python "
        "that brings the best of Vue, React, Django, and Jinja."
    )


# The default instance the build and dev server use.
config = DocsConfig()
