"""
Deeply nested templates parse and compile on a small thread.

Three parts of the Rust code call themselves once per nesting level: the
compiler, the parser for a template written in an attribute value, and
printing the tree with `repr()`. Each of those runs through a stack guard
that moves the work to a new stack segment when the thread's own stack
runs low. The parser's other passes, and copying, comparing and freeing the
parsed tree, keep their own list of what is left to visit. Here templates
nested 512 tags deep (256 for control flow and components) are parsed and
compiled on a thread with a 128 KiB stack, the default for threads on musl
Linux.

The checks run in a separate interpreter, so a crash fails one test instead
of ending the pytest run.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

# Templates up to 512 tags deep: 512 for plain elements, 256 for control-flow
# and component tags.
SHAPES = {
    "elements": "'<div>' * 512 + '{{ x }}' + '</div>' * 512",
    "if_tags": "'<c-if cond=\"x\">' * 256 + '{{ x }}' + '</c-if>' * 256",
    "mixed": "'<c-if cond=\"x\"><div>' * 256 + '{{ x }}' + '</div></c-if>' * 256",
    "components": "'<c-my-comp>' * 256 + '{{ x }}' + '</c-my-comp>' * 256",
    "attribute_template": "'<c-my-tag c-body=\"' + '<div>' * 511 + '{{ x }}' + '</div>' * 511 + '\" />'",
}


@pytest.mark.parametrize("shape", SHAPES)
def test_deep_templates_parse_and_compile_on_a_small_thread(shape: str) -> None:
    code = f"""
        import threading

        from citry_core.template_parser import _compile_prepared_template, compile_template, parse_template

        source = {SHAPES[shape]}

        def work():
            template = parse_template(source)
            compile_template(template)
            _compile_prepared_template(template)
            # Reading a field copies the subtree it holds into Python, and
            # `==` and `repr()` walk the whole tree.
            template.elements
            assert template == template
            repr(template)
            del template
            print("done")

        threading.stack_size(128 * 1024)
        thread = threading.Thread(target=work)
        thread.start()
        thread.join()
    """
    result = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(code)],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    # Exit code 0 means no crash, and "done" means the work finished.
    assert result.returncode == 0, result.stderr[-2000:]
    assert result.stdout.strip() == "done", result.stderr[-2000:]


def test_an_invalid_expression_fails_cleanly_on_a_small_thread() -> None:
    # Reporting an invalid expression needs far more stack than parsing a
    # valid one.
    code = """
        import threading

        from citry_core.template_parser import parse_template

        def work():
            for source in ['{{ x + }}', '<c-x c-body="<div>{{ x + }}</div>" />']:
                try:
                    parse_template(source)
                except SyntaxError:
                    print("SyntaxError")

        threading.stack_size(128 * 1024)
        thread = threading.Thread(target=work)
        thread.start()
        thread.join()
    """
    result = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(code)],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    assert result.stdout.split() == ["SyntaxError", "SyntaxError"]
