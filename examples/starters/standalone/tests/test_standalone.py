from pathlib import Path

import pytest
from app.data import Project, find_projects
from app.render import render_document, write_document


def test_project_filter_uses_all_visible_fields() -> None:
    assert [project.name for project in find_projects("python")] == [
        "Atlas",
        "Canopy",
        "Ember",
    ]
    assert [project.name for project in find_projects("incident")] == ["Beacon"]
    assert find_projects("missing") == ()


def test_document_contains_prepared_vue_data_and_local_assets() -> None:
    document = render_document()

    assert "<!DOCTYPE html>" in document
    assert "Project Explorer" in document
    assert "Atlas" in document
    assert "_ctx.tipsOpen = !_ctx.tipsOpen" in document
    assert "CitryStable.startPrepared(" in document
    assert '"preparedData"' in document
    assert "<style" in document
    assert "<script" in document
    assert 'src="http' not in document
    assert 'href="http' not in document
    assert "/citry/" not in document
    assert "</html><" not in document


def test_document_is_deterministic() -> None:
    assert render_document() == render_document()


def test_document_escapes_project_data_in_vue_json(monkeypatch: pytest.MonkeyPatch) -> None:
    def projects_with_markup() -> tuple[Project, ...]:
        return (Project("<script>alert(1)</script>", "Safe summary", "Active", "Python"),)

    monkeypatch.setattr("app.render.find_projects", projects_with_markup)
    document = render_document()

    assert r"\u003cscript>alert(1)\u003c/script>" in document
    assert "<script>alert(1)</script>" not in document


def test_write_document_creates_the_requested_file(tmp_path: Path) -> None:
    output = write_document(tmp_path / "site" / "index.html")

    assert output == tmp_path / "site" / "index.html"
    assert output.is_file()
    assert "Fathom" in output.read_text(encoding="utf-8")
