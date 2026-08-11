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
        if not extension.configured:
            raise SystemExit("Configure extensions_defaults['i18n'] before running this command.")
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


I18N_COMMANDS = (ExtractI18nCommand, CheckI18nCommand, CompileI18nCommand, InspectI18nCommand)

__all__ = ["I18N_COMMANDS"]
