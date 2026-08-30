from __future__ import annotations

import time
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, ValidationError

from app.components.contact_detail import ContactDetail
from app.components.contact_form import ContactForm
from app.components.search_results import SearchResults
from app.components.team_picker import TeamPicker
from app.data import DEPARTMENTS, get_contact, list_teams, search_contacts, update_contact

if TYPE_CHECKING:
    from collections.abc import Mapping

    from app.data import ContactView
    from citry import CitryElement

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

router = APIRouter()


class ContactUpdate(BaseModel):
    """Values accepted when someone saves a contact."""

    name: str = Field(min_length=2, max_length=80)
    email: str = Field(max_length=254, pattern=EMAIL_PATTERN)
    team_id: int


def _fragment(component: CitryElement) -> str:
    return component.render().serialize(deps_strategy="fragment")


def _fragment_response(component: CitryElement) -> HTMLResponse:
    return HTMLResponse(_fragment(component))


def _contact_or_404(contact_id: int) -> ContactView:
    try:
        return get_contact(contact_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Contact not found") from error


def _form_text(form: Mapping[str, object], name: str) -> str:
    value = form.get(name)
    return value if isinstance(value, str) else ""


def _page_html() -> str:
    search_results = _fragment(SearchResults(contacts=search_contacts(), query=""))
    team_picker = _fragment(TeamPicker(department="engineering", teams=list_teams("engineering")))
    department_options = "".join(f'<option value="{value}">{label}</option>' for value, label in DEPARTMENTS)
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>HTMX + Citry patterns</title>
    <link rel="stylesheet" href="/static/demo.css" />
    <script src="/static/htmx.min.js"></script>
    <script src="/static/citry-htmx.js"></script>
    <script src="/citry/citry.js"></script>
  </head>
  <body hx-ext="citry-fragments">
    <a class="skip-link" href="#demo-content">Skip to the demo</a>
    <header class="site-header">
      <div class="site-header__inner">
        <a class="citry-brand" href="https://citry.dev/" aria-label="Citry website">
          <span class="citry-brand__mark" aria-hidden="true"></span>
          <span class="citry-brand__name">Citry</span>
        </a>
        <span class="demo-badge">HTMX demo</span>
      </div>
    </header>
    <main id="demo-content">
      <section class="page-intro" aria-labelledby="page-title">
        <div class="page-intro__inner">
          <p class="page-context">FastAPI integration</p>
          <h1 id="page-title">HTMX + Citry patterns</h1>
          <p>
            Already using HTMX? You can keep it. This demo uses Citry to render
            the HTML, CSS, and JavaScript that FastAPI routes return.
          </p>
        </div>
      </section>

      <div class="demo-layout">
        <section class="demo-panel" aria-labelledby="search-title">
          <div class="demo-panel__intro">
            <h2 id="search-title">Find a contact</h2>
            <p>
              HTMX refreshes the list as you type. Choose Edit to replace that
              contact's row with the form.
            </p>
          </div>
          <label class="field-label" for="contact-search">Search by name, email, or team</label>
          <div class="search-row">
            <input
              id="contact-search"
              type="search"
              name="q"
              autocomplete="off"
              placeholder="Try Grace or Platform"
              hx-get="/fragments/search"
              hx-trigger="input changed delay:300ms"
              hx-target="#search-results"
              hx-swap="innerHTML"
              hx-sync="this:replace"
              hx-indicator="#search-indicator"
            />
            <span id="search-indicator" class="htmx-indicator" role="status">Searching…</span>
          </div>
          <p class="demo-hint">
            Type <code>Ada</code> to simulate a response that takes about 750 ms.
            Then type <code>Grace</code> to see <code>hx-sync="this:replace"</code>
            cancel the slower request.
          </p>
          <div id="search-results" class="fragment-host">{search_results}</div>
        </section>

        <div class="demo-secondary">
          <section class="demo-panel" aria-labelledby="cascade-title">
            <div class="demo-panel__intro">
              <h2 id="cascade-title">Choose a team</h2>
              <p>Choose a department and HTMX refreshes the list of teams.</p>
            </div>
            <div class="picker-grid">
              <div>
                <label class="field-label" for="department-choice">Department</label>
                <select
                  id="department-choice"
                  name="department"
                  style="margin-bottom: 24px;"
                  hx-get="/fragments/team-picker"
                  hx-trigger="change"
                  hx-target="#team-picker"
                  hx-swap="innerHTML"
                  hx-sync="this:replace"
                >
                  {department_options}
                </select>
              </div>
              <div id="team-picker" class="fragment-host">{team_picker}</div>
            </div>
          </section>

          <aside class="greenfield-note">
            <strong>Starting a new Citry application?</strong>
            Try Citry Events first. This demo is for existing HTMX applications
            and teams adding Citry one component at a time.
          </aside>
        </div>
      </div>
    </main>
  </body>
</html>"""


@router.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    return HTMLResponse(_page_html())


@router.get("/fragments/search", response_class=HTMLResponse)
def search(q: str = "") -> HTMLResponse:
    # Keep one search slow so the demo can show HTMX canceling an older request.
    if q.strip().casefold() == "ada":
        time.sleep(0.75)
    return _fragment_response(SearchResults(contacts=search_contacts(q), query=q.strip()))


@router.get("/fragments/team-picker", response_class=HTMLResponse)
def teams(department: str = "") -> HTMLResponse:
    return _fragment_response(TeamPicker(department=department, teams=list_teams(department)))


@router.get("/fragments/contacts/{contact_id}", response_class=HTMLResponse)
def contact_detail(contact_id: int) -> HTMLResponse:
    return _fragment_response(ContactDetail(contact=_contact_or_404(contact_id)))


@router.get("/fragments/contacts/{contact_id}/edit", response_class=HTMLResponse)
def edit_contact(contact_id: int) -> HTMLResponse:
    contact = _contact_or_404(contact_id)
    return _fragment_response(
        ContactForm(
            contact_id=contact.id,
            name=contact.name,
            email=contact.email,
            selected_team_id=contact.team_id,
            teams=list_teams(),
        )
    )


@router.post("/fragments/contacts/{contact_id}", response_class=HTMLResponse)
async def save_contact(contact_id: int, request: Request) -> HTMLResponse:
    _contact_or_404(contact_id)
    # This local demo has no user accounts or cookies. In a real application,
    # check authorization and CSRF protection before changing the contact.
    form = await request.form()
    name = _form_text(form, "name").strip()
    email = _form_text(form, "email").strip()
    team_value = _form_text(form, "team_id").strip()

    try:
        update = ContactUpdate.model_validate({"name": name, "email": email, "team_id": team_value})
        invalid_fields: set[str] = set()
    except ValidationError as error:
        update = None
        invalid_fields = {str(item["loc"][0]) for item in error.errors()}

    name_error = "Enter a name between 2 and 80 characters." if "name" in invalid_fields else ""
    email_error = "Enter a valid email address." if "email" in invalid_fields else ""
    try:
        selected_team_id = int(team_value)
    except ValueError:
        selected_team_id = None
    valid_team = selected_team_id is not None and any(team.id == selected_team_id for team in list_teams())
    team_error = "Choose an available team." if not valid_team else ""

    if name_error or email_error or team_error:
        return _fragment_response(
            ContactForm(
                contact_id=contact_id,
                name=name,
                email=email,
                selected_team_id=selected_team_id,
                teams=list_teams(),
                name_error=name_error,
                email_error=email_error,
                team_error=team_error,
            )
        )

    if update is None:  # pragma: no cover - errors above cover every model field
        raise RuntimeError("Contact validation succeeded without returning a ContactUpdate.")
    updated = update_contact(contact_id, name=update.name, email=update.email, team_id=update.team_id)
    return _fragment_response(ContactDetail(contact=updated, notice=f"Saved {updated.name}."))
