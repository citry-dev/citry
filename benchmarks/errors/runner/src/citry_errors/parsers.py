"""Turn each tool's raw output into findings with a file, a line and a severity."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
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
# A finding about a component class, or one of its members, that Citry
# read from the class's file, such as
# `/work/app/board_page.py (app.board_page.BoardPage.js_data)`.
_ORIGIN_WITH_MEMBER = re.compile(r"^(?P<file>.+?) \((?P<member>[^()]+)\)$")


def _citry_location(origin: str, span: dict, work: Path) -> tuple[str | None, int | None]:
    """Map a Citry finding to a file and a line in that file.

    A finding in a template file or a Python file names `path:line:col`. A
    finding in a template written inside a Python class names the attribute
    instead, `package.module.Class.template`, with lines counted inside the
    template, so the class is looked up to turn that into a file line. A
    field of a `JsData` class names `package.module.Class.JsData.field`, and
    a value `js_data()` returns or an i18n call in Python names the file
    with the class or member in brackets, `path (package.module.Class.js_data)`
    or `path (package.module.Class)`; these count lines of the file from 0.
    When the app could not be loaded, `citry check` reads a template from
    the file alone and names it `path (Class.template)`, with lines counted
    inside the template.
    """
    if not origin:
        return None, None
    match = _ORIGIN_WITH_LINE.match(origin)
    if match:
        return relative(match["file"], work), int(match["line"])
    template_line = (span.get("start") or {}).get("line")
    match = _ORIGIN_WITH_MEMBER.match(origin)
    if match:
        path = Path(match["file"])
        if match["member"].endswith(".template"):
            class_name = match["member"].split(".")[-2]
            return relative(str(path), work), _inline_template_line(path, class_name, "template", template_line)
        return relative(str(path), work), None if template_line is None else int(template_line) + 1
    parts = origin.split(".")
    for split in range(len(parts) - 2, 0, -1):
        path = work.joinpath(*parts[:split]).with_suffix(".py")
        if not path.is_file():
            continue
        class_name, attribute = parts[split], parts[split + 1] if split + 1 < len(parts) else ""
        if attribute == "JsData":
            # A JsData field's range already counts lines of the file, from 0.
            return relative(str(path), work), None if template_line is None else int(template_line) + 1
        return relative(str(path), work), _inline_template_line(path, class_name, attribute, template_line)
    return origin, None


def _inline_template_line(path: Path, class_name: str, attribute: str, template_line: int | None) -> int | None:
    """Turn a line counted inside a template written as a class attribute into a line of the file."""
    if not path.is_file():
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next((i for i, text in enumerate(lines) if re.match(rf"\s*class {class_name}\b", text)), None)
    if start is None:
        return None
    assign = next(
        (i for i in range(start, len(lines)) if re.match(rf"\s*{re.escape(attribute)}\s*[:=]", lines[i])),
        None,
    )
    if assign is None or template_line is None:
        return None
    # The literal starts on the assignment line (number `assign + 1`), and
    # template line 1 is the rest of that line. Template syntax errors and
    # the unknown-variable rule count from 1, the other template rules
    # from 0; the one-line difference stays within `window`.
    return assign + int(template_line)


def pyright_json(stdout: str, stderr: str, exit_code: int, work: Path) -> list[Finding]:
    """Read `pyright --outputjson`."""
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return exit_status(stdout, stderr, exit_code, work)
    findings = []
    for raw in payload.get("generalDiagnostics", []):
        # pyright's "information" level is below a warning; Pylance shows it in
        # blue, and this benchmark does not count it as a report.
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
            # ruff names a syntax error `invalid-syntax`; the fallback covers a finding with no code.
            str(raw.get("code") or "invalid-syntax"),
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


# esbuild starts each report with `✘ [ERROR] message` or `▲ [WARNING] message`
# (`X` in place of `✘` on Windows), then gives its place as `    path:line:col:`.
# A report's notes may name further places; only the first one is the report's.
_ESBUILD_HEADER = re.compile(r"^\s*(?:✘|▲|X)\s*\[(?P<level>ERROR|WARNING)\]\s+(?P<msg>.*)$")
_ESBUILD_LOCATION = re.compile(r"^\s+(?P<file>[^\s:][^:]*):(?P<line>\d+):\d+:\s*$")


def esbuild(stdout: str, stderr: str, exit_code: int, work: Path) -> list[Finding]:
    """Read the esbuild errors and warnings a build command prints, such as Tetra's `manage.py tetrabuild`.

    A command can print esbuild's error and still succeed, as tetrabuild does.
    The developer sees the error, but a CI build passes, so the error counts as
    a warning then, and as an error only when the command fails. esbuild's own
    warnings are always warnings. A report esbuild gives no place for has the
    code `esbuild-unlocated`, so a case's note that accepts located reports
    does not also accept it.
    """
    error_severity = "error" if exit_code != 0 else "warning"
    findings = []
    # The report whose place has not been read yet: its severity and message.
    pending: tuple[str, str] | None = None
    for line in _strip_ansi(stdout + "\n" + stderr).splitlines():
        match = _ESBUILD_HEADER.match(line)
        if match:
            if pending is not None:
                findings.append(Finding(None, None, pending[0], "esbuild-unlocated", pending[1]))
            pending = (error_severity if match["level"] == "ERROR" else "warning", match["msg"].strip())
            continue
        match = _ESBUILD_LOCATION.match(line)
        if pending is not None and match:
            findings.append(
                Finding(relative(match["file"], work), int(match["line"]), pending[0], "esbuild", pending[1])
            )
            pending = None
    if pending is not None:
        findings.append(Finding(None, None, pending[0], "esbuild-unlocated", pending[1]))
    # The command can also fail before esbuild runs, such as on a Python import error.
    if exit_code != 0 and not any(finding.severity == "error" for finding in findings):
        findings.extend(exit_status(stdout, stderr, exit_code, work))
    return findings


# One frame of a Python traceback, `  File "/path/app.py", line 12, in index`,
# or the first line of a SyntaxError report, which has no `in` part.
_PYTHON_FRAME = re.compile(r'^\s*File "(?P<file>[^"]+)", line (?P<line>\d+)')
# The line that names the exception, such as
# `reflex_base.utils.exceptions.VarAttributeError: The State var ...` or a
# bare `AssertionError`. Python prints it at the start of a line, while the
# source lines it quotes under each frame are indented.
_PYTHON_EXCEPTION = re.compile(r"^(?P<name>[A-Za-z_][\w.]*)(?::|$)")


def python_traceback(stdout: str, stderr: str, exit_code: int, work: Path) -> list[Finding]:
    """
    Read the output of a Python command that fails with a traceback, such as `reflex compile`.

    The last frame in the working copy is the app's own line the failure
    passed through; the frames below it are the framework's. That frame's file
    and line are where a developer would look, so the finding points there,
    and its code is the exception's class name. A failure with no frame in
    the working copy is read as `exit` reads it.
    """
    if exit_code == 0:
        return []
    text = _strip_ansi(stdout + "\n" + stderr)
    lines = text.splitlines()
    location: tuple[str, int] | None = None
    last_frame = -1
    for index, line in enumerate(lines):
        match = _PYTHON_FRAME.match(line)
        if not match:
            continue
        last_frame = index
        path = relative(match["file"], work)
        # A path that `relative` left as it was lies outside the working
        # copy: a framework file, or a `<frozen ...>` module. A folder whose
        # name starts with a dot, such as Reflex's generated `.web`, holds
        # what a tool wrote, not the app's code.
        if path != match["file"].strip() and not path.startswith("."):
            location = (path, int(match["line"]))
    if location is None:
        return exit_status(stdout, stderr, exit_code, work)
    # The exception line and the notes after it, such as Reflex's
    # `Happened while evaluating page 'index'`, follow the last frame.
    after = [line.rstrip() for line in lines[last_frame + 1 :] if line.strip()]
    start = next((index for index, line in enumerate(after) if _PYTHON_EXCEPTION.match(line)), None)
    if start is None:
        return [Finding(location[0], location[1], "error", f"exit-{exit_code}", "\n".join(after[:4]))]
    named = _PYTHON_EXCEPTION.match(after[start])
    code = named["name"].rsplit(".", 1)[-1] if named else f"exit-{exit_code}"
    return [Finding(location[0], location[1], "error", code, "\n".join(after[start : start + 4]))]


def exit_status(stdout: str, stderr: str, exit_code: int, work: Path) -> list[Finding]:
    """Treat a failing command as one unlocated error, quoting the end of its output."""
    if exit_code == 0:
        return []
    text = _strip_ansi(stdout + "\n" + stderr)
    tail = [line for line in text.splitlines() if line.strip()][-12:]
    # A build that fails on a file usually names it with a line somewhere in
    # its output, often above the tail kept as the message, such as Vite's
    # `[plugin vite:vue] <work>/app/components/Card.vue:15:5`.
    for folder in (str(work.resolve()), str(work)):
        match = re.search(re.escape(folder) + r"/([^\s:()'\"]+):(\d+)", text)
        if match:
            return [Finding(match[1], int(match[2]), "error", f"exit-{exit_code}", "\n".join(tail))]
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
    "esbuild": esbuild,
    "python-traceback": python_traceback,
    "exit": exit_status,
}
