from app.citry_app import citry_app
from citry import Component


class StandardPriorityBadge(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <span class="priority">Standard</span>
    """
