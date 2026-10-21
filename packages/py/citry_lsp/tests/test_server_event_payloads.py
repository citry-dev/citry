"""
Tests for the editor's checks of what a template sends to a server event.

With the application loaded, the editor reads each handler's description
from the app worker and reports the same `@c-*` argument and form-field
mistakes as ``citry check``. It stays silent when the description cannot
prove what the server accepts, or when the handler or its data class has
unsaved edits the loaded app has not seen.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from citry_lsp.engine import DocumentState, browser_diagnostics
from citry_lsp.project import load_project

if TYPE_CHECKING:
    from pathlib import Path

_APP = '''from citry import Citry, Component, LintSettings

engine = Citry(autodiscover=False{engine_options})


class SaveIn:
    amount: int


class SearchIn:
    q: str


class Counter(Component):
    citry = engine

    class Events:
        def save(self, data: SaveIn):
            return None

        def search(self, data: SearchIn):
            return None

    template = """
      <section>
        {markup}
      </section>
    """
'''

_PAYLOAD_CODES = {
    "citry.browser.unknown-server-event-field",
    "citry.browser.missing-server-event-field",
    "citry.browser.incompatible-server-event-field",
    "citry.browser.unknown-form-field",
    "citry.browser.missing-form-field",
}


def _app(tmp_path: Path, markup: str, *, engine_options: str = "") -> tuple[Path, str]:
    source = _APP.format(markup=markup, engine_options=engine_options)
    app_file = tmp_path / "app.py"
    app_file.write_text(source, encoding="utf8")
    return app_file, source


def _findings(tmp_path: Path, app_file: Path, source: str, *, edited: str | None = None) -> list[tuple[str, str, str]]:
    project = load_project(tmp_path, "app:engine")
    assert project.status.registry_ready, project.status.message
    text = source if edited is None else edited
    document = DocumentState(app_file.as_uri(), "python", text, 1)
    document.update(text, 1, project)
    found = []
    for diagnostic in browser_diagnostics(document, project, {document.uri: document}):
        if diagnostic.code in _PAYLOAD_CODES:
            line = text.splitlines()[diagnostic.range.start.line]
            covered = line[diagnostic.range.start.character : diagnostic.range.end.character]
            found.append((str(diagnostic.code), covered, diagnostic.message))
    return found


def test_the_editor_reports_the_payload_mistakes_citry_check_reports(tmp_path):
    markup = """<button @c-click="save({amont: 1})">a</button>
        <button @c-click="save({amount: '1'})">b</button>
        <button @c-click="save()">c</button>"""
    app_file, source = _app(tmp_path, markup)

    assert _findings(tmp_path, app_file, source) == [
        (
            "citry.browser.missing-server-event-field",
            "save",
            "Server event 'save' requires field 'amount', which this call does not send, so the server rejects it.",
        ),
        (
            "citry.browser.unknown-server-event-field",
            "amont",
            "Server event 'save' has no field 'amont', so the server rejects this call. Did you mean 'amount'?",
        ),
        (
            "citry.browser.incompatible-server-event-field",
            "'1'",
            "Server event 'save' rejects this value for field 'amount': Expected int, got str.",
        ),
        (
            "citry.browser.missing-server-event-field",
            "save",
            "Server event 'save' requires field 'amount', which this call does not send, so the server rejects it.",
        ),
    ]


def test_the_editor_reports_a_misspelled_form_field(tmp_path):
    markup = """<form @c-submit.prevent="search">
          <input name="qeury" />
          <input type="hidden" name="csrfmiddlewaretoken" />
        </form>"""
    app_file, source = _app(tmp_path, markup)

    assert [(code, covered) for code, covered, _message in _findings(tmp_path, app_file, source)] == [
        ("citry.browser.missing-form-field", "search"),
        ("citry.browser.unknown-form-field", "qeury"),
    ]


def test_the_editor_follows_the_csrf_field_names_setting(tmp_path):
    markup = """<form @c-submit.prevent="search">
          <input name="q" />
          <input type="hidden" name="authenticity_token" />
        </form>"""
    app_file, source = _app(
        tmp_path,
        markup,
        engine_options=', extensions_defaults={"events": {"_csrf_field_names": ["authenticity_token"]}}',
    )

    assert _findings(tmp_path, app_file, source) == []


def test_the_editor_follows_the_rule_settings(tmp_path):
    app_file, source = _app(
        tmp_path,
        '<form @c-submit.prevent="search"><input name="qeury" /></form>',
        engine_options=', lint=LintSettings(rule_unknown_form_field="ignore")',
    )

    assert [code for code, _covered, _message in _findings(tmp_path, app_file, source)] == [
        "citry.browser.missing-form-field"
    ]


def test_an_unsaved_edit_to_the_data_class_turns_the_rules_off_until_the_app_reloads(tmp_path):
    app_file, source = _app(tmp_path, '<button @c-click="save({amont: 1})">a</button>')
    # The author is adding the field the template already sends.
    edited = source.replace("    amount: int\n", "    amount: int\n    amont: int = 0\n")

    assert _findings(tmp_path, app_file, source, edited=edited) == []


def test_an_unsaved_edit_to_the_template_alone_keeps_the_rules_on(tmp_path):
    app_file, source = _app(tmp_path, '<button @c-click="save({amount: 1})">a</button>')
    edited = source.replace("save({amount: 1})", "save({amont: 1})")

    assert [code for code, _covered, _message in _findings(tmp_path, app_file, source, edited=edited)] == [
        "citry.browser.missing-server-event-field",
        "citry.browser.unknown-server-event-field",
    ]


def test_a_pydantic_data_class_is_not_checked_in_the_editor(tmp_path):
    pytest.importorskip("pydantic")
    app_file, source = _app(tmp_path, '<button @c-click="save({amont: 1})">a</button>')
    source = source.replace(
        "class SaveIn:\n", "from pydantic import BaseModel, ConfigDict\n\n\nclass SaveIn(BaseModel):\n"
    )
    source = source.replace("    amount: int\n", '    model_config = ConfigDict(extra="forbid")\n    amount: int\n')
    app_file.write_text(source, encoding="utf8")

    assert _findings(tmp_path, app_file, source) == []
