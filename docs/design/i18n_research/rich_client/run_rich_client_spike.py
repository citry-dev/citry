from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import json
import os
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
FIXTURES = HERE / "fixtures"
SHARED_BROWSER = HERE.parent / "runtime_backend" / "browser"
BROWSER_NAMES = ("chromium", "firefox", "webkit")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_command(command: list[str], *, cwd: Path = REPO, env: dict[str, str] | None = None) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.returncode:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(command)}\n{completed.stdout}")
    return completed.stdout.strip()


def ensure_always_on_checks() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    asserts = [node for node in ast.walk(tree) if isinstance(node, ast.Assert)]
    require(not asserts, "the evidence harness must not use optimization-sensitive assert statements")
    browser_source = (BROWSER / "runner.js").read_text(encoding="utf-8")
    require("console.assert" not in browser_source, "the browser probe must not use console.assert")


def installed_node_package(name: str) -> dict[str, Any]:
    package_path = SHARED_BROWSER / "node_modules" / name / "package.json"
    require(package_path.is_file(), f"missing installed browser package {name}; run pnpm install first")
    return json.loads(package_path.read_text(encoding="utf-8"))


def bundle_probe(destination: Path) -> None:
    env = dict(os.environ)
    env["NODE_PATH"] = str(SHARED_BROWSER / "node_modules")
    run_command(
        [
            "pnpm",
            "--dir",
            str(SHARED_BROWSER),
            "exec",
            "esbuild",
            str(BROWSER / "runner.js"),
            "--bundle",
            "--format=iife",
            "--platform=browser",
            f"--outfile={destination}",
        ],
        env=env,
    )


def fixture_sources() -> dict[str, str]:
    return {
        "ar": (FIXTURES / "ar.ftl").read_text(encoding="utf-8"),
        "en-US": (FIXTURES / "en-US.ftl").read_text(encoding="utf-8"),
        "missing": (FIXTURES / "missing-slot.ftl").read_text(encoding="utf-8"),
    }


def run_browsers(bundle: Path) -> tuple[dict[str, Any], dict[str, str]]:
    sources = fixture_sources()
    results: dict[str, Any] = {}
    versions: dict[str, str] = {}
    with sync_playwright() as playwright:
        for name in BROWSER_NAMES:
            browser_type = getattr(playwright, name)
            browser = browser_type.launch(headless=True)
            try:
                versions[name] = browser.version
                page = browser.new_page()
                page.set_content("<!doctype html><html lang='en'><head></head><body></body></html>")
                page.add_script_tag(path=bundle)
                result = page.evaluate("sources => globalThis.runCitryRichClientProbe(sources)", sources)
                require(isinstance(result, dict), f"{name} returned invalid evidence: {result!r}")
                results[name] = result
            finally:
                browser.close()
    canonical = results[BROWSER_NAMES[0]]
    require(
        all(results[name] == canonical for name in BROWSER_NAMES[1:]),
        f"browser semantic results differ: {results!r}",
    )
    return results, versions


def artifact_hashes(bundle: Path) -> dict[str, str]:
    paths = {
        "browser_runner": BROWSER / "runner.js",
        "fixture_ar": FIXTURES / "ar.ftl",
        "fixture_en_us": FIXTURES / "en-US.ftl",
        "fixture_missing_slot": FIXTURES / "missing-slot.ftl",
        "harness": Path(__file__),
        "shared_browser_lock": SHARED_BROWSER / "pnpm-lock.yaml",
        "shared_browser_manifest": SHARED_BROWSER / "package.json",
        "uv_lock": REPO / "uv.lock",
    }
    hashes = {name: sha256(path) for name, path in paths.items()}
    hashes["browser_bundle"] = sha256(bundle)
    return hashes


def build_evidence() -> dict[str, Any]:
    ensure_always_on_checks()
    package = json.loads((SHARED_BROWSER / "package.json").read_text(encoding="utf-8"))
    fluent = installed_node_package("@fluent/bundle")
    esbuild = installed_node_package("esbuild")
    require(fluent["version"] == package["dependencies"]["@fluent/bundle"], "active Fluent version drift")
    require(esbuild["version"] == package["devDependencies"]["esbuild"], "active esbuild version drift")
    require(
        run_command(["pnpm", "--dir", str(SHARED_BROWSER), "exec", "esbuild", "--version"]) == esbuild["version"],
        "active esbuild executable drift",
    )
    require(run_command(["pnpm", "--version"]) == "10.32.1", "active pnpm version drift")
    require(importlib.metadata.version("playwright") == "1.62.0", "active Playwright version drift")

    with tempfile.TemporaryDirectory(prefix="citry-i18n-rich-client-") as directory:
        bundle = Path(directory) / "probe.js"
        bundle_probe(bundle)
        results, browser_versions = run_browsers(bundle)
        hashes = artifact_hashes(bundle)

    canonical = results[BROWSER_NAMES[0]]
    gates = canonical["gates"] | canonical["performance"]
    require(all(value is True for value in gates.values()), f"one or more browser gates failed: {gates!r}")
    return {
        "artifacts": hashes,
        "browser_results_equal": True,
        "browser_versions": browser_versions,
        "bounded_limits": [
            "the probe uses a production-shaped range reconciler, not Citry's current ownership runtime",
            (
                "the probe starts from compiled FTL that already contains SLOT; "
                "authored-source compilation was proved separately"
            ),
            "cross-language rich fallback is rejected rather than rendered with a metadata-bearing rich wrapper",
            "the timing gate uses a tiny two-locale fixture and is not the full catalog performance benchmark",
        ],
        "dependencies": {
            "esbuild": esbuild["version"],
            "fluent_bundle": fluent["version"],
            "greenlet": importlib.metadata.version("greenlet"),
            "playwright": importlib.metadata.version("playwright"),
            "pnpm": "10.32.1",
            "pyee": importlib.metadata.version("pyee"),
            "uv": run_command(["uv", "--version"]),
        },
        "environment": {
            "machine": platform.machine(),
            "node": run_command(["node", "--version"]),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "python_executable_name": Path(sys.executable).name,
        },
        "result": "PASS_BOUNDED",
        "semantic_result": canonical,
        "tested_browsers": list(BROWSER_NAMES),
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
    sys.stdout.write(f"PASS_BOUNDED\nevidence={arguments.output}\n")


if __name__ == "__main__":
    main()
