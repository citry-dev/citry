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
from docs_site._internal.config import config as default_config
from docs_site._internal.util import lstrip_outside_pre


class People(Component):
    """``<c-people group="maintainers" />`` renders the avatar grid for a people.yml group."""

    transparent = True

    class Kwargs:
        group: str

    class Slots:
        pass

    template = "{{ grid }}"

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        group = str(kwargs.group)
        people_path = default_config.base_dir / "data" / "people.yml"
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
        grid = lstrip_outside_pre(str(UserGrid(users=users, show_count=group == "contributors")))
        return {"grid": Markup(f"\n\n{grid}\n\n")}  # noqa: S704
