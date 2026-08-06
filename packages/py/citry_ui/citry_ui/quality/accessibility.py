"""Owned dispositions for axe findings that require human judgment."""

from __future__ import annotations

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
                "Axe asks for manual confirmation when a Dialog activator's aria-controls target is hidden "
                "in the initial state."
            ),
            automated_evidence=(
                "Dialog browser tests assert that every activator references its rendered native dialog "
                "before opening."
            ),
            manual_task="assistive-technology",
        ),
    )
}


def disposition_manifest() -> list[dict[str, str]]:
    """Return deterministic axe incomplete ownership for release records."""
    return [asdict(disposition) for disposition in AXE_INCOMPLETE_DISPOSITIONS.values()]
