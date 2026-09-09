import tarfile
from hashlib import sha256

import pytest
from examples._internal.archive import build_archive
from examples._internal.catalog import load_catalog
from examples._internal.qualify import copy_project


@pytest.mark.parametrize("project", load_catalog(), ids=lambda project: project.id)
def test_archive_is_deterministic_and_contains_only_project_inventory(tmp_path, project) -> None:
    copied = copy_project(project, tmp_path / "copy")
    first, checksum = build_archive(project, tmp_path / "first")
    second, _second_checksum = build_archive(project, tmp_path / "second")

    assert first.read_bytes() == second.read_bytes()
    assert checksum.read_text().startswith(sha256(first.read_bytes()).hexdigest())
    with tarfile.open(first, "r:gz") as archive:
        names = archive.getnames()
        # Copiers and archive readers must receive the same setup instructions.
        instructions = ["README.md"]
        if project.kind == "starter":
            instructions.extend(("AGENTS.md", "CLAUDE.md"))
        for relative in instructions:
            member = archive.extractfile(f"{project.id}/{relative}")
            assert member is not None
            with member:
                assert member.read() == (copied / relative).read_bytes() == (project.source / relative).read_bytes()
    assert f"{project.id}/README.md" in names
    assert f"{project.id}/.vscode/settings.json" in names
    assert f"{project.id}/uv.lock" in names
    assert not any(".venv" in name or "__pycache__" in name for name in names)
