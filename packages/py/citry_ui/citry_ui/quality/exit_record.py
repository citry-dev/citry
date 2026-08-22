"""Build the machine-readable Phase 7.5 qualification record."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from citry_ui.quality.accessibility import disposition_manifest
from citry_ui.quality.capture_visuals import capture_plan
from citry_ui.quality.scenarios import manifest_json

_PROFILE_COMMANDS = {
    "scenario-catalog": "python -m citry_ui.quality.scenarios",
    "routes": "pytest citry_ui/quality/tests/test_routes.py",
    "chromium-accessibility": "pytest citry_ui/quality/tests/e2e/test_scenario_catalog_e2e.py --browser chromium",
    "css-coexistence": "pytest citry_ui/quality/tests/e2e/test_scenario_catalog_e2e.py --browser chromium",
    "nu-html": "python -m citry_ui.quality.validate_html <rendered.html> --scenario <id>",
    "lighthouse": "lhci autorun --config=.github/lighthouserc.citry-ui.json",
    "visual-candidates": "python -m citry_ui.quality.capture_visuals <output-dir>",
    "assets": "python -m citry_ui.quality.asset_report",
    "scaling": "python -m citry_ui.quality.scaling",
    "hosts": "pytest citry_ui/quality/tests/test_hosts.py",
    "wheel": "python -m citry_ui.quality.qualify_wheel <wheel>",
    "public-docs": "python -m docs_site build-check --strict",
}
_VALID_STATUSES = frozenset(
    {
        "configured",
        "passed",
        "failed",
        "diagnostic-only",
        "awaiting-human-review",
        "unavailable",
    },
)


def _package_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "not-installed"


def _command_version(command: list[str]) -> str:
    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable"
    output = (completed.stdout or completed.stderr).strip().splitlines()
    return output[0] if output else "unavailable"


def _browser_version() -> str:
    try:
        sync_playwright = import_module("playwright.sync_api").sync_playwright
    except (AttributeError, ModuleNotFoundError):
        return "not-installed"
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                return browser.version
            finally:
                browser.close()
    except Exception:  # noqa: BLE001
        return "browser-not-installed"


def qualification_record(
    *,
    results: dict[str, str] | None = None,
    artifacts: dict[str, str] | None = None,
    inspect_browser: bool = False,
) -> dict[str, object]:
    """Return a deterministic record that distinguishes evidence from setup."""
    results = dict(results or {})
    artifacts = dict(artifacts or {})
    unknown = sorted((results.keys() | artifacts.keys()) - _PROFILE_COMMANDS.keys())
    if unknown:
        msg = f"Unknown qualification profiles: {', '.join(unknown)}."
        raise ValueError(msg)
    invalid = sorted({status for status in results.values() if status not in _VALID_STATUSES})
    if invalid:
        msg = f"Unknown qualification statuses: {', '.join(invalid)}."
        raise ValueError(msg)

    profiles = []
    for profile_id, command in _PROFILE_COMMANDS.items():
        profiles.append(
            {
                "id": profile_id,
                "status": results.get(
                    profile_id,
                    "diagnostic-only" if profile_id == "scaling" else "configured",
                ),
                "command": command,
                "artifact": artifacts.get(profile_id),
            },
        )

    return {
        "schema": "citry-ui-phase-7.5-exit/v1",
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": {
                name: _package_version(name)
                for name in ("citry", "citry-core", "citry-ui", "playwright", "pytest", "brotli")
            },
            "node": _command_version(["node", "--version"]),
            "java": _command_version(["java", "-version"]),
            "chromium": _browser_version() if inspect_browser else "not-inspected",
        },
        "scenarios": json.loads(manifest_json()),
        "visual_candidates": [
            {"scenario": entry.scenario_id, "profile": entry.profile.id, "status": "awaiting-human-review"}
            for entry in capture_plan()
        ],
        "axe_incomplete_dispositions": disposition_manifest(),
        "profiles": profiles,
        "manual_tasks": [
            {
                "id": "visual-design-approval",
                "status": "awaiting-human-review",
                "scope": "Hierarchy, typography, spacing, color, responsive behavior, and consistency.",
                "instructions": "citry_ui/quality/MANUAL_QUALIFICATION.md#review-visual-candidates",
            },
            {
                "id": "assistive-technology",
                "status": "unavailable",
                "scope": "NVDA, JAWS, VoiceOver, and TalkBack announcements and navigation.",
                "instructions": "citry_ui/quality/MANUAL_QUALIFICATION.md#assistive-technology-sessions",
            },
            {
                "id": "real-devices",
                "status": "unavailable",
                "scope": "Real Safari, iOS, Android, touch, zoom, and high-contrast samples.",
                "instructions": "citry_ui/quality/MANUAL_QUALIFICATION.md#real-device-and-environmental-sessions",
            },
            {
                "id": "multi-release-lifecycle",
                "status": "unavailable",
                "scope": "Upgrade and downgrade between published citry-ui releases.",
            },
        ],
        "known_limitations": [
            "The bundled catalog supplies en-US source messages; applications provide any additional locale catalogs.",
            "Headless counterparts remain parked until applications provide representative APIs and render trees.",
            "Scaling timings are diagnostic and do not act as cross-machine pass thresholds.",
        ],
    }


def _key_value(value: str) -> tuple[str, str]:
    key, separator, item = value.partition("=")
    if not separator or not key or not item:
        msg = f"Expected PROFILE=VALUE, got {value!r}."
        raise argparse.ArgumentTypeError(msg)
    return key, item


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Citry UI Phase 7.5 qualification record.")
    parser.add_argument("--result", action="append", default=[], type=_key_value)
    parser.add_argument("--artifact", action="append", default=[], type=_key_value)
    parser.add_argument("--inspect-browser", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        record = qualification_record(
            results=dict(args.result),
            artifacts=dict(args.artifact),
            inspect_browser=args.inspect_browser,
        )
    except ValueError as error:
        parser.exit(1, f"citry-ui exit record failed: {error}\n")
    payload = json.dumps(record, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        sys.stdout.write(payload)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
