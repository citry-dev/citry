"""
``<c-advisory-watch part="..." />`` prints one piece of the landing page's
advisory section: the intro sentence, the graphic, or the note under it.

The README shows the same section, with the graphic as two SVG files (see
``docs_site/scripts/advisory_watch.py``). Both places build every piece from
the same functions and the same data file, so the numbers and sentences
cannot differ. The heading and the link are written in both places; the
``readme_advisory_watch`` validator checks that the headings match. On the landing page the graphic is inline SVG coloured by the site's
CSS variables, so the theme toggle recolours it; a ``<picture>`` would follow
only the reader's system setting.
"""

from __future__ import annotations

from typing import Any, Literal

from markupsafe import Markup

from citry import Component
from docs_site.scripts import advisory_watch


class AdvisoryWatch(Component):
    """``<c-advisory-watch part="chart" />``; see the module docstring."""

    transparent = True

    class Kwargs:
        # "intro" and "note" are plain sentences; "chart" is the inline SVG.
        part: Literal["intro", "chart", "note"]

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        data = advisory_watch.load_data()
        # Bad data fails the docs build here, as it fails the README script.
        advisory_watch.check_data(data)
        part = str(kwargs.part)
        if part == "intro":
            return {"content": advisory_watch.intro(data)}
        if part == "note":
            return {"content": advisory_watch.note(data)}
        # The SVG is built from the checked-in data file, with every project
        # name escaped, so it is safe to insert as markup. Blank lines keep
        # the Markdown pass from joining it to a neighbouring paragraph.
        svg = advisory_watch.inline_svg(data)
        return {"content": Markup(f'\n\n<div class="landing-advisories">{svg}</div>\n\n')}  # noqa: S704

    template = """
      {{ content }}
    """
