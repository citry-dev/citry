from citry import Component, SlotInput
from citry.ext.events import EventError, actions

from ..citry_app import citry_app
from ..store import LaneView, Task, add_task, board_snapshot, list_tasks, toggle_task
from .badges import HighPriorityBadge, StandardPriorityBadge  # noqa: F401


class TaskCard(Component):
    citry = citry_app

    class Kwargs:
        task: Task

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots):
        task = kwargs.task
        theme = self.inject("board_theme")
        return {
            "title": task.title,
            "owner": task.owner,
            "completed": task.completed,
            "toggle_label": "Move back to active" if task.completed else "Mark complete",
            "badge_component": ("high-priority-badge" if task.priority == "high" else "standard-priority-badge"),
            "accent_style": f"--board-accent: {theme.accent};",
        }

    def js_data(self, kwargs: Kwargs, slots: Slots):
        return {"taskId": kwargs.task.id}

    template = """
      <article
        class="task-card"
        c-class="{'task-card--done': completed}"
        c-style="accent_style"
      >
        <div class="task-card__meta">
          <c-component c-is="badge_component" />
          <span>{{ owner }}</span>
        </div>
        <h3>{{ title }}</h3>
        <button
          class="task-card__toggle"
          type="button"
          @click="$dispatch('board:toggle', { taskId })"
        >
          {{ toggle_label }}
        </button>
      </article>
    """

    css = """
      .task-card {
        display: grid;
        gap: 1rem;
        padding: 1rem;
        border: 1px solid #d8d9d2;
        border-top: 0.25rem solid var(--board-accent);
        border-radius: 0.85rem;
        background: #fff;
        box-shadow: 0 0.5rem 1.4rem rgb(41 48 43 / 0.06);
      }
      .task-card--done { opacity: 0.68; }
      .task-card--done h3 { text-decoration: line-through; }
      .task-card__meta {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.6rem;
        color: #727a74;
        font-size: 0.74rem;
      }
      .task-card h3 { margin: 0; font-size: 0.98rem; line-height: 1.4; }
      .task-card__toggle {
        justify-self: start;
        padding: 0;
        border: 0;
        color: #405d4c;
        background: transparent;
        font-size: 0.78rem;
        font-weight: 750;
        text-decoration: underline;
        text-underline-offset: 0.2rem;
      }
    """


class Lane(Component):
    citry = citry_app

    class Kwargs:
        title: str
        count: int

    class Slots:
        default: SlotInput
        footer: SlotInput | None = None

    def template_data(self, kwargs: Kwargs, slots: Slots):
        theme = self.inject("board_theme")
        return {
            "title": kwargs.title,
            "count": kwargs.count,
            "accent_style": f"--board-accent: {theme.accent};",
        }

    template = """
      <section class="lane" c-style="accent_style">
        <header class="lane__header">
          <h2>{{ title }}</h2>
          <span aria-label="{{ count }} tasks">{{ count }}</span>
        </header>
        <div class="lane__tasks">
          <c-slot />
        </div>
        <footer class="lane__footer">
          <c-slot name="footer">Ready for the next task.</c-slot>
        </footer>
      </section>
    """

    css = """
      .lane {
        display: grid;
        min-width: 0;
        gap: 0.8rem;
        align-content: start;
        padding: 0.85rem;
        border: 1px solid #d3d4ce;
        border-radius: 1rem;
        background: #f5f5f0;
      }
      .lane__header { display: flex; align-items: center; justify-content: space-between; }
      .lane__header h2 { margin: 0; font-size: 0.95rem; }
      .lane__header > span {
        display: grid;
        min-width: 1.8rem;
        min-height: 1.8rem;
        place-items: center;
        border-radius: 50%;
        color: #fff;
        background: var(--board-accent);
        font-size: 0.72rem;
        font-weight: 800;
      }
      .lane__tasks { display: grid; gap: 0.75rem; }
      .lane__footer { color: #7a817c; font-size: 0.72rem; text-align: center; }
      .lane-empty {
        margin: 0;
        padding: 1.4rem 0.5rem;
        border: 1px dashed #c2c4bc;
        border-radius: 0.7rem;
        color: #7a817c;
        text-align: center;
      }
    """


class AddTaskIn:
    title: str = ""
    lane: str = "backlog"
    priority: str = "normal"


class ToggleTaskIn:
    task_id: int


class ProjectBoard(Component):
    citry = citry_app

    class Kwargs:
        lanes: tuple[LaneView, ...]
        query: str = ""
        show_completed: bool = False

    class Slots:
        pass

    class State:
        query: str = ""
        show_completed: bool = False

    class Events:
        def refresh(self, state):
            return ProjectBoard(
                lanes=board_snapshot(state.query, state.show_completed),
                query=state.query,
                show_completed=state.show_completed,
            )

        def add(self, data: AddTaskIn, state):
            title = data.title.strip()
            if len(title) < 4:
                raise EventError(
                    "Give the task a little more detail.",
                    fields={"title": "Use at least four characters."},
                )
            try:
                task = add_task(title, data.lane, data.priority)
            except ValueError as error:
                raise EventError("Choose a valid lane and priority.") from error
            return [
                actions.Render(
                    ProjectBoard(
                        lanes=board_snapshot(state.query, state.show_completed),
                        query=state.query,
                        show_completed=state.show_completed,
                    )
                ),
                actions.Dispatch(
                    "board:notice",
                    {"message": f"Added “{task.title}”."},
                ),
            ]

        def toggle(self, data: ToggleTaskIn, state):
            try:
                task = toggle_task(data.task_id)
            except KeyError as error:
                raise EventError("That task no longer exists. Refresh the board.") from error
            verb = "Completed" if task.completed else "Reopened"
            return [
                actions.Render(
                    ProjectBoard(
                        lanes=board_snapshot(state.query, state.show_completed),
                        query=state.query,
                        show_completed=state.show_completed,
                    )
                ),
                actions.Dispatch(
                    "board:notice",
                    {"message": f"{verb} “{task.title}”."},
                ),
            ]

    def template_data(self, kwargs: Kwargs, slots: Slots):
        # Descendants inject this theme instead of threading it through props.
        self.provide("board_theme", accent="#4f725c")
        return {
            "lanes": kwargs.lanes,
            "query": kwargs.query,
            "show_completed": kwargs.show_completed,
            "visible_count": sum(len(lane.tasks) for lane in kwargs.lanes),
            "completed_count": sum(task.completed for task in list_tasks()),
            "total_count": len(list_tasks()),
        }

    def js_data(self, kwargs: Kwargs, slots: Slots):
        return {"helpOpen": False, "notice": ""}

    template = """
      <section
        class="board-region"
        @c-board:toggle="toggle({task_id: $event.detail.taskId})"
        @board:notice.window="notice = $event.detail.message"
      >
        <div class="board-toolbar">
          <label class="filter-control filter-control--search">
            <span>Search board</span>
            <input
              type="search"
              placeholder="Task, owner, lane, or priority"
              autocomplete="off"
              :c-query.debounce.300ms="refresh"
            />
          </label>
          <label class="filter-control filter-control--check">
            <input type="checkbox" :c-show_completed="refresh" />
            <span>Show completed</span>
          </label>
          <button
            class="quiet-button"
            type="button"
            @click="helpOpen = !helpOpen"
            :aria-expanded="helpOpen.toString()"
            aria-controls="board-help"
            x-text="helpOpen ? 'Hide guide' : 'How this works'"
          >
            How this works
          </button>
        </div>

        <aside id="board-help" class="board-help" x-cloak x-show="helpOpen">
          Filters call Python because they change server data. This guide and
          the notice dismissal are local Alpine expressions. Task cards send a
          bubbling browser event; this board translates it into one typed
          Citry Event.
        </aside>

        <div class="board-stats" aria-live="polite">
          <strong>{{ visible_count }} visible</strong>
          <span>{{ completed_count }} of {{ total_count }} complete</span>
          <span x-show="$loading()">Updating board…</span>
        </div>
        <p
          class="event-error"
          role="alert"
          x-show="$error('refresh') || $error('toggle')"
          x-text="($error('refresh') || $error('toggle'))?.message || ''"
        ></p>

        <div class="board-grid">
          <c-for each="lane in lanes">
            <c-Lane c-title="lane.title" c-count="lane.count">
              <c-fill name="default">
                <c-if cond="lane.tasks">
                  <c-for each="task in lane.tasks">
                    <c-TaskCard c-task="task" />
                  </c-for>
                </c-if>
                <c-else>
                  <p class="lane-empty">No matching tasks</p>
                </c-else>
              </c-fill>
              <c-fill name="footer">
                {{ lane.title }} · {{ lane.count }} visible
              </c-fill>
            </c-Lane>
          </c-for>
        </div>

        <section class="composer" aria-labelledby="composer-title">
          <div>
            <p class="section-kicker">Server form Event</p>
            <h2 id="composer-title">Add a task</h2>
            <p>Invalid input returns a field error without losing what you typed.</p>
          </div>
          <form class="composer__form" @c-submit.prevent="add">
            <label class="filter-control composer__title">
              <span>Task title</span>
              <input name="title" placeholder="Describe a useful next step" />
              <span
                class="field-error"
                role="alert"
                x-show="$error('add')?.fieldErrors?.title"
                x-text="$error('add')?.fieldErrors?.title || ''"
              ></span>
            </label>
            <label class="filter-control">
              <span>Lane</span>
              <select name="lane">
                <option value="backlog">Backlog</option>
                <option value="progress">In progress</option>
                <option value="review">Review</option>
              </select>
            </label>
            <label class="filter-control">
              <span>Priority</span>
              <select name="priority">
                <option value="normal">Standard</option>
                <option value="high">High</option>
              </select>
            </label>
            <button
              class="primary-button"
              type="submit"
              :disabled="$loading('add')"
              x-text="$loading('add') ? 'Adding…' : 'Add task'"
            >
              Add task
            </button>
          </form>
          <p
            class="event-error"
            role="alert"
            x-show="$error('add') && !$error('add')?.fieldErrors?.title"
            x-text="$error('add')?.message || ''"
          ></p>
        </section>

        <div class="toast" role="status" x-cloak x-show="notice">
          <span x-text="notice"></span>
          <button type="button" @click="notice = ''" aria-label="Dismiss notification">&times;</button>
        </div>
      </section>
    """

    css = """
      .board-region { display: grid; gap: 1.25rem; }
      .board-toolbar {
        display: grid;
        grid-template-columns: minmax(16rem, 1fr) auto auto;
        align-items: end;
        gap: 0.8rem;
      }
      .filter-control { display: grid; gap: 0.38rem; color: #5d655f; font-size: 0.74rem; font-weight: 750; }
      .filter-control > span:first-child { letter-spacing: 0.04em; text-transform: uppercase; }
      .filter-control input:not([type="checkbox"]), .filter-control select {
        min-height: 2.85rem;
        padding: 0.6rem 0.75rem;
        border: 1px solid #bfc2ba;
        border-radius: 0.65rem;
        color: #222822;
        background: #fff;
      }
      .filter-control--check {
        display: flex;
        min-height: 2.85rem;
        align-items: center;
        gap: 0.5rem;
        padding: 0.6rem 0.75rem;
        border: 1px solid #bfc2ba;
        border-radius: 0.65rem;
        background: #f7f7f2;
      }
      .filter-control--check > span { letter-spacing: normal; text-transform: none; }
      .quiet-button, .primary-button {
        min-height: 2.85rem;
        padding: 0.6rem 0.85rem;
        border: 1px solid #58675e;
        border-radius: 0.65rem;
        color: #32443a;
        background: transparent;
        font-weight: 750;
      }
      .primary-button { color: #fff; background: #334e40; }
      .primary-button:disabled { cursor: wait; opacity: 0.6; }
      .board-help {
        padding: 1rem;
        border-left: 0.3rem solid #e56e43;
        color: #535d56;
        background: #fff8ef;
        line-height: 1.55;
      }
      .board-stats { display: flex; flex-wrap: wrap; gap: 0.55rem 1.2rem; color: #687069; font-size: 0.82rem; }
      .board-stats strong { color: #29352e; }
      .event-error, .field-error { min-height: 1rem; margin: 0; color: #a83a2b; font-size: 0.78rem; }
      .board-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.8rem; }
      .composer {
        display: grid;
        grid-template-columns: minmax(12rem, 0.7fr) minmax(24rem, 1.3fr);
        gap: 1.5rem;
        margin-top: 1rem;
        padding: clamp(1.2rem, 4vw, 2rem);
        border-radius: 1rem;
        color: #eef4ef;
        background: #2a3730;
      }
      .section-kicker {
        margin: 0 0 0.5rem;
        color: #f3a06f;
        font-size: 0.7rem;
        font-weight: 800;
        text-transform: uppercase;
      }
      .composer h2 { margin: 0; font-family: Georgia, serif; font-size: 2rem; font-weight: 500; }
      .composer p { color: #bdc8c0; line-height: 1.5; }
      .composer__form { display: grid; grid-template-columns: 1fr 1fr auto; align-items: start; gap: 0.75rem; }
      .composer__title { grid-column: 1 / -1; }
      .composer .filter-control { color: #dbe2dc; }
      .composer .event-error, .composer .field-error { color: #ffb39f; }
      .toast {
        position: fixed;
        right: 1rem;
        bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        max-width: min(24rem, calc(100% - 2rem));
        padding: 0.85rem 1rem;
        border-radius: 0.75rem;
        color: #fff;
        background: #202a25;
        box-shadow: 0 1rem 3rem rgb(0 0 0 / 0.25);
      }
      .toast button { border: 0; color: inherit; background: transparent; font-size: 1.4rem; }
      @media (max-width: 58rem) {
        .board-grid { grid-template-columns: 1fr; }
        .board-toolbar { grid-template-columns: 1fr 1fr; }
        .filter-control--search { grid-column: 1 / -1; }
        .composer { grid-template-columns: 1fr; }
      }
      @media (max-width: 38rem) {
        .board-toolbar, .composer__form { grid-template-columns: 1fr; }
        .filter-control--search, .composer__title { grid-column: auto; }
      }
    """
