from typing import Any, NamedTuple

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CheckboxVariantView(NamedTuple):
    value: str
    title: str


class CheckboxVariantsAndSizes(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="checkbox-matrix" aria-label="Checkbox variants and sizes">
        <c-for each="variant in variants">
          <article>
            <h3>{{ variant.title }}</h3>
            <c-for each="size in sizes">
              <c-CCheckbox
                c-variant="variant.value"
                c-size="size"
                checked
              >
                {{ size }} preserved specimen
              </c-CCheckbox>
            </c-for>
            <c-CCheckbox c-variant="variant.value" indeterminate>
              Partly cataloged collection
            </c-CCheckbox>
            <c-CCheckbox c-variant="variant.value" disabled checked>
              Locked archive record
            </c-CCheckbox>
            <c-CCheckbox c-variant="variant.value" invalid>
              Provenance needs review
            </c-CCheckbox>
          </article>
        </c-for>
      </section>
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "variants": (
                CheckboxVariantView("solid", "Solid"),
                CheckboxVariantView("outline", "Outline"),
            ),
            "sizes": ("sm", "md", "lg"),
        }

    css = """
      :where(.checkbox-matrix) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
        gap: 1rem;
        max-width: 52rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.checkbox-matrix article) {
        display: grid;
        align-content: start;
        gap: 0.8rem;
        padding: 1rem;
        border: 1px solid light-dark(#c3d5c0, #405743);
        border-radius: 0.875rem;
        background: Canvas;
      }

      :where(.checkbox-matrix h3) {
        margin: 0 0 0.2rem;
      }
    """


preview = CheckboxVariantsAndSizes()

preview  # noqa: B018
