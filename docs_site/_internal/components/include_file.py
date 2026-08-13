"""
The ``<c-include-file />`` tag: drop a repo file into a page as a fenced code
block, inferring the language from the file extension when one is not given.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any

from markupsafe import Markup

from citry import Component
from docs_site._internal.project import current_docs_project

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
    ".ftl": "fluent",
}


class IncludeFile(Component):
    """``<c-include-file path="..." language="..." />`` renders a file as a fenced code block."""

    transparent = True

    class Kwargs:
        path: str
        language: str = ""

    class Slots:
        pass

    template = "{{ block }}"

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        # A constant tag attribute arrives wrapped in citry's Const proxy; coerce
        # to a real str before handing it to pathlib (which type-checks).
        path = str(kwargs.path)
        text = (current_docs_project().runtime.repo_root / path).read_text(encoding="utf-8")
        language = str(kwargs.language) or _EXT_TO_LANGUAGE.get(PurePosixPath(path).suffix, "")
        # Markup so the fenced block reaches the markdown pass un-escaped; the
        # markdown pass then escapes the code inside the fence. Trusted: the
        # included file is one the page author named.
        return {
            "block": Markup(f"```{language}\n{text}\n```"),  # noqa: S704
        }
