"""Check Rusty backend use, canonical behavior and byte-exact DTL parity."""

# Configure Django by importing the application before constructing templates.

import unittest

import app
from django.template.backends.django import DjangoTemplates
from django.template.loader import get_template
from django.test import Client
from django_rusty_templates import Template as RustyTemplate

SCENARIO = app.SCENARIO
ORIGINAL_APP = app.HERE.parent / "django_htmx_alpine"
ACTION_NAMES = (
    "select",
    "filter",
    "clear-filter",
    "invalid-save",
    "save",
    "insert",
    "reorder",
    "remove",
    "probe",
)


def action_input(name: str) -> app.ActionInput:
    values = {
        "select": {"action": "select", "row_id": "1"},
        "filter": {"action": "filter", "query": "Lorem ipsum 12"},
        "clear-filter": {"action": "filter", "query": ""},
        "invalid-save": {"action": "save", "title": ""},
        "save": {"action": "save", "title": "Reviewed project"},
        "insert": {"action": "insert"},
        "reorder": {"action": "reorder"},
        "remove": {"action": "remove"},
        "probe": {"action": "probe"},
    }
    value = {"operation": f"parity-{name}", **values[name]}
    return app.ActionInput(**value)


class ApplicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = Client(enforce_csrf_checks=True)

    def test_configured_backend_is_rusty_and_renders_initial_and_fragment(self) -> None:
        assert app.settings.TEMPLATES[0]["BACKEND"] == "django_rusty_templates.RustyTemplates"
        template = get_template("board.html")
        assert isinstance(template, RustyTemplate)
        initial = self.client.get("/?count=14&session=lifecycle")
        assert initial.status_code == 200
        assert b"No project tags" in initial.content
        updated = self.client.post(
            "/action",
            {
                "session": "lifecycle",
                "action": "select",
                "operation": "test-select",
                "row_id": "1",
                "csrfmiddlewaretoken": self.client.cookies["csrftoken"].value,
            },
        )
        assert updated.status_code == 200
        assert updated["X-Bench-Operation"] == "test-select"
        assert b'data-revision="1"' in updated.content
        assert b'data-selected="true"' in updated.content

    def test_missing_csrf_and_invalid_protocol_fail_without_mutation(self) -> None:
        self.client.get("/?count=14&session=protected")
        values = {"session": "protected", "action": "insert", "operation": "forbidden"}
        assert self.client.post("/action", values).status_code == 403
        values["csrfmiddlewaretoken"] = self.client.cookies["csrftoken"].value
        response = self.client.post("/action", {**values, "action": "unknown"})
        assert response.status_code == 400
        assert app.snapshot("protected")["revision"] == 0

    def test_all_fixture_sizes_render(self) -> None:
        for count in (14, 140, 1400):
            with self.subTest(count=count):
                response = self.client.get(f"/?count={count}&session=size-{count}")
                assert response.status_code == 200
                assert response.content.count(b'data-row-id="') == count

    def test_strict_parity_with_original_django_template_at_all_states(self) -> None:
        django_backend = DjangoTemplates(
            {
                "NAME": "django",
                "DIRS": [str(ORIGINAL_APP)],
                "APP_DIRS": False,
                "OPTIONS": {"autoescape": True},
            }
        )
        django_template = django_backend.get_template("board.html")
        rusty_template = get_template("board.html")
        assert isinstance(rusty_template, RustyTemplate)
        for count in (14, 140, 1400):
            with self.subTest(count=count):
                session = f"parity-{count}"
                app.reset(session, count)
                csrf = "parity-csrf"
                for state in range(len(ACTION_NAMES) + 1):
                    with self.subTest(state=state):
                        expected = django_template.render(app.view_data(session, csrf))
                        actual = rusty_template.render(app.view_data(session, csrf))
                        assert actual == expected
                    if state < len(ACTION_NAMES):
                        data = action_input(ACTION_NAMES[state])
                        app.apply(session, data)


if __name__ == "__main__":
    unittest.main()
