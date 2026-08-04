"""
The ``<c-people />`` tag: render the avatar grid (``UserGrid``) for a group of
people from ``data/people.yml``.
"""

from __future__ import annotations

from typing import Any

import yaml
from markupsafe import Markup, escape

from citry import Component
from docs_site._internal.components.user_grid import UserGrid
from docs_site._internal.project import current_docs_project
from docs_site._internal.util import flatten_for_markdown


class People(Component):
    """``<c-people group="maintainers" />`` renders the avatar grid for a people.yml group."""

    transparent = True

    class Kwargs:
        group: str
        # Contributor counts belong on the People page; a page that only
        # acknowledges the group can drop them with a bare `plain` attribute.
        plain: bool = False
        # `avatars` reduces the grid to circular portraits: no handle, no link.
        # Use it where the group is an acknowledgment rather than a directory.
        avatars: bool = False

    class Slots:
        pass

    template = "{{ grid }}"

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        group = str(kwargs.group)
        people_path = current_docs_project().runtime.base_dir / "data" / "people.yml"
        if not people_path.is_file():
            return {
                "grid": Markup(  # noqa: S704
                    f'<p class="docs-error">People data not found: {escape(str(people_path))}</p>'
                ),
            }
        data = yaml.safe_load(people_path.read_text(encoding="utf-8")) or {}
        users = data.get(group)
        if users is None:
            return {
                "grid": Markup(  # noqa: S704
                    f'<p class="docs-error">Unknown people group: {escape(group)}</p>'
                ),
            }

        # Render the grid, flush it left (outside <pre>) so the markdown pass treats
        # it as block HTML, and pad with blank lines. Trusted: our own people.yml.
        avatars_only = bool(kwargs.avatars)
        show_count = group == "contributors" and not bool(kwargs.plain) and not avatars_only
        grid = flatten_for_markdown(
            str(
                UserGrid(
                    users=users,
                    show_count=show_count,
                    show_name=not avatars_only,
                    link=not avatars_only,
                ),
            ),
        )
        return {"grid": Markup(f"\n\n{grid}\n\n")}  # noqa: S704
