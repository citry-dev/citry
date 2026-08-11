"""End-to-end tests for type-aware template expression features."""

from __future__ import annotations

import ast
import sys
from dataclasses import replace
from typing import TYPE_CHECKING, cast

import pytest
from lsprotocol import types

from citry_lsp.engine import DocumentState, expression_shadows, template_variable_hover
from citry_lsp.project import load_project
from citry_lsp.semantic import (
    semantic_completions,
    semantic_definition,
    semantic_diagnostics,
    semantic_hover,
    semantic_signature_help,
    semantic_type_definition,
    semantic_variable_hover,
)
from citry_lsp.type_analysis import TyAnalyzer, TyDiagnostic, TyDocument, position_at_offset

if TYPE_CHECKING:
    from pathlib import Path


class _PartialTypeAnalyzer:
    """Return one target and then prove that another shadow has no answer."""

    def __init__(self, location: types.Location) -> None:
        self.location = location
        self.calls = 0

    async def type_definition(self, *_args: object, **_kwargs: object) -> tuple[types.Location, ...]:
        self.calls += 1
        return (self.location,) if self.calls == 1 else ()


class _CountingDiagnosticsAnalyzer:
    """Return one finding per marked expression while recording request count."""

    def __init__(self) -> None:
        self.calls = 0

    async def diagnostics(
        self,
        document: TyDocument,
        *,
        synchronized: tuple[TyDocument, ...] = (),
    ) -> tuple[TyDiagnostic, ...]:
        del synchronized
        self.calls += 1
        ast.parse(document.source)
        findings: list[TyDiagnostic] = []
        for marker in ("title.missing", "title.other_missing"):
            start = document.source.find(marker)
            if start < 0:
                continue
            findings.append(
                TyDiagnostic(
                    types.Range(
                        position_at_offset(document.source, start),
                        position_at_offset(document.source, start + len(marker)),
                    ),
                    f"Unknown attribute in {marker}",
                    types.DiagnosticSeverity.Error,
                    "unresolved-attribute",
                    "ty",
                    None,
                )
            )
        return tuple(findings)


def _position(source: str, marker: str, offset: int = 0) -> types.Position:
    index = source.index(marker) + offset
    before = source[:index]
    return types.Position(before.count("\n"), len(before.rsplit("\n", 1)[-1].encode("utf-16-le")) // 2)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "template_source",
    [
        '<div c-if="method is not None" c-title="method.lo"></div>',
        '<c-if cond="method is None">none</c-if><div c-else c-title="method.lo"></div>',
    ],
)
async def test_declared_schema_completion_uses_template_narrowing(
    tmp_path: Path,
    template_source: str,
) -> None:
    template_file = tmp_path / "card.html"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class TemplateData:\n"
        "        method: str | None\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    documents = {document.uri: document}
    analyzer = TyAnalyzer(tmp_path)
    try:
        items = await semantic_completions(
            analyzer,
            document,
            _position(template_source, "method.lo", len("method.lo")),
            project,
            documents,
        )
    finally:
        await analyzer.close()

    by_label = {item.label: item for item in items}
    assert "lower" in by_label
    assert by_label["lower"].detail == "bound method str.lower() -> str"
    assert isinstance(by_label["lower"].text_edit, types.InsertReplaceEdit)
    assert by_label["lower"].text_edit.new_text == "lower"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("marker", "member"),
    [
        ("site_name.lo", "lower"),
        ("request.up", "upper"),
    ],
)
async def test_global_and_lint_metadata_types_power_member_completion(
    tmp_path: Path,
    marker: str,
    member: str,
) -> None:
    template_file = tmp_path / "card.html"
    template_source = "{{ site_name.lo }} {{ request.up }}"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component, LintSettings\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False, "
        "template_globals={'site_name': 'Citry'}, "
        "lint=LintSettings(template_variables={'request': str}))\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    documents = {document.uri: document}
    analyzer = TyAnalyzer(tmp_path)
    try:
        items = await semantic_completions(
            analyzer,
            document,
            _position(template_source, marker, len(marker)),
            project,
            documents,
        )
    finally:
        await analyzer.close()

    assert member in {item.label for item in items}


@pytest.mark.asyncio
async def test_lint_metadata_resolves_a_qualified_forward_type(tmp_path: Path) -> None:
    template_file = tmp_path / "card.html"
    template_source = "{{ request.acc }}"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "framework.py").write_text(
        "class Request:\n    def accepted(self) -> bool:\n        return True\n",
        encoding="utf-8",
    )
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component, LintSettings\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False, "
        "lint=LintSettings(template_variables={'request': 'framework.Request'}))\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    analyzer = TyAnalyzer(tmp_path)
    try:
        items = await semantic_completions(
            analyzer,
            document,
            _position(template_source, "request.acc", len("request.acc")),
            project,
            {document.uri: document},
        )
    finally:
        await analyzer.close()

    assert "accepted" in {item.label for item in items}


@pytest.mark.asyncio
async def test_declared_variable_hover_uses_python_style_and_template_narrowing(tmp_path: Path) -> None:
    template_file = tmp_path / "card.html"
    template_source = '{{ method }}<div c-if="method is not None">{{ method }}</div>'
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class TemplateData:\n"
        "        method: str | None\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    documents = {document.uri: document}
    outside = _position(template_source, "{{ method", len("{{ met"))
    narrowed = _position(template_source, 'None">{{ method', len('None">{{ met'))
    outside_variable = template_variable_hover(document, outside, project, documents)
    narrowed_variable = template_variable_hover(document, narrowed, project, documents)
    assert outside_variable is not None
    assert narrowed_variable is not None

    analyzer = TyAnalyzer(tmp_path)
    try:
        outside_hint = await semantic_variable_hover(
            analyzer,
            document,
            outside,
            project,
            documents,
            outside_variable,
        )
        narrowed_hint = await semantic_variable_hover(
            analyzer,
            document,
            narrowed,
            project,
            documents,
            narrowed_variable,
        )
    finally:
        await analyzer.close()

    assert outside_hint.contents.value == (
        "```python\n(variable) method: str | None\n```\n\nTemplateData field · required"
    )
    assert narrowed_hint.contents.value == ("```python\n(variable) method: str\n```\n\nTemplateData field · required")


@pytest.mark.asyncio
async def test_inferred_and_loop_variable_hover_use_analyzer_types(tmp_path: Path) -> None:
    template_file = tmp_path / "card.html"
    template_source = '<c-for each="ch in title">{{ ch }}</c-for>{{ title }} {{ action }}'
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class Kwargs:\n"
        "        action: str | None\n"
        "    def template_data(self, kwargs):\n"
        "        return {'title': 'Hello', 'action': kwargs.action}\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    documents = {document.uri: document}
    loop_declaration_position = _position(template_source, 'each="ch', len('each="c'))
    loop_position = _position(template_source, "{{ ch", len("{{ c"))
    root_position = _position(template_source, "</c-for>{{ title", len("</c-for>{{ tit"))
    optional_position = _position(template_source, "{{ action", len("{{ act"))
    loop_declaration_variable = template_variable_hover(
        document,
        loop_declaration_position,
        project,
        documents,
    )
    loop_variable = template_variable_hover(document, loop_position, project, documents)
    root_variable = template_variable_hover(document, root_position, project, documents)
    optional_variable = template_variable_hover(document, optional_position, project, documents)
    assert loop_declaration_variable is not None
    assert loop_variable is not None
    assert root_variable is not None
    assert optional_variable is not None

    analyzer = TyAnalyzer(tmp_path)
    try:
        loop_declaration_hint = await semantic_variable_hover(
            analyzer,
            document,
            loop_declaration_position,
            project,
            documents,
            loop_declaration_variable,
        )
        loop_hint = await semantic_variable_hover(
            analyzer,
            document,
            loop_position,
            project,
            documents,
            loop_variable,
        )
        root_hint = await semantic_variable_hover(
            analyzer,
            document,
            root_position,
            project,
            documents,
            root_variable,
        )
        optional_hint = await semantic_variable_hover(
            analyzer,
            document,
            optional_position,
            project,
            documents,
            optional_variable,
        )
    finally:
        await analyzer.close()

    assert loop_declaration_hint.contents.value == (
        '```python\n(variable) ch: Literal["H", "e", "l", "o"]\n```\n\nLoop variable introduced by c-for.'
    )
    assert loop_hint.contents.value == ("```python\n(variable) ch: str\n```\n\nLoop variable introduced by c-for.")
    assert root_hint.contents.value == (
        '```python\n(variable) title: Literal["Hello"]\n```\n\nInferred from template_data()'
    )
    assert optional_hint.contents.value == (
        "```python\n(variable) action: str | None\n```\n\nInferred from template_data()"
    )


@pytest.mark.asyncio
async def test_shared_variable_hover_retains_every_consumer_type(tmp_path: Path) -> None:
    template_file = tmp_path / "shared.html"
    template_source = "{{ value }}"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class TextCard(Component):\n"
        "    citry = engine\n"
        "    template_file = 'shared.html'\n"
        "    class TemplateData:\n"
        "        value: str\n"
        "class CountCard(Component):\n"
        "    citry = engine\n"
        "    template_file = 'shared.html'\n"
        "    class TemplateData:\n"
        "        value: int\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    documents = {document.uri: document}
    position = _position(template_source, "value", 2)
    variable = template_variable_hover(document, position, project, documents)
    assert variable is not None

    analyzer = TyAnalyzer(tmp_path)
    try:
        hint = await semantic_variable_hover(
            analyzer,
            document,
            position,
            project,
            documents,
            variable,
        )
    finally:
        await analyzer.close()

    assert hint.contents.value in {
        "```python\n(variable) value: str | int\n```\n\nTemplateData field",
        "```python\n(variable) value: int | str\n```\n\nTemplateData field",
    }


@pytest.mark.asyncio
async def test_shared_variable_hover_labels_declared_and_inferred_consumers(tmp_path: Path) -> None:
    template_file = tmp_path / "shared.html"
    template_source = "{{ value }}"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class TextCard(Component):\n"
        "    citry = engine\n"
        "    template_file = 'shared.html'\n"
        "    class TemplateData:\n"
        "        value: str\n"
        "class CountCard(Component):\n"
        "    citry = engine\n"
        "    template_file = 'shared.html'\n"
        "    def template_data(self, kwargs):\n"
        "        return {'value': 1}\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    documents = {document.uri: document}
    position = _position(template_source, "value", 2)
    variable = template_variable_hover(document, position, project, documents)
    assert variable is not None
    assert variable.provenance == "Proven by TemplateData and template_data()"
    assert variable.fallback_types == ()

    analyzer = TyAnalyzer(tmp_path)
    try:
        hint = await semantic_variable_hover(
            analyzer,
            document,
            position,
            project,
            documents,
            variable,
        )
    finally:
        await analyzer.close()

    assert hint.contents.value in {
        "```python\n(variable) value: str | Literal[1]\n```\n\nProven by TemplateData and template_data()",
        "```python\n(variable) value: Literal[1] | str\n```\n\nProven by TemplateData and template_data()",
    }


@pytest.mark.asyncio
async def test_shared_variable_hover_does_not_reuse_one_kwargs_fallback(tmp_path: Path) -> None:
    template_file = tmp_path / "shared.html"
    template_source = "{{ value }}"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class TextCard(Component):\n"
        "    citry = engine\n"
        "    template_file = 'shared.html'\n"
        "    class Kwargs:\n"
        "        value: str\n"
        "class CountCard(Component):\n"
        "    citry = engine\n"
        "    template_file = 'shared.html'\n"
        "    def template_data(self, kwargs):\n"
        "        return {'value': 1}\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    documents = {document.uri: document}
    position = _position(template_source, "value", 2)
    variable = template_variable_hover(document, position, project, documents)
    assert variable is not None
    assert variable.provenance == "Inferred from template_data()"
    assert variable.fallback_types == ()

    analyzer = TyAnalyzer(tmp_path)
    try:
        hint = await semantic_variable_hover(
            analyzer,
            document,
            position,
            project,
            documents,
            variable,
        )
    finally:
        await analyzer.close()

    assert hint.contents.value in {
        "```python\n(variable) value: str | Literal[1]\n```\n\nInferred from template_data()",
        "```python\n(variable) value: Literal[1] | str\n```\n\nInferred from template_data()",
    }


@pytest.mark.asyncio
async def test_fill_variable_hover_keeps_provenance_with_an_unknown_type(tmp_path: Path) -> None:
    template_file = tmp_path / "card.html"
    template_source = '<c-layout><c-fill name="body" data="{row}">{{ row }}</c-fill></c-layout>'
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component, SlotInput\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Layout(Component):\n"
        "    citry = engine\n"
        "    class Slots:\n"
        "        body: SlotInput[dict[str, object]]\n"
        "    template = '''\n<c-slot name=\"body\" />\n'''\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class TemplateData: pass\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    documents = {document.uri: document}
    declaration_position = _position(template_source, 'data="{row', len('data="{ro'))
    position = _position(template_source, "{{ row", len("{{ ro"))
    declaration_variable = template_variable_hover(document, declaration_position, project, documents)
    variable = template_variable_hover(document, position, project, documents)
    assert declaration_variable is not None
    assert variable is not None

    analyzer = TyAnalyzer(tmp_path)
    try:
        declaration_hint = await semantic_variable_hover(
            analyzer,
            document,
            declaration_position,
            project,
            documents,
            declaration_variable,
        )
        hint = await semantic_variable_hover(
            analyzer,
            document,
            position,
            project,
            documents,
            variable,
        )
        declaration_types = await semantic_type_definition(
            analyzer,
            document,
            declaration_position,
            project,
            documents,
        )
        use_types = await semantic_type_definition(
            analyzer,
            document,
            position,
            project,
            documents,
        )
    finally:
        await analyzer.close()

    assert declaration_hint.contents.value == (
        "```python\n(variable) row\n```\n\nSlot-data variable introduced by c-fill."
    )
    assert hint.contents.value == ("```python\n(variable) row: Any\n```\n\nSlot-data variable introduced by c-fill.")
    assert declaration_types
    assert declaration_types == use_types


@pytest.mark.asyncio
async def test_unused_fill_binding_has_a_neutral_type_definition(tmp_path: Path) -> None:
    template_file = tmp_path / "card.html"
    template_source = '<c-layout><c-fill name="body" data="{row}"></c-fill></c-layout>'
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component, SlotInput\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Layout(Component):\n"
        "    citry = engine\n"
        "    class Slots:\n"
        "        body: SlotInput[dict[str, object]]\n"
        "    template = '<c-slot name=\"body\" />'\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    documents = {document.uri: document}

    analyzer = TyAnalyzer(tmp_path)
    try:
        locations = await semantic_type_definition(
            analyzer,
            document,
            _position(template_source, 'data="{row', len('data="{ro')),
            project,
            documents,
        )
    finally:
        await analyzer.close()

    assert locations
    assert locations[0].uri.endswith("/stdlib/typing.pyi")


@pytest.mark.asyncio
async def test_type_definition_declines_a_stale_synchronized_template_owner(tmp_path: Path) -> None:
    template_file = tmp_path / "card.html"
    template_source = "{{ user }}"
    template_file.write_text(template_source, encoding="utf-8")
    app_file = tmp_path / "app.py"
    app_source = (
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class TemplateData:\n"
        "        user: str\n"
    )
    app_file.write_text(app_source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    synchronized = app_source.replace("'card.html'", "'other.html'")
    python_document = DocumentState(app_file.as_uri(), "python", synchronized, 2)
    python_document.update(synchronized, 2, project)
    documents = {document.uri: document, python_document.uri: python_document}
    analyzer = _PartialTypeAnalyzer(
        types.Location(app_file.as_uri(), types.Range(types.Position(0, 0), types.Position(0, 1)))
    )

    result = await semantic_type_definition(
        cast("TyAnalyzer", analyzer),
        document,
        _position(template_source, "user", 2),
        project,
        documents,
    )

    assert result == ()
    assert analyzer.calls == 0


@pytest.mark.asyncio
async def test_member_completion_handles_optional_roots_and_structural_hosts(
    tmp_path: Path,
) -> None:
    template_file = tmp_path / "card.html"
    template_file.write_text("{{ form_id }}", encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from typing import Literal\n"
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class TemplateData:\n"
        "        action: str | None\n"
        "        method: Literal['get', 'post'] | None\n"
        "        form_id: str\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    cases = (
        ("{{ action. }}", "action."),
        ("{{ action.lo }}", "action.lo"),
        ("{{ method. }}", "method."),
        ('<div c-title="action."></div>', "action."),
        ('<c-if cond="form_id."></c-if>', "form_id."),
        ('<c-for each="ch in form_id.">{{ ch }}</c-for>', "form_id."),
        ('<c-for each="ch in action.">{{ ch }}</c-for>', "action."),
        ('<div c-if="form_id."></div>', "form_id."),
        ('<div c-for="ch in form_id.">{{ ch }}</div>', "form_id."),
        ('<div c-for="ch in action.">{{ ch }}</div>', "action."),
        ("{{ ':=' }}{{ form_id. }}", "form_id."),
        ('{# := #}<c-if cond="form_id."></c-if>', "form_id."),
    )
    analyzer = TyAnalyzer(tmp_path)
    try:
        for version, (template_source, marker) in enumerate(cases, start=1):
            document = DocumentState(template_file.as_uri(), "citry-html", template_source, version)
            document.update(template_source, version, project)
            items = await semantic_completions(
                analyzer,
                document,
                _position(template_source, marker, len(marker)),
                project,
                {document.uri: document},
            )
            assert "lower" in {item.label for item in items}, template_source
    finally:
        await analyzer.close()


@pytest.mark.asyncio
async def test_optional_completion_narrowing_does_not_hide_diagnostics(tmp_path: Path) -> None:
    template_file = tmp_path / "card.html"
    template_source = "{{ action.lower() }}"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class TemplateData:\n"
        "        action: str | None\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    analyzer = TyAnalyzer(tmp_path)
    try:
        findings = await semantic_diagnostics(
            analyzer,
            document,
            project,
            {document.uri: document},
        )
    finally:
        await analyzer.close()

    assert any(finding.code == "citry.python.unresolved-attribute" for finding in findings)


def test_repaired_loop_completion_still_withholds_after_a_real_walrus(tmp_path: Path) -> None:
    template_file = tmp_path / "card.html"
    template_source = '{{ (seen := True) }}<c-for each="ch in form_id.">{{ ch }}</c-for>'
    template_file.write_text("{{ form_id }}", encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class TemplateData:\n"
        "        form_id: str\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)

    assert not expression_shadows(
        document,
        _position(template_source, "form_id.", len("form_id.")),
        project,
        {document.uri: document},
        repair_completion=True,
    )


@pytest.mark.asyncio
async def test_inline_python_template_gets_optional_and_structural_member_completion(
    tmp_path: Path,
) -> None:
    app_file = tmp_path / "app.py"

    def app_source(template_source: str) -> str:
        return (
            "from citry import Citry, Component\n"
            "engine = Citry(autodiscover=False)\n"
            "class Card(Component):\n"
            "    citry = engine\n"
            "    class TemplateData:\n"
            "        action: str | None\n"
            "        form_id: str\n"
            f"    template = '''{template_source}'''\n"
        )

    app_file.write_text(app_source("{{ form_id }}"), encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    cases = (
        ("{{ action. }}", "action."),
        ('<c-for each="ch in form_id.">{{ ch }}</c-for>', "form_id."),
        ('<c-if cond="form_id."></c-if>', "form_id."),
    )
    analyzer = TyAnalyzer(tmp_path)
    try:
        for version, (template_source, marker) in enumerate(cases, start=1):
            source = app_source(template_source)
            document = DocumentState(app_file.as_uri(), "python", source, version)
            document.update(source, version, project)
            items = await semantic_completions(
                analyzer,
                document,
                _position(source, marker, len(marker)),
                project,
                {document.uri: document},
            )
            assert "lower" in {item.label for item in items}, template_source
    finally:
        await analyzer.close()


@pytest.mark.asyncio
async def test_empty_template_data_keeps_lexical_loop_types(tmp_path: Path) -> None:
    template_file = tmp_path / "card.html"
    template_source = "<div c-for=\"item in ['hello']\">{{ item.lo }}</div>"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class TemplateData: pass\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    analyzer = TyAnalyzer(tmp_path)
    try:
        items = await semantic_completions(
            analyzer,
            document,
            _position(template_source, "item.lo", len("item.lo")),
            project,
            {document.uri: document},
        )
    finally:
        await analyzer.close()

    assert "lower" in {item.label for item in items}


@pytest.mark.asyncio
async def test_inferred_return_types_support_hover_and_user_member_definition(tmp_path: Path) -> None:
    template_file = tmp_path / "card.html"
    template_source = '{{ user.display_name }} {{ user.greet("") }}'
    template_file.write_text(template_source, encoding="utf-8")
    app_file = tmp_path / "app.py"
    app_file.write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class User:\n"
        "    display_name: str\n"
        "    def greet(self, prefix: str, count: int = 0) -> str:\n"
        "        return prefix\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    def template_data(self, kwargs):\n"
        "        return {'user': User()}\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    documents = {document.uri: document}
    position = _position(template_source, "display_name", 4)
    analyzer = TyAnalyzer(tmp_path)
    try:
        hint = await semantic_hover(analyzer, document, position, project, documents)
        locations = await semantic_definition(analyzer, document, position, project, documents)
        type_locations = await semantic_type_definition(
            analyzer,
            document,
            _position(template_source, "user.display_name", len("us")),
            project,
            documents,
        )
        signatures = await semantic_signature_help(
            analyzer,
            document,
            _position(template_source, 'greet("', len("greet(")),
            project,
            documents,
        )
    finally:
        await analyzer.close()

    assert hint is not None
    assert "str" in hint.contents.value
    assert hint.range == types.Range(types.Position(0, 8), types.Position(0, 20))
    assert len(locations) == 1
    assert locations[0].uri == app_file.as_uri()
    assert locations[0].range.start.line == 4
    assert len(type_locations) == 1
    assert type_locations[0].uri == app_file.as_uri()
    assert type_locations[0].range.start.line == 3
    assert signatures is not None
    assert any(
        "prefix: str" in signature.label and "count: int" in signature.label for signature in signatures.signatures
    )


@pytest.mark.asyncio
async def test_type_definition_withholds_a_partial_return_path_answer(tmp_path: Path) -> None:
    template_file = tmp_path / "card.html"
    template_source = "{{ user }}"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class User: pass\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    def template_data(self, kwargs):\n"
        "        if kwargs:\n"
        "            return {'user': User()}\n"
        "        return {'user': User()}\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    location = types.Location(
        (tmp_path / "types.py").as_uri(),
        types.Range(types.Position(0, 0), types.Position(0, 4)),
    )
    analyzer = _PartialTypeAnalyzer(location)

    result = await semantic_type_definition(
        cast("TyAnalyzer", analyzer),
        document,
        _position(template_source, "user", 2),
        project,
        {document.uri: document},
    )

    assert analyzer.calls == 2
    assert not result


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("template_source", "cursor_marker"),
    [
        ("{{ user.greet( }}", "greet("),
        ('{{ user.greet("prefix", }}', 'greet("prefix",'),
        ("{{ ':=' }}{{ user.greet( }}", "greet("),
    ],
)
async def test_signature_help_repairs_an_unfinished_authored_call(
    tmp_path: Path,
    template_source: str,
    cursor_marker: str,
) -> None:
    template_file = tmp_path / "card.html"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class User:\n"
        "    def greet(self, prefix: str, count: int = 0) -> str:\n"
        "        return prefix\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    def template_data(self, kwargs):\n"
        "        return {'user': User()}\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    analyzer = TyAnalyzer(tmp_path)
    try:
        result = await semantic_signature_help(
            analyzer,
            document,
            _position(template_source, cursor_marker, len(cursor_marker)),
            project,
            {document.uri: document},
        )
    finally:
        await analyzer.close()

    assert result is not None
    assert any("prefix: str" in signature.label for signature in result.signatures)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "template_source",
    [
        '<c-for each="item in items.copy(">{{ item }}</c-for>',
        '<div c-for="item in items.copy(">{{ item }}</div>',
    ],
)
async def test_signature_help_repairs_unfinished_calls_in_loop_hosts(
    tmp_path: Path,
    template_source: str,
) -> None:
    template_file = tmp_path / "card.html"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class TemplateData:\n"
        "        items: list[str]\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    analyzer = TyAnalyzer(tmp_path)
    try:
        result = await semantic_signature_help(
            analyzer,
            document,
            _position(template_source, "copy(", len("copy(")),
            project,
            {document.uri: document},
        )
    finally:
        await analyzer.close()

    assert result is not None
    assert result.signatures


@pytest.mark.asyncio
async def test_semantic_diagnostics_map_members_and_defer_unknown_roots(tmp_path: Path) -> None:
    template_file = tmp_path / "card.html"
    template_source = "{{ title.missing }} {{ project_global.missing }}"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class TemplateData:\n"
        "        title: str\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    analyzer = TyAnalyzer(tmp_path)
    try:
        findings = await semantic_diagnostics(
            analyzer,
            document,
            project,
            {document.uri: document},
        )
    finally:
        await analyzer.close()

    assert len(findings) == 1
    assert findings[0].code == "citry.python.unresolved-attribute"
    assert findings[0].range == types.Range(types.Position(0, 3), types.Position(0, 16))
    assert "missing" in findings[0].message


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "data_declaration",
    [
        "    class TemplateData:\n        title: str\n",
        "    def template_data(self, kwargs, slots):\n        return {'title': 'hello'}\n",
    ],
)
async def test_semantic_diagnostics_batch_queries_per_consumer(
    tmp_path: Path,
    data_declaration: str,
) -> None:
    template_file = tmp_path / "card.html"
    template_source = "{{ title.missing }}\n{{ title.other_missing }}"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        f"{data_declaration}",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    analyzer = _CountingDiagnosticsAnalyzer()

    findings = await semantic_diagnostics(
        cast("TyAnalyzer", analyzer),
        document,
        project,
        {document.uri: document},
    )

    assert analyzer.calls == 1
    assert [finding.range.start.line for finding in findings] == [0, 1]
    assert all(finding.code == "citry.python.unresolved-attribute" for finding in findings)


@pytest.mark.asyncio
async def test_default_template_data_gets_types_from_effective_kwargs(tmp_path: Path) -> None:
    template_file = tmp_path / "card.html"
    template_source = "{{ title.lo }}"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class Kwargs:\n"
        "        title: str\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    analyzer = TyAnalyzer(tmp_path)
    try:
        items = await semantic_completions(
            analyzer,
            document,
            _position(template_source, "title.lo", len("title.lo")),
            project,
            {document.uri: document},
        )
    finally:
        await analyzer.close()

    assert "lower" in {item.label for item in items}


@pytest.mark.asyncio
async def test_inferred_kwargs_type_survives_same_named_method_local(tmp_path: Path) -> None:
    template_file = tmp_path / "card.html"
    template_source = "{{ title.lo }}"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class Kwargs:\n"
        "        title: str\n"
        "    def template_data(self, kwargs, slots):\n"
        "        Card = int\n"
        "        return kwargs\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    analyzer = TyAnalyzer(tmp_path)
    try:
        items = await semantic_completions(
            analyzer,
            document,
            _position(template_source, "title.lo", len("title.lo")),
            project,
            {document.uri: document},
        )
    finally:
        await analyzer.close()

    assert "lower" in {item.label for item in items}


@pytest.mark.asyncio
async def test_composed_template_data_keeps_each_declaring_field_type(tmp_path: Path) -> None:
    template_file = tmp_path / "card.html"
    template_source = "{{ title.lo }} {{ count.bit_ }}"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Titled(Component):\n"
        "    citry = engine\n"
        "    class TemplateData:\n"
        "        title: str\n"
        "class Counted(Component):\n"
        "    citry = engine\n"
        "    class TemplateData:\n"
        "        count: int\n"
        "class Card(Titled, Counted):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    analyzer = TyAnalyzer(tmp_path)
    try:
        title = await semantic_completions(
            analyzer,
            document,
            _position(template_source, "title.lo", len("title.lo")),
            project,
            {document.uri: document},
        )
        count = await semantic_completions(
            analyzer,
            document,
            _position(template_source, "count.bit_", len("count.bit_")),
            project,
            {document.uri: document},
        )
    finally:
        await analyzer.close()

    assert "lower" in {item.label for item in title}
    assert "bit_length" in {item.label for item in count}


@pytest.mark.asyncio
async def test_composed_kwargs_type_the_inherited_default_roots(tmp_path: Path) -> None:
    template_file = tmp_path / "card.html"
    template_source = "{{ title.lo }} {{ count.bit_ }}"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Titled(Component):\n"
        "    citry = engine\n"
        "    class Kwargs:\n"
        "        title: str\n"
        "class Counted(Component):\n"
        "    citry = engine\n"
        "    class Kwargs:\n"
        "        count: int\n"
        "class Card(Titled, Counted):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    analyzer = TyAnalyzer(tmp_path)
    try:
        title = await semantic_completions(
            analyzer,
            document,
            _position(template_source, "title.lo", len("title.lo")),
            project,
            {document.uri: document},
        )
        count = await semantic_completions(
            analyzer,
            document,
            _position(template_source, "count.bit_", len("count.bit_")),
            project,
            {document.uri: document},
        )
    finally:
        await analyzer.close()

    assert "lower" in {item.label for item in title}
    assert "bit_length" in {item.label for item in count}


@pytest.mark.asyncio
async def test_declared_schema_uses_unsaved_python_annotations(tmp_path: Path) -> None:
    template_file = tmp_path / "card.html"
    template_source = "{{ value.bit_ }}"
    template_file.write_text(template_source, encoding="utf-8")
    app_file = tmp_path / "app.py"
    disk_source = (
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class TemplateData:\n"
        "        value: str\n"
    )
    app_file.write_text(disk_source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    template_document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    template_document.update(template_source, 1, project)
    unsaved_source = disk_source.replace("value: str", "value: int")
    python_document = DocumentState(app_file.as_uri(), "python", unsaved_source, 2)
    python_document.update(unsaved_source, 2, project)
    documents = {
        template_document.uri: template_document,
        python_document.uri: python_document,
    }
    analyzer = TyAnalyzer(tmp_path)
    try:
        items = await semantic_completions(
            analyzer,
            template_document,
            _position(template_source, "value.bit_", len("value.bit_")),
            project,
            documents,
        )
    finally:
        await analyzer.close()

    labels = {item.label for item in items}
    assert "bit_length" in labels
    assert "lower" not in labels


@pytest.mark.asyncio
async def test_unsaved_imported_type_withholds_disk_stale_semantics(tmp_path: Path) -> None:
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    template_file = package / "card.html"
    template_source = "{{ user. }}"
    template_file.write_text(template_source, encoding="utf-8")
    models_file = package / "models.py"
    disk_models = "class User:\n    def wave(self) -> str:\n        return 'hello'\n"
    models_file.write_text(disk_models, encoding="utf-8")
    (package / "app.py").write_text(
        "from citry import Citry, Component\n"
        "from .models import User\n"
        "engine = Citry(autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    def template_data(self, kwargs):\n"
        "        return {'user': User()}\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "pkg.app:engine")
    template_document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    template_document.update(template_source, 1, project)
    unsaved_models = disk_models.replace("wave", "jump")
    models_document = DocumentState(models_file.as_uri(), "python", unsaved_models, 2)
    models_document.update(unsaved_models, 2, project)
    documents = {
        template_document.uri: template_document,
        models_document.uri: models_document,
    }
    analyzer = TyAnalyzer(tmp_path)
    try:
        items = await semantic_completions(
            analyzer,
            template_document,
            _position(template_source, "user.", len("user.")),
            project,
            documents,
        )
    finally:
        await analyzer.close()

    assert not items


@pytest.mark.asyncio
async def test_unchanged_crlf_import_is_not_mistaken_for_an_unsaved_edit(tmp_path: Path) -> None:
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    template_file = package / "card.html"
    template_source = "{{ user. }}"
    template_file.write_text(template_source, encoding="utf-8")
    models_file = package / "models.py"
    disk_models = "class User:\r\n    def wave(self) -> str:\r\n        return 'hello'\r\n"
    models_file.write_bytes(disk_models.encode())
    (package / "app.py").write_text(
        "from citry import Citry, Component\n"
        "from .models import User\n"
        "engine = Citry(autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    def template_data(self, kwargs):\n"
        "        return {'user': User()}\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "pkg.app:engine")
    template_document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    template_document.update(template_source, 1, project)
    models_document = DocumentState(models_file.as_uri(), "python", disk_models, 1)
    models_document.update(disk_models, 1, project)
    documents = {
        template_document.uri: template_document,
        models_document.uri: models_document,
    }
    analyzer = TyAnalyzer(tmp_path)
    try:
        unchanged = await semantic_completions(
            analyzer,
            template_document,
            _position(template_source, "user.", len("user.")),
            project,
            documents,
        )
        edited_models = disk_models.replace("wave", "jump")
        models_document.update(edited_models, 2, project)
        edited = await semantic_completions(
            analyzer,
            template_document,
            _position(template_source, "user.", len("user.")),
            project,
            documents,
        )
    finally:
        await analyzer.close()

    assert "wave" in {item.label for item in unchanged}
    assert not edited


@pytest.mark.asyncio
async def test_symlinked_unsaved_owner_withholds_shared_consumer_answers(tmp_path: Path) -> None:
    workspace = tmp_path / "real"
    package = workspace / "pkg"
    package.mkdir(parents=True)
    link = tmp_path / "link"
    try:
        link.symlink_to(workspace, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are unavailable")
    (package / "__init__.py").write_text("", encoding="utf-8")
    template_file = package / "shared.html"
    template_source = "{{ user.jump() }}"
    template_file.write_text(template_source, encoding="utf-8")
    (package / "app.py").write_text(
        "from citry import Citry\nengine = Citry(autodiscover=False)\nfrom . import a, b\n",
        encoding="utf-8",
    )
    (package / "a.py").write_text(
        "from citry import Component\n"
        "from .app import engine\n"
        "from .b import User\n"
        "class A(Component):\n"
        "    citry = engine\n"
        "    template_file = 'shared.html'\n"
        "    class TemplateData:\n"
        "        user: User\n",
        encoding="utf-8",
    )
    b_file = package / "b.py"
    disk_b = (
        "from citry import Component\n"
        "from .app import engine\n"
        "class User:\n"
        "    def wave(self) -> str:\n"
        "        return 'hello'\n"
        "class B(Component):\n"
        "    citry = engine\n"
        "    template_file = 'shared.html'\n"
        "    class TemplateData:\n"
        "        user: User\n"
    )
    b_file.write_text(disk_b, encoding="utf-8")
    project = load_project(workspace, "pkg.app:engine")
    template_document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    template_document.update(template_source, 1, project)
    unsaved_b = disk_b.replace("wave", "jump")
    linked_b = link / "pkg" / "b.py"
    python_document = DocumentState(linked_b.as_uri(), "python", unsaved_b, 2)
    python_document.update(unsaved_b, 2, project)
    documents = {
        template_document.uri: template_document,
        python_document.uri: python_document,
    }
    analyzer = TyAnalyzer(workspace)
    try:
        items = await semantic_completions(
            analyzer,
            template_document,
            _position(template_source, "user.jump", len("user.ju")),
            project,
            documents,
        )
        diagnostics = await semantic_diagnostics(analyzer, template_document, project, documents)
    finally:
        await analyzer.close()

    assert not items
    assert not diagnostics


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "data_declaration",
    [
        "    def template_data(self, kwargs):\n        return {'user': User()}\n",
        "    class TemplateData:\n        user: User\n",
    ],
)
async def test_package_initializer_relative_import_types_are_resolved(
    tmp_path: Path,
    data_declaration: str,
) -> None:
    package = tmp_path / "pkg"
    package.mkdir()
    template_file = package / "card.html"
    template_source = "{{ user. }}"
    template_file.write_text(template_source, encoding="utf-8")
    (package / "models.py").write_text(
        "class User:\n    def wave(self) -> str:\n        return 'hello'\n",
        encoding="utf-8",
    )
    (package / "__init__.py").write_text(
        "from citry import Citry, Component\n"
        "from .models import User\n"
        "engine = Citry(autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n" + data_declaration,
        encoding="utf-8",
    )
    project = load_project(tmp_path, "pkg:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    analyzer = TyAnalyzer(tmp_path)
    try:
        items = await semantic_completions(
            analyzer,
            document,
            _position(template_source, "user.", len("user.")),
            project,
            {document.uri: document},
        )
    finally:
        await analyzer.close()

    assert "wave" in {item.label for item in items}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "data_declaration",
    [
        "    class TemplateData:\n        from .models import User\n        user: User\n",
        ("    from .models import User\n    def template_data(self, kwargs):\n        return {'user': self.User()}\n"),
    ],
)
async def test_component_class_relative_import_types_are_resolved(
    tmp_path: Path,
    data_declaration: str,
) -> None:
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    template_file = package / "card.html"
    template_source = "{{ user. }}"
    template_file.write_text(template_source, encoding="utf-8")
    (package / "models.py").write_text(
        "class User:\n    def wave(self) -> str:\n        return 'hello'\n",
        encoding="utf-8",
    )
    (package / "app.py").write_text(
        "from citry import Citry, Component\n"
        "engine = Citry(autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n" + data_declaration,
        encoding="utf-8",
    )
    project = load_project(tmp_path, "pkg.app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    analyzer = TyAnalyzer(tmp_path)
    try:
        items = await semantic_completions(
            analyzer,
            document,
            _position(template_source, "user.", len("user.")),
            project,
            {document.uri: document},
        )
    finally:
        await analyzer.close()

    assert "wave" in {item.label for item in items}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("source_name", "app_target"),
    [
        ("app.py", "pkg.app:engine"),
        ("__init__.py", "pkg:engine"),
    ],
)
async def test_type_checking_relative_import_types_are_resolved(
    tmp_path: Path,
    source_name: str,
    app_target: str,
) -> None:
    package = tmp_path / "pkg"
    package.mkdir()
    template_file = package / "card.html"
    template_source = "{{ user. }}"
    template_file.write_text(template_source, encoding="utf-8")
    (package / "models.py").write_text(
        "class User:\n    def wave(self) -> str:\n        return 'hello'\n",
        encoding="utf-8",
    )
    if source_name != "__init__.py":
        (package / "__init__.py").write_text("", encoding="utf-8")
    (package / source_name).write_text(
        "from __future__ import annotations\n"
        "from typing import TYPE_CHECKING\n"
        "from citry import Citry, Component\n"
        "if TYPE_CHECKING:\n"
        "    from .models import User\n"
        "engine = Citry(autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class TemplateData:\n"
        "        user: User\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, app_target)
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    analyzer = TyAnalyzer(tmp_path)
    try:
        items = await semantic_completions(
            analyzer,
            document,
            _position(template_source, "user.", len("user.")),
            project,
            {document.uri: document},
        )
    finally:
        await analyzer.close()

    assert "wave" in {item.label for item in items}


@pytest.mark.asyncio
async def test_inferred_types_preserve_conditional_relative_import_branches(tmp_path: Path) -> None:
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    template_file = package / "card.html"
    template_source = "{{ user. }}"
    template_file.write_text(template_source, encoding="utf-8")
    (package / "current.py").write_text(
        "class User:\n    def current_only(self) -> str:\n        return 'current'\n",
        encoding="utf-8",
    )
    (package / "other.py").write_text(
        "class User:\n    def other_only(self) -> str:\n        return 'other'\n",
        encoding="utf-8",
    )
    (package / "app.py").write_text(
        "import sys\n"
        "from citry import Citry, Component\n"
        f"if sys.platform == {sys.platform!r}:\n"
        "    from .current import User\n"
        "else:\n"
        "    from .other import User\n"
        "engine = Citry(autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    def template_data(self, kwargs):\n"
        "        return {'user': User()}\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "pkg.app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    analyzer = TyAnalyzer(tmp_path)
    try:
        items = await semantic_completions(
            analyzer,
            document,
            _position(template_source, "user.", len("user.")),
            project,
            {document.uri: document},
        )
    finally:
        await analyzer.close()

    labels = {item.label for item in items}
    assert "current_only" in labels
    assert "other_only" not in labels


@pytest.mark.asyncio
async def test_unknown_builtin_name_is_masked_but_a_declared_same_name_is_typed(tmp_path: Path) -> None:
    template_file = tmp_path / "card.html"
    template_source = "{{ str.bit_ }}"
    template_file.write_text(template_source, encoding="utf-8")
    app_file = tmp_path / "app.py"
    source_prefix = (
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
    )
    app_file.write_text(source_prefix, encoding="utf-8")

    async def completions() -> set[str]:
        project = load_project(tmp_path, "app:engine")
        document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
        document.update(template_source, 1, project)
        analyzer = TyAnalyzer(tmp_path)
        try:
            items = await semantic_completions(
                analyzer,
                document,
                _position(template_source, "str.bit_", len("str.bit_")),
                project,
                {document.uri: document},
            )
        finally:
            await analyzer.close()
        return {item.label for item in items}

    assert "bit_length" not in await completions()
    app_file.write_text(source_prefix + "    class TemplateData:\n        str: int\n", encoding="utf-8")
    assert "bit_length" in await completions()


@pytest.mark.asyncio
@pytest.mark.parametrize("unknown_name", ["secret", "kwargs"])
async def test_inferred_method_locals_are_not_template_roots(tmp_path: Path, unknown_name: str) -> None:
    template_file = tmp_path / "card.html"
    template_source = f"{{{{ {unknown_name}. }}}}"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class User:\n"
        "    def wave(self): return 'hello'\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    def template_data(self, kwargs):\n"
        "        secret = User()\n"
        "        return {'title': 'hello'}\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    analyzer = TyAnalyzer(tmp_path)
    try:
        items = await semantic_completions(
            analyzer,
            document,
            _position(template_source, f"{unknown_name}.", len(f"{unknown_name}.")),
            project,
            {document.uri: document},
        )
    finally:
        await analyzer.close()

    assert not items


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "template_source",
    [
        "{{ (value := 1) }}{{ value.lo }}",
        "{{ (lambda: (value := 1))() }}{{ value.lo }}",
        "{{ (lambda: (value := 1))() and value.lo }}",
    ],
)
async def test_walrus_context_mutation_withholds_unsound_semantics(
    tmp_path: Path,
    template_source: str,
) -> None:
    template_file = tmp_path / "card.html"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class TemplateData:\n"
        "        value: str\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    analyzer = TyAnalyzer(tmp_path)
    try:
        items = await semantic_completions(
            analyzer,
            document,
            _position(template_source, "value.lo", len("value.lo")),
            project,
            {document.uri: document},
        )
    finally:
        await analyzer.close()

    assert not items


@pytest.mark.asyncio
async def test_walrus_in_loop_iterable_withholds_shadow_syntax_diagnostic(tmp_path: Path) -> None:
    template_file = tmp_path / "card.html"
    template_source = '<c-for each="item in (values := items)">{{ item }}</c-for>'
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class TemplateData:\n"
        "        items: list[str]\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    analyzer = TyAnalyzer(tmp_path)
    try:
        findings = await semantic_diagnostics(
            analyzer,
            document,
            project,
            {document.uri: document},
        )
    finally:
        await analyzer.close()

    assert not findings


@pytest.mark.asyncio
async def test_loop_clause_diagnostics_use_comprehension_semantics(tmp_path: Path) -> None:
    template_file = tmp_path / "card.html"
    template_source = '<c-for each="item in items.missing">{{ item }}</c-for>'
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class TemplateData:\n"
        "        items: list[str]\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    analyzer = TyAnalyzer(tmp_path)
    try:
        findings = await semantic_diagnostics(
            analyzer,
            document,
            project,
            {document.uri: document},
        )
    finally:
        await analyzer.close()

    assert len(findings) == 1
    assert findings[0].code == "citry.python.unresolved-attribute"
    assert findings[0].range == types.Range(types.Position(0, 21), types.Position(0, 34))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "template_source",
    [
        '<c-for each="item in items  # keep">{{ item.up }}</c-for>',
        '<div c-for="item in items  # keep">{{ item.up }}</div>',
    ],
)
async def test_loop_trailing_comments_keep_body_member_semantics(
    tmp_path: Path,
    template_source: str,
) -> None:
    template_file = tmp_path / "card.html"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Card(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class TemplateData:\n"
        "        items: list[str]\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    analyzer = TyAnalyzer(tmp_path)
    try:
        items = await semantic_completions(
            analyzer,
            document,
            _position(template_source, "item.up", len("item.up")),
            project,
            {document.uri: document},
        )
    finally:
        await analyzer.close()

    assert "upper" in {item.label for item in items}


@pytest.mark.asyncio
@pytest.mark.parametrize("leading", [" ", "\u00a0"])
async def test_nested_expression_uses_the_registry_parser_recursively(
    tmp_path: Path,
    leading: str,
) -> None:
    template_file = tmp_path / "card.html"
    template_source = f"<c-wrapper c-body=\"{leading}<><div c-for='item in items'>{{{{ item.up }}}}</div></>\" />"
    template_file.write_text(template_source, encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        "from citry import Citry, Component\n"
        "engine = Citry(dirs=[Path(__file__).parent], autodiscover=False)\n"
        "class Wrapper(Component):\n"
        "    citry = engine\n"
        "    template = '<c-slot />'\n"
        "    class Kwargs:\n"
        "        body: object\n"
        "class Page(Component):\n"
        "    citry = engine\n"
        "    template_file = 'card.html'\n"
        "    class TemplateData:\n"
        "        items: list[str]\n",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    assert project.analysis is not None
    calls: list[str] = []
    original_analysis = project.analysis

    class TrackingAnalysis:
        component_lint = original_analysis.component_lint

        def parse_template(self, source: str):
            calls.append(source)
            return original_analysis.parse_template(source)

        def to_dict(self):
            return original_analysis.to_dict()

    tracked_project = replace(project, analysis=TrackingAnalysis())
    document = DocumentState(template_file.as_uri(), "citry-html", template_source, 1)
    document.update(template_source, 1, project)
    analyzer = TyAnalyzer(tmp_path)
    try:
        items = await semantic_completions(
            analyzer,
            document,
            _position(template_source, "item.up", len("item.up")),
            tracked_project,
            {document.uri: document},
        )
    finally:
        await analyzer.close()

    assert calls
    by_label = {item.label: item for item in items}
    assert "upper" in by_label
    edit = by_label["upper"].text_edit
    assert isinstance(edit, types.InsertReplaceEdit)
    assert edit.replace == types.Range(
        _position(template_source, "item.up", len("item.")),
        _position(template_source, "item.up", len("item.up")),
    )
