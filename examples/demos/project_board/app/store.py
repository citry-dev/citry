from dataclasses import dataclass, replace
from threading import RLock


@dataclass(frozen=True, slots=True)
class Task:
    id: int
    title: str
    owner: str
    lane: str
    priority: str
    completed: bool = False


@dataclass(frozen=True, slots=True)
class LaneView:
    key: str
    title: str
    tasks: tuple[Task, ...]

    @property
    def count(self) -> int:
        return len(self.tasks)


LANES = (
    ("backlog", "Backlog"),
    ("progress", "In progress"),
    ("review", "Review"),
)

_FIXTURES = (
    Task(1, "Map the onboarding journey", "Ari", "backlog", "high"),
    Task(2, "Write empty-state copy", "Mina", "backlog", "normal"),
    Task(3, "Build the activity timeline", "Sol", "progress", "high"),
    Task(4, "Connect project search", "Ari", "progress", "normal"),
    Task(5, "Review keyboard navigation", "Mina", "review", "high"),
    Task(6, "Approve color tokens", "Sol", "review", "normal", completed=True),
)

_lock = RLock()
_tasks = list(_FIXTURES)


def reset_tasks() -> None:
    """Restore the deterministic demo state (also used by tests)."""
    with _lock:
        _tasks[:] = _FIXTURES


def list_tasks() -> tuple[Task, ...]:
    with _lock:
        return tuple(_tasks)


def board_snapshot(
    query: str = "",
    show_completed: bool = False,
) -> tuple[LaneView, ...]:
    normalized = query.strip().casefold()
    tasks = (
        task
        for task in list_tasks()
        if (show_completed or not task.completed)
        and (not normalized or normalized in " ".join((task.title, task.owner, task.lane, task.priority)).casefold())
    )
    by_lane = {key: [] for key, _title in LANES}
    for task in tasks:
        by_lane[task.lane].append(task)
    return tuple(LaneView(key=key, title=title, tasks=tuple(by_lane[key])) for key, title in LANES)


def add_task(title: str, lane: str, priority: str) -> Task:
    title = title.strip()
    if lane not in {key for key, _title in LANES}:
        raise ValueError("Unknown lane")
    if priority not in {"normal", "high"}:
        raise ValueError("Unknown priority")
    with _lock:
        task = Task(
            id=max((task.id for task in _tasks), default=0) + 1,
            title=title,
            owner="You",
            lane=lane,
            priority=priority,
        )
        _tasks.append(task)
        return task


def toggle_task(task_id: int) -> Task:
    with _lock:
        for index, task in enumerate(_tasks):
            if task.id == task_id:
                updated = replace(task, completed=not task.completed)
                _tasks[index] = updated
                return updated
    raise KeyError(task_id)
