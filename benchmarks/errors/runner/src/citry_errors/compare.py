"""Compare a case's browser check with the clean app's and decide whether the mistake showed at runtime."""

from __future__ import annotations

import re

from .runtime import _ARIA, _ID, Observation
from .score import RuntimeResult

# An HTTP status counts only where access logs print it: after the request
# line (`"GET / HTTP/1.1" 500`) or after the method and path (`POST /save 500`),
# so a response size such as `200 512` or a timing such as `250ms` is not
# read as a status.
_STATUS = re.compile(r'(?:HTTP/[\d.]+"? |\b(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS) \S+ )([1-5]\d\d)\b')
# `\w*Error` also covers Python's and JavaScript's named errors, such as
# `TypeError:`, and `[500]` is how some dev servers tag a failed request.
_SERVER_ERROR = re.compile(
    r'Traceback|Exception|\bERROR\b|\b\w*Error\b|\[5\d\d\]|HTTP/[\d.]+"? 5\d\d\b'
    r"|\b(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS) \S+ 5\d\d\b"
)
_SERVER_WARNING = re.compile(r"\bWARN(ING)?\b|\bwarn\b|Warning")
# 16 or more hex digits in a row in an id or any aria-* value are taken to be
# made up per render, such as the 32 random hex digits after `citry-vue-` on
# the element Citry mounts an interactive page into. A name a developer writes
# rarely has such a sequence; one that does is blanked too.
_GENERATED = re.compile(r"[0-9a-fA-F]{16,}")


def _normal(line: str, *, keep_status: bool) -> str:
    """Blank what differs between any two runs: ports, timestamps, counters.

    In a server log, HTTP status codes are kept, so a 500 in the access log
    does not look like the clean app's 200.
    """
    statuses = [match.group(1) for match in _STATUS.finditer(line)] if keep_status else []
    # Each case runs in a working folder named after it, which a dev server
    # may print, such as "Will watch for changes in .../work/m01-...".
    line = re.sub(r"\bwork/[^/\s'\"]+", "work/<case>", line)
    return " ".join(re.sub(r"\d+", "N", line).split()) + "".join(f" status={code}" for code in statuses)


def _response_key(line: str) -> str:
    # A failed response is recorded as `<status> <url>`; the status is kept so
    # a 500 on a URL does not look like the clean app's 404 on it.
    status, _, url = line.partition(" ")
    return f"{status} {_normal(url, keep_status=False)}"


def _added(
    baseline: list[str], mutated: list[str], *, keep_status: bool = False, responses: bool = False
) -> list[str]:
    """Return the case's lines that the clean app's run did not have."""

    def key(line: str) -> str:
        return _response_key(line) if responses else _normal(line, keep_status=keep_status)

    seen = {key(line) for line in baseline if line.strip()}
    return [line for line in mutated if line.strip() and key(line) not in seen]


def problems(observation: Observation) -> list[str]:
    """List what makes the clean app's run unusable as the comparison point."""
    found = []
    if not observation.started:
        found.append("did not start")
    if observation.failure:
        found.append(observation.failure)
    found += [f"journey {name}: {record.failure}" for name, record in observation.journeys.items() if record.failure]
    found += observation.console_errors[:3] + observation.bad_responses[:3]
    found += [line for line in observation.server_log if _SERVER_ERROR.search(line)][:3]
    return found


def compare(baseline: Observation, mutated: Observation) -> RuntimeResult:
    """Classify the case's runtime behavior against the clean app's."""
    result = RuntimeResult(started=mutated.started)
    errors = (
        _added(baseline.console_errors, mutated.console_errors)
        + _added(baseline.bad_responses, mutated.bad_responses, responses=True)
        + [
            line
            for line in _added(baseline.server_log, mutated.server_log, keep_status=True)
            if _SERVER_ERROR.search(line)
        ]
    )
    if mutated.failure and not baseline.failure:
        # The scripted clicks could not run, for example because a button is
        # missing. That is a visible difference, not an error message.
        result.output_differs = True
        result.evidence.append(f"interaction: {mutated.failure}")
    for name, record in mutated.journeys.items():
        clean = baseline.journeys.get(name)
        # The same rule for every other journey: a step the clean page could
        # take and the case's page could not is a visible difference.
        if record.failure and not (clean and clean.failure):
            result.output_differs = True
            result.evidence.append(f"interaction ({name}): {record.failure}")
    warnings = _added(baseline.console_warnings, mutated.console_warnings) + [
        line
        for line in _added(baseline.server_log, mutated.server_log, keep_status=True)
        if _SERVER_WARNING.search(line) and not _SERVER_ERROR.search(line)
    ]
    if not mutated.started:
        result.error = True
        result.evidence.append(mutated.failure)
    result.error = result.error or bool(errors)
    result.warning = bool(warnings)
    result.evidence += [f"error: {line}" for line in errors[:10]] + [f"warning: {line}" for line in warnings[:10]]
    if _pages(mutated) != _pages(baseline):
        result.output_differs = True
    return result


def _pages(observation: Observation) -> tuple:
    """Gather every page record of one run, in the form the comparison uses."""
    # A journey only one run has (a server that never started records none)
    # makes the two differ too.
    return (
        comparable(observation.snapshot_loaded),
        comparable(observation.snapshot),
        comparable(observation.snapshot_reloaded),
        {name: comparable(record.snapshot) for name, record in observation.journeys.items()},
    )


def comparable(snapshot: dict | None) -> dict | None:
    """
    Blank the parts of a page record that a framework generates anew on every render.

    Without this, two loads of the same clean page would never match, and
    every case of that framework would read as "silently wrong".
    """
    if snapshot is None:
        return None
    elements = []
    for element in snapshot["elements"]:
        row = list(element)
        row[_ID] = _blank_generated(row[_ID])
        # aria-controls and aria-labelledby name other elements by id.
        row[_ARIA] = [[name, _blank_generated(value)] for name, value in row[_ARIA]]
        elements.append(row)
    return {**snapshot, "elements": elements}


def _blank_generated(value: str | None) -> str | None:
    return None if value is None else _GENERATED.sub("<generated>", value)
