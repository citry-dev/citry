"""Run the pinned Nu Html Checker against a rendered scenario artifact."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# Alpine's three attribute spellings, all of which Nu reports as not allowed
# because HTML permits no attribute outside `data-*` and its own fixed set:
# the `x-` directives, `@event` for `x-on:event`, and `:attr` for `x-bind:attr`.
#
# `@c-` is deliberately left out. That prefix is Citry's own event syntax, which
# the server consumes and never renders, so meeting one in output means it
# leaked rather than that Nu failed to recognize Alpine. `@citry-...` is
# unaffected: only the exact `@c-` prefix is excluded.
_ALPINE_ATTRIBUTE = r"(?:x-[a-z][a-z0-9_.:-]*|@(?!c-)[a-z][a-z0-9_.:-]*|:[a-z][a-z0-9_.-]*)"
_ALPINE_ATTRIBUTE_ERROR = re.compile(
    rf"^Attribute “(?P<attribute>{_ALPINE_ATTRIBUTE})” "
    r"not allowed on element “[a-z][a-z0-9-]*” at this point\.$"
)
_CSS_ANCHOR_PROPERTY_ERROR = re.compile(
    r"^CSS: “(?P<property>anchor-name|position-anchor|position-area|"
    r"position-try-fallbacks|position-visibility)”: Property “(?P=property)” "
    r"doesn't exist\.$"
)
_CSS_ANCHOR_SIZE_ERROR = "CSS: “inline-size”: Parse Error."


class HtmlQualificationError(ValueError):
    """Rendered HTML contains an unexpected Nu error."""


@dataclass(frozen=True, slots=True)
class HtmlReport:
    """Compact HTML result suitable for CI artifacts and exit records."""

    scenario: str
    checker_version: str
    errors: int
    alpine_directives: tuple[str, ...]
    css_anchor_features: tuple[str, ...]
    information: int


def qualify_nu_result(result: dict[str, Any], *, scenario: str) -> HtmlReport:
    """Reject Nu errors except its known inability to recognize Alpine directives."""
    unexpected: list[dict[str, Any]] = []
    alpine_directives: set[str] = set()
    css_anchor_features: set[str] = set()
    information = 0

    for finding in result.get("messages", []):
        finding_type = finding.get("type")
        message = str(finding.get("message", ""))
        if finding_type != "error":
            information += 1
            continue
        alpine = _ALPINE_ATTRIBUTE_ERROR.fullmatch(message)
        if alpine is not None:
            # Recorded rather than discarded: the report lists every directive
            # that was tolerated, so the exemption stays visible in CI output.
            alpine_directives.add(alpine.group("attribute"))
            continue
        css_anchor_property = _CSS_ANCHOR_PROPERTY_ERROR.fullmatch(message)
        if css_anchor_property is not None:
            # Nu's CSS parser has not caught up with browser-supported CSS
            # anchor positioning. Keep each tolerated feature visible in the
            # report instead of hiding CSS errors wholesale.
            css_anchor_features.add(css_anchor_property.group("property"))
            continue
        if message == _CSS_ANCHOR_SIZE_ERROR and "anchor-size(" in str(finding.get("extract", "")):
            css_anchor_features.add("anchor-size()")
            continue
        unexpected.append(finding)

    if unexpected:
        rendered = "; ".join(
            f"line {finding.get('lastLine', '?')}: {finding.get('message', 'unknown error')}" for finding in unexpected
        )
        msg = f"Nu HTML errors for {scenario}: {rendered}"
        raise HtmlQualificationError(msg)

    return HtmlReport(
        scenario=scenario,
        checker_version=str(result.get("version", "unknown")),
        errors=0,
        alpine_directives=tuple(sorted(alpine_directives)),
        css_anchor_features=tuple(sorted(css_anchor_features)),
        information=information,
    )


def _resolve_vnu_jar() -> Path:
    node = shutil.which("node")
    if node is None:
        raise HtmlQualificationError("Node is required to resolve the pinned vnu-jar package.")
    completed = subprocess.run(
        [node, "-p", "require('vnu-jar').toString()"],
        check=False,
        capture_output=True,
        text=True,
    )
    jar = Path(completed.stdout.strip())
    if completed.returncode != 0 or not jar.is_file():
        detail = completed.stderr.strip() or completed.stdout.strip() or "vnu-jar was not found"
        raise HtmlQualificationError(f"Unable to resolve pinned vnu-jar: {detail}")
    return jar


def validate_html(path: Path, *, scenario: str) -> HtmlReport:
    """Run Nu using an explicit Java runtime and qualify its JSON output."""
    if not path.is_file():
        raise HtmlQualificationError(f"Rendered HTML file does not exist: {path}.")
    java = shutil.which("java")
    if java is None:
        raise HtmlQualificationError("Java 17 or newer is required to run Nu Html Checker.")
    completed = subprocess.run(
        [java, "-jar", str(_resolve_vnu_jar()), "--format", "json", str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    payload = completed.stderr.strip() or completed.stdout.strip()
    try:
        result = json.loads(payload)
    except json.JSONDecodeError as error:
        detail = payload or f"checker exited with status {completed.returncode}"
        raise HtmlQualificationError(f"Nu did not return a JSON report: {detail}") from error
    return qualify_nu_result(result, scenario=scenario)


def main() -> int:
    parser = argparse.ArgumentParser(description="Qualify rendered Citry UI HTML with Nu.")
    parser.add_argument("html", type=Path)
    parser.add_argument("--scenario", required=True)
    args = parser.parse_args()
    try:
        report = validate_html(args.html, scenario=args.scenario)
    except HtmlQualificationError as error:
        parser.exit(1, f"citry-ui HTML qualification failed: {error}\n")
    sys.stdout.write(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
