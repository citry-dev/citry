class AddTaskIn:
    title: str = ""
    lane: str = "backlog"
    priority: str = "normal"


class SetTaskCompletedIn:
    task_id: int
    completed: bool


class MoveTaskIn:
    task_id: int
    lane: str
    focus_control: bool = False
