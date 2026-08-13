from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CTagsInput

citry.register_library(citry_ui)


class BasicTagsInput(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        return {
            "python_tags": CTagsInput(
                name="reviewers",
                value=("ada@example.test", "grace@example.test"),
                variant="filled",
                input_attrs={"aria-label": "Reviewers"},
            )
        }

    template = """
      <section
        class="tags-input-basic"
        x-data="{submitted:'Nothing submitted yet'}"
      >
        <form
          @submit.prevent="
            submitted = JSON.stringify(
              new FormData($event.target).getAll('labels')
            )
          "
        >
          <c-CField required>
            <c-fill name="label">Routing labels</c-fill>
            <c-fill name="description">
              Press Enter or comma to add a label.
            </c-fill>
            <c-fill name="default">
              <c-CTagsInput
                name="labels"
                c-value="['urgent', 'billing']"
              />
            </c-fill>
          </c-CField>
          <button type="submit">Inspect repeated values</button>
        </form>

        <article>
          <h3>Direct Python composition</h3>
          {{ python_tags }}
        </article>

        <output x-text="submitted">Nothing submitted yet</output>
      </section>
    """

    css = """
      :where(.tags-input-basic) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tags-input-basic form, .tags-input-basic article) {
        display: grid;
        gap: 0.75rem;
        align-content: start;
        margin: 0;
        padding: 1rem;
        border: 1px solid color-mix(in srgb, CanvasText 20%, transparent);
        border-radius: 0.75rem;
      }

      :where(.tags-input-basic h3) {
        margin: 0;
      }

      :where(.tags-input-basic output) {
        grid-column: 1 / -1;
      }
    """


preview = BasicTagsInput()

preview  # noqa: B018
