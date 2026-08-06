"""Tests for the public template-analysis and source-coordinate contracts."""

from __future__ import annotations

import ast

import pytest

from citry import (
    Citry,
    Component,
    LspPosition,
    LspRange,
    PythonTemplateSourceMap,
    TemplateAnalysis,
    discover_python_templates,
)


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
        engine = Citry(autodiscover=False)

        class PortableCard(Component):
            citry = engine

            class Kwargs:
                title: str

        original = engine.template_analysis()
        restored = TemplateAnalysis.from_dict(original.to_dict())

        assert restored.component_names == original.component_names
        with pytest.raises(SyntaxError, match="must have one of the following attributes"):
            restored.parse_template("<c-portable-card />")


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
