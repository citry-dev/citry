import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TabsControlledSelection(Component):
    template = """
      <section
        class="tabs-controlled"
        x-data="{
          current: 'mercury',
          requested: 'none',
          requestSource: 'none',
          applyRequests: true,
        }"
      >
        <header>
          <p>Owner-controlled selection</p>
          <h2>Planetary briefing</h2>
        </header>

        <div
          class="tabs-controlled__owner-actions"
          role="group"
          aria-label="Select a briefing"
        >
          <button type="button" @click="current = 'mercury'">
            Show Mercury
          </button>
          <button type="button" @click="current = 'europa'">
            Show Europa
          </button>
          <button type="button" @click="current = 'titan'">
            Show Titan
          </button>
        </div>

        <label class="tabs-controlled__commit">
          <input type="checkbox" x-model="applyRequests" />
          <span>Apply requests from Tabs</span>
        </label>

        <dl class="tabs-controlled__status" aria-live="polite">
          <div>
            <dt>Selected</dt>
            <dd x-text="current">mercury</dd>
          </div>
          <div>
            <dt>Last request</dt>
            <dd>
              <span x-text="requested">none</span>
              <span x-show="requestSource !== 'none'">
                via <span x-text="requestSource"></span>
              </span>
            </dd>
          </div>
        </dl>

        <c-CTabs
          default_value="mercury"
          aria_label="Planetary briefing topics"
          $c-props="{
            value: current,
            onValueChange: (value, detail) => {
              requested = value;
              requestSource = detail.source;
              if (applyRequests) {
                current = value;
              }
            },
          }"
        >
          <c-CTab value="mercury">
            Mercury
          </c-CTab>
          <c-CTab value="europa">
            Europa
          </c-CTab>
          <c-CTab value="titan">
            Titan
          </c-CTab>

          <c-CTabPanel value="mercury">
            Mercury has the shortest year of any planet.
          </c-CTabPanel>
          <c-CTabPanel value="europa">
            Europa's fractured ice may cover a deep ocean.
          </c-CTabPanel>
          <c-CTabPanel value="titan">
            Titan has a dense atmosphere rich in nitrogen.
          </c-CTabPanel>
        </c-CTabs>
      </section>
    """

    css = """
      :where(.tabs-controlled) {
        --cui-tabs-accent: light-dark(#4338ca, #a5b4fc);
        --cui-tabs-focus-color: light-dark(#4f46e5, #818cf8);
        display: grid;
        gap: 1rem;
        max-width: 48rem;
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid color-mix(in srgb, var(--cui-tabs-accent) 46%, transparent);
        border-radius: 0.75rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tabs-controlled h2, .tabs-controlled p) {
        margin-block: 0;
      }

      :where(.tabs-controlled header p) {
        color: var(--cui-tabs-accent);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }

      :where(.tabs-controlled__owner-actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
      }

      :where(.tabs-controlled__owner-actions button) {
        min-height: 2.25rem;
        padding-inline: 0.75rem;
        border: 1px solid color-mix(in srgb, currentColor 24%, transparent);
        border-radius: 0.375rem;
        background: Canvas;
        color: CanvasText;
        font: inherit;
        cursor: pointer;
      }

      :where(.tabs-controlled__owner-actions button:focus-visible) {
        outline: 0.1875rem solid var(--cui-tabs-focus-color);
        outline-offset: 0.125rem;
      }

      :where(.tabs-controlled__commit) {
        display: flex;
        gap: 0.5rem;
        align-items: center;
        width: fit-content;
      }

      :where(.tabs-controlled__commit input) {
        inline-size: 1rem;
        block-size: 1rem;
        margin: 0;
      }

      :where(.tabs-controlled__status) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem 1.5rem;
        margin: 0;
        padding: 0.75rem;
        border-radius: 0.5rem;
        background: color-mix(in srgb, currentColor 7%, transparent);
      }

      :where(.tabs-controlled__status div) {
        display: flex;
        gap: 0.375rem;
      }

      :where(.tabs-controlled__status dt) {
        color: color-mix(in srgb, currentColor 68%, transparent);
      }

      :where(.tabs-controlled__status dd) {
        margin: 0;
        font-weight: 700;
      }
    """


preview = TabsControlledSelection()

preview  # noqa: B018
