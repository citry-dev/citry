import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SplitButtonDisabledAndLoading(Component):
    template = """
      <section
        class="split-button-disabled-demo"
        x-data="{
          disabled: false,
          primaryDisabled: false,
          menuDisabled: false,
          loading: false,
          saves: 0,
          last: 'Ready',
        }"
      >
        <h2>Large specimen image</h2>
        <div class="split-button-disabled-demo__controls" aria-label="Split Button state">
          <label><input type="checkbox" x-model="disabled" /> Disable both</label>
          <label><input type="checkbox" x-model="primaryDisabled" /> Disable primary</label>
          <label><input type="checkbox" x-model="menuDisabled" /> Disable Menu</label>
          <label><input type="checkbox" x-model="loading" /> Save pending</label>
        </div>

        <c-CSplitButton
          label="Specimen image actions"
          menu_label="More specimen image actions"
          c-primary_attrs="{'@click':'saves += 1; last = `Saved ${saves} times`'}"
          $c-props="{
            disabled,
            primaryDisabled,
            menuDisabled,
            loading,
            onAction: (value) => last = value,
          }"
        >
          <c-fill name="default">Save image</c-fill>
          <c-fill name="menu">
            <c-CMenuItem value="Export TIFF">Export TIFF</c-CMenuItem>
            <c-CMenuItem value="Export JPEG">Export JPEG</c-CMenuItem>
          </c-fill>
        </c-CSplitButton>
        <output aria-live="polite" x-text="last">Ready</output>

        <fieldset disabled>
          <legend>Disabled fieldset lifecycle</legend>
          <c-CSplitButton
            label="Fieldset-owned image actions"
            menu_label="More fieldset-owned image actions"
          >
            <c-fill name="default">Save fieldset image</c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="export-fieldset">Export fieldset image</c-CMenuItem>
            </c-fill>
          </c-CSplitButton>
        </fieldset>
      </section>
    """

    css = """
      :where(.split-button-disabled-demo) {
        display: grid;
        gap: 1rem;
        justify-items: start;
        inline-size: min(100%, 34rem);
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.split-button-disabled-demo h2) { margin: 0; }
      :where(.split-button-disabled-demo__controls) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem 1rem;
      }
      :where(.split-button-disabled-demo__controls label) {
        display: inline-flex;
        gap: 0.4rem;
        align-items: center;
      }
      :where(.split-button-disabled-demo fieldset) {
        inline-size: 100%;
        padding: 1rem;
        border: 1px solid GrayText;
        border-radius: 0.75rem;
      }

      @media (forced-colors: active) {
        :where(.split-button-disabled-demo fieldset) { border-color: CanvasText; }
      }
    """


preview = SplitButtonDisabledAndLoading()

preview  # noqa: B018
