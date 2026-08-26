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

    @property
    def task_label(self) -> str:
        return "task" if self.count == 1 else "tasks"


LANES = (
    ("backlog", "Backlog"),
    ("progress", "In progress"),
    ("review", "Review"),
)

_LANE_TITLES = dict(LANES)
_PRIORITY_TITLES = {
    "normal": "Standard",
    "high": "High",
}

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
    """Restore the original task list."""
    with _lock:
        _tasks[:] = _FIXTURES


def list_tasks() -> tuple[Task, ...]:
    """Return an immutable snapshot of every task."""
    with _lock:
        return tuple(_tasks)


def board_snapshot(
    query: str = "",
    show_completed: bool = False,
) -> tuple[LaneView, ...]:
    """Group the tasks that match the current filters by column."""
    normalized = query.strip().casefold()
    tasks = (
        task
        for task in list_tasks()
        if (show_completed or not task.completed)
        and (
            not normalized
            or normalized
            in " ".join(
                (
                    task.title,
                    task.owner,
                    task.lane,
                    _LANE_TITLES[task.lane],
                    task.priority,
                    _PRIORITY_TITLES[task.priority],
                )
            ).casefold()
        )
    )
    by_lane = {key: [] for key, _title in LANES}
    for task in tasks:
        by_lane[task.lane].append(task)
    return tuple(LaneView(key=key, title=title, tasks=tuple(by_lane[key])) for key, title in LANES)


def add_task(title: str, lane: str, priority: str) -> Task:
    """Add a task after checking its column and priority."""
    title = title.strip()
    if lane not in {key for key, _title in LANES}:
        raise ValueError(f"Unknown lane: {lane!r}")
    if priority not in {"normal", "high"}:
        raise ValueError(f"Unknown priority: {priority!r}")
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


def set_task_completed(task_id: int, completed: bool) -> Task:
    """Set whether a task is complete."""
    with _lock:
        for index, task in enumerate(_tasks):
            if task.id == task_id:
                updated = replace(task, completed=completed)
                _tasks[index] = updated
                return updated
    raise KeyError(task_id)


def move_task(task_id: int, lane: str) -> Task:
    """Move a task after checking that the destination column exists."""
    if lane not in _LANE_TITLES:
        raise ValueError(f"Unknown lane: {lane!r}")
    with _lock:
        for index, task in enumerate(_tasks):
            if task.id == task_id:
                updated = replace(task, lane=lane)
                _tasks[index] = updated
                return updated
    raise KeyError(task_id)
