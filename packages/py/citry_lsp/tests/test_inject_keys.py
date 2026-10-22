"""
Tests for the editor's check of ``self.inject("key")`` keys against the keys provided above a component.

When the app loads, the app worker works out which keys reach each component
class. The editor compares the ``self.inject()`` calls in the file being
edited with those keys and reports a key nothing provides, as ``citry check``
does.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from citry_lsp.engine import DocumentState, browser_diagnostics
from citry_lsp.project import _inject_keys, load_project

if TYPE_CHECKING:
    from pathlib import Path

_APP = '''from citry import Citry, Component, LintSettings

engine = Citry(autodiscover=False{engine_options})


class Card(Component):
    citry = engine

    def template_data(self, kwargs, slots):
        board = self.inject("{key}")
        return {{"name": board.name}}

    template = """
      <p>{{{{ name }}}}</p>
    """


class Board(Component):
    citry = engine
    template = """
      <c-provide key="board" name="Projects">
        <c-card />
      </c-provide>
    """
'''

_CODE = "citry.template.unknown-inject-key"


def _findings(
    tmp_path: Path,
    key: str,
    *,
    engine_options: str = "",
    edited_key: str | None = None,
) -> list[tuple[str, str, int]]:
    source = _APP.format(key=key, engine_options=engine_options)
    app_file = tmp_path / "app.py"
    app_file.write_text(source, encoding="utf8")
    project = load_project(tmp_path, "app:engine")
    assert project.status.registry_ready, project.status.message
    text = source if edited_key is None else source.replace(f'self.inject("{key}")', f'self.inject("{edited_key}")')
    document = DocumentState(app_file.as_uri(), "python", text, 1)
    document.update(text, 1, project)
    found = []
    for diagnostic in browser_diagnostics(document, project, {document.uri: document}):
        if diagnostic.code == _CODE:
            line = text.splitlines()[diagnostic.range.start.line]
            covered = line[diagnostic.range.start.character : diagnostic.range.end.character]
            found.append((covered, diagnostic.message, int(diagnostic.severity or 0)))
    return found


def test_the_editor_reports_the_benchmark_misspelled_key(tmp_path):
    assert _findings(tmp_path, "bord") == [
        (
            '"bord"',
            "No component above Card provides 'bord', so self.inject('bord') raises KeyError when Card renders. "
            "Did you mean 'board'?",
            2,
        )
    ]


def test_an_inject_call_typed_after_the_app_loaded_is_checked_at_once(tmp_path):
    # The worker sent the keys that reach Card; the call itself comes from the edited text.
    assert [item[0] for item in _findings(tmp_path, "board", edited_key="bord")] == ['"bord"']
    assert _findings(tmp_path, "bord", edited_key="board") == []


def test_the_editor_follows_the_inject_key_setting(tmp_path):
    ignore = ', lint=LintSettings(rule_unknown_inject_key="ignore")'
    error = ', lint=LintSettings(rule_unknown_inject_key="error")'

    assert _findings(tmp_path, "bord", engine_options=ignore) == []
    assert [item[2] for item in _findings(tmp_path, "bord", engine_options=error)] == [1]


def test_the_worker_record_is_read_and_checked():
    record = {
        "file": "/app.py",
        "qualname": "Card",
        "name": "Card",
        "provided": ["board"],
        "everywhere": False,
        "definition_ids": ["d1"],
    }

    classes = _inject_keys({"checked": True, "classes": [record]})
    assert classes is not None
    assert classes[0].provided == frozenset({"board"})
    assert _inject_keys(None) is None
    assert _inject_keys({"checked": False, "classes": []}) is None


@pytest.mark.parametrize(
    "value",
    [
        {"checked": True},
        {"checked": "yes", "classes": []},
        {"checked": True, "classes": [{"file": "/app.py"}]},
        {
            "checked": True,
            "classes": [
                {
                    "file": "/app.py",
                    "qualname": "Card",
                    "name": "Card",
                    "provided": "board",
                    "everywhere": False,
                    "definition_ids": [],
                }
            ],
        },
    ],
)
def test_a_malformed_worker_record_is_rejected(value):
    with pytest.raises(ValueError, match="inject key"):
        _inject_keys(value)
