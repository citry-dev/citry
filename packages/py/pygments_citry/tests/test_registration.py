"""The ``citry`` lexer registers with Pygments as a plugin and on import."""

from importlib.metadata import entry_points

from pygments.lexers import LEXERS, get_lexer_by_name

import pygments_citry


def test_resolves_by_alias():
    lexer = get_lexer_by_name("citry")
    assert type(lexer).__name__ == "CitryPythonLexer"


def test_plugin_entry_point_declared():
    values = {ep.value for ep in entry_points(group="pygments.lexers") if ep.name == "citry"}
    assert "pygments_citry.lexers:CitryPythonLexer" in values


def test_import_registers_in_builtin_table():
    assert "CitryPythonLexer" in LEXERS
    assert "CitryHtmlLexer" in LEXERS
    assert pygments_citry.CitryPythonLexer.name == "Citry Python"
    assert pygments_citry.CitryHtmlLexer.name == "Citry HTML"


def test_citry_html_resolves_by_alias():
    lexer = get_lexer_by_name("citry-html")
    assert type(lexer).__name__ == "CitryHtmlLexer"


def test_citry_html_entry_point_declared():
    values = {ep.value for ep in entry_points(group="pygments.lexers") if ep.name == "citry-html"}
    assert "pygments_citry.citry_html:CitryHtmlLexer" in values


def test_fluent_dependency_aliases_resolve():
    fluent = get_lexer_by_name("fluent")
    ftl = get_lexer_by_name("ftl")

    assert fluent.name == "Fluent Lexer"
    assert type(fluent) is type(ftl)
