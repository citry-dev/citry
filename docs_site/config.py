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

# This file lives at <repo>/docs_site/config.py, so the docs-site dir is its
# parent and the repo root is one level up again.
_DOCS_SITE_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _DOCS_SITE_DIR.parent


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

    # Public site URL (drives canonical / Open Graph / sitemap URLs). A deploy
    # overrides it; the default points at the project's GitHub Pages URL.
    site_url: str = field(
        default_factory=lambda: os.environ.get("DOCS_SITE_URL", "https://jurooravec.github.io/citry/")
    )

    # Subpath prefix for project-Pages / fork-preview deploys (e.g. "/citry").
    # Empty for a root deploy.
    base_path: str = field(default_factory=lambda: os.environ.get("DOCS_BASE_PATH", "").rstrip("/"))

    # The site name, shown in the page title suffix and Open Graph metadata.
    site_name: str = "Citry"


# The default instance the build and dev server use.
config = DocsConfig()
