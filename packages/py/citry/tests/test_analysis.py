"""Tests for the public template-analysis and source-coordinate contracts."""

from __future__ import annotations

import ast
from typing import Annotated

import pytest

from citry import (
    Citry,
    Component,
    ComponentSourceLint,
    LintSettings,
    LspPosition,
    LspRange,
    PythonTemplateSourceMap,
    TemplateAnalysis,
    TemplateLintConsumer,
    discover_python_component_assets,
    discover_python_templates,
    format_python_templates,
    lint_unknown_template_variables,
)
from citry._linting import TemplateLintInfo, _application_lint_info, _component_lint_info
from citry.analysis import (
    component_name_match,
    css_data_completion_at,
    css_data_reference_at,
    css_data_references,
    discover_untraced_component_templates,
    project_module_exists,
    python_application_lint_variable_range,
    python_component_lint_variable_range,
    template_tag_uses,
    unknown_component_uses,
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


def test_portable_component_names_match_desktop_spelling_rules():
    exact = component_name_match("c-card", "c-card", is_class_name=False, variant_index=0)
    compact = component_name_match("c-CardHe", "c-Card-Header", is_class_name=True, variant_index=1)

    assert exact is not None
    assert exact.filter_text == "c-card"
    assert compact is not None
    assert compact.filter_text == "c-CardHeader"
    assert compact.sort_text > exact.sort_text


def test_portable_unknown_component_uses_include_nested_templates():
    source = '<c-known c-body="<><c-missing /></>"><c-other /></c-known>'
    template = parse_template(source)

    uses = unknown_component_uses(template, {"known", "other"})

    assert [(use.tag, source.encode()[use.start_index : use.end_index].decode()) for use in uses] == [
        ("c-missing", "c-missing")
    ]
    tags = template_tag_uses(template)
    assert [(use.tag, use.closing) for use in tags] == [
        ("c-known", False),
        ("c-missing", False),
        ("c-other", False),
        ("c-known", True),
    ]


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
                rule_alpine_attribute="ignore",
            ),
        )

        class PortableCard(Component):
            citry = engine

            class Kwargs:
                title: str

            class Lint:
                rule_alpine_cloak = "warning"

        original = engine.template_analysis()
        restored = TemplateAnalysis.from_dict(original.to_dict())

        assert restored.component_names == original.component_names
        assert restored.lint == original.lint
        assert dict(restored.component_lint) == dict(original.component_lint)
        assert {item.name for item in restored.lint.template_variables} == {"request", "site_name"}
        # The Alpine rules survive the portable dict at both levels.
        card_lint = restored.component_lint[PortableCard.definition_id]
        assert (restored.lint.rule_alpine_attribute, restored.lint.rule_alpine_cloak) == ("ignore", "error")
        assert (card_lint.rule_alpine_attribute, card_lint.rule_alpine_cloak) == ("ignore", "warning")
        with pytest.raises(SyntaxError, match="must have one of the following attributes"):
            restored.parse_template("<c-portable-card />")

    def test_lint_record_from_an_older_app_worker_gets_the_new_rule_default(self):
        # An app worker running an older citry sends no misspelled-directive
        # rule; the editor must still read the record, with the default.
        record = TemplateLintInfo("warning", (), rule_misspelled_directive="ignore").to_dict()
        assert TemplateLintInfo.from_dict(record).rule_misspelled_directive == "ignore"
        del record["rule_misspelled_directive"]

        restored = TemplateLintInfo.from_dict(record)

        assert restored.rule_misspelled_directive == "error"
        assert restored.rule_unknown_template_variable == "warning"
        # Only the later fields may be missing, and no field may be unknown.
        with pytest.raises(ValueError, match="exact supported fields"):
            TemplateLintInfo.from_dict({**record, "rule_from_the_future": "error"})

    def test_lint_record_carries_the_template_rules_and_fills_in_missing_ones(self):
        record = TemplateLintInfo(
            "warning",
            (),
            rule_missing_image_alt="error",
            rule_undeclared_component_event="ignore",
        ).to_dict()
        restored = TemplateLintInfo.from_dict(record)
        assert (restored.rule_missing_image_alt, restored.rule_undeclared_component_event) == ("error", "ignore")
        # A record from an older citry has none of these rules.
        for name in ("rule_missing_image_alt", "rule_undeclared_component_event", "rule_invalid_vue_expression"):
            del record[name]
        older = TemplateLintInfo.from_dict(record)
        assert (older.rule_missing_image_alt, older.rule_undeclared_component_event) == ("warning", "warning")
        assert older.rule_invalid_vue_expression == "error"
        with pytest.raises(ValueError, match="rule_duplicate_id"):
            TemplateLintInfo("warning", (), rule_duplicate_id="fatal")  # type: ignore[arg-type]
        del record["rule_alpine_cloak"]
        with pytest.raises(ValueError, match="exact supported fields"):
            TemplateLintInfo.from_dict(record)

    @pytest.mark.parametrize("mode", ["warn", "strict"])
    def test_lint_record_carries_the_security_csp_mode(self, mode):
        record = TemplateLintInfo("warning", (), security_csp=mode).to_dict()
        assert record["security_csp"] == mode
        assert TemplateLintInfo.from_dict(record).security_csp == mode

    def test_lint_record_leaves_out_security_csp_while_off_and_reads_a_record_without_it(self):
        # An editor from a citry without the field must still read the record.
        assert TemplateLintInfo("warning", ()).security_csp == "off"
        record = TemplateLintInfo("warning", (), security_csp="off").to_dict()
        assert "security_csp" not in record
        assert TemplateLintInfo.from_dict(record).security_csp == "off"
        # A record that spells out "off" reads the same.
        assert TemplateLintInfo.from_dict({**record, "security_csp": "off"}).security_csp == "off"

    @pytest.mark.parametrize("mode", ["", "Strict", "on", None, True, 1])
    def test_lint_record_rejects_an_unknown_security_csp_mode(self, mode):
        with pytest.raises(ValueError, match="Unknown security_csp mode"):
            TemplateLintInfo("warning", (), security_csp=mode)  # type: ignore[arg-type]
        record = TemplateLintInfo("warning", ()).to_dict()
        with pytest.raises(ValueError, match="Unknown security_csp mode"):
            TemplateLintInfo.from_dict({**record, "security_csp": mode})

    @pytest.mark.parametrize("mode", ["off", "warn", "strict"])
    def test_lint_info_takes_the_security_csp_mode_from_the_engine(self, mode):
        engine = Citry(autodiscover=False, security_csp=mode)

        class Card(Component):
            citry = engine

            class Lint:
                rule_missing_image_alt = "error"

        # A component cannot set its own policy, so it reads the engine's.
        assert _application_lint_info(engine).security_csp == mode
        assert _component_lint_info(engine, Card).security_csp == mode
        analysis = engine.template_analysis()
        assert analysis.lint.security_csp == mode
        assert analysis.component_lint[Card.definition_id].security_csp == mode
        # The record the app worker sends the editor keeps it.
        restored = TemplateAnalysis.from_dict(analysis.to_dict())
        assert restored.lint.security_csp == mode
        assert restored.component_lint[Card.definition_id].security_csp == mode

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
        # Recovered text has no class to read, so no owner's Lint is known.
        assert recovered.regions[0].owner_lint == ()


def _owner_lint(source: str) -> dict[str, list[ComponentSourceLint]]:
    """Return each discovered template's owner Lint records, keyed by the declaring class."""
    return {
        region.component_name: list(region.owner_lint)
        for region in discover_python_templates("from citry import Component\n" + source).regions
    }


_TEMPLATE = "    template = '<p></p>'\n"


class TestTemplateOwnerLint:
    def test_reads_string_literals_from_the_component_lint_class(self):
        source = (
            "class Card(Component):\n" + _TEMPLATE + "    class Lint:\n"
            "        rule_misspelled_directive = 'ignore'\n"
            "        rule_invalid_attribute_value: str = 'error'\n"
            "        rule_alpine_attribute = 'warning'\n"
            "        rule_alpine_cloak = 'ignore'\n"
            "        rule_unknown_template_variable = 'ignore'\n"
        )
        assert _owner_lint(source) == {
            "Card": [ComponentSourceLint("warning", "ignore", "error", "ignore")],
        }

    def test_leaves_unreadable_and_unknown_values_unset(self):
        # A name, a call, an unknown severity, and a value bound inside an
        # `if` cannot be read from the source; the last value of a rule wins.
        source = (
            "from x import SEVERITY\n"
            "class Card(Component):\n" + _TEMPLATE + "    class Lint:\n"
            "        rule_misspelled_directive = SEVERITY\n"
            "        rule_invalid_attribute_value = str('ignore')\n"
            "        rule_alpine_cloak = 'off'\n"
            "        if SEVERITY:\n"
            "            rule_alpine_attribute = 'ignore'\n"
            "class Other(Component):\n" + _TEMPLATE + "    class Lint:\n"
            "        rule_misspelled_directive = 'ignore'\n"
            "        rule_misspelled_directive = SEVERITY\n"
        )
        assert _owner_lint(source) == {"Card": [ComponentSourceLint()], "Other": [ComponentSourceLint()]}

    def test_combines_lint_from_same_module_bases_nearest_first(self):
        source = (
            "class Base(Component):\n"
            "    class Lint:\n"
            "        rule_misspelled_directive = 'ignore'\n"
            "        rule_alpine_cloak = 'warning'\n"
            "class Card(Base):\n" + _TEMPLATE + "    class Lint:\n"
            "        rule_misspelled_directive = 'warning'\n"
        )
        assert _owner_lint(source) == {
            "Card": [ComponentSourceLint(rule_alpine_cloak="warning", rule_misspelled_directive="warning")],
        }

    def test_lint_none_drops_inherited_settings(self):
        source = (
            "class Base(Component):\n"
            "    class Lint:\n"
            "        rule_misspelled_directive = 'ignore'\n"
            "class Card(Base):\n" + _TEMPLATE + "    Lint = None\n"
        )
        assert _owner_lint(source) == {"Card": [ComponentSourceLint()]}

    def test_a_base_the_source_does_not_show_hides_inherited_settings(self):
        # A Lint class with its own base, a Lint bound to a name or inside an
        # `if`, and a decorated Lint may each bring rules from elsewhere; only
        # what the body itself shows is read.
        base = "class Base(Component):\n    class Lint:\n        rule_misspelled_directive = 'ignore'\n"
        cases = {
            "class Card(Base):\n" + _TEMPLATE + "    class Lint(Shared):\n        rule_alpine_cloak = 'ignore'\n": [
                ComponentSourceLint(rule_alpine_cloak="ignore"),
            ],
            "class Card(Base):\n" + _TEMPLATE + "    Lint = Shared\n": [ComponentSourceLint()],
            "class Card(Base):\n" + _TEMPLATE + "    if FLAG:\n        Lint = None\n": [ComponentSourceLint()],
            "class Card(Base):\n" + _TEMPLATE + "    @wrap\n    class Lint:\n        pass\n": [
                ComponentSourceLint(),
            ],
        }
        for card, expected in cases.items():
            assert _owner_lint(base + card) == {"Card": expected}, card
        # With a mixin next to the component base, the template language is
        # not proven either, so the template is not checked at all.
        assert _owner_lint(base + "class Card(Mixin, Base):\n" + _TEMPLATE) == {}

    def test_subclasses_that_keep_the_template_are_owners_too(self):
        # Shop, Plain, and Native render Card's template; Fancy chooses its
        # own, Markdown renders another language, and Mixed may get a
        # template from its mixin.
        source = (
            "class Card(Component):\n" + _TEMPLATE + "    class Lint:\n"
            "        rule_misspelled_directive = 'ignore'\n"
            "class Shop(Card):\n"
            "    class Lint:\n"
            "        rule_misspelled_directive = 'warning'\n"
            "class Plain(Shop):\n"
            "    Lint = None\n"
            "class Fancy(Card):\n"
            "    template_file = 'fancy.html'\n"
            "class Native(Card):\n"
            "    template_lang = None\n"
            "    class Lint:\n"
            "        rule_alpine_cloak = 'warning'\n"
            "class Markdown(Card):\n"
            "    template_lang = 'markdown'\n"
            "class Mixed(Mixin, Card):\n"
            "    pass\n"
        )
        assert _owner_lint(source) == {
            "Card": [
                ComponentSourceLint(rule_misspelled_directive="ignore"),
                ComponentSourceLint(rule_misspelled_directive="warning"),
                ComponentSourceLint(),
                ComponentSourceLint(rule_alpine_cloak="warning", rule_misspelled_directive="ignore"),
            ],
        }

    def test_follows_the_name_a_base_is_bound_to_when_the_subclass_is_defined(self):
        # Re-importing Component under Base's name makes Card's base Citry's
        # own, so Base's Lint does not apply to it.
        source = (
            "class Base(Component):\n"
            "    class Lint:\n"
            "        rule_misspelled_directive = 'ignore'\n"
            "from citry import Component as Base\n"
            "class Card(Base):\n" + _TEMPLATE
        )
        assert _owner_lint(source) == {"Card": [ComponentSourceLint()]}

    def test_the_last_lint_binding_in_a_class_wins(self):
        base = "class Base(Component):\n    class Lint:\n        rule_misspelled_directive = 'ignore'\n"
        lint = "    class Lint:\n        rule_alpine_cloak = 'ignore'\n"
        reset = "    Lint: ClassVar[type | None] = None\n"
        assert _owner_lint(base + "class Card(Base):\n" + _TEMPLATE + lint + reset) == {
            "Card": [ComponentSourceLint()]
        }
        assert _owner_lint(base + "class Card(Base):\n" + _TEMPLATE + reset + lint) == {
            "Card": [ComponentSourceLint(rule_alpine_cloak="ignore", rule_misspelled_directive="ignore")],
        }

    def test_reads_lint_on_library_components(self):
        source = (
            "from citry import LibraryComponent\n"
            "class Card(LibraryComponent):\n" + _TEMPLATE + "    class Lint:\n"
            "        rule_misspelled_directive = 'warning'\n"
        )
        assert _owner_lint(source) == {"Card": [ComponentSourceLint(rule_misspelled_directive="warning")]}

    def test_builds_consumers_with_no_application_severities_for_unset_rules(self):
        unset = ComponentSourceLint()
        assert unset.alpine_consumer().rule_alpine_attribute == "warning"
        assert unset.alpine_consumer().rule_alpine_cloak == "error"
        assert unset.attribute_value_consumer().rule_invalid_attribute_value == "warning"
        assert unset.directive_consumer().rule_misspelled_directive == "error"
        chosen = ComponentSourceLint("ignore", "warning", "error", "ignore")
        assert chosen.alpine_consumer().rule_alpine_attribute == "ignore"
        assert chosen.alpine_consumer().rule_alpine_cloak == "warning"
        assert chosen.attribute_value_consumer().rule_invalid_attribute_value == "error"
        assert chosen.directive_consumer().rule_misspelled_directive == "ignore"
        with pytest.raises(ValueError, match="rule_misspelled_directive"):
            ComponentSourceLint(rule_misspelled_directive="fatal")  # type: ignore[arg-type]

    def test_reads_the_html_rules_and_builds_their_consumer(self):
        source = (
            "class Card(Component):\n" + _TEMPLATE + "    class Lint:\n"
            "        rule_missing_image_alt = 'error'\n"
            "        rule_invalid_vue_expression = 'ignore'\n"
        )
        (lint,) = _owner_lint(source)["Card"]
        assert lint == ComponentSourceLint(rule_missing_image_alt="error", rule_invalid_vue_expression="ignore")
        consumer = lint.markup_consumer()
        assert (consumer.rule_missing_image_alt, consumer.rule_invalid_vue_expression) == ("error", "ignore")
        # Unset rules keep their defaults, and the source cannot show whether
        # the component has browser code, so a root image may get its alt.
        assert consumer.rule_duplicate_id == "error"
        assert consumer.rule_misspelled_event == "warning"
        assert consumer.root_may_receive_attributes is True
        with pytest.raises(ValueError, match="rule_invalid_nesting"):
            ComponentSourceLint(rule_invalid_nesting="fatal")  # type: ignore[arg-type]


def test_source_map_long_unicode_lines_keep_utf16_columns():
    line = "aé😀" * 2000
    source = 'value = """' + line + "\r\n" + line + '"""'
    source_map = PythonTemplateSourceMap.from_ast(source, _assigned_string(source))
    line_bytes = len(line.encode("utf-8"))
    assert source_map.map_range(line_bytes - 4, line_bytes) == LspRange(LspPosition(0, 8009), LspPosition(0, 8011))
    assert source_map.map_range(line_bytes + 1, line_bytes + 2) == LspRange(LspPosition(1, 0), LspPosition(1, 1))


def test_untraced_component_templates_follow_project_imports_only(tmp_path):
    package = tmp_path / "app"
    (package / "ui").mkdir(parents=True)
    for path in (package / "__init__.py", package / "ui" / "__init__.py", package / "ui" / "base.py"):
        path.write_text("", encoding="utf-8")
    card = package / "ui" / "card.py"
    source = (
        "from citry import Component\n"
        "from .base import BaseCard\n"
        "from app.ui.base import Mixin\n"
        "from installed import Widget\n"
        "import app.ui.base as base\n"
        "class Local(BaseCard):\n"
        "    pass\n"
        "class Card(Local):\n"
        "    template = '<article></article>'\n"
        "class Mixed(Mixin, Widget):\n"
        "    template: str = '<p></p>'\n"
        "class FromPackage(Widget):\n"
        "    template = '<p></p>'\n"
        "class Plain(BaseCard):\n"
        "    template = 'card.html'\n"
        "class Dotted(base.BaseCard):\n"
        "    template = '<p></p>'\n"
        "class Proven(Component):\n"
        "    template = '<p></p>'\n"
    )

    found = discover_untraced_component_templates(
        source,
        is_project_module=lambda module, level: project_module_exists(module, level, file=card, root=tmp_path),
    )

    # A base defined in the file is followed to the class it imports; an installed
    # package, a template that is a file name, a dotted base, and a proven
    # component are not reported.
    assert [(item.component_name, item.base, item.line, item.start_column) for item in found] == [
        ("Card", "BaseCard", 8, 6),
        ("Mixed", "Mixin", 10, 6),
    ]


def test_app_components_read_a_decorated_component_the_app_lists():
    source = (
        "from citry import Component\n"
        "from app.registry import register\n"
        "@register\n"
        "class Listed(Component):\n"
        "    template = '<p>listed</p>'\n"
        "@register\n"
        "class Unlisted(Component):\n"
        "    template = '<p>unlisted</p>'\n"
    )

    # Reading the file alone, a decorator may replace the class, so neither
    # template is read; the app's record proves the listed one.
    assert discover_python_templates(source).regions == ()
    assert [
        region.component_name for region in discover_python_templates(source, app_components={"Listed": True}).regions
    ] == ["Listed"]


def test_app_components_find_templates_whose_base_comes_from_another_module():
    source = (
        "from app.base import AppBase, JinjaBase, register\n"
        "class Card(AppBase):\n"
        "    template = '<article>{{ title }}</article>'\n"
        "    js = 'console.log(1)'\n"
        "    css = 'article { color: red }'\n"
        "class Wide(Card):\n"
        "    template = '<section></section>'\n"
        "class Legacy(JinjaBase):\n"
        "    template = '<p>{% if x %}{% endif %}</p>'\n"
        "    css = 'p { margin: 0 }'\n"
        "@register\n"
        "class Decorated(AppBase):\n"
        "    template = '<p></p>'\n"
        "class Added(AppBase):\n"
        "    template = '<p>  </p>'\n"
    )
    # What a loaded app reports: Legacy's base sets another template_lang.
    # Added is not listed, as for a class written after the app loaded.
    app_components = {"Card": True, "Legacy": False, "Decorated": True}

    templates = discover_python_templates(source, app_components=app_components)
    assets = discover_python_component_assets(source, app_components=app_components)
    untraced = discover_untraced_component_templates(
        source,
        is_project_module=lambda module, _level: module == "app.base",
        app_components=app_components,
    )

    # A listed class is a component, and a same-file subclass traces
    # through it. A template the app does not call Citry's own is skipped,
    # though its CSS is still found. The app's record names the class that
    # declares the template, so a decorated one is read too.
    assert [(region.component_name, region.source_map.template_source) for region in templates.regions] == [
        ("Card", "<article>{{ title }}</article>"),
        ("Wide", "<section></section>"),
        ("Decorated", "<p></p>"),
    ]
    assert [(region.component_name, region.kind.value) for region in assets.regions] == [
        ("Card", "template"),
        ("Card", "js"),
        ("Card", "css"),
        ("Wide", "template"),
        ("Legacy", "css"),
        ("Decorated", "template"),
    ]
    # Only the classes still skipped keep their notice.
    assert [(item.component_name, item.base) for item in untraced] == [("Added", "AppBase")]
    # Without the app, and for the formatter, which never loads it, reading
    # the file alone finds none of them.
    assert discover_python_templates(source).regions == ()
    assert discover_python_component_assets(source).regions == ()
    assert format_python_templates(source).changed_component_names == ()
