import tarfile
from hashlib import sha256

from examples.tools.archive import build_archive
from examples.tools.catalog import load_catalog


def test_archive_is_deterministic_and_contains_only_project_inventory(tmp_path) -> None:
    project = load_catalog()[0]
    first, checksum = build_archive(project, tmp_path / "first")
    second, _second_checksum = build_archive(project, tmp_path / "second")

    assert first.read_bytes() == second.read_bytes()
    assert checksum.read_text().startswith(sha256(first.read_bytes()).hexdigest())
    with tarfile.open(first, "r:gz") as archive:
        names = archive.getnames()
    assert f"{project.id}/README.md" in names
    assert f"{project.id}/uv.lock" in names
    assert not any(".venv" in name or "__pycache__" in name for name in names)
