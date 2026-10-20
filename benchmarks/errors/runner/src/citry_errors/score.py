"""Decide which stage first reported a mistake, from findings and runtime observations."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from .config import STATIC_STAGES

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .parsers import Finding


def new_findings(baseline: Iterable[Finding], mutated: Iterable[Finding]) -> list[Finding]:
    """Keep the findings the case added, counting repeats so a second copy of a known finding still counts.

    Findings are first matched exactly, then with numbers blanked. The
    second pass catches a known finding whose message quotes a line that
    moved, and running it second keeps "expected 2 arguments" from being
    taken for the clean app's "expected 1 arguments" when both are present.
    """
    clean = list(baseline)
    unmatched = list(mutated)
    for loose in (False, True):
        still = []
        for finding in unmatched:
            key = finding.key(loose=loose)
            known = next((candidate for candidate in clean if candidate.key(loose=loose) == key), None)
            if known is None:
                still.append(finding)
            else:
                # Each clean finding explains at most one finding of the case.
                clean.remove(known)
        unmatched = still
    return unmatched


def near_mistake(finding: Finding, mistake_file: str, mistake_line: int | None, window: int) -> bool:
    """Tell whether a new finding points at the change, which makes it a direct report of the mistake.

    A finding elsewhere can still come from the change: a parser reports an
    unclosed tag at the outer element, and a type checker reports a wrong value
    where it is used. But it can also be a side effect that says nothing about
    the mistake, such as a variable the change left unused. So such an
    indirect finding counts only when the case confirms it, with a reason.
    """
    if finding.file is None:
        # A failure with no location counts only when it names the changed
        # file; otherwise it could be an unrelated failure, such as a build
        # that could not reach the network.
        return Path(mistake_file).name in finding.message
    if finding.file != mistake_file:
        return False
    return finding.line is None or mistake_line is None or abs(finding.line - mistake_line) <= window


@dataclass
class StageResult:
    stage: str
    label: str
    error: bool = False
    warning: bool = False
    timed_out: bool = False
    # Findings that point elsewhere and that the case's `indirect` note covers.
    indirect_error: bool = False
    indirect_warning: bool = False
    evidence: list[Finding] = field(default_factory=list)
    indirect: list[Finding] = field(default_factory=list)
    # Findings that point elsewhere and that no note covers; listed, never counted.
    unconfirmed: list[Finding] = field(default_factory=list)


def score_stage(
    stage: str,
    label: str,
    baseline: list[Finding] | None,
    mutated: list[Finding] | None,
    mistake_file: str,
    mistake_line: int | None,
    window: int,
    accepted_codes: tuple[str, ...] = (),
) -> StageResult:
    result = StageResult(stage, label)
    if baseline is None or mutated is None:
        result.timed_out = True
        return result
    for finding in new_findings(baseline, mutated):
        direct = near_mistake(finding, mistake_file, mistake_line, window)
        if not direct and finding.code not in accepted_codes:
            result.unconfirmed.append(finding)
            continue
        (result.evidence if direct else result.indirect).append(finding)
        if finding.severity == "error":
            if direct:
                result.error = True
            else:
                result.indirect_error = True
        elif direct:
            result.warning = True
        else:
            result.indirect_warning = True
    return result


@dataclass
class RuntimeResult:
    started: bool = True
    error: bool = False
    warning: bool = False
    output_differs: bool = False
    evidence: list[str] = field(default_factory=list)


def earliest(
    stages: list[StageResult],
    runtime: RuntimeResult | None,
    *,
    count_warnings: bool,
    accept_indirect: bool = False,
) -> str:
    """
    Return the first outcome a developer would meet, under one warning policy.

    With `count_warnings` false only errors count (the record's `strict`);
    with it true, warnings count too (`lenient`).
    """
    for name in STATIC_STAGES:
        for result in stages:
            error = result.error or (accept_indirect and result.indirect_error)
            warning = result.warning or (accept_indirect and result.indirect_warning)
            if result.stage == name and (error or (count_warnings and warning)):
                return name
    if runtime is None:
        return "not-run"
    if runtime.error or not runtime.started:
        return "runtime-error"
    if count_warnings and runtime.warning:
        return "runtime-warning"
    return "silent" if runtime.output_differs else "never"
