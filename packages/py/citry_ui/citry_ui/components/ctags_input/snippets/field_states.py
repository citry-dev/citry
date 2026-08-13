import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagsInputFieldStates(Component):
    template = """
      <section
        class="tags-input-fields"
        x-data="{
          required:true,
          readonly:false,
          moveDisabled:true,
        }"
      >
        <div class="tags-input-fields__controls">
          <label><input type="checkbox" x-model="required" /> Required</label>
          <label><input type="checkbox" x-model="readonly" /> Readonly</label>
          <button
            type="button"
            @click="
              const target = moveDisabled ? $refs.disabled : $refs.enabled;
              target.append($refs.moving);
              moveDisabled = !moveDisabled;
            "
          >
            Move the Field between fieldsets
          </button>
        </div>

        <c-CField
          $c-props="{required,readonly}"
        >
          <c-fill name="label">Publication topics</c-fill>
          <c-fill name="description">
            Field owns required and readonly state for the TagsInput.
          </c-fill>
          <c-fill name="default">
            <c-CTagsInput
              name="topics"
              c-value="['botany', 'fieldwork']"
            />
          </c-fill>
        </c-CField>

        <c-CField invalid>
          <c-fill name="label">Review labels</c-fill>
          <c-fill name="default">
            <c-CTagsInput name="review" c-value="['needs-source']" />
          </c-fill>
          <c-fill name="error">Resolve the review label before publishing.</c-fill>
        </c-CField>

        <div class="tags-input-fields__fieldsets">
          <fieldset x-ref="enabled">
            <legend>Enabled ancestry</legend>
            <div x-ref="moving">
              <c-CField>
                <c-fill name="label">Moved labels</c-fill>
                <c-fill name="default">
                  <c-CTagsInput name="moved" c-value="['portable']" />
                </c-fill>
              </c-CField>
            </div>
          </fieldset>
          <fieldset x-ref="disabled" disabled>
            <legend>Disabled ancestry</legend>
          </fieldset>
        </div>
      </section>
    """

    css = """
      :where(.tags-input-fields) {
        display: grid;
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tags-input-fields__controls, .tags-input-fields__fieldsets) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }

      :where(.tags-input-fields fieldset) {
        flex: 1 1 16rem;
        min-inline-size: 0;
      }
    """


preview = TagsInputFieldStates()

preview  # noqa: B018
