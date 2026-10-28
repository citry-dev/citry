"""
The language server analyzes a template at the logic nesting limit within a fixed Python frame budget.

This is the editor's half of the frame budget test in
``packages/py/citry/tests/_frame_budget.py``. An editor can run the
language server inside a host that already uses part of Python's stack, so
each template is analyzed 200 frames deep, with Python's recursion limit
lowered to allow only 500 more frames. Several analysis steps catch
``RecursionError`` and quietly report less, so the diagnostics under the low
limit must equal the diagnostics under the normal one, not merely appear.

The analysis runs in a subprocess, so the lowered recursion limit never
reaches the pytest process. Like the citry half, it is a qualification
test that runs only on Linux, because frame counts depend on the Python
version, not the operating system; set ``CITRY_FRAME_BUDGET_ANY_OS=1`` to
run it elsewhere.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from citry import Citry, Component
from citry_core import _rust
from citry_lsp.catalog import CatalogIndex
from citry_lsp.engine import DocumentState
from citry_lsp.project import ProjectState
from citry_lsp.protocol import ProjectStatus

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import FrameType

# The logic nesting limit, read from the parser so the two cannot disagree.
LOGIC_LIMIT = _rust.template_parser._MAX_LOGIC_NESTING
# Frames the host holds below the language server.
HOST_FRAMES = 200
# Frames the analysis may use above the host.
BUDGET = 500

# Each template nests `LOGIC_LIMIT` logic levels and ends in a component
# nobody registered, so the analysis reports it only if it reaches the
# innermost level, and the comparison below has something to compare.
UNKNOWN = "<c-Nope />"
TEMPLATES: dict[str, str] = {
    "if_tags": '<c-if cond="flag">' * (LOGIC_LIMIT - 1) + UNKNOWN + "</c-if>" * (LOGIC_LIMIT - 1),
    # Each `<div c-if c-for>` is three levels, two of them logic: 127 of them
    # are 254 logic levels, and a `<c-if>` and the component make 256.
    "if_and_for_attributes": "".join(
        f'<div c-if="flag" c-for="x{level} in items">' for level in range((LOGIC_LIMIT - 2) // 2)
    )
    + '<c-if cond="flag">'
    + UNKNOWN
    + "</c-if>"
    + "</div>" * ((LOGIC_LIMIT - 2) // 2),
    # Each step is one logic level and one element, so this nests 511 tags
    # in all, and the component is the 512th.
    "if_tags_around_elements": '<c-if cond="flag"><div>' * (LOGIC_LIMIT - 1)
    + "<p>"
    + UNKNOWN
    + "</p>"
    + "</div></c-if>" * (LOGIC_LIMIT - 1),
}


def _project() -> ProjectState:
    """A project with one registered component, as the editor sees an application."""
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        template = """
            <article><c-slot /></article>
        """

    del Card
    catalog = CatalogIndex(engine.inspect_components(include_builtins=True).to_dict())
    return ProjectState(
        ProjectStatus(
            interpreter="python",
            workspace=str(Path.cwd()),
            app="app:engine",
            mode="registry",
            registry_ready=True,
            citry_version=catalog.citry_version,
            catalog_schema_version=catalog.schema_version,
        ),
        engine.template_analysis(),
        catalog,
    )


def _diagnostics(source: str, project: ProjectState) -> list[str]:
    document = DocumentState("file:///template.html", "citry-html", source, 1)
    document.update(source, 1, project)
    return sorted(f"{item.code}: {item.message}" for item in document.diagnostics)


def _stack_depth() -> int:
    depth = 0
    frame: FrameType | None = sys._getframe(1)
    while frame is not None:
        depth += 1
        frame = frame.f_back
    return depth


def _with_host_stack(work: Callable[[], Any]) -> Any:
    """Run `work` with `HOST_FRAMES` frames below it and `BUDGET` frames of room above."""

    def descend() -> Any:
        if _stack_depth() < HOST_FRAMES:
            return descend()
        limit = sys.getrecursionlimit()
        sys.setrecursionlimit(_stack_depth() + BUDGET)
        try:
            return work()
        finally:
            sys.setrecursionlimit(limit)

    return descend()


def _worker() -> None:
    """Analyze every template under the normal and the low limit, and print the results as JSON."""
    results: dict[str, Any] = {}
    for name, source in TEMPLATES.items():
        normal = _diagnostics(source, _project())
        try:
            low = _with_host_stack(lambda source=source: _diagnostics(source, _project()))
        except RecursionError as error:
            results[name] = {"error": f"RecursionError: {error}"}
            continue
        results[name] = {"same": low == normal, "diagnostics": normal}
    print(json.dumps(results))  # noqa: T201 - the parent test reads this


@pytest.mark.qualification
@pytest.mark.skipif(
    sys.platform != "linux" and os.environ.get("CITRY_FRAME_BUDGET_ANY_OS") != "1",
    reason="frame counts depend on the Python version, not the OS, so only the Linux jobs run this",
)
def test_the_logic_limit_fits_the_frame_budget_in_the_editor() -> None:
    result = subprocess.run(
        [sys.executable, __file__],
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )
    assert result.returncode == 0, result.stderr[-4000:]
    results: dict[str, Any] = json.loads(result.stdout.splitlines()[-1])
    over_budget = {name: entry["error"] for name, entry in results.items() if "error" in entry}
    assert not over_budget, over_budget
    changed = [name for name, entry in results.items() if not entry["same"]]
    assert not changed, f"diagnostics changed under the low recursion limit: {changed}"
    # The component at the innermost level is found in every template, so
    # the whole template was analyzed.
    unreached = [
        name
        for name, entry in results.items()
        if not any("unknown-component" in item for item in entry["diagnostics"])
    ]
    assert not unreached, unreached


if __name__ == "__main__":
    _worker()
