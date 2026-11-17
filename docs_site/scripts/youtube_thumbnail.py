# ruff: noqa: T201 - a maintenance script that prints its progress to stdout
r"""
Save a YouTube video's thumbnail as a file the docs site serves itself.

``<c-youtube-video>`` shows a play button until the visitor clicks it, and
loads nothing from YouTube or Google before that, so the embed stays
privacy-enhanced (no cookies and no visit to YouTube before the click). A
picture linked straight from ``i.ytimg.com`` (YouTube's image server) would
break that promise: the visitor's browser would contact Google when the page
loads.
This script downloads the picture once, and the repository keeps it as
``docs_site/static/img/video-thumbnails/<video id>.jpg``.

It asks for ``maxresdefault.jpg`` (1280 by 720) and falls back to
``hqdefault.jpg`` (480 by 360) when YouTube has no large version. Run it when
a video is added or re-recorded; a new recording has a new video id, so it gets
a new file::

    uv run --no-sync python \
      -m docs_site.scripts.youtube_thumbnail <video id>

Then pass the path it prints to the component::

    <c-youtube-video
      video_id="<video id>"
      title="..."
      thumbnail="/static/img/video-thumbnails/<video id>.jpg"
    />

The script refuses to replace a file that exists, because every docs version
loads images from the shared ``/static/`` folder and an old version may show
that picture. Pass ``--replace`` to overwrite one on purpose. See
``docs/codebase.md`` ("Add a video thumbnail").
"""

from __future__ import annotations

import argparse
import sys
from http.client import HTTPException
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from docs_site._internal.components.youtube_video import VIDEO_ID_RE

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
THUMBNAIL_DIR = REPO_ROOT / "docs_site" / "static" / "img" / "video-thumbnails"
# The site path the component's `thumbnail` argument takes, for a file in THUMBNAIL_DIR.
THUMBNAIL_URL_PREFIX = "/static/img/video-thumbnails/"

# Largest first. YouTube answers 404 for a size it never made, such as the 1280
# by 720 picture of a video uploaded at a lower resolution.
THUMBNAIL_URLS = (
    "https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
    "https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
)

# A complete JPEG file starts with the bytes ff d8 ff and ends with ff d9. An
# error page or a redirect to a login wall does not start that way, and a
# download cut short does not end that way, so neither is saved as a picture.
_JPEG_START = b"\xff\xd8\xff"
_JPEG_END = b"\xff\xd9"

_NOT_FOUND = 404


def download(url: str) -> bytes:
    """Fetch one URL, raising ``HTTPError`` when YouTube answers with an error such as 404."""
    request = Request(url, headers={"User-Agent": "citry-docs-thumbnail-script"})  # noqa: S310 - fixed https URL
    with urlopen(request, timeout=30) as response:  # noqa: S310
        return response.read()


def fetch_thumbnail(video_id: str, fetch: Callable[[str], bytes] = download) -> bytes:
    """
    Return the largest thumbnail YouTube has for a video, as JPEG bytes.

    Args:
        video_id: The 11-character YouTube video id.
        fetch: A function that downloads one URL; tests pass a fake so nothing touches the network.

    Raises:
        ValueError: The id is malformed, or an answer was not a complete JPEG.
        LookupError: YouTube has no thumbnail at any size.
        HTTPError: YouTube answered with an error other than 404, such as a rate limit.

    """
    # The id goes into a URL, so check its shape before building one.
    if VIDEO_ID_RE.fullmatch(video_id) is None:
        msg = f"YouTube video IDs must contain exactly 11 URL-safe characters, got {video_id!r}"
        raise ValueError(msg)
    for template in THUMBNAIL_URLS:
        try:
            data = fetch(template.format(video_id=video_id))
        except HTTPError as error:
            # Only "this size does not exist" moves on to a smaller one; any
            # other failure (rate limit, outage) must stop rather than save
            # a lower-quality picture by accident.
            if error.code != _NOT_FOUND:
                raise
            continue
        if not (data.startswith(_JPEG_START) and data.endswith(_JPEG_END)):
            msg = (
                f"the answer for {video_id} was not a complete JPEG image; "
                "try again, and save the picture by hand if it repeats"
            )
            raise ValueError(msg)
        return data
    msg = f"YouTube has no thumbnail for {video_id}; check the id and that the video is public"
    raise LookupError(msg)


def save_thumbnail(
    video_id: str,
    *,
    out_dir: Path = THUMBNAIL_DIR,
    replace: bool = False,
    fetch: Callable[[str], bytes] = download,
) -> Path:
    """
    Download a video's thumbnail into ``out_dir`` as ``<video_id>.jpg``.

    Args:
        video_id: The 11-character YouTube video id.
        out_dir: The folder to write into; tests pass a temporary folder.
        replace: Overwrite a file that already exists.
        fetch: A function that downloads one URL; tests pass a fake.

    Raises:
        ValueError: The id is malformed, or an answer was not a complete JPEG.
        LookupError: YouTube has no thumbnail at any size.
        HTTPError: YouTube answered with an error other than 404, such as a rate limit.
        FileExistsError: The file exists and ``replace`` is false.

    """
    target = out_dir / f"{video_id}.jpg"
    # An old docs version may show this picture, so replacing it is a decision.
    # Checking before the download reports this error even when offline.
    if target.exists() and not replace:
        msg = f"{target} already exists; pass --replace to overwrite it"
        raise FileExistsError(msg)
    data = fetch_thumbnail(video_id, fetch)
    out_dir.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return target


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Save a YouTube video's thumbnail into docs_site/static/img/video-thumbnails/."
    )
    parser.add_argument("video_id", help="the 11-character YouTube video id")
    parser.add_argument("--replace", action="store_true", help="overwrite the file if it already exists")
    args = parser.parse_args(argv)

    try:
        target = save_thumbnail(args.video_id, replace=args.replace)
    # URLError and HTTPException are a failed connection or a cut-off answer.
    except (ValueError, LookupError, FileExistsError, URLError, HTTPException, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {target.relative_to(REPO_ROOT)} ({target.stat().st_size} bytes)")
    print(f'use it as: thumbnail="{THUMBNAIL_URL_PREFIX}{args.video_id}.jpg"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
