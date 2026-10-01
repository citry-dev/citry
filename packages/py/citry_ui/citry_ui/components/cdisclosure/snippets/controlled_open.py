import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledDisclosure(Component):
    template = """
      <section
        class="controlled-disclosure"
      >
        <c-CDisclosure
          :open="controlled ? open : null" :onOpenChange="(next, detail) => {
              last = `${detail.source}: ${next ? 'open' : 'closed'}`;
              if (controlled && accept) open = next;
            }"
        >
          <c-fill name="title">Advanced logging</c-fill>
          <c-fill name="default">
            Include request identifiers and timing details in diagnostic output.
          </c-fill>
        </c-CDisclosure>
        <label>
          <input type="checkbox" v-model="accept" />
          Accept trigger requests
        </label>
        <div class="controlled-disclosure__controls" role="group" aria-label="Disclosure owner controls">
          <button type="button" @click="controlled=true; open=true">Show</button>
          <button type="button" @click="controlled=true; open=false">Hide</button>
          <button type="button" @click="controlled=false">Release control</button>
        </div>
        <output>
          Ownership: <span v-text="controlled ? 'browser-controlled' : 'released'">browser-controlled</span>
          · Requests: <span v-text="accept ? 'accepted' : 'refused'">accepted</span>
          · Last: <span v-text="last">none</span>
        </output>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            open:false, controlled:true, accept:true, last:'none'
          };
        },
      });
    """

    css = """
      :where(.controlled-disclosure) { display: grid; gap: 0.75rem; }
      :where(.controlled-disclosure__controls) { display: flex; flex-wrap: wrap; }
      :where(.controlled-disclosure__controls > button) {
        min-block-size: 2rem;
        padding-inline: 0.75rem;
        border: 1px solid color-mix(in srgb, currentColor 24%, transparent);
        background: Canvas;
        color: CanvasText;
        font: inherit;
      }
    """


preview = ControlledDisclosure()
preview  # noqa: B018
