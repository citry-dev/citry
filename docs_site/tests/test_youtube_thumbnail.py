"""Tests for the script that saves a YouTube thumbnail into the docs site."""

from __future__ import annotations

from pathlib import Path
from urllib.error import HTTPError

import pytest

from docs_site.scripts import youtube_thumbnail
from docs_site.scripts.youtube_thumbnail import fetch_thumbnail, save_thumbnail

VIDEO_ID = "d3nPqvDdNB0"
JPEG = b"\xff\xd8\xff\xe0 pretend picture \xff\xd9"


def _http_error(url: str, code: int) -> HTTPError:
    return HTTPError(url, code, "answer", {}, None)  # type: ignore[arg-type]


def test_fetch_prefers_the_largest_thumbnail() -> None:
    requested: list[str] = []

    def fetch(url: str) -> bytes:
        requested.append(url)
        return JPEG

    assert fetch_thumbnail(VIDEO_ID, fetch) == JPEG
    assert requested == [f"https://i.ytimg.com/vi/{VIDEO_ID}/maxresdefault.jpg"]


def test_fetch_falls_back_when_the_large_size_does_not_exist() -> None:
    requested: list[str] = []

    def fetch(url: str) -> bytes:
        requested.append(url)
        if "maxresdefault" in url:
            raise _http_error(url, 404)
        return JPEG

    assert fetch_thumbnail(VIDEO_ID, fetch) == JPEG
    assert requested[-1] == f"https://i.ytimg.com/vi/{VIDEO_ID}/hqdefault.jpg"


def test_fetch_reports_a_video_with_no_thumbnail() -> None:
    def fetch(url: str) -> bytes:
        raise _http_error(url, 404)

    with pytest.raises(LookupError, match="no thumbnail"):
        fetch_thumbnail(VIDEO_ID, fetch)


def test_fetch_stops_on_a_failure_that_is_not_a_missing_size() -> None:
    # A rate limit must not quietly save the smaller picture.
    def fetch(url: str) -> bytes:
        raise _http_error(url, 429)

    with pytest.raises(HTTPError):
        fetch_thumbnail(VIDEO_ID, fetch)


def test_fetch_rejects_an_answer_that_is_not_a_jpeg() -> None:
    with pytest.raises(ValueError, match="not a complete JPEG"):
        fetch_thumbnail(VIDEO_ID, lambda _url: b"<html>sign in</html>")


def test_fetch_rejects_a_download_that_was_cut_short() -> None:
    with pytest.raises(ValueError, match="not a complete JPEG"):
        fetch_thumbnail(VIDEO_ID, lambda _url: JPEG[:-2])


def test_fetch_rejects_a_malformed_video_id_before_any_request() -> None:
    def fetch(url: str) -> bytes:
        raise AssertionError(url)

    with pytest.raises(ValueError, match="exactly 11 URL-safe characters"):
        fetch_thumbnail("../not-an-id", fetch)


def test_save_writes_one_file_named_for_the_video(tmp_path: Path) -> None:
    target = save_thumbnail(VIDEO_ID, out_dir=tmp_path / "thumbs", fetch=lambda _url: JPEG)

    assert target == tmp_path / "thumbs" / f"{VIDEO_ID}.jpg"
    assert target.read_bytes() == JPEG


def test_save_keeps_an_existing_file_unless_told_to_replace_it(tmp_path: Path) -> None:
    (tmp_path / f"{VIDEO_ID}.jpg").write_bytes(b"old picture")

    with pytest.raises(FileExistsError, match="--replace"):
        save_thumbnail(VIDEO_ID, out_dir=tmp_path, fetch=lambda _url: JPEG)
    assert (tmp_path / f"{VIDEO_ID}.jpg").read_bytes() == b"old picture"

    save_thumbnail(VIDEO_ID, out_dir=tmp_path, replace=True, fetch=lambda _url: JPEG)
    assert (tmp_path / f"{VIDEO_ID}.jpg").read_bytes() == JPEG


def test_save_checks_for_an_existing_file_before_downloading(tmp_path: Path) -> None:
    (tmp_path / f"{VIDEO_ID}.jpg").write_bytes(b"old picture")

    def fetch(url: str) -> bytes:
        raise AssertionError(url)

    with pytest.raises(FileExistsError):
        save_thumbnail(VIDEO_ID, out_dir=tmp_path, fetch=fetch)


def test_main_prints_the_value_to_use_and_exits_cleanly(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    monkeypatch.setattr(youtube_thumbnail, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        youtube_thumbnail,
        "save_thumbnail",
        lambda video_id, **_options: tmp_path / f"{video_id}.jpg",
    )
    (tmp_path / f"{VIDEO_ID}.jpg").write_bytes(JPEG)

    assert youtube_thumbnail.main([VIDEO_ID]) == 0
    assert f'thumbnail="/static/img/video-thumbnails/{VIDEO_ID}.jpg"' in capsys.readouterr().out


def test_main_exits_with_an_error_when_the_download_fails(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fail(video_id: str, **_options: object) -> Path:
        raise LookupError(f"YouTube has no thumbnail for {video_id}")

    monkeypatch.setattr(youtube_thumbnail, "save_thumbnail", fail)

    assert youtube_thumbnail.main([VIDEO_ID]) == 2
    assert "no thumbnail" in capsys.readouterr().err
