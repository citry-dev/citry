"""Shared Toggle scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def toggle_states_component(app: Citry) -> type[Component]:
    class CitryUiToggleStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack" data-quality-toggle-ready>
            <h1>Toggle states</h1>
            <c-CToggle c-pressed="True">Standalone pressed</c-CToggle>
            <c-CToggleGroup label="Single tools" value="one" c-mandatory="True">
              <c-CToggle value="one">One</c-CToggle>
              <c-CToggle value="two">Two</c-CToggle>
              <c-CToggle value="three" c-disabled="True">Three</c-CToggle>
            </c-CToggleGroup>
            <c-CToggleGroup label="Multiple layers" c-value="['stars', 'labels']" c-multiple="True" variant="soft">
              <c-CToggle value="stars">Stars</c-CToggle>
              <c-CToggle value="labels">Labels</c-CToggle>
              <c-CToggle value="grid">Grid</c-CToggle>
            </c-CToggleGroup>
            <c-CToggleGroup label="Vertical tools" orientation="vertical" value="north">
              <c-CToggle value="north">North</c-CToggle>
              <c-CToggle value="south">South</c-CToggle>
            </c-CToggleGroup>
            <div dir="rtl">
              <c-CToggleGroup label="RTL tools" value="start">
                <c-CToggle value="start">Start</c-CToggle>
                <c-CToggle value="end">End</c-CToggle>
              </c-CToggleGroup>
            </div>
          </section>
        """

    return CitryUiToggleStates
