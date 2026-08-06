"""Shared Tabs scenario used by docs and Phase 7.5 quality tools."""

from __future__ import annotations

from citry import Citry, Component


def tabs_overview_component(app: Citry) -> type[Component]:
    """Create the reusable Tabs overview component for one Citry instance."""

    class CitryUiTabsDemo(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section
            class="citry-ui-tabs-demo"
            x-data="{ selected: 'account' }"
          >
            <p>
              Browser selection:
              <output id="tabs-overview-selection" x-text="selected">account</output>
            </p>
            <c-CTabs
              default_value="account"
              aria_label="Account settings"
              variant="pill"
              grow
              $c-props="{
                onValueChange: (value) => {
                  selected = value;
                },
              }"
            >
              <c-CTab value="account">
                Account
              </c-CTab>
              <c-CTab value="notifications">
                Notifications
              </c-CTab>
              <c-CTab value="billing" disabled>
                Billing
              </c-CTab>
              <c-CTabPanel value="account">
                Update your profile and sign-in preferences.
                <c-CTabs
                  default_value="profile"
                  aria_label="Account detail views"
                  density="compact"
                >
                  <c-CTab value="profile">
                    Profile
                  </c-CTab>
                  <c-CTab value="access">
                    Access
                  </c-CTab>
                  <c-CTabPanel value="profile">
                    Public account details.
                  </c-CTabPanel>
                  <c-CTabPanel value="access">
                    Sign-in and recovery settings.
                  </c-CTabPanel>
                </c-CTabs>
              </c-CTabPanel>
              <c-CTabPanel value="notifications">
                Choose which product and security messages you receive.
              </c-CTabPanel>
              <c-CTabPanel value="billing">
                Billing is unavailable for this account.
              </c-CTabPanel>
            </c-CTabs>
            <div x-data="{ selectedMetric: 'delivery' }">
              <p>
                Controlled metric:
                <output id="tabs-manual-selection" x-text="selectedMetric">delivery</output>
              </p>
              <c-CTabs
                default_value="delivery"
                aria_label="Manual metrics views"
                orientation="vertical"
                activation="manual"
                direction="rtl"
                c-loop="False"
                density="compact"
                align="end"
                $c-props="{
                  value: selectedMetric,
                  onValueChange: (value) => {
                    selectedMetric = value;
                  },
                }"
              >
                <c-CTab value="delivery">
                  Delivery performance over the last quarter
                </c-CTab>
                <c-CTab value="quality">
                  Quality and reliability
                </c-CTab>
                <c-CTabPanel value="delivery">
                  Delivery metrics.
                </c-CTabPanel>
                <c-CTabPanel value="quality">
                  Quality metrics.
                </c-CTabPanel>
              </c-CTabs>
            </div>
          </section>
        """

        css = """
          :where(.citry-ui-tabs-demo) {
            max-width: 42rem;
            color: CanvasText;
            font-family: ui-sans-serif, system-ui, sans-serif;
          }

          :where(.citry-ui-tabs-demo > p) {
            color: color-mix(in srgb, currentColor 72%, transparent);
          }

          :where(.citry-ui-tabs-demo output) {
            color: var(--cui-tabs-accent, LinkText);
            font-weight: 700;
          }
        """

    return CitryUiTabsDemo
