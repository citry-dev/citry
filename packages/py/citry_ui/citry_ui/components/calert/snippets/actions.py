import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AlertActions(Component):
    template = """
      <section
        class="alert-actions-demo"
        x-data
        x-init="Alpine.store('alertActions', {visible: true})"
      >
        <div
          x-show="$store.alertActions.visible"
          x-bind:inert="!$store.alertActions.visible"
        >
          <c-CAlert
            intent="warn"
            actions_label="Cloud-cover actions"
          >
            <c-fill name="title">Cloud cover approaching</c-fill>
            <c-fill name="default">
              The western ridge may disappear after midnight.
            </c-fill>
            <c-fill name="actions">
              <c-CButton
                href="#forecast"
                size="sm"
                variant="outline"
              >
                Open forecast
              </c-CButton>
              <c-CButton
                size="sm"
                intent="neutral"
                @click="$store.alertActions.visible = false;
                  Alpine.nextTick(() => document
                    .getElementById('restore-observatory-notice')
                    .focus())"
              >
                Dismiss
              </c-CButton>
            </c-fill>
          </c-CAlert>
        </div>
        <button
          id="restore-observatory-notice"
          x-show="!$store.alertActions.visible"
          type="button"
          @click="$store.alertActions.visible = true"
        >
          Restore observatory notice
        </button>
      </section>
    """

    css = """
      :where(.alert-actions-demo) {
        display: grid;
        gap: 0.75rem;
        max-width: 52rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.alert-actions-demo > button) {
        justify-self: start;
        padding: 0.5rem 0.75rem;
        border: 1px solid light-dark(#8da1bb, #687b97);
        border-radius: 0.5rem;
        background: Canvas;
        color: CanvasText;
        cursor: pointer;
      }
    """


preview = AlertActions()

preview  # noqa: B018
