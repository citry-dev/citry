"""Shared Switch scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def switch_states_component(app: Citry) -> type[Component]:
    """Create the reusable Switch state and environment scenario."""

    class CitryUiSwitchStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section class="citry-ui-quality-stack" aria-labelledby="switch-states-title">
            <h1 id="switch-states-title">Switch states</h1>
            <div class="citry-ui-quality-grid">
              <c-CSwitch checked>Garden lighting</c-CSwitch>
              <c-CSwitch>
                <c-fill name="default">Air circulation</c-fill>
                <c-fill name="description">Keep air moving through the glasshouse.</c-fill>
              </c-CSwitch>
              <c-CSwitch checked disabled>Locked ventilation</c-CSwitch>
              <c-CSwitch invalid>Faulted irrigation</c-CSwitch>
              <c-for each="size in sizes">
                <c-CSwitch c-size="size" checked>{{ size }} size</c-CSwitch>
              </c-for>
              <c-CSwitch label_pos="start" checked>Label first</c-CSwitch>
            </div>
            <div x-data="{checked: true}" data-quality-state="controlled">
              <c-CSwitch
                $c-props="{checked}"
                @input="checked = $event.target.checked"
              >Controlled lighting</c-CSwitch>
              <button type="button" @click="checked = !checked">Change setting</button>
            </div>
            <form data-quality-state="formdata">
              <c-CSwitch name="quiet" value="enabled" required>Quiet hours</c-CSwitch>
              <button type="reset">Reset</button>
            </form>
            <c-CField control_id="quality-switch-field" required>
              <c-fill name="label">Field-owned reminder</c-fill>
              <c-fill name="default"><c-CSwitch name="reminder" /></c-fill>
              <c-fill name="description">Notify the household before sunset.</c-fill>
              <c-fill name="error">Enable the reminder.</c-fill>
            </c-CField>
            <div dir="rtl"><c-CSwitch checked label_pos="start">إضاءة المساء</c-CSwitch></div>
            <div style="color-scheme: dark"><c-CSwitch checked>Nested dark</c-CSwitch></div>
            <div class="switch-quality-brand switch-quality-brand--oak">
              <c-CSwitch checked>Oak brand</c-CSwitch>
            </div>
            <div class="switch-quality-brand switch-quality-brand--linen">
              <c-CSwitch checked>Linen brand</c-CSwitch>
            </div>
          </section>
        """

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"sizes": ("sm", "md", "lg")}

        css = """
          :where(.switch-quality-brand) {
            padding: 1rem;
            border-radius: 0.75rem;
          }

          :where(.switch-quality-brand--oak) {
            --cui-switch-on-color: light-dark(#7c4a25, #d8a06f);
            --cui-switch-foreground: light-dark(#40230f, #f5dfca);
            background: light-dark(#fff4e8, #2d1b0e);
          }

          :where(.switch-quality-brand--linen) {
            --cui-switch-on-color: light-dark(#426b63, #88c9bc);
            --cui-switch-foreground: light-dark(#1e3f39, #d9f3ed);
            background: light-dark(#edf8f5, #102925);
          }
        """

    return CitryUiSwitchStates
