"""The privileged release job accepts only the generated site artifact."""

from pathlib import Path

import pytest
from scripts.apply_release_site_update import apply_update


def _artifact(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "artifact"
    repository = tmp_path / "repository"
    for root in (source, repository / "docs_site"):
        (root / "versions").mkdir(parents=True)
        (root / "versions/versions.json").write_text("[]\n")
        (root / "static/playground").mkdir(parents=True)
        (root / "static/playground/runtime.json").write_text("{}\n")
    return source, repository


def test_update_replaces_generated_tree_and_preserves_source(tmp_path: Path) -> None:
    source, repository = _artifact(tmp_path)
    (repository / "docs_site/versions/stale.html").write_text("stale")
    (repository / "source.py").write_text("unchanged")
    (source / "versions/new.html").write_text("new")
    (source / "static/playground/runtime.json").write_text('{"updated": true}\n')
    apply_update(source, repository)
    assert not (repository / "docs_site/versions/stale.html").exists()
    assert (repository / "docs_site/versions/new.html").read_text() == "new"
    assert (repository / "source.py").read_text() == "unchanged"
    assert (repository / "docs_site/static/playground/runtime.json").read_text() == '{"updated": true}\n'


@pytest.mark.parametrize("extra", [".github/workflows/attack.yml", "static/playground/attack.js", "source.py"])
def test_unexpected_file_rejected_before_writing(tmp_path: Path, extra: str) -> None:
    source, repository = _artifact(tmp_path)
    path = source / extra
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("unexpected")
    with pytest.raises(ValueError, match="unexpected path"):
        apply_update(source, repository)
    assert (repository / "docs_site/versions/versions.json").read_text() == "[]\n"


def test_symlink_rejected_before_writing(tmp_path: Path) -> None:
    source, repository = _artifact(tmp_path)
    (source / "versions/linked").symlink_to(repository / "docs_site/versions")
    with pytest.raises(ValueError, match="non-regular"):
        apply_update(source, repository)


def test_incomplete_artifact_rejected_before_writing(tmp_path: Path) -> None:
    source, repository = _artifact(tmp_path)
    (source / "static/playground/runtime.json").unlink()
    with pytest.raises(ValueError, match="must contain"):
        apply_update(source, repository)
