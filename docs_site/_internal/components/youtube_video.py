"""A responsive, privacy-enhanced YouTube embed for authored docs pages."""

from __future__ import annotations

import re
from typing import Any

from citry import Component

_VIDEO_ID_RE = re.compile(r"[A-Za-z0-9_-]{11}")


class YoutubeVideo(Component):
    """``<c-youtube-video />`` renders a lazy-loaded YouTube player."""

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
      <figure class="youtube-video">
        <iframe
          class="youtube-video__frame"
          c-src="embed_url"
          c-title="title"
          loading="lazy"
          referrerpolicy="strict-origin-when-cross-origin"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          allowfullscreen
        ></iframe>
        <figcaption class="youtube-video__caption">
          <a c-href="watch_url" target="_blank" rel="noopener">
            Watch the {{ title }} on YouTube
          </a>
        </figcaption>
      </figure>
    """
