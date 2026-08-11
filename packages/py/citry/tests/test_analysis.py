"""Tests for the public template-analysis and source-coordinate contracts."""

from __future__ import annotations

import ast
from typing import Annotated

import pytest

from citry import (
    Citry,
    Component,
    LintSettings,
    LspPosition,
    LspRange,
    PythonTemplateSourceMap,
    TemplateAnalysis,
    TemplateLintConsumer,
    discover_python_templates,
    lint_unknown_template_variables,
)
from citry.analysis import (
    css_data_completion_at,
    css_data_reference_at,
    css_data_references,
    python_application_lint_variable_range,
    python_component_lint_variable_range,
)
from citry_core.template_parser import parse_template


def _assigned_string(source: str) -> ast.Constant:
    module = ast.parse(source)
    assignment = module.body[-1]
    assert isinstance(assignment, ast.Assign)
    assert isinstance(assignment.value, ast.Constant)
    assert type(assignment.value.value) is str
    return assignment.value


def _lsp_position(source: str, offset: int) -> LspPosition:
    before = source[:offset]
    line = before.count("\n")
    line_text = before.rsplit("\n", 1)[-1]
    character = len(line_text.encode("utf-16-le")) // 2
    return LspPosition(line, character)


def test_css_data_reference_scanner_keeps_exact_var_arguments_only():
    source = """
    .card {
      --declared: 1px;
      width: var(--chart_height);
      color: VAR( /* current */ --row-color, var(--fallback));
      content: "var(--inside-string)";
      /* var(--inside-comment) */
    }
    """

    references = css_data_references(source)

    assert [reference.name for reference in references] == ["chart_height", "row-color", "fallback"]
    chart = references[0]
    assert source.encode()[chart.start_index : chart.end_index].decode() == "--chart_height"
    assert css_data_reference_at(source, chart.start_index + 4) == chart


def test_css_data_completion_covers_empty_partial_unicode_and_declines_escapes():
    source = ".card { color: var(--café"
    cursor = len(source.encode())

    completion = css_data_completion_at(source, cursor)

    assert completion is not None
    assert completion.prefix == "café"
    assert source.encode()[completion.start_index : completion.end_index].decode() == "--café"
    empty = "a { color: var(--"
    assert css_data_completion_at(empty, len(empty.encode())).prefix == ""  # type: ignore[union-attr]
    escaped = "a { color: var(--\\63 olor) }"
    assert css_data_references(escaped) == ()
    assert css_data_completion_at(escaped, len(b"a { color: var(--")) is None


class TestTemplateAnalysis:
    def test_snapshot_parses_with_complete_registered_contracts(self):
        engine = Citry(autodiscover=False)

        class AnalysisCard(Component):
            citry = engine

            class Kwargs:
                title: str

            template = """
            <article>{{ title }}</article>
            """

        analysis = engine.template_analysis()

        assert isinstance(analysis, TemplateAnalysis)
        assert {"analysiscard", "analysis-card"} <= analysis.component_names
        with pytest.raises(SyntaxError, match="must have one of the following attributes"):
            analysis.parse_template("<c-analysis-card />")
        parsed = analysis.parse_template('<c-analysis-card title="Hello" />')
        assert len(parsed.elements) == 1

    def test_snapshot_remains_coherent_after_later_registration(self):
        engine = Citry(autodiscover=False)
        before = engine.template_analysis()

        class LaterCard(Component):
            citry = engine
            template = """
            <p>Later</p>
            """

        after = engine.template_analysis()

        assert "later-card" not in before.component_names
        assert "later-card" in after.component_names

    def test_portable_round_trip_preserves_component_rules(self):
        engine = Citry(
            autodiscover=False,
            template_globals={"site_name": "Citry"},
            lint=LintSettings(
                rule_unknown_template_variable="warning",
                template_variables={
                    "request": Annotated[str, "Current request."],
                },
            ),
        )

        class PortableCard(Component):
            citry = engine

            class Kwargs:
                title: str

        original = engine.template_analysis()
        restored = TemplateAnalysis.from_dict(original.to_dict())

        assert restored.component_names == original.component_names
        assert restored.lint == original.lint
        assert dict(restored.component_lint) == dict(original.component_lint)
        assert {item.name for item in restored.lint.template_variables} == {"request", "site_name"}
        with pytest.raises(SyntaxError, match="must have one of the following attributes"):
            restored.parse_template("<c-portable-card />")

    def test_runtime_global_cycles_and_executable_annotation_text_drop_only_the_type(self):
        cyclic: list[object] = []
        cyclic.append(cyclic)
        engine = Citry(
            autodiscover=False,
            template_globals={"cyclic": cyclic},
            lint=LintSettings(template_variables={"request": "factory()"}),
        )

        by_name = {item.name: item for item in engine.template_analysis().lint.template_variables}

        assert by_name["cyclic"].type_display is None
        assert by_name["request"].type_display is None
        assert set(by_name) == {"cyclic", "request"}


class TestLintVariableSourceRanges:
    def test_application_range_follows_direct_settings_aliases(self):
        source = (
            "from citry import Citry, LintSettings\n"
            "variables = {'request': str}\n"
            "settings = LintSettings(template_variables=variables)\n"
            "app = Citry(autodiscover=False, lint=settings)\n"
        )
        start = source.index("'request'")

        assert python_application_lint_variable_range(source, "app", "request") == LspRange(
            _lsp_position(source, start),
            _lsp_position(source, start + len("'request'")),
        )

    def test_component_range_uses_the_exact_nested_lint_class(self):
        source = (
            "class Outer:\n    class Card:\n        class Lint:\n            template_variables = {'request': str}\n"
        )
        start = source.index("'request'")

        assert python_component_lint_variable_range(source, "Outer.Card.Lint", "request") == LspRange(
            _lsp_position(source, start),
            _lsp_position(source, start + len("'request'")),
        )

    @pytest.mark.parametrize(
        ("source", "resolver"),
        [
            ("app = Citry(lint=build_settings())\n", "application"),
            (
                "class Card:\n    class Lint:\n        template_variables = build_variables()\n",
                "component",
            ),
        ],
    )
    def test_dynamic_settings_decline_navigation(self, source, resolver):
        if resolver == "application":
            result = python_application_lint_variable_range(source, "app", "request")
        else:
            result = python_component_lint_variable_range(source, "Card.Lint", "request")

        assert result is None

    def test_unknown_root_lint_uses_parser_free_names_and_severity_matrix(self):
        template = parse_template(
            '<div c-title="known + missing"><c-for each="item in items">{{ item }}</c-for></div>'
        )
        closed = TemplateLintConsumer(frozenset({"known", "items"}), "closed", "error")
        allowed = TemplateLintConsumer(frozenset({"known", "items"}), "allow-extra", "error")

        closed_findings = lint_unknown_template_variables(template, (closed,))
        allowed_findings = lint_unknown_template_variables(template, (allowed,))

        assert [(item.name, item.severity) for item in closed_findings] == [("missing", "error")]
        assert [(item.name, item.severity) for item in allowed_findings] == [("missing", "warning")]
        assert closed_findings[0].code == "citry.template.unknown-variable"

    def test_shared_template_uses_the_strictest_missing_consumer(self):
        template = parse_template("{{ shared }} {{ absent }}")
        warning = TemplateLintConsumer(frozenset({"shared"}), "allow-extra", "error")
        strict = TemplateLintConsumer(frozenset({"shared"}), "unknown", "error")
        ignored = TemplateLintConsumer(frozenset(), "closed", "ignore")

        findings = lint_unknown_template_variables(template, (warning, strict, ignored))

        assert [(item.name, item.severity) for item in findings] == [("absent", "error")]

    def test_unknown_root_lint_joins_python_identifier_identity(self):
        template = parse_template("{{ K }}")  # noqa: RUF001 - normalization is the behavior under test
        consumer = TemplateLintConsumer(frozenset({"K"}), "closed", "error")

        assert lint_unknown_template_variables(template, (consumer,)) == ()


class TestPythonTemplateSourceMap:
    def test_dedented_parser_source_maps_back_to_indented_python(self):
        source = 'template = """\n  <main>\n    <p>Hi</p>\n  </main>\n  """'
        source_map = PythonTemplateSourceMap.from_ast(source, _assigned_string(source))
        host_start = source.index("<p>")
        parser_start = len(b"\n<main>\n  ")
        parser_end = parser_start + len(b"<p>")

        assert source_map.template_source == "\n<main>\n  <p>Hi</p>\n</main>\n"
        assert source_map.map_range(parser_start, parser_end) == LspRange(
            _lsp_position(source, host_start),
            _lsp_position(source, host_start + len("<p>")),
        )
        removed_indent = source.index("    <p>") + 1
        assert source_map.parser_index_at(_lsp_position(source, removed_indent)) is None

    def test_maps_parser_bytes_through_non_ascii_python_to_utf16(self):
        source = 'prefix = "😀"; template = """é<div>"""'
        source_map = PythonTemplateSourceMap.from_ast(source, _assigned_string(source))
        template_start = len("é".encode())
        template_end = template_start + len(b"<div>")
        host_start = source.index("<div>")

        assert source_map.template_source == "é<div>"
        assert source_map.map_range(template_start, template_end) == LspRange(
            _lsp_position(source, host_start),
            _lsp_position(source, host_start + len("<div>")),
        )
        with pytest.raises(ValueError, match="splits a UTF-8 code point"):
            source_map.map_range(1, template_end)

    def test_escape_range_maps_to_the_authored_escape(self):
        source = 'template = """line\\n<c-card />"""'
        source_map = PythonTemplateSourceMap.from_ast(source, _assigned_string(source))
        escape_start = source.index("\\n")

        assert source_map.template_source == "line\n<c-card />"
        assert source_map.map_range(4, 5) == LspRange(
            _lsp_position(source, escape_start),
            _lsp_position(source, escape_start + 2),
        )

    @pytest.mark.parametrize(
        ("literal", "expected"),
        [
            ('r"""\\n<div>"""', "\\n<div>"),
            ("u'''é<div>'''", "é<div>"),
            ('"<div>"', "<div>"),
            ("'<div>'", "<div>"),
        ],
    )
    def test_decodes_supported_prefixes_and_quote_styles(self, literal, expected):
        source = f"template = {literal}"

        source_map = PythonTemplateSourceMap.from_ast(source, _assigned_string(source))

        assert source_map.template_source == expected

    def test_maps_implicitly_concatenated_literals(self):
        source = 'template = ("<div>"\n            "é</div>")'
        source_map = PythonTemplateSourceMap.from_ast(source, _assigned_string(source))
        byte_start = len(b"<div>")
        byte_end = byte_start + len("é".encode())
        host_start = source.index("é")

        assert source_map.template_source == "<div>é</div>"
        assert source_map.map_range(byte_start, byte_end) == LspRange(
            _lsp_position(source, host_start),
            _lsp_position(source, host_start + 1),
        )
        assert source_map.range_is_unambiguous(byte_start, byte_end) is True
        assert source_map.range_is_unambiguous(0, byte_end) is False

    def test_normalized_multiline_range_remains_unambiguous(self):
        source = 'template = """\n  {{ (\n    value\n  ) }}\n  """'
        source_map = PythonTemplateSourceMap.from_ast(source, _assigned_string(source))

        assert source_map.range_is_unambiguous(0, len(source_map.template_source.encode())) is True

    def test_maps_concatenation_across_a_python_comment(self):
        source = 'template = ("a"  # authored note\n            r"\\nb")'

        source_map = PythonTemplateSourceMap.from_ast(source, _assigned_string(source))

        assert source_map.template_source == "a\\nb"

    def test_normalizes_physical_crlf_like_cpython(self):
        source = 'template = """a\r\n<div>"""'
        source_map = PythonTemplateSourceMap.from_ast(source, _assigned_string(source))
        host_start = source.index("<div>")

        assert source_map.template_source == "a\n<div>"
        assert source_map.map_range(2, 7) == LspRange(
            _lsp_position(source, host_start),
            _lsp_position(source, host_start + len("<div>")),
        )

    def test_maps_named_unicode_escape_to_its_complete_source_span(self):
        source = 'template = """\\N{GRINNING FACE}<div>"""'
        source_map = PythonTemplateSourceMap.from_ast(source, _assigned_string(source))
        escape_start = source.index("\\N")
        escape_end = source.index("}") + 1

        assert source_map.template_source == "😀<div>"
        assert source_map.map_range(0, len("😀".encode())) == LspRange(
            _lsp_position(source, escape_start),
            _lsp_position(source, escape_end),
        )

    def test_accepts_an_incomplete_triple_quoted_region(self):
        source = 'template = r"""<div>😀'
        source_map = PythonTemplateSourceMap.from_coordinates(
            source,
            lineno=1,
            col_offset=len(b"template = "),
            accept_incomplete=True,
        )
        byte_start = len(b"<div>")
        byte_end = byte_start + len("😀".encode())
        host_start = source.index("😀")

        assert source_map.template_source == "<div>😀"
        assert source_map.map_range(byte_start, byte_end) == LspRange(
            _lsp_position(source, host_start),
            _lsp_position(source, host_start + 1),
        )

    def test_rejects_dynamic_string_prefixes(self):
        source = 'template = f"""<div>{value}</div>"""'

        with pytest.raises(ValueError, match="does not produce a static text value"):
            PythonTemplateSourceMap.from_coordinates(
                source,
                lineno=1,
                col_offset=len(b"template = "),
                end_lineno=1,
                end_col_offset=len(source.encode()),
            )


class TestDiscoverPythonTemplates:
    def test_discovers_proven_component_literals_and_language_notices(self):
        discovery = discover_python_templates(
            "from citry import Component\n"
            "class Card(Component):\n"
            '    template = """<c-panel />"""\n'
            "class MarkdownCard(Component):\n"
            '    template_lang = "markdown"\n'
            '    template = """# Title"""\n',
        )

        assert [region.component_name for region in discovery.regions] == ["Card"]
        assert discovery.regions[0].source_map.template_source == "<c-panel />"
        assert [(notice.component_name, notice.message) for notice in discovery.notices] == [
            (
                "MarkdownCard",
                "unsupported non-None template_lang (str); template skipped",
            ),
        ]
        assert discovery.valid_python is True

    def test_incomplete_recovery_is_explicit(self):
        source = 'from citry import Component\nclass Card(Component):\n    template = r"""<c-panel />'

        with pytest.raises(SyntaxError):
            discover_python_templates(source)

        recovered = discover_python_templates(source, recover_incomplete=True)
        assert recovered.valid_python is False
        assert recovered.regions[0].source_map.template_source == "<c-panel />"
