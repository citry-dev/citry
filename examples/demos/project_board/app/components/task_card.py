from app.citry_app import citry_app
from app.store import LANES, Task
from citry import Component


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
