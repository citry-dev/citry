import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ConfigureCombobox(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section
        class="combo-config"
        x-data
        x-init="Alpine.store('comboConfig', {
          variant: 'outline',
          size: 'md',
          filter: 'contains',
          clearable: true,
          open_on_focus: false,
          auto_highlight: false,
        })"
        @citry-ui-preview-controls.window="Object.assign($store.comboConfig, $event.detail)"
      >
        <p>Observatory controls</p>
        <h2>Configure the catalog</h2>
        <c-CField>
          <c-fill name="label">
            Deep-sky object
          </c-fill>
          <c-fill name="default">
            <c-CCombobox
              c-options="objects"
              placeholder="Search the catalog"
              $c-props="{
                variant: $store.comboConfig.variant,
                size: $store.comboConfig.size,
                filter: $store.comboConfig.filter,
                clearable: $store.comboConfig.clearable,
                openOnFocus: $store.comboConfig.open_on_focus,
                autoHighlight: $store.comboConfig.auto_highlight,
              }"
            />
          </c-fill>
        </c-CField>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "objects": (
                citry_ui.CComboboxOption("m31", "Andromeda Galaxy", "Spiral galaxy in Andromeda"),
                citry_ui.CComboboxOption("m42", "Orion Nebula", "Diffuse nebula in Orion"),
                citry_ui.CComboboxOption("m45", "Pleiades", "Open star cluster in Taurus"),
                citry_ui.CComboboxOption("ngc7000", "North America Nebula", "Emission nebula in Cygnus"),
            )
        }

    css = """
      :where(.combo-config) {
        display: grid;
        gap: 0.75rem;
        max-width: 38rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#bae6fd, #075985);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.combo-config h2, .combo-config p) {
        margin: 0;
      }

      :where(.combo-config > p) {
        color: light-dark(#0369a1, #7dd3fc);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview_controls = (
    {
        "name": "variant",
        "label": "Variant",
        "type": "select",
        "default": "outline",
        "options": (("outline", "Outline"), ("filled", "Filled"), ("plain", "Plain")),
    },
    {
        "name": "size",
        "label": "Size",
        "type": "select",
        "default": "md",
        "options": (("sm", "Small"), ("md", "Medium"), ("lg", "Large")),
    },
    {
        "name": "filter",
        "label": "Local filter",
        "type": "select",
        "default": "contains",
        "options": (("contains", "Contains"), ("starts_with", "Starts with"), ("none", "None")),
    },
    {"name": "clearable", "label": "Show clear action", "type": "checkbox", "default": True},
    {"name": "open_on_focus", "label": "Open on focus", "type": "checkbox", "default": False},
    {"name": "auto_highlight", "label": "Highlight first match", "type": "checkbox", "default": False},
)

preview = ConfigureCombobox()

preview  # noqa: B018
