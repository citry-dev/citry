import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BadgeIntents(Component):
    template = """
      <c-CGroup class_="badge-intents">
        <c-CBadge intent="neutral">Unsorted</c-CBadge>
        <c-CBadge intent="primary">In study</c-CBadge>
        <c-CBadge intent="success">Verified</c-CBadge>
        <c-CBadge intent="warn">Handle carefully</c-CBadge>
        <c-CBadge intent="danger">Restricted</c-CBadge>
      </c-CGroup>
    """
    css = """
      :where(.badge-intents) {
        max-inline-size: 34rem;
        padding: 1rem;
        border-radius: 0.75rem;
        background: light-dark(#f5f1e8, #25221e);
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = BadgeIntents()

preview  # noqa: B018
