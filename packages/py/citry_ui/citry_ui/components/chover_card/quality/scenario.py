"""Shared HoverCard scenario used by repository quality tools."""

# ruff: noqa: E501

from __future__ import annotations

from citry import Citry, Component


def hover_card_states_component(app: Citry) -> type[Component]:
    class CitryUiHoverCardStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack" data-quality-hover-card-ready>
            <h1>HoverCard states</h1>
            <div style="display:flex;align-items:center;gap:3rem;min-block-size:16rem">
              <c-CHoverCard open>
                <c-fill name="activator" data="{ activator_attrs }"><a href="#ada" c-bind="activator_attrs">Ada profile</a></c-fill>
                <c-fill name="default"><strong>Ada Lovelace</strong><p>Supplementary profile preview.</p></c-fill>
              </c-CHoverCard>
              <c-CHoverCard size="sm" c-arrow="False">
                <c-fill name="activator" data="{ activator_attrs }"><a href="#grace" c-bind="activator_attrs">Grace profile</a></c-fill>
                <c-fill name="default">Small preview without arrow.</c-fill>
              </c-CHoverCard>
              <div dir="rtl"><c-CHoverCard placement="top-end" size="lg">
                <c-fill name="activator" data="{ activator_attrs }"><a href="#rtl" c-bind="activator_attrs">ملف تعريفي</a></c-fill>
                <c-fill name="default">معلومات إضافية غير أساسية.</c-fill>
              </c-CHoverCard></div>
            </div>
          </section>
        """

    return CitryUiHoverCardStates
