"""Shared Virtual List scenario used by repository quality tools."""

from citry import Citry, Component


def virtual_list_states_component(app: Citry) -> type[Component]:
    class CitryUiVirtualListStates(Component):
        citry = app
        template = """
          <section
            class="citry-ui-quality-stack virtual-list-quality"
            data-quality-virtual-list-ready
            x-data="{itemSize:48,overscan:3,last:'No range request'}"
          >
            <h1>Virtual List states</h1>
            <div class="virtual-list-quality__grid">
              <section>
                <h2>Complete server DOM</h2>
                <c-CVirtualList
                  aria_label="Complete quality records"
                  c-estimated_item_size="64"
                  c-viewport_size="320"
                  c-attrs="{'data-quality-states':'complete-dom css-only variable-height keyboard focus print'}"
                >
                  <c-for each="record in complete_records">
                    <c-CVirtualListItem c-item_key="record['key']">
                      <article>
                        <strong>{{ record['title'] }}</strong>
                        <p>{{ record['detail'] }}</p>
                      </article>
                    </c-CVirtualListItem>
                  </c-for>
                </c-CVirtualList>
              </section>
              <section>
                <h2>Controlled fixed window</h2>
                <c-CVirtualWindow
                  aria_label="Windowed quality records"
                  c-total_count="10000"
                  c-start_index="20"
                  c-item_size="48"
                  c-initial_index="20"
                  c-viewport_size="320"
                  c-attrs="{'data-quality-states':'window fixed-size positions spacers pending controlled cleanup'}"
                  $c-props="{
                    itemSize,
                    overscan,
                    onRangeChange:(detail)=>last=`${detail.reason}: ${detail.startIndex}-${detail.endIndex - 1}`,
                  }"
                >
                  <c-for each="record in window_records">
                    <c-CVirtualListItem c-item_key="record['key']">
                      <span>{{ record['number'] }}</span><strong>{{ record['title'] }}</strong>
                    </c-CVirtualListItem>
                  </c-for>
                </c-CVirtualWindow>
                <output x-text="last">No range request</output>
              </section>
              <section dir="rtl" style="color-scheme:dark">
                <h2>RTL dark complete list</h2>
                <c-CVirtualList aria_label="سجل كامل" c-viewport_size="220" c-focusable="False">
                  <c-for each="record in rtl_records">
                    <c-CVirtualListItem c-item_key="record['key']">{{ record['title'] }}</c-CVirtualListItem>
                  </c-for>
                </c-CVirtualList>
              </section>
            </div>
          </section>
        """
        css = """
          :where(.virtual-list-quality__grid) { display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem; }
          :where(.virtual-list-quality [data-citry-ui-part="item"]) {
            padding:0.75rem 1rem;border-block-end:1px solid color-mix(in srgb,currentColor 14%,transparent);
          }
          :where(.virtual-list-quality [data-strategy="window"] [data-citry-ui-part="item"]) {
            display:flex;align-items:center;gap:0.75rem;
          }
          :where(.virtual-list-quality article p) { margin-block:0.25rem 0; }
          @media (max-width:48rem) { :where(.virtual-list-quality__grid) { grid-template-columns:1fr; } }
        """

        def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
            return {
                "complete_records": [
                    {
                        "key": f"complete-{index}",
                        "title": f"Complete record {index + 1}",
                        "detail": "Variable-height server content remains in the document.",
                    }
                    for index in range(48)
                ],
                "window_records": [
                    {"key": f"window-{index}", "number": f"#{index + 1:05d}", "title": "Fixed row"}
                    for index in range(20, 36)
                ],
                "rtl_records": [{"key": f"rtl-{index}", "title": f"السجل {index + 1}"} for index in range(12)],
            }

    return CitryUiVirtualListStates


__all__ = ["virtual_list_states_component"]
