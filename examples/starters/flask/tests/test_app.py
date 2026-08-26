import pytest
from app import create_app
from app.data import Project


def test_page_and_citry_runtime_are_served() -> None:
    client = create_app().test_client()

    page = client.get("/")
    runtime = client.get("/citry/citry.js")
    events_runtime = client.get("/citry/ext/events/runtime.js")

    assert page.status_code == 200
    assert page.content_type.startswith("text/html")
    assert "Project Explorer" in page.text
    assert "Atlas" in page.text
    assert "/citry/ext/events/runtime.js" in page.text
    assert runtime.status_code == 200
    assert runtime.content_type.startswith("text/javascript")
    assert events_runtime.status_code == 200
    assert events_runtime.content_type.startswith("text/javascript")


def test_page_escapes_project_data(monkeypatch: pytest.MonkeyPatch) -> None:
    def projects_with_markup() -> tuple[Project, ...]:
        return (Project("<script>alert(1)</script>", "Safe summary", "Active", "Python"),)

    monkeypatch.setattr("app.find_projects", projects_with_markup)
    page = create_app().test_client().get("/")

    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page.text
    assert "<script>alert(1)</script>" not in page.text


def test_citry_mount_does_not_claim_prefix_lookalike() -> None:
    assert create_app().test_client().get("/citryx").status_code == 404
