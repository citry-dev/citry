import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class VirtualWindowExample(Component):
    template = """
      <section x-data="{last:'This static preview supplies one complete window'}">
        <output x-text="last">This static preview supplies one complete window</output>
        <c-CVirtualWindow
          aria_label="Audit records"
          c-total_count="16"
          c-item_size="48"
          $c-props="{onRangeChange:(detail)=>last=`Requested ${detail.startIndex}-${detail.endIndex - 1}`}"
        >
          <c-for each="record in records">
            <c-CVirtualListItem c-item_key="record['key']">
              <span>{{ record['number'] }}</span> {{ record['label'] }}
            </c-CVirtualListItem>
          </c-for>
        </c-CVirtualWindow>
      </section>
    """
    css = """
      :where([data-citry-ui-part="item"]) {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding-inline: 1rem;
        border-block-end: 1px solid color-mix(in srgb, currentColor 12%, transparent);
      }
      :where([data-citry-ui-part="item"] > span) { color: GrayText; font-variant-numeric: tabular-nums; }
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "records": [
                {"key": f"audit-{index}", "number": f"#{index + 1:05d}", "label": "Signed deployment record"}
                for index in range(16)
            ]
        }


preview = VirtualWindowExample()
preview  # noqa: B018
