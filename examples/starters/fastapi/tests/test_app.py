import pytest
from app.data import Project
from app.main import web_app
from fastapi.testclient import TestClient


def test_page_and_citry_runtime_are_served() -> None:
    with TestClient(web_app) as client:
        page = client.get("/")
        runtime = client.get("/citry/citry.js")
        events_runtime = client.get("/citry/ext/events/runtime.js")

    assert page.status_code == 200
    assert page.headers["content-type"].startswith("text/html")
    assert "Project Explorer" in page.text
    assert "Atlas" in page.text
    assert ':c-query.debounce.300ms="refresh"' not in page.text
    assert "/citry/" in page.text
    assert "/citry/ext/events/runtime.js" in page.text
    assert runtime.status_code == 200
    assert runtime.headers["content-type"].startswith("text/javascript")
    assert events_runtime.status_code == 200
    assert events_runtime.headers["content-type"].startswith("text/javascript")


def test_page_escapes_project_data(monkeypatch: pytest.MonkeyPatch) -> None:
    def projects_with_markup() -> tuple[Project, ...]:
        return (Project("<script>alert(1)</script>", "Safe summary", "Active", "Python"),)

    monkeypatch.setattr("app.main.find_projects", projects_with_markup)
    with TestClient(web_app) as client:
        page = client.get("/")

    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page.text
    assert "<script>alert(1)</script>" not in page.text


def test_unknown_page_is_not_claimed_by_the_mount() -> None:
    with TestClient(web_app) as client:
        response = client.get("/missing")

    assert response.status_code == 404
