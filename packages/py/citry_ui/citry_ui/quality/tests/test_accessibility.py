import json
import re

from citry_ui.quality.accessibility import (
    AXE_INCOMPLETE_DISPOSITIONS,
    AXE_RULE_EXCLUSIONS,
    axe_rule_exclusions_script,
    disposition_manifest,
    exclusion_manifest,
)


def test_every_axe_incomplete_disposition_has_automated_and_manual_ownership():
    assert set(AXE_INCOMPLETE_DISPOSITIONS) == {
        "color-contrast",
        "aria-valid-attr-value",
        "form-field-multiple-labels",
        "label-content-name-mismatch",
    }
    assert all(disposition.reason for disposition in AXE_INCOMPLETE_DISPOSITIONS.values())
    assert all(disposition.automated_evidence for disposition in AXE_INCOMPLETE_DISPOSITIONS.values())
    assert all(disposition.manual_task for disposition in AXE_INCOMPLETE_DISPOSITIONS.values())
    assert [item["rule"] for item in disposition_manifest()] == [
        "color-contrast",
        "aria-valid-attr-value",
        "form-field-multiple-labels",
        "label-content-name-mismatch",
    ]


def test_axe_rule_exclusions_are_narrow_and_explained():
    # Each exclusion names the elements it covers and why, so a reviewer can
    # see the rule still checks every other control.
    assert [(item.rule, item.selector) for item in AXE_RULE_EXCLUSIONS] == [
        ("label-content-name-mismatch", "[role=option][aria-labelledby][aria-describedby]"),
        ("label-content-name-mismatch", '[data-citry-ui-part="command-palette-command"]'),
        ("label-content-name-mismatch", '[data-citry-ui-part="item"][role=treeitem][aria-expanded=true]'),
    ]
    assert all(item.reason for item in AXE_RULE_EXCLUSIONS)
    assert [item["selector"] for item in exclusion_manifest()] == [item.selector for item in AXE_RULE_EXCLUSIONS]


def test_axe_rule_exclusions_script_gives_each_rule_one_selector():
    script = axe_rule_exclusions_script()
    # The rules are the one JSON value in the script, so read them from it
    # instead of locking the surrounding JavaScript.
    match = re.search(r"const rules = (\[.*?\]);", script)
    assert match is not None
    assert json.loads(match.group(1)) == [
        {
            "id": "label-content-name-mismatch",
            "selector": (
                "*:not([role=option][aria-labelledby][aria-describedby])"
                ':not([data-citry-ui-part="command-palette-command"])'
                ':not([data-citry-ui-part="item"][role=treeitem][aria-expanded=true])'
            ),
        }
    ]
    # The script refuses a rule whose own selector it would widen, then applies the rules.
    assert script.index("throw new Error") < script.index("axe.configure({ rules })")
