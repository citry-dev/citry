from app.citry_app import citry_app
from citry import Component, SlotInput


class Lane(Component):
    citry = citry_app

    class Kwargs:
        lane_key: str
        title: str
        count: int

    class Slots:
        default: SlotInput

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
        :class="{ 'lane--drop-target': dropTarget }"
        c-style="accent_style"
        c-aria-label="title + ' column'"
        @dragover.prevent="highlightDropTarget($event)"
        @dragleave="clearDropTarget($event)"
        @drop.prevent="dropTask($event)"
      >
        <header class="lane__header">
          <h2>{{ title }}</h2>
          <span c-aria-label="count_label">{{ count }}</span>
        </header>
        <div class="lane__tasks">
          <c-if cond="count">
            <c-slot />
          </c-if>
          <c-else>
            <p class="lane-empty">No tasks shown</p>
          </c-else>
        </div>
        <footer class="lane__footer">
          {{ title }}: {{ count_label }} shown
        </footer>
      </section>
    """

    js = """
      $component({
        emits: ['drop-task'],
        data() {
          return { dropTarget: false };
        },
        methods: {
          highlightDropTarget(event) {
            this.dropTarget = true;
            event.dataTransfer.dropEffect = 'move';
          },
          clearDropTarget(event) {
            // dragleave also fires when the pointer moves onto one of the
            // column's own children, so keep the highlight until the pointer
            // leaves the column itself.
            if (!this.$el.contains(event.relatedTarget)) {
              this.dropTarget = false;
            }
          },
          dropTask(event) {
            // TaskCard stores these values when the drag starts.
            const taskId = Number(event.dataTransfer.getData('text/plain'));
            const sourceLane = event.dataTransfer.getData(
              'application/x-citry-lane',
            );
            this.dropTarget = false;
            // Ignore drags that did not start on a task card or carry no
            // valid task ID, and drops back onto the card's own column, so
            // the board sends no request for them.
            if (
              !sourceLane ||
              !Number.isSafeInteger(taskId) ||
              taskId <= 0 ||
              sourceLane === this.laneKey
            ) {
              return;
            }
            // ProjectBoard listens for this and sends the move to Python.
            this.$emit('drop-task', { taskId, lane: this.laneKey });
          },
        },
      });
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
