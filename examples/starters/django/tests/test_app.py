import pytest
from django.test import Client
from project_explorer.data import Project


def test_page_runtime_and_csrf_cookie_are_served() -> None:
    client = Client()

    page = client.get("/")
    runtime = client.get("/citry/citry.js")
    events_runtime = client.get("/citry/ext/events/runtime.js")

    assert page.status_code == 200
    assert page["Content-Type"].startswith("text/html")
    assert "Project Explorer" in page.content.decode()
    assert "Atlas" in page.content.decode()
    assert "/citry/ext/events/runtime.js" in page.content.decode()
    assert "csrftoken" in page.cookies
    assert runtime.status_code == 200
    assert runtime["Content-Type"].startswith("text/javascript")
    assert events_runtime.status_code == 200
    assert events_runtime["Content-Type"].startswith("text/javascript")


def test_page_escapes_project_data(monkeypatch: pytest.MonkeyPatch) -> None:
    def projects_with_markup() -> tuple[Project, ...]:
        return (Project("<script>alert(1)</script>", "Safe summary", "Active", "Python"),)

    monkeypatch.setattr("project_explorer.views.find_projects", projects_with_markup)
    page = Client().get("/")
    html = page.content.decode()

    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "<script>alert(1)</script>" not in html


def test_unknown_page_returns_not_found() -> None:
    assert Client().get("/missing").status_code == 404
