"""Executable evidence for the Stage 3 preview-value decision."""

# Assertions are the pytest test contract in this research proof.
# ruff: noqa: S101

from __future__ import annotations

import re

import pytest
from preview_runner import (
    PLAYGROUND_FILENAME,
    Runner,
    run_explicit_render,
    run_implicit,
    run_named_preview,
    run_print_as_html,
)
from starter_candidates import ALL_STARTERS, StarterCandidate

IMPLICIT_VALUES = {
    "string": "html = '<strong>string</strong>'\nhtml",
    "Markup": "from markupsafe import Markup\nMarkup('<strong>markup</strong>')",
    "CitryElement": '''from citry import Component
class Demo(Component):
    template = """
      <strong>element</strong>
    """
Demo()
''',
    "CitryRender": '''from citry import Component
class Demo(Component):
    template = """
      <strong>render</strong>
    """
Demo().render()
''',
}

DEMO_COMPONENT = '''from citry import Component

class MatrixDemo(Component):
    template = """
      <strong>matrix</strong>
    """
'''

BROKEN_COMPONENT = '''from citry import Component

class MatrixBroken(Component):
    class Kwargs:
        required: str

    template = """
      <p>{{ required }}</p>
    """
'''

MATRIX_SOURCES = {
    "implicit": {
        "string": "html = '<strong>matrix</strong>'\nhtml\n",
        "CitryElement": f"{DEMO_COMPONENT}MatrixDemo()\n",
        "CitryRender": f"{DEMO_COMPONENT}MatrixDemo().render()\n",
        "no expression": "answer = 42\n",
        "None": "None\n",
        "object": "object()\n",
        "multiple print": 'print("one")\nprint("two")\n"<p>preview</p>"\n',
        "render error": f"{BROKEN_COMPONENT}MatrixBroken()\n",
    },
    "explicit render": {
        "string": "render('<strong>matrix</strong>')\n",
        "CitryElement": f"{DEMO_COMPONENT}render(MatrixDemo())\n",
        "CitryRender": f"{DEMO_COMPONENT}render(MatrixDemo().render())\n",
        "no expression": "answer = 42\n",
        "None": "render(None)\n",
        "object": "render(object())\n",
        "multiple print": 'print("one")\nprint("two")\nrender("<p>preview</p>")\n',
        "render error": f"{BROKEN_COMPONENT}render(MatrixBroken())\n",
    },
    "print as HTML": {
        "string": "print('<strong>matrix</strong>')\n",
        "CitryElement": f"{DEMO_COMPONENT}print(MatrixDemo())\n",
        "CitryRender": f"{DEMO_COMPONENT}print(MatrixDemo().render())\n",
        "no expression": "answer = 42\n",
        "None": "print(None)\n",
        "object": "print(object())\n",
        "multiple print": 'print("one")\nprint("two")\n',
        "render error": f"{BROKEN_COMPONENT}print(MatrixBroken())\n",
    },
    "named preview": {
        "string": "preview = '<strong>matrix</strong>'\n",
        "CitryElement": f"{DEMO_COMPONENT}preview = MatrixDemo()\n",
        "CitryRender": f"{DEMO_COMPONENT}preview = MatrixDemo().render()\n",
        "no expression": "answer = 42\n",
        "None": "preview = None\n",
        "object": "preview = object()\n",
        "multiple print": 'print("one")\nprint("two")\npreview = "<p>preview</p>"\n',
        "render error": f"{BROKEN_COMPONENT}preview = MatrixBroken()\n",
    },
}

MATRIX_RUNNERS = {
    "implicit": run_implicit,
    "explicit render": run_explicit_render,
    "print as HTML": run_print_as_html,
    "named preview": run_named_preview,
}


@pytest.mark.parametrize(("value_type", "source"), IMPLICIT_VALUES.items())
def test_implicit_accepts_documented_preview_values(
    value_type: str,
    source: str,
) -> None:
    result = run_implicit(source)

    assert result.ok, (value_type, result.diagnostic)
    expected = {
        "string": "string",
        "Markup": "markup",
        "CitryElement": "element",
        "CitryRender": "render",
    }[value_type]
    assert f">{expected}</strong>" in result.html or result.html == (f"<strong>{expected}</strong>")


@pytest.mark.parametrize(
    ("value_type", "expression"),
    [
        ("string", "'<strong>string</strong>'"),
        ("Markup", "Markup('<strong>markup</strong>')"),
        ("CitryElement", "Demo()"),
        ("CitryRender", "Demo().render()"),
    ],
)
def test_explicit_render_accepts_documented_preview_values(
    value_type: str,
    expression: str,
) -> None:
    imports = "from markupsafe import Markup\n" if value_type == "Markup" else ""
    component = ""
    if value_type in {"CitryElement", "CitryRender"}:
        component = '''from citry import Component
class Demo(Component):
    template = """
      <strong>citry</strong>
    """
'''
    result = run_explicit_render(f"{imports}{component}render({expression})\n")

    assert result.ok, result.diagnostic
    assert "</strong>" in result.html


@pytest.mark.parametrize("candidate", MATRIX_RUNNERS)
@pytest.mark.parametrize("value_type", ["string", "CitryElement", "CitryRender"])
def test_every_candidate_handles_the_three_primary_result_shapes(
    candidate: str,
    value_type: str,
) -> None:
    result = MATRIX_RUNNERS[candidate](MATRIX_SOURCES[candidate][value_type])

    assert result.ok, (candidate, value_type, result.diagnostic)
    assert "matrix" in result.html


@pytest.mark.parametrize("candidate", MATRIX_RUNNERS)
def test_every_candidate_reports_a_missing_preview(candidate: str) -> None:
    result = MATRIX_RUNNERS[candidate](MATRIX_SOURCES[candidate]["no expression"])

    assert result.diagnostic.kind == "missing_preview"


@pytest.mark.parametrize("candidate", MATRIX_RUNNERS)
@pytest.mark.parametrize("value_type", ["None", "object"])
def test_strict_candidates_reject_values_that_print_silently_accepts(
    candidate: str,
    value_type: str,
) -> None:
    result = MATRIX_RUNNERS[candidate](MATRIX_SOURCES[candidate][value_type])

    if candidate == "print as HTML":
        assert result.ok
        assert result.html
    else:
        expected = "none_preview" if value_type == "None" else "unsupported_preview_type"
        assert result.diagnostic.kind == expected


@pytest.mark.parametrize("candidate", MATRIX_RUNNERS)
def test_every_candidate_captures_multiple_print_calls(candidate: str) -> None:
    result = MATRIX_RUNNERS[candidate](MATRIX_SOURCES[candidate]["multiple print"])

    assert result.ok
    assert result.stdout == "one\ntwo\n"
    if candidate == "print as HTML":
        assert result.html == result.stdout
    else:
        assert result.html == "<p>preview</p>"


@pytest.mark.parametrize("candidate", MATRIX_RUNNERS)
def test_every_candidate_exercises_a_citry_render_error(candidate: str) -> None:
    result = MATRIX_RUNNERS[candidate](MATRIX_SOURCES[candidate]["render error"])

    assert result.diagnostic.kind == "python_error"
    assert "required" in result.diagnostic.message
    if candidate == "named preview":
        # Normalizing an assigned element after exec loses the assignment frame.
        # Recovering it would require another AST rewrite or weaker semantics.
        assert result.diagnostic.filename == "<runner>"
    else:
        assert PLAYGROUND_FILENAME in result.diagnostic.traceback


@pytest.mark.parametrize("runner", [run_implicit, run_explicit_render])
def test_serious_candidates_reject_none_and_unrelated_objects(runner: Runner) -> None:
    none_source = "None" if runner is run_implicit else "render(None)"
    object_source = "object()" if runner is run_implicit else "render(object())"

    none_result = runner(none_source)
    object_result = runner(object_source)

    assert none_result.diagnostic.kind == "none_preview"
    assert object_result.diagnostic.kind == "unsupported_preview_type"
    assert "object" in object_result.diagnostic.message


def test_implicit_reports_no_expression_without_losing_stdout() -> None:
    result = run_implicit('print("ordinary log")\nanswer = 42\n')

    assert result.diagnostic.kind == "missing_preview"
    assert result.diagnostic.line == 2
    assert PLAYGROUND_FILENAME in result.diagnostic.traceback
    assert result.stdout == "ordinary log\n"


def test_stdout_and_stderr_are_captured_independently() -> None:
    result = run_implicit(
        "import sys\nprint('ordinary output')\nprint('warning output', file=sys.stderr)\n'<p>preview</p>'\n"
    )

    assert result.ok
    assert result.html == "<p>preview</p>"
    assert result.stdout == "ordinary output\n"
    assert result.stderr == "warning output\n"


def test_docstring_only_module_is_metadata_not_preview_html() -> None:
    result = run_implicit('"""Module documentation, not HTML output."""\n')

    assert result.diagnostic.kind == "missing_preview"


def test_module_docstring_is_preserved_when_a_later_expression_is_previewed() -> None:
    result = run_implicit('"""kept docs"""\n__doc__\n')

    assert result.ok
    assert result.html == "kept docs"


def test_future_import_stays_in_its_legal_position() -> None:
    result = run_implicit(
        "from __future__ import annotations\nclass Model:\n    item: TypeDeclaredLater\n'<p>future import kept</p>'\n"
    )

    assert result.ok
    assert result.html == "<p>future import kept</p>"


def test_semicolon_ending_uses_only_the_final_expression() -> None:
    result = run_implicit('discarded = "first"; "<p>second</p>"\n')

    assert result.ok
    assert result.html == "<p>second</p>"


def test_private_names_in_user_source_do_not_collide() -> None:
    result = run_implicit(
        '__citry_playground_result = "user result"\n'
        '__citry_playground_normalize = "user normalizer"\n'
        '"<p>runner result</p>"\n'
    )

    assert result.ok
    assert result.html == "<p>runner result</p>"


@pytest.mark.parametrize("runner", [run_implicit, run_explicit_render])
def test_serious_candidates_capture_stdout_but_never_use_it_as_html(
    runner: Runner,
) -> None:
    ending = "'<p>preview</p>'" if runner is run_implicit else "render('<p>preview</p>')"
    result = runner(f'print("first")\nprint("second")\n{ending}\n')

    assert result.ok
    assert result.html == "<p>preview</p>"
    assert result.stdout == "first\nsecond\n"


def test_print_candidate_concatenates_logs_and_accepts_arbitrary_objects() -> None:
    result = run_print_as_html('print("<p>preview</p>")\nprint("debug record")\nprint({"unrelated": 1})\n')

    assert result.ok
    assert result.html == ("<p>preview</p>\ndebug record\n{'unrelated': 1}\n")


def test_named_preview_adds_a_reserved_global_and_ignores_final_expression() -> None:
    missing = run_named_preview("'<p>ignored</p>'\n")
    assigned = run_named_preview("preview = '<p>assigned</p>'\n")

    assert missing.diagnostic.kind == "missing_preview"
    assert assigned.ok
    assert assigned.html == "<p>assigned</p>"


@pytest.mark.parametrize(
    "runner",
    [
        run_implicit,
        run_explicit_render,
        run_print_as_html,
        run_named_preview,
    ],
)
def test_syntax_errors_keep_playground_source_positions(runner: Runner) -> None:
    result = runner("class Broken(\n")

    assert result.diagnostic.kind == "syntax_error"
    assert result.diagnostic.filename == PLAYGROUND_FILENAME
    assert result.diagnostic.line == 1
    assert PLAYGROUND_FILENAME in result.diagnostic.traceback


def test_render_error_traceback_includes_the_implicit_expression_line() -> None:
    source = '''from citry import Component

class Broken(Component):
    class Kwargs:
        required: str

    template = """
      <p>{{ required }}</p>
    """

Broken()
'''
    result = run_implicit(source)

    assert result.diagnostic.kind == "python_error"
    assert f'File "{PLAYGROUND_FILENAME}", line 11' in result.diagnostic.traceback
    assert "required" in result.diagnostic.message
    assert "preview_runner.py" not in result.diagnostic.traceback
    assert "run_implicit" not in result.diagnostic.traceback
    assert "normalize_preview" not in result.diagnostic.traceback
    assert "/Users/" not in result.diagnostic.traceback


def test_render_error_traceback_includes_the_explicit_call_line() -> None:
    source = '''from citry import Component

class Broken(Component):
    class Kwargs:
        required: str

    template = """
      <p>{{ required }}</p>
    """

render(Broken())
'''
    result = run_explicit_render(source)

    assert result.diagnostic.kind == "python_error"
    assert f'File "{PLAYGROUND_FILENAME}", line 11' in result.diagnostic.traceback
    assert "required" in result.diagnostic.message


def test_runtime_traceback_keeps_original_function_and_call_lines() -> None:
    result = run_implicit("def explode():\n    raise ValueError('boom')\nexplode()\n")

    assert result.diagnostic.kind == "python_error"
    assert f'File "{PLAYGROUND_FILENAME}", line 3' in result.diagnostic.traceback
    assert f'File "{PLAYGROUND_FILENAME}", line 2' in result.diagnostic.traceback
    assert result.diagnostic.line == 2


def test_exception_chain_cycle_returns_a_filtered_diagnostic() -> None:
    result = run_implicit("error = ValueError('boom')\nraise error from error\n")

    assert result.diagnostic.kind == "python_error"
    assert result.diagnostic.filename == PLAYGROUND_FILENAME
    assert result.diagnostic.line == 2
    assert "exception chain cycle omitted" in result.diagnostic.traceback
    assert "preview_runner.py" not in result.diagnostic.traceback
    assert "/Users/" not in result.diagnostic.traceback


@pytest.mark.parametrize("runner", [run_implicit, run_explicit_render])
@pytest.mark.parametrize(
    "source",
    [
        "await load_preview()\n",
        "async for item in items:\n    pass\n",
        "async with context:\n    pass\n",
    ],
)
def test_top_level_async_is_rejected_as_normal_module_in_v1(
    runner: Runner,
    source: str,
) -> None:
    result = runner(source)

    assert result.diagnostic.kind == "top_level_await"
    assert result.diagnostic.line == 1
    assert "normal Python module" in result.diagnostic.message


def test_async_function_definitions_remain_legal() -> None:
    result = run_implicit(
        "async def load_preview():\n    return '<p>async result</p>'\n'<p>definition accepted</p>'\n"
    )

    assert result.ok
    assert result.html == "<p>definition accepted</p>"


def test_playground_has_module_identity_and_does_not_run_main_guard() -> None:
    result = run_implicit("if __name__ == '__main__':\n    raise RuntimeError('main guard ran')\n__name__\n")

    assert result.ok
    assert result.html == "__playground__"


@pytest.mark.parametrize("statement", ["raise SystemExit(3)", "raise KeyboardInterrupt"])
def test_control_flow_exceptions_do_not_escape_the_runner(statement: str) -> None:
    result = run_implicit(f"{statement}\n")

    assert result.diagnostic.kind == "execution_stopped"
    assert result.diagnostic.filename == PLAYGROUND_FILENAME
    assert result.diagnostic.line == 1


def test_explicit_render_rejects_multiple_preview_calls() -> None:
    result = run_explicit_render("render('<p>first</p>')\nrender('<p>second</p>')\n")

    assert result.diagnostic.kind == "multiple_preview_calls"
    assert f'File "{PLAYGROUND_FILENAME}", line 2' in result.diagnostic.traceback


@pytest.mark.parametrize("starter", ALL_STARTERS, ids=lambda item: item.name)
def test_starter_candidates_render_with_current_citry(
    starter: StarterCandidate,
) -> None:
    result = run_implicit(starter.source)

    assert result.ok, result.diagnostic
    assert starter.expected_text in re.sub(r"\s+", " ", result.html)
    assert starter.next_link.startswith("/")


def test_card_starter_edits_change_python_data_and_css() -> None:
    starter = next(item for item in ALL_STARTERS if item.name == "Typed welcome card")
    edited_source = starter.source.replace("ada lovelace", "grace hopper").replace(
        "#6f42c1",
        "#0969da",
    )

    result = run_implicit(edited_source)

    assert result.ok, result.diagnostic
    normalized_html = re.sub(r"\s+", " ", result.html)
    assert "Welcome, <strong>Grace Hopper</strong>" in normalized_html
    assert "#0969da" in result.html
    assert "#6f42c1" not in result.html
