"""Contract tests for the published LSP4IJ template and spike fixture."""

from __future__ import annotations

import json
from pathlib import Path

from citry_lsp.engine import DocumentState
from citry_lsp.project import load_project

_REPO_ROOT = Path(__file__).resolve().parents[4]
_JETBRAINS_ROOT = _REPO_ROOT / "packages" / "editors" / "jetbrains"
_TEMPLATE_ROOT = _JETBRAINS_ROOT / "lsp4ij" / "citry"
_FIXTURE_ROOT = _JETBRAINS_ROOT / "spike_fixture"
_FIXTURE_APP = "packages.editors.jetbrains.spike_fixture.app:app"


def test_lsp4ij_template_preserves_the_citry_client_contract():
    template = json.loads((_TEMPLATE_ROOT / "template.json").read_text())
    initialization = json.loads((_TEMPLATE_ROOT / "initializationOptions.json").read_text())

    assert template["id"] == "citry-language-server"
    assert template["workingDir"] == "$PROJECT_DIR$"
    assert template["programArgs"] == {
        "windows": "$PROJECT_DIR$/.venv/Scripts/citry-lsp.exe",
        "default": "$PROJECT_DIR$/.venv/bin/citry-lsp",
    }
    assert template["languageMappings"] == [{"language": "Python", "languageId": "python"}]
    assert template["fileTypeMappings"] == [{"fileType": {"patterns": ["*.citry-html"]}, "languageId": "citry-html"}]
    assert initialization == {
        "protocolVersion": 1,
        "app": "app:app",
        "standardFormatting": True,
    }


def test_jetbrains_spike_fixture_loads_and_parses_both_document_shapes():
    project = load_project(_REPO_ROOT, _FIXTURE_APP)

    assert project.status.registry_ready is True
    assert project.catalog is not None
    registered = {name for component in project.catalog.components for name in component.registered_names}
    assert {"external-card", "frame", "inline-card"} <= registered

    documents = (
        (_FIXTURE_ROOT / "app.py", "python"),
        (_FIXTURE_ROOT / "external_card.citry-html", "citry-html"),
    )
    for path, language_id in documents:
        source = path.read_text()
        document = DocumentState(path.as_uri(), language_id, source, 1)
        document.update(source, 1, project)
        assert document.regions
        assert document.diagnostics == ()
