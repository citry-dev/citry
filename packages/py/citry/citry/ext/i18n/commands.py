"""Project and standalone-package commands for the i18n extension."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from citry.command import CommandArg
from citry.extension import ExtensionCommand

from .packages import compile_catalog_package

if TYPE_CHECKING:
    from .extension import I18nExtension


class _I18nCommand(ExtensionCommand):
    def extension(self) -> I18nExtension:
        if self.citry is None:
            raise SystemExit("Run this command through 'citry ext run i18n'.")
        extension = cast("I18nExtension", self.citry.extensions.get_extension("i18n"))
        if not extension.available:
            raise SystemExit(
                "Configure extensions_defaults['i18n'] or register component messages with "
                "Component.I18n.messages_locale before running this command."
            )
        return extension


class CheckI18nCommand(_I18nCommand):
    name = "check"
    help = "Compile and validate the complete project catalog without rendering a component."

    def handle(self, **kwargs: Any) -> None:  # noqa: ARG002
        extension = self.extension()
        extension._load_project_sources()
        catalog = extension._compiled_catalog
        if catalog is None:
            raise SystemExit("The project catalog did not produce a checked runtime.")
        print(  # noqa: T201 - CLI result
            json.dumps(
                {
                    "schema_version": 1,
                    "catalog_revision": catalog.revision,
                    "formats_revision": catalog.formats_revision,
                },
                sort_keys=True,
            )
        )


class InspectI18nCommand(_I18nCommand):
    name = "inspect"
    help = "Print the complete checked project catalog artifact."
    arguments = (CommandArg(["--out"], help="Write JSON to this path instead of stdout."),)

    def handle(self, **kwargs: Any) -> None:
        extension = self.extension()
        extension._load_project_sources()
        catalog = extension._compiled_catalog
        if catalog is None:
            raise SystemExit("The project catalog did not produce a checked runtime.")
        text = json.dumps(json.loads(catalog.artifact_json()), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        out = kwargs.get("out")
        if out is None:
            print(text, end="")  # noqa: T201 - CLI artifact
        else:
            Path(out).write_text(text, encoding="utf-8")
            print(f"Wrote the checked i18n artifact to {out}.")  # noqa: T201 - CLI status


class CoverageI18nCommand(ExtensionCommand):
    name = "coverage"
    help = "Report exact translations and locale/source fallbacks for every checked output."
    arguments = (
        CommandArg(
            ["--locale"],
            action="append",
            help="Report one locale. Repeat the option to select several locales.",
        ),
        CommandArg(["--json"], action="store_true", help="Print a stable JSON report."),
        CommandArg(
            ["--fail-on-missing"],
            action="store_true",
            help="Exit with status 1 when any requested locale falls back to an owner's source locale.",
        ),
    )

    def handle(self, **kwargs: Any) -> None:
        if self.citry is None:
            raise SystemExit("Run this command through 'citry ext run i18n'.")
        extension = cast("I18nExtension", self.citry.extensions.get_extension("i18n"))
        extension._load_project_sources()
        catalog = extension._compiled_catalog
        if catalog is None:
            raise SystemExit(
                "No i18n catalog is available. Define component messages with "
                "Component.I18n.messages_locale or configure engine i18n settings."
            )
        artifact = cast("dict[str, object]", json.loads(catalog.artifact_json()))
        manifest = cast("dict[str, dict[str, dict[str, object]]]", artifact["manifest"])
        requested = kwargs.get("locale")
        if requested:
            locales = tuple(_canonical_coverage_locale(value, manifest=manifest) for value in requested)
            duplicate = next((item for index, item in enumerate(locales) if item in locales[:index]), None)
            if duplicate is not None:
                raise SystemExit(f"Coverage locale {duplicate!r} was requested more than once.")
        else:
            locales = tuple(sorted(manifest))

        locale_reports = [_coverage_locale_report(locale, manifest[locale]) for locale in locales]
        report = {
            "schema_version": 1,
            "catalog_revision": catalog.revision,
            "locales": locale_reports,
        }
        if kwargs.get("json"):
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))  # noqa: T201
        else:
            _print_coverage_report(report)
        missing = sum(cast("dict[str, int]", locale["summary"])["source_fallback"] for locale in locale_reports)
        if kwargs.get("fail_on_missing") and missing:
            raise SystemExit(1)


class ExtractI18nCommand(_I18nCommand):
    name = "extract"
    help = "Print the deterministic source-unit index used by the project compiler."

    def handle(self, **kwargs: Any) -> None:  # noqa: ARG002
        extension = self.extension()
        extension._load_project_sources()
        request = extension._compile_request(dict(extension._catalogs))
        catalogs = cast("list[dict[str, object]]", request["catalogs"])
        sources = [
            {
                "package": item["package"],
                "locale": item["locale"],
                "path": item["path"],
            }
            for item in catalogs
        ]
        print(json.dumps({"schema_version": 1, "sources": sources}, indent=2, sort_keys=True))  # noqa: T201


class CompileI18nCommand(_I18nCommand):
    name = "compile"
    help = "Write checked manifest and server artifacts into standalone catalog source packages."
    arguments = (
        CommandArg(
            "packages",
            nargs="*",
            help="Import packages to compile. The configured catalogs are used when omitted.",
        ),
    )

    def handle(self, **kwargs: Any) -> None:
        extension = self.extension()
        names = tuple(kwargs.get("packages") or extension.config.catalogs)
        if not names:
            raise SystemExit("No standalone i18n catalog packages were supplied or configured.")
        for name in names:
            manifest, server, link = compile_catalog_package(name)
            print(f"Compiled {name}: {manifest}, {server}, and {link}.")  # noqa: T201 - CLI status


def _canonical_coverage_locale(
    value: object,
    *,
    manifest: dict[str, dict[str, dict[str, object]]],
) -> str:
    from citry_core.i18n import canonicalize_locale  # noqa: PLC0415

    if type(value) is not str or not value:
        raise SystemExit(f"Coverage locale must be an exact non-empty string; got {value!r}.")
    try:
        locale = canonicalize_locale(value)
    except ValueError as error:
        raise SystemExit(f"Invalid coverage locale {value!r}: {error}") from error
    if locale not in manifest:
        available = ", ".join(repr(item) for item in sorted(manifest)) or "none"
        raise SystemExit(f"Coverage locale {locale!r} is unavailable; checked locales: {available}.")
    return locale


def _coverage_locale_report(locale: str, outputs: dict[str, dict[str, object]]) -> dict[str, object]:
    records: list[dict[str, object]] = []
    summary = {"exact": 0, "translation_fallback": 0, "source_fallback": 0}
    for token, entry in sorted(outputs.items()):
        bundle_locale = cast("str", entry["bundle_locale"])
        owner_source_locale = cast("str", entry["owner_source_locale"])
        if bundle_locale == locale:
            status = "exact"
        elif bundle_locale == owner_source_locale:
            status = "source_fallback"
        else:
            status = "translation_fallback"
        summary[status] += 1
        records.append(
            {
                "output": token,
                "status": status,
                "selected_locale": bundle_locale,
                "owner_source_locale": owner_source_locale,
                "owner": entry["owner"],
                "definition_path": entry["definition_path"],
            }
        )
    return {"locale": locale, "summary": summary, "outputs": records}


def _print_coverage_report(report: dict[str, object]) -> None:
    for locale in cast("list[dict[str, object]]", report["locales"]):
        summary = cast("dict[str, int]", locale["summary"])
        print(  # noqa: T201 - CLI result
            f"{locale['locale']}: {summary['exact']} exact, "
            f"{summary['translation_fallback']} translation fallback, "
            f"{summary['source_fallback']} source fallback"
        )
        for output in cast("list[dict[str, object]]", locale["outputs"]):
            if output["status"] == "exact":
                continue
            status = cast("str", output["status"])
            print(  # noqa: T201 - CLI result
                f"  {output['output']}: {status.replace('_', ' ')} "
                f"via {output['selected_locale']} (source {output['owner_source_locale']})"
            )


I18N_COMMANDS = (
    ExtractI18nCommand,
    CheckI18nCommand,
    CompileI18nCommand,
    InspectI18nCommand,
    CoverageI18nCommand,
)

__all__ = ["I18N_COMMANDS"]
