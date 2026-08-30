"""Route published packages and build their Discord release payloads."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal, TypeAlias

if TYPE_CHECKING:
    from collections.abc import Sequence

DiscordChannel: TypeAlias = Literal["announcements", "development"]


class ReleaseNotificationError(ValueError):
    """A release cannot be routed or represented safely."""


@dataclass(frozen=True, slots=True)
class ReleaseRoute:
    """Assign one published package tag family to a Discord channel."""

    tag_prefix: str
    channel: DiscordChannel
    workflow: str


RELEASE_ROUTES = (
    ReleaseRoute("citry@", "announcements", "py--citry--publish.yml"),
    ReleaseRoute("citry-ui@", "announcements", "py--citry-ui--publish.yml"),
    ReleaseRoute("vscode-citry@", "announcements", "vscode--citry--publish.yml"),
    ReleaseRoute("citry-lsp@", "development", "py--citry-lsp--publish.yml"),
    ReleaseRoute("citry-core@", "development", "py--citry-core--publish.yml"),
    ReleaseRoute("pygments-citry@", "development", "py--pygments-citry--publish.yml"),
)

_DESCRIPTION_LIMIT = 4000
_TRUNCATION_SUFFIX = "\n\n_... see the release for the full notes._"


def route_release(tag: str) -> ReleaseRoute:
    """Return the explicit Discord route for one final release tag."""
    for route in RELEASE_ROUTES:
        if not tag.startswith(route.tag_prefix):
            continue
        version = tag.removeprefix(route.tag_prefix)
        # Citry's publish tag only stages PyPI bytes and creates no GitHub
        # Release, so it must never look like a community release.
        if not version or version.startswith("publish-") or any(character.isspace() for character in version):
            break
        return route
    msg = f"published release tag {tag!r} has no Discord channel route"
    raise ReleaseNotificationError(msg)


def discord_payload(release: object, *, repository: str) -> dict[str, object]:
    """Build the Discord webhook payload for one GitHub Release response."""
    if not isinstance(release, dict):
        msg = "GitHub Release data must be an object"
        raise ReleaseNotificationError(msg)

    tag = _required_text(release, "tagName")
    route_release(tag)
    name = _optional_text(release, "name") or tag
    url = _required_text(release, "url")
    timestamp = _required_text(release, "publishedAt")
    body = _optional_text(release, "body") or "Open the GitHub Release for package notes and artifacts."
    author = release.get("author")
    if not isinstance(author, dict):
        msg = "GitHub Release author must be an object"
        raise ReleaseNotificationError(msg)
    user = _required_text(author, "login")

    # Discord caps embed descriptions at 4096 characters. Keep a small margin
    # for the suffix so a long GitHub body cannot make the webhook reject it.
    if len(body) > _DESCRIPTION_LIMIT:
        body = f"{body[:_DESCRIPTION_LIMIT]}{_TRUNCATION_SUFFIX}"

    return {
        "username": "GitHub Releases",
        "avatar_url": "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png",
        "embeds": [
            {
                "title": f"🚀 New release: {name}",
                "url": url,
                "description": body,
                "color": 2664261,
                "author": {"name": user},
                "footer": {"text": repository},
                "timestamp": timestamp,
            }
        ],
    }


def _required_text(value: dict[object, object], field: str) -> str:
    found = value.get(field)
    if isinstance(found, str) and found:
        return found
    msg = f"GitHub Release field {field!r} must be a non-empty string"
    raise ReleaseNotificationError(msg)


def _optional_text(value: dict[object, object], field: str) -> str | None:
    found = value.get(field)
    if found is None or isinstance(found, str):
        return found
    msg = f"GitHub Release field {field!r} must be a string or null"
    raise ReleaseNotificationError(msg)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    route = subparsers.add_parser("route", help="print the Discord channel for a release tag")
    route.add_argument("tag")
    payload = subparsers.add_parser("payload", help="build a Discord payload from gh release JSON")
    payload.add_argument("release_json", type=Path)
    payload.add_argument("--repository", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the release router or payload builder."""
    args = _parser().parse_args(argv)
    if args.command == "route":
        sys.stdout.write(f"{route_release(args.tag).channel}\n")
        return 0

    release = json.loads(args.release_json.read_text(encoding="utf-8"))
    sys.stdout.write(f"{json.dumps(discord_payload(release, repository=args.repository), ensure_ascii=False)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
