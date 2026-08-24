from citry import Component

from ..citry_app import citry_app


class HighPriorityBadge(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    template = '<span class="priority priority--high">High priority</span>'


class StandardPriorityBadge(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    template = '<span class="priority">Standard</span>'


class BadgeStyles(Component):
    """Collect the shared stylesheet once without wrapping badge markup."""

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
        color: #58625b;
        background: #eceee9;
        font-size: 0.68rem;
        font-weight: 750;
      }
      .priority--high { color: #9b3e22; background: #ffe2d5; }
    """
