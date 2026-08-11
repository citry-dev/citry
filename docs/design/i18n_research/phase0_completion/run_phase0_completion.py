from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import importlib.metadata
import importlib.util
import json
import platform
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
BROWSER = HERE / "browser"
COMPLETE_PAYLOAD = BROWSER / "complete_payload.mjs"
SWITCH_BENCHMARK = BROWSER / "switch_benchmark.js"
RUNTIME_BROWSER = REPO / "docs/design/i18n_research/runtime_backend/browser"
PROVIDER = REPO / "docs/design/i18n_research/provider_runtime"
PROVIDER_CANDIDATE = PROVIDER / "browser/candidate.js"
PROVIDER_RUNNER = PROVIDER / "run_provider_runtime_spike.py"
PROVIDER_EVIDENCE = PROVIDER / "evidence.json"
RICH_CANDIDATE = REPO / "docs/design/i18n_research/rich_client_relocation/browser/candidate.js"
PRODUCTION_EVIDENCE = REPO / "docs/design/i18n_research/production_slice/evidence.json"
BROWSER_NAMES = ("chromium", "firefox", "webkit")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(command: list[str], *, cwd: Path = REPO) -> str:
    result = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result.stdout.strip()


def ensure_always_on_checks() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    require(
        not [node for node in ast.walk(tree) if isinstance(node, ast.Assert)],
        "the evidence harness must not use optimization-sensitive assert statements",
    )
    for script in (COMPLETE_PAYLOAD, SWITCH_BENCHMARK):
        require("console.assert" not in script.read_text(encoding="utf-8"), f"{script.name} uses console.assert")


def simple_messages(locale: str) -> tuple[list[str], str]:
    ids = [f"payload-message-{index}" for index in range(100)]
    source = "\n".join(f"{message_id} = {locale} message {index}" for index, message_id in enumerate(ids))
    return ids, source


def build_browser_payload() -> dict[str, Any]:
    public_ids, source = simple_messages("en-US")
    additional_ids, additional_source = simple_messages("cs-CZ")
    require(public_ids == additional_ids, "locale partitions expose different public IDs")
    entry = f"""
import {{
  createMessageRuntime,
  decodeWire,
  providerFormat,
  richRelocationFormat,
}} from {json.dumps(str(COMPLETE_PAYLOAD))};
const artifact = Object.freeze({{
  locale: "en-US",
  messages: {json.dumps(source)},
  publicIds: {json.dumps(public_ids)},
  revision: "{"8" * 64}",
}});
const runtime = createMessageRuntime(artifact);
export const payloadCanary = Object.freeze({{
  exactInteger: decodeWire({{ type: "int", value: "9007199254740993" }}).value,
  message: runtime.format("payload-message-99"),
  negativeZero: Object.is(decodeWire({{ type: "f64", bits: "8000000000000000" }}), -0),
  providerFormat,
  richRelocationFormat,
}});
"""
    additional_entry = f"export const locale = 'cs-CZ';\nexport const messages = {json.dumps(additional_source)};\n"
    with tempfile.TemporaryDirectory(prefix="citry-i18n-phase0-payload-") as temp_name:
        temp = Path(temp_name)
        entry_path = temp / "entry.mjs"
        output_path = temp / "bundle.min.mjs"
        metafile_path = temp / "metafile.json"
        additional_path = temp / "additional.mjs"
        additional_output = temp / "additional.min.mjs"
        entry_path.write_text(entry, encoding="utf-8")
        additional_path.write_text(additional_entry, encoding="utf-8")
        common = [
            "pnpm",
            "exec",
            "esbuild",
            "--bundle",
            "--minify",
            "--format=esm",
            "--platform=browser",
            "--target=es2020",
        ]
        command(
            [
                *common,
                str(entry_path),
                f"--alias:@fluent/bundle={RUNTIME_BROWSER / 'node_modules/@fluent/bundle/index.js'}",
                f"--outfile={output_path}",
                f"--metafile={metafile_path}",
            ],
            cwd=RUNTIME_BROWSER,
        )
        command([*common, str(additional_path), f"--outfile={additional_output}"], cwd=RUNTIME_BROWSER)
        output = output_path.read_bytes()
        additional = additional_output.read_bytes()
        canary_script = (
            f"import({json.dumps(output_path.as_uri())}).then((module) => {{"
            "const value = module.payloadCanary;"
            "if (value.exactInteger !== '9007199254740993' || !value.negativeZero "
            "|| value.message !== 'en-US message 99' "
            "|| value.providerFormat !== 'citry-i18n-provider-research/1' "
            "|| value.richRelocationFormat !== 'citry-i18n-rich-relocation-research/2') "
            "throw new Error(JSON.stringify(value));"
            "});"
        )
        command(["node", "--input-type=module", "--eval", canary_script])
        inputs = sorted(
            path if not path.startswith("../../../../../../../") else Path(path).name
            for path in json.loads(metafile_path.read_text(encoding="utf-8"))["inputs"]
        )
    complete_gzip = len(gzip.compress(output, mtime=0))
    additional_gzip = len(gzip.compress(additional, mtime=0))
    require(complete_gzip <= 35 * 1024, f"complete client payload is {complete_gzip} gzip bytes")
    require(additional_gzip <= 15 * 1024, f"additional locale is {additional_gzip} gzip bytes")
    return {
        "additional_locale": {
            "gzip_bytes": additional_gzip,
            "limit_bytes": 15 * 1024,
            "message_count": 100,
            "minified_bytes": len(additional),
            "passes": True,
            "source_bytes": len(additional_source.encode()),
        },
        "complete_client": {
            "catalog_parser_included": True,
            "gzip_bytes": complete_gzip,
            "limit_bytes": 35 * 1024,
            "message_count": 100,
            "metafile_inputs": inputs,
            "minified_bytes": len(output),
            "passes": True,
            "source_bytes": len(source.encode()),
        },
    }


def load_provider_runner() -> Any:
    spec = importlib.util.spec_from_file_location("citry_i18n_provider_phase0", PROVIDER_RUNNER)
    require(spec is not None and spec.loader is not None, "could not load the provider exploration harness")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_switch_benchmarks() -> tuple[dict[str, Any], dict[str, Any]]:
    provider = load_provider_runner()
    engine, document, _server_gates = provider.build_fixture(benchmark_readers=100)
    candidate = PROVIDER_CANDIDATE.read_text(encoding="utf-8")
    benchmark_script = SWITCH_BENCHMARK.read_text(encoding="utf-8")
    measurements: dict[str, Any] = {}
    gates: dict[str, Any] = {}
    versions: dict[str, str] = {}
    with provider.serve_page(engine, document) as url, sync_playwright() as playwright:
        for name in BROWSER_NAMES:
            browser = getattr(playwright, name).launch(headless=True)
            try:
                versions[name] = browser.version
                page = browser.new_page()
                errors: list[str] = []
                page.on("pageerror", lambda error, target=errors: target.append(str(error)))
                page.add_init_script(script=candidate)
                page.goto(url)
                page.wait_for_function(
                    "Object.keys(window.__providerProbe?.readers || {}).length === 105 "
                    "&& Object.keys(window.__providerProbe?.services || {}).length === 4"
                )
                page.add_script_tag(content=benchmark_script)
                result = page.evaluate("CitryI18nSwitchBenchmark.runSwitchBenchmark()")
                require(not errors, f"{name} page errors: {errors!r}")
                browser_gates = {
                    "no_mixed_sampled_frames": result["mixed_frames"] == 0,
                    "p95_at_or_below_50_ms": result["p95_ms"] <= 50,
                    "thirty_samples": result["sample_count"] == 30,
                }
                require(all(browser_gates.values()), f"{name} switch benchmark failed: {result!r}")
                gates[name] = browser_gates
                measurements[name] = {
                    key: round(value, 4) if isinstance(value, float) else value for key, value in result.items()
                }
            finally:
                browser.close()
    return (
        {"browser_versions": versions, "gates": gates, "result": "PASS"},
        {"host_specific": True, "measurements": measurements, "threshold_p95_ms": 50},
    )


def build_evidence() -> tuple[dict[str, Any], dict[str, Any]]:
    ensure_always_on_checks()
    provider_evidence = json.loads(PROVIDER_EVIDENCE.read_text(encoding="utf-8"))
    fixed_locale_zero = provider_evidence["server_provider_gates"]["server_only_provider_has_no_i18n_browser_payload"]
    require(fixed_locale_zero is True, "the fixed-locale zero-byte provider gate is not checked and passing")
    payload = build_browser_payload()
    switch, measurements = run_switch_benchmarks()
    return (
        {
            "artifacts": {
                "complete_payload": sha256(COMPLETE_PAYLOAD),
                "harness": sha256(Path(__file__)),
                "pnpm_lock": sha256(RUNTIME_BROWSER / "pnpm-lock.yaml"),
                "production_slice_evidence": sha256(PRODUCTION_EVIDENCE),
                "provider_candidate": sha256(PROVIDER_CANDIDATE),
                "provider_evidence": sha256(PROVIDER_EVIDENCE),
                "provider_runner": sha256(PROVIDER_RUNNER),
                "rich_candidate": sha256(RICH_CANDIDATE),
                "switch_benchmark": sha256(SWITCH_BENCHMARK),
            },
            "dependencies": {
                "esbuild": command(["pnpm", "exec", "esbuild", "--version"], cwd=RUNTIME_BROWSER),
                "playwright": importlib.metadata.version("playwright"),
            },
            "environment": {
                "machine": platform.machine(),
                "node": command(["node", "--version"]),
                "platform": platform.platform(),
                "python": platform.python_version(),
            },
            "fixed_locale": {"browser_i18n_bytes": 0, "passes": fixed_locale_zero},
            "payload": payload,
            "result": "PASS_BOUNDED",
            "switch": switch,
        },
        measurements,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--measurements", type=Path, default=HERE / "performance.json")
    parser.add_argument("--output", type=Path, default=HERE / "evidence.json")
    arguments = parser.parse_args()
    evidence, measurements = build_evidence()
    arguments.output.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    arguments.measurements.write_text(
        json.dumps(measurements, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    sys.stdout.write(f"PASS_BOUNDED\nevidence={arguments.output}\nmeasurements={arguments.measurements}\n")


if __name__ == "__main__":
    main()
