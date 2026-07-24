"""
Example-page contract guard.

Checks that each runnable example directory under ``examples/`` ships both a
``component.py`` and a ``page.py``, registered a usable page class, and carries
at least one ``test_example_*.py`` regression test, and that every
``<c-example name="X" />`` directive in the markdown names a real example.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from docs_site._internal.guards.base import GuardResult
from docs_site._internal.guards.fence_validator import _source_files

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.examples import ExampleInfo
    from docs_site._internal.guards.base import GuardContext

# Matches a `<c-example name="X"` directive opening; captures the example name.
_EXAMPLE_RE = re.compile(r"""<c-example\s+name=["'](?P<name>[^"']+)["']""")


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    # The registry is built by example autodiscovery; without it there is
    # nothing to validate against, so do nothing.
    if ctx.example_registry is None:
        return
    registry: dict[str, ExampleInfo] = ctx.example_registry

    # Each example directory must ship both files and register a page class.
    if ctx.examples_dir.is_dir():
        for example_dir in sorted(ctx.examples_dir.iterdir()):
            if not example_dir.is_dir():
                continue
            component_file = example_dir / "component.py"
            page_file = example_dir / "page.py"
            # Only directories that look like examples (have at least one of the
            # two contract files) are held to the contract.
            if not component_file.exists() and not page_file.exists():
                continue

            name = example_dir.name
            source = str(example_dir)

            for required, present in (("component.py", component_file.exists()), ("page.py", page_file.exists())):
                if not present:
                    yield GuardResult.error(
                        guard="example_contract",
                        message=f"Example {name!r} is missing required file: {required}",
                        source=source,
                    )

            info = registry.get(name)
            if info is None or info.page_cls is None:
                yield GuardResult.error(
                    guard="example_contract",
                    message=f"Example {name!r} has no *Page component in page.py",
                    source=source,
                )

            # An example that follows the contract also ships at least one
            # per-example test (test_example_*.py in the example directory), so
            # its rendered demo keeps a regression guard of its own.
            if not any(example_dir.glob("test_example_*.py")):
                yield GuardResult.error(
                    guard="example_contract",
                    message=f"Example {name!r} has no test_example_*.py file",
                    source=source,
                )

    # Every `<c-example name="X" />` in the markdown must name a real example.
    for label, text in _source_files(ctx):
        for match in _EXAMPLE_RE.finditer(text):
            name = match.group("name")
            if name not in registry:
                yield GuardResult.error(
                    guard="example_contract",
                    message=f"Example {name!r} referenced by <c-example> is not a registered example",
                    source=label,
                )
