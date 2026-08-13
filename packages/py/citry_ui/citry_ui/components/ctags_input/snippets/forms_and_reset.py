import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagsInputFormsAndReset(Component):
    template = """
      <section
        class="tags-input-forms"
        x-data="{
          cancelReset:false,
          result:'No Form action yet',
        }"
      >
        <form
          id="tags-input-external-form"
          @submit.prevent="
            result = JSON.stringify(
              Array.from(new FormData($event.target).entries())
            )
          "
          @reset="
            if (cancelReset) {
              $event.preventDefault();
              result='Reset canceled';
            } else {
              setTimeout(() => result='Server baselines restored', 0);
            }
          "
        >
          <h3>Specimen routing Form</h3>
          <button type="submit">Submit repeated values</button>
          <button type="reset">Reset values and draft</button>
        </form>

        <c-CTagsInput
          id="external-routing-labels"
          name="labels"
          form="tags-input-external-form"
          required
          c-value="['urgent', 'billing']"
          input_value="unfinished"
          c-input_attrs="{'aria-label':'External routing labels'}"
        />

        <label>
          <input type="checkbox" x-model="cancelReset" />
          Cancel the next reset
        </label>

        <div class="tags-input-forms__transport">
          <c-CTagsInput
            name="readonly-labels"
            form="tags-input-external-form"
            readonly
            c-value="['preserved', 'ordered']"
            c-input_attrs="{'aria-label':'Readonly labels'}"
          />
          <c-CTagsInput
            name="disabled-labels"
            form="tags-input-external-form"
            disabled
            c-value="['omitted']"
            c-input_attrs="{'aria-label':'Disabled labels'}"
          />
        </div>

        <output aria-live="polite" x-text="result">
          No Form action yet
        </output>
      </section>
    """

    css = """
      :where(.tags-input-forms) {
        display: grid;
        gap: 1rem;
        max-inline-size: 42rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tags-input-forms form, .tags-input-forms__transport) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
      }

      :where(.tags-input-forms h3) {
        flex-basis: 100%;
        margin: 0;
      }
    """


preview = TagsInputFormsAndReset()

preview  # noqa: B018
