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
