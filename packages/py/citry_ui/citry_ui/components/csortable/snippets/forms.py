import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SortableForms(Component):
    template = """
      <form>
        <c-CSortable name="priority" c-order="['security','quality','speed']">
          <c-CSortableItem value="speed" label="Delivery speed" />
          <c-CSortableItem value="quality" label="Product quality" />
          <c-CSortableItem value="security" label="Security" />
        </c-CSortable>
        <button type="reset">Reset order</button>
        <button type="submit">Save priorities</button>
      </form>
    """


preview = SortableForms()
preview  # noqa: B018
