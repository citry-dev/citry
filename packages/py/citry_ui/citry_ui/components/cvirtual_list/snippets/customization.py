import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class VirtualListCustomization(Component):
    template = """
      <c-CVirtualList aria_label="Pinned environments" class_="environment-list" c-viewport_size="260">
        <c-for each="environment in environments">
          <c-CVirtualListItem c-item_key="environment['key']">
            <strong>{{ environment['name'] }}</strong>
            <span>{{ environment['region'] }}</span>
          </c-CVirtualListItem>
        </c-for>
      </c-CVirtualList>
    """
    css = """
      :where(.environment-list) {
        --cui-virtual-list-border: 2px solid #7c3aed;
        --cui-virtual-list-radius: 1rem;
        --cui-virtual-list-background: light-dark(#faf5ff, #2e1065);
        --cui-virtual-list-item-background: light-dark(#fff, #1e1b4b);
      }
      :where(.environment-list [data-citry-ui-part="item"]) {
        display:grid;
        grid-template-columns:1fr auto;
        gap:1rem;
        padding:0.875rem 1rem;
        margin:0.5rem;
        border-radius:0.625rem;
      }
      :where(.environment-list [data-citry-ui-part="item"] span) { color:GrayText; }
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "environments": [
                {"key": f"environment-{index}", "name": f"Service {index + 1}", "region": "eu-central"}
                for index in range(24)
            ]
        }


preview = VirtualListCustomization()
preview  # noqa: B018
