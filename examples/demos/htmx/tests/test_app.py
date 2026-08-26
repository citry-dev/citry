from app.data import get_contact
from app.main import web_app
from fastapi.testclient import TestClient


def test_page_serves_local_htmx_and_citry_scripts() -> None:
    with TestClient(web_app) as client:
        page = client.get("/")
        stylesheet = client.get("/static/demo.css")
        brand_mark = client.get("/static/citry-mark.svg")
        htmx = client.get("/static/htmx.min.js")
        adapter = client.get("/static/citry-htmx.js")
        citry = client.get("/citry/citry.js")

    assert page.status_code == 200
    assert page.headers["content-type"].startswith("text/html")
    assert "HTMX + Citry patterns" in page.text
    assert "Already using HTMX? You can keep it." in page.text
    assert 'class="citry-brand__mark"' in page.text
    assert "HTMX demo" in page.text
    assert 'hx-get="/fragments/search"' in page.text
    assert 'hx-ext="citry-fragments"' in page.text
    assert 'class="contact-row-host"' in page.text
    assert 'id="contact-row-1"' in page.text
    assert 'hx-target="closest .contact-row-host"' in page.text
    assert 'id="contact-editor"' not in page.text
    assert 'id="search-results" class="fragment-host"' in page.text
    assert 'class="contact-results__summary" role="status"' in page.text
    assert "data-citry-graph" in page.text
    assert "data-citry" in page.text
    assert stylesheet.status_code == 200
    assert "color-scheme: light" in stylesheet.text
    assert "prefers-color-scheme: dark" not in stylesheet.text
    assert brand_mark.status_code == 200
    assert brand_mark.headers["content-type"].startswith("image/svg+xml")
    assert htmx.status_code == 200
    assert "2.0.10" in htmx.text
    assert adapter.status_code == 200
    assert 'htmx.defineExtension("citry-fragments"' in adapter.text
    assert "[0-9a-f]{8}" in adapter.text
    assert "data-citry-htmx-cap" in adapter.text
    assert 'Set hx-swap="innerHTML" on a wrapper that remains on the page' in adapter.text
    assert "encodeURIComponent" not in adapter.text
    assert citry.status_code == 200
    assert citry.headers["content-type"].startswith("text/javascript")


def test_search_response_includes_component_html_and_dependencies() -> None:
    with TestClient(web_app) as client:
        response = client.get("/fragments/search", params={"q": "grace"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Grace Hopper" in response.text
    assert "Ada Lovelace" not in response.text
    assert 'class="contact-results__summary" role="status"' in response.text
    assert "<!--citry:g1:" in response.text
    assert "data-citry-graph" in response.text
    assert "data-citry" in response.text


def test_team_picker_returns_teams_for_the_selected_department() -> None:
    with TestClient(web_app) as client:
        engineering = client.get("/fragments/team-picker", params={"department": "engineering"})
        design = client.get("/fragments/team-picker", params={"department": "design"})
        operations = client.get("/fragments/team-picker", params={"department": "operations"})
        unknown = client.get("/fragments/team-picker", params={"department": "missing"})

    assert engineering.status_code == 200
    assert "Platform" in engineering.text
    assert "Developer Experience" in engineering.text
    assert "Infrastructure" in engineering.text
    assert "Security" in engineering.text
    assert "4 teams available" in engineering.text
    assert design.status_code == 200
    assert "Product Design" in design.text
    assert "Research" in design.text
    assert "Platform" not in design.text
    assert "2 teams available" in design.text
    assert operations.status_code == 200
    assert "Customer Operations" in operations.text
    assert "Platform" not in operations.text
    assert "1 team available" in operations.text
    assert unknown.status_code == 200
    assert "No teams available" in unknown.text
    assert "disabled" in unknown.text


def test_contact_form_shows_errors_and_saves_valid_changes() -> None:
    with TestClient(web_app) as client:
        edit = client.get("/fragments/contacts/1/edit")
        cancel = client.get("/fragments/contacts/1")
        invalid = client.post(
            "/fragments/contacts/1",
            data={"name": "A", "email": "broken", "team_id": "missing"},
        )
        saved = client.post(
            "/fragments/contacts/1",
            data={"name": "Ada Byron", "email": "ada.byron@example.test", "team_id": "4"},
        )

    assert edit.status_code == 200
    assert "Edit Ada Lovelace" in edit.text
    assert "autofocus" in edit.text
    assert 'hx-post="/fragments/contacts/1"' in edit.text
    assert 'hx-target="closest .contact-row-host"' in edit.text
    assert 'hx-disabled-elt="find button[type=&#39;submit&#39;]"' in edit.text
    assert 'hx-disabled-elt="this"' in edit.text
    assert cancel.status_code == 200
    assert "Ada Lovelace" in cancel.text
    assert 'hx-target="closest .contact-row-host"' in cancel.text
    assert invalid.status_code == 200
    assert "Enter a name between 2 and 80 characters." in invalid.text
    assert "Enter a valid email address." in invalid.text
    assert "Choose an available team." in invalid.text
    assert saved.status_code == 200
    assert "Saved Ada Byron." in saved.text
    assert 'hx-target="closest .contact-row-host"' in saved.text
    assert get_contact(1).name == "Ada Byron"
    assert get_contact(1).team_name == "Research"


def test_contact_form_rejects_a_long_name_and_invalid_email() -> None:
    with TestClient(web_app) as client:
        response = client.post(
            "/fragments/contacts/1",
            data={"name": "x" * 81, "email": "unsafe@example", "team_id": "1"},
        )

    assert response.status_code == 200
    assert "Enter a name between 2 and 80 characters." in response.text
    assert "Enter a valid email address." in response.text
    assert get_contact(1).name == "Ada Lovelace"


def test_unknown_contact_returns_not_found() -> None:
    with TestClient(web_app) as client:
        assert client.get("/fragments/contacts/999").status_code == 404
        assert client.get("/fragments/contacts/999/edit").status_code == 404
        assert client.post("/fragments/contacts/999", data={}).status_code == 404
