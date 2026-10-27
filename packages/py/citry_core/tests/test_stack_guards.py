"""
Rust entry points start safely when Python has left little stack.

CPython lets a call into an extension through until only about 20 KiB of the
thread's stack is left, and a debug build's large frames can use more than
that before the first stack guard inside the work. So each Rust entry point
that does deep work runs its Rust work through the stack guard, which moves
that work to a new stack segment when little is left.

Each check runs in a separate interpreter on a 512 KiB thread (the macOS
default for a thread started outside Python). It nests C-level calls until
CPython refuses one, then backs off four levels at a time and calls the
entry point at each depth, so each call starts with a different amount of
stack, from CPython's limit up to plenty. A crash fails one test
instead of ending the pytest run. Only CPython 3.14 and later check the
real stack, so older versions could crash in the probe itself, and the
tests skip them.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 14), reason="only CPython 3.14 and later check the stack left before a call"
)

_HARNESS = """
import operator
import sys
import threading

sys.setrecursionlimit(1_000_000)


def at_depth(depth, work):
    # Each level is a C call, which uses the thread's own stack.
    if depth == 0:
        return work()
    return operator.call(at_depth, depth - 1, work)


def deepest():
    low, high = 0, 100_000
    while low < high:
        middle = (low + high + 1) // 2
        try:
            at_depth(middle, lambda: None)
        except RecursionError:
            high = middle - 1
        else:
            low = middle
    return low


def run():
    top = deepest()
    returned = []
    for back in range(0, 240, 4):
        try:
            at_depth(top - back, work)
        except (RecursionError, MemoryError):
            # CPython refused a call cleanly, which is fine.
            pass
        else:
            returned.append(back)
    # The closest call to CPython's limit that returned, so the test can check
    # that some call really started with little stack left.
    print("done", min(returned, default=-1))


threading.stack_size(512 * 1024)
thread = threading.Thread(target=run)
thread.start()
thread.join()
"""

_DEEP_TEMPLATE = (
    "''.join(f'<div c-for=\"row{level} in rows\">' for level in range(256))"
    " + '<div>' * 144 + '{{ n }}' + '</div>' * 144 + '</div>' * 256"
)

WORK = {
    "parse and compile": f"""
        from citry_core.template_parser import _compile_prepared_template, compile_template, parse_template

        source = {_DEEP_TEMPLATE}

        def work():
            template = parse_template(source)
            compile_template(template)
            _compile_prepared_template(template)
    """,
    "format": """
        from citry_core.template_formatter import format_template

        # Plain nesting: the formatter's time grows fast with nested
        # expressions, and this case calls it sixty times.
        source = "<div>" * 400 + "{{ n }}" + "</div>" * 400

        def work():
            format_template(source)
    """,
    "output check": """
        from citry_core.html_transform import _check_output_html

        source = "<div>" * 400 + "x" + "</div>" * 400

        def work():
            _check_output_html(
                source,
                pre_extension=False,
                csp=True,
                javascript=None,
                marker_prefix=None,
                trusted_tag_starts=set(),
                omit_handler_marker=None,
            )
    """,
}


@pytest.mark.parametrize("name", WORK)
def test_entry_points_start_with_little_stack_left(name: str) -> None:
    code = textwrap.dedent(WORK[name]) + _HARNESS
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    # Exit code 0 means no crash, and "done" means the loop finished.
    assert result.returncode == 0, result.stderr[-2000:]
    word, closest = result.stdout.split()
    assert word == "done", result.stderr[-2000:]
    # Each level of the probe uses about 0.7 KiB (measured on macOS arm64),
    # and CPython refuses a call with about 20 KiB left. So a call that
    # returned within 40 levels of the limit started with less than about
    # 50 KiB, below the guard's 100 KiB, and the guard had to move its work.
    assert 0 <= int(closest) <= 40, result.stdout
