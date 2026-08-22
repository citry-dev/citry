"""Shared Disclosure scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def disclosure_states_component(app: Citry) -> type[Component]:
    """Create the reusable Disclosure state and environment scenario."""

    class CitryUiDisclosureStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section
            class="citry-ui-quality-stack disclosure-quality"
            aria-labelledby="disclosure-states-title"
            x-data="{open:true}"
          >
            <h1 id="disclosure-states-title">Disclosure states</h1>

            <c-CDisclosure
              open
              region
              heading_level="2"
              actions_label="System requirement actions"
              $c-props="{open,onOpenChange:(next)=>open=next}"
              c-attrs="{'data-quality-states':'controlled open actions region outline md indicator-end ltr'}"
            >
              <c-fill name="title">System requirements</c-fill>
              <c-fill name="actions"><a href="#requirements">Copy link</a></c-fill>
              <c-fill name="default">Python 3.13 or newer and 512 MB of storage.</c-fill>
            </c-CDisclosure>

            <div class="citry-ui-quality-grid">
              <c-for each="variant in variants">
                <c-CDisclosure
                  c-variant="variant"
                  open
                  heading_level="2"
                  c-attrs="{'data-quality-states':variant}"
                >
                  <c-fill name="title">{{ variant }} treatment</c-fill>
                  <c-fill name="default">Representative expanded content.</c-fill>
                </c-CDisclosure>
              </c-for>
              <c-for each="size in sizes">
                <c-CDisclosure
                  c-size="size"
                  indicator_pos="start"
                  heading_level="2"
                  c-attrs="{'data-quality-states':size + ' indicator-start'}"
                >
                  <c-fill name="title">{{ size }} geometry</c-fill>
                  <c-fill name="default">Size-specific panel content.</c-fill>
                </c-CDisclosure>
              </c-for>
            </div>

            <c-CDisclosure
              disabled
              heading_level="2"
              c-indicator="False"
              c-attrs="{'data-quality-states':'disabled-closed closed indicator-hidden'}"
            >
              <c-fill name="title">Disabled closed guidance</c-fill>
              <c-fill name="default">Unavailable supporting content.</c-fill>
            </c-CDisclosure>
            <c-CDisclosure
              open
              disabled
              heading_level="2"
              c-attrs="{'data-quality-states':'disabled-open open'}"
            >
              <c-fill name="title">Disabled open guidance</c-fill>
              <c-fill name="default">Open state remains visible while unavailable.</c-fill>
            </c-CDisclosure>

            <div dir="rtl" class="disclosure-quality__narrow">
              <c-CDisclosure
                open
                variant="soft"
                heading_level="2"
                c-attrs="{'data-quality-states':'rtl long-content'}"
              >
                <c-fill name="title">requirementsrequirementsrequirementsrequirements</c-fill>
                <c-fill name="default">Long logical-layout stress content.</c-fill>
              </c-CDisclosure>
            </div>

            <div class="disclosure-quality__dark" style="color-scheme:dark">
              <c-CDisclosure open heading_level="2" c-attrs="{'data-quality-states':'nested nested-dark'}">
                <c-fill name="title">Nested handbook topic</c-fill>
                <c-fill name="default">
                  <c-CDisclosure variant="plain" size="sm">
                    <c-fill name="title">Nested detail</c-fill>
                    <c-fill name="default">Independent nested content.</c-fill>
                  </c-CDisclosure>
                  <c-CAccordion value="check" variant="plain" size="sm">
                    <c-CAccordionItem value="check">
                      <c-fill name="title">Grouped check</c-fill>
                      <c-fill name="default">Accordion remains the collection owner.</c-fill>
                    </c-CAccordionItem>
                  </c-CAccordion>
                </c-fill>
              </c-CDisclosure>
            </div>

            <form class="disclosure-quality__orchard" id="disclosure-quality-form">
              <c-CDisclosure
                open
                variant="soft"
                heading_level="2"
                c-attrs="{'data-quality-states':'form-content brand-orchard'}"
              >
                <c-fill name="title">Notification settings</c-fill>
                <c-fill name="default"><label>Email <input name="email" value="ops@example.com" /></label></c-fill>
              </c-CDisclosure>
            </form>

            <div class="disclosure-quality__harbor">
              <c-CDisclosure
                open
                indicator_pos="start"
                heading_level="2"
                c-attrs="{'data-quality-states':'brand-harbor'}"
              >
                <c-fill name="title">Harbor handbook</c-fill>
                <c-fill name="default">Scheme-aware brand adaptation.</c-fill>
              </c-CDisclosure>
            </div>
          </section>
        """

        def template_data(
            self,
            kwargs: Kwargs,  # noqa: ARG002
            slots: Slots,  # noqa: ARG002
        ) -> dict[str, object]:
            return {"variants": ("outline", "soft", "plain"), "sizes": ("sm", "md", "lg")}

        css = """
          :where(.disclosure-quality__narrow) { inline-size: 10rem; }
          :where(.disclosure-quality__dark) {
            padding: 1rem;
            background: #101d2a;
            color: #edf7ff;
          }
          :where(.disclosure-quality__orchard) {
            --cui-disclosure-background: light-dark(#fff7ed, #2b170b);
            --cui-disclosure-foreground: light-dark(#431407, #ffedd5);
            --cui-disclosure-trigger-open-color: light-dark(#9a3412, #fdba74);
          }
          :where(.disclosure-quality__harbor) {
            --cui-disclosure-background: light-dark(#ecfeff, #082f49);
            --cui-disclosure-foreground: light-dark(#164e63, #cffafe);
            --cui-disclosure-trigger-open-color: light-dark(#0369a1, #7dd3fc);
          }
        """

    return CitryUiDisclosureStates
