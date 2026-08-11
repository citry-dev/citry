"""Shared Tag scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def tag_states_component(app: Citry) -> type[Component]:
    class CitryUiTagStates(Component):
        citry = app
        css = """
          :where(.quality-tag-fern) {
            --cui-tag-selected-background: light-dark(#176b4d, #48c79b);
            --cui-tag-selected-foreground: light-dark(#ffffff, #102a20);
          }
          :where(.quality-tag-river) {
            --cui-tag-selected-background: light-dark(#175cd3, #8bb8ff);
            --cui-tag-selected-foreground: light-dark(#ffffff, #10233e);
            --cui-tag-radius: 0.45rem;
          }
        """
        template = """
          <section class="citry-ui-quality-stack" data-quality-tag-ready>
            <h1>Tag states</h1>
            <c-CTagGroup label="Descriptive topics" c-attrs="{'data-quality-state': 'descriptive'}">
              <c-CTag value="css">CSS</c-CTag>
              <c-CTag value="html">HTML</c-CTag>
              <c-CTag value="very-long">A very long unbrokenish-topic-label-that-must-wrap</c-CTag>
            </c-CTagGroup>
            <c-CTagGroup
              label="Selectable amenities"
              selection_mode="multiple"
              c-value="['wifi', 'pool']"
              removable
              actionable
              c-attrs="{'data-quality-state': 'interactive'}"
            >
              <c-CTag value="wifi">Wi-Fi</c-CTag>
              <c-CTag value="parking">Parking</c-CTag>
              <c-CTag value="pool">Pool</c-CTag>
              <c-CTag value="closed" c-disabled="True">Closed</c-CTag>
            </c-CTagGroup>
            <div class="citry-ui-quality-grid" data-quality-state="variants">
              <c-CTagGroup label="Soft" variant="soft" selection_mode="single" value="one">
                <c-CTag value="one">One</c-CTag><c-CTag value="two">Two</c-CTag>
              </c-CTagGroup>
              <c-CTagGroup label="Solid" variant="solid" size="sm">
                <c-CTag value="one">Small</c-CTag>
              </c-CTagGroup>
              <c-CTagGroup label="Outline" variant="outline" size="lg">
                <c-CTag value="one">Large</c-CTag>
              </c-CTagGroup>
            </div>
            <div dir="rtl" data-quality-state="rtl">
              <c-CTagGroup label="RTL topics" selection_mode="single" value="end">
                <c-CTag value="start">Start</c-CTag><c-CTag value="end">End</c-CTag>
              </c-CTagGroup>
            </div>
            <div style="color-scheme: dark" data-quality-state="nested-dark">
              <c-CTagGroup label="Dark topics" selection_mode="single" value="moon">
                <c-CTag value="moon">Moon</c-CTag><c-CTag value="stars">Stars</c-CTag>
              </c-CTagGroup>
            </div>
            <c-CTagGroup
              label="Fern brand"
              class_="quality-tag-fern"
              selection_mode="single"
              value="fern"
              c-attrs="{'data-quality-state': 'brand-fern'}"
            ><c-CTag value="fern">Fern</c-CTag><c-CTag value="moss">Moss</c-CTag></c-CTagGroup>
            <c-CTagGroup
              label="River brand"
              class_="quality-tag-river"
              selection_mode="single"
              value="river"
              c-attrs="{'data-quality-state': 'brand-river'}"
            ><c-CTag value="river">River</c-CTag><c-CTag value="lake">Lake</c-CTag></c-CTagGroup>
          </section>
        """

    return CitryUiTagStates
