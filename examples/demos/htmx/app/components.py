from citry import Component

from .citry_app import citry_app
from .data import ContactView, Team


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


class ContactForm(Component):
    citry = citry_app

    class Kwargs:
        contact_id: int
        name: str
        email: str
        selected_team_id: int | None
        teams: tuple[Team, ...]
        name_error: str = ""
        email_error: str = ""
        team_error: str = ""

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots):
        return {
            "save_url": f"/fragments/contacts/{kwargs.contact_id}",
            "cancel_url": f"/fragments/contacts/{kwargs.contact_id}",
            "name": kwargs.name,
            "email": kwargs.email,
            "selected_team_id": kwargs.selected_team_id,
            "teams": kwargs.teams,
            "name_error": kwargs.name_error,
            "email_error": kwargs.email_error,
            "team_error": kwargs.team_error,
            "name_invalid": "true" if kwargs.name_error else "false",
            "email_invalid": "true" if kwargs.email_error else "false",
            "team_invalid": "true" if kwargs.team_error else "false",
            "name_error_id": f"contact-{kwargs.contact_id}-name-error",
            "email_error_id": f"contact-{kwargs.contact_id}-email-error",
            "team_error_id": f"contact-{kwargs.contact_id}-team-error",
        }

    template = """
      <form
        class="contact-form"
        novalidate
        c-hx-post="save_url"
        hx-target="closest .contact-row-host"
        hx-swap="innerHTML"
        hx-sync="this:replace"
        hx-disabled-elt="find button[type='submit']"
      >
        <h3>Edit {{ name }}</h3>
        <label>
          <span>Name</span>
          <input
            name="name"
            c-value="name"
            c-aria-invalid="name_invalid"
            c-aria-describedby="name_error_id"
            autocomplete="name"
            autofocus
          />
          <span c-id="name_error_id" class="field-error" role="alert">{{ name_error }}</span>
        </label>
        <label>
          <span>Email</span>
          <input
            name="email"
            type="email"
            c-value="email"
            c-aria-invalid="email_invalid"
            c-aria-describedby="email_error_id"
            autocomplete="email"
          />
          <span c-id="email_error_id" class="field-error" role="alert">{{ email_error }}</span>
        </label>
        <label>
          <span>Team</span>
          <select
            name="team_id"
            c-aria-invalid="team_invalid"
            c-aria-describedby="team_error_id"
          >
            <c-for each="team in teams">
              <option c-value="team.id" c-selected="team.id == selected_team_id">{{ team.name }}</option>
            </c-for>
          </select>
          <span c-id="team_error_id" class="field-error" role="alert">{{ team_error }}</span>
        </label>
        <div class="contact-form__actions">
          <button type="submit">Save contact</button>
          <button
            type="button"
            class="secondary-button"
            c-hx-get="cancel_url"
            hx-target="closest .contact-row-host"
            hx-swap="innerHTML"
            hx-disabled-elt="this"
          >
            Cancel
          </button>
          <span class="htmx-indicator" role="status">Saving…</span>
        </div>
      </form>
    """

    js = """
      $component(({ els }) => {
        els[0]?.querySelector("input[name='name']")?.focus();
      });
    """

    css = """
      .contact-form {
        display: grid;
        gap: 0.8rem;
        width: 100%;
      }
      .contact-form h3,
      .contact-form p {
        margin: 0;
      }
      .contact-form label {
        display: grid;
        gap: 0.28rem;
        color: var(--color-text);
        font-size: 0.82rem;
        font-weight: 700;
      }
      .contact-form input,
      .contact-form select {
        min-height: 2.6rem;
        min-width: 0;
        width: 100%;
        padding: 0.55rem 0.65rem;
        border: 1px solid var(--color-input-border);
        border-radius: 0.45rem;
        color: var(--color-text);
        background: var(--color-input);
      }
      .contact-form [aria-invalid="true"] {
        border-color: var(--color-danger);
      }
      .contact-form__actions {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 0.6rem;
      }
      .field-error {
        min-height: 1rem;
        color: var(--color-danger);
        font-size: 0.75rem;
        font-weight: 600;
      }
    """


class TeamPicker(Component):
    citry = citry_app

    class Kwargs:
        department: str
        teams: tuple[Team, ...]

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots):
        count = len(kwargs.teams)
        return {
            "teams": kwargs.teams,
            "has_teams": bool(kwargs.teams),
            "summary": f"{count} team{'s' if count != 1 else ''} available",
        }

    template = """
      <div class="team-picker-fragment">
        <label for="team-choice">Team</label>
        <select id="team-choice" name="team" c-disabled="not has_teams">
          <c-if cond="has_teams">
            <c-for each="team in teams">
              <option c-value="team.id">{{ team.name }}</option>
            </c-for>
          </c-if>
          <c-else>
            <option value="">No teams available</option>
          </c-else>
        </select>
        <small role="status">{{ summary }}</small>
      </div>
    """

    css = """
      .team-picker-fragment {
        display: grid;
        gap: 0.3rem;
      }
      .team-picker-fragment label {
        color: var(--color-text);
        font-size: 0.82rem;
        font-weight: 650;
      }
      .team-picker-fragment select {
        min-height: 2.55rem;
        padding: 0.45rem 0.65rem;
        border: 1px solid var(--color-input-border);
        border-radius: 0.375rem;
        color: var(--color-text);
        background: var(--color-input);
      }
      .team-picker-fragment small {
        color: var(--color-muted);
      }
    """
