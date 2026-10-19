"""Apply shared domain actions through Tetra's public Python methods."""

from pathlib import Path

from model import ActionInput, apply, snapshot
from tetra import BasicComponent, Component, public


def project_view(session: str) -> dict:
    view = snapshot(session)
    view.pop("rows")
    for phase in view["phase_groups"]:
        for row in phase["outputs"]:
            row["badge"] = (
                "Missing dependency"
                if any(not dependency["completed"] for dependency in row["dependencies"])
                else "Completed"
                if row["completed"]
                else "In progress"
            )
    return view


class ProjectLayout(BasicComponent):
    def load(self, board: dict) -> None:
        self.board = board

    template = (Path(__file__).parents[2] / "project_layout.html").read_text()


class ProjectInfo(BasicComponent):
    def load(self, board: dict) -> None:
        self.board = board

    template = (Path(__file__).parents[2] / "project_info.html").read_text()


class NotePanel(BasicComponent):
    def load(self, tab: dict) -> None:
        self.tab = tab

    template = (Path(__file__).parents[2] / "note_panel.html").read_text()


class ProjectOutput(BasicComponent):
    def load(self, board: dict, row: dict) -> None:
        self.board = board
        self.row = row

    template = (Path(__file__).parents[2] / "project_output.html").read_text()


class PhaseGroup(BasicComponent):
    def load(self, board: dict, phase: dict) -> None:
        self.board = board
        self.phase = phase

    template = (Path(__file__).parents[2] / "phase_group.html").read_text()


class Board(Component):
    active_tab: str = public("outputs")

    def load(self, session: str) -> None:
        self.session = session
        self.active_tab = "outputs"
        self.board = project_view(session)

    @public
    def act(self, values: dict[str, str]) -> None:
        apply(self.session, ActionInput(**values))
        self.board = project_view(self.session)

    template = (Path(__file__).parents[2] / "board.html").read_text()
