import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledSplitButtonMenu(Component):
    template = """
      <section
        class="split-button-controlled"
        x-data="{
          open:false,
          controlled:true,
          accept:true,
          lastReason:'none'
        }"
      >
        <c-CSplitButton
          label="Publication actions"
          menu_label="More publication actions"
          $c-props="{
            open: controlled ? open : null,
            onOpenChange: (nextOpen, detail) => {
              lastReason = detail.reason;
              if (controlled && accept) open = nextOpen;
            },
          }"
        >
          <c-fill name="default">Publish specimen</c-fill>
          <c-fill name="menu">
            <c-CMenuItem value="preview">Preview publication</c-CMenuItem>
            <c-CMenuItem value="schedule">Schedule publication</c-CMenuItem>
          </c-fill>
        </c-CSplitButton>

        <label>
          <input type="checkbox" x-model="accept" />
          Accept Menu requests
        </label>
        <div role="group" aria-label="Menu owner controls">
          <button type="button" @click="controlled=true;open=true">
            Show
          </button>
          <button type="button" @click="controlled=true;open=false">
            Hide
          </button>
          <button type="button" @click="controlled=false">
            Release control
          </button>
        </div>
        <output>
          Ownership:
          <span x-text="controlled ? 'controlled' : 'released'">
            controlled
          </span>
          · Last reason:
          <span x-text="lastReason">none</span>
        </output>
      </section>
    """

    css = """
      :where(.split-button-controlled) {
        display: grid;
        gap: 0.85rem;
        justify-items: start;
        min-block-size: 17rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.split-button-controlled [role="group"]) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
      }
    """


preview = ControlledSplitButtonMenu()

preview  # noqa: B018
