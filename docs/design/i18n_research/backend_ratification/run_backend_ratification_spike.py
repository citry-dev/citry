from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

import tomllib

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RUST = HERE / "rust"
MANIFEST = RUST / "Cargo.toml"
LOCK = RUST / "Cargo.lock"
RUST_SOURCE = RUST / "src/main.rs"
BASELINE_SOURCE = RUST / "src/bin/baseline.rs"
BROWSER_SOURCE = HERE / "browser/runner.mjs"
FORMATTER_EVIDENCE = REPO / "docs/design/i18n_research/formatter_backend/evidence.json"
RUNTIME_EVIDENCE = REPO / "docs/design/i18n_research/runtime_backend/evidence.json"
PRODUCTION_EVIDENCE = REPO / "docs/design/i18n_research/production_slice/evidence.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str]) -> str:
    result = subprocess.run(
        command,
        cwd=REPO,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result.stdout


def ensure_always_on_checks() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    require(
        not [node for node in ast.walk(tree) if isinstance(node, ast.Assert)],
        "the evidence harness must not use optimization-sensitive assert statements",
    )


def cargo_versions() -> dict[str, str]:
    lock = tomllib.loads(LOCK.read_text(encoding="utf-8"))
    wanted = {
        "fixed_decimal",
        "icu",
        "icu_calendar",
        "icu_datetime",
        "icu_decimal",
        "icu_experimental",
        "icu_list",
        "icu_locale",
        "icu_plurals",
        "icu_provider",
        "icu_time",
    }
    return {package["name"]: package["version"] for package in lock["package"] if package["name"] in wanted}


def build_evidence() -> dict[str, Any]:
    ensure_always_on_checks()
    run(
        [
            "cargo",
            "fmt",
            "--manifest-path",
            str(MANIFEST),
            "--",
            "--check",
        ]
    )
    run(
        [
            "cargo",
            "clippy",
            "--release",
            "--locked",
            "--manifest-path",
            str(MANIFEST),
            "--all-targets",
            "--",
            "-D",
            "warnings",
        ]
    )
    run(
        [
            "cargo",
            "build",
            "--release",
            "--locked",
            "--manifest-path",
            str(MANIFEST),
            "--bins",
        ]
    )
    candidate_path = RUST / "target/release/citry-i18n-backend-ratification"
    baseline_path = RUST / "target/release/baseline"
    candidate = json.loads(run([str(candidate_path)]))
    browser = json.loads(run(["node", str(BROWSER_SOURCE)]))

    require(all(candidate["capabilities"].values()), "an ICU4X capability check failed")
    require(all(candidate["known_gaps"].values()), "an expected ICU4X gap changed")
    require(
        candidate["first_constructor_ns"] < 5_000_000,
        "the first decimal formatter construction exceeded 5 ms",
    )
    require(
        candidate["repeated_format_ns_per_operation"] < 10_000,
        "repeated decimal formatting exceeded 10 microseconds per operation",
    )

    rust_outputs = candidate["outputs"]
    browser_outputs = browser["outputs"]
    exact_matches = {
        key: rust_outputs[key] == browser_outputs[key]
        for key in (
            "arabic_currency",
            "arabic_exact_decimal",
            "buddhist_date",
            "czech_relative_day",
            "devanagari_exact_decimal",
            "spanish_list",
        )
    }
    require(all(exact_matches.values()), f"an exact comparison changed: {exact_matches!r}")
    require(
        rust_outputs["czech_fraction_plural"].lower() == browser_outputs["czech_fraction_plural"],
        "Czech fractional plural category diverged",
    )
    require(
        rust_outputs["arabic_unit"] != browser_outputs["arabic_unit"],
        "the expected Arabic unit grammar difference disappeared",
    )
    require(
        rust_outputs["arabic_percent"] != browser_outputs["arabic_percent_fraction"],
        "the expected Arabic percent difference disappeared",
    )

    candidate_bytes = candidate_path.read_bytes()
    baseline_bytes = baseline_path.read_bytes()
    return {
        "artifacts": {
            "baseline_source": sha256(BASELINE_SOURCE),
            "browser_source": sha256(BROWSER_SOURCE),
            "cargo_lock": sha256(LOCK),
            "cargo_manifest": sha256(MANIFEST),
            "formatter_evidence": sha256(FORMATTER_EVIDENCE),
            "harness": sha256(Path(__file__)),
            "production_slice_evidence": sha256(PRODUCTION_EVIDENCE),
            "runtime_evidence": sha256(RUNTIME_EVIDENCE),
            "rust_source": sha256(RUST_SOURCE),
        },
        "candidate": {
            "capabilities": candidate["capabilities"],
            "concurrency_enabled": candidate["capabilities"]["concurrent_formatting"],
            "first_constructor_under_5ms": True,
            "known_direct_api_gaps": {
                **candidate["known_gaps"],
                "arabic_unit_grammar_differs_from_intl": True,
            },
            "repeated_decimal_format_under_10us": True,
            "strict_decimal_parser_uses_resolved_icu4x_symbols": True,
        },
        "comparison": {
            "exact_output_matches": exact_matches,
            "fractional_plural_matches": True,
            "node_icu": browser["icu"],
        },
        "decision": {
            "cldr_service": "ICU4X is the selected Rust foundation, not a ratified full formatter adapter",
            "full_formatter_ready": False,
            "message_runtime": "fluent-bundle 0.16.0 through the existing Rust/PyO3 boundary",
            "pyicu_role": "comparison oracle only; PyPI 2.16.2 has no binary wheels",
        },
        "environment": {
            "cargo": run(["cargo", "--version"]).strip(),
            "machine": platform.machine(),
            "node": browser["node"],
            "platform": platform.platform(),
            "python": platform.python_version(),
            "rust_packages": cargo_versions(),
            "rustc": run(["rustc", "--version"]).strip(),
        },
        "research_binary": {
            "baseline_bytes": len(baseline_bytes),
            "candidate_bytes": len(candidate_bytes),
            "candidate_gzip_bytes": len(gzip.compress(candidate_bytes, mtime=0)),
            "incremental_bytes": len(candidate_bytes) - len(baseline_bytes),
        },
        "result": "PASS_BOUNDED_WITH_UNRATIFIED_FULL_FORMATTER",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "evidence.json")
    arguments = parser.parse_args()
    evidence = build_evidence()
    arguments.output.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    sys.stdout.write(f"{evidence['result']}\nevidence={arguments.output}\n")


if __name__ == "__main__":
    main()
