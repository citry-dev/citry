import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SplitButtonAtAGlance(Component):
    template = """
      <section
        class="split-button-glance"
        x-data="{saved:0,last:'No action yet'}"
      >
        <p class="split-button-glance__eyebrow">Field journal</p>
        <h2>Alpine gentian specimen</h2>
        <p>Keep the primary save action visible and related work nearby.</p>
        <c-CSplitButton
          label="Save specimen actions"
          menu_label="More save specimen actions"
          c-primary_attrs="{'@click':'saved += 1; last = `Saved specimen ${saved}`'}"
          $c-props="{onAction:(value)=>last=value}"
        >
          <c-fill name="default">Save specimen</c-fill>
          <c-fill name="menu">
            <c-CMenuItem value="Save a copy">Save a copy</c-CMenuItem>
            <c-CMenuItem value="Export record">Export record</c-CMenuItem>
            <c-CMenuItem value="Archive specimen" intent="danger">
              Archive specimen
            </c-CMenuItem>
          </c-fill>
        </c-CSplitButton>
        <output x-text="last">No action yet</output>
      </section>
    """

    css = """
      :where(.split-button-glance) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        min-block-size: 18rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.split-button-glance h2, .split-button-glance p) {
        margin: 0;
      }

      :where(.split-button-glance__eyebrow) {
        color: light-dark(#3f6b42, #9ed5a1);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview = SplitButtonAtAGlance()

preview  # noqa: B018
