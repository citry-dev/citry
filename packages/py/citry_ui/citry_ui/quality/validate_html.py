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

_ALPINE_ATTRIBUTE_ERROR = re.compile(
    r"^Attribute “x-[a-z][a-z0-9_.:-]*” not allowed on element “[a-z][a-z0-9-]*” at this point\.$"
)


class HtmlQualificationError(ValueError):
    """Rendered HTML contains an unexpected Nu error."""


@dataclass(frozen=True, slots=True)
class HtmlReport:
    """Compact HTML result suitable for CI artifacts and exit records."""

    scenario: str
    checker_version: str
    errors: int
    alpine_directives: tuple[str, ...]
    information: int


def qualify_nu_result(result: dict[str, Any], *, scenario: str) -> HtmlReport:
    """Reject Nu errors except its known inability to recognize Alpine directives."""
    unexpected: list[dict[str, Any]] = []
    alpine_directives: set[str] = set()
    information = 0

    for finding in result.get("messages", []):
        finding_type = finding.get("type")
        message = str(finding.get("message", ""))
        if finding_type != "error":
            information += 1
            continue
        if _ALPINE_ATTRIBUTE_ERROR.fullmatch(message):
            match = re.search(r"“(?P<attribute>x-[a-z][a-z0-9_.:-]*)”", message)
            if match is not None:
                alpine_directives.add(match.group("attribute"))
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
