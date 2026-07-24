"""
``VersionPicker`` - the header docs-version dropdown, as a Citry component.

Renders a native ``<select>`` seeded with the version the current page was built
as. The behavior (fetch ``versions.json``, list the other versions, redirect on
change) lives in ``static/js/site.js``, keyed off the ``data-version-picker``
attribute, the same markup-only plus site.js split the theme picker uses.

A native ``<select>`` is keyboard- and screen-reader-friendly for free, and it
degrades gracefully: with no version manifest to fetch (the single-version build),
the control just shows the current version and does nothing. site.js only fetches
a manifest when the page is under ``/v/<version>/`` or carries a
``data-versions-root`` attribute, neither of which a single-version build emits,
so it never requests a manifest that is not there.
"""

from __future__ import annotations

from citry import Component


class VersionPicker(Component):
    """The header version dropdown; behavior lives in site.js."""

    transparent = True

    class Kwargs:
        current_version: str = ""

    class Slots:
        pass

    template = """
      <c-if cond="current_version">
        <div
          class="djc-version-picker"
          data-version-picker
          c-data-current="current_version"
        >
          <select class="djc-version-picker__select" aria-label="Choose docs version">
            <option c-value="current_version" selected>{{ current_version }}</option>
          </select>
          <svg
            class="djc-version-picker__caret"
            viewBox="0 0 24 24"
            width="14"
            height="14"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>
      </c-if>
    """
