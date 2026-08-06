"""Executable Citry examples for the livecomponents migration guide."""

from __future__ import annotations

from typing import Any

from citry import Citry, Component
from citry.ext.events import actions

citry_app = Citry(secret="docs-only-test-secret")  # noqa: S106 - executable docs fixture
citry_app.set_mounted_prefix("/citry")


# --8<-- [start:server-state]
class ServerCounter(Component):
    citry = citry_app

    class Kwargs:
        count: int = 0

    class State(Kwargs):
        _storage = "server"
        _public = ("count",)

    class Events:
        def increment(self, state):
            state.count += 1
            return ServerCounter(count=state.count)

    def template_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> dict[str, Any]:
        return {"count": kwargs.count}

    template = """
      <button @c-click="increment">
        Count: {{ count }}
      </button>
    """


# --8<-- [end:server-state]


# --8<-- [start:signed-state]
class SignedCounter(Component):
    citry = citry_app

    class Kwargs:
        count: int = 0

    class State(Kwargs):
        pass

    class Events:
        def increment(self, state):
            state.count += 1
            return SignedCounter(count=state.count)

    def template_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> dict[str, Any]:
        return {"count": kwargs.count}

    template = """
      <button @c-click="increment">
        Count: {{ count }}
      </button>
    """


# --8<-- [end:signed-state]


# --8<-- [start:multi-component-result]
class TaskIn:
    task_id: int


class TaskSummary(Component):
    citry = citry_app

    class Kwargs:
        task_id: int

    def template_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> dict[str, Any]:
        return {"task_id": kwargs.task_id}

    template = """
      <p id="task-summary">Task {{ task_id }} saved</p>
    """


class TaskEditor(Component):
    citry = citry_app

    class Events:
        def save(self, data: TaskIn):
            save_task(data.task_id)
            return [
                actions.Render(
                    TaskSummary(task_id=data.task_id),
                    target="#task-summary",
                ),
                actions.Dispatch(
                    "TaskEditor:saved",
                    {"taskId": data.task_id},
                ),
            ]

    template = """
      <button @c-click="save({ task_id: 42 })">
        Save task
      </button>
      <p id="task-summary">Task 42 not saved</p>
    """


# --8<-- [end:multi-component-result]


def save_task(task_id: int) -> None:
    """Stand-in side effect for the executable guide fixture."""
