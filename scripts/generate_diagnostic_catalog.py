#!/usr/bin/env python
"""Generate language bindings from the versioned Citry diagnostic catalog."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from pprint import pformat
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "packages/protocol/diagnostics/v1/catalog.json"
PYTHON_PATH = ROOT / "packages/py/citry/citry/_diagnostic_catalog.py"
PARSER_RUST_PATH = ROOT / "crates/citry_template_parser/src/diagnostic_catalog.rs"
FORMATTER_RUST_PATH = ROOT / "crates/citry_template_formatter/src/diagnostic_catalog.rs"
TYPESCRIPT_PATH = ROOT / "packages/editors/vscode/src/diagnosticCatalog.ts"


def load_catalog() -> dict[str, Any]:
    """Load the checked-in catalog without importing a product package."""
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def generated_files(catalog: dict[str, Any] | None = None) -> dict[Path, str]:
    """Return every generated path and its deterministic expected contents."""
    catalog = catalog or load_catalog()
    diagnostics = catalog["diagnostics"]
    return {
        PYTHON_PATH: _python(catalog),
        PARSER_RUST_PATH: _rust(diagnostics, surface="parser"),
        FORMATTER_RUST_PATH: _rust(diagnostics, surface="formatter"),
        TYPESCRIPT_PATH: _typescript(catalog),
    }


def check_generated() -> list[str]:
    """Report generated bindings that are absent or out of date."""
    problems: list[str] = []
    for path, expected in generated_files().items():
        relative = path.relative_to(ROOT)
        if not path.is_file():
            problems.append(f"missing generated diagnostic binding: {relative}")
        elif path.read_text(encoding="utf-8") != expected:
            problems.append(
                f"stale generated diagnostic binding: {relative}; run python scripts/generate_diagnostic_catalog.py"
            )
    return problems


def write_generated() -> None:
    """Write each generated binding after catalog validation has succeeded."""
    for path, contents in generated_files().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")


def _python(catalog: dict[str, Any]) -> str:
    constants = "\n".join(f"{item['constant']} = {item['code']!r}" for item in catalog["diagnostics"])
    definitions = pformat(
        {item["code"]: item for item in catalog["diagnostics"]},
        sort_dicts=True,
        width=120,
    )
    prefixes = pformat(catalog["externalCodePrefixes"], sort_dicts=True, width=120)
    return (
        '"""Generated from packages/protocol/diagnostics/v1/catalog.json. Do not edit."""\n\n'
        "# ruff: noqa: E501, Q000\n"
        "# fmt: off\n\n"
        "from __future__ import annotations\n\n"
        "from typing import Final\n\n"
        f"SCHEMA_VERSION: Final = {catalog['schemaVersion']}\n"
        f"DOCUMENTATION_BASE_URL: Final = {catalog['documentationBaseUrl']!r}\n\n"
        f"{constants}\n\n"
        f"DIAGNOSTICS: Final = {definitions}\n\n"
        f"EXTERNAL_CODE_PREFIXES: Final = {prefixes}\n\n"
        "# fmt: on\n"
    )


def _rust(diagnostics: list[dict[str, Any]], *, surface: str) -> str:
    lines: list[str] = []
    for item in diagnostics:
        if surface not in item["surfaces"]:
            continue
        declaration = f'pub(crate) const {item["constant"]}: &str = "{item["code"]}";'
        if len(declaration) <= 100:
            lines.append(declaration)
        else:
            lines.extend(
                (
                    f"pub(crate) const {item['constant']}: &str =",
                    f'    "{item["code"]}";',
                )
            )
    constants = "\n".join(lines)
    return (
        "// Generated from packages/protocol/diagnostics/v1/catalog.json. Do not edit.\n"
        "#![allow(dead_code)]\n\n"
        f"{constants}\n"
    )


def _typescript(catalog: dict[str, Any]) -> str:
    constants = "\n".join(
        f'export const {item["constant"]} = "{item["code"]}" as const;'
        for item in catalog["diagnostics"]
        if "vscode" in item["surfaces"]
    )
    return (
        "// Generated from packages/protocol/diagnostics/v1/catalog.json. Do not edit.\n\n"
        f'export const DIAGNOSTIC_DOCUMENTATION_BASE_URL = "{catalog["documentationBaseUrl"]}" as const;\n\n'
        f"{constants}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report stale files without writing them")
    args = parser.parse_args()
    if args.check:
        problems = check_generated()
        if problems:
            for problem in problems:
                print(problem)  # noqa: T201 - command-line drift report
            return 1
        return 0
    write_generated()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
