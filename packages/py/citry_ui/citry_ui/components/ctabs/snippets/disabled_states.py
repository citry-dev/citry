import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TabsDisabledStates(Component):
    template = """
      <section
        class="tabs-disabled"
        x-data="{ group_disabled: false }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <header>
          <p class="tabs-eyebrow">Launch windows</p>
          <h2>Inner-planet missions</h2>
        </header>

        <c-CTabs
          default_value="mercury"
          aria_label="Inner-planet mission windows"
          variant="pill"
          grow
          $c-props="{ disabled: group_disabled }"
        >
          <c-CTab value="mercury">
            Mercury
          </c-CTab>
          <c-CTab value="venus" disabled>
            Venus
          </c-CTab>
          <c-CTab value="mars">
            Mars
          </c-CTab>

          <c-CTabPanel value="mercury">
            The next transfer study opens in September.
          </c-CTabPanel>
          <c-CTabPanel value="venus">
            No launch window is available for this mission profile.
          </c-CTabPanel>
          <c-CTabPanel value="mars">
            The next transfer study opens in November.
          </c-CTabPanel>
        </c-CTabs>
      </section>
    """

    css = """
      :where(.tabs-disabled) {
        --cui-tabs-accent: light-dark(#4338ca, #a5b4fc);
        --cui-tabs-focus-color: light-dark(#4f46e5, #818cf8);
        --cui-tabs-active-background: light-dark(#eef2ff, #1e1b4b);
        max-width: 44rem;
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid color-mix(in srgb, var(--cui-tabs-accent) 46%, transparent);
        border-radius: 0.75rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tabs-disabled header) {
        margin-block-end: 1rem;
      }

      :where(.tabs-disabled h2, .tabs-disabled p) {
        margin-block: 0;
      }

      :where(.tabs-disabled header p) {
        color: var(--cui-tabs-accent);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }

      :where(.tabs-eyebrow) {
        color: var(--cui-tabs-accent, LinkText);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
      }
    """


preview_controls = (
    {
        "name": "group_disabled",
        "label": "Disable the whole group",
        "type": "checkbox",
        "default": False,
    },
)

preview = TabsDisabledStates()

preview  # noqa: B018
