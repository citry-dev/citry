"""Tests for atomic formatting of Citry templates embedded in Python."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

import citry.analysis as analysis_module
from citry import (
    PythonTemplateFormatError,
    PythonTemplateFormatResult,
    discover_python_templates,
    format_python_templates,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
CORPUS_ROOT = REPO_ROOT / "crates" / "citry_template_formatter" / "tests" / "fixtures" / "v1"


def _component_source(template_literal: str, *, component_name: str = "Card") -> str:
    return f"from citry import Component\n\nclass {component_name}(Component):\n    template = {template_literal}\n"


def test_shared_python_host_corpus() -> None:
    index = json.loads((CORPUS_ROOT / "index.json").read_text(encoding="utf-8"))
    for case in index["python_hosts"]:
        source = case.get("input_text")
        if source is None:
            source = (CORPUS_ROOT / case["input"]).read_text(encoding="utf-8")
        expected_path = case.get("expected")
        expected = case.get("expected_text")
        if expected_path is not None or expected is not None:
            if expected is None:
                expected = (CORPUS_ROOT / expected_path).read_text(encoding="utf-8")
            result = format_python_templates(source)
            assert result.source == expected, case["id"]
            assert format_python_templates(result.source).source == result.source, case["id"]
            continue

        expected_error = case["expected_error"]
        with pytest.raises(PythonTemplateFormatError) as raised:
            format_python_templates(source)
        assert raised.value.code == expected_error["code"], case["id"]
        if contains := expected_error.get("contains"):
            assert contains in str(raised.value), case["id"]

        if raised.value.code == "citry.format.host-syntax":
            assert raised.value.range is not None, case["id"]
            assert isinstance(raised.value.diagnostic, SyntaxError), case["id"]


def test_result_is_immutable_and_reports_changed_components() -> None:
    source = _component_source("u'''<div  title = \"žluťoučký\" ></div>'''")

    result = format_python_templates(source)

    assert isinstance(result, PythonTemplateFormatResult)
    assert result.changed_component_names == ("Card",)
    assert result.notices == ()
    assert "u'''<div title=\"žluťoučký\"></div>'''" in result.source
    with pytest.raises(AttributeError):
        result.source = source  # type: ignore[misc]


def test_document_rewrite_is_atomic_when_a_later_template_is_ineligible() -> None:
    source = (
        "from citry import Component\n\n"
        "class First(Component):\n"
        '    template = """<div  id = "first" ></div>"""\n\n'
        "class Second(Component):\n"
        '    template = ("<span  " "id = \\"second\\" ></span>")\n'
    )

    with pytest.raises(PythonTemplateFormatError, match="implicit") as raised:
        format_python_templates(source)

    assert raised.value.code == "citry.format.ineligible"
    assert [notice.component_name for notice in raised.value.notices] == ["Second"]
    assert not hasattr(raised.value, "source")


def test_cursor_scope_formats_only_the_containing_template() -> None:
    source = (
        "from citry import Component\n\n"
        "class First(Component):\n"
        '    template = """<div  id = "first" ></div>"""\n\n'
        "class Second(Component):\n"
        '    template = """<span  id = "second" ></span>"""\n'
    )
    second_template_offset = source.index("<span")

    result = format_python_templates(source, host_offset=second_template_offset)

    assert '<div  id = "first" ></div>' in result.source
    assert '<span id="second"></span>' in result.source
    assert result.changed_component_names == ("Second",)


def test_cursor_scope_reports_notices_elsewhere_without_failing_selection() -> None:
    source = (
        "from citry import Component\n\n"
        "class Card(Component):\n"
        '    template = """<div  id = "card" ></div>"""\n\n'
        "class MarkdownCard(Component):\n"
        '    template_lang = "markdown"\n'
        '    template = """# Heading"""\n'
    )

    result = format_python_templates(source, host_offset=source.index("<div"))

    assert result.changed_component_names == ("Card",)
    assert [notice.component_name for notice in result.notices] == ["MarkdownCard"]


def test_cursor_outside_a_template_is_an_explicit_ineligibility() -> None:
    source = _component_source('"""<div></div>"""')

    with pytest.raises(PythonTemplateFormatError, match="does not contain") as raised:
        format_python_templates(source, host_offset=0)

    assert raised.value.code == "citry.format.ineligible"


@pytest.mark.parametrize("host_offset", [-1, 10_000, True, 1.5])
def test_host_offset_must_be_a_valid_python_string_offset(host_offset: object) -> None:
    source = _component_source('"""<div></div>"""')

    with pytest.raises((TypeError, ValueError)):
        format_python_templates(source, host_offset=host_offset)  # type: ignore[arg-type]


def test_computed_template_is_not_reported_as_clean() -> None:
    source = _component_source('"<div>" + suffix')

    with pytest.raises(PythonTemplateFormatError, match="computed") as raised:
        format_python_templates(source)

    assert raised.value.code == "citry.format.ineligible"
    assert raised.value.notices[0].component_name == "Card"


@pytest.mark.parametrize(
    "template_literal",
    [
        'f"<div>{value}</div>"',
        'b"<div></div>"',
    ],
)
def test_dynamic_literal_forms_are_explicitly_ineligible(template_literal: str) -> None:
    source = _component_source(template_literal)

    with pytest.raises(PythonTemplateFormatError) as raised:
        format_python_templates(source)

    assert raised.value.code == "citry.format.ineligible"
    assert raised.value.notices[0].component_name == "Card"


def test_alternate_template_language_is_explicitly_ineligible() -> None:
    source = (
        "from citry import Component\n\n"
        "class Card(Component):\n"
        '    template_lang = "markdown"\n'
        '    template = """# Heading"""\n'
    )

    with pytest.raises(PythonTemplateFormatError, match="template_lang") as raised:
        format_python_templates(source)

    assert raised.value.code == "citry.format.ineligible"


@pytest.mark.parametrize(
    "source",
    [
        (
            "from citry import Component\n\n"
            "class Card(Component):\n"
            "    template_lang = choose_language()\n"
            '    template = """<div></div>"""\n'
        ),
        (
            "from citry import Component\n\n"
            "class Mix: pass\n\n"
            "class Card(Component, Mix):\n"
            '    template = """<div></div>"""\n'
        ),
        (
            "from citry import Component\n\n"
            "class Card(Component):\n"
            "    template_file = choose_template()\n"
            '    template = """<div></div>"""\n'
        ),
    ],
)
def test_unprovable_direct_template_source_is_not_a_false_clean(source: str) -> None:
    with pytest.raises(PythonTemplateFormatError) as raised:
        format_python_templates(source)

    assert raised.value.code == "citry.format.ineligible"
    assert raised.value.notices[0].component_name == "Card"


def test_no_definite_templates_is_a_clean_no_op() -> None:
    source = "value = 1\n"

    result = format_python_templates(source)

    assert result == PythonTemplateFormatResult(source, (), ())


def test_library_component_alias_uses_the_same_rewrite_contract() -> None:
    source = (
        "from citry import LibraryComponent as Base\n\n"
        "class Card(Base):\n"
        '    template = """<div  class = "row" ></div>"""\n'
    )

    result = format_python_templates(source)

    assert '<div class="row"></div>' in result.source
    assert result.changed_component_names == ("Card",)


def test_single_quoted_literal_remains_single_quoted_when_no_newline_is_needed() -> None:
    source = _component_source("'<div  class = \"row\" ></div>'")

    result = format_python_templates(source)

    assert "template = '<div class=\"row\"></div>'" in result.source


def test_unchanged_escape_outside_rewrite_hunks_is_preserved() -> None:
    source = _component_source('"""line\\n<div  class = "row" ></div>"""')

    result = format_python_templates(source)

    assert '"""line\\n<div class="row"></div>"""' in result.source


def test_fmt_off_preserves_python_host_framing() -> None:
    source = _component_source(
        '"""\n    {# fmt: off #}\n    <main><section></section></main>\n    """',
    )

    result = format_python_templates(source)

    assert result.source == source


def test_template_error_range_is_mapped_to_absolute_python_offsets() -> None:
    source = _component_source('"""é{# fmt: on #}<div></div>"""')

    with pytest.raises(PythonTemplateFormatError) as raised:
        format_python_templates(source)

    error = raised.value
    assert error.code == "citry.format.suppression"
    assert error.range is not None
    assert source[slice(*error.range)] == "{# fmt: on #}"
    assert error.diagnostic is None


def test_changed_literal_is_rediscovered_as_exact_formatter_output() -> None:
    source = _component_source('r"""<div  title = "😀" ></div>"""')

    result = format_python_templates(source)
    ast.parse(result.source)
    discovery = discover_python_templates(result.source)

    assert discovery.regions[0].source_map.template_source == '<div title="😀"></div>'


def test_unrepresentable_core_output_never_exposes_a_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    source = _component_source('"""<div></div>"""')
    monkeypatch.setattr(analysis_module, "_format_template", lambda _source: '"""')

    with pytest.raises(PythonTemplateFormatError) as raised:
        format_python_templates(source)

    assert raised.value.code == "citry.format.ineligible"
    assert not hasattr(raised.value, "source")
