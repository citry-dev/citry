"""Tests for the authored-docs YouTube embed."""

import pytest
from lxml import html

from docs_site._internal.components.youtube_video import YoutubeVideo


def test_youtube_video_uses_click_to_load_facade_and_fallback_link() -> None:
    rendered = html.fromstring(str(YoutubeVideo(video_id="d3nPqvDdNB0", title="Citry code-along")))
    button = rendered.xpath(".//button[@data-youtube-load]")[0]
    link = rendered.xpath(".//figcaption/a")[0]

    assert rendered.xpath(".//iframe") == []
    assert rendered.attrib["data-youtube-embed-url"] == "https://www.youtube-nocookie.com/embed/d3nPqvDdNB0"
    assert rendered.attrib["data-youtube-title"] == "Citry code-along"
    assert button.attrib["aria-label"] == "Play Citry code-along on YouTube"
    assert "Play Citry code-along" in button.text_content()
    assert link.attrib == {
        "href": "https://www.youtube.com/watch?v=d3nPqvDdNB0",
        "target": "_blank",
        "rel": "noopener",
    }
    assert link.text_content().strip() == "Watch the Citry code-along on YouTube"


def test_youtube_video_rejects_invalid_video_id() -> None:
    with pytest.raises(
        ValueError,
        match="YouTube video IDs must contain exactly 11 URL-safe characters",
    ):
        str(YoutubeVideo(video_id="not/a/video", title="Invalid"))


def test_youtube_video_rejects_empty_accessible_title() -> None:
    with pytest.raises(ValueError, match="YouTube video titles must not be empty"):
        str(YoutubeVideo(video_id="d3nPqvDdNB0", title="  "))
