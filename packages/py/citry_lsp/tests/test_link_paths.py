"""
Tests for the editor's check of literal link paths against the app's routes and static files.

When the app loads, the app worker asks each registered path checker about
every link path in the templates. The editor then reports the paths the
framework does not serve, as ``citry check`` does. Without a registered checker the editor reports no link at all.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from citry_lsp.engine import DocumentState, browser_diagnostics
from citry_lsp.project import load_project

if TYPE_CHECKING:
    from pathlib import Path

_APP = '''from citry import Citry, Component, LintSettings
from citry._path_checks import PathLookup, register_path_checker

engine = Citry(autodiscover=False{engine_options})
SERVED = ("/about", "/static/avatar.svg")

{register}


class Page(Component):
    citry = engine
    template = """
      <nav>
        {markup}
      </nav>
    """
'''

# A host app that serves two paths, registered as an integration's mount() would.
_REGISTER = "register_path_checker(engine, lambda path: PathLookup(path in SERVED, SERVED))"

_URL = "citry.template.unknown-url"


def _findings(
    tmp_path: Path,
    markup: str,
    *,
    register: str = _REGISTER,
    engine_options: str = "",
    edited_markup: str | None = None,
) -> list[tuple[str, str, str, int]]:
    source = _APP.format(markup=markup, register=register, engine_options=engine_options)
    app_file = tmp_path / "app.py"
    app_file.write_text(source, encoding="utf8")
    project = load_project(tmp_path, "app:engine")
    assert project.status.registry_ready, project.status.message
    text = source if edited_markup is None else source.replace(markup, edited_markup)
    document = DocumentState(app_file.as_uri(), "python", text, 1)
    document.update(text, 1, project)
    found = []
    for diagnostic in browser_diagnostics(document, project, {document.uri: document}):
        if diagnostic.code == _URL:
            line = text.splitlines()[diagnostic.range.start.line]
            covered = line[diagnostic.range.start.character : diagnostic.range.end.character]
            found.append((str(diagnostic.code), covered, diagnostic.message, int(diagnostic.severity or 0)))
    return found


def test_the_editor_reports_a_link_the_app_does_not_serve(tmp_path):
    markup = '<a href="/abuot">About</a> <a href="/about#team">Team</a> <img src="/static/avtar.svg" alt="">'

    assert _findings(tmp_path, markup) == [
        (
            _URL,
            "/abuot",
            "Your app has no route or static file for '/abuot', so the browser gets a 404 Not Found. "
            "Did you mean '/about'?",
            2,
        ),
        (
            _URL,
            "/static/avtar.svg",
            "Your app has no route or static file for '/static/avtar.svg', so the browser gets a 404 Not Found. "
            "Did you mean '/static/avatar.svg'?",
            2,
        ),
    ]


def test_the_editor_checks_no_links_without_a_registered_checker(tmp_path):
    assert _findings(tmp_path, '<a href="/abuot">About</a>', register="") == []


def test_a_link_added_after_the_app_loaded_waits_for_the_next_load(tmp_path):
    # The worker answered only for the paths the templates held when it ran.
    edited = '<a href="/about">About</a> <a href="/contcat">Contact</a>'

    assert _findings(tmp_path, '<a href="/about">About</a>', edited_markup=edited) == []


def test_the_editor_follows_the_link_rule_setting(tmp_path):
    markup = '<a href="/abuot">About</a>'

    assert _findings(tmp_path, markup, engine_options=', lint=LintSettings(rule_unknown_url="ignore")') == []
    assert [
        item[3] for item in _findings(tmp_path, markup, engine_options=', lint=LintSettings(rule_unknown_url="error")')
    ] == [1]
