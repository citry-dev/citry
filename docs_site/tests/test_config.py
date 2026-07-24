"""Structural tests for the docs-site default paths."""

from pathlib import Path

from docs_site._internal.config import config


def test_default_paths_stay_rooted_at_the_author_facing_docs_directory() -> None:
    docs_dir = Path(__file__).resolve().parents[1]
    repo_root = docs_dir.parent

    assert config.base_dir == docs_dir
    assert config.repo_root == repo_root
    assert config.content_dir == docs_dir / "content"
    assert config.examples_dir == docs_dir / "examples"
    assert config.versions_dir == docs_dir / "versions"
    assert config.versions_config == docs_dir / "docs_versions.toml"
    assert config.site_dir == repo_root / "site"
