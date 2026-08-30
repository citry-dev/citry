from app.citry_app import citry_app
from app.data import Team
from citry import Component


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
