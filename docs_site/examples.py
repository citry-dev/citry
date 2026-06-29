"""
Example discovery, plus the ``ExampleCard`` HTML the ``<c-example />`` directive emits.

Each runnable example lives in ``examples/<name>/`` as a ``component.py`` (the
component being demonstrated) and a ``page.py`` (a ``<Name>Page`` component that
renders a full standalone page using it). The registry walks that directory,
imports both modules (registering their components), and finds the page class.

The card is a tabbed widget (live-demo iframe + the two source files,
Pygments-highlighted). It is built as a flush-left HTML string so the markdown
pass treats it as block HTML; the ``<label for>`` attributes rule out a pure
citry template (``for`` would collide with the ``c-for`` loop), so it is
assembled in Python.
"""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from markupsafe import Markup, escape
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer

from citry import Component
from docs_site.config import config as default_config

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class ExampleInfo:
    name: str
    page_cls: type[Component]
    example_dir: Path


_registry: dict[str, ExampleInfo] | None = None


def get_example_registry() -> dict[str, ExampleInfo]:
    """Return the cached example registry, discovering on first call."""
    global _registry  # noqa: PLW0603
    if _registry is None:
        _registry = _discover_examples(default_config.examples_dir)
    return _registry


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
        _import_module_file(component_file, name, "component")
        page_module = _import_module_file(page_file, name, "page")
        if page_module is None:
            continue

        page_cls = _find_page_class(page_module)
        if page_cls is not None:
            registry[name] = ExampleInfo(name=name, page_cls=page_cls, example_dir=example_dir)

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
    module_name = f"docs_site_examples.{example_name}.{module_type}"
    if module_name in sys.modules:
        return sys.modules[module_name]

    spec = importlib.util.spec_from_file_location(module_name, py_file)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def render_example_card(name: str, info: ExampleInfo) -> str:
    """Build the tabbed example card (live demo + the two source files)."""
    formatter = HtmlFormatter(cssclass="highlight", nowrap=False)
    lexer = PythonLexer()
    component_code = highlight((info.example_dir / "component.py").read_text(encoding="utf-8"), lexer, formatter)
    page_code = highlight((info.example_dir / "page.py").read_text(encoding="utf-8"), lexer, formatter)

    group = f"__tabbed_ex_{name}"
    demo_url = f"/examples/{name}/"
    # Flush-left so the markdown pass treats it as block HTML (md_in_html); the
    # Pygments <pre> blocks keep their own indentation.
    return (
        f'<div class="tabbed-set example-card" data-tabs="ex-{name}:3">\n'
        f'<input checked id="{group}_1" name="{group}" type="radio">\n'
        f'<input id="{group}_2" name="{group}" type="radio">\n'
        f'<input id="{group}_3" name="{group}" type="radio">\n'
        f'<div class="tabbed-labels">\n'
        f'<label for="{group}_1">Live demo</label>\n'
        f'<label for="{group}_2">Component</label>\n'
        f'<label for="{group}_3">Page</label>\n'
        f"</div>\n"
        f'<div class="tabbed-content">\n'
        f'<div class="tabbed-block tabbed-block--demo">'
        f'<iframe src="{demo_url}" class="example-demo-frame"'
        f' sandbox="allow-scripts allow-same-origin" loading="lazy"></iframe>'
        f"</div>\n"
        f'<div class="tabbed-block">{component_code}</div>\n'
        f'<div class="tabbed-block">{page_code}</div>\n'
        f"</div>\n"
        f"</div>"
    )


def example_not_found(name: str) -> str:
    """Inline error shown when a ``<c-example />`` names an unknown example."""
    # escape() makes the interpolated name safe.
    return Markup(f'<p class="docs-error">Unknown example: {escape(name)}</p>')  # noqa: S704
