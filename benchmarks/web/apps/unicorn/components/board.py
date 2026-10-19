"""Keep editable inputs in Unicorn state and derive rows from the shared model."""

from typing import Any

from django.core.exceptions import PermissionDenied
from django_unicorn.components import UnicornView
from model import ActionInput, apply, snapshot


def render_snapshot(session: str) -> dict[str, Any]:
    state = snapshot(session)
    for phase in state["phase_groups"]:
        for row in phase["outputs"]:
            row["badge"] = (
                "Missing dependency"
                if any(not dependency["completed"] for dependency in row["dependencies"])
                else "Completed"
                if row["completed"]
                else "In progress"
            )
    return state


class BoardView(UnicornView):
    session: str = ""
    operation: str = "manual"
    query: str = ""
    title_input: str = "Project Name"

    def hydrate(self) -> None:
        # Bind signed component state to this browser's signed Django session.
        if self.session != self.request.session.get("board_session"):
            raise PermissionDenied("Board session does not match browser session")

    def act(self, action: str, row_id: int = 0) -> None:
        self.hydrate()
        apply(
            self.session,
            ActionInput(
                action=action, operation=self.operation, row_id=str(row_id), query=self.query, title=self.title_input
            ),
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        self.hydrate()
        context = super().get_context_data(**kwargs)
        context.update(render_snapshot(self.session))
        return context
