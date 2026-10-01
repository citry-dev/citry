from app.citry_app import citry_app
from citry import Component


class PriorityBadge(Component):
    """Show a task's priority as a small pill, highlighted for high priority."""

    citry = citry_app

    class Kwargs:
        high: bool

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots):
        return {
            "label": "High priority" if kwargs.high else "Standard",
            "high": kwargs.high,
        }

    template = """
      <span
        class="priority"
        c-class="{'priority--high': high}"
      >
        {{ label }}
      </span>
    """

    css = """
      .priority {
        display: inline-flex;
        align-items: center;
        min-height: 1.55rem;
        padding: 0.18rem 0.48rem;
        border-radius: 999px;
        color: var(--color-faint);
        background: var(--color-border-subtle);
        font-size: 0.68rem;
        font-weight: 650;
      }

      .priority--high {
        color: var(--color-accent-ink);
        background: var(--color-accent-soft);
      }
    """
