"""Keep Citry-owned diagnostic codes and generated bindings in one catalog."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
from string import Formatter
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "packages/protocol/diagnostics/v1/catalog.json"
GENERATOR_PATH = ROOT / "scripts/generate_diagnostic_catalog.py"
CODE_RE = re.compile(
    r"(?P<quote>['\"])(?P<code>citry\."
    r"(?:parse|template|component|check|format|python)\."
    r"[a-z0-9][a-z0-9.-]*)(?P=quote)"
)
CODE_RE_FULL = re.compile(r"citry\.[a-z0-9]+(?:[.-][a-z0-9]+)*\Z")
CONSTANT_RE = re.compile(r"[A-Z][A-Z0-9_]*\Z")
SURFACES = frozenset({"parser", "formatter", "check", "lsp", "vscode"})
SEVERITIES = frozenset({"error", "warning", "information"})
IMPLEMENTATION_ROOTS = (
    ROOT / "crates/citry_template_parser/src",
    ROOT / "crates/citry_template_formatter/src",
    ROOT / "packages/py/citry/citry",
    ROOT / "packages/py/citry_lsp/citry_lsp",
    ROOT / "packages/editors/vscode/src",
)
GENERATED_PATHS = {
    ROOT / "packages/py/citry/citry/_diagnostic_catalog.py",
    ROOT / "crates/citry_template_parser/src/diagnostic_catalog.rs",
    ROOT / "crates/citry_template_formatter/src/diagnostic_catalog.rs",
    ROOT / "packages/editors/vscode/src/diagnosticCatalog.ts",
}


def check() -> list[str]:
    """Return every catalog, generated-binding, and code-ownership problem."""
    problems: list[str] = []
    try:
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"cannot load diagnostic catalog: {error}"]
    codes, prefixes = _validate_catalog(catalog, problems)
    problems.extend(_generated_problems())
    problems.extend(_code_literal_problems(codes, prefixes))
    return problems


def _validate_catalog(catalog: Any, problems: list[str]) -> tuple[set[str], tuple[str, ...]]:
    if type(catalog) is not dict:
        problems.append("diagnostic catalog root must be an object")
        return set(), ()
    expected_root = {"schemaVersion", "documentationBaseUrl", "externalCodePrefixes", "diagnostics"}
    if set(catalog) != expected_root:
        problems.append("diagnostic catalog root fields do not match the v1 schema")
    if catalog.get("schemaVersion") != 1:
        problems.append("diagnostic catalog schemaVersion must remain 1 for this directory")
    if catalog.get("documentationBaseUrl") != "https://citry.dev":
        problems.append("diagnostic documentationBaseUrl must be https://citry.dev")

    prefixes: list[str] = []
    raw_prefixes = catalog.get("externalCodePrefixes")
    if type(raw_prefixes) is not list:
        problems.append("externalCodePrefixes must be an array")
    else:
        for index, raw in enumerate(raw_prefixes):
            label = f"externalCodePrefixes[{index}]"
            if type(raw) is not dict or set(raw) != {"prefix", "provider", "summary"}:
                problems.append(f"{label} fields do not match the v1 schema")
                continue
            prefix = raw.get("prefix")
            if type(prefix) is not str or not prefix.startswith("citry.") or not prefix.endswith("."):
                problems.append(f"{label}.prefix must be a Citry code prefix ending in a dot")
            elif prefix in prefixes:
                problems.append(f"duplicate external diagnostic prefix {prefix!r}")
            else:
                prefixes.append(prefix)
            for field in ("provider", "summary"):
                if type(raw.get(field)) is not str or not raw[field].strip():
                    problems.append(f"{label}.{field} must be a non-empty string")

    codes: set[str] = set()
    constants: set[str] = set()
    raw_diagnostics = catalog.get("diagnostics")
    if type(raw_diagnostics) is not list or not raw_diagnostics:
        problems.append("diagnostics must be a non-empty array")
        return codes, tuple(prefixes)
    required = {
        "code",
        "constant",
        "title",
        "summary",
        "when",
        "defaultSeverity",
        "surfaces",
        "parameters",
        "messages",
        "documentationPath",
    }
    optional = {"configurableSeverity", "examples"}
    for index, raw in enumerate(raw_diagnostics):
        label = f"diagnostics[{index}]"
        if type(raw) is not dict:
            problems.append(f"{label} must be an object")
            continue
        if set(raw) - required - optional or required - set(raw):
            problems.append(f"{label} fields do not match the v1 schema")
            continue
        code = raw["code"]
        constant = raw["constant"]
        if type(code) is not str or CODE_RE_FULL.fullmatch(code) is None:
            problems.append(f"{label}.code is not a valid Citry diagnostic code")
        elif code in codes:
            problems.append(f"duplicate diagnostic code {code!r}")
        else:
            codes.add(code)
        if type(constant) is not str or CONSTANT_RE.fullmatch(constant) is None:
            problems.append(f"{label}.constant is not an uppercase identifier")
        elif constant in constants:
            problems.append(f"duplicate diagnostic constant {constant!r}")
        else:
            constants.add(constant)
        for field in ("title", "summary", "when"):
            if type(raw[field]) is not str or not raw[field].strip():
                problems.append(f"{label}.{field} must be a non-empty string")
        if raw["defaultSeverity"] not in SEVERITIES:
            problems.append(f"{label}.defaultSeverity is invalid")
        if "configurableSeverity" in raw and type(raw["configurableSeverity"]) is not bool:
            problems.append(f"{label}.configurableSeverity must be a boolean")
        surfaces = raw["surfaces"]
        if (
            type(surfaces) is not list
            or not surfaces
            or len(surfaces) != len(set(surfaces))
            or any(surface not in SURFACES for surface in surfaces)
        ):
            problems.append(f"{label}.surfaces must contain unique supported surfaces")
        parameters = raw["parameters"]
        messages = raw["messages"]
        if type(parameters) is not dict or any(
            type(name) is not str or not name or type(description) is not str or not description.strip()
            for name, description in parameters.items()
        ):
            problems.append(f"{label}.parameters must describe named string parameters")
            parameters = {}
        if type(messages) is not dict or not messages:
            problems.append(f"{label}.messages must be a non-empty object")
        else:
            for variant, template in messages.items():
                if type(variant) is not str or not variant or type(template) is not str or not template:
                    problems.append(f"{label}.messages contains an invalid variant")
                    continue
                try:
                    placeholders = {name for _, name, _, _ in Formatter().parse(template) if name is not None}
                except ValueError as error:
                    problems.append(f"{label}.messages.{variant} is invalid: {error}")
                    continue
                if not placeholders.issubset(parameters):
                    unknown = ", ".join(sorted(placeholders - set(parameters)))
                    problems.append(f"{label}.messages.{variant} uses undeclared parameter(s): {unknown}")
        examples = raw.get("examples")
        if examples is not None:
            if type(examples) is not list or not examples:
                problems.append(f"{label}.examples must be a non-empty array")
            else:
                for example_index, example in enumerate(examples):
                    example_label = f"{label}.examples[{example_index}]"
                    if type(example) is not dict or set(example) not in (
                        {"title", "language", "source"},
                        {"title", "language", "source", "description"},
                    ):
                        problems.append(f"{example_label} fields do not match the v1 schema")
                        continue
                    for field in ("title", "language", "source"):
                        if type(example[field]) is not str or not example[field].strip():
                            problems.append(f"{example_label}.{field} must be a non-empty string")
                    description = example.get("description")
                    if description is not None and (type(description) is not str or not description.strip()):
                        problems.append(f"{example_label}.description must be a non-empty string")
        expected_path = f"/ide/diagnostics/#{code}"
        if raw["documentationPath"] != expected_path:
            problems.append(f"{label}.documentationPath must be {expected_path!r}")
    for code in codes:
        if any(code.startswith(prefix) for prefix in prefixes):
            problems.append(f"catalog code {code!r} overlaps an external provider prefix")
    return codes, tuple(prefixes)


def _generated_problems() -> list[str]:
    spec = importlib.util.spec_from_file_location("diagnostic_catalog_generator", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        return ["cannot load scripts/generate_diagnostic_catalog.py"]
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.check_generated()


def _code_literal_problems(codes: set[str], prefixes: tuple[str, ...]) -> list[str]:
    """Reject uncataloged IDs and catalog-value duplication outside generated bindings."""
    problems: list[str] = []
    for root in IMPLEMENTATION_ROOTS:
        for path in root.rglob("*"):
            if path in GENERATED_PATHS or not path.is_file() or path.suffix not in {".py", ".rs", ".ts"}:
                continue
            if any(part in {"tests", "out", "__pycache__"} for part in path.parts) or path.name == "corpus.rs":
                continue
            source = path.read_text(encoding="utf-8")
            for match in CODE_RE.finditer(source):
                code = match.group("code")
                if code in codes:
                    problems.append(
                        f"{path.relative_to(ROOT)} duplicates catalog code {code!r}; use the generated binding"
                    )
                elif not any(code.startswith(prefix) for prefix in prefixes):
                    problems.append(f"{path.relative_to(ROOT)} uses uncataloged diagnostic code {code!r}")
    return problems
