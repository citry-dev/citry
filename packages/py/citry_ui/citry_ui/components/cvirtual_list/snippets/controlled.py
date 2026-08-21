import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class VirtualWindowControlled(Component):
    template = """
      <section x-data="{itemSize:56,overscan:2,last:'No request'}">
        <label>Row size <input type="range" min="40" max="72" x-model.number="itemSize" /></label>
        <label>Overscan <input type="range" min="0" max="8" x-model.number="overscan" /></label>
        <output x-text="last">No request</output>
        <c-CVirtualWindow
          aria_label="Controlled geometry"
          c-total_count="12"
          c-item_size="56"
          c-viewport_size="280"
          $c-props="{
            itemSize,
            overscan,
            onRangeChange:(detail)=>last=`${detail.reason}: ${detail.startIndex}-${detail.endIndex - 1}`,
          }"
        >
          <c-for each="index in indexes">
            <c-CVirtualListItem c-item_key="f'controlled-{index}'">Record {{ index + 1 }}</c-CVirtualListItem>
          </c-for>
        </c-CVirtualWindow>
      </section>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {"indexes": list(range(12))}

    css = """
      :where([data-citry-ui-part="item"]) { display:flex;align-items:center;padding-inline:1rem; }
      :where(label) { display:inline-flex;gap:0.5rem;margin-inline-end:1rem; }
      :where(output) { display:block;margin-block:0.5rem; }
    """


preview = VirtualWindowControlled()
preview  # noqa: B018
