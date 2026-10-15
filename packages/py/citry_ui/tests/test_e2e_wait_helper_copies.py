"""Keep the two copies of the browser-test wait helpers identical."""

from __future__ import annotations

from pathlib import Path

# The citry and citry_ui browser suites cannot import from each other's test
# folders, so each conftest holds the same marked region of wait helpers.
# Comparing the regions here means a fix made to one copy cannot be forgotten
# in the other.
_REPO = Path(__file__).resolve().parents[4]
_COPIES = (
    _REPO / "packages/py/citry/tests/e2e/conftest.py",
    _REPO / "packages/py/citry_ui/conftest.py",
)
_BEGIN = "# BEGIN shared browser wait helpers"
_END = "# END shared browser wait helpers"


def _region(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    # Exactly one region per file, so a stray second marker cannot hide a copy.
    assert text.count(_BEGIN) == 1, f"{path} must contain one '{_BEGIN}' line"
    assert text.count(_END) == 1, f"{path} must contain one '{_END}' line"
    return text[text.index(_BEGIN) : text.index(_END)]


def test_browser_wait_helper_copies_are_identical() -> None:
    citry_region, citry_ui_region = (_region(path) for path in _COPIES)
    assert citry_region == citry_ui_region, (
        f"the wait-helper regions in {_COPIES[0]} and {_COPIES[1]} differ; apply the same change to both"
    )
