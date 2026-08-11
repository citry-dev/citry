"""Shared Icon scenario used by repository quality tools."""

from __future__ import annotations

from typing import Any, get_args

from citry import Citry, Component
from citry_ui.components.cicon import CIconName


def icon_states_component(app: Citry) -> type[Component]:
    """Create the reusable Icon catalog and semantics scenario."""

    class CitryUiIconStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section
            class="citry-ui-quality-stack"
            aria-labelledby="icon-states-title"
          >
            <h1 id="icon-states-title">
              Icon states
            </h1>
            <div class="citry-ui-quality-grid">
              <c-for each="name in names">
                <figure>
                  <c-CIcon c-name="name" size="lg" />
                  <figcaption>{{ name }}</figcaption>
                </figure>
              </c-for>
            </div>
            <p>
              <c-CIcon name="warn" />
              Decorative warning beside visible text
            </p>
            <p>
              Standalone meaning:
              <c-CIcon name="leaf" label="Healthy habitat" />
            </p>
            <div dir="rtl">
              <c-CIcon name="arrow-left" />
              <c-CIcon name="back" />
              <c-CIcon name="forward" />
              <c-CIcon name="next" />
            </div>
            <div style="color: rgb(21 128 61); --cui-icon-size: 2rem; --cui-icon-stroke-width: 1.5">
              <c-CIcon name="leaf" class_="quality-custom-icon" />
            </div>
          </section>
        """

        css = """
          :where(.citry-ui-quality-grid figure) {
            display: flex;
            gap: 0.5rem;
            align-items: center;
            margin: 0;
            min-width: 0;
          }

          :where(.citry-ui-quality-grid figcaption) {
            overflow-wrap: anywhere;
          }
        """

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
            return {"names": get_args(CIconName)}

    return CitryUiIconStates
