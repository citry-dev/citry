from app.citry_app import citry_app
from citry import Component


class BadgeStyles(Component):
    """Provide the CSS shared by both priority badges."""

    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    template = ""

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
