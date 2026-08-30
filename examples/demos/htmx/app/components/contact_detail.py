from app.citry_app import citry_app
from app.data import ContactView
from citry import Component


class ContactDetail(Component):
    citry = citry_app

    class Kwargs:
        contact: ContactView
        notice: str = ""

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots):
        return {
            "contact": kwargs.contact,
            "edit_url": kwargs.contact.edit_url,
            "notice": kwargs.notice,
        }

    def js_data(self, kwargs: Kwargs, slots: Slots):
        return {"contactId": kwargs.contact.id}

    template = """
      <article class="contact-detail">
        <c-if cond="notice">
          <p class="contact-detail__notice" role="status">{{ notice }}</p>
        </c-if>
        <div class="contact-detail__identity">
          <h3>{{ contact.name }}</h3>
          <span>{{ contact.email }} · {{ contact.team_name }}</span>
        </div>
        <button
          type="button"
          class="secondary-button"
          c-hx-get="edit_url"
          hx-target="closest .contact-row-host"
          hx-swap="innerHTML"
        >
          Edit {{ contact.name }}
        </button>
      </article>
    """

    js = """
      $component(({ els, data }) => {
        if (els[0]) {
          els[0].dataset.citryContact = String(data.contactId);
        }
      });
    """

    css = """
      .contact-detail {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: center;
        gap: 0.45rem 1rem;
      }
      .contact-detail h3,
      .contact-detail p {
        margin: 0;
      }
      .contact-detail__identity {
        display: grid;
        gap: 0.18rem;
        min-width: 0;
      }
      .contact-detail__identity span {
        color: var(--color-muted);
        font-size: 0.8rem;
        overflow-wrap: anywhere;
      }
      .contact-detail button {
        grid-column: 2;
        padding: 0.45rem 0.7rem;
      }
      .contact-detail__notice {
        grid-column: 1 / -1;
        padding: 0.6rem 0.75rem;
        border-radius: 0.5rem;
        color: var(--color-success-ink);
        background: var(--color-success-soft);
      }
      @media (max-width: 42rem) {
        .contact-detail {
          grid-template-columns: 1fr;
        }
        .contact-detail button {
          grid-column: 1;
          justify-self: stretch;
        }
      }
    """
