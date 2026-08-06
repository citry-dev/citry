import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TabsKeyboardActivation(Component):
    template = """
      <section
        class="tabs-activation"
        x-data="{ automaticValue: 'orbit', manualValue: 'orbit' }"
      >
        <article class="tabs-activation__card">
          <header>
            <p class="tabs-eyebrow">Arrow keys select immediately</p>
            <h2>Automatic</h2>
            <output x-text="automaticValue">orbit</output>
          </header>

          <c-CTabs
            default_value="orbit"
            aria_label="Automatic probe data"
            activation="automatic"
            $c-props="{
              onValueChange: (value) => {
                automaticValue = value;
              },
            }"
          >
            <c-CTab value="orbit">
              Orbit
            </c-CTab>
            <c-CTab value="surface">
              Surface
            </c-CTab>
            <c-CTab value="signals">
              Signals
            </c-CTab>

            <c-CTabPanel value="orbit">
              The probe is completing its 18th orbit.
            </c-CTabPanel>
            <c-CTabPanel value="surface">
              Surface imaging resumes after local sunrise.
            </c-CTabPanel>
            <c-CTabPanel value="signals">
              The high-gain antenna is locked on Earth.
            </c-CTabPanel>
          </c-CTabs>
        </article>

        <article class="tabs-activation__card tabs-activation__card--manual">
          <header>
            <p class="tabs-eyebrow">Arrow keys move focus; Enter or Space selects</p>
            <h2>Manual</h2>
            <output x-text="manualValue">orbit</output>
          </header>

          <c-CTabs
            default_value="orbit"
            aria_label="Manual probe data"
            activation="manual"
            $c-props="{
              onValueChange: (value) => {
                manualValue = value;
              },
            }"
          >
            <c-CTab value="orbit">
              Orbit
            </c-CTab>
            <c-CTab value="surface">
              Surface
            </c-CTab>
            <c-CTab value="signals">
              Signals
            </c-CTab>

            <c-CTabPanel value="orbit">
              The probe is completing its 18th orbit.
            </c-CTabPanel>
            <c-CTabPanel value="surface">
              Surface imaging resumes after local sunrise.
            </c-CTabPanel>
            <c-CTabPanel value="signals">
              The high-gain antenna is locked on Earth.
            </c-CTabPanel>
          </c-CTabs>
        </article>
      </section>
    """

    css = """
      :where(.tabs-activation) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
        gap: 1rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tabs-activation__card) {
        --cui-tabs-accent: light-dark(#4338ca, #a5b4fc);
        --cui-tabs-focus-color: light-dark(#4f46e5, #818cf8);
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid color-mix(in srgb, var(--cui-tabs-accent) 46%, transparent);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.tabs-activation__card--manual) {
        --cui-tabs-accent: light-dark(#0f766e, #5eead4);
        --cui-tabs-focus-color: light-dark(#0d9488, #2dd4bf);
      }

      :where(.tabs-activation__card header) {
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 0.125rem 0.75rem;
        align-items: end;
        margin-block-end: 0.75rem;
      }

      :where(.tabs-activation__card h2, .tabs-activation__card p) {
        margin-block: 0;
      }

      :where(.tabs-activation__card header p) {
        grid-column: 1 / -1;
        color: color-mix(in srgb, currentColor 68%, transparent);
        font-size: 0.75rem;
      }

      :where(.tabs-activation__card output) {
        color: var(--cui-tabs-accent);
        font-weight: 700;
      }

      :where(.tabs-eyebrow) {
        color: var(--cui-tabs-accent, LinkText);
        font-size: 0.75rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
      }
    """


preview = TabsKeyboardActivation()

preview  # noqa: B018
