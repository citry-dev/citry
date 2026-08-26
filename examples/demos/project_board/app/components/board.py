from citry import Component, SlotInput
from citry.ext.events import EventError, actions

from ..citry_app import citry_app
from ..store import LANES, LaneView, Task, add_task, board_snapshot, list_tasks, move_task, set_task_completed
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
            "toggle_label": "Reopen task" if task.completed else "Mark complete",
            "badge_component": ("high-priority-badge" if task.priority == "high" else "standard-priority-badge"),
            "accent_style": f"--board-accent: {theme.accent};",
            "lane_options": LANES,
            "current_lane": task.lane,
            "task_dom_id": f"task-{task.id}",
        }

    def js_data(self, kwargs: Kwargs, slots: Slots):
        return {
            "taskId": kwargs.task.id,
            "laneKey": kwargs.task.lane,
            "taskCompleted": kwargs.task.completed,
        }

    template = """
      <article
        c-id="task_dom_id"
        class="task-card"
        c-class="{'task-card--done': completed}"
        c-style="accent_style"
        draggable="true"
        @dragstart="
          $el.classList.add('task-card--dragging');
          $event.dataTransfer.effectAllowed = 'move';
          $event.dataTransfer.setData('text/plain', taskId.toString());
          $event.dataTransfer.setData('application/x-citry-lane', laneKey);
        "
        @dragend="$el.classList.remove('task-card--dragging')"
      >
        <div class="task-card__meta">
          <c-component c-is="badge_component" />
          <span>{{ owner }}</span>
        </div>
        <h3>{{ title }}</h3>
        <div class="task-card__actions">
          <label class="task-card__move">
            <span>Move to column</span>
            <select
              c-aria-label="'Move ' + title + ' to column'"
              @change="
                if ($event.target.value !== laneKey) {
                  $dispatch('board:move', {
                    taskId,
                    lane: $event.target.value,
                    focusControl: true,
                  });
                }
              "
            >
              <c-for each="lane_key, lane_title in lane_options">
                <option
                  c-value="lane_key"
                  c-selected="lane_key == current_lane"
                >
                  {{ lane_title }}
                </option>
              </c-for>
            </select>
          </label>
          <button
            class="task-card__toggle"
            type="button"
            @click="
              $dispatch('board:set-completed', {
                taskId,
                completed: !taskCompleted,
              })
            "
          >
            {{ toggle_label }}
          </button>
        </div>
      </article>
    """

    css = """
      .task-card {
        display: grid;
        gap: 0.9rem;
        padding: 1rem;
        border: 1px solid var(--color-border);
        border-top: 0.2rem solid var(--board-accent);
        border-radius: 0.5rem;
        background: var(--color-input);
        cursor: grab;
        transition:
          border-color 120ms ease,
          opacity 120ms ease,
          transform 120ms ease;
      }

      .task-card--dragging {
        opacity: 0.55;
        cursor: grabbing;
        transform: scale(0.98);
      }

      .task-card--done {
        background: var(--color-surface);
      }

      .task-card--done h3 {
        text-decoration: line-through;
      }

      .task-card__meta {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.6rem;
        color: var(--color-faint);
        font-size: 0.74rem;
      }

      .task-card h3 {
        margin: 0;
        color: var(--color-text);
        font-size: 0.98rem;
        line-height: 1.4;
      }

      .task-card__toggle {
        padding: 0;
        border: 0;
        color: var(--color-accent-ink);
        background: transparent;
        font-size: 0.78rem;
        font-weight: 650;
        text-decoration: underline;
        text-underline-offset: 0.2rem;
      }

      .task-card__actions {
        display: flex;
        flex-wrap: wrap;
        align-items: end;
        justify-content: space-between;
        gap: 0.75rem;
      }

      .task-card__move {
        display: grid;
        gap: 0.2rem;
        color: var(--color-faint);
        font-size: 0.68rem;
        font-weight: 650;
      }

      .task-card__move > span {
        letter-spacing: 0.04em;
        text-transform: uppercase;
      }

      .task-card__move select {
        min-height: 2rem;
        padding: 0.25rem 1.8rem 0.25rem 0.45rem;
        border: 1px solid var(--color-input-border);
        border-radius: 0.375rem;
        color: var(--color-text);
        background: var(--color-input);
        font-size: 0.75rem;
      }
    """


class Lane(Component):
    citry = citry_app

    class Kwargs:
        lane_key: str
        title: str
        count: int

    class Slots:
        default: SlotInput
        footer: SlotInput | None = None

    def template_data(self, kwargs: Kwargs, slots: Slots):
        theme = self.inject("board_theme")
        task_label = "task" if kwargs.count == 1 else "tasks"
        return {
            "title": kwargs.title,
            "count": kwargs.count,
            "count_label": f"{kwargs.count} {task_label}",
            "accent_style": f"--board-accent: {theme.accent};",
        }

    def js_data(self, kwargs: Kwargs, slots: Slots):
        return {
            "laneKey": kwargs.lane_key,
        }

    template = """
      <section
        class="lane"
        c-style="accent_style"
        c-aria-label="title + ' column'"
        @dragover.prevent="
          $el.classList.add('lane--drop-target');
          $event.dataTransfer.dropEffect = 'move';
        "
        @dragleave="
          if (!$el.contains($event.relatedTarget)) {
            $el.classList.remove('lane--drop-target');
          }
        "
        @drop.prevent="
          const rawTaskId = $event.dataTransfer.getData('text/plain');
          const taskId = Number(rawTaskId);
          const sourceLane = $event.dataTransfer.getData(
            'application/x-citry-lane',
          );
          $el.classList.remove('lane--drop-target');
          if (
            sourceLane &&
            Number.isSafeInteger(taskId) &&
            taskId > 0 &&
            sourceLane !== laneKey
          ) {
            $dispatch('board:move', {
              taskId,
              lane: laneKey,
              focusControl: false,
            });
          }
        "
      >
        <header class="lane__header">
          <h2>{{ title }}</h2>
          <span c-aria-label="count_label">{{ count }}</span>
        </header>
        <div class="lane__tasks">
          <c-slot />
        </div>
        <footer class="lane__footer">
          <c-slot name="footer">
            No tasks shown
          </c-slot>
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
        border: 1px solid var(--color-border);
        border-radius: 0.5rem;
        background: var(--color-surface);
        transition:
          border-color 120ms ease,
          background 120ms ease;
      }

      .lane--drop-target {
        border-color: var(--color-accent);
        background: var(--color-accent-soft);
      }

      .lane__header {
        display: flex;
        align-items: center;
        justify-content: space-between;
      }

      .lane__header h2 {
        margin: 0;
        color: var(--color-text);
        font-size: 0.95rem;
      }

      .lane__header > span {
        display: grid;
        min-width: 1.8rem;
        min-height: 1.8rem;
        place-items: center;
        border-radius: 50%;
        color: var(--color-primary-ink);
        background: var(--board-accent);
        font-size: 0.72rem;
        font-weight: 700;
      }

      .lane__tasks {
        display: grid;
        min-height: 8rem;
        gap: 0.75rem;
        align-content: start;
      }

      .lane__footer {
        color: var(--color-faint);
        font-size: 0.72rem;
        text-align: center;
      }

      .lane-empty {
        margin: 0;
        padding: 1.4rem 0.5rem;
        border: 1px dashed var(--color-input-border);
        border-radius: 0.375rem;
        color: var(--color-faint);
        text-align: center;
      }
    """


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
            if not 4 <= len(title) <= 80:
                raise EventError(
                    "Check the task details.",
                    fields={"title": "Enter 4 to 80 characters."},
                )
            try:
                task = add_task(title, data.lane, data.priority)
            except ValueError as error:
                raise EventError("Choose a valid column and priority.") from error
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

        def set_completed(self, data: SetTaskCompletedIn, state):
            try:
                task = set_task_completed(data.task_id, data.completed)
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
                    {
                        "message": f"{verb} “{task.title}”.",
                        "focusBoard": task.completed and not state.show_completed,
                    },
                ),
            ]

        def move(self, data: MoveTaskIn, state):
            try:
                task = move_task(data.task_id, data.lane)
            except ValueError as error:
                raise EventError("Choose a valid destination column.") from error
            except KeyError as error:
                raise EventError("That task no longer exists. Refresh the board.") from error
            lane_title = dict(LANES)[task.lane]
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
                    {
                        "message": f"Moved “{task.title}” to {lane_title}.",
                        "focusTaskId": task.id if data.focus_control else None,
                    },
                ),
            ]

    def template_data(self, kwargs: Kwargs, slots: Slots):
        # The board provides one accent so each column and its cards use the same color.
        self.provide("board_theme", accent="var(--color-accent)")
        visible_count = sum(len(lane.tasks) for lane in kwargs.lanes)
        return {
            "lanes": kwargs.lanes,
            "query": kwargs.query,
            "show_completed": kwargs.show_completed,
            "visible_count": visible_count,
            "visible_task_label": "task" if visible_count == 1 else "tasks",
            "completed_count": sum(task.completed for task in list_tasks()),
            "total_count": len(list_tasks()),
        }

    def js_data(self, kwargs: Kwargs, slots: Slots):
        return {"helpOpen": False, "notice": ""}

    template = """
      <section
        class="board-region"
        @c-board:set-completed="
          set_completed({
            task_id: $event.detail.taskId,
            completed: $event.detail.completed,
          })
        "
        @c-board:move="
          move({
            task_id: $event.detail.taskId,
            lane: $event.detail.lane,
            focus_control: Boolean($event.detail.focusControl),
          })
        "
        @board:notice.window="
          notice = $event.detail.message;
          if ($event.detail.focusBoard) {
            $nextTick(() => $refs.boardStatus.focus());
          }
          if ($event.detail.focusTaskId) {
            $nextTick(() => {
              document
                .getElementById('task-' + $event.detail.focusTaskId)
                ?.querySelector('.task-card__move select')
                ?.focus();
            });
          }
        "
      >
        <div class="board-toolbar">
          <label class="filter-control filter-control--search">
            <span>Search tasks</span>
            <input
              type="search"
              placeholder="Title, owner, column, or priority"
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
            x-text="helpOpen ? 'Hide explanation' : 'How this page works'"
          >
            How this page works
          </button>
        </div>

        <aside id="board-help" class="board-help" x-cloak x-show="helpOpen">
          You can open this explanation and dismiss notices without calling
          Python. When you search, add, move, or complete a task, Citry sends
          an Event to Python. Python updates the in-memory tasks and returns a
          new board. Drag a card onto another column, or use its Move to column
          menu with a keyboard or touchscreen.
        </aside>

        <div
          class="board-stats"
          x-ref="boardStatus"
          tabindex="-1"
          aria-live="polite"
        >
          <strong>
            {{ visible_count }} {{ visible_task_label }} shown
          </strong>
          <span>{{ completed_count }} of {{ total_count }} complete</span>
          <span x-show="$loading()">Updating board…</span>
        </div>
        <p
          class="event-error"
          role="alert"
          x-show="
            $error('refresh') ||
            $error('set_completed') ||
            $error('move')
          "
          x-text="
            (
              $error('refresh') ||
              $error('set_completed') ||
              $error('move')
            )?.message || ''
          "
        ></p>

        <div class="board-grid">
          <c-for each="lane in lanes">
            <c-Lane
              c-lane_key="lane.key"
              c-title="lane.title"
              c-count="lane.count"
            >
              <c-fill name="default">
                <c-if cond="lane.tasks">
                  <c-for each="task in lane.tasks">
                    <c-TaskCard c-task="task" />
                  </c-for>
                </c-if>
                <c-else>
                  <p class="lane-empty">No tasks shown</p>
                </c-else>
              </c-fill>
              <c-fill name="footer">
                {{ lane.title }}: {{ lane.count }}
                {{ lane.task_label }} shown
              </c-fill>
            </c-Lane>
          </c-for>
        </div>

        <section class="composer" aria-labelledby="composer-title">
          <div>
            <p class="section-kicker">Python validates this form</p>
            <h2 id="composer-title">Add a task</h2>
            <p>
              If Python finds a problem, your entries stay in the form so you
              can correct them.
            </p>
          </div>
          <form class="composer__form" @c-submit.prevent="add">
            <label class="filter-control composer__title">
              <span>Task title</span>
              <input
                name="title"
                placeholder="Describe a useful next step"
                maxlength="80"
                aria-describedby="task-title-error"
                :aria-invalid="
                  Boolean($error('add')?.fieldErrors?.title).toString()
                "
              />
              <span
                id="task-title-error"
                class="field-error"
                role="alert"
                x-show="$error('add')?.fieldErrors?.title"
                x-text="$error('add')?.fieldErrors?.title || ''"
              ></span>
            </label>
            <label class="filter-control">
              <span>Column</span>
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
      .board-region {
        display: grid;
        gap: 1.25rem;
      }

      .board-toolbar {
        display: grid;
        grid-template-columns: minmax(16rem, 1fr) auto auto;
        align-items: end;
        gap: 0.8rem;
      }

      .filter-control {
        display: grid;
        gap: 0.38rem;
        color: var(--color-muted);
        font-size: 0.74rem;
        font-weight: 650;
      }

      .filter-control > span:first-child {
        letter-spacing: 0.04em;
        text-transform: uppercase;
      }

      .filter-control input:not([type="checkbox"]),
      .filter-control select {
        min-height: 2.85rem;
        padding: 0.6rem 0.75rem;
        border: 1px solid var(--color-input-border);
        border-radius: 0.375rem;
        color: var(--color-text);
        background: var(--color-input);
      }

      .filter-control--check {
        display: flex;
        min-height: 2.85rem;
        align-items: center;
        gap: 0.5rem;
        padding: 0.6rem 0.75rem;
        border: 1px solid var(--color-border);
        border-radius: 0.375rem;
        background: var(--color-surface);
      }

      .filter-control--check > span {
        letter-spacing: normal;
        text-transform: none;
      }

      .quiet-button,
      .primary-button {
        min-height: 2.85rem;
        padding: 0.6rem 0.85rem;
        border: 1px solid var(--color-accent);
        border-radius: 0.375rem;
        color: var(--color-accent-ink);
        background: transparent;
        font-weight: 650;
      }

      .quiet-button:hover {
        color: var(--color-primary-ink);
        background: var(--color-accent-hover);
      }

      .primary-button {
        color: var(--color-primary-ink);
        background: var(--color-primary);
      }

      .primary-button:hover {
        background: var(--color-accent-hover);
      }

      .primary-button:disabled {
        cursor: wait;
        opacity: 0.6;
      }

      .board-help {
        padding: 1rem;
        border-left: 0.25rem solid var(--color-accent);
        color: var(--color-muted);
        background: var(--color-accent-soft);
        line-height: 1.55;
      }

      .board-stats {
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem 1.2rem;
        color: var(--color-faint);
        font-size: 0.82rem;
      }

      .board-stats strong {
        color: var(--color-text);
      }

      .event-error,
      .field-error {
        min-height: 1rem;
        margin: 0;
        color: var(--color-danger);
        font-size: 0.78rem;
      }

      .board-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.8rem;
      }

      .composer {
        display: grid;
        grid-template-columns: minmax(12rem, 0.7fr) minmax(24rem, 1.3fr);
        gap: 1.5rem;
        margin-top: 1rem;
        padding: clamp(1.2rem, 4vw, 2rem);
        border: 1px solid var(--color-border);
        border-radius: 0.5rem;
        color: var(--color-muted);
        background: var(--color-surface);
      }

      .section-kicker {
        margin: 0 0 0.5rem;
        color: var(--color-accent-ink);
        font-size: 0.7rem;
        font-weight: 650;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }

      .composer h2 {
        margin: 0;
        color: var(--color-text);
        font-size: 1.6rem;
        font-weight: 700;
      }

      .composer p {
        color: var(--color-muted);
        line-height: 1.5;
      }

      .composer__form {
        display: grid;
        grid-template-columns: 1fr 1fr auto;
        align-items: start;
        gap: 0.75rem;
      }

      .composer__title {
        grid-column: 1 / -1;
      }

      .toast {
        position: fixed;
        right: 1rem;
        bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        max-width: min(24rem, calc(100% - 2rem));
        padding: 0.85rem 1rem;
        border-radius: 0.5rem;
        color: var(--color-primary-ink);
        background: var(--color-text);
        box-shadow: 0 1rem 3rem rgb(0 0 0 / 0.16);
      }

      .toast button {
        border: 0;
        color: inherit;
        background: transparent;
        font-size: 1.4rem;
      }

      @media (max-width: 58rem) {
        .board-toolbar {
          grid-template-columns: 1fr 1fr;
        }

        .filter-control--search {
          grid-column: 1 / -1;
        }

        .composer {
          grid-template-columns: 1fr;
        }
      }

      @media (max-width: 37.5rem) {
        .board-grid {
          grid-template-columns: 1fr;
        }
      }

      @media (max-width: 38rem) {
        .board-toolbar,
        .composer__form {
          grid-template-columns: 1fr;
        }

        .filter-control--search,
        .composer__title {
          grid-column: auto;
        }
      }
    """
