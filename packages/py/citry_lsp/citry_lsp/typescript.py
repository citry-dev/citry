"""
Type-check Citry's browser projections with TypeScript and map the findings back.

The engine builds one generated JavaScript file per template region and per
component JavaScript region (`type_check_projections`). Something then runs
TypeScript over those files: VS Code's own TypeScript server through the
extension, or the `tsc` compiler this module finds and runs for other editors
and for `citry check --types`. Either way the raw findings come back here,
where Citry keeps the useful kinds, drops anything that lands in generated
declarations, drops a finding Citry's own rules already report, and moves the
rest to the authored source.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from lsprotocol import types

from citry._diagnostic_catalog import (
    BROWSER_INCOMPATIBLE_COMPONENT_PROP,
    BROWSER_MISSING_COMPONENT_PROP,
    BROWSER_UNDECLARED_COMPONENT_EVENT,
    BROWSER_UNDECLARED_EMIT,
    BROWSER_UNKNOWN_SERVER_EVENT,
    BROWSER_UNKNOWN_STATE_FIELD,
    COMPONENT_JS_UNKNOWN_MEMBER,
    COMPONENT_JS_UNKNOWN_VARIABLE,
    I18N_ARGUMENT_INVALID,
    I18N_UNKNOWN_MESSAGE,
    VUE_PYTHON_VARIABLE,
    VUE_UNKNOWN_VARIABLE,
)
from citry_lsp.engine import DocumentState, browser_diagnostics, type_check_projections
from citry_lsp.uri import file_uri_path

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from citry_lsp.engine import ProjectionSourceMapping, TypeCheckProjection
    from citry_lsp.project import ProjectState

# Shown as the diagnostic source, next to the "Citry (ty)" source of Python findings.
TYPE_CHECK_SOURCE = "Citry (ts)"
# A forwarded finding's code is this prefix plus TypeScript's own number, such as `ts2322`.
TYPE_CHECK_CODE_PREFIX = "citry.typescript."

# The compiler options every runner uses. The VS Code extension writes the same
# options into the projection folder's jsconfig.json, so hover types and the
# check agree. `strict` stays off: with it, a Vue `data()` value that starts as
# `null` could never take another value, which is how most Options code starts.
TYPE_CHECK_COMPILER_OPTIONS: Mapping[str, object] = {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "allowJs": True,
    "checkJs": True,
    "strict": False,
    "moduleDetection": "force",
    "noEmit": True,
    "skipLibCheck": True,
    "types": [],
}

# The TypeScript errors Citry forwards, grouped by the mistake they describe.
# Other codes are style or strictness opinions about code the author may not
# control, such as implicit `any`, so they are left out.
_TYPE_MISMATCH_CODES = frozenset(
    {
        2322,  # Type 'X' is not assignable to type 'Y'.
        2345,  # Argument of type 'X' is not assignable to parameter of type 'Y'.
        2349,  # This expression is not callable.
        2351,  # This expression is not constructable.
        2362,  # The left-hand side of an arithmetic operation must be a number.
        2363,  # The right-hand side of an arithmetic operation must be a number.
        2365,  # Operator 'X' cannot be applied to types 'Y' and 'Z'.
        2367,  # This comparison appears to be unintentional.
        2540,  # Cannot assign to 'x' because it is a read-only property.
        2559,  # Type 'X' has no properties in common with type 'Y'.
        2588,  # Cannot assign to 'x' because it is a constant.
        2630,  # Cannot assign to 'x' because it is a function.
        2739,  # Type 'X' is missing the following properties from type 'Y'.
        2740,  # Type 'X' is missing the following properties from type 'Y', and more.
        2741,  # Property 'x' is missing in type 'X' but required in type 'Y'.
        2769,  # No overload matches this call.
        2820,  # Type 'X' is not assignable to type 'Y'. Did you mean 'Z'?
    }
)
_UNKNOWN_MEMBER_CODES = frozenset(
    {
        2339,  # Property 'x' does not exist on type 'Y'.
        2353,  # Object literal may only specify known properties.
        2551,  # Property 'x' does not exist on type 'Y'. Did you mean 'z'?
        2561,  # Object literal may only specify known properties. Did you mean 'z'?
    }
)
_CALL_ARITY_CODES = frozenset(
    {
        2554,  # Expected N arguments, but got M.
        2555,  # Expected at least N arguments, but got M.
        2556,  # A spread argument must either have a tuple type or be passed to a rest parameter.
        2575,  # No overload expects N arguments.
    }
)
_UNDEFINED_NAME_CODES = frozenset(
    {
        2304,  # Cannot find name 'x'.
        2552,  # Cannot find name 'x'. Did you mean 'y'?
        2662,  # Cannot find name 'x'. Did you mean the static member 'Y.x'?
        2663,  # Cannot find name 'x'. Did you mean the instance member 'this.x'?
    }
)
_SYNTAX_CODES_START = 1000
_SYNTAX_CODES_END = 2000
REPORTED_TYPESCRIPT_CODES = _TYPE_MISMATCH_CODES | _UNKNOWN_MEMBER_CODES | _CALL_ARITY_CODES | _UNDEFINED_NAME_CODES

# Citry's own findings that describe the same mistake as a TypeScript error on
# the same text. Citry's message explains the Citry rule and follows the
# project's severity setting, so its finding wins and TypeScript's is dropped.
_CITRY_OWNED_CODES = frozenset(
    {
        VUE_UNKNOWN_VARIABLE,
        VUE_PYTHON_VARIABLE,
        COMPONENT_JS_UNKNOWN_VARIABLE,
        COMPONENT_JS_UNKNOWN_MEMBER,
        BROWSER_UNDECLARED_EMIT,
        BROWSER_UNDECLARED_COMPONENT_EVENT,
        BROWSER_UNKNOWN_SERVER_EVENT,
        BROWSER_UNKNOWN_STATE_FIELD,
        BROWSER_MISSING_COMPONENT_PROP,
        BROWSER_INCOMPATIBLE_COMPONENT_PROP,
        I18N_UNKNOWN_MESSAGE,
        I18N_ARGUMENT_INVALID,
    }
)

# How long one `tsc` run may take before Citry gives up on it.
_TSC_TIMEOUT_SECONDS = 300.0
# How long a stopped `tsc` may take to exit.
_TSC_STOP_SECONDS = 2.0

# One `tsc --pretty false` finding: `file(line,column): error TS1234: message`.
# A chained message continues on the following lines, indented.
_TSC_LINE = re.compile(
    r"^(?P<file>\S.*?)\((?P<line>\d+),(?P<column>\d+)\): "
    r"(?P<category>error|warning|message) TS(?P<code>\d+): (?P<message>.*)$"
)
_TSC_GLOBAL_ERROR = re.compile(r"^error TS(?P<code>\d+): (?P<message>.*)$")
# The text a `tsc` finding starts at, for the end of its range; `tsc` prints
# only the start. A member chain such as `this.clearDropTarget` or a whole
# string literal reads better than its first character.
_TOKEN = re.compile(
    r"[\w$]+(?:\??\.[\w$]+)*"
    r"|'(?:[^'\\\n]|\\.)*'"
    r'|"(?:[^"\\\n]|\\.)*"'
    r"|`(?:[^`\\\n]|\\.)*`"
    r"|\S"
)


class TypeScriptUnavailableError(RuntimeError):
    """TypeScript cannot run here; the message says what to install or configure."""


@dataclass(frozen=True, slots=True)
class TypeScriptFinding:
    """One TypeScript diagnostic in the coordinates of the projection file it belongs to."""

    # The `TypeCheckProjection.identity` of that file.
    file_id: str
    range: types.Range
    code: int
    message: str
    category: Literal["error", "warning", "suggestion", "message"] = "error"


def map_type_check_findings(
    projections: Sequence[TypeCheckProjection],
    findings: Iterable[TypeScriptFinding],
    citry_diagnostics: Iterable[types.Diagnostic] = (),
) -> tuple[types.Diagnostic, ...]:
    """
    Turn raw TypeScript findings into diagnostics on the authored document.

    A finding is kept only when it is an error of a reported kind, both ends
    of its range fall inside authored text, and no Citry finding for the same
    mistake covers the same text. Syntax errors count only for a projection
    with `report_syntax`. Template projections also drop "cannot find name":
    the `citry.vue.unknown-variable` rule decides which names a template may
    read, including the ones a project declares as open.
    """
    by_identity = {projection.identity: projection for projection in projections}
    owned = tuple(
        diagnostic.range
        for diagnostic in citry_diagnostics
        if isinstance(diagnostic.code, str) and diagnostic.code in _CITRY_OWNED_CODES
    )
    retained: dict[tuple[int, int, int, int, int, str], types.Diagnostic] = {}
    for finding in findings:
        projection = by_identity.get(finding.file_id)
        if projection is None or finding.category != "error":
            continue
        # TypeScript numbers its syntax errors from 1000 to 1999.
        syntax = projection.report_syntax and _SYNTAX_CODES_START <= finding.code < _SYNTAX_CODES_END
        if finding.code not in REPORTED_TYPESCRIPT_CODES and not syntax:
            continue
        if finding.code in _UNDEFINED_NAME_CODES and projection.identity.startswith("template:"):
            continue
        mapped = map_projection_range(finding.range, projection.source_mappings)
        if mapped is None or any(_ranges_touch(mapped, other) for other in owned):
            continue
        key = (
            mapped.start.line,
            mapped.start.character,
            mapped.end.line,
            mapped.end.character,
            finding.code,
            finding.message,
        )
        retained.setdefault(
            key,
            types.Diagnostic(
                mapped,
                finding.message,
                severity=types.DiagnosticSeverity.Error,
                code=f"{TYPE_CHECK_CODE_PREFIX}ts{finding.code}",
                source=TYPE_CHECK_SOURCE,
            ),
        )
    return tuple(retained.values())


def map_projection_range(
    value: types.Range,
    mappings: Sequence[ProjectionSourceMapping],
) -> types.Range | None:
    """Map a projection range to authored source, or `None` when an end is generated text."""
    start = _map_position(value.start, mappings, "start")
    # An empty range is one cursor, so both ends share the start mapping.
    end = start if value.start == value.end else _map_position(value.end, mappings, "end")
    if start is None or end is None or _compare(start, end) > 0:
        return None
    return types.Range(start, end)


def _map_position(
    position: types.Position,
    mappings: Sequence[ProjectionSourceMapping],
    edge: Literal["start", "end"],
) -> types.Position | None:
    """
    Map one projection position through the stretches of authored text the engine recorded.

    This follows the VS Code client's `mapSegmentedPosition`, so the editor and
    `citry check` place a finding on the same authored text. A stretch whose
    authored and generated lengths differ, such as a Python escape sequence,
    maps only its two ends.
    """
    containing = [
        mapping
        for mapping in mappings
        if _compare(mapping.virtual_range.start, position) <= 0 and _compare(position, mapping.virtual_range.end) <= 0
    ]
    if not containing:
        return None
    # At the boundary of two runs, the run this edge belongs to wins.
    preferred = next(
        (
            mapping
            for mapping in containing
            if (mapping.virtual_range.start if edge == "start" else mapping.virtual_range.end) == position
        ),
        containing[0],
    )
    source = preferred.source_range
    virtual = preferred.virtual_range
    linear = (
        source.start.line == source.end.line
        and virtual.start.line == virtual.end.line
        and source.end.character - source.start.character == virtual.end.character - virtual.start.character
    )
    if linear:
        return types.Position(source.start.line, source.start.character + position.character - virtual.start.character)
    if position == virtual.start:
        return source.start
    if position == virtual.end:
        return source.end
    return None


def _compare(first: types.Position, second: types.Position) -> int:
    return (first.line > second.line or (first.line == second.line and first.character > second.character)) - (
        first.line < second.line or (first.line == second.line and first.character < second.character)
    )


def _ranges_touch(first: types.Range, second: types.Range) -> bool:
    """Whether two ranges share text, counting an empty range at a boundary as shared."""
    return _compare(first.start, second.end) <= 0 and _compare(second.start, first.end) <= 0


def find_typescript_compiler(workspace: Path) -> tuple[str, ...]:
    """
    Return the command that runs TypeScript's `tsc` for this workspace.

    The project's own TypeScript wins, so the check uses the version the
    project pins: the nearest `node_modules/.bin/tsc` in the workspace or a
    folder above it. Otherwise `tsc` on `PATH` is used. Node.js must be on
    `PATH` in both cases, because `tsc` is a Node.js program.

    Raises:
        TypeScriptUnavailableError: When Node.js or `tsc` cannot be found.

    """
    if shutil.which("node") is None:
        msg = "Node.js was not found on PATH. Install Node.js and TypeScript (npm install --save-dev typescript)."
        raise TypeScriptUnavailableError(msg)
    names = ("tsc.cmd", "tsc.exe", "tsc") if os.name == "nt" else ("tsc",)
    for folder in (workspace.resolve(), *workspace.resolve().parents):
        for name in names:
            candidate = folder / "node_modules" / ".bin" / name
            if candidate.is_file():
                return (str(candidate),)
    on_path = shutil.which("tsc")
    if on_path is not None:
        return (on_path,)
    msg = (
        "TypeScript's tsc was not found in the project's node_modules or on PATH. "
        "Install it with npm install --save-dev typescript."
    )
    raise TypeScriptUnavailableError(msg)


def run_typescript_compiler(
    command: Sequence[str],
    files: Sequence[tuple[str, str]],
    *,
    timeout: float = _TSC_TIMEOUT_SECONDS,
) -> tuple[TypeScriptFinding, ...]:
    """
    Type-check `(file_id, source)` pairs with one `tsc` run and return its findings.

    Each source is written to its own file in a temporary folder beside a
    `tsconfig.json` holding `TYPE_CHECK_COMPILER_OPTIONS`, so the project's
    own configuration never changes the result.

    Raises:
        TypeScriptUnavailableError: When `tsc` cannot start, times out, or
            fails without reporting a finding in one of the files.

    """
    if not files:
        return ()
    with tempfile.TemporaryDirectory(prefix="citry-type-check-") as directory:
        folder, names = _write_check_folder(Path(directory), files)
        try:
            result = subprocess.run(
                _tsc_arguments(command),
                cwd=folder,
                capture_output=True,
                check=False,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            msg = f"TypeScript could not run ({' '.join(command)}): {exc}"
            raise TypeScriptUnavailableError(msg) from exc
    return _tsc_findings(command, result.returncode, f"{result.stdout}\n{result.stderr}", names)


async def run_typescript_compiler_async(
    command: Sequence[str],
    files: Sequence[tuple[str, str]],
    *,
    timeout: float = _TSC_TIMEOUT_SECONDS,
) -> tuple[TypeScriptFinding, ...]:
    """
    Run `run_typescript_compiler` without blocking the language server.

    A newer edit cancels the waiting task, and the `tsc` process is killed
    with it, so cancelled checks never pile up.

    Raises:
        TypeScriptUnavailableError: As `run_typescript_compiler` does.

    """
    if not files:
        return ()
    with tempfile.TemporaryDirectory(prefix="citry-type-check-") as directory:
        folder, names = _write_check_folder(Path(directory), files)
        try:
            process = await asyncio.create_subprocess_exec(
                *_tsc_arguments(command),
                cwd=folder,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except OSError as exc:
            msg = f"TypeScript could not run ({' '.join(command)}): {exc}"
            raise TypeScriptUnavailableError(msg) from exc
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except BaseException as exc:
            # Cancelled or too slow: stop `tsc` before the folder it reads is removed.
            with contextlib.suppress(ProcessLookupError):
                process.kill()
            # A child that `tsc` started may keep the output pipes open, so
            # waiting for them is bounded.
            with contextlib.suppress(asyncio.TimeoutError):
                await asyncio.wait_for(process.wait(), timeout=_TSC_STOP_SECONDS)
            if isinstance(exc, asyncio.TimeoutError):
                msg = f"TypeScript took longer than {timeout:g} seconds ({' '.join(command)})"
                raise TypeScriptUnavailableError(msg) from exc
            raise
    output = f"{stdout.decode('utf-8', 'replace')}\n{stderr.decode('utf-8', 'replace')}"
    return _tsc_findings(command, process.returncode or 0, output, names)


def _write_check_folder(
    folder: Path,
    files: Sequence[tuple[str, str]],
) -> tuple[Path, dict[str, tuple[str, str]]]:
    """Write the projection files and their `tsconfig.json`; return the folder and each file's owner."""
    # `tsc` prints paths relative to the real folder, so name it by its real path.
    folder = folder.resolve()
    names: dict[str, tuple[str, str]] = {}
    for index, (file_id, source) in enumerate(files):
        name = f"projection-{index}.js"
        (folder / name).write_text(source, encoding="utf-8", newline="")
        names[name] = (file_id, source)
    config = {"compilerOptions": dict(TYPE_CHECK_COMPILER_OPTIONS), "include": ["*.js"]}
    (folder / "tsconfig.json").write_text(json.dumps(config), encoding="utf-8")
    return folder, names


def _tsc_arguments(command: Sequence[str]) -> list[str]:
    # A relative project path keeps every printed file name short and relative.
    return [*command, "--project", "tsconfig.json", "--pretty", "false"]


def _tsc_findings(
    command: Sequence[str],
    returncode: int,
    output: str,
    names: Mapping[str, tuple[str, str]],
) -> tuple[TypeScriptFinding, ...]:
    findings = parse_tsc_output(output, names)
    if returncode != 0 and not findings:
        detail = output.strip().splitlines()[:5]
        msg = f"TypeScript failed ({' '.join(command)}): {' '.join(detail) or f'exit status {returncode}'}"
        raise TypeScriptUnavailableError(msg)
    return findings


def parse_tsc_output(output: str, files: Mapping[str, tuple[str, str]]) -> tuple[TypeScriptFinding, ...]:
    """
    Read `tsc --pretty false` output for the named projection files.

    `files` maps each file name `tsc` prints to its `(file_id, source)`. `tsc`
    prints only where a finding starts, so the range ends after the word it
    starts at. A finding in any other file, such as Vue's bundled types, is
    skipped.

    Raises:
        TypeScriptUnavailableError: When `tsc` reports a problem with the
            configuration itself, which no projection file can explain.

    """
    findings: list[TypeScriptFinding] = []
    current: dict[str, object] | None = None

    def flush() -> None:
        if current is not None:
            findings.append(TypeScriptFinding(**current))  # type: ignore[arg-type]

    for line in output.splitlines():
        match = _TSC_LINE.match(line)
        if match is not None:
            flush()
            current = None
            entry = files.get(Path(match["file"]).name)
            if entry is None:
                continue
            file_id, source = entry
            start = types.Position(int(match["line"]) - 1, int(match["column"]) - 1)
            current = {
                "file_id": file_id,
                "range": types.Range(start, _token_end(source, start)),
                "code": int(match["code"]),
                "message": match["message"],
                "category": match["category"],
            }
            continue
        global_error = _TSC_GLOBAL_ERROR.match(line)
        if global_error is not None:
            msg = f"TypeScript rejected the check configuration: TS{global_error['code']}: {global_error['message']}"
            raise TypeScriptUnavailableError(msg)
        if current is not None and line.startswith(" "):
            # A chained message explains the first line in more detail.
            current["message"] = f"{current['message']}\n{line.strip()}"
    flush()
    return tuple(findings)


# The version of the `citry/typeCheck` request a client answers.
TYPE_CHECK_CLIENT_VERSION = 1
_CATEGORIES = frozenset({"error", "warning", "suggestion", "message"})


def type_check_request_params(
    document: DocumentState,
    projections: Sequence[TypeCheckProjection],
) -> dict[str, object]:
    """Build the `citry/typeCheck` request that asks the client to run TypeScript."""
    return {
        "version": TYPE_CHECK_CLIENT_VERSION,
        "textDocument": {"uri": document.uri, "version": document.version},
        "files": [projection.to_dict() for projection in projections],
    }


def parse_type_check_response(response: object, expected_ids: Sequence[str]) -> tuple[TypeScriptFinding, ...] | None:
    """
    Read a client's `citry/typeCheck` answer.

    `None` means the client could not run TypeScript this time, for example
    while VS Code's TypeScript server is still starting.

    Raises:
        ValueError: When the answer does not follow the request's shape.

    """
    if response is None:
        return None
    if type(response) is not dict or response.get("version") != TYPE_CHECK_CLIENT_VERSION:
        msg = "citry/typeCheck response must be an object with version 1"
        raise ValueError(msg)
    files = response.get("files")
    if type(files) is not list:
        msg = "citry/typeCheck response requires a files list"
        raise ValueError(msg)
    expected = frozenset(expected_ids)
    findings: list[TypeScriptFinding] = []
    for entry in files:
        if type(entry) is not dict or entry.get("id") not in expected or type(entry.get("diagnostics")) is not list:
            msg = "citry/typeCheck files must name a requested file and list its diagnostics"
            raise ValueError(msg)
        for raw in entry["diagnostics"]:
            findings.append(_wire_finding(entry["id"], raw))
    return tuple(findings)


def _wire_finding(file_id: str, raw: object) -> TypeScriptFinding:
    if type(raw) is not dict:
        msg = "citry/typeCheck diagnostics must be objects"
        raise ValueError(msg)
    code = raw.get("code")
    message = raw.get("message")
    category = raw.get("category")
    if type(code) is not int or type(message) is not str or category not in _CATEGORIES:
        msg = "citry/typeCheck diagnostics need an integer code, a message, and a category"
        raise ValueError(msg)
    return TypeScriptFinding(file_id, _wire_range(raw.get("range")), code, message, category)


def _wire_range(raw: object) -> types.Range:
    if type(raw) is not dict:
        msg = "citry/typeCheck diagnostics need a range"
        raise ValueError(msg)
    start, end = raw.get("start"), raw.get("end")
    return types.Range(_wire_position(start), _wire_position(end))


def _wire_position(raw: object) -> types.Position:
    if type(raw) is not dict:
        msg = "citry/typeCheck positions must be objects"
        raise ValueError(msg)
    line, character = raw.get("line"), raw.get("character")
    if type(line) is not int or type(character) is not int or line < 0 or character < 0:
        msg = "citry/typeCheck positions need non-negative line and character numbers"
        raise ValueError(msg)
    return types.Position(line, character)


def check_document_types(
    document: DocumentState,
    project: ProjectState,
    open_documents: Mapping[str, DocumentState],
    command: Sequence[str],
    citry_diagnostics: Iterable[types.Diagnostic],
) -> tuple[types.Diagnostic, ...]:
    """
    Type-check one document with `tsc` and return its forwarded findings.

    The language server uses this for an editor that does not run TypeScript
    itself. `citry_diagnostics` are Citry's current findings for the document,
    so a mistake Citry already reports is not reported twice.

    Raises:
        TypeScriptUnavailableError: When `tsc` cannot run.

    """
    projections = type_check_projections(document, project, open_documents)
    if not projections:
        return ()
    raw = run_typescript_compiler(command, [(projection.identity, projection.source) for projection in projections])
    return map_type_check_findings(projections, raw, citry_diagnostics)


@dataclass(frozen=True, slots=True)
class ProjectTypeFinding:
    """One forwarded TypeScript finding in one authored file."""

    path: Path
    source: str
    diagnostic: types.Diagnostic


def check_project_types(
    project: ProjectState,
    workspace: Path,
    command: Sequence[str],
) -> tuple[ProjectTypeFinding, ...]:
    """
    Type-check the browser code of every component whose source is in `workspace`.

    Each Python file with inline templates or JavaScript, each template file,
    and each component JavaScript file is read from disk and checked the way
    the editor checks it when open. Components installed from another
    package are skipped, because their authors check them.

    Raises:
        TypeScriptUnavailableError: When `tsc` cannot run.

    """
    documents = _project_documents(project, workspace.resolve())
    files: list[tuple[str, str]] = []
    owners: dict[str, tuple[DocumentState, tuple[TypeCheckProjection, ...]]] = {}
    for document in documents.values():
        projections = type_check_projections(document, project, documents)
        if not projections:
            continue
        owners[document.uri] = (document, projections)
        # One run checks every file, so each projection gets a globally unique id.
        files.extend((f"{document.uri}#{projection.identity}", projection.source) for projection in projections)
    raw = run_typescript_compiler(command, files)
    by_document: dict[str, list[TypeScriptFinding]] = {}
    for finding in raw:
        uri, _, identity = finding.file_id.rpartition("#")
        by_document.setdefault(uri, []).append(
            TypeScriptFinding(identity, finding.range, finding.code, finding.message, finding.category)
        )
    results: list[ProjectTypeFinding] = []
    for uri, (document, projections) in sorted(owners.items()):
        citry = browser_diagnostics(document, project, documents, js_data_checks=False)
        path = file_uri_path(uri) or Path(uri)
        results.extend(
            ProjectTypeFinding(path, document.source, diagnostic)
            for diagnostic in sorted(
                map_type_check_findings(projections, by_document.get(uri, ()), citry),
                key=lambda item: (item.range.start.line, item.range.start.character),
            )
        )
    return tuple(results)


def _project_documents(project: ProjectState, workspace: Path) -> dict[str, DocumentState]:
    """Read every authored file that holds a component's template or JavaScript."""
    catalog = project.catalog
    if catalog is None:
        return {}
    languages: dict[Path, str] = {}
    for component in catalog.components:
        for kind, language in (("template", "citry-html"), ("js", "javascript")):
            asset = getattr(component.assets, kind)
            if asset.kind == "inline" and asset.owner_file is not None:
                languages.setdefault(asset.owner_file.resolve(), "python")
            elif asset.resolved_path is not None:
                languages.setdefault(asset.resolved_path.resolve(), language)
    documents: dict[str, DocumentState] = {}
    for path, language in sorted(languages.items()):
        if not path.is_relative_to(workspace):
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        document = DocumentState(path.as_uri(), language, source, 0)
        document.update(source, 0, project)
        documents[document.uri] = document
    return documents


def _token_end(source: str, start: types.Position) -> types.Position:
    """Return the end of the word at `start`, counting columns in UTF-16 units as TypeScript does."""
    lines = source.split("\n")
    if start.line >= len(lines):
        return start
    text = lines[start.line].removesuffix("\r")
    units = 0
    for index, character in enumerate(text):
        if units >= start.character:
            match = _TOKEN.match(text, index)
            if match is None:
                return start
            width = len(match.group().encode("utf-16-le")) // 2
            return types.Position(start.line, start.character + width)
        units += len(character.encode("utf-16-le")) // 2
    return start


__all__ = [
    "REPORTED_TYPESCRIPT_CODES",
    "TYPE_CHECK_CLIENT_VERSION",
    "TYPE_CHECK_CODE_PREFIX",
    "TYPE_CHECK_COMPILER_OPTIONS",
    "TYPE_CHECK_SOURCE",
    "ProjectTypeFinding",
    "TypeScriptFinding",
    "TypeScriptUnavailableError",
    "check_document_types",
    "check_project_types",
    "find_typescript_compiler",
    "map_projection_range",
    "map_type_check_findings",
    "parse_tsc_output",
    "parse_type_check_response",
    "run_typescript_compiler",
    "run_typescript_compiler_async",
    "type_check_request_params",
]
