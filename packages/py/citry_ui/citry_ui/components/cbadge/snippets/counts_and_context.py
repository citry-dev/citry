import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BadgeCountsAndContext(Component):
    template = """
      <nav class="badge-counts" aria-label="Mineral archive queues">
        <a href="#unfiled" aria-label="Unfiled specimens, 12 items">
          <span>Unfiled specimens</span><c-CBadge shape="pill">12</c-CBadge>
        </a>
        <a href="#review" aria-label="Awaiting review, 4 items">
          <span>Awaiting review</span><c-CBadge shape="pill" intent="warn">4</c-CBadge>
        </a>
      </nav>
    """
    css = """
      :where(.badge-counts) {
        display: grid;
        gap: 0.375rem;
        max-inline-size: 22rem;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.badge-counts a) {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        padding: 0.75rem;
        border-radius: 0.6rem;
        color: CanvasText;
        text-decoration: none;
      }

      :where(.badge-counts a:hover) {
        background: light-dark(#ece6da, #322d27);
      }
    """


preview = BadgeCountsAndContext()

preview  # noqa: B018
