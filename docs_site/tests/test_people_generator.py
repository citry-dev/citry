"""
Tests for the people-data generator (``docs_site/scripts/people.py``).

The network call to GitHub is mocked, so these cover the logic that matters: the
cross-repository merge (a contributor to both citry and django-components is
counted once, with summed totals), the featured/contributor split, bot
filtering, and that the hand-emitted YAML round-trips through ``yaml.safe_load``
(which the ``<c-people />`` directive uses to read it back).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import yaml

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "people.py"


def _load() -> Any:
    spec = importlib.util.spec_from_file_location("people_script", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


people = _load()


def test_dump_yaml_round_trips() -> None:
    data = {
        "maintainers": [
            {"login": "JuroOravec", "avatarUrl": "https://a/x?u=1&v=4", "url": "https://github.com/JuroOravec"},
        ],
        "special_thanks": [
            {"login": "EmilStenstrom", "avatarUrl": "https://a/e?v=4", "url": "https://github.com/EmilStenstrom"},
        ],
        "contributors": [
            {"login": "alice", "avatarUrl": "https://a/y?v=4", "url": "https://github.com/alice", "count": 3},
        ],
    }
    # The '&' in the avatar URL and the integer count must survive the round-trip.
    dumped = people.dump_people_yaml(data)
    assert yaml.safe_load(dumped) == data
    assert dumped.index("maintainers:") < dumped.index("special_thanks:") < dumped.index("contributors:")


def test_empty_groups_emit_valid_yaml() -> None:
    data = {"maintainers": [], "special_thanks": [], "contributors": []}
    loaded = yaml.safe_load(people.dump_people_yaml(data))
    assert loaded == data


def test_collect_people_merges_repos_splits_maintainers_and_drops_bots(monkeypatch: Any) -> None:
    # Two repos. alice has a merged PR in each (should total 2). Juro and Emil
    # are featured separately. dependabot is a bot.
    by_repo = {
        ("citry-dev", "citry"): [
            {"login": "JuroOravec", "avatarUrl": "j", "url": "uj"},
            {"login": "EmilStenstrom", "avatarUrl": "e", "url": "ue"},
            {"login": "alice", "avatarUrl": "a", "url": "ua"},
        ],
        ("django-components", "django-components"): [
            {"login": "EmilStenstrom", "avatarUrl": "e", "url": "ue"},
            {"login": "alice", "avatarUrl": "a", "url": "ua"},
            {"login": "dependabot[bot]", "avatarUrl": "d", "url": "ud"},
        ],
    }
    monkeypatch.setattr(people, "_merged_pr_authors", lambda _token, owner, name: by_repo[(owner, name)])

    result = people.collect_people("token")

    assert [m["login"] for m in result["maintainers"]] == ["JuroOravec"]
    assert [m["login"] for m in result["special_thanks"]] == ["EmilStenstrom"]
    # Contributors exclude both featured groups and bots; alice's two repos sum to 2.
    assert {c["login"]: c["count"] for c in result["contributors"]} == {"alice": 2}
