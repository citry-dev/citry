import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledMissionTarget(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section
        class="controlled-target"
        x-data
        x-init="Alpine.store('missionTarget', {
          value: null,
          query: '',
          open: false,
          lastReason: 'none',
        })"
      >
        <c-CField>
          <c-fill name="label">
            Mission target
          </c-fill>
          <c-fill name="default">
            <c-CCombobox
              c-options="targets"
              $c-props="{
                value: $store.missionTarget.value,
                inputValue: $store.missionTarget.query,
                open: $store.missionTarget.open,
                onValueChange: (next, detail) => {
                  $store.missionTarget.value = next;
                  $store.missionTarget.lastReason = `value: ${detail.reason}`;
                },
                onInputValueChange: (next, detail) => {
                  $store.missionTarget.query = next;
                  $store.missionTarget.lastReason = `query: ${detail.reason}`;
                },
                onOpenChange: (next, detail) => {
                  $store.missionTarget.open = next;
                  $store.missionTarget.lastReason = `popup: ${detail.reason}`;
                },
              }"
            />
          </c-fill>
        </c-CField>
        <dl aria-live="polite">
          <div>
            <dt>Value</dt>
            <dd x-text="$store.missionTarget.value ?? 'none'">none</dd>
          </div>
          <div>
            <dt>Query</dt>
            <dd x-text="$store.missionTarget.query || 'empty'">empty</dd>
          </div>
          <div>
            <dt>Last request</dt>
            <dd x-text="$store.missionTarget.lastReason">none</dd>
          </div>
        </dl>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "targets": (
                citry_ui.CComboboxOption("ceres", "Ceres", "Dwarf planet in the asteroid belt"),
                citry_ui.CComboboxOption("vesta", "Vesta", "Large rocky asteroid"),
                citry_ui.CComboboxOption("psyche", "16 Psyche", "Metal-rich asteroid"),
            )
        }

    css = """
      :where(.controlled-target) {
        display: grid;
        gap: 1rem;
        max-width: 34rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#ddd6fe, #5b21b6);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.controlled-target dl) {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.75rem;
        margin: 0;
      }

      :where(.controlled-target dl > div) {
        min-width: 0;
        padding: 0.625rem;
        border-radius: 0.5rem;
        background: color-mix(in srgb, CanvasText 6%, Canvas);
      }

      :where(.controlled-target dt) {
        color: color-mix(in srgb, currentColor 65%, transparent);
        font-size: 0.75rem;
      }

      :where(.controlled-target dd) {
        margin: 0.2rem 0 0;
        overflow-wrap: anywhere;
        font-size: 0.875rem;
        font-weight: 650;
      }
    """


preview = ControlledMissionTarget()

preview  # noqa: B018
