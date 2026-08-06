"""Structural tests for the docs-site default paths."""

from pathlib import Path

from docs_site._internal.config import DocsConfig, config


def test_default_paths_stay_rooted_at_the_author_facing_docs_directory() -> None:
    docs_dir = Path(__file__).resolve().parents[1]
    repo_root = docs_dir.parent

    assert config.base_dir == docs_dir
    assert config.repo_root == repo_root
    assert config.content_dir == docs_dir / "content"
    assert config.examples_dir == docs_dir / "examples"
    assert config.versions_dir == docs_dir / "versions"
    assert config.versions_config == docs_dir / "docs_versions.yml"
    assert config.site_dir == repo_root / "site"


def test_base_dir_rebases_every_implicit_docs_path(tmp_path: Path) -> None:
    docs_dir = tmp_path / "relocated-docs"
    relocated = DocsConfig(base_dir=docs_dir)

    assert relocated.repo_root == tmp_path
    assert relocated.content_dir == docs_dir / "content"
    assert relocated.examples_dir == docs_dir / "examples"
    assert relocated.site_dir == tmp_path / "site"
    assert relocated.settings_config == docs_dir / "settings.yml"
    assert relocated.reference_config == docs_dir / "reference.yml"
    assert relocated.ui_library_config == docs_dir / "ui_library.yml"
    assert relocated.redirects_config == docs_dir / "redirects.yml"
    assert relocated.versions_config == docs_dir / "docs_versions.yml"
    assert relocated.people_sources_config == docs_dir / "people_sources.yml"
