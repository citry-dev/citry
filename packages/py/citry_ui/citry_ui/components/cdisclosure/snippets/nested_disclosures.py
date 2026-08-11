import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NestedDisclosures(Component):
    template = """
      <section class="nested-disclosure-demo" dir="rtl">
        <c-CDisclosure open>
          <c-fill name="title">Network setup</c-fill>
          <c-fill name="default">
            <c-CStack gap="md">
              <p>Configure the application endpoint before optional proxy rules.</p>
              <c-CDisclosure variant="soft" size="sm">
                <c-fill name="title">Proxy settings</c-fill>
                <c-fill name="default">Use HTTPS_PROXY for outbound requests.</c-fill>
              </c-CDisclosure>
              <c-CAccordion value="timeouts" variant="plain" size="sm">
                <c-CAccordionItem value="timeouts">
                  <c-fill name="title">Timeout troubleshooting</c-fill>
                  <c-fill name="default">Check firewall and DNS resolution first.</c-fill>
                </c-CAccordionItem>
              </c-CAccordion>
            </c-CStack>
          </c-fill>
        </c-CDisclosure>
      </section>
    """

    css = """
      :where(.nested-disclosure-demo) { inline-size: min(100%, 20rem); }
      :where(.nested-disclosure-demo p) { overflow-wrap: anywhere; }
    """


preview = NestedDisclosures()
preview  # noqa: B018
