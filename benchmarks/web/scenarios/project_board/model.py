"""Keep deterministic canonical project state for each browser session."""

from __future__ import annotations

import json
from contextvars import ContextVar
from dataclasses import asdict, dataclass, field
from pathlib import Path
from threading import RLock
from typing import Any

CANONICAL_OUTPUT_COUNT = 14
SUPPORTED_COUNTS = (14, 140, 1400)
FILTER_QUERY = "Lorem ipsum 12"
PHASE_TYPES = ("PHASE_1", "PHASE_2", "PHASE_3", "PHASE_4", "PHASE_5")


@dataclass
class Row:
    id: int
    source_id: int | None
    title: str
    status: str
    completed: bool
    description: str
    phase_id: int
    attachments: list[dict[str, Any]] = field(default_factory=list)
    dependencies: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Board:
    session: str
    rows: list[Row]
    project: dict[str, Any]
    phase_order: list[int]
    note_tabs: list[dict[str, Any]]
    roles: list[dict[str, Any]]
    bookmarks: list[dict[str, Any]]
    contacts: list[dict[str, Any]]
    status_updates: list[dict[str, Any]]
    project_tags: list[dict[str, Any]]
    phase_titles: dict[int, str]
    revision: int = 0
    operation: str = "initial"
    title: str = "Project Name"
    title_input: str = "Project Name"
    query: str = ""
    selected: int = 0
    error: str = ""
    notice: str = ""
    next_id: int = 1
    inserted: int = 0


@dataclass
class ActionInput:
    action: str = ""
    operation: str = ""
    row_id: str = "0"
    query: str = ""
    title: str = ""


_boards: dict[str, Board] = {}
_lock = RLock()
response_identity: ContextVar[tuple[str, int] | None] = ContextVar("response_identity", default=None)


def _source() -> dict[str, Any]:
    payload = json.loads(Path(__file__).with_name("canonical_project.json").read_text())
    return payload["data"]


def _canonical_state(count: int) -> dict[str, Any]:
    source = _source()
    scale = count // CANONICAL_OUTPUT_COUNT
    templates = {item["pk"]: item["fields"] for item in source["phase_templates"]}
    phases_by_type = {templates[item["fields"]["phase_template"]]["type"]: item["pk"] for item in source["phases"]}
    phase_order = [phases_by_type[phase_type] for phase_type in PHASE_TYPES]
    phase_titles = {phases_by_type[kind]: source["phase_titles"][kind] for kind in PHASE_TYPES}
    outputs_by_source = {item[0]["pk"]: item[0] for item in source["outputs"]}
    outputs_by_phase = {
        phase_id: [item for item in source["outputs"] if item[0]["fields"]["phase"] == phase_id]
        for phase_id in phase_order
    }

    ordered: list[tuple[int, list[Any]]] = []
    for phase_id in phase_order:
        for replica in range(scale):
            ordered.extend((replica, item) for item in outputs_by_phase[phase_id])
    output_ids = {(replica, item[0]["pk"]): row_id for row_id, (replica, item) in enumerate(ordered, 1)}
    rows = []
    attachment_id = 1
    for row_id, (replica, (output, attachments, dependencies)) in enumerate(ordered, 1):
        fields = output["fields"]
        row_attachments = []
        for attachment, tags in attachments:
            attachment_fields = attachment["fields"]
            row_attachments.append(
                {
                    "id": attachment_id,
                    "name": attachment_fields["text"],
                    "url": attachment_fields["url"],
                    "tags": [str(tag) for tag in tags],
                }
            )
            attachment_id += 1
        row_dependencies = []
        for dependency, _metadata in dependencies:
            source_id = dependency["pk"]
            target = outputs_by_source[source_id]["fields"]
            row_dependencies.append(
                {
                    "id": output_ids[(replica, source_id)],
                    "title": target["name"],
                    "completed": bool(target["completed"]),
                }
            )
        completed = bool(fields["completed"])
        rows.append(
            Row(
                id=row_id,
                source_id=output["pk"],
                title=fields["name"],
                status="done" if completed else "open",
                completed=completed,
                description=fields["description"],
                phase_id=fields["phase"],
                attachments=row_attachments,
                dependencies=row_dependencies,
            )
        )

    users = {item["pk"]: item["fields"] for item in source["users"]}
    note_tabs = []
    note_id = 1
    comment_id = 1
    for tab_number in range(1, 4):
        base_notes = source[f"notes_{tab_number}"]
        base_comments = source[f"comments_by_notes_{tab_number}"]
        notes = []
        for _replica in range(scale):
            for note in base_notes:
                comments = []
                for comment in base_comments.get(str(note["pk"]), []):
                    fields = comment["fields"]
                    author = users.get(fields["modified_by"], source["users"][0]["fields"])["name"]
                    comments.append(
                        {
                            "id": comment_id,
                            "text": fields.get("text", fields.get("notes", "")),
                            "author": author,
                        }
                    )
                    comment_id += 1
                notes.append({"id": note_id, "text": note["fields"]["text"], "comments": comments})
                note_id += 1
        note_tabs.append({"id": f"notes-{tab_number}", "title": f"Notes {tab_number}", "notes": notes})

    roles = []
    role_id = 1
    for _replica in range(scale):
        for role in source["roles_with_users"]:
            fields = role["fields"]
            roles.append({"id": role_id, "name": fields["name"], "user_name": users[fields["user"]]["name"]})
            role_id += 1
    bookmarks = [
        {"id": replica + 1, "text": "Test bookmark", "url": "/bookmarks/9/create"} for replica in range(scale)
    ]
    project_fields = source["project"]["fields"]
    organizations = {item["pk"]: item["fields"] for item in source["organizations"]}
    project = {
        "id": source["project"]["pk"],
        "name": project_fields["name"],
        "status": project_fields["status"],
        "start_date": project_fields["start_date"],
        "end_date": project_fields["end_date"],
        "organization": organizations[project_fields["organization"]]["name"],
    }
    return {
        "rows": rows,
        "project": project,
        "phase_order": phase_order,
        "phase_titles": phase_titles,
        "note_tabs": note_tabs,
        "roles": roles,
        "bookmarks": bookmarks,
        "contacts": list(source["contacts"]),
        "status_updates": list(source["status_updates"]),
        "project_tags": list(source["project_tags"]),
    }


def reset(session: str, count: int) -> None:
    if count not in SUPPORTED_COUNTS:
        raise ValueError("count must be 14, 140 or 1400 outputs")
    if not session or len(session) > 128 or not all(c.isalnum() or c in "_-" for c in session):
        raise ValueError("session must contain 1 to 128 letters, digits, underscores or hyphens")
    state = _canonical_state(count)
    with _lock:
        _boards[session] = Board(
            session=session,
            **state,
            title=state["project"]["name"],
            title_input=state["project"]["name"],
            next_id=count + 1,
        )
        response_identity.set(("initial", 0))


def snapshot(session: str) -> dict[str, Any]:
    with _lock:
        board = _boards[session]
        result = asdict(board)
        visible = [row for row in result["rows"] if board.query.casefold() in row["title"].casefold()]
        for row in visible:
            row["element_id"] = f"row-{row['id']}"
            row["select_action"] = f"select-{row['id']}"
            row["selected"] = row["id"] == board.selected
        grouped = {phase_id: [] for phase_id in board.phase_order}
        for row in visible:
            grouped[row["phase_id"]].append(row)
        result["rows"] = visible
        result["phase_groups"] = [
            {"id": phase_id, "title": board.phase_titles[phase_id], "outputs": grouped[phase_id]}
            for phase_id in board.phase_order
        ]
        result["visible_count"] = len(visible)
        result["total_count"] = len(board.rows)
        result.pop("phase_order")
        result.pop("phase_titles")
        return result


def apply(session: str, data: ActionInput) -> None:
    """Apply one server action; business validation errors also produce a revision."""
    if not data.operation or len(data.operation) > 128:
        raise ValueError("operation must contain 1 to 128 characters")
    with _lock:
        board = _boards[session]
        if data.action == "select":
            row_id = int(data.row_id)
            if not any(row.id == row_id for row in board.rows):
                raise ValueError("selected output does not exist")
            board.selected = row_id
        elif data.action == "filter":
            board.query = data.query
        elif data.action == "save":
            board.title_input = data.title
            title = data.title.strip()
            board.error = "Use between 3 and 80 characters." if not 3 <= len(title) <= 80 else ""
            board.notice = "" if board.error else "Saved on server."
            if not board.error:
                board.title = title
                board.project["name"] = title
        elif data.action == "insert":
            phase_id = board.phase_order[-1]
            row = Row(
                id=board.next_id,
                source_id=None,
                title=f"New output {board.next_id:04d}",
                status="open",
                completed=False,
                description="",
                phase_id=phase_id,
            )
            board.rows.append(row)
            board.inserted = row.id
            board.next_id += 1
        elif data.action == "remove":
            if not board.inserted:
                raise ValueError("insert an output before removing it")
            board.rows = [row for row in board.rows if row.id != board.inserted]
            board.inserted = 0
        elif data.action == "reorder":
            board.rows.reverse()
            board.phase_order.reverse()
        elif data.action != "probe":
            raise ValueError("unknown board action")
        board.revision += 1
        board.operation = data.operation
        response_identity.set((board.operation, board.revision))
