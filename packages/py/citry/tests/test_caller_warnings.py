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

import warnings
from functools import partial
from typing import TYPE_CHECKING

import pytest

from citry import Citry, Component
from citry._caller_warnings import warn_at_caller

if TYPE_CHECKING:
    from collections.abc import Callable


def _warning_sites(action: Callable[[], object]) -> list[tuple[str, str]]:
    """Run ``action`` and return each RuntimeWarning's file and the start of its message."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        action()
    return [(item.filename, str(item.message)[:40]) for item in caught if item.category is RuntimeWarning]


def test_repeated_id_warning_names_the_callers_line_for_every_path() -> None:
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

    rendered = Page().render()
    for action in (lambda: str(rendered), rendered.serialize, lambda: Page().render().serialize()):
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
