"""Catalog-driven Citry UI overview links."""

from __future__ import annotations

from typing import Any

from citry import Component
from docs_site._internal.project import current_docs_project
from docs_site._internal.ui_library_projection import ui_library_overview_items


class UiLibraryList(Component):
    """Render the ordered component catalog without duplicating page metadata."""

    transparent = True

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        project = current_docs_project()
        return {
            "items": ui_library_overview_items(
                project.ui_library,
                repo_root=project.runtime.repo_root,
            )
        }

    template = """
      <ul>
        <li c-for="item in items">
          <a c-href="item['path']">{{ item['title'] }}</a> - {{ item['description'] }}
        </li>
      </ul>
    """
