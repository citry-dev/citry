"""Shared Breadcrumbs scenario used by repository quality tools."""

from __future__ import annotations

import citry_ui
from citry import Citry, Component


def breadcrumbs_states_component(app: Citry) -> type[Component]:
    """Create the reusable Breadcrumbs state and environment scenario."""

    class CitryUiBreadcrumbsStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {
                "short": (
                    citry_ui.CBreadcrumbItem("Library", "/library"),
                    citry_ui.CBreadcrumbItem("Fantasy", "/library/fantasy"),
                    citry_ui.CBreadcrumbItem("A Wizard of Earthsea"),
                ),
                "linked_current": (
                    citry_ui.CBreadcrumbItem("Library", "/library"),
                    citry_ui.CBreadcrumbItem("New arrivals", "/library/new"),
                ),
                "long": tuple(
                    citry_ui.CBreadcrumbItem(label, f"/shelf/{index}")
                    if index < 5
                    else citry_ui.CBreadcrumbItem(label)
                    for index, label in enumerate(
                        (
                            "Library",
                            "Collections",
                            "Natural history",
                            "Forests",
                            "Temperate woodland",
                            "Field notes",
                        )
                    )
                ),
                "sizes": ("sm", "md", "lg"),
            }

        template = """
          <section class="citry-ui-quality-stack" aria-labelledby="breadcrumbs-states-title">
            <h1 id="breadcrumbs-states-title">Breadcrumbs states</h1>
            <c-CBreadcrumbs c-items="short" label="Book location" />
            <c-CBreadcrumbs c-items="linked_current" label="Collection location" />
            <c-CBreadcrumbs c-items="short" label="Custom separator location" separator="»" />
            <c-CBreadcrumbs c-items="short" label="Scoped separator location">
              <c-fill name="separator" data="{ index }">
                →
              </c-fill>
            </c-CBreadcrumbs>
            <c-for each="size in sizes">
              <c-CBreadcrumbs c-items="short" c-size="size" c-label="f'{size} location'" />
            </c-for>
            <div class="breadcrumbs-quality-narrow">
              <c-CBreadcrumbs c-items="long" label="Wrapping location" />
            </div>
            <div class="breadcrumbs-quality-narrow">
              <c-CBreadcrumbs c-items="long" label="Scrolling location" c-wrap="False" />
            </div>
            <div dir="rtl">
              <c-CBreadcrumbs c-items="short" label="موقع الكتاب" separator="←" />
            </div>
            <div class="breadcrumbs-quality-dark">
              <c-CBreadcrumbs c-items="short" label="Nested dark location" />
            </div>
            <div class="breadcrumbs-quality-brand breadcrumbs-quality-brand--cedar">
              <c-CBreadcrumbs c-items="short" label="Cedar location" />
            </div>
            <div class="breadcrumbs-quality-brand breadcrumbs-quality-brand--ink">
              <c-CBreadcrumbs c-items="short" label="Ink location" />
            </div>
          </section>
        """

        css = """
          :where(.breadcrumbs-quality-narrow) {
            inline-size: min(100%, 18rem);
          }

          :where(.breadcrumbs-quality-brand) {
            padding: 1rem;
            border-radius: 0.75rem;
          }

          :where(.breadcrumbs-quality-dark) {
            color-scheme: dark;
            padding: 1rem;
            background: Canvas;
            color: CanvasText;
          }

          :where(.breadcrumbs-quality-brand--cedar) {
            --cui-breadcrumbs-link-color: light-dark(#8a3b12, #fdba74);
            --cui-breadcrumbs-current-color: light-dark(#431407, #ffedd5);
            --cui-breadcrumbs-separator-color: light-dark(#9a3412, #fb923c);
            background: light-dark(#fff7ed, #34170a);
            color: light-dark(#431407, #ffedd5);
          }

          :where(.breadcrumbs-quality-brand--ink) {
            --cui-breadcrumbs-link-color: light-dark(#1d4ed8, #93c5fd);
            --cui-breadcrumbs-current-color: light-dark(#172554, #dbeafe);
            --cui-breadcrumbs-separator-color: light-dark(#475569, #cbd5e1);
            background: light-dark(#eff6ff, #111827);
            color: light-dark(#172554, #dbeafe);
          }
        """

    return CitryUiBreadcrumbsStates
