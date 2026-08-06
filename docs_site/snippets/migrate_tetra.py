"""Executable Citry examples for the Tetra migration guide."""

from __future__ import annotations

from typing import Any

from citry import Citry, Component
from citry.ext.events import actions, event

citry_app = Citry(secret="docs-only-test-secret")  # noqa: S106 - executable docs fixture
citry_app.set_mounted_prefix("/citry")


# --8<-- [start:counter]
class StepIn:
    amount: int = 1


class Counter(Component):
    citry = citry_app

    class Kwargs:
        count: int = 0

    class State(Kwargs):
        pass

    class Events:
        @event(debounce=200)
        def increment(self, data: StepIn, state):
            state.count += data.amount
            return [
                Counter(count=state.count),
                actions.Data({"count": state.count}),
            ]

    def template_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> dict[str, Any]:
        return {"count": kwargs.count}

    template = """
      <button @c-click="increment({ amount: 1 })">
        Count: {{ count }}
      </button>
    """

    js = """
      $component(({ scope, sendEvent }) => {
        scope.addOne = async () => {
          const result = await sendEvent("increment", { amount: 1 });
          return result.count;
        };
      });
    """


# --8<-- [end:counter]


# --8<-- [start:closed-actions]
class TaskIn:
    task_id: int


class TaskSummary(Component):
    citry = citry_app

    class Kwargs:
        task_id: int
        status: str

    def template_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> dict[str, Any]:
        return {"task_id": kwargs.task_id, "status": kwargs.status}

    template = """
      <p id="task-summary">Task {{ task_id }}: {{ status }}</p>
    """


class TaskEditor(Component):
    citry = citry_app

    class Events:
        def complete(self, data: TaskIn):
            mark_complete(data.task_id)
            return [
                actions.Dispatch(
                    "TaskEditor:completed",
                    {"taskId": data.task_id},
                ),
                actions.Render(
                    TaskSummary(task_id=data.task_id, status="complete"),
                    target="#task-summary",
                ),
            ]

    template = """
      <button @c-click="complete({ task_id: 42 })">
        Complete task
      </button>
      <p id="task-summary">Task 42: pending</p>
    """


# --8<-- [end:closed-actions]


def mark_complete(task_id: int) -> None:
    """Stand-in side effect for the executable guide fixture."""
