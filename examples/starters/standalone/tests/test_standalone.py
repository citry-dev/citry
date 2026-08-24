from pathlib import Path

from app.data import find_projects
from app.render import render_document, write_document


def test_project_filter_uses_all_visible_fields() -> None:
    assert [project.name for project in find_projects("python")] == [
        "Atlas",
        "Canopy",
        "Ember",
    ]
    assert [project.name for project in find_projects("incident")] == ["Beacon"]
    assert find_projects("missing") == ()


def test_document_contains_data_styles_scripts_and_local_alpine() -> None:
    document = render_document()

    assert "<!DOCTYPE html>" in document
    assert "Project Explorer" in document
    assert "Atlas" in document
    assert "tipsOpen = !tipsOpen" in document
    assert "<style" in document
    assert "<script" in document
    assert 'src="http' not in document
    assert 'href="http' not in document
    assert "/citry/" not in document


def test_write_document_creates_the_requested_file(tmp_path: Path) -> None:
    output = write_document(tmp_path / "site" / "index.html")

    assert output == tmp_path / "site" / "index.html"
    assert output.is_file()
    assert "Fathom" in output.read_text(encoding="utf-8")
