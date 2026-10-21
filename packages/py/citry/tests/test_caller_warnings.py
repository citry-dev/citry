"""
Render-time warnings point at the author's call, not at a line inside Citry.

Python prints a warning with the file and line it is attributed to. The
repeated-id warning and the `security_csp` / `security_javascript` "warn"
reports are raised deep inside serialization, and how many Citry frames sit
above them depends on whether the page was turned into HTML with `str()`,
`serialize()`, or another path. Each must still name the line that called
Citry.
"""

from __future__ import annotations

import inspect
import json
import subprocess
import sys
import warnings
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

import citry
from citry import Citry, Component, _caller_warnings
from citry._caller_warnings import warn_at_caller

if TYPE_CHECKING:
    from collections.abc import Callable


def _warning_sites(action: Callable[[], object]) -> list[tuple[str, str]]:
    """Run ``action`` and return each RuntimeWarning's file and the start of its message."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        action()
    return [(item.filename, str(item.message)[:40]) for item in caught if item.category is RuntimeWarning]


def _repeated_id_page() -> type[Component]:
    """Return a page component that writes the same id twice, so serializing it warns."""
    engine = Citry(autodiscover=False, mode="development")

    class Card(Component):
        citry = engine
        template = """
<article id="card">x</article>
"""

    class Page(Component):
        citry = engine
        template = """
<!doctype html>
<html><head><title>x</title></head><body><c-Card /><c-Card /></body></html>
"""

    return Page


def test_repeated_id_warning_names_the_callers_line_for_every_path() -> None:
    page = _repeated_id_page()
    rendered = page().render()
    for action in (lambda: str(rendered), rendered.serialize, lambda: page().render().serialize()):
        sites = _warning_sites(action)
        assert [filename for filename, _ in sites] == [__file__], sites


def test_javascript_policy_warning_names_the_callers_line() -> None:
    engine = Citry(autodiscover=False)
    # A fragment links its scripts by URL, which needs a mount prefix.
    engine.set_mounted_prefix("/citry")

    class Card(Component):
        citry = engine
        template = """
<main><button @click="save()">Save</button></main>
"""
        js = """
globalThis.cardReady = true;
"""

    rendered = Card().render()
    for strategy in ("document", "simple", "fragment"):
        sites = _warning_sites(partial(rendered.serialize, deps_strategy=strategy, security_javascript="warn"))
        assert sites, strategy
        assert {filename for filename, _ in sites} == {__file__}, (strategy, sites)


def test_csp_warning_names_the_callers_line() -> None:
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        template = """
<main><script>globalThis.raw = true;</script></main>
"""

    rendered = Card().render()
    sites = _warning_sites(lambda: rendered.serialize(deps_strategy="simple", security_csp="warn"))
    assert sites
    assert {filename for filename, _ in sites} == {__file__}, sites
    assert sites[0][1].startswith("Citry found")


def test_warn_at_caller_skips_every_citry_frame() -> None:
    # Called from outside the package, the helper's own frame is the only
    # Citry frame, so the warning lands on this line.
    with pytest.warns(UserWarning, match="from a test") as caught:
        warn_at_caller("from a test", UserWarning)
    assert caught[0].filename == __file__


def _runtime_warning_sites(action: Callable[[], object]) -> list[tuple[str, int]]:
    """Run ``action`` and return each RuntimeWarning's file and line."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        action()
    return [(item.filename, item.lineno) for item in caught if item.category is RuntimeWarning]


def test_warning_names_the_line_of_a_direct_call() -> None:
    rendered = _repeated_id_page()().render()

    def convert_with_str() -> None:
        str(rendered)

    def convert_with_serialize() -> None:
        rendered.serialize()

    for convert in (convert_with_str, convert_with_serialize):
        # The call is the first line of each function body.
        line = convert.__code__.co_firstlineno + 1
        assert _runtime_warning_sites(convert) == [(__file__, line)], convert.__name__


def test_warning_names_the_outermost_frame_when_every_frame_is_citrys(monkeypatch: pytest.MonkeyPatch) -> None:
    # Treat every file as Citry's own, as under the `citry` command, where
    # no frame belongs to the author.
    monkeypatch.setattr(_caller_warnings, "CITRY_PACKAGE_DIRS", ("",))
    outermost = inspect.currentframe()
    assert outermost is not None
    while outermost.f_back is not None:
        outermost = outermost.f_back
    with pytest.warns(UserWarning, match="no author frame") as caught:
        warn_at_caller("no author frame", UserWarning)
    # The walk stops at the frame that started the process, so the warning
    # still names a real file and line rather than Python's "sys" fallback.
    assert (caught[0].filename, caught[0].lineno) == (outermost.f_code.co_filename, outermost.f_lineno)


def test_warning_skips_citry_frames_imported_through_a_symlink(tmp_path: Path) -> None:
    # A frame names its file by the path Python imported it from, so a citry
    # imported through a symlinked directory (such as macOS `/tmp`) must still
    # count as Citry. A subprocess gets a fresh import from the linked path.
    linked = tmp_path / "linked"
    try:
        linked.symlink_to(Path(citry.__file__).resolve().parents[1], target_is_directory=True)
    except OSError:
        pytest.skip("this system cannot create a directory symlink")
    script = tmp_path / "author.py"
    script.write_text(
        f"""
import json
import sys
import warnings

sys.path.insert(0, {str(linked)!r})

from citry import Citry, Component

assert Citry.__module__ == "citry.citry"
assert sys.modules["citry"].__file__.startswith({str(linked)!r}), sys.modules["citry"].__file__

engine = Citry(autodiscover=False, mode="development")


class Card(Component):
    citry = engine
    template = "<article id='card'>x</article>"


class Page(Component):
    citry = engine
    template = "<html><head><title>x</title></head><body><c-Card /><c-Card /></body></html>"


rendered = Page().render()
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    str(rendered)
print(json.dumps([item.filename for item in caught if item.category is RuntimeWarning]))
""",
        encoding="utf-8",
    )
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout.strip().splitlines()[-1]) == [str(script)]
