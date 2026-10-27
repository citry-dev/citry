"""Owned dispositions for axe findings that require human judgment."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class AxeIncompleteDisposition:
    """Why an axe incomplete result remains open and who resolves it."""

    rule: str
    reason: str
    automated_evidence: str
    manual_task: str


AXE_INCOMPLETE_DISPOSITIONS = {
    disposition.rule: disposition
    for disposition in (
        AxeIncompleteDisposition(
            rule="color-contrast",
            reason=(
                "Axe cannot always resolve system colors such as Canvas and CanvasText through inherited "
                "light and dark color-scheme scopes."
            ),
            automated_evidence="Focused computed-style tests prove documented variables reach rendered controls.",
            manual_task="visual-design-approval",
        ),
        AxeIncompleteDisposition(
            rule="aria-valid-attr-value",
            reason=(
                "Axe asks for manual confirmation when a closed overlay trigger's aria-controls target is hidden "
                "in the initial state."
            ),
            automated_evidence=(
                "Overlay browser tests assert that every trigger references its rendered dialog, listbox, or menu "
                "before opening."
            ),
            manual_task="assistive-technology",
        ),
        AxeIncompleteDisposition(
            rule="form-field-multiple-labels",
            reason=(
                "Axe requests human judgment for Rating's first native radio: CField labels the whole "
                "group through its control ID while the radio's wrapping label names that exact score."
            ),
            automated_evidence=(
                "Rating server and browser tests prove the root group label, one exact value label per radio, "
                "native radio keyboard behavior, and the Field label relationship."
            ),
            manual_task="assistive-technology",
        ),
        AxeIncompleteDisposition(
            rule="label-content-name-mismatch",
            reason=(
                "Axe 4.14 cannot judge text that is only a symbol, such as the \N{MULTIPLICATION SIGN} of a "
                "close button or the + and \N{MINUS SIGN} of a number input, or a single letter, such as a "
                'tree item labelled "A". Each such control\'s name contains that text or is a full text name. '
                "WCAG 2.5.3 Label in Name does not apply to symbols. The scenario tests still fail when axe "
                "reports this rule's other incomplete result: that the text of a switch, checkbox, radio, or "
                "checkable menu item may be its value. They also fail when a control's name is a symbol or "
                "single letter that differs from its visible text."
            ),
            automated_evidence=(
                "Component browser tests find each icon-only control by its full name, such as Close, Clear "
                "date, or Remove followed by the tag, and the listbox and tree tests read each item's name."
            ),
            manual_task="assistive-technology",
        ),
    )
}


@dataclass(frozen=True, slots=True)
class AxeRuleExclusion:
    """Elements that one axe rule skips, and why that rule does not apply to them."""

    rule: str
    selector: str
    reason: str


# Each entry covers markup whose name already holds the control's whole
# label, where the rest of the visible text is a description, a child, or
# decoration. Keep the selector as narrow as the reason, so the rule still
# checks every other control.
AXE_RULE_EXCLUSIONS = (
    AxeRuleExclusion(
        rule="label-content-name-mismatch",
        selector="[role=option][aria-labelledby][aria-describedby]",
        reason=(
            "Each option is named by its label element and points aria-describedby at its visible "
            "description. The whole label is in the name, and screen "
            "readers read the description after it. Adding the description to the name would read it twice. "
            "Any aria-hidden start or end slot content of the option is decoration."
        ),
    ),
    AxeRuleExclusion(
        rule="label-content-name-mismatch",
        selector='[data-citry-ui-part="command-palette-command"]',
        reason=(
            "A CCommandPalette command is named by its label. Its other visible text is the item_start and "
            "item_end content that the application supplies as decoration, and the shortcut hint, which "
            "aria-keyshortcuts exposes to assistive technology. These parts are aria-hidden and inert."
        ),
    ),
    AxeRuleExclusion(
        rule="label-content-name-mismatch",
        selector='[data-citry-ui-part="item"][role=treeitem][aria-expanded=true]',
        reason=(
            "The W3C ARIA tree pattern places an expanded CTree item's child group inside the item, so the "
            "item's visible text includes its children's labels. Its name is its own label, which starts that "
            "text."
        ),
    ),
)


def disposition_manifest() -> list[dict[str, str]]:
    """Return deterministic axe incomplete ownership for release records."""
    return [asdict(disposition) for disposition in AXE_INCOMPLETE_DISPOSITIONS.values()]


def exclusion_manifest() -> list[dict[str, str]]:
    """Return the axe rule exclusions, in their declared order, for release records."""
    return [asdict(exclusion) for exclusion in AXE_RULE_EXCLUSIONS]


def axe_rule_exclusions_script() -> str:
    """
    Return JavaScript that makes the axe already loaded on a page skip the excluded elements.

    A browser test runs it after it adds axe and before it calls ``axe.run``.
    The new selector is every element except the excluded ones, which is
    right only for a rule that checks every element. The script throws for
    a rule with a narrower selector of its own, which it would widen, and
    does nothing for a rule it has already narrowed on this page. It reads
    each rule's selector from ``axe._audit``, a private object, because
    axe's public ``getRules()`` does not return selectors.
    """
    selectors: dict[str, list[str]] = {}
    for exclusion in AXE_RULE_EXCLUSIONS:
        selectors.setdefault(exclusion.rule, []).append(exclusion.selector)
    rules = [
        {"id": rule, "selector": "*" + "".join(f":not({selector})" for selector in rule_selectors)}
        for rule, rule_selectors in selectors.items()
    ]
    return (
        "() => {"
        f" const rules = {json.dumps(rules)};"
        " for (const rule of rules) {"
        "  const current = axe._audit.rules.find((candidate) => candidate.id === rule.id);"
        "  if (current && current.selector === rule.selector) continue;"
        "  if (!current || current.selector !== '*') {"
        "   throw new Error(`axe rule ${rule.id} does not check every element, so it cannot be excluded this way`);"
        "  }"
        " }"
        " axe.configure({ rules });"
        " }"
    )
