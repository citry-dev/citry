import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class VirtualListAccessibility(Component):
    template = """
      <c-CStack>
        <section>
          <h2>Complete collection</h2>
          <c-CVirtualList aria_label="All release notes" c-viewport_size="220">
            <c-for each="index in complete_indexes">
              <c-CVirtualListItem c-item_key="f'complete-{index}'">
                <a c-href="f'#release-{index + 1}'">Release {{ index + 1 }}</a>
              </c-CVirtualListItem>
            </c-for>
          </c-CVirtualList>
        </section>
        <section>
          <h2>Supplied range</h2>
          <c-CVirtualWindow
            aria_label="Windowed release notes"
            c-total_count="8"
            c-item_size="44"
            c-viewport_size="220"
          >
            <c-for each="index in window_indexes">
              <c-CVirtualListItem c-item_key="f'window-{index}'">Release {{ index + 1 }}</c-CVirtualListItem>
            </c-for>
          </c-CVirtualWindow>
        </section>
      </c-CStack>
    """
    css = """
      :where([data-citry-ui-part="item"]) {
        display:flex;align-items:center;padding-inline:0.75rem;min-block-size:44px;
      }
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {"complete_indexes": list(range(16)), "window_indexes": list(range(8))}


preview = VirtualListAccessibility()
preview  # noqa: B018
