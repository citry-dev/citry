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


def test_youtube_video_without_thumbnail_keeps_the_plain_facade() -> None:
    rendered = html.fromstring(str(YoutubeVideo(video_id="d3nPqvDdNB0", title="Citry code-along")))
    button = rendered.xpath(".//button[@data-youtube-load]")[0]

    assert rendered.xpath(".//img") == []
    assert button.attrib["class"] == "youtube-video__facade"


def test_youtube_video_shows_a_thumbnail_served_by_this_site() -> None:
    thumbnail = "/static/img/video-thumbnails/d3nPqvDdNB0.jpg"
    rendered = html.fromstring(
        str(YoutubeVideo(video_id="d3nPqvDdNB0", title="Citry code-along", thumbnail=thumbnail))
    )
    button = rendered.xpath(".//button[@data-youtube-load]")[0]
    image = button.xpath(".//img")[0]

    assert button.attrib["class"] == "youtube-video__facade youtube-video__facade--thumbnail"
    assert image.attrib["src"] == thumbnail
    # The docs checks warn about an image with no alt text; the button's label
    # still names the action.
    assert image.attrib["alt"] == "Thumbnail of Citry code-along"
    assert (image.attrib["width"], image.attrib["height"]) == ("1280", "720")
    assert image.attrib["loading"] == "lazy"
    assert button.attrib["aria-label"] == "Play Citry code-along on YouTube"
    # The only file the box loads is the thumbnail, from this site, and no
    # player exists yet.
    assert rendered.xpath(".//iframe") == []
    assert rendered.xpath(".//@src") == [thumbnail]


@pytest.mark.parametrize(
    "thumbnail",
    [
        "https://i.ytimg.com/vi/d3nPqvDdNB0/maxresdefault.jpg",
        "//i.ytimg.com/vi/d3nPqvDdNB0/maxresdefault.jpg",
        "img/video-thumbnails/d3nPqvDdNB0.jpg",
        "/img/video-thumbnails/d3nPqvDdNB0.jpg",
    ],
)
def test_youtube_video_rejects_a_thumbnail_outside_this_site(thumbnail: str) -> None:
    with pytest.raises(ValueError, match="must start with /static/"):
        str(YoutubeVideo(video_id="d3nPqvDdNB0", title="Citry code-along", thumbnail=thumbnail))
