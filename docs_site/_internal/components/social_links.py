"""
The project's social channels, and the icon row that links to them.

The channel definitions live here, while their destinations come from the
active ``DocsProject`` loaded from ``settings.yml``. ``<c-social-links />``
renders the row; pass ``variant`` to pick up a caller's own spacing and colour.
"""

from __future__ import annotations

from typing import Any

from markupsafe import Markup

from citry import Component
from docs_site._internal.project import current_docs_project
from docs_site._internal.util import flatten_for_markdown

# One entry per channel: the label a screen reader reads, the destination, and
# the single path that draws its mark.
_CHANNELS = (
    {
        "label": "GitHub",
        "url_key": "repository",
        "box": "0 0 16 16",
        "path": (
            "M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49"
            "-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 "
            "1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59"
            ".82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27"
            "1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 "
            "3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42"
            "-3.58-8-8-8z"
        ),
    },
    {
        "label": "PyPI",
        "url_key": "pypi",
        "box": "0 0 448 512",
        "path": (
            "M439.8 200.5c-7.7-30.9-22.3-54.2-53.4-54.2h-40.1v47.4c0 36.8-31.2 67.8-66.8 67.8H172.7c-29.2 "
            "0-53.4 25-53.4 54.3v101.8c0 29 25.2 46 53.4 54.3 33.8 9.9 66.3 11.7 106.8 0 26.9-7.8 53.4-23.5 "
            "53.4-54.3v-40.7H226.2v-13.6h160.2c31.1 0 42.6-21.7 53.4-54.2 11.2-33.5 10.7-65.7 0-108.6M286.2 "
            "444.7a20.4 20.4 0 1 1 0-40.7 20.4 20.4 0 1 1 0 40.7M167.8 248.1h106.8c29.7 0 53.4-24.5 "
            "53.4-54.3V91.9c0-29-24.4-50.7-53.4-55.6-35.8-5.9-74.7-5.6-106.8.1-45.2 8-53.4 24.7-53.4 "
            "55.6v40.7h106.9v13.6h-147c-31.1 0-58.3 18.7-66.8 54.2-9.8 40.7-10.2 66.1 0 108.6 7.6 31.6 25.7 "
            "54.2 56.8 54.2H101v-48.8c0-35.3 30.5-66.4 66.8-66.4m-6.6-183.4a20.4 20.4 0 1 1 0 40.8 20.4 20.4 "
            "0 1 1 0-40.8"
        ),
    },
    {
        "label": "Discord",
        "url_key": "discord",
        "box": "0 0 576 512",
        "path": (
            "M492.5 69.8c-.2-.3-.4-.6-.8-.7-38.1-17.5-78.4-30-119.7-37.1-.4-.1-.8 0-1.1.1s-.6.4-.8.8c-5.5 "
            "9.9-10.5 20.2-14.9 30.6-44.6-6.8-89.9-6.8-134.4 0-4.5-10.5-9.5-20.7-15.1-30.6-.2-.3-.5-.6-.8-.8"
            "s-.7-.2-1.1-.2C162.5 39 122.2 51.5 84.1 69c-.3.1-.6.4-.8.7C7.1 183.5-13.8 294.6-3.6 404.2c0 .3"
            ".1.5.2.8s.3.4.5.6c44.4 32.9 94 58 146.8 74.2.4.1.8.1 1.1 0s.7-.4.9-.7c11.3-15.4 21.4-31.8 "
            "30-48.8.1-.2.2-.5.2-.8s0-.5-.1-.8-.2-.5-.4-.6-.4-.3-.7-.4c-15.8-6.1-31.2-13.4-45.9-21.9-.3-.2"
            "-.5-.4-.7-.6s-.3-.6-.3-.9 0-.6.2-.9.3-.5.6-.7c3.1-2.3 6.2-4.7 9.1-7.1.3-.2.6-.4.9-.4s.7 0 1 .1"
            "c96.2 43.9 200.4 43.9 295.5 0 .3-.1.7-.2 1-.2s.7.2.9.4c2.9 2.4 6 4.9 9.1 7.2.2.2.4.4.6.7s.2.6"
            ".2.9-.1.6-.3.9-.4.5-.6.6c-14.7 8.6-30 15.9-45.9 21.8-.2.1-.5.2-.7.4s-.3.4-.4.7-.1.5-.1.8.1.5"
            ".2.8c8.8 17 18.8 33.3 30 48.8.2.3.6.6.9.7s.8.1 1.1 0c52.9-16.2 102.6-41.3 147.1-74.2.2-.2.4-.4"
            ".5-.6s.2-.5.2-.8c12.3-126.8-20.5-236.9-86.9-334.5zm-302 267.7c-29 0-52.8-26.6-52.8-59.2s23.4"
            "-59.2 52.8-59.2c29.7 0 53.3 26.8 52.8 59.2 0 32.7-23.4 59.2-52.8 59.2m195.4 0c-29 0-52.8-26.6"
            "-52.8-59.2s23.4-59.2 52.8-59.2c29.7 0 53.3 26.8 52.8 59.2 0 32.7-23.2 59.2-52.8 59.2"
        ),
    },
)


class SocialLinksMarkup(Component):
    """The icon row itself."""

    transparent = True

    class Kwargs:
        variant: str = ""

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        settings = current_docs_project().settings
        urls = {
            "repository": settings.repository.url,
            "pypi": settings.pypi_url,
            "discord": settings.discord_url,
        }
        channels = tuple({**channel, "url": urls[channel["url_key"]]} for channel in _CHANNELS)
        return {"channels": channels, "variant": str(kwargs.variant)}

    template = """
      <div c-class="'social-links ' + variant">
        <a
          c-for="channel in channels"
          class="social-links__link"
          c-href="channel['url']"
          c-aria-label="channel['label']"
          target="_blank"
          rel="noopener"
        >
          <svg
            c-viewBox="channel['box']"
            width="18"
            height="18"
            fill="currentColor"
            aria-hidden="true"
          >
            <path c-d="channel['path']" />
          </svg>
        </a>
      </div>
    """


class SocialLinks(Component):
    """``<c-social-links />`` places the icon row, flattened for the markdown pass."""

    transparent = True

    class Kwargs:
        variant: str = ""

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        markup = flatten_for_markdown(str(SocialLinksMarkup(variant=str(kwargs.variant))))
        return {"row": Markup(f"\n\n{markup}\n\n")}  # noqa: S704 - markup from this module

    template = """
      {{ row }}
    """
