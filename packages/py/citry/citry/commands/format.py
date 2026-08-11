"""The development-only ``citry format`` batch command."""

from __future__ import annotations

import sys
from contextlib import ExitStack
from pathlib import Path
from typing import Any, NoReturn

from citry._embedded_provider import BiomeEmbeddedProvider, EmbeddedProviderConfigError
from citry._formatter import EmbeddedMode, FormatMode, FormatReport, FormatUsageError, format_paths
from citry.command import CommandArg
from citry.extension import ExtensionCommand
from citry_core.template_formatter import python_expression_provider


class FormatCommand(ExtensionCommand):
    """
    Format statically identifiable Citry component assets.

    Explicit Python files use conservative component discovery. Explicit
    ``.html``, ``.citry``, and ``.citry-html`` files are standalone templates.
    Directories use Citry's module-file discovery rules and add only direct,
    constant ``template_file``, ``js_file``, and ``css_file`` declarations
    that stay inside the directory. JavaScript and CSS run only through
    explicitly configured providers.

    Write mode replaces each changed file atomically. ``--check`` and
    ``--diff`` are read-only and exit with status 1 when formatting would make
    a change. File errors are reported together and exit with status 2.
    Formatting is independent of a Citry app selection.
    """

    name = "format"
    help = "Format statically identifiable Citry component assets."
    arguments = (
        CommandArg(
            "paths",
            nargs="*",
            default=(".",),
            metavar="PATH",
            help="Python, Citry template, JavaScript, CSS, or directory target (default: current directory).",
        ),
        CommandArg(
            "--check",
            action="store_true",
            help="Report files that would change without writing them.",
        ),
        CommandArg(
            "--diff",
            action="store_true",
            help="Print unified diffs without writing files.",
        ),
        CommandArg(
            "--verbose",
            action="store_true",
            help="Report active formatter capabilities.",
        ),
        CommandArg(
            "--embedded",
            choices=("off", "available", "required"),
            default="available",
            help="Control JavaScript/CSS provider requirements (default: available).",
        ),
        CommandArg(
            "--javascript-provider",
            default=None,
            metavar="ADAPTER:EXECUTABLE",
            help="Explicit JavaScript provider, initially biome:/absolute/path/to/biome.",
        ),
        CommandArg(
            "--css-provider",
            default=None,
            metavar="ADAPTER:EXECUTABLE",
            help="Explicit CSS provider, initially biome:/absolute/path/to/biome.",
        ),
    )

    def handle(
        self,
        *,
        paths: list[str] | tuple[str, ...] = (".",),
        check: bool = False,
        diff: bool = False,
        verbose: bool = False,
        embedded: EmbeddedMode = "available",
        javascript_provider: str | None = None,
        css_provider: str | None = None,
        **_kwargs: Any,
    ) -> None:
        """Run one deterministic batch and map its report to the CLI contract."""
        if check and diff:
            _usage_error("--check and --diff are mutually exclusive")
        mode: FormatMode = "check" if check else ("diff" if diff else "write")
        javascript: BiomeEmbeddedProvider | None = None
        css: BiomeEmbeddedProvider | None = None
        try:
            # A provider owns a locked executable copy, so every construction
            # is registered for cleanup before another construction can fail.
            with ExitStack() as providers:
                javascript = (
                    BiomeEmbeddedProvider.from_spec(
                        javascript_provider,
                        language="javascript",
                    )
                    if embedded != "off" and javascript_provider is not None
                    else None
                )
                if javascript is not None:
                    providers.callback(javascript.close)
                css = (
                    BiomeEmbeddedProvider.from_spec(css_provider, language="css")
                    if embedded != "off" and css_provider is not None
                    else None
                )
                if css is not None:
                    providers.callback(css.close)
                report = format_paths(
                    paths,
                    mode=mode,
                    cwd=Path.cwd(),
                    embedded=embedded,
                    javascript_provider=javascript,
                    css_provider=css,
                )
        except (EmbeddedProviderConfigError, FormatUsageError) as error:
            _usage_error(str(error))
        if verbose:
            javascript_capability = (
                "off" if embedded == "off" else (javascript.identity if javascript else "unavailable")
            )
            css_capability = "off" if embedded == "off" else (css.identity if css else "unavailable")
            sys.stderr.write(
                f"citry-html@1, python-expressions:{python_expression_provider()}, "
                f"javascript:{javascript_capability}, css:{css_capability}\n",
            )
        _print_report(report)
        if report.exit_code:
            raise SystemExit(report.exit_code)


def _print_report(report: FormatReport) -> None:
    for result in report.results:
        for notice in result.notices:
            sys.stderr.write(f"{result.display_path}: {notice}\n")
        if result.status == "formatted":
            if report.mode == "write":
                sys.stdout.write(f"formatted: {result.display_path}\n")
            elif report.mode == "check":
                sys.stdout.write(f"would format: {result.display_path}\n")
            elif result.diff is not None:
                sys.stdout.write(result.diff)
        elif result.status == "errored":
            sys.stderr.write(f"{result.display_path}: {result.message}\n")

    changed_label = "formatted" if report.mode == "write" else "would format"
    sys.stderr.write(
        f"citry format: {report.count('formatted')} {changed_label}, "
        f"{report.count('unchanged')} unchanged, "
        f"{report.count('skipped')} skipped, "
        f"{report.count('errored')} errored\n",
    )


def _usage_error(message: str) -> NoReturn:
    sys.stderr.write(f"citry format: error: {message}\n")
    raise SystemExit(2)


__all__: list[str] = []
