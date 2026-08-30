"""Contracts for routing package releases to Discord."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from scripts.discord_release import (  # noqa: E402
    RELEASE_ROUTES,
    ReleaseNotificationError,
    discord_payload,
    main,
    route_release,
)


@pytest.mark.parametrize(
    ("tag", "channel"),
    [
        ("citry@0.4.5", "announcements"),
        ("citry-ui@0.3.0", "announcements"),
        ("vscode-citry@0.1.2", "announcements"),
        ("citry-lsp@0.1.3", "development"),
        ("citry-core@1.7.0", "development"),
        ("pygments-citry@0.2.1", "development"),
    ],
)
def test_release_tags_have_explicit_channels(tag: str, channel: str) -> None:
    assert route_release(tag).channel == channel


@pytest.mark.parametrize("tag", ["citry@publish-0.4.5", "citry@", "unknown@1.0.0", "citry@0.4.5 bad"])
def test_non_final_or_unclassified_tags_fail_closed(tag: str) -> None:
    with pytest.raises(ReleaseNotificationError, match="no Discord channel route"):
        route_release(tag)


def test_every_route_owns_one_distinct_publisher() -> None:
    assert len({route.tag_prefix for route in RELEASE_ROUTES}) == len(RELEASE_ROUTES)
    assert len({route.workflow for route in RELEASE_ROUTES}) == len(RELEASE_ROUTES)


def test_payload_preserves_release_identity_and_notes() -> None:
    payload = discord_payload(
        {
            "tagName": "citry@0.4.5",
            "name": "Citry 0.4.5",
            "url": "https://github.com/citry-dev/citry/releases/tag/citry%400.4.5",
            "body": "Release notes.",
            "author": {"login": "github-actions[bot]"},
            "publishedAt": "2026-08-30T18:00:00Z",
        },
        repository="citry-dev/citry",
    )

    assert payload["username"] == "GitHub Releases"
    embed = payload["embeds"][0]
    assert embed == {
        "title": "🚀 New release: Citry 0.4.5",
        "url": "https://github.com/citry-dev/citry/releases/tag/citry%400.4.5",
        "description": "Release notes.",
        "color": 2664261,
        "author": {"name": "github-actions[bot]"},
        "footer": {"text": "citry-dev/citry"},
        "timestamp": "2026-08-30T18:00:00Z",
    }


def test_payload_truncates_long_release_notes() -> None:
    payload = discord_payload(
        {
            "tagName": "citry-lsp@0.1.3",
            "name": None,
            "url": "https://example.com/release",
            "body": "x" * 5000,
            "author": {"login": "publisher"},
            "publishedAt": "2026-08-30T18:00:00Z",
        },
        repository="citry-dev/citry",
    )

    embed = payload["embeds"][0]
    assert embed["title"] == "🚀 New release: citry-lsp@0.1.3"
    assert embed["description"].startswith("x" * 4000)
    assert embed["description"].endswith("see the release for the full notes._")


def test_cli_builds_payload_from_gh_release_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    release_json = tmp_path / "release.json"
    release_json.write_text(
        json.dumps(
            {
                "tagName": "vscode-citry@0.1.2",
                "name": "vscode-citry@0.1.2",
                "url": "https://example.com/release",
                "body": None,
                "author": {"login": "publisher"},
                "publishedAt": "2026-08-30T18:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    assert main(["payload", str(release_json), "--repository", "citry-dev/citry"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["embeds"][0]["description"] == "Open the GitHub Release for package notes and artifacts."
