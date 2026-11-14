from __future__ import annotations

from typing import TYPE_CHECKING

from scripts import supported_versions

if TYPE_CHECKING:
    from pathlib import Path


def _matrix(cells: list[tuple[str, str]], full: list[tuple[str, str]]) -> str:
    def as_json(pairs: list[tuple[str, str]]) -> str:
        return "[" + ",".join(f'{{"python-version":"{v}","os":"{o}"}}' for v, o in pairs) + "]"

    return (
        "          ${{ fromJSON(github.event_name == 'pull_request'\n"
        f"          && '{as_json(cells)}'\n"
        f"          || '{as_json(full)}') }}}}\n"
    )


def test_matrix_versions_unions_every_jobs_full_list(tmp_path: Path) -> None:
    # Linux leaves out the Check workflow's Python, so a version that only
    # another OS tests must still count as tested.
    workflow = tmp_path / "py--tests.yml"
    workflow.write_text(
        _matrix([("3.11", "ubuntu-latest")], [("3.11", "ubuntu-latest"), ("3.15", "ubuntu-latest")])
        + _matrix([("3.11", "windows-latest")], [("3.11", "windows-latest"), ("3.14", "windows-latest")]),
        encoding="utf-8",
    )
    assert supported_versions.matrix_versions(workflow) == {(3, 11), (3, 14), (3, 15)}


def test_matrix_versions_reads_the_real_workflow() -> None:
    assert supported_versions.matrix_versions(supported_versions.TESTS_WORKFLOW) == {
        (3, 11),
        (3, 12),
        (3, 13),
        (3, 14),
        (3, 15),
    }
