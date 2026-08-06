"""
``<c-citry-mark />`` - the C3 logo, drawn in exactly one place.

The mark appears in the site header and again on every social-share card, and
those two want different things from it: the header sizes it from a stylesheet
and lets it inherit the theme's accent colour, while a card is screenshotted on
its own and has to state its size and colour outright. Both get them from the
same component, so the curves cannot drift apart.

The path data matches ``docs_site/static/img/citry-mark.svg``, which is the
artwork the favicons and the README logo are cut from. Change one and change the
other; ``docs_site/scripts/icons.py`` regenerates everything downstream of the
SVG file.
"""

from __future__ import annotations

from typing import Any

from citry import Component


class CitryMark(Component):
    """``<c-citry-mark />`` draws the C3 logo. The one place its geometry lives."""

    transparent = True

    class Kwargs:
        # Class the caller styles it through, for size and colour from its own
        # stylesheet. The header uses this; a standalone card does not.
        css_class: str = ""
        # Stroke colour. The default follows the caller's CSS ``color``, which is
        # what lets the header's accent token drive it.
        color: str = "currentColor"
        # Pixel size, for a caller with no stylesheet to size it from. Leave both
        # empty to let CSS do it.
        width: str = ""
        height: str = ""

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        # An empty value drops the attribute rather than rendering it blank, so a
        # caller that sizes the mark from CSS gets no width/height to fight with.
        return {
            "css_class": kwargs.css_class or None,
            "color": kwargs.color,
            "width": kwargs.width or None,
            "height": kwargs.height or None,
        }

    # Every place this is used already names the project in adjacent text, so the
    # mark is decorative and a screen reader should skip it.
    template = """
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0.5 13.5 83 73"
        fill="none"
        c-class="css_class"
        c-width="width"
        c-height="height"
        aria-hidden="true"
        focusable="false"
      >
        <g fill="none" c-stroke="color" stroke-linecap="round">
          <path d="M 47.2 32.4 A 15 15 0 1 1 62 50 A 15 15 0 1 1 47.2 67.6" stroke-width="11"/>
        </g>
        <g fill="none" c-stroke="color">
          <path d="M 48.9 28.7 A 26 26 0 1 0 48.9 71.3" stroke-width="13"/>
        </g>
      </svg>
    """
