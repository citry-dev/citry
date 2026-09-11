"""State bindings report unsupported controls at their authored attribute keys."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest
from lsprotocol import types

from citry_lsp.engine import DocumentState, browser_diagnostics
from citry_lsp.project import ProjectState
from citry_lsp.protocol import ProjectStatus

if TYPE_CHECKING:
    from pathlib import Path

_CODE = "citry.browser.invalid-state-binding-target"


def _position(source: str, offset: int) -> types.Position:
    lines = re.split(r"\r\n|\r|\n", source[:offset])
    return types.Position(len(lines) - 1, len(lines[-1].encode("utf-16-le")) // 2)


def _project(tmp_path: Path) -> ProjectState:
    return ProjectState(ProjectStatus(interpreter="python", workspace=str(tmp_path), mode="syntax-only"))


def _document(source: str, project: ProjectState, *, language: str = "citry-html") -> DocumentState:
    suffix = "py" if language == "python" else "citry-html"
    document = DocumentState(f"file:///state-binding-targets.{suffix}", language, source, 1)
    document.update(source, 1, project)
    assert document.parsed
    assert not document.diagnostics
    return document


@pytest.mark.parametrize(
    "source",
    [
        '<head :c-query="refresh"></head>',
        '<div :c-query="refresh"></div>',
        '<span :c-query="refresh"></span>',
        '<button :c-query="refresh"></button>',
        '<c-Card :c-query="refresh" />',
        '<input type="hidden" :c-query="refresh" />',
        '<input type="file" :c-query="refresh" />',
        '<input type="submit" :c-query="refresh" />',
        '<input type="image" :c-query="refresh" />',
        '<input type="reset" :c-query="refresh" />',
        '<input type="button" :c-query="refresh" />',
        '<input type="unknown" :c-query="refresh" />',
        '<input type=" text " :c-query="refresh" />',
        '<c-element is="head" :c-query="refresh" />',
    ],
)
def test_invalid_state_binding_targets_report_without_an_app(source: str, tmp_path: Path) -> None:
    """The element itself proves these failures without a component registry."""
    project = _project(tmp_path)
    document = _document(source, project)

    findings = browser_diagnostics(document, project)

    assert len(findings) == 1
    finding = findings[0]
    start = source.index(":c-query")
    assert finding.code == _CODE
    assert finding.severity == types.DiagnosticSeverity.Error
    assert finding.source == "citry"
    assert finding.range == types.Range(_position(source, start), _position(source, start + len(":c-query")))
    assert finding.code_description is not None


@pytest.mark.parametrize("tag", ["head", "div", "span", "c-Card"])
def test_one_way_bindings_also_need_a_value_control(tag: str, tmp_path: Path) -> None:
    """One-way state still needs an element that can receive its value."""
    project = _project(tmp_path)
    document = _document(f"<{tag} :c-query />", project)

    assert [finding.code for finding in browser_diagnostics(document, project)] == [_CODE]


@pytest.mark.parametrize(
    "source",
    [
        '<input :c-query="refresh" />',
        '<input type="TEXT" :c-query="refresh" />',
        '<input type="checkbox" :c-query="refresh" />',
        '<input type="radio" :c-query="refresh" />',
        '<textarea :c-query="refresh"></textarea>',
        '<select :c-query="refresh"></select>',
        '<my-picker :c-query.on:change="refresh"></my-picker>',
        '<input type="hidden" :c-query />',
        '<c-element is="input" :c-query="refresh" />',
        '<c-element c-is="tag" :c-query="refresh" />',
        '<c-element c-bind="attrs" :c-query="refresh" />',
        '<input c-type="control_type" :c-query="refresh" />',
        '<input :type="controlType" :c-query="refresh" />',
        '<input c-bind="attrs" :c-query="refresh" />',
        '<input type="file" c-bind="attrs" :c-query="refresh" />',
        '<head @c-click="refresh"></head>',
    ],
)
def test_supported_or_dynamic_state_binding_targets_are_not_rejected(source: str, tmp_path: Path) -> None:
    """Supported controls pass, and dynamic selections wait for runtime values."""
    project = _project(tmp_path)
    document = _document(source, project)

    assert browser_diagnostics(document, project) == ()


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_inline_binding_error_maps_unicode_and_the_complete_modifier_key(newline: str, tmp_path: Path) -> None:
    """The diagnostic covers the binding key after decoding an indented Python literal."""
    marker = ":c-query.debounce.300ms"
    source = newline.join(
        [
            "from citry import Component",
            "",
            "class Example(Component):",
            '    template = """',
            "      <!-- précédé 😀 -->",
            f'      <head title="😀" {marker}="refresh"></head>',
            '    """',
            "",
        ],
    )
    project = _project(tmp_path)
    document = _document(source, project, language="python")

    findings = browser_diagnostics(document, project)

    assert len(findings) == 1
    start = source.index(marker)
    assert findings[0].code == _CODE
    assert findings[0].range == types.Range(_position(source, start), _position(source, start + len(marker)))


def test_nested_template_binding_error_uses_the_inner_authored_key(tmp_path: Path) -> None:
    """Nested template offsets must not point into the outer component attribute."""
    source = "<c-card c-body=\"<>😀<head :c-query.on:change='refresh'></head></>\" />"
    project = _project(tmp_path)
    document = _document(source, project)

    findings = browser_diagnostics(document, project)

    assert len(findings) == 1
    marker = ":c-query.on:change"
    start = source.index(marker)
    assert findings[0].code == _CODE
    assert findings[0].range == types.Range(_position(source, start), _position(source, start + len(marker)))


def test_fixing_a_state_binding_target_clears_its_diagnostic(tmp_path: Path) -> None:
    """Editing a current document replaces findings from its previous version."""
    project = _project(tmp_path)
    document = _document('<head :c-query="refresh"></head>', project)
    assert [finding.code for finding in browser_diagnostics(document, project)] == [_CODE]

    document.update('<input :c-query="refresh" />', 2, project)

    assert browser_diagnostics(document, project) == ()
