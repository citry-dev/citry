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
_CSS_ANCHOR_SIZE_VALUE_ERROR = re.compile(
    r"CSS: “(?P<property>min-inline-size)”: “anchor-size\(width\)” "
    r"is not a “(?P=property)” value\."
)
_CSS_ANCHOR_VALUES = {
    "anchor-name": re.compile(r"--_cui-[a-z0-9-]+"),
    "position-anchor": re.compile(r"(?:var\(\s*--_cui-[a-z0-9-]+\s*\)|--_cui-[a-z0-9-]+)"),
    "position-area": re.compile(
        r"(?:block-end(?:\s+span-inline-(?:end|start))?|"
        r"block-start(?:\s+span-inline-(?:end|start))?|"
        r"inline-(?:end|start)\s+span-block-end)"
    ),
    "position-try-fallbacks": re.compile(r"flip-block,\s*flip-inline,\s*flip-block\s+flip-inline"),
    "position-visibility": re.compile(r"anchors-visible"),
    "inline-size": re.compile(
        r"min\(\s*anchor-size\(\s*width\s*\)\s*,\s*"
        r"(?:var\(\s*--_cui-menu-max-inline-size\s*\)|calc\(\s*100vw\s*-\s*2rem\s*\))\s*\)"
    ),
    "min-inline-size": re.compile(r"anchor-size\(\s*width\s*\)"),
}
_CSS_CONTAINER_TYPE_ERROR = "CSS: “container-type”: Property “container-type” doesn't exist."
_CSS_CONTAINER_RULE_ERROR = "CSS: Unrecognized at-rule “@container”"
_CSS_CONTAINER_TYPE_VALUE = re.compile(r"inline-size")
_CSS_CONTAINER_CONDITION = re.compile(r"(?:width\s*<=\s*22rem|max-width\s*:\s*22rem|inline-size\s*<\s*44rem)")


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
    css_container_features: tuple[str, ...]
    information: int


def _source_declaration_value(finding: dict[str, Any], source: str | None, property_name: str) -> str | None:
    """Return one exact declaration value from Nu's reported source line."""
    line_number = finding.get("lastLine")
    if source is None or not isinstance(line_number, int):
        return None
    lines = source.splitlines()
    if not 1 <= line_number <= len(lines):
        return None
    line = lines[line_number - 1]
    declaration = re.compile(rf"(?<![-\w]){re.escape(property_name)}\s*:\s*(?P<value>[^;{{}}]+)")
    matches = list(declaration.finditer(line))
    if len(matches) == 1:
        return matches[0].group("value").strip()
    last_column = finding.get("lastColumn")
    if not isinstance(last_column, int):
        return None
    matches = [match for match in matches if match.start() + 1 <= last_column <= match.end()]
    return matches[0].group("value").strip() if len(matches) == 1 else None


def _known_css_anchor_feature(finding: dict[str, Any], message: str, source: str | None) -> str | None:
    """Recognize only exact anchor declarations emitted by Citry UI."""
    property_error = _CSS_ANCHOR_PROPERTY_ERROR.fullmatch(message)
    if property_error is not None:
        property_name = property_error.group("property")
        feature = property_name
    elif message == _CSS_ANCHOR_SIZE_ERROR:
        property_name = "inline-size"
        feature = "anchor-size()"
    elif (size_value_error := _CSS_ANCHOR_SIZE_VALUE_ERROR.fullmatch(message)) is not None:
        property_name = size_value_error.group("property")
        feature = "anchor-size()"
    else:
        return None
    value = _source_declaration_value(finding, source, property_name)
    if value is None or _CSS_ANCHOR_VALUES[property_name].fullmatch(value) is None:
        return None
    return feature


def _source_at_rule_condition(finding: dict[str, Any], source: str | None, rule_name: str) -> str | None:
    """Return one at-rule condition from Nu's reported source line."""
    line_number = finding.get("lastLine")
    if source is None or not isinstance(line_number, int):
        return None
    lines = source.splitlines()
    if not 1 <= line_number <= len(lines):
        return None
    line = lines[line_number - 1]
    rule = re.compile(rf"@{re.escape(rule_name)}\s*\((?P<condition>[^{{}}]+)\)\s*{{")
    matches = list(rule.finditer(line))
    if len(matches) == 1:
        return matches[0].group("condition").strip()
    last_column = finding.get("lastColumn")
    if not isinstance(last_column, int):
        return None
    matches = [match for match in matches if match.start() + 1 <= last_column <= match.end()]
    return matches[0].group("condition").strip() if len(matches) == 1 else None


def _known_css_container_feature(finding: dict[str, Any], message: str, source: str | None) -> str | None:
    """Recognize only the container-query CSS emitted by Citry UI."""
    if message == _CSS_CONTAINER_TYPE_ERROR:
        value = _source_declaration_value(finding, source, "container-type")
        return "container-type" if value is not None and _CSS_CONTAINER_TYPE_VALUE.fullmatch(value) else None
    if message == _CSS_CONTAINER_RULE_ERROR:
        condition = _source_at_rule_condition(finding, source, "container")
        return "@container" if condition is not None and _CSS_CONTAINER_CONDITION.fullmatch(condition) else None
    return None


def qualify_nu_result(result: dict[str, Any], *, scenario: str, source: str | None = None) -> HtmlReport:
    """Reject Nu errors except checked Alpine and browser-CSS compatibility gaps."""
    unexpected: list[dict[str, Any]] = []
    alpine_directives: set[str] = set()
    css_anchor_features: set[str] = set()
    css_container_features: set[str] = set()
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
        css_anchor_feature = _known_css_anchor_feature(finding, message, source)
        if css_anchor_feature is not None:
            # Nu's CSS parser has not caught up with browser-supported CSS
            # anchor positioning. Keep each tolerated feature visible in the
            # report instead of hiding CSS errors wholesale.
            css_anchor_features.add(css_anchor_feature)
            continue
        css_container_feature = _known_css_container_feature(finding, message, source)
        if css_container_feature is not None:
            # Citry UI exercises these container queries in browser tests. Nu
            # still reports them, so retain the exact tolerated feature here.
            css_container_features.add(css_container_feature)
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
        css_container_features=tuple(sorted(css_container_features)),
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
    return qualify_nu_result(result, scenario=scenario, source=path.read_text(encoding="utf-8"))


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
