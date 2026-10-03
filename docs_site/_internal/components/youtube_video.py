"""A responsive, privacy-enhanced, click-to-load YouTube embed."""

from __future__ import annotations

import re
from typing import Any

from citry import Component

_VIDEO_ID_RE = re.compile(r"[A-Za-z0-9_-]{11}")


class YoutubeVideo(Component):
    """``<c-youtube-video />`` renders a lazy-loaded YouTube player facade."""

    transparent = True

    class Kwargs:
        video_id: str
        title: str

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        video_id = str(kwargs.video_id)
        if _VIDEO_ID_RE.fullmatch(video_id) is None:
            msg = "YouTube video IDs must contain exactly 11 URL-safe characters"
            raise ValueError(msg)
        title = str(kwargs.title).strip()
        if not title:
            msg = "YouTube video titles must not be empty"
            raise ValueError(msg)
        return {
            "embed_url": f"https://www.youtube-nocookie.com/embed/{video_id}",
            "title": title,
            "watch_url": f"https://www.youtube.com/watch?v={video_id}",
        }

    template = """
      <figure
        class="youtube-video"
        c-data-youtube-embed-url="embed_url"
        c-data-youtube-title="title"
      >
        <button
          type="button"
          class="youtube-video__facade"
          data-youtube-load
          c-aria-label="'Play ' + title + ' on YouTube'"
        >
          <span class="youtube-video__play" aria-hidden="true">▶</span>
          <span>Play {{ title }}</span>
        </button>
        <figcaption class="youtube-video__caption">
          <a c-href="watch_url" target="_blank" rel="noopener">
            Watch the {{ title }} on YouTube
          </a>
        </figcaption>
      </figure>
    """
