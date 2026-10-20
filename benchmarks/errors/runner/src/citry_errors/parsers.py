"""Turn each tool's raw output into findings with a file, a line and a severity."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class ToolUnavailable(RuntimeError):
    """The tool ran but skipped its checks, so its silence says nothing about the case."""


@dataclass(frozen=True)
class Finding:
    file: str | None
    line: int | None
    severity: str
    code: str
    message: str

    def key(self, *, loose: bool = False) -> tuple[str | None, str, str, str]:
        """Identify a finding without its line, so a finding that only moved is not counted as new.

        The loose key also blanks the numbers in the message, for a message
        that quotes a line number or a counter.
        """
        return (self.file, self.code, self.severity, _normalize(self.message, blank_numbers=loose))


def _normalize(text: str, *, blank_numbers: bool) -> str:
    # The working copy's folder differs between the clean app and each case,
    # absolute or relative, so it is blanked before two outputs are compared.
    text = re.sub(r"[^\s'\"(]*\bwork/[^/\s'\"]+/", "<work>/", text)
    if blank_numbers:
        text = re.sub(r"\d+", "N", text)
    return " ".join(text.split())


def relative(path: str, work: Path) -> str:
    """Express a reported path relative to the case's working copy."""
    path = path.strip()
    for prefix in (str(work.resolve()) + "/", str(work) + "/"):
        path = path.removeprefix(prefix)
    # Some tools print paths relative to a parent folder instead, such as
    # Turbopack's `./work/<case>/app/card.tsx`.
    marker = f"work/{work.name}/"
    if marker in path:
        path = path.split(marker, 1)[1]
    return path.removeprefix("./")


def citry_json(stdout: str, stderr: str, exit_code: int, work: Path) -> list[Finding]:
    """Read `citry --app ... check --format json`."""
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return exit_status(stdout, stderr, exit_code, work)
    if any("did not run" in note for note in payload.get("notes", [])) or (
        exit_code == 2 and not payload.get("app_failure")
    ):
        # `--types` could not start TypeScript or ty. A clean report would
        # wrongly read as "nothing found", so the stage counts as not run.
        raise ToolUnavailable("; ".join(payload.get("notes", [])) or f"citry check exited {exit_code}")
    findings = []
    if payload.get("app_failure"):
        # The app failed to import; that is a report of the mistake with no location.
        findings.append(Finding(None, None, "error", "citry.app-failure", str(payload["app_failure"])))
    for raw in payload.get("findings", []):
        file, line = _citry_location(str(raw.get("origin", "")), raw.get("range") or {}, work)
        findings.append(
            Finding(file, line, _severity(raw.get("severity")), str(raw.get("code", "")), str(raw.get("message", "")))
        )
    return findings


_ORIGIN_WITH_LINE = re.compile(r"^(?P<file>.+?):(?P<line>\d+)(?::\d+)?$")


def _citry_location(origin: str, span: dict, work: Path) -> tuple[str | None, int | None]:
    """Map a Citry finding to a file and a line in that file.

    A finding in a template file or a Python file names `path:line:col`. A
    finding in a template written inside a Python class names the attribute
    instead, `package.module.Class.template`, with lines counted inside the
    template, so the class is looked up to turn that into a file line.
    """
    if not origin:
        return None, None
    match = _ORIGIN_WITH_LINE.match(origin)
    if match:
        return relative(match["file"], work), int(match["line"])
    template_line = (span.get("start") or {}).get("line")
    parts = origin.split(".")
    for split in range(len(parts) - 2, 0, -1):
        path = work.joinpath(*parts[:split]).with_suffix(".py")
        if not path.is_file():
            continue
        class_name, attribute = parts[split], parts[split + 1] if split + 1 < len(parts) else ""
        lines = path.read_text(encoding="utf-8").splitlines()
        start = next((i for i, text in enumerate(lines) if re.match(rf"\s*class {class_name}\b", text)), None)
        if start is None:
            return relative(str(path), work), None
        assign = next(
            (i for i in range(start, len(lines)) if re.match(rf"\s*{re.escape(attribute)}\s*[:=]", lines[i])),
            None,
        )
        if assign is None or template_line is None:
            return relative(str(path), work), None
        # The literal starts on the assignment line (number `assign + 1`), and
        # template line 1 is the rest of that line. Template syntax errors and
        # the unknown-variable rule count from 1, the other template rules
        # from 0; the one-line difference stays within `window`.
        return relative(str(path), work), assign + int(template_line)
    return origin, None


def pyright_json(stdout: str, stderr: str, exit_code: int, work: Path) -> list[Finding]:
    """Read `pyright --outputjson`."""
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return exit_status(stdout, stderr, exit_code, work)
    findings = []
    for raw in payload.get("generalDiagnostics", []):
        # An "information" diagnostic is a hint the editor shows faintly, not a report.
        if raw.get("severity") == "information":
            continue
        start = (raw.get("range") or {}).get("start") or {}
        line = start.get("line")
        findings.append(
            Finding(
                relative(raw.get("file", ""), work) or None,
                None if line is None else int(line) + 1,
                _severity(raw.get("severity")),
                str(raw.get("rule", "pyright")),
                str(raw.get("message", "")),
            )
        )
    return findings


_TSC_PAREN = re.compile(
    r"^(?P<file>[^\s(][^(]*)\((?P<line>\d+),\d+\): (?P<sev>error|warning) (?P<code>TS\d+): (?P<msg>.*)$"
)
_TSC_COLON = re.compile(
    r"^(?P<file>[^\s:][^:]*):(?P<line>\d+):\d+ - (?P<sev>error|warning) (?P<code>TS\d+): (?P<msg>.*)$"
)
# `next build` prints the file on one line and "Type error: ..." on the next.
_NEXT_FILE = re.compile(r"^(?P<file>\./[^\s:]+):(?P<line>\d+):\d+\s*$")


def tsc(stdout: str, stderr: str, exit_code: int, work: Path) -> list[Finding]:
    """Read `tsc`, `vue-tsc` and `next build` diagnostics."""
    text = _strip_ansi(stdout + "\n" + stderr)
    findings = []
    pending: tuple[str, int] | None = None
    for line in text.splitlines():
        match = _TSC_PAREN.match(line) or _TSC_COLON.match(line)
        if match:
            findings.append(
                Finding(
                    relative(match["file"], work),
                    int(match["line"]),
                    match["sev"],
                    match["code"],
                    match["msg"],
                )
            )
            pending = None
            continue
        match = _NEXT_FILE.match(line.strip())
        if match:
            pending = (relative(match["file"], work), int(match["line"]))
            continue
        if pending and line.strip():
            findings.append(Finding(pending[0], pending[1], "error", "build", line.strip()))
            pending = None
    if exit_code != 0 and not findings:
        findings.extend(exit_status(stdout, stderr, exit_code, work))
    return findings


def eslint_json(stdout: str, stderr: str, exit_code: int, work: Path) -> list[Finding]:
    """Read `eslint -f json`."""
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return exit_status(stdout, stderr, exit_code, work)
    findings = []
    for result in payload:
        for message in result.get("messages", []):
            findings.append(
                Finding(
                    relative(result.get("filePath", ""), work),
                    message.get("line"),
                    "error" if message.get("severity") == 2 else "warning",
                    str(message.get("ruleId") or "eslint"),
                    str(message.get("message", "")),
                )
            )
    return findings


def ruff_json(stdout: str, stderr: str, exit_code: int, work: Path) -> list[Finding]:
    """Read `ruff check --output-format json`.

    ruff has no severity: any finding fails the command, so each one is an error.
    """
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return exit_status(stdout, stderr, exit_code, work)
    return [
        Finding(
            relative(raw.get("filename", ""), work),
            (raw.get("location") or {}).get("row"),
            "error",
            # A syntax error has no rule code.
            str(raw.get("code") or "syntax-error"),
            str(raw.get("message", "")),
        )
        for raw in payload
    ]


# djLint prints a file's path, a rule line, then one `CODE line:col message` per finding.
_DJLINT_FINDING = re.compile(r"^(?P<code>[A-Z]\d{3}) (?P<line>\d+):\d+ (?P<msg>.*)$")


def djlint(stdout: str, stderr: str, exit_code: int, work: Path) -> list[Finding]:
    """Read `djlint --lint`. Like ruff it has no severity, and any finding fails the command."""
    findings = []
    current: str | None = None
    for line in _strip_ansi(stdout).splitlines():
        stripped = line.strip()
        match = _DJLINT_FINDING.match(stripped)
        if match:
            findings.append(Finding(current, int(match["line"]), "error", match["code"], match["msg"]))
        elif stripped and not stripped.startswith(("─", "Linting", "Linted")) and "/" in stripped:
            current = relative(stripped, work)
    if exit_code != 0 and not findings:
        findings.extend(exit_status(stdout, stderr, exit_code, work))
    return findings


def exit_status(stdout: str, stderr: str, exit_code: int, work: Path) -> list[Finding]:
    """Treat a failing command as one unlocated error, quoting the end of its output."""
    del work  # Every parser takes the same arguments; this one has no paths to rewrite.
    if exit_code == 0:
        return []
    tail = [line for line in _strip_ansi(stdout + "\n" + stderr).splitlines() if line.strip()][-12:]
    return [Finding(None, None, "error", f"exit-{exit_code}", "\n".join(tail))]


def _severity(value: object) -> str:
    return "error" if str(value).lower() == "error" else "warning"


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text)


PARSE = {
    "citry-json": citry_json,
    "pyright-json": pyright_json,
    "tsc": tsc,
    "eslint-json": eslint_json,
    "ruff-json": ruff_json,
    "djlint": djlint,
    "exit": exit_status,
}
