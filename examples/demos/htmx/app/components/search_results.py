from app.citry_app import citry_app
from app.data import ContactView
from citry import Component


class SearchResults(Component):
    citry = citry_app

    class Kwargs:
        contacts: tuple[ContactView, ...]
        query: str = ""

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots):
        count = len(kwargs.contacts)
        return {
            "contacts": kwargs.contacts,
            "summary": f"{count} contact{'s' if count != 1 else ''} found",
        }

    def js_data(self, kwargs: Kwargs, slots: Slots):
        return {"query": kwargs.query}

    template = """
      <div class="contact-results">
        <p class="contact-results__summary" role="status">{{ summary }}</p>
        <c-if cond="contacts">
          <ul class="contact-results__list">
            <c-for each="contact in contacts">
              <li>
                <div class="contact-row-host" c-id="f'contact-row-{contact.id}'">
                  <c-ContactDetail c-contact="contact" />
                </div>
              </li>
            </c-for>
          </ul>
        </c-if>
        <c-else>
          <p class="contact-results__empty">No contacts match that search.</p>
        </c-else>
      </div>
    """

    js = """
      $component(({ els, data }) => {
        if (els[0]) {
          els[0].dataset.citryActivated = data.query || "all";
        }
      });
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
