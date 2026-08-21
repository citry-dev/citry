import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class VirtualListAtAGlance(Component):
    template = """
      <c-CVirtualList aria_label="Build activity" c-estimated_item_size="64">
        <c-for each="entry in entries">
          <c-CVirtualListItem c-item_key="entry['key']">
            <article>
              <strong>{{ entry['title'] }}</strong><br />
              <small>{{ entry['detail'] }}</small>
            </article>
          </c-CVirtualListItem>
        </c-for>
      </c-CVirtualList>
    """
    css = """
      :where([data-citry-ui-part="virtual-list"] article) {
        padding: 0.75rem 1rem;
        border-block-end: 1px solid color-mix(in srgb, currentColor 14%, transparent);
      }
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "entries": [
                {"key": f"build-{index}", "title": f"Build {2400 + index}", "detail": "Checks passed"}
                for index in range(80)
            ]
        }


preview = VirtualListAtAGlance()
preview  # noqa: B018
