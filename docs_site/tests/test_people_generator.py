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
from contextlib import nullcontext
from pathlib import Path
from typing import Any

import pytest
import yaml

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "people.py"


def _load() -> Any:
    spec = importlib.util.spec_from_file_location("people_script", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


people = _load()


def _write_sources(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def _valid_sources() -> str:
    return """\
repositories:
  - owner: citry-dev
    name: citry
  - owner: django-components
    name: django-components
maintainers:
  - JuroOravec
special_thanks:
  - EmilStenstrom
ignored_logins:
  - dependabot[bot]
"""


def test_load_people_sources_preserves_author_order(tmp_path: Path) -> None:
    path = _write_sources(tmp_path / "people_sources.yml", _valid_sources())

    sources = people.load_people_sources(path)

    assert [(repo.owner, repo.name) for repo in sources.repositories] == [
        ("citry-dev", "citry"),
        ("django-components", "django-components"),
    ]
    assert sources.maintainers == ("JuroOravec",)
    assert sources.special_thanks == ("EmilStenstrom",)
    assert sources.ignored_logins == frozenset({"dependabot[bot]"})


def test_site_repository_entry_uses_central_repository_identity(tmp_path: Path) -> None:
    path = _write_sources(
        tmp_path / "people_sources.yml",
        _valid_sources().replace("  - owner: citry-dev\n    name: citry", "  - site", 1),
    )

    sources = people.load_people_sources(
        path,
        site_repository=people.Repository("configured-owner", "configured-repo"),
    )

    assert sources.repositories[0] == people.Repository("configured-owner", "configured-repo")


@pytest.mark.parametrize(
    ("text", "field", "message"),
    [
        (_valid_sources() + "unexpected: true\n", "unexpected", "unknown key"),
        (_valid_sources().replace("maintainers:\n  - JuroOravec", "maintainers: JuroOravec"), "maintainers", "list"),
        (_valid_sources().replace("  - JuroOravec", "  - JuroOravec\n  - jurooravec"), "maintainers", "duplicate"),
        (
            _valid_sources().replace(
                "  - owner: django-components\n    name: django-components",
                "  - owner: CITRY-DEV\n    name: Citry",
            ),
            "repositories[1]",
            "duplicate",
        ),
        (_valid_sources().replace("  - EmilStenstrom", "  - jurooravec"), "special_thanks", "maintainers"),
        (_valid_sources().replace("    name: citry", "    repo: citry", 1), "repositories[0]", "unknown key"),
        (_valid_sources().replace("    name: citry", "    name: ''", 1), "repositories[0].name", "non-empty"),
        (
            _valid_sources().replace(
                "repositories:\n  - owner: citry-dev\n    name: citry\n"
                "  - owner: django-components\n    name: django-components",
                "repositories: []",
            ),
            "repositories",
            "at least one",
        ),
        (_valid_sources().replace("maintainers:\n  - JuroOravec", "maintainers: []"), "maintainers", "at least one"),
    ],
)
def test_load_people_sources_rejects_invalid_manifest(
    tmp_path: Path,
    text: str,
    field: str,
    message: str,
) -> None:
    path = _write_sources(tmp_path / "people_sources.yml", text)

    with pytest.raises(people.PeopleSourcesError) as exc_info:
        people.load_people_sources(path)

    error = str(exc_info.value)
    assert str(path) in error
    assert field in error
    assert message in error


@pytest.mark.parametrize(
    "value",
    ["", "two words", "owner/repo", "-citry", "citry-", "citry--dev", "x" * 40, 42, None, True],
)
def test_load_people_sources_rejects_malformed_repo_owner(tmp_path: Path, value: object) -> None:
    data = yaml.safe_load(_valid_sources())
    data["repositories"][0]["owner"] = value
    path = _write_sources(tmp_path / "people_sources.yml", yaml.safe_dump(data, sort_keys=False))

    with pytest.raises(people.PeopleSourcesError, match=r"repositories\[0\]\.owner"):
        people.load_people_sources(path)


@pytest.mark.parametrize("value", ["", "two words", "owner/repo", ".", "..", "x" * 101, 42, None, True])
def test_load_people_sources_rejects_malformed_repo_name(tmp_path: Path, value: object) -> None:
    data = yaml.safe_load(_valid_sources())
    data["repositories"][0]["name"] = value
    path = _write_sources(tmp_path / "people_sources.yml", yaml.safe_dump(data, sort_keys=False))

    with pytest.raises(people.PeopleSourcesError, match=r"repositories\[0\]\.name"):
        people.load_people_sources(path)


@pytest.mark.parametrize("login", ["two words", "owner/login", "bad--login", "x" * 40, "[bot]"])
def test_load_people_sources_rejects_malformed_login(tmp_path: Path, login: str) -> None:
    data = yaml.safe_load(_valid_sources())
    data["maintainers"][0] = login
    path = _write_sources(tmp_path / "people_sources.yml", yaml.safe_dump(data, sort_keys=False))

    with pytest.raises(people.PeopleSourcesError, match=r"maintainers\[0\]"):
        people.load_people_sources(path)


def test_load_people_sources_wraps_invalid_utf8(tmp_path: Path) -> None:
    path = tmp_path / "people_sources.yml"
    path.write_bytes(b"\xff")

    with pytest.raises(people.PeopleSourcesError) as exc_info:
        people.load_people_sources(path)

    assert str(path) in str(exc_info.value)
    assert "<file>" in str(exc_info.value)


def test_load_people_sources_rejects_duplicate_yaml_keys(tmp_path: Path) -> None:
    path = _write_sources(tmp_path / "people_sources.yml", _valid_sources() + "maintainers: []\n")

    with pytest.raises(people.PeopleSourcesError) as exc_info:
        people.load_people_sources(path)

    assert str(path) in str(exc_info.value)
    assert "<yaml>" in str(exc_info.value)
    assert "duplicate key" in str(exc_info.value)


def test_main_validates_sources_before_network_or_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    sources_path = _write_sources(tmp_path / "broken.yml", "repositories: []\n")
    output_path = tmp_path / "people.yml"
    output_path.write_text("keep me\n", encoding="utf-8")

    def fail_network(*_args: object, **_kwargs: object) -> None:
        pytest.fail("configuration must be validated before a network call")

    monkeypatch.setattr(people, "_merged_pr_authors", fail_network)
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.setattr(
        "sys.argv",
        ["people.py", "--sources", str(sources_path), "--output", str(output_path)],
    )

    assert people.main() == 2
    assert output_path.read_text(encoding="utf-8") == "keep me\n"
    assert str(sources_path) in capsys.readouterr().err


def test_graphql_reports_missing_configured_repository(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(people, "urlopen", lambda *_args, **_kwargs: nullcontext(object()))
    monkeypatch.setattr(people.json, "load", lambda _response: {"data": {"repository": None}})

    with pytest.raises(RuntimeError, match=r"citry-dev/missing.*not found"):
        people._graphql("token", {"owner": "citry-dev", "name": "missing", "after": None})


def test_main_reports_output_write_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    sources_path = _write_sources(tmp_path / "people_sources.yml", _valid_sources())
    monkeypatch.setattr(
        people,
        "collect_people",
        lambda *_args: {"maintainers": [], "special_thanks": [], "contributors": []},
    )
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.setattr(
        "sys.argv",
        ["people.py", "--sources", str(sources_path), "--output", str(tmp_path)],
    )

    assert people.main() == 2
    error = capsys.readouterr().err
    assert "could not write" in error
    assert str(tmp_path) in error


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


def test_dump_yaml_quotes_strings_that_yaml_would_reinterpret() -> None:
    data = {
        "maintainers": [{"login": "null", "avatarUrl": "https://a/# value", "url": "yes"}],
        "special_thanks": [],
        "contributors": [],
    }

    dumped = people.dump_people_yaml(data)

    assert yaml.safe_load(dumped) == data
    assert '- login: "null"' in dumped


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
            {"login": "alice", "avatarUrl": "a-new", "url": "ua-new"},
            {"login": "bob", "avatarUrl": "b", "url": "ub"},
            {"login": "bob", "avatarUrl": "b", "url": "ub"},
            {"login": "dependabot[bot]", "avatarUrl": "d", "url": "ud"},
        ],
    }
    monkeypatch.setattr(people, "_merged_pr_authors", lambda _token, owner, name: by_repo[(owner, name)])

    sources = people.PeopleSources(
        repositories=(
            people.Repository(owner="citry-dev", name="citry"),
            people.Repository(owner="django-components", name="django-components"),
        ),
        maintainers=("JuroOravec",),
        special_thanks=("EmilStenstrom",),
        ignored_logins=frozenset({"dependabot[bot]"}),
    )

    result = people.collect_people("token", sources)

    assert [m["login"] for m in result["maintainers"]] == ["JuroOravec"]
    assert [m["login"] for m in result["special_thanks"]] == ["EmilStenstrom"]
    # Contributors exclude both featured groups and bots. Tied totals retain
    # first-seen order, and a later repository supplies the current profile.
    assert result["contributors"] == [
        {"login": "alice", "avatarUrl": "a-new", "url": "ua-new", "count": 2},
        {"login": "bob", "avatarUrl": "b", "url": "ub", "count": 2},
    ]


def test_collect_people_matches_featured_and_ignored_logins_case_insensitively(monkeypatch: Any) -> None:
    authors = [
        {"login": "JuroOravec", "avatarUrl": "j", "url": "uj"},
        {"login": "Dependabot[bot]", "avatarUrl": "d", "url": "ud"},
    ]
    monkeypatch.setattr(people, "_merged_pr_authors", lambda *_args: authors)
    sources = people.PeopleSources(
        repositories=(people.Repository(owner="citry-dev", name="citry"),),
        maintainers=("jurooravec",),
        special_thanks=(),
        ignored_logins=frozenset({"dependabot[bot]"}),
    )

    result = people.collect_people("token", sources)

    assert result == {
        "maintainers": [{"login": "JuroOravec", "avatarUrl": "j", "url": "uj"}],
        "special_thanks": [],
        "contributors": [],
    }
