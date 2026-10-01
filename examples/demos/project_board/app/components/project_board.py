from app.citry_app import citry_app
from app.components.event_inputs import AddTaskIn, MoveTaskIn, SetTaskCompletedIn
from app.components.provides import ThemeData
from app.store import LANES, LaneView, add_task, board_snapshot, list_tasks, move_task, set_task_completed
from citry import Component
from citry.ext.events import EventError, actions


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
        def refresh(self, state: "ProjectBoard.State"):
            return board_for(state)

        def add(self, data: AddTaskIn, state: "ProjectBoard.State"):
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
                actions.Render(board_for(state)),
                actions.Dispatch(
                    "board:notice",
                    {"message": f"Added “{task.title}”."},
                ),
            ]

        def set_completed(
            self,
            data: SetTaskCompletedIn,
            state: "ProjectBoard.State",
        ):
            try:
                task = set_task_completed(data.task_id, data.completed)
            except KeyError as error:
                raise EventError("That task no longer exists. Refresh the board.") from error
            verb = "Completed" if task.completed else "Reopened"
            return [
                actions.Render(board_for(state)),
                actions.Dispatch(
                    "board:notice",
                    {
                        "message": f"{verb} “{task.title}”.",
                        "focusBoard": task.completed and not state.show_completed,
                    },
                ),
            ]

        def move(self, data: MoveTaskIn, state: "ProjectBoard.State"):
            try:
                task = move_task(data.task_id, data.lane)
            except ValueError as error:
                raise EventError("Choose a valid destination column.") from error
            except KeyError as error:
                raise EventError("That task no longer exists. Refresh the board.") from error
            lane_title = dict(LANES)[task.lane]
            return [
                actions.Render(board_for(state)),
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
        theme = ThemeData(accent="var(--color-accent)")
        self.provide("board_theme", theme)
        visible_count = sum(len(lane.tasks) for lane in kwargs.lanes)
        return {
            "lanes": kwargs.lanes,
            "lane_options": LANES,
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
        @board:notice="showNotice($event.detail)"
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
            :aria-expanded="helpOpen"
            aria-controls="board-help"
            v-text="helpOpen ? 'Hide explanation' : 'How this page works'"
          >
            How this page works
          </button>
        </div>

        <aside id="board-help" class="board-help" v-cloak v-show="helpOpen">
          You can open this explanation and dismiss notices without calling
          Python. When you search, add, move, or complete a task, Citry sends
          an Event to Python. Python updates the in-memory tasks and returns a
          new board. Drag a card onto another column, or use its Move to column
          menu with a keyboard or touchscreen.
        </aside>

        <div
          class="board-stats"
          ref="boardStatus"
          tabindex="-1"
          aria-live="polite"
        >
          <strong>
            {{ visible_count }} {{ visible_task_label }} shown
          </strong>
          <span>{{ completed_count }} of {{ total_count }} complete</span>
          <span v-show="$loading()">Updating board…</span>
        </div>
        <p
          class="event-error"
          role="alert"
          v-show="boardError()"
          v-text="boardError()?.message || ''"
        ></p>

        <div class="board-grid">
          <c-for each="lane in lanes">
            <c-Lane
              #c-key="lane.key"
              c-lane_key="lane.key"
              c-title="lane.title"
              c-count="lane.count"
              @c-drop-task="
                move({task_id: $event.taskId, lane: $event.lane})
              "
            >
              <c-for each="task in lane.tasks">
                <c-TaskCard
                  #c-key="task.id"
                  c-task="task"
                  @c-move="
                    move({
                      task_id: $event.taskId,
                      lane: $event.lane,
                      focus_control: true,
                    })
                  "
                  @c-set-completed="
                    set_completed({
                      task_id: $event.taskId,
                      completed: $event.completed,
                    })
                  "
                />
              </c-for>
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
                  Boolean($error('add')?.fieldErrors?.title)
                "
              />
              <span
                id="task-title-error"
                class="field-error"
                role="alert"
                v-show="$error('add')?.fieldErrors?.title"
                v-text="$error('add')?.fieldErrors?.title || ''"
              ></span>
            </label>
            <label class="filter-control">
              <span>Column</span>
              <select name="lane">
                <c-for each="lane_key, lane_title in lane_options">
                  <option
                    #c-key="lane_key"
                    c-value="lane_key"
                  >
                    {{ lane_title }}
                  </option>
                </c-for>
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
              v-text="$loading('add') ? 'Adding…' : 'Add task'"
            >
              Add task
            </button>
          </form>
          <p
            class="event-error"
            role="alert"
            v-show="$error('add') && !$error('add')?.fieldErrors?.title"
            v-text="$error('add')?.message || ''"
          ></p>
        </section>

        <div class="toast" role="status" v-cloak v-show="notice">
          <span v-text="notice"></span>
          <button
            type="button"
            aria-label="Dismiss notification"
            @click="notice = ''"
          >
            &times;
          </button>
        </div>
      </section>
    """

    js = """
      $component({
        methods: {
          // The board shows one error line for the handlers the board itself
          // calls. The add form shows its own error beside the form.
          boardError() {
            return (
              this.$error('refresh') ||
              this.$error('set_completed') ||
              this.$error('move')
            );
          },
          // Python dispatches board:notice from this component's root after
          // it renders the new board, so the new cards already exist here.
          showNotice(detail) {
            this.notice = detail.message;
            if (detail.focusBoard) {
              // The completed card disappeared, so focus the board summary
              // instead of letting focus fall back to the page.
              this.$nextTick(() => this.$refs.boardStatus?.focus());
            }
            if (detail.focusTaskId) {
              // A move from the card's menu puts focus back on that menu,
              // which now sits in the destination column.
              this.$nextTick(() => {
                this.$el
                  .querySelector('#task-' + detail.focusTaskId + ' select')
                  ?.focus();
              });
            }
          },
        },
      });
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


def board_for(state: ProjectBoard.State):
    """Render the board again with the search text and filter the browser sent."""
    return ProjectBoard(
        lanes=board_snapshot(state.query, state.show_completed),
        query=state.query,
        show_completed=state.show_completed,
    )
