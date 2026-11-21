"""The workflow action pin validator rejects actions named by a movable tag."""

from pathlib import Path

import pytest
from scripts.validators import workflow_action_pins

_SHA = "3d3c42e5aac5ba805825da76410c181273ba90b1"
_ADVICE = (
    "pin the action or reusable workflow to its full lowercase commit SHA "
    "with the tag as a comment, such as `@<40-hex sha> # v7`"
)


def _check(tmp_path: Path, text: str, *, where: str = "workflows/ci.yml") -> list[str]:
    path = tmp_path / ".github" / where
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return workflow_action_pins.check(tmp_path)


def _steps(*steps: str) -> str:
    return "jobs:\n  test:\n    steps:\n" + "".join(f"      {step}\n" for step in steps)


@pytest.mark.parametrize(
    "step",
    [
        f"- uses: actions/checkout@{_SHA} # v7",
        f"- uses: 'actions/cache/restore@{_SHA}'  # v6",
        # Local actions run code from this checkout; Docker images are out of scope.
        "- uses: ./.github/actions/install-rust",
        "- uses: docker://alpine:3.20",
    ],
)
def test_a_sha_pin_with_its_tag_and_a_local_action_pass(tmp_path: Path, step: str) -> None:
    assert _check(tmp_path, _steps(step)) == []


@pytest.mark.parametrize(
    ("step", "ref", "line"),
    [
        ("- uses: actions/checkout@v7", "actions/checkout@v7", 4),
        # GitHub accepts each of these spellings, so the validator must read them all.
        ("- {uses: actions/checkout@v7}", "actions/checkout@v7", 4),
        ('- "uses": actions/setup-node@v7', "actions/setup-node@v7", 4),
        ("- uses:\n          actions/cache@v6", "actions/cache@v6", 5),
        # YAML keeps `#v7` in the value because no space precedes it.
        (f"- uses: actions/checkout@{_SHA}#v7", f"actions/checkout@{_SHA}#v7", 4),
        (f"- uses: actions/checkout@{_SHA.upper()} # v7", f"actions/checkout@{_SHA.upper()}", 4),
    ],
)
def test_a_reference_that_is_not_a_lowercase_sha_is_reported(tmp_path: Path, step: str, ref: str, line: int) -> None:
    # The line is where the value starts, which is the next line when the value wraps.
    assert _check(tmp_path, _steps(step)) == [f".github/workflows/ci.yml:{line} uses {ref}; {_ADVICE}"]


def test_a_tag_pin_is_reported_in_a_composite_action(tmp_path: Path) -> None:
    # Composite actions run with the calling job's secrets, so they are checked too.
    text = "runs:\n  using: composite\n  steps:\n    - uses: actions/checkout@v7\n"
    assert _check(tmp_path, text, where="actions/wheel/action.yml") == [
        f".github/actions/wheel/action.yml:4 uses actions/checkout@v7; {_ADVICE}"
    ]


def test_a_reusable_workflow_named_by_branch_is_reported(tmp_path: Path) -> None:
    text = "jobs:\n  call:\n    uses: org/repo/.github/workflows/x.yml@main\n"
    assert _check(tmp_path, text) == [
        f".github/workflows/ci.yml:3 uses org/repo/.github/workflows/x.yml@main; {_ADVICE}"
    ]


def test_a_sha_pin_without_its_tag_comment_is_reported(tmp_path: Path) -> None:
    # Dependabot reads the comment to know which release line to follow.
    assert _check(tmp_path, _steps(f"- uses: actions/checkout@{_SHA}")) == [
        f".github/workflows/ci.yml:4 pins actions/checkout@{_SHA} without a `# <tag>` comment naming its release"
    ]
