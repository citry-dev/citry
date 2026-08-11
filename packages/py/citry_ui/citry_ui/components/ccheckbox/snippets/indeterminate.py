import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class IndeterminateCheckbox(Component):
    template = """
      <section
        class="habitat-summary"
        x-data="{
          meadow: true,
          woodland: false,
          wetland: true,
          get count() { return [this.meadow, this.woodland, this.wetland].filter(Boolean).length },
          get all() { return this.count === 3 },
          get mixed() { return this.count > 0 && this.count < 3 },
          setAll(value) { this.meadow = value; this.woodland = value; this.wetland = value },
        }"
      >
        <c-CCheckbox
          variant="outline"
          $c-props="{checked: all, indeterminate: mixed}"
          @input="setAll($event.target.checked)"
        >
          <c-fill name="default">All survey habitats</c-fill>
          <c-fill name="description">
            <span x-text="`${count} of 3 selected`"></span>
          </c-fill>
        </c-CCheckbox>
        <div class="habitat-summary__children">
          <c-CCheckbox
            $c-props="{checked: meadow}"
            @input="meadow = $event.target.checked"
          >
            Limestone meadow
          </c-CCheckbox>
          <c-CCheckbox
            $c-props="{checked: woodland}"
            @input="woodland = $event.target.checked"
          >
            Beech woodland
          </c-CCheckbox>
          <c-CCheckbox
            $c-props="{checked: wetland}"
            @input="wetland = $event.target.checked"
          >
            Reed wetland
          </c-CCheckbox>
        </div>
      </section>
    """

    css = """
      :where(.habitat-summary) {
        display: grid;
        gap: 0.9rem;
        max-width: 36rem;
        padding: 1rem;
        border: 1px solid light-dark(#b8d0b9, #3b5a41);
        border-radius: 0.875rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.habitat-summary__children) {
        display: grid;
        gap: 0.7rem;
        padding-inline-start: 1.75rem;
      }
    """


preview = IndeterminateCheckbox()

preview  # noqa: B018
