import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SplitButtonDisabledAndLoading(Component):
    template = """
      <section
        class="split-button-disabled-demo"

      >
        <h2>Large specimen image</h2>
        <div class="split-button-disabled-demo__controls" aria-label="Split Button state">
          <label><input type="checkbox" v-model="disabled" /> Disable both</label>
          <label><input type="checkbox" v-model="primaryDisabled" /> Disable primary</label>
          <label><input type="checkbox" v-model="menuDisabled" /> Disable Menu</label>
          <label><input type="checkbox" v-model="loading" /> Save pending</label>
        </div>

        <c-CSplitButton
          ref="split"
          label="Specimen image actions"
          menu_label="More specimen image actions"
          v-bind="{
            disabled,
            primaryDisabled,
            menuDisabled,
            loading,
            onAction: (value) => last = value,
          }"
        >
          <c-fill name="default">
            Save image
          </c-fill>
          <c-fill name="menu">
            <c-CMenuItem value="Export TIFF">Export TIFF</c-CMenuItem>
            <c-CMenuItem value="Export JPEG">Export JPEG</c-CMenuItem>
          </c-fill>
        </c-CSplitButton>
        <output aria-live="polite" v-text="last">Ready</output>

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

    js = r"""
      $component({data(){return {
          disabled: false,
          primaryDisabled: false,
          menuDisabled: false,
          loading: false,
          saves: 0,
          last: 'Ready',
        };},
        onServerRender({component}) {
          const primary=component.$refs.split.$el.querySelector(
            '[data-citry-ui-part="split-button-primary"]'
          );
          const save=()=>{component.saves += 1; component.last=`Saved ${component.saves} times`;};
          primary.addEventListener('click',save);
          return ()=>primary.removeEventListener('click',save);
        },
      });
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
