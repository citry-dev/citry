from app.main import web_app
from app.store import add_task, board_snapshot, list_tasks, toggle_task
from fastapi.testclient import TestClient


def test_page_and_citry_runtime_are_served() -> None:
    with TestClient(web_app) as client:
        page = client.get("/")
        runtime = client.get("/citry/citry.js")

    assert page.status_code == 200
    assert "Launch workspace" in page.text
    assert "Map the onboarding journey" in page.text
    assert "Mark complete" in page.text
    assert "ext/events" in page.text
    assert runtime.status_code == 200
    assert runtime.headers["content-type"].startswith("text/javascript")


def test_store_filters_adds_and_toggles_deterministically() -> None:
    initial = list_tasks()
    assert len(initial) == 6
    assert [task.title for lane in board_snapshot("keyboard") for task in lane.tasks] == ["Review keyboard navigation"]

    created = add_task("Plan release notes", "review", "high")
    assert created.id == 7
    assert created in list_tasks()

    completed = toggle_task(created.id)
    assert completed.completed is True
    assert completed not in [task for lane in board_snapshot() for task in lane.tasks]
    assert completed in [task for lane in board_snapshot(show_completed=True) for task in lane.tasks]


def test_unknown_page_returns_not_found() -> None:
    with TestClient(web_app) as client:
        assert client.get("/missing").status_code == 404
