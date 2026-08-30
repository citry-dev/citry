from app.citry_app import citry_app
from citry import Component


class HighPriorityBadge(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <span class="priority priority--high">High priority</span>
    """
