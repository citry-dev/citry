"""The axe rule exclusions skip only the elements they name."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from playwright.sync_api import Error as PlaywrightError

from citry_ui.quality import accessibility
from citry_ui.quality.accessibility import AxeRuleExclusion, axe_rule_exclusions_script

pytestmark = pytest.mark.e2e

# Every element here shows text that its name leaves out. Only the three
# kinds of element the exclusions name are skipped: a described option, a
# command palette command, and an expanded CTree item. Each other element
# must still be reported, and each one lacks exactly one part of a selector:
# an option with no description, an option with a description but no
# `aria-labelledby`, a button (not an option) with both attributes, a
# collapsed CTree item, an expanded item that is not a tree item, and a
# tree item outside CTree.
_PAGE = """
<!doctype html>
<html lang="en">
  <body>
    <div role="listbox" aria-label="Planets">
      <div id="described" role="option" aria-selected="false" aria-labelledby="mars" aria-describedby="mars-note">
        <span id="mars">Mars</span>
        <span id="mars-note">Fourth planet</span>
      </div>
      <div id="no-description" role="option" aria-selected="false" aria-labelledby="venus">
        <span id="venus">Venus</span>
        <span>Second planet</span>
      </div>
      <div id="label-only" role="option" aria-selected="false" aria-label="Jupiter" aria-describedby="jupiter-note">
        <span>Fifth</span>
        <span id="jupiter-note">Gas giant</span>
      </div>
      <div id="command" role="option" aria-selected="false" aria-labelledby="settings"
        data-citry-ui-part="command-palette-command">
        <span id="settings">Open settings</span>
        <span aria-hidden="true">Ctrl ,</span>
      </div>
    </div>
    <div role="tree" aria-label="Files">
      <div id="expanded" role="treeitem" aria-selected="false" aria-expanded="true" aria-label="Source"
        data-citry-ui-part="item">
        <span>Source</span>
        <div role="group">
          <div role="treeitem" aria-selected="false">main.py</div>
        </div>
      </div>
      <div id="collapsed" role="treeitem" aria-selected="false" aria-expanded="false" aria-label="Continent"
        data-citry-ui-part="item">
        <span>Asia</span>
      </div>
      <div id="branch" role="treeitem" aria-selected="false" aria-expanded="true" aria-label="Europe">
        <span>Europe</span>
        <div role="group">
          <div role="treeitem" aria-selected="false">Prague</div>
        </div>
      </div>
    </div>
    <button id="mismatch" type="button" aria-label="Save draft">Delete everything</button>
    <button id="button-described" type="button" aria-labelledby="archive" aria-describedby="archive-note">
      Archive now
    </button>
    <span id="archive" hidden>Archive</span>
    <span id="archive-note" hidden>Moves the file out of sight</span>
    <button id="accordion" type="button" aria-expanded="true" aria-label="Details"
      data-citry-ui-part="item">
      Shipping
    </button>
  </body>
</html>
"""


_ALL_MISMATCHED = [
    "#accordion",
    "#branch",
    "#button-described",
    "#collapsed",
    "#command",
    "#described",
    "#expanded",
    "#label-only",
    "#mismatch",
    "#no-description",
]
_STILL_MISMATCHED = [
    "#accordion",
    "#branch",
    "#button-described",
    "#collapsed",
    "#label-only",
    "#mismatch",
    "#no-description",
]


def _repository_root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    msg = "Could not find the Citry repository root from the axe exclusion test."
    raise RuntimeError(msg)


def _mismatched_ids(page: Any) -> list[str]:
    return page.evaluate(
        """async () => {
          const results = await axe.run(document, {runOnly: ['label-content-name-mismatch']});
          return results.violations.flatMap((finding) => finding.nodes.map((node) => node.target.join(' ')));
        }"""
    )


def test_the_exclusions_skip_the_named_elements_and_check_every_other_one(page: Any) -> None:
    axe_path = _repository_root() / "node_modules" / "axe-core" / "axe.min.js"
    assert axe_path.is_file(), "run `pnpm install` before Citry UI axe tests"
    page.set_content(_PAGE)
    page.add_script_tag(path=str(axe_path))

    # Without the exclusions, axe reports all ten elements, so the page
    # really does trigger the rule for each kind.
    assert sorted(_mismatched_ids(page)) == _ALL_MISMATCHED

    page.evaluate(axe_rule_exclusions_script())

    # axe still reports an option with no description, an option described
    # but not labelled by an element, a button that has both attributes but
    # is not an option, a collapsed CTree item, an expanded item that is not
    # a tree item, and a tree item outside CTree, such as a CCascader branch.
    # Dropping any one attribute from an exclusion selector would hide one
    # of them.
    assert sorted(_mismatched_ids(page)) == _STILL_MISMATCHED


def test_running_the_script_twice_keeps_the_same_exclusions(page: Any) -> None:
    axe_path = _repository_root() / "node_modules" / "axe-core" / "axe.min.js"
    assert axe_path.is_file(), "run `pnpm install` before Citry UI axe tests"
    page.set_content(_PAGE)
    page.add_script_tag(path=str(axe_path))

    # A page can load the script twice, for example when a test helper and
    # the page both add it. The second run finds the rule already narrowed,
    # so it must leave it alone and not throw.
    page.evaluate(axe_rule_exclusions_script())
    page.evaluate(axe_rule_exclusions_script())

    assert sorted(_mismatched_ids(page)) == _STILL_MISMATCHED


def test_the_script_refuses_a_rule_that_does_not_check_every_element(
    page: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    axe_path = _repository_root() / "node_modules" / "axe-core" / "axe.min.js"
    assert axe_path.is_file(), "run `pnpm install` before Citry UI axe tests"
    page.set_content(_PAGE)
    page.add_script_tag(path=str(axe_path))
    # `button-name` checks only buttons. Writing a `*:not(...)` selector for
    # it would make it check every element, so the script must throw instead.
    monkeypatch.setattr(
        accessibility,
        "AXE_RULE_EXCLUSIONS",
        (AxeRuleExclusion(rule="button-name", selector=".skip", reason="A rule with its own selector."),),
    )

    with pytest.raises(PlaywrightError, match="does not check every element"):
        page.evaluate(axe_rule_exclusions_script())


def test_axe_and_playwright_role_queries_share_a_dialog_name_without_crashing_firefox(page: Any) -> None:
    axe_path = _repository_root() / "node_modules" / "axe-core" / "axe.min.js"
    assert axe_path.is_file(), "run `pnpm install` before Citry UI axe tests"
    # One dialog is named by the element its `aria-labelledby` points at, and
    # the other points at an id that does not exist, so it has no name.
    page.set_content(
        """
        <!doctype html>
        <html lang="en">
          <body>
            <main>
              <div id="named" role="dialog" aria-labelledby="named-title"><h2 id="named-title">Archive</h2></div>
              <div id="unnamed" role="dialog" aria-labelledby="missing-title"><p>No title</p></div>
            </main>
          </body>
        </html>
        """
    )
    # Playwright reads the dialog's name before axe runs, as a test does when
    # it opens a dialog by its role and name.
    page.get_by_role("dialog", name="Archive").wait_for()
    page.add_script_tag(path=str(axe_path))
    page.evaluate(axe_rule_exclusions_script())

    # Before the guard in the script, Playwright's Firefox crashed the page
    # here. In every browser, axe must still follow `aria-labelledby` and
    # report only the dialog whose reference points nowhere.
    unnamed = page.evaluate(
        """async () => {
          const results = await axe.run(document, {runOnly: ['aria-dialog-name']});
          return results.violations.flatMap((finding) => finding.nodes.map((node) => node.target.join(' ')));
        }"""
    )
    assert unnamed == ["#unnamed"]

    # The page is still alive, and Playwright still finds the dialog by name.
    assert page.get_by_role("dialog", name="Archive").get_attribute("id") == "named"
