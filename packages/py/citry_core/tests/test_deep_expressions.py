"""
Deep expressions fail with a clean error, never a crash.

The Rust passes over an expression's syntax tree call themselves once per
level, so an expression such as ``1+1+...+1`` or ``not not ... x`` with many
thousands of terms would overflow the stack. The parser rejects an expression
whose depth bound, counted from its tokens, is above 200 (about 97 chained
``+`` or 65 nested lists) with ``SyntaxError``, and a template that holds more
than 100,000 ``{`` characters the same way.

The 10,000-level cases run in a separate interpreter, so a crash fails one test
instead of ending the pytest run.
"""

from __future__ import annotations

import re
import subprocess
import sys
import textwrap

import pytest

from citry_core.safe_eval import safe_eval
from citry_core.template_formatter import TemplateFormatError, format_template
from citry_core.template_parser import parse_template

TOO_DEEP = "expression is nested too deeply"

# Shapes that overflow the stack without the depth check, each nesting `n` levels deep.
SHAPES = {
    "lists": lambda n: "[" * n + "]" * n,
    "additions": lambda n: "1" + "+1" * n,
    "not": lambda n: "not " * n + "x",
    "minus": lambda n: "-" * n + "1",
    "attributes": lambda n: "a" + ".b" * n,
    "conditionals": lambda n: "1 if x else " * n + "2",
}


def test_an_expression_within_the_limit_still_evaluates() -> None:
    # 60 nested lists stay under the limit, and Python evaluates them as usual.
    source = "[" * 60 + "]" * 60
    assert safe_eval(source)({}) == eval(source)  # noqa: S307 - a literal built above


@pytest.mark.parametrize("shape", SHAPES)
def test_a_too_deep_expression_raises_syntax_error(shape: str) -> None:
    expression = SHAPES[shape](150)
    with pytest.raises(SyntaxError, match=TOO_DEEP):
        safe_eval(expression)
    with pytest.raises(SyntaxError, match=TOO_DEEP):
        parse_template("{{ " + expression + " }}")
    with pytest.raises(TemplateFormatError, match=TOO_DEEP):
        format_template("<p>{{ " + expression + " }}</p>")


def test_too_many_braces_raise_syntax_error() -> None:
    braces = "{" * 100_000 + "}" * 100_000
    with pytest.raises(SyntaxError, match=re.escape("holds more than 100000 `{` characters")):
        parse_template("{{ " + braces + " }}")


def _run(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(code)],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )


# Deeply nested braces, plain and with each `}` inside a string. The template
# grammar skips a `}` in a string, so both open one grammar level per `{`.
BRACE_SHAPES = {
    "braces": "'{' * 10_000 + '}' * 10_000",
    "braces_closed_in_strings": "'{\"}\"' * 10_000 + '}' * 10_000",
}


@pytest.mark.parametrize("shape", [*SHAPES, *BRACE_SHAPES])
def test_ten_thousand_levels_fail_cleanly_in_every_entry_point(shape: str) -> None:
    builder = BRACE_SHAPES.get(shape) or repr(SHAPES[shape](10_000))
    result = _run(
        f"""
        from citry_core.safe_eval import safe_eval
        from citry_core.template_formatter import format_template
        from citry_core.template_parser import parse_template

        expression = {builder}
        calls = [
            lambda: safe_eval(expression),
            lambda: parse_template("{{{{ " + expression + " }}}}"),
            lambda: format_template("<p>{{{{ " + expression + " }}}}</p>"),
        ]
        for call in calls:
            try:
                call()
            except Exception as error:
                print(type(error).__name__)
            else:
                print("no error")
        """
    )
    # Exit code 0 means no crash. Each call must have raised a clean error.
    assert result.returncode == 0, result.stderr[-2000:]
    assert result.stdout.split() == ["SyntaxError", "SyntaxError", "TemplateFormatError"]


def test_the_limit_holds_on_a_small_python_thread() -> None:
    # A 256 KiB thread stack is smaller than the usual default. The deepest
    # list the parser accepts (65 levels) must still be parsed and formatted
    # there.
    result = _run(
        """
        import threading

        from citry_core.safe_eval import safe_eval
        from citry_core.template_formatter import format_template
        from citry_core.template_parser import parse_template

        def work():
            expression = "[" * 65 + "]" * 65
            safe_eval(expression)
            parse_template("{{ " + expression + " }}")
            format_template("<p>{{ " + expression + " }}</p>")
            print("done")

        threading.stack_size(256 * 1024)
        thread = threading.Thread(target=work)
        thread.start()
        thread.join()
        """
    )
    assert result.returncode == 0, result.stderr[-2000:]
    assert result.stdout.strip() == "done"
