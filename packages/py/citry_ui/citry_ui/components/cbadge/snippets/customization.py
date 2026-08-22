import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BadgeCustomization(Component):
    template = """
      <c-CRow class_="badge-themes">
        <div class="badge-themes__quartz">
          <c-CBadge>Quartz archive</c-CBadge>
        </div>
        <div class="badge-themes__basalt">
          <c-CBadge variant="outline">Basalt archive</c-CBadge>
        </div>
      </c-CRow>
    """
    css = """
      :where(.badge-themes > div) {
        padding: 1.25rem;
        border-radius: 0.75rem;
      }

      :where(.badge-themes__quartz) {
        --cui-badge-background: #f0e7ff;
        --cui-badge-foreground: #4c1d75;
        --cui-badge-radius: 0.2rem;
        background: #faf7ff;
      }

      :where(.badge-themes__basalt) {
        color-scheme: dark;
        --cui-badge-background: #1e2930;
        --cui-badge-foreground: #d7edf2;
        --cui-badge-border-color: #72a8b5;
        --cui-badge-radius: 999px;
        background: #10171b;
      }
    """


preview = BadgeCustomization()

preview  # noqa: B018
