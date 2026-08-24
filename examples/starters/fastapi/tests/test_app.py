from app.main import web_app
from fastapi.testclient import TestClient


def test_page_and_citry_runtime_are_served() -> None:
    with TestClient(web_app) as client:
        page = client.get("/")
        runtime = client.get("/citry/citry.js")

    assert page.status_code == 200
    assert "Project Explorer" in page.text
    assert "Atlas" in page.text
    assert ':c-query.debounce.300ms="refresh"' not in page.text
    assert "/citry/" in page.text
    assert runtime.status_code == 200
    assert runtime.headers["content-type"].startswith("text/javascript")


def test_unknown_page_is_not_claimed_by_the_mount() -> None:
    with TestClient(web_app) as client:
        response = client.get("/missing")

    assert response.status_code == 404
