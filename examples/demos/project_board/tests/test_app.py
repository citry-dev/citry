import pytest
from app.components.board import AddTaskIn, ProjectBoard
from app.main import web_app
from app.store import add_task, board_snapshot, list_tasks, move_task, set_task_completed
from fastapi.testclient import TestClient

from citry.ext.events import EventError


def test_page_and_citry_runtime_are_served() -> None:
    with TestClient(web_app) as client:
        page = client.get("/")
        runtime = client.get("/citry/citry.js")
        events_runtime = client.get("/citry/ext/events/runtime.js")

    assert page.status_code == 200
    assert page.headers["content-type"].startswith("text/html")
    assert "Plan the product launch." in page.text
    assert "Map the onboarding journey" in page.text
    assert "Mark complete" in page.text
    assert "Move Map the onboarding journey to column" in page.text
    assert "5 tasks shown" in page.text
    assert "ext/events" in page.text
    assert runtime.status_code == 200
    assert runtime.headers["content-type"].startswith("text/javascript")
    assert events_runtime.status_code == 200
    assert events_runtime.headers["content-type"].startswith("text/javascript")


def test_store_filters_adds_and_toggles_deterministically() -> None:
    initial = list_tasks()
    assert len(initial) == 6
    assert [task.title for lane in board_snapshot("keyboard") for task in lane.tasks] == ["Review keyboard navigation"]

    created = add_task("Plan release notes", "review", "high")
    assert created.id == 7
    assert created in list_tasks()

    completed = set_task_completed(created.id, completed=True)
    assert completed.completed is True
    assert set_task_completed(created.id, completed=True).completed is True
    assert completed not in [task for lane in board_snapshot() for task in lane.tasks]
    assert completed in [task for lane in board_snapshot(show_completed=True) for task in lane.tasks]


def test_store_moves_tasks_between_valid_columns() -> None:
    moved = move_task(1, "review")

    assert moved.lane == "review"
    assert [task.id for task in board_snapshot()[2].tasks] == [1, 5]
    assert [task.id for lane in board_snapshot("in progress") for task in lane.tasks] == [3, 4]
    assert [task.id for lane in board_snapshot("standard") for task in lane.tasks] == [2, 4]

    with pytest.raises(ValueError, match="Unknown lane"):
        move_task(1, "missing")
    with pytest.raises(KeyError, match="999"):
        move_task(999, "review")


def test_add_event_rejects_titles_over_80_characters() -> None:
    data = AddTaskIn()
    data.title = "x" * 81

    with pytest.raises(EventError, match="Check the task details") as error:
        ProjectBoard.Events.add(object(), data, object())

    assert error.value.fields == {"title": "Enter 4 to 80 characters."}


def test_unknown_page_returns_not_found() -> None:
    with TestClient(web_app) as client:
        assert client.get("/missing").status_code == 404
