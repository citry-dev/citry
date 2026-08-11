"""Shared Accordion scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def accordion_states_component(app: Citry) -> type[Component]:
    """Create the reusable Accordion state and environment scenario."""

    class CitryUiAccordionStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section
            class="citry-ui-quality-stack accordion-quality"
            aria-labelledby="accordion-states-title"
            x-data
            x-init="Alpine.store('accordionQuality', {
              value: 'canopy',
              variant: 'outline',
              size: 'md',
            })"
          >
            <h1 id="accordion-states-title">Accordion states</h1>
            <c-CAccordion
              value="canopy"
              region
              c-attrs="{
                'data-quality-states':
                  'controlled single collapsible open closed disabled-item '
                  'actions region outline md indicator-end ltr',
              }"
              $c-props="{
                value: $store.accordionQuality.value,
                variant: $store.accordionQuality.variant,
                size: $store.accordionQuality.size,
                onValueChange: (value) => $store.accordionQuality.value = value,
              }"
            >
              <c-CAccordionItem value="canopy">
                <c-fill name="title">Canopy</c-fill>
                <c-fill name="default">The upper crowns collect most sunlight.</c-fill>
              </c-CAccordionItem>
              <c-CAccordionItem value="understory" actions_label="Understory actions">
                <c-fill name="title">Understory</c-fill>
                <c-fill name="actions">
                  <a href="#understory-map">Map</a>
                </c-fill>
                <c-fill name="default">Ferns and saplings grow in filtered light.</c-fill>
              </c-CAccordionItem>
              <c-CAccordionItem value="closed-trail" disabled>
                <c-fill name="title">Closed trail</c-fill>
                <c-fill name="default">High water has covered the footbridge.</c-fill>
              </c-CAccordionItem>
            </c-CAccordion>

            <div class="citry-ui-quality-grid">
              <c-for each="variant in variants">
                <c-CAccordion
                  c-variant="variant"
                  value="one"
                  size="sm"
                  c-attrs="{'data-quality-states': variant}"
                >
                  <c-CAccordionItem value="one">
                    <c-fill name="title">{{ variant }} treatment</c-fill>
                    <c-fill name="default">Representative panel content.</c-fill>
                  </c-CAccordionItem>
                </c-CAccordion>
              </c-for>
              <c-for each="size in sizes">
                <c-CAccordion
                  c-size="size"
                  value="one"
                  variant="soft"
                  c-attrs="{'data-quality-states': size}"
                >
                  <c-CAccordionItem value="one">
                    <c-fill name="title">{{ size }} geometry</c-fill>
                    <c-fill name="default">Size-specific panel content.</c-fill>
                  </c-CAccordionItem>
                </c-CAccordion>
              </c-for>
            </div>

            <div dir="rtl" class="accordion-quality__narrow">
              <c-CAccordion
                value="one"
                indicator_pos="start"
                c-attrs="{
                  'data-quality-states': 'indicator-start rtl long-content',
                }"
              >
                <c-CAccordionItem value="one">
                  <c-fill name="title">
                    forestforestforestforestforestforestforestforest
                  </c-fill>
                  <c-fill name="default">
                    Long right-to-left environment stress content.
                  </c-fill>
                </c-CAccordionItem>
              </c-CAccordion>
            </div>

            <div class="accordion-quality__dark" style="color-scheme: dark">
              <c-CAccordion
                value="outer"
                variant="separated"
                c-attrs="{'data-quality-states': 'nested nested-dark'}"
              >
                <c-CAccordionItem value="outer">
                  <c-fill name="title">Nested group</c-fill>
                  <c-fill name="default">
                    <c-CAccordion value="inner" variant="plain" size="sm">
                      <c-CAccordionItem value="inner">
                        <c-fill name="title">Inner section</c-fill>
                        <c-fill name="default">Nested panel content.</c-fill>
                      </c-CAccordionItem>
                    </c-CAccordion>
                  </c-fill>
                </c-CAccordionItem>
              </c-CAccordion>
            </div>

            <div class="accordion-quality__fern">
              <form id="accordion-quality-form">
                <c-CAccordion
                  multiple
                  c-value="['wetland']"
                  variant="soft"
                  c-attrs="{
                    'data-quality-states': 'multiple form-content brand-fern',
                  }"
                >
                  <c-CAccordionItem value="wetland">
                    <c-fill name="title">Wetland notes</c-fill>
                    <c-fill name="default">Waterlogged soil observations.</c-fill>
                  </c-CAccordionItem>
                  <c-CAccordionItem value="upland">
                    <c-fill name="title">Upland notes</c-fill>
                    <c-fill name="default">
                      <label>
                        Ridge note
                        <input name="ridge-note" value="Dry trail" />
                      </label>
                    </c-fill>
                  </c-CAccordionItem>
                </c-CAccordion>
              </form>
            </div>

            <div class="accordion-quality__river">
              <c-CAccordion
                value="current"
                c-collapsible="False"
                size="lg"
                c-attrs="{
                  'data-quality-states': 'noncollapsible brand-river',
                }"
              >
                <c-CAccordionItem value="current">
                  <c-fill name="title">River current</c-fill>
                  <c-fill name="default">A fixed-open reference section.</c-fill>
                </c-CAccordionItem>
              </c-CAccordion>
            </div>
          </section>
        """

        def template_data(
            self,
            kwargs: Kwargs,  # noqa: ARG002
            slots: Slots,  # noqa: ARG002
        ) -> dict[str, object]:
            return {
                "variants": ("outline", "soft", "separated", "plain"),
                "sizes": ("sm", "md", "lg"),
            }

        css = """
          :where(.accordion-quality__narrow) {
            inline-size: 10rem;
          }

          :where(.accordion-quality__dark) {
            --cui-accordion-trigger-open-color: #8fe0aa;

            padding: 1rem;
            background: #122019;
            color: #effaf3;
          }

          :where(.accordion-quality__fern) {
            --cui-accordion-background: light-dark(#eef8ec, #14291a);
            --cui-accordion-foreground: light-dark(#17351c, #e6f5e8);
            --cui-accordion-trigger-open-color: light-dark(#245b2a, #8ee69a);
          }

          :where(.accordion-quality__river) {
            --cui-accordion-background: light-dark(#e9f5fb, #102a38);
            --cui-accordion-foreground: light-dark(#123446, #e3f3fb);
            --cui-accordion-trigger-open-color: light-dark(#075985, #7dd3fc);
          }
        """

    return CitryUiAccordionStates
