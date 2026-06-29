"""
Pass 1: the authoring directives, and the render that expands them.

Authors write directives as citry tags in their markdown - ``<c-version />``,
``<c-include-file path="..." />`` - and ``expand_directives`` renders the page
body as a citry template so those tags turn into HTML before the markdown pass.
This is the citry equivalent of the upstream Django ``{% example %}`` /
``{% version %}`` template tags.

The directives are ordinary citry components, registered on import. Each is
``transparent`` so it adds no ``data-cid`` marker to the expanded markdown.

Still to add: ``<c-example />`` (the live example widget), ``<c-docstring />``
(API reference), ``<c-image />``, and ``<c-people />``.
"""

from __future__ import annotations

import itertools
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _package_version
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Any

from markupsafe import Markup

from citry import Component
from citry import citry as default_citry
from docs_site.config import config as default_config
from docs_site.examples import example_not_found, get_example_registry, render_example_card

if TYPE_CHECKING:
    from citry import Citry

# A fresh content-component class per render gets a unique registered name, so
# concurrent or repeated renders never collide; it is unregistered right after.
_content_counter = itertools.count()

_EXT_TO_LANGUAGE = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".html": "html",
    ".css": "css",
    ".sh": "sh",
    ".toml": "toml",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".json": "json",
    ".rs": "rust",
}


class _Version(Component):
    """``<c-version />`` renders the installed citry version."""

    name = "version"
    transparent = True
    template = "{{ value }}"

    def template_data(self, kwargs: Any, slots: Any | None = None) -> dict[str, Any]:  # noqa: ARG002
        try:
            value = _package_version("citry")
        except PackageNotFoundError:
            value = ""
        return {"value": value}


class _IncludeFile(Component):
    """``<c-include-file path="..." language="..." />`` renders a file as a fenced code block."""

    name = "include-file"
    transparent = True
    template = "{{ block }}"

    class Kwargs:
        path: str
        language: str = ""

    def template_data(self, kwargs: Any, slots: Any | None = None) -> dict[str, Any]:  # noqa: ARG002
        # A constant tag attribute arrives wrapped in citry's Const proxy; coerce
        # to a real str before handing it to pathlib (which type-checks).
        path = str(kwargs.path)
        text = (default_config.repo_root / path).read_text(encoding="utf-8")
        language = str(kwargs.language) or _EXT_TO_LANGUAGE.get(PurePosixPath(path).suffix, "")
        # Markup so the fenced block reaches the markdown pass un-escaped; the
        # markdown pass then escapes the code inside the fence. Trusted: the
        # included file is one the page author named.
        return {"block": Markup(f"```{language}\n{text}\n```")}  # noqa: S704


class _Example(Component):
    """``<c-example name="..." />`` renders the live example card (demo + source)."""

    name = "example"
    transparent = True
    template = "{{ card }}"

    class Kwargs:
        name: str

    def template_data(self, kwargs: Any, slots: Any | None = None) -> dict[str, Any]:  # noqa: ARG002
        example_name = str(kwargs.name)
        info = get_example_registry().get(example_name)
        if info is None:
            return {"card": example_not_found(example_name)}
        # Blank lines around the flush-left card so the markdown pass treats it
        # as block HTML rather than indented text. Trusted: built from the
        # example's own source plus Pygments output.
        return {"card": Markup(f"\n\n{render_example_card(example_name, info)}\n\n")}  # noqa: S704


def expand_directives(
    body: str,
    *,
    citry_instance: Citry | None = None,
    context: dict[str, Any] | None = None,
) -> str:
    """
    Render ``body`` as a citry template, expanding the docs directives.

    ``body`` should already have its code protected (see
    ``fence_protection.protect_fences``). ``context`` supplies any bare
    ``{{ ... }}`` values the page uses outside directives.
    """
    citry_instance = citry_instance or default_citry
    page_context = context or {}

    content_cls = type(
        "DocsContent",
        (Component,),
        {
            "citry": citry_instance,
            "name": f"docs-content-{next(_content_counter)}",
            "transparent": True,
            "template": body,
            "template_data": lambda self, kwargs, slots=None: page_context,  # noqa: ARG005
        },
    )
    try:
        return str(content_cls())
    finally:
        citry_instance.unregister(content_cls)
