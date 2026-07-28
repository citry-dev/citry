"""
Example discovery.

Each runnable example lives in ``examples/<name>/`` as a ``component.py`` (the
component being demonstrated) and a ``page.py`` (a ``<Name>Page`` component that
renders a full standalone page using it). The registry walks that directory,
imports both modules (registering their components), and finds the page class.

The tabbed card itself is the ``ExampleCard`` citry component
(``components/example_card.py``); the ``<c-example />`` directive looks up the
registry here and renders it.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, cast

from markupsafe import Markup, escape

from citry import Component
from docs_site._internal.config import config as default_config

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class ExampleInfo:
    name: str
    page_cls: type[Component]
    example_dir: Path
    # variant name -> a component class rendered as an HTML fragment. Empty unless
    # the example's component.py defines a module-level FRAGMENTS dict; the build
    # instantiates and pre-renders each variant below
    # examples/<public-slug>/demo/ and writes its dep files (see
    # build._pre_render_examples).
    fragments: dict[str, Any] = field(default_factory=dict)

    @property
    def public_slug(self) -> str:
        """The kebab-case URL segment shared by the recipe and its demo."""
        return self.name.replace("_", "-")


_registry: dict[str, ExampleInfo] | None = None
_PROJECTION_BLOCK_RE = re.compile(
    r"<!-- docs-example:(?P<name>[a-z0-9_-]+):start -->.*?"
    r"<!-- docs-example:(?P=name):end -->",
    re.DOTALL,
)


def get_example_registry() -> dict[str, ExampleInfo]:
    """Return the cached example registry, discovering on first call."""
    global _registry  # noqa: PLW0603
    if _registry is None:
        _registry = _discover_examples(default_config.examples_dir)
    return _registry


def get_example_by_slug(slug: str) -> ExampleInfo | None:
    """Return the example with this public URL slug, if one exists."""
    return next(
        (info for info in get_example_registry().values() if info.public_slug == slug),
        None,
    )


def _discover_examples(examples_dir: Path) -> dict[str, ExampleInfo]:
    registry: dict[str, ExampleInfo] = {}
    if not examples_dir.is_dir():
        return registry

    for example_dir in sorted(examples_dir.iterdir()):
        component_file = example_dir / "component.py"
        page_file = example_dir / "page.py"
        if not example_dir.is_dir() or not component_file.exists() or not page_file.exists():
            continue

        name = example_dir.name
        # Import the component first so the page's tags can resolve it.
        component_module = _import_module_file(component_file, name, "component")
        page_module = _import_module_file(page_file, name, "page")
        if page_module is None:
            continue

        page_cls = _find_page_class(page_module)
        if page_cls is not None:
            # A fragment demo declares `FRAGMENTS = {variant: <component element>}`.
            fragments = dict(getattr(component_module, "FRAGMENTS", {}) or {})
            registry[name] = ExampleInfo(name=name, page_cls=page_cls, example_dir=example_dir, fragments=fragments)

    return registry


def _find_page_class(module: object) -> type[Component] | None:
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if (
            isinstance(attr, type)
            and issubclass(attr, Component)
            and attr is not Component
            and attr_name.endswith("Page")
        ):
            return cast("type[Component]", attr)
    return None


def _import_module_file(py_file: Path, example_name: str, module_type: str) -> object | None:
    module_name = f"docs_site.examples.{example_name}.{module_type}"
    if module_name in sys.modules:
        return sys.modules[module_name]

    spec = importlib.util.spec_from_file_location(module_name, py_file)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def example_not_found(name: str) -> str:
    """Inline error shown when a ``<c-example />`` names an unknown example."""
    # escape() makes the interpolated name safe.
    return Markup(f'<p class="docs-error">Unknown example: {escape(name)}</p>')  # noqa: S704


def example_text_projection(info: ExampleInfo) -> str:
    """Return the concise Markdown projection of one executable example."""
    component = (info.example_dir / "component.py").read_text(encoding="utf-8").rstrip()
    page = (info.example_dir / "page.py").read_text(encoding="utf-8").rstrip()
    return (
        "### Component\n\n"
        f"````citry\n{component}\n````\n\n"
        "### Page\n\n"
        f"````citry\n{page}\n````\n\n"
        f"[Open the live result](/examples/{info.public_slug}/demo/)"
    )


def project_examples_for_text(source: str) -> str:
    """Replace rich example-card blocks with source-first Markdown."""
    registry = get_example_registry()

    def replace(match: re.Match[str]) -> str:
        name = match.group("name")
        info = registry.get(name)
        return match.group(0) if info is None else example_text_projection(info)

    return _PROJECTION_BLOCK_RE.sub(replace, source)
