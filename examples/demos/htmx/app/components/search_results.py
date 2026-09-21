from app.citry_app import citry_app
from citry import Component, Markup


class SearchResults(Component):
    citry = citry_app

    class Kwargs:
        rows_html: Markup
        count: int

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots):
        return {
            "rows_html": kwargs.rows_html,
            "count": kwargs.count,
            "summary": f"{kwargs.count} contact{'s' if kwargs.count != 1 else ''} found",
        }

    template = """
      <div class="contact-results" data-citry-activated="server">
        <p class="contact-results__summary" role="status">{{ summary }}</p>
        <c-if cond="count">
          <ul class="contact-results__list">{{ rows_html }}</ul>
        </c-if>
        <c-else>
          <p class="contact-results__empty">No contacts match that search.</p>
        </c-else>
      </div>
    """

    css = """
      .contact-results {
        overflow: hidden;
        border: 1px solid var(--color-border);
        border-left: 0.25rem solid var(--color-accent);
        border-radius: 0.6rem;
        background: var(--color-surface);
      }
      .contact-results__summary {
        margin: 0;
        padding: 0.65rem 0.85rem;
        color: var(--color-accent-ink);
        background: var(--color-accent-soft);
        font-size: 0.85rem;
        font-weight: 750;
      }
      .contact-results__list {
        display: grid;
        gap: 0;
        margin: 0;
        padding: 0;
        list-style: none;
      }
      .contact-results__list li {
        padding: 0.85rem;
        border-bottom: 1px solid var(--color-border);
      }
      .contact-results__list li:last-child {
        border-bottom: 0;
      }
      .contact-row-host {
        min-width: 0;
      }
      .contact-results__empty {
        margin: 0;
        padding: 1rem;
        color: var(--color-muted);
      }
    """
