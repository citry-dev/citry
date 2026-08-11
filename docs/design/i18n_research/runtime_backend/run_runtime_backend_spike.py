"""Compare frozen Fluent runtimes against one bounded Citry message contract."""

# The probe is an executable assertion harness, not production code.
# ruff: noqa: ANN001, ANN201, S607, T201

from __future__ import annotations

import ast
import gzip
import hashlib
import importlib.metadata
import json
import platform
import secrets
import subprocess
import sys
import tempfile
from pathlib import Path

from fluent.syntax import FluentParser
from fluent.syntax import ast as fluent_ast

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[3]
FIXTURES = ROOT / "fixtures"
BROWSER = ROOT / "browser"
RUST_MANIFEST = ROOT / "rust" / "Cargo.toml"
PYTHON_REQUIREMENTS = ROOT / "python-requirements.txt"
FSI = "\u2068"
LRI = "\u2066"
PDI = "\u2069"
HOSTILE_NAME = "אבג <Ada&Co>"
PYTHON_PACKAGES = {
    "attrs": "26.1.0",
    "Babel": "2.18.0",
    "fluent.runtime": "0.4.0",
    "fluent.syntax": "0.19.0",
    "pytz": "2026.3.post1",
    "typing-extensions": "4.15.0",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command_output(command, *, cwd=REPO_ROOT):
    return subprocess.check_output(command, cwd=cwd, text=True).strip()


def json_command(command, *, cwd=REPO_ROOT):
    return json.loads(command_output(command, cwd=cwd).splitlines()[-1])


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def browser_payload():
    messages = "\n".join(f"payload-message-{index} = Message {index}" for index in range(100))
    entry = (
        'import { FluentBundle, FluentResource } from "@fluent/bundle";\n'
        f"const source = {json.dumps(messages)};\n"
        "export const resource = new FluentResource(source);\n"
        'export const bundle = new FluentBundle("en-US");\n'
        "bundle.addResource(resource);\n"
    )
    with tempfile.TemporaryDirectory(prefix=".citry-i18n-runtime-", dir=BROWSER) as temp_name:
        temp = Path(temp_name)
        entry_path = temp / "entry.mjs"
        output_path = temp / "bundle.min.mjs"
        metafile_path = temp / "metafile.json"
        entry_path.write_text(entry)
        subprocess.run(
            [
                "pnpm",
                "exec",
                "esbuild",
                str(entry_path),
                "--bundle",
                "--minify",
                "--format=esm",
                "--platform=browser",
                "--target=es2020",
                f"--outfile={output_path}",
                f"--metafile={metafile_path}",
            ],
            cwd=BROWSER,
            check=True,
            capture_output=True,
            text=True,
        )
        output = output_path.read_bytes()
        inputs = sorted(
            "<generated-entry>" if path.endswith("/entry.mjs") else path
            for path in json.loads(metafile_path.read_text())["inputs"]
        )
    source_bytes = messages.encode()
    return {
        "message_count": 100,
        "minified_bytes": len(output),
        "gzip_bytes": len(gzip.compress(output, mtime=0)),
        "source_bytes": len(source_bytes),
        "source_gzip_bytes": len(gzip.compress(source_bytes, mtime=0)),
        "catalog_parser_included": any(path.endswith("/resource.js") for path in inputs),
        "metafile_inputs": inputs,
    }


def variable_term_argument_evidence():
    source = (FIXTURES / "unsupported-variable-term-argument.ftl").read_text()
    resource = FluentParser(with_spans=True).parse(source)
    junk = [entry for entry in resource.body if isinstance(entry, fluent_ast.Junk)]
    annotations = [annotation.message for entry in junk for annotation in entry.annotations]
    require(len(junk) == 1, f"expected one Junk entry, received {len(junk)}")
    require(
        any("Expected literal" in message for message in annotations),
        f"expected literal-argument rejection, received {annotations}",
    )
    return {
        "junk_entries": len(junk),
        "annotations": annotations,
        "conclusion": "current Fluent named term arguments accept literals, not variables",
    }


def python_assertion_evidence():
    sources = (ROOT / "run_runtime_backend_spike.py", ROOT / "python_candidate.py")
    assertion_count = sum(
        isinstance(node, ast.Assert)
        for path in sources
        for node in ast.walk(ast.parse(path.read_text(), filename=str(path)))
    )
    require(assertion_count == 0, f"Python spike sources contain {assertion_count} assert statements")
    return {"source_files_checked": len(sources), "assert_statements": assertion_count}


def main():
    for package, version in PYTHON_PACKAGES.items():
        installed = importlib.metadata.version(package)
        require(installed == version, f"{package} resolved to {installed}, expected {version}")
    browser_packages = json.loads((BROWSER / "package.json").read_text())
    require(
        browser_packages["dependencies"]["@fluent/bundle"] == "0.19.1",
        "browser package.json must pin @fluent/bundle 0.19.1",
    )
    require(
        browser_packages["devDependencies"]["esbuild"] == "0.28.1",
        "browser package.json must pin esbuild 0.28.1",
    )
    esbuild_version = command_output(["pnpm", "exec", "esbuild", "--version"], cwd=BROWSER)
    require(esbuild_version == "0.28.1", f"resolved esbuild is {esbuild_version}, expected 0.28.1")
    required = [
        BROWSER / "pnpm-lock.yaml",
        PYTHON_REQUIREMENTS,
        ROOT / "rust" / "Cargo.lock",
        *(path for path in FIXTURES.iterdir() if path.is_file()),
    ]
    for path in required:
        require(path.exists(), f"missing exact spike input: {path}")
    hostile_config = json.loads((FIXTURES / "hostile-bidi-control.json").read_text())

    marker_seed = secrets.token_hex(32)
    python = json_command([sys.executable, str(ROOT / "python_candidate.py"), str(FIXTURES), marker_seed])
    browser = json_command(["node", str(BROWSER / "runner.mjs"), str(FIXTURES), marker_seed])
    rust = json_command(
        [
            "cargo",
            "run",
            "--quiet",
            "--manifest-path",
            str(RUST_MANIFEST),
            "--locked",
            "--",
            str(FIXTURES),
            marker_seed,
        ]
    )
    candidates = {item["candidate"]: item for item in (python, browser, rust)}
    require(
        len(candidates) == 3 and set(candidates) == {"python", "browser", "rust"},
        f"unexpected candidate identities: {sorted(candidates)}",
    )
    require(
        browser.get("runtime_versions") == {"@fluent/bundle": "0.19.1"},
        f"browser used unexpected runtime versions: {browser.get('runtime_versions')}",
    )

    cases_equal = python["cases"] == browser["cases"] == rust["cases"]
    require(cases_equal, "Python, browser, and Rust normalized cases differ")
    repeated_slots_rehydrated = all(
        sum(segment["kind"] == "slot" for segment in candidate["cases"][locale]["rich"]) == 2
        for candidate in candidates.values()
        for locale in ("en-US", "cs-CZ")
    )
    require(repeated_slots_rehydrated, "repeated rich Slot markers were not all rehydrated")
    expected_rejections = {
        "bidi-control-catalog",
        "bidi-control-plain",
        "bidi-control-rich",
        "invalid-plural-infinity",
        "invalid-plural-input",
        "invalid-plural-nan",
        "paragraph-boundary-plain",
        "paragraph-boundary-rich",
        "slot-function-scalar",
        "slot_catalog_collision",
        "slot_marker_omitted",
        "slot_marker_wrapped",
        "slot_scalar_collision",
        "unknown-function",
        "unknown-variable",
    }
    for candidate in candidates.values():
        name = candidate["candidate"]
        require(
            set(candidate["rejections"]) == expected_rejections,
            f"{name} rejection mismatch: {sorted(candidate['rejections'])}",
        )
        require(
            candidate["unsafe_runtime_behaviors"] == {"slot_as_selector": "Also invalid"},
            f"{name} unsafe-runtime behavior changed",
        )
        require(
            candidate["marker_properties"] == {"distinct_per_locale": True, "distinct_per_resolution": True},
            f"{name} did not use distinct locale/resolution markers",
        )
        expected_bidi_properties = {
            "catalog_cases_rejected": len(hostile_config["bidi_control_hex"])
            * len(hostile_config["fluent_escape_forms"]),
            "catalog_escape_forms": hostile_config["fluent_escape_forms"],
            "paragraph_boundaries_rejected_per_scalar_sink": len(hostile_config["paragraph_boundary_hex"]),
            "whole_message_paragraph_cases_isolated": len(hostile_config["paragraph_boundary_hex"]) + 1,
        }
        require(
            candidate["bidi_properties"] == expected_bidi_properties,
            f"{name} bidi property mismatch: {candidate['bidi_properties']}",
        )

    cases = python["cases"]
    for locale in ("en-US", "cs-CZ"):
        require("NUM[" in cases[locale]["balance"], f"{locale} did not call NUMBER")
        require("DATE[" in cases[locale]["due_date"], f"{locale} did not call DATETIME")
        require(
            [segment["kind"] for segment in cases[locale]["rich"]] == ["text", "slot", "text", "slot", "text"],
            f"{locale} rich segment shape changed",
        )
        require(
            [segment["occurrence"] for segment in cases[locale]["rich"] if segment["kind"] == "slot"] == [0, 1],
            f"{locale} rich Slot occurrence identities changed",
        )
        rich_text = "".join(segment.get("value", "") for segment in cases[locale]["rich"])
        require(
            f"{FSI}{HOSTILE_NAME}{PDI}" in rich_text,
            f"{locale} rich scalar lost its Citry-owned bidi isolation",
        )
        require(marker_seed not in json.dumps(cases[locale]), f"{locale} leaked a slot marker")
        require(
            cases[locale]["layered_reference"]
            == "Library wrapper: application override via application private term / library private term",
            f"{locale} cross-layer generated result changed",
        )
        multiline = cases[locale]["multiline_fallback_isolated"]
        require(
            "\n" in multiline and multiline.count(LRI) == 2 and multiline.count(PDI) == 2,
            f"{locale} fallback message was not isolated per bidi paragraph",
        )
    require(cases["cs-CZ"]["plural_1"].endswith("položka"), "Czech one failed")
    require(
        cases["en-US"]["plural_negative_zero"] == "No items"
        and cases["cs-CZ"]["plural_negative_zero"] == "Žádné položky",
        "signed negative zero did not match compiler-owned exact zero",
    )
    require(cases["cs-CZ"]["plural_2"].endswith("položky"), "Czech few failed")
    require(cases["cs-CZ"]["plural_5"].endswith("položek"), "Czech other failed")
    require(
        cases["cs-CZ"]["plural_1_5"].endswith("desetinné položky")
        and cases["cs-CZ"]["plural_2_5"].endswith("desetinné položky"),
        "Czech many/fractional selection failed",
    )
    require(cases["en-US"]["ordinal_1"].endswith("st"), "English ordinal one failed")
    require(cases["en-US"]["ordinal_2"].endswith("nd"), "English ordinal two failed")
    require(cases["en-US"]["ordinal_3"].endswith("rd"), "English ordinal few failed")
    require(
        cases["en-US"]["ordinal_4"].endswith("th")
        and cases["en-US"]["ordinal_11"].endswith("th")
        and cases["en-US"]["ordinal_21"].endswith("st"),
        "English ordinal other/teen/cycle selection failed",
    )

    fixture_digests = {path.name: sha256(path) for path in sorted(FIXTURES.iterdir()) if path.is_file()}
    harness_digests = {
        path.relative_to(ROOT).as_posix(): sha256(path)
        for path in (
            ROOT / "python_candidate.py",
            PYTHON_REQUIREMENTS,
            ROOT / "run_runtime_backend_spike.py",
            BROWSER / "package.json",
            BROWSER / "runner.mjs",
            ROOT / "rust" / "Cargo.toml",
            ROOT / "rust" / "src" / "main.rs",
        )
    }
    evidence = {
        "result": "PASS_BOUNDED",
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "node": command_output(["node", "--version"]),
            "pnpm": command_output(["pnpm", "--version"]),
            "uv": command_output(["uv", "--version"]),
            "rustc": command_output(["rustc", "--version"]),
            "cargo": command_output(["cargo", "--version"]),
            "packages": {
                **PYTHON_PACKAGES,
                "@fluent/bundle": browser["runtime_versions"]["@fluent/bundle"],
                "esbuild": esbuild_version,
                "fluent-bundle": "0.16.0",
            },
            "locks": {
                "browser_pnpm_sha256": sha256(BROWSER / "pnpm-lock.yaml"),
                "python_exact_pins_sha256": sha256(PYTHON_REQUIREMENTS),
                "rust_cargo_sha256": sha256(ROOT / "rust" / "Cargo.lock"),
            },
        },
        "fixtures": fixture_digests,
        "harness": harness_digests,
        "semantic_parity": {
            "candidate_count": 3,
            "cases_equal": cases_equal,
            "cases": cases,
        },
        "formatter_delegation": {
            "number_called": True,
            "datetime_called": True,
            "plural_called": True,
            "ordinal_called": True,
            "exact_selector_called": True,
            "exact_and_plural_selection_delegated": True,
        },
        "unproved_design_contract": {
            "source_checker_proved": False,
            "authored_to_lowered_transform_proved": False,
            "intended_rules": [
                "implicit typed number/date display is rejected",
                "ordinary numeric selectors compile to CITRY_PLURAL",
                "ordinary displayed scalars compile to CITRY_TEXT",
            ],
        },
        "rich_placeholder_adapter": {
            "opaque_marker_rehydrated": True,
            "markers_random_per_run": True,
            "markers_distinct_per_locale": True,
            "markers_distinct_per_resolution": True,
            "slot_object_entered_runtime": False,
            "runtime_result_was_flat_string": True,
            "required_slot_omission_rejected": True,
            "repeated_slot_occurrences_rehydrated": repeated_slots_rehydrated,
            "catalog_and_scalar_collision_rejected": True,
            "citry_owned_scalar_isolation_exercised": True,
            "embedded_bidi_controls_rejected": True,
            "escaped_catalog_bidi_controls_rejected": True,
            "scalar_paragraph_boundaries_rejected": True,
            "whole_message_paragraph_isolation_exercised": True,
            "fluent_owned_isolation_disabled": True,
            "slot_marker_remained_unisolated": True,
            "source_to_lowered_transform_proved": False,
            "static_slot_usage_contract_required": True,
            "unsafe_selector_behavior": "all runtimes accepted a Slot marker as an ordinary selector string",
        },
        "strict_resolution": {candidate: value["rejections"] for candidate, value in candidates.items()},
        "bidi_validation": {candidate: value["bidi_properties"] for candidate, value in candidates.items()},
        "python_optimization_safety": python_assertion_evidence(),
        "rust_function_error_strategy": {
            "final_text_sentinel_used": False,
            "pre_resolution_value_contract_exercised": True,
            "source_function_option_validation_required": True,
            "production_infallible_callback_binding_proved": False,
        },
        "cross_layer_lowering": {
            "illustrative_lowered_artifact_public_reference_rendered": True,
            "distinct_internal_private_term_ids_rendered": True,
            "actual_layer_precedence_exercised": False,
            "source_to_lowered_transform_proved": False,
        },
        "term_variable_argument": variable_term_argument_evidence(),
        "browser_payload": {
            **browser_payload(),
            "upstream_runtime_only": True,
            "includes_citry_adapter": False,
            "full_budget_gate_passed": False,
        },
        "bounded_claims": {
            "rust_bundle_send_sync_compile_assertion": True,
            "production_backend_ratified": False,
            "formatting_backend_ratified": False,
            "rich_message_api_ratified": False,
            "production_pyo3_binding_proved": False,
            "browser_compiled_catalog_proved": False,
        },
    }
    print(json.dumps(evidence, indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
