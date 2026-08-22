"""Shared Sortable scenario used by repository quality tools."""

from citry import Citry, Component


def sortable_states_component(app: Citry) -> type[Component]:
    class CitryUiSortableStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack" data-quality-sortable-ready>
            <h1>Sortable states</h1>
            <c-CSortable id="quality-sortable" name="quality-order" c-attrs="quality_attrs">
              <c-CSortableItem value="long" label="A very long localized Item that wraps safely">
                A very long localized Item that wraps safely without covering its handle or leaving the container.
              </c-CSortableItem>
              <c-CSortableItem value="rtl" label="Arabic Item"><span dir="rtl">عنصر عربي طويل</span></c-CSortableItem>
              <c-CSortableItem value="disabled" label="Fixed disabled Item" c-disabled="True" />
            </c-CSortable>
          </section>
        """

        def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
            return {
                "quality_attrs": {
                    "data-quality-states": "server enhanced form keyboard pointer disabled rtl narrow localized"
                }
            }

    return CitryUiSortableStates


__all__ = ["sortable_states_component"]
