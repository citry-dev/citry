"""A responsive, privacy-enhanced, click-to-load YouTube embed."""

from __future__ import annotations

import re
from typing import Any

from citry import Component

# Also read by docs_site/scripts/youtube_thumbnail.py, so both reject the same ids.
VIDEO_ID_RE = re.compile(r"[A-Za-z0-9_-]{11}")

# Where a thumbnail must live. The page loads nothing from YouTube or Google
# before the visitor clicks, so a thumbnail is a file this site serves itself;
# `docs_site/scripts/youtube_thumbnail.py` downloads one into
# docs_site/static/img/video-thumbnails/.
_THUMBNAIL_PREFIX = "/static/"


class YoutubeVideo(Component):
    """
    ``<c-youtube-video />`` shows a play button that loads the YouTube player only when clicked.

    Clicking the button swaps in YouTube's privacy-enhanced player
    (``youtube-nocookie.com``), so the page loads nothing from YouTube or
    Google until then. Give it a ``thumbnail`` to show the video's own picture
    behind the play button instead of a plain dark box.
    """

    transparent = True

    class Kwargs:
        video_id: str
        title: str
        # A path under /static/ to a picture of the video, such as
        # "/static/img/video-thumbnails/<video id>.jpg". The box is 16:9, and a
        # 4:3 picture is cropped to fit. Empty shows the plain dark box, so a
        # video can ship before its thumbnail does.
        thumbnail: str = ""

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        video_id = str(kwargs.video_id)
        if VIDEO_ID_RE.fullmatch(video_id) is None:
            msg = "YouTube video IDs must contain exactly 11 URL-safe characters"
            raise ValueError(msg)
        title = str(kwargs.title).strip()
        if not title:
            msg = "YouTube video titles must not be empty"
            raise ValueError(msg)
        thumbnail = str(kwargs.thumbnail).strip()
        # A remote address would make the visitor's browser contact that site
        # when the page loads, which is the leak the click-to-load box exists
        # to prevent. A path that starts with /static/ stays on this site.
        if thumbnail and not thumbnail.startswith(_THUMBNAIL_PREFIX):
            msg = (
                f"<c-youtube-video> thumbnail {thumbnail!r} must start with {_THUMBNAIL_PREFIX}: "
                "a picture from another site would contact that site when the page loads. "
                "Save one with: python -m docs_site.scripts.youtube_thumbnail <video id>"
            )
            raise ValueError(msg)
        return {
            "embed_url": f"https://www.youtube-nocookie.com/embed/{video_id}",
            # The picture styles apply only to a box that holds one, so an
            # older docs version that shares this stylesheet keeps its look.
            "facade_class": (
                "youtube-video__facade youtube-video__facade--thumbnail" if thumbnail else "youtube-video__facade"
            ),
            "thumbnail": thumbnail,
            "thumbnail_alt": f"Thumbnail of {title}",
            "title": title,
            "watch_url": f"https://www.youtube.com/watch?v={video_id}",
        }

    # The button's `aria-label` already names the action and a button's
    # children are not read separately, so the alt text is for the docs
    # checks (every image needs one) and for a browser that cannot show the
    # file. The width and height are the size of the large picture; the CSS
    # makes the image fill the box, so they do not change the layout.
    template = """
      <figure
        class="youtube-video"
        c-data-youtube-embed-url="embed_url"
        c-data-youtube-title="title"
      >
        <button
          type="button"
          c-class="facade_class"
          data-youtube-load
          c-aria-label="'Play ' + title + ' on YouTube'"
        >
          <c-if cond="thumbnail">
            <img
              class="youtube-video__thumbnail"
              c-src="thumbnail"
              c-alt="thumbnail_alt"
              width="1280"
              height="720"
              loading="lazy"
              decoding="async"
            >
          </c-if>
          <span class="youtube-video__play" aria-hidden="true">▶</span>
          <span class="youtube-video__label">Play {{ title }}</span>
        </button>
        <figcaption class="youtube-video__caption">
          <a c-href="watch_url" target="_blank" rel="noopener">
            Watch the {{ title }} on YouTube
          </a>
        </figcaption>
      </figure>
    """
