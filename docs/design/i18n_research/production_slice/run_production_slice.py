from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import json
import math
import platform
import re
import resource
import statistics
import subprocess
import sys
import tempfile
import time
import zipfile
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any

from citry import Citry, Component, Extension
from citry.assets import _load_pair
from citry.constness import const_value
from citry.extension import TemplateNamespaceContribution
from citry_core.template_parser import parse_template

if TYPE_CHECKING:
    from collections.abc import Iterator

    from citry.slots import Slot


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RUST = HERE / "rust"
FIXTURES = HERE / "fixtures"
FSI = "\u2068"
PDI = "\u2069"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_command(command: list[str], *, cwd: Path = REPO) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.returncode:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(command)}\n{completed.stdout}")
    return completed.stdout.strip()


def build_extension() -> tuple[Any, dict[str, str]]:
    with tempfile.TemporaryDirectory(prefix="citry-i18n-phase0-wheel-") as wheel_dir_text:
        wheel_dir = Path(wheel_dir_text)
        run_command(
            [
                "uv",
                "run",
                "--frozen",
                "maturin",
                "build",
                "--manifest-path",
                str(RUST / "Cargo.toml"),
                "--locked",
                "--interpreter",
                sys.executable,
                "--out",
                str(wheel_dir),
            ]
        )
        wheels = sorted(wheel_dir.glob("*.whl"))
        require(len(wheels) == 1, f"expected one wheel, got {wheels!r}")
        wheel = wheels[0]
        extracted = Path(tempfile.mkdtemp(prefix="citry-i18n-phase0-import-"))
        with zipfile.ZipFile(wheel) as archive:
            archive.extractall(extracted)
    sys.path.insert(0, str(extracted))
    module = importlib.import_module("citry_i18n_phase0")
    extension_binary = Path(module.citry_i18n_phase0.__file__)
    return module, {
        "cargo_lock_sha256": sha256(RUST / "Cargo.lock"),
        "cargo_manifest_sha256": sha256(RUST / "Cargo.toml"),
        "extension_binary_sha256": sha256(extension_binary),
        "python_package_initializer_sha256": sha256(Path(module.__file__)),
        "rust_source_sha256": sha256(RUST / "src" / "lib.rs"),
    }


def catalog(path: str, package: str, layer: str, precedence: int, locale: str) -> dict[str, Any]:
    fixture = FIXTURES / path
    return {
        "path": f"fixtures/{path}",
        "package": package,
        "layer": layer,
        "precedence": precedence,
        "locale": locale,
        "source": fixture.read_text(encoding="utf-8"),
    }


def base_request() -> dict[str, Any]:
    return {
        "schema_version": 2,
        "active_locales": ["en-US", "cs-CZ"],
        "packages": [
            {
                "name": "citry_ui",
                "source_locale": "en-US",
                "exports": [
                    "citry-ui-account",
                    "citry-ui-fallback-only",
                    "citry-ui-ref-target",
                    "citry-ui-ref-wrapper",
                    "citry-ui-item-count",
                    "citry-ui-rank",
                    "citry-ui-balance",
                    "citry-ui-due",
                ],
            },
            {
                "name": "my_app",
                "source_locale": "cs-CZ",
                "exports": [
                    "my-app-rich-choice",
                    "my-app-source-only",
                    "my-app-target",
                    "my-app-wrapper",
                ],
            },
        ],
        "catalogs": [
            catalog("citry_ui/en-US.ftl", "citry_ui", "citry_ui", 0, "en-US"),
            catalog("citry_ui/cs-CZ.ftl", "citry_ui", "citry_ui", 0, "cs-CZ"),
            catalog("application/en-US.ftl", "my_app", "application", 1, "en-US"),
            catalog("application/cs-CZ.ftl", "my_app", "application", 1, "cs-CZ"),
        ],
    }


def compile_json(compiler: Any, request: dict[str, Any]) -> dict[str, Any]:
    payload = json.dumps(request, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return json.loads(compiler.compile(payload))


def copy_json(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False))


def capture_compile_error(module: Any, request: dict[str, Any]) -> dict[str, Any]:
    compiler = module.CatalogCompiler()
    try:
        compile_json(compiler, request)
    except module.I18nCompileError as error:
        result = {
            "code": error.code,
            "message": str(error),
            "path": error.path,
            "start": error.start,
            "end": error.end,
            "line": error.line,
            "column": error.column,
            "message_id": error.message_id,
            "related": json.loads(error.related_json),
        }
        require(result["code"].startswith("I18N_"), f"unstable diagnostic code: {result!r}")
        return result
    raise RuntimeError("compile request unexpectedly succeeded")


def negative_requests(module: Any) -> dict[str, dict[str, Any]]:
    malformed = base_request()
    malformed["catalogs"][1]["source"] += "\nbroken = {\n"

    added_variable = base_request()
    added_variable["catalogs"][2]["source"] = added_variable["catalogs"][2]["source"].replace(
        "accepted { $terms_link }", "accepted { $terms_link } { $extra }"
    )

    missing_slot = base_request()
    missing_slot["catalogs"][2]["source"] = missing_slot["catalogs"][2]["source"].replace(
        "my-app-target = { $name } accepted { $terms_link }; details: { $terms_link }.",
        "my-app-target = { $name } accepted.",
    )

    missing_branch_slot = base_request()
    missing_branch_slot["catalogs"][2]["source"] = missing_branch_slot["catalogs"][2]["source"].replace(
        "*[other] { $name }: { $terms_link }, then { $terms_link }",
        "*[other] { $name }: no link on this branch",
    )

    missing_profile = base_request()
    missing_profile["catalogs"][0]["source"] = missing_profile["catalogs"][0]["source"].replace(
        'citry-ui-balance = Balance: { NUMBER($amount, profile: "decimal") }',
        "citry-ui-balance = Balance: { NUMBER($amount) }",
    )

    bidi_literal = base_request()
    bidi_literal["catalogs"][0]["source"] = bidi_literal["catalogs"][0]["source"].replace(
        "citry-ui-fallback-only = LIBRARY SOURCE FALLBACK",
        "citry-ui-fallback-only = \u2069",
    )

    bidi_u4 = base_request()
    bidi_u4["catalogs"][0]["source"] = bidi_u4["catalogs"][0]["source"].replace(
        "citry-ui-fallback-only = LIBRARY SOURCE FALLBACK",
        'citry-ui-fallback-only = { "\\u2069" }',
    )

    bidi_u6 = base_request()
    bidi_u6["catalogs"][0]["source"] = bidi_u6["catalogs"][0]["source"].replace(
        "citry-ui-fallback-only = LIBRARY SOURCE FALLBACK",
        'citry-ui-fallback-only = { "\\U002069" }',
    )

    conflict_source = """
# @param {str} $shared
app-a = A { $shared }
# @param {Slot} $shared
app-b = B { $shared }
app-wrapper = { app-a } { app-b }
""".lstrip()
    conflict = {
        "schema_version": 2,
        "active_locales": ["en-US"],
        "packages": [
            {
                "name": "app",
                "source_locale": "en-US",
                "exports": ["app-a", "app-b", "app-wrapper"],
            }
        ],
        "catalogs": [
            {
                "path": "fixtures/negative/type-conflict.ftl",
                "package": "app",
                "layer": "app",
                "precedence": 0,
                "locale": "en-US",
                "source": conflict_source,
            }
        ],
    }

    select_source = """
# @param {str} $mode
app-select = { $mode ->
    [one] One
   *[other] Other
}
""".lstrip()
    select = {
        "schema_version": 2,
        "active_locales": ["en-US"],
        "packages": [{"name": "app", "source_locale": "en-US", "exports": ["app-select"]}],
        "catalogs": [
            {
                "path": "fixtures/negative/select.ftl",
                "package": "app",
                "layer": "app",
                "precedence": 0,
                "locale": "en-US",
                "source": select_source,
            }
        ],
    }

    unknown_field = base_request()
    unknown_field["unexpected"] = True

    stale_schema = base_request()
    stale_schema["schema_version"] = 1

    authored_slot = {
        "schema_version": 2,
        "active_locales": ["en-US"],
        "packages": [{"name": "app", "source_locale": "en-US", "exports": ["app-slot"]}],
        "catalogs": [
            {
                "path": "fixtures/negative/authored-slot.ftl",
                "package": "app",
                "layer": "app",
                "precedence": 0,
                "locale": "en-US",
                "source": "# @param {Slot} $link\napp-slot = { SLOT($link) }\n",
            }
        ],
    }

    return {
        "malformed_fluent": capture_compile_error(module, malformed),
        "translation_added_variable": capture_compile_error(module, added_variable),
        "translation_missing_slot": capture_compile_error(module, missing_slot),
        "translation_branch_missing_slot": capture_compile_error(module, missing_branch_slot),
        "transitive_type_conflict": capture_compile_error(module, conflict),
        "invalid_selector_type": capture_compile_error(module, select),
        "missing_format_profile": capture_compile_error(module, missing_profile),
        "literal_bidi_control": capture_compile_error(module, bidi_literal),
        "escaped_u4_bidi_control": capture_compile_error(module, bidi_u4),
        "escaped_u6_bidi_control": capture_compile_error(module, bidi_u6),
        "stale_schema": capture_compile_error(module, stale_schema),
        "authored_slot_function": capture_compile_error(module, authored_slot),
        "strict_unknown_field": capture_compile_error(module, unknown_field),
    }


def direct_tr_metadata(template: str) -> dict[str, Any]:
    parsed = parse_template(template)
    records: list[dict[str, Any]] = []
    unsupported: list[dict[str, Any]] = []
    for element in parsed.elements:
        value = getattr(element, "_0", None)
        if not hasattr(value, "value"):
            continue
        source = value.value.content.strip()
        expression = ast.parse(source, mode="eval").body
        tr_calls = [
            node
            for node in ast.walk(expression)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "tr"
        ]
        if not tr_calls:
            continue
        direct = expression if isinstance(expression, ast.Call) else None
        if direct is None or not isinstance(direct.func, ast.Name) or direct.func.id != "tr":
            unsupported.append(
                {
                    "code": "I18N_TEMPLATE_CALL_NOT_DIRECT",
                    "line": value.value.line_col[0],
                    "column": value.value.line_col[1],
                }
            )
            continue
        if (
            not direct.args
            or not isinstance(direct.args[0], ast.Constant)
            or not isinstance(direct.args[0].value, str)
        ):
            unsupported.append(
                {
                    "code": "I18N_TEMPLATE_ID_NOT_LITERAL",
                    "line": value.value.line_col[0],
                    "column": value.value.line_col[1],
                }
            )
            continue
        records.append(
            {
                "message_id": direct.args[0].value,
                "keywords": sorted(keyword.arg for keyword in direct.keywords if keyword.arg is not None),
                "start": value.value.start_index,
                "end": value.value.end_index,
                "line": value.value.line_col[0],
                "column": value.value.line_col[1],
            }
        )
    return {"direct_calls": records, "unsupported": unsupported}


def parser_metadata() -> dict[str, Any]:
    rich = (
        '<c-trans id="citry-ui-account" c-values="{\'name\': name}">'
        '<c-fill name="terms_link"><a>Terms</a></c-fill></c-trans>'
    )
    rich_debug = repr(parse_template(rich).elements[0])
    direct = direct_tr_metadata('{{ tr("citry-ui-account", name=name) }}')
    composed = direct_tr_metadata('{{ tr("citry-ui-account", name=name).upper() }}')
    dynamic = direct_tr_metadata("{{ tr(message_id, name=name) }}")
    result = {
        "direct_call": direct,
        "composed_call": composed,
        "dynamic_id": dynamic,
        "rich_component": {
            "ordinary_component": 'content: "c-trans"' in rich_debug,
            "ordinary_fill": 'content: "c-fill"' in rich_debug,
            "contains_fills": "contains_fills: true" in rich_debug,
            "spans": all(marker in rich_debug for marker in ("start_index:", "end_index:", "line_col:")),
        },
    }
    require(len(direct["direct_calls"]) == 1, f"direct tr() metadata missing: {result!r}")
    require(
        composed["unsupported"] == [{"code": "I18N_TEMPLATE_CALL_NOT_DIRECT", "line": 1, "column": 4}],
        f"composed tr() was not classified: {result!r}",
    )
    require(
        dynamic["unsupported"] == [{"code": "I18N_TEMPLATE_ID_NOT_LITERAL", "line": 1, "column": 4}],
        f"dynamic tr() was not classified: {result!r}",
    )
    require(all(result["rich_component"].values()), f"rich parser metadata missing: {result!r}")
    return result


def strip_controls(value: str) -> str:
    return value.replace(FSI, "").replace(PDI, "")


def tagged_value(type_name: str, value: Any) -> dict[str, str]:
    if type_name == "str":
        require(isinstance(value, str), f"str value must be text, got {type(value)!r}")
        return {"type": "str", "value": value}
    if type_name == "int":
        require(isinstance(value, int) and not isinstance(value, bool), f"int value is invalid: {value!r}")
        return {"type": "int", "value": str(value)}
    if type_name == "Decimal":
        require(isinstance(value, Decimal), f"Decimal value is invalid: {value!r}")
        return {"type": "decimal", "value": str(value)}
    if type_name == "datetime":
        require(isinstance(value, datetime) and value.tzinfo is not None, f"datetime needs an offset: {value!r}")
        rendered = value.isoformat().replace("+00:00", "Z")
        return {"type": "datetime", "value": rendered}
    if type_name == "Slot":
        require(isinstance(value, str), f"Slot marker must be text, got {type(value)!r}")
        return {"type": "slot", "value": value}
    raise RuntimeError(f"unsupported Phase 0 source type {type_name!r}")


def tagged_args(contract: dict[str, str], values: dict[str, Any]) -> dict[str, dict[str, str]]:
    require(set(values) == set(contract), f"argument names do not match contract: {values!r} vs {contract!r}")
    return {name: tagged_value(contract[name], values[name]) for name in sorted(contract)}


def source_map_proof(compiled: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    sources = {item["path"]: item["source"] for item in request["catalogs"]}
    expected_generated = {
        "scalar": "CITRY_TEXT(",
        "slot": "SLOT(",
        "public-reference": "citry-",
        "private-term": "citry-term-",
        "plural-selector": "CITRY_PLURAL(",
        "ordinal-selector": "CITRY_PLURAL(",
        "number": "NUMBER(",
        "datetime": "DATETIME(",
    }
    authored_ranges = []
    for item in compiled["source_maps"]:
        source = sources[item["authored_path"]]
        artifact = compiled["artifacts"][item["generated_locale"]]
        source_bytes = source.encode()
        artifact_bytes = artifact.encode()
        authored = source_bytes[item["authored_start"] : item["authored_end"]].decode()
        generated = artifact_bytes[item["generated_start"] : item["generated_end"]].decode()
        require(authored, f"empty authored source range: {item!r}")
        require(
            generated.startswith(expected_generated[item["kind"]]),
            f"generated range does not match {item['kind']}: {generated!r}",
        )
        prefix = source_bytes[: item["authored_start"]]
        require(item["authored_line"] == prefix.count(b"\n") + 1, f"authored line drift: {item!r}")
        require(
            item["authored_column"] == item["authored_start"] - prefix.rfind(b"\n"),
            f"authored column drift: {item!r}",
        )
        authored_ranges.append(
            (
                item["generated_locale"],
                item["internal_id"],
                item["authored_path"],
                item["authored_start"],
                item["authored_end"],
                item["kind"],
            )
        )
    kinds = {item["kind"] for item in compiled["source_maps"]}
    expected_kinds = set(expected_generated)
    repeated_slots = [
        item for item in compiled["source_maps"] if item["kind"] == "slot" and item["output"] == "my-app-rich-choice"
    ]
    result = {
        "all_ranges_replay": True,
        "all_operation_kinds_present": kinds == expected_kinds,
        "authored_ranges_are_distinct": len(authored_ranges) == len(set(authored_ranges)),
        "repeated_slot_occurrences_mapped": len(repeated_slots) >= 4
        and len({(item["authored_path"], item["authored_start"]) for item in repeated_slots}) >= 4,
    }
    require(all(result.values()), f"source-map proof failed: {result!r}; kinds={kinds!r}")
    return result


def runtime_proof(module: Any, compiled_json: str, compiled: dict[str, Any]) -> dict[str, Any]:
    runtime = module.I18nRuntime(compiled_json)

    def formatted(locale: str, message_id: str, values: dict[str, Any]) -> str:
        contract = compiled["manifest"][locale][message_id]["contract"]
        return strip_controls(
            runtime.format(
                locale,
                message_id,
                json.dumps(
                    tagged_args(contract, values),
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ),
            )
        )

    marker = "__CITRY_SLOT_PHASE0_RUNTIME_TERMS__"
    samples = {
        "czech_fractional_many": formatted("cs-CZ", "citry-ui-item-count", {"count": Decimal("2.5")}),
        "english_exact_zero": formatted("en-US", "citry-ui-item-count", {"count": Decimal(0)}),
        "english_signed_zero": formatted("en-US", "citry-ui-item-count", {"count": Decimal("-0.0")}),
        "english_ordinal": formatted("en-US", "citry-ui-rank", {"position": 21}),
        "exact_large_integer": formatted("en-US", "citry-ui-rank", {"position": 9007199254740993}),
        "exact_large_decimal": formatted("en-US", "citry-ui-balance", {"amount": Decimal("9007199254740993.25")}),
        "tagged_datetime": formatted(
            "en-US",
            "citry-ui-due",
            {"when": datetime.fromisoformat("2026-08-10T12:34:56+00:00")},
        ),
        "repeated_slot": formatted(
            "cs-CZ",
            "my-app-rich-choice",
            {"count": 1, "name": "Ada", "terms_link": marker},
        ),
    }
    gates = {
        "czech_fractional_many": "2.5" in samples["czech_fractional_many"]
        and "položky" in samples["czech_fractional_many"],
        "english_exact_zero": samples["english_exact_zero"] == "No items",
        "english_signed_zero": samples["english_signed_zero"] == "No items",
        "english_ordinal": "21" in samples["english_ordinal"] and samples["english_ordinal"].endswith("st"),
        "large_integer_preserved": "9007199254740993" in samples["exact_large_integer"],
        "large_decimal_preserved": "9007199254740993.25" in samples["exact_large_decimal"],
        "datetime_preserved": "2026-08-10T12:34:56Z" in samples["tagged_datetime"],
        "slot_repeated": samples["repeated_slot"].count(marker) == 2,
    }
    require(all(gates.values()), f"runtime gates failed: {gates!r}; samples={samples!r}")

    account_contract = compiled["manifest"]["en-US"]["citry-ui-account.aria-label"]["contract"]
    invalid = {}
    invalid_cases = {
        "wrong_tag": (
            "citry-ui-account",
            "aria-label",
            {"name": {"type": "int", "value": "1"}},
        ),
        "bidi_control": (
            "citry-ui-account",
            "aria-label",
            tagged_args(account_contract, {"name": "Ada\u2069override"}),
        ),
        "paragraph_boundary": (
            "citry-ui-account",
            "aria-label",
            tagged_args(account_contract, {"name": "Ada\nBob"}),
        ),
        "noncanonical_decimal": (
            "citry-ui-balance",
            None,
            {"amount": {"type": "decimal", "value": "01.50"}},
        ),
        "nonfinite_decimal": (
            "citry-ui-balance",
            None,
            {"amount": {"type": "decimal", "value": "Infinity"}},
        ),
        "datetime_without_zone": (
            "citry-ui-due",
            None,
            {"when": {"type": "datetime", "value": "2026-08-10T12:34:56"}},
        ),
        "invalid_slot_marker": (
            "my-app-rich-choice",
            None,
            {
                "count": {"type": "int", "value": "1"},
                "name": {"type": "str", "value": "Ada"},
                "terms_link": {"type": "slot", "value": "predictable"},
            },
        ),
    }
    for name, (message_id, attribute, payload) in invalid_cases.items():
        try:
            runtime.format(
                "en-US",
                message_id,
                json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
                attribute,
            )
        except ValueError as error:
            invalid[name] = str(error)
        else:
            raise RuntimeError(f"runtime accepted invalid tagged input {name}")
    stale_artifact = copy_json(compiled)
    stale_artifact["schema_version"] = 1
    try:
        module.I18nRuntime(json.dumps(stale_artifact, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
    except ValueError as error:
        invalid["stale_artifact_schema"] = str(error)
    else:
        raise RuntimeError("runtime accepted a stale compiled artifact schema")
    require(set(invalid) == {*invalid_cases, "stale_artifact_schema"}, f"runtime rejections drifted: {invalid!r}")
    return {"gates": gates, "rejections": invalid, "samples": samples}


def integration_proof(
    module: Any,
    compiled_json: str,
    compiled: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    runtime = module.I18nRuntime(compiled_json)
    locale_var: ContextVar[str] = ContextVar("phase0_locale", default="cs-CZ")

    class PrototypeI18n(Extension):
        name = "i18n"
        render_cache_mode = "stateless"
        render_cache_version = 1

        class Config(Extension.Config):
            client_messages: tuple[str, ...] = ()

            def tr(self, message_id: str, /, **values: Any) -> str:
                extension = self.component.citry.extensions.get_extension("i18n")
                return extension.tr(message_id, **values)

        def validate_config_fields(
            self,
            fields: dict[str, Any],
            *,
            component: type[Component] | None = None,
        ) -> None:
            for field, value in fields.items():
                if field != "client_messages":
                    raise ValueError(f"unknown i18n config field {field!r}")
                if component is None:
                    raise ValueError("client_messages is component-only")
                if not isinstance(value, tuple) or any(not isinstance(item, str) or not item for item in value):
                    raise ValueError("client_messages must be a tuple of non-empty strings")
                if len(value) != len(set(value)):
                    raise ValueError("client_messages cannot contain duplicates")

        def inspect_template_namespace(self, ctx: Any) -> TemplateNamespaceContribution:  # noqa: ARG002
            return TemplateNamespaceContribution(template_variables={"tr": "Callable[..., str]"})

        def on_component_data(self, ctx: Any) -> None:
            if "tr" in ctx.template_data:
                raise ValueError("template variable 'tr' is reserved while i18n is installed")
            ctx.template_data["tr"] = self.tr

        def tr(self, message_id: str, /, *, attribute: str | None = None, **values: Any) -> str:
            active_locale = locale_var.get()
            token = message_id if attribute is None else f"{message_id}.{attribute}"
            contract = compiled["manifest"][active_locale][token]["contract"]
            return runtime.format(
                active_locale,
                message_id,
                json.dumps(
                    tagged_args(contract, values),
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                attribute,
            )

        def rich(self, message_id: str, values: dict[str, Any], slots: dict[str, Slot]) -> tuple[Any, ...]:
            token = compiled["manifest"][locale_var.get()][message_id]
            contract = token["contract"]
            scalar_names = {name for name, type_name in contract.items() if type_name != "Slot"}
            slot_names = {name for name, type_name in contract.items() if type_name == "Slot"}
            if set(values) != scalar_names or set(slots) != slot_names:
                raise ValueError(
                    f"rich inputs mismatch: values={sorted(values)}, slots={sorted(slots)}, contract={contract}"
                )
            args = dict(values)
            markers: dict[str, Slot] = {}
            for index, name in enumerate(sorted(slots)):
                marker = f"__CITRY_SLOT_PHASE0_{index}_{name}__"
                args[name] = marker
                markers[marker] = slots[name]
            rendered = runtime.format(
                locale_var.get(),
                message_id,
                json.dumps(
                    tagged_args(contract, args),
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ),
            )
            segments: list[Any] = []
            cursor = 0
            marker_pattern = re.compile("|".join(re.escape(marker) for marker in markers))
            for match in marker_pattern.finditer(rendered):
                if match.start() > cursor:
                    segments.append(rendered[cursor : match.start()])
                segments.append(markers[match.group(0)])
                cursor = match.end()
            if cursor < len(rendered):
                segments.append(rendered[cursor:])
            return tuple(segments)

        @contextmanager
        def locale(self, locale: str) -> Iterator[None]:
            token = locale_var.set(locale)
            try:
                yield
            finally:
                locale_var.reset(token)

    app = Citry(extensions=[PrototypeI18n], autodiscover=False)

    class InlineMessages(Component):
        citry = app
        name = "phase0-inline-messages"
        messages = """
            inline-message = Inline.
        """

    class FileMessages(Component):
        citry = app
        name = "phase0-file-messages"
        messages_file = "fixtures/component_messages.ftl"

    class ConflictingMessages(Component):
        citry = app
        name = "phase0-conflicting-messages"
        messages = "conflict = Inline."
        messages_file = "fixtures/component_messages.ftl"

    inline_content, inline_path = _load_pair(InlineMessages, "messages", "messages_file")
    file_content, file_path = _load_pair(FileMessages, "messages", "messages_file")
    try:
        _load_pair(ConflictingMessages, "messages", "messages_file")
    except ValueError as error:
        pair_error = str(error)
    else:
        raise RuntimeError("the prototype message loader accepted both messages and messages_file")
    asset_proof = {
        "inline_dedented": inline_content == "\ninline-message = Inline.\n",
        "inline_has_no_path": inline_path is None,
        "file_loaded": file_content == (FIXTURES / "component_messages.ftl").read_text(encoding="utf-8"),
        "file_resolved": file_path == (FIXTURES / "component_messages.ftl").resolve(),
        "file_index_registered": FileMessages in app.get_components_for_file(FIXTURES / "component_messages.ftl"),
        "pair_not_core_validated": "both 'messages' and 'messages_file'" in pair_error,
    }
    require(all(asset_proof.values()), f"message asset integration failed: {asset_proof!r}")

    class AccountCard(Component):
        citry = app
        name = "phase0-account-card"

        class I18n:
            client_messages = ("citry-ui-account",)

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:  # noqa: ARG002
            return {
                "name": kwargs["name"],
                "python_label": self.i18n.tr("citry-ui-account", attribute="aria-label", name=kwargs["name"]),
            }

        template = """
          <span>{{ python_label }}</span>
          <span>{{ tr("citry-ui-account", attribute="aria-label", name=name) }}</span>
        """

    class Trans(Component):
        citry = app
        name = "trans"
        transparent = True
        template = '<c-for each="segment in segments">{{ segment }}</c-for>'

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            extension = self.citry.extensions.get_extension("i18n")
            return {
                "segments": extension.rich(
                    const_value(kwargs["id"]),
                    const_value(kwargs.get("values", {})),
                    slots,
                )
            }

    class RichPage(Component):
        citry = app
        name = "phase0-rich-page"
        transparent = True
        template = """
          <c-trans id="citry-ui-account" c-values="{'name': name}">
            <c-fill name="terms_link"><a href="/terms">Terms &amp; conditions</a></c-fill>
          </c-trans>
        """

    card_html = AccountCard(name="<Ada>").render().serialize()
    page_html = RichPage(name="<Ada>").render().serialize()
    extension = app.extensions.get_extension("i18n")
    with extension.locale("en-US"):
        english_page = RichPage(name="Ada").render().serialize()

    visible_card = re.sub(r' data-cid-[^=]+=""', "", strip_controls(card_html))
    visible_page = strip_controls(page_html)
    visible_english = strip_controls(english_page)
    integration = {
        "template_tr_injected": visible_card.count("Akce účtu pro &lt;Ada&gt;") == 2,
        "python_self_i18n": visible_card.count("Akce účtu pro &lt;Ada&gt;") == 2,
        "component_config_scoped": AccountCard.I18n.client_messages == ("citry-ui-account",),
        "ordinary_trans_component": "APPLICATION-CS:" in visible_page,
        "private_term_scoped": "LIBRARY-CS" not in visible_page,
        "application_anchor_preserved_twice": visible_page.count('<a href="/terms">') == 2,
        "scalar_escaped": "&lt;Ada&gt;" in visible_page,
        "english_switch": "APPLICATION-EN:" in visible_english and "accepted" in visible_english,
        "runtime_revision": runtime.revision == compiled["revision"],
    }
    require(all(integration.values()), f"Citry integration failed: {integration!r}\n{visible_page}")

    localized_template = "\n".join(
        ['<span>{{ tr("citry-ui-account", attribute="aria-label", name=name) }}</span>' for _ in range(100)]
        + ['<span>{{ tr("citry-ui-balance", amount=amount) }}</span>' for _ in range(20)]
    )
    literal_template = "\n".join(
        ["<span>Akce účtu pro Ada</span>" for _ in range(100)]
        + ["<span>Zůstatek: NUM[value=1234.5,profile=decimal]</span>" for _ in range(20)]
    )

    class LocalizedBenchmark(Component):
        citry = app
        name = "phase0-localized-benchmark"
        template = localized_template

        def template_data(self, _kwargs: Any, _slots: Any) -> dict[str, Any]:
            return {"amount": Decimal("1234.5"), "name": "Ada"}

    class LiteralBenchmark(Component):
        citry = app
        name = "phase0-literal-benchmark"
        template = literal_template

    unconfigured_app = Citry(autodiscover=False)

    class UnconfiguredBenchmark(Component):
        citry = unconfigured_app
        name = "phase0-unconfigured-benchmark"
        template = literal_template

    def visible_benchmark_html(value: str) -> str:
        return re.sub(r' data-cid-[^=]+=""', "", strip_controls(value))

    localized_sample = visible_benchmark_html(LocalizedBenchmark().render().serialize())
    literal_sample = visible_benchmark_html(LiteralBenchmark().render().serialize())
    unconfigured_sample = visible_benchmark_html(UnconfiguredBenchmark().render().serialize())
    require(localized_sample == literal_sample, "the localized benchmark tree is not equivalent to the literal tree")
    require(unconfigured_sample == literal_sample, "the unconfigured benchmark tree differs from the literal tree")

    def render_sample(component: type[Component], iterations: int = 10) -> float:
        started = time.perf_counter_ns()
        for _ in range(iterations):
            component().render().serialize()
        return (time.perf_counter_ns() - started) / 1_000_000 / iterations

    for _ in range(5):
        render_sample(LiteralBenchmark, 2)
        render_sample(LocalizedBenchmark, 2)
        render_sample(UnconfiguredBenchmark, 2)

    samples = {"literal": [], "localized": [], "unconfigured": []}
    rss_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    orders = (
        (LiteralBenchmark, LocalizedBenchmark, UnconfiguredBenchmark),
        (LocalizedBenchmark, UnconfiguredBenchmark, LiteralBenchmark),
        (UnconfiguredBenchmark, LiteralBenchmark, LocalizedBenchmark),
    )
    names = {
        LiteralBenchmark: "literal",
        LocalizedBenchmark: "localized",
        UnconfiguredBenchmark: "unconfigured",
    }
    for sample_index in range(30):
        for component in orders[sample_index % len(orders)]:
            samples[names[component]].append(render_sample(component))
    rss_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    def summarize(values: list[float]) -> dict[str, float]:
        ordered = sorted(values)
        p95 = ordered[math.ceil(0.95 * len(ordered)) - 1]
        return {
            "max_ms": round(max(values), 4),
            "median_ms": round(statistics.median(values), 4),
            "min_ms": round(min(values), 4),
            "p95_ms": round(p95, 4),
            "stdev_ms": round(statistics.stdev(values), 4),
        }

    summaries = {name: summarize(values) for name, values in samples.items()}
    literal_summary = summaries["literal"]
    localized_summary = summaries["localized"]
    median_budget = max(literal_summary["median_ms"] * 0.15, 2.0)
    p95_budget = max(literal_summary["p95_ms"] * 0.20, 3.0)
    added_median = localized_summary["median_ms"] - literal_summary["median_ms"]
    added_p95 = localized_summary["p95_ms"] - literal_summary["p95_ms"]
    literal_mean = statistics.mean(samples["literal"])
    literal_margin = 1.96 * statistics.stdev(samples["literal"]) / math.sqrt(len(samples["literal"]))
    unconfigured_mean = statistics.mean(samples["unconfigured"])
    render_benchmark = {
        "added_median_ms": round(added_median, 4),
        "added_p95_ms": round(added_p95, 4),
        "gates": {
            "localized_added_median_within_budget": added_median <= median_budget,
            "localized_added_p95_within_budget": added_p95 <= p95_budget,
            "unconfigured_mean_within_literal_95pct_ci": (
                literal_mean - literal_margin <= unconfigured_mean <= literal_mean + literal_margin
            ),
        },
        "host_specific": True,
        "literal_95pct_mean_ci_ms": [
            round(literal_mean - literal_margin, 4),
            round(literal_mean + literal_margin, 4),
        ],
        "memory": {
            "peak_rss_after": rss_after,
            "peak_rss_before": rss_before,
            "peak_rss_delta": max(0, rss_after - rss_before),
            "platform_units": "bytes on macOS; KiB on Linux",
        },
        "operations": {"message_resolutions": 100, "named_format_calls": 20},
        "samples_per_tree": 30,
        "summaries": summaries,
        "thresholds_ms": {
            "added_median": round(median_budget, 4),
            "added_p95": round(p95_budget, 4),
        },
        "warmups_per_tree": 5,
    }
    require(
        render_benchmark["gates"]["localized_added_median_within_budget"],
        f"localized median render budget failed: {render_benchmark!r}",
    )
    require(
        render_benchmark["gates"]["localized_added_p95_within_budget"],
        f"localized p95 render budget failed: {render_benchmark!r}",
    )
    return (
        {"assets": asset_proof, "render": integration, "samples": {"card": visible_card, "rich": visible_page}},
        render_benchmark,
    )


def benchmark_compile(module: Any, request: dict[str, Any], iterations: int) -> dict[str, Any]:
    compiler = module.CatalogCompiler()
    cold_start = time.perf_counter()
    compile_json(compiler, request)
    cold_ms = (time.perf_counter() - cold_start) * 1000
    warm_start = time.perf_counter()
    for _ in range(iterations):
        compile_json(compiler, request)
    warm_ms = (time.perf_counter() - warm_start) * 1000 / iterations
    changed = copy_json(request)
    changed["catalogs"][1]["source"] += "\n# selective invalidation benchmark\n"
    changed_start = time.perf_counter()
    changed_result = compile_json(compiler, changed)
    changed_ms = (time.perf_counter() - changed_start) * 1000
    require(changed_result["stats"]["parsed_catalogs"] == 1, "selective benchmark reparsed more than one catalog")
    return {
        "iterations": iterations,
        "cold_ms": round(cold_ms, 3),
        "warm_mean_ms": round(warm_ms, 3),
        "one_catalog_change_ms": round(changed_ms, 3),
        "host_specific": True,
    }


def input_identity() -> dict[str, Any]:
    fixture_hashes = {
        str(path.relative_to(HERE)): sha256(path) for path in sorted(FIXTURES.rglob("*")) if path.is_file()
    }
    production_paths = [
        REPO / "packages/py/citry/citry/assets.py",
        REPO / "packages/py/citry/citry/component.py",
        REPO / "packages/py/citry/citry/component_render.py",
        REPO / "packages/py/citry/citry/constness.py",
        REPO / "packages/py/citry/citry/extension.py",
        REPO / "packages/py/citry/citry/slots.py",
        REPO / "packages/py/citry_core/citry_core/template_parser/__init__.py",
        REPO / "packages/py/citry_core/citry_core/template_parser/parse.py",
        REPO / "uv.lock",
    ]
    production_hashes = {str(path.relative_to(REPO)): sha256(path) for path in production_paths}
    core_module = importlib.import_module("citry_core._rust")
    production_hashes["loaded:citry_core._rust"] = sha256(Path(core_module.__file__))
    return {
        "fixtures": fixture_hashes,
        "harness_sha256": sha256(Path(__file__)),
        "production_inputs": production_hashes,
    }


def run(*, benchmark_iterations: int) -> tuple[dict[str, Any], dict[str, Any]]:
    module, build = build_extension()
    compiler = module.CatalogCompiler()
    request = base_request()
    payload = json.dumps(request, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    first_json = compiler.compile(payload)
    first = json.loads(first_json)
    warm = compile_json(compiler, request)
    reversed_request = copy_json(request)
    reversed_request["catalogs"].reverse()
    reversed_result = compile_json(module.CatalogCompiler(), reversed_request)
    changed_request = copy_json(request)
    changed_request["catalogs"][1]["source"] += "\n# changed catalog only\n"
    changed = compile_json(compiler, changed_request)

    require(first["stats"]["parsed_catalogs"] == 4, f"cold parse stats wrong: {first['stats']!r}")
    require(warm["stats"]["reused_catalogs"] == 4, f"warm parse stats wrong: {warm['stats']!r}")
    require(
        changed["stats"]["parsed_catalogs"] == 1
        and changed["stats"]["invalidated_catalogs"] == 1
        and changed["stats"]["reused_catalogs"] == 3,
        f"selective invalidation stats wrong: {changed['stats']!r}",
    )
    require(first["revision"] == reversed_result["revision"], "catalog discovery order changed the artifact")
    require(first["manifest"] == reversed_result["manifest"], "catalog discovery order changed the manifest")

    manifest = first["manifest"]
    source_maps = source_map_proof(first, request)
    architectural = {
        "application_override_selected": manifest["cs-CZ"]["citry-ui-account"]["selected_layer"] == "application",
        "owner_preserved": manifest["cs-CZ"]["citry-ui-account"]["owner"] == "citry_ui",
        "attribute_resolved_independently": (
            manifest["cs-CZ"]["citry-ui-account.aria-label"]["selected_layer"] == "citry_ui"
        ),
        "owner_source_graph_fallback": (
            manifest["cs-CZ"]["citry-ui-ref-wrapper"]["bundle_locale"] == "en-US"
            and manifest["cs-CZ"]["citry-ui-ref-wrapper"]["selected_path"] == "fixtures/citry_ui/en-US.ftl"
        ),
        "application_source_fallback": manifest["en-US"]["my-app-wrapper"]["bundle_locale"] == "cs-CZ",
        "transitive_contract": manifest["cs-CZ"]["my-app-wrapper"]["contract"]
        == {"name": "str", "terms_link": "Slot"},
        "operation_source_maps": all(source_maps.values()),
        "selectors_generated": "CITRY_PLURAL(" in first["artifacts"]["en-US"]
        and "CITRY_PLURAL(" in first["artifacts"]["cs-CZ"],
        "formatter_calls_generated": all(
            operation in "\n".join(first["artifacts"].values()) for operation in ("NUMBER(", "DATETIME(")
        ),
        "slot_is_internal_only": all(
            "SLOT(" not in item["source"] and "CITRY_" not in item["source"] for item in request["catalogs"]
        )
        and "SLOT(" in "\n".join(first["artifacts"].values()),
        "deterministic_discovery": first["revision"] == reversed_result["revision"],
        "cold_cache": first["stats"]["parsed_catalogs"] == 4,
        "warm_cache": warm["stats"]["reused_catalogs"] == 4,
        "selective_invalidation": changed["stats"]["parsed_catalogs"] == 1,
    }
    require(all(architectural.values()), f"architectural gates failed: {architectural!r}")

    negatives = negative_requests(module)
    expected_codes = {
        "malformed_fluent": "I18N_FTL_SYNTAX",
        "translation_added_variable": "I18N_TRANSLATION_VARIABLE_ADDED",
        "translation_missing_slot": "I18N_REQUIRED_SLOT_MISSING",
        "translation_branch_missing_slot": "I18N_REQUIRED_SLOT_MISSING",
        "transitive_type_conflict": "I18N_TRANSITIVE_TYPE_CONFLICT",
        "invalid_selector_type": "I18N_SELECTOR_TYPE",
        "missing_format_profile": "I18N_FORMAT_PROFILE",
        "literal_bidi_control": "I18N_BIDI_CONTROL_CATALOG",
        "escaped_u4_bidi_control": "I18N_BIDI_CONTROL_CATALOG",
        "escaped_u6_bidi_control": "I18N_BIDI_CONTROL_CATALOG",
        "stale_schema": "I18N_SCHEMA_VERSION",
        "authored_slot_function": "I18N_SLOT_FUNCTION",
        "strict_unknown_field": "I18N_REQUEST_JSON",
    }
    require(
        {name: item["code"] for name, item in negatives.items()} == expected_codes,
        f"negative diagnostics drifted: {negatives!r}",
    )
    require(
        negatives["malformed_fluent"]["line"] is not None
        and negatives["translation_added_variable"]["message_id"] == "my-app-target",
        f"structured diagnostic positions missing: {negatives!r}",
    )

    template = parser_metadata()
    runtime = runtime_proof(module, first_json, first)
    integration, render_benchmark = integration_proof(module, first_json, first)
    benchmark = benchmark_compile(module, request, benchmark_iterations)
    benchmark["render"] = render_benchmark
    benchmark_gates = {
        "cold_under_100_ms": benchmark["cold_ms"] < 100,
        "localized_added_median_within_budget": render_benchmark["gates"]["localized_added_median_within_budget"],
        "localized_added_p95_within_budget": render_benchmark["gates"]["localized_added_p95_within_budget"],
        "warm_mean_under_100_ms": benchmark["warm_mean_ms"] < 100,
        "one_catalog_change_under_100_ms": benchmark["one_catalog_change_ms"] < 100,
    }
    require(all(benchmark_gates.values()), f"bounded benchmark gate failed: {benchmark!r}")

    result = {
        "schema_version": 2,
        "result": "PASS_BOUNDED",
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "python_optimize": sys.flags.optimize,
            "rustc": run_command(["rustc", "--version"]),
            "cargo": run_command(["cargo", "--version"]),
            "maturin": run_command(["uv", "run", "--frozen", "maturin", "--version"]),
        },
        "build": build,
        "inputs": input_identity(),
        "architectural_gates": architectural,
        "cache_stats": {"cold": first["stats"], "warm": warm["stats"], "changed": changed["stats"]},
        "diagnostics": negatives,
        "source_maps": source_maps,
        "runtime": runtime,
        "template_metadata": template,
        "citry_integration": integration,
        "artifact": {
            "revision": first["revision"],
            "artifact_sha256": hashlib.sha256(
                json.dumps(first["artifacts"], sort_keys=True).encode("utf-8")
            ).hexdigest(),
            "manifest_sha256": hashlib.sha256(
                json.dumps(first["manifest"], sort_keys=True).encode("utf-8")
            ).hexdigest(),
            "source_map_count": len(first["source_maps"]),
        },
        "benchmark_gates": benchmark_gates,
        "bounded_limits": [
            "plural rules and formatter text are deterministic Phase 0 stand-ins, not the final CLDR backend",
            "the tagged wire covers str, int, Decimal, datetime, and Slot, not the complete planned value set",
            "browser switching and Slot DOM ownership are not exercised",
            "fresh concurrent Slot marker generation is not exercised",
            "fallback-language metadata and whole-message direction are not exercised",
            "messages/messages_file reuse private core helpers and are not yet a core asset pair",
        ],
    }
    return result, benchmark


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-iterations", type=int, default=25)
    parser.add_argument("--benchmark-output", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result, benchmark = run(benchmark_iterations=args.benchmark_iterations)
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        sys.stdout.write(rendered)
    else:
        args.output.write_text(rendered, encoding="utf-8")
    if args.benchmark_output is not None:
        args.benchmark_output.write_text(
            json.dumps(benchmark, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
