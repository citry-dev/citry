"""The conservative ``citry check`` batch template checker."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, ClassVar, NoReturn, cast

from citry._app_selection import CheckAppSelection, app_failure_message, load_app
from citry._checker import CheckFinding, CheckReport, _lsp_range_coordinates, check_project
from citry.command import CommandArg
from citry.extension import ExtensionCommand


class CheckCommand(ExtensionCommand):
    """
    Validate authored component templates without rendering them.

    Invoke the command in exactly one mode. ``citry check --static`` scans the
    current directory for conservative static component candidates and parses
    their direct literal ``template`` assignments with the base Citry parser.
    This mode never assumes the component registry is complete, so it does not
    report unknown component names or apply component input and slot rules.

    ``citry --app module:engine check`` imports the app only after command-line
    arguments have been validated. It initializes the complete registry, reads
    registered inline and file templates directly from their authored sources,
    and parses them with the registry's ``TagRules``. This enables component
    input, slot, typed slot-data, and unknown registered-name checks. Runtime
    template loaders and transform hooks are not called because their output
    cannot yet be mapped back to authored source.

    Registry mode also applies the application's template lint policy. Unknown
    free roots are errors by default, while an explicitly extra-preserving
    schema caps its finding at warning. Runtime globals and declared
    analysis-only variables count as known. Static mode has no component
    namespace and therefore does not run this rule.

    If explicit app import or registry preparation fails, report that failure
    once, discard all registry-derived facts, finish the static check, and exit
    with status 2. Otherwise, exit with status 1 when any source or template
    error is present. Warning-only and clean reports return normally with status
    0. A missing mode or a command that combines ``--app`` with ``--static``
    exits with status 2 without importing the app or scanning source.
    ``build_check_command`` binds the per-invocation app-selection state used by
    :meth:`handle`.

    ``--types`` also type-checks the components whose source is in the
    current directory, as the editor does. TypeScript checks their JavaScript
    and Vue template expressions and reports ``citry.typescript.*`` errors,
    and ty, the Python type checker that ``citry-lsp`` installs, checks their
    Python template expressions and reports ``citry.python.*`` findings. It
    needs registry mode, the ``citry-lsp`` package, and Node.js with the
    ``tsc`` compiler in the project's ``node_modules`` or on ``PATH``. When
    one of them is missing, or ty cannot start, the command says what to
    install or fix and exits with status 2.
    """

    name = "check"
    help = "Check authored component templates."
    arguments = (
        CommandArg(
            "--static",
            action="store_true",
            help="Check limited inline template candidates without importing an app.",
        ),
        CommandArg(
            "--types",
            action="store_true",
            help=(
                "Also type-check component JavaScript and Vue expressions with TypeScript, "
                "and Python template expressions with ty (needs citry-lsp and tsc)."
            ),
        ),
        CommandArg(
            "--format",
            choices=("text", "json"),
            default="text",
            help="Select human-readable text or the versioned JSON report.",
        ),
    )
    selection: ClassVar[CheckAppSelection] = CheckAppSelection()

    def handle(
        self,
        *,
        static: bool = False,
        types: bool = False,
        format: str = "text",  # noqa: A002
        **_kwargs: Any,
    ) -> None:
        """Run the conservative checker and preserve the CLI handler contract."""
        app_selected = any(
            value is not None for value in (self.selection.spec, self.selection.engine, self.selection.failure)
        )
        if static and app_selected:
            _mode_error("--static cannot be combined with an app selection")
        if static and types:
            _mode_error("--types needs the app's registry; use 'citry --app module:engine check --types'")
        if not static and not app_selected:
            _mode_error(
                "choose 'citry --app module:engine check' for registry-backed checking "
                "or 'citry check --static' for limited source scanning",
            )

        selection = self.selection
        if selection.spec is not None and selection.engine is None and selection.failure is None:
            try:
                engine = load_app(selection.spec)
            except (Exception, SystemExit) as exc:  # noqa: BLE001 - project failures degrade after CLI validation
                selection = CheckAppSelection(spec=selection.spec, failure=app_failure_message(exc))
            else:
                selection = CheckAppSelection(spec=selection.spec, engine=engine)

        report = check_project(selection, Path.cwd())
        if types and report.app_failure is None and selection.spec is not None:
            report = _with_type_findings(report, selection.spec, Path.cwd())
        elif types:
            # A registry that failed to load has no components to type-check.
            report = CheckReport(report.findings, report.app_failure, (*report.notes, TYPES_SKIPPED_NOTE))
        if format == "json":
            print(_json_report(report, static=static, app_spec=selection.spec))
        else:
            if report.app_failure is not None:
                sys.stderr.write(f"citry check: app unavailable: {report.app_failure}\n")
            for note in report.notes:
                sys.stderr.write(f"citry check: note: {note}\n")
            for finding in report.findings:
                # The checker's own spelling of its code leads the message, as
                # `tsc` and `ty` print it.
                if finding.code.startswith(TYPESCRIPT_CODE_PREFIX):
                    code = f"{finding.code.removeprefix(TYPESCRIPT_CODE_PREFIX).upper()}: "
                elif finding.code.startswith(PYTHON_CODE_PREFIX):
                    code = f"{finding.code.removeprefix(PYTHON_CODE_PREFIX)}: "
                else:
                    code = ""
                sys.stderr.write(f"{finding.origin}: {finding.severity}: {code}{finding.message}\n")
        if report.exit_code:
            raise SystemExit(report.exit_code)


def _json_report(report: CheckReport, *, static: bool, app_spec: str | None) -> str:
    """Serialize one deterministic versioned checker envelope."""
    mode = "static" if static else ("degraded" if report.app_failure is not None else "registry")
    payload = {
        "schema_version": 1,
        "mode": mode,
        "app": app_spec,
        "app_failure": report.app_failure,
        "notes": list(report.notes),
        "exit_code": report.exit_code,
        "findings": [
            {
                "origin": finding.origin,
                "code": finding.code,
                "severity": finding.severity,
                "message": finding.message,
                "range": (
                    {
                        "start_index": finding.start_index,
                        "end_index": finding.end_index,
                        "start": {"line": finding.line, "column": finding.column},
                        "end": {"line": finding.end_line, "column": finding.end_column},
                    }
                    if finding.start_index is not None
                    else None
                ),
            }
            for finding in report.findings
        ],
    }
    return json.dumps(payload, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))


# The code prefix of a TypeScript finding; the rest is TypeScript's number, such as `ts2322`.
TYPESCRIPT_CODE_PREFIX = "citry.typescript."
# The code prefix of a ty finding; the rest is ty's rule name, such as `invalid-argument-type`.
PYTHON_CODE_PREFIX = "citry.python."
TYPES_SKIPPED_NOTE = "--types did not run TypeScript or ty; it needs an app loaded from 'citry --app module:engine'"


def _with_type_findings(report: CheckReport, app_spec: str, cwd: Path) -> CheckReport:
    """Add TypeScript's and ty's findings for the components in `cwd` to `report`."""
    # citry-lsp is an optional companion package that itself imports citry, so
    # it can only be imported here, once the command needs it.
    try:
        from citry_lsp.project import load_project  # noqa: PLC0415
        from citry_lsp.project_check import check_project_python_types  # noqa: PLC0415
        from citry_lsp.type_analysis import TyUnavailableError  # noqa: PLC0415
        from citry_lsp.typescript import (  # noqa: PLC0415
            TypeScriptUnavailableError,
            check_project_types,
            find_typescript_compiler,
        )
    except ImportError:
        _type_check_error(
            "it needs a citry-lsp release with TypeScript checks; "
            "install or upgrade it with 'python -m pip install --upgrade citry-lsp'"
        )
    try:
        command = find_typescript_compiler(cwd)
    except TypeScriptUnavailableError as exc:
        _type_check_error(str(exc))
    # The language server's project loader reads the same registry facts the editor uses.
    project = load_project(cwd, app_spec)
    if not project.status.registry_ready:
        _type_check_error(project.status.message or "the app's component registry is unavailable")
    try:
        found = check_project_types(project, cwd, command)
    except TypeScriptUnavailableError as exc:
        _type_check_error(str(exc))
    try:
        python_found = check_project_python_types(project, cwd)
    except TyUnavailableError as exc:
        _type_check_error(str(exc), checker="ty")
    findings = list(report.findings)
    for item in (*found, *python_found):
        start = item.diagnostic.range.start
        code = str(item.diagnostic.code)
        coordinates = _lsp_range_coordinates(item.source, item.diagnostic.range)
        findings.append(
            CheckFinding(
                f"{item.path}:{start.line + 1}:{start.character + 1}",
                item.diagnostic.message,
                code,
                # TypeScript findings are always errors; ty keeps its own
                # severity, as the editor shows it.
                "warning" if item.diagnostic.severity == _LSP_WARNING_SEVERITY else "error",
                *(coordinates or ()),
            )
        )
    return CheckReport(tuple(findings), report.app_failure, report.notes)


# The LSP `DiagnosticSeverity.Warning` value, so this module need not import lsprotocol.
_LSP_WARNING_SEVERITY = 2


def _type_check_error(message: str, *, checker: str = "TypeScript") -> NoReturn:
    """Stop `--types` with a message that says what to install or fix."""
    sys.stderr.write(f"citry check: error: --types cannot run {checker}: {message}\n")
    raise SystemExit(2)


def _mode_error(message: str) -> NoReturn:
    """Report an invalid check-mode selection with argparse's exit status."""
    sys.stderr.write(f"citry check: error: {message}\n")
    raise SystemExit(2)


def build_check_command(selection: CheckAppSelection | None = None) -> type[CheckCommand]:
    """Bind one invocation's app-selection state to its command class."""
    namespace = {"selection": selection or CheckAppSelection()}
    return cast("type[CheckCommand]", type("BoundCheckCommand", (CheckCommand,), namespace))


__all__: list[str] = []
