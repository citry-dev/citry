"""Capture deterministic visual candidates from shared Citry UI scenarios."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from importlib import import_module
from importlib.metadata import version
from pathlib import Path

from citry_ui.quality.routes import render_scenario
from citry_ui.quality.scenarios import SCENARIOS, QualityTool, scenario_by_id


@dataclass(frozen=True, slots=True)
class VisualProfile:
    """A pinned browser environment that protects one visual decision."""

    id: str
    width: int
    height: int
    color_scheme: str = "light"
    reduced_motion: str = "no-preference"
    forced_colors: str = "none"
    direction: str = "ltr"
    touch: bool = False
    zoom_percent: int = 100


@dataclass(frozen=True, slots=True)
class CapturePlanEntry:
    """One scenario and environment pair selected by bounded coverage."""

    scenario_id: str
    profile: VisualProfile


VISUAL_PROFILES = {
    "desktop-light": VisualProfile("desktop-light", 1280, 900),
    "desktop-dark": VisualProfile("desktop-dark", 1280, 900, color_scheme="dark"),
    "narrow-light": VisualProfile("narrow-light", 390, 844),
    "rtl-light": VisualProfile("rtl-light", 1280, 900, direction="rtl"),
    "reduced-motion": VisualProfile("reduced-motion", 1280, 900, reduced_motion="reduce"),
    "forced-colors": VisualProfile("forced-colors", 1280, 900, forced_colors="active"),
    "touch-light": VisualProfile("touch-light", 390, 844, touch=True),
    # A 640 CSS-pixel viewport represents the reflow pressure of viewing a
    # 1280-pixel desktop layout at 200 percent browser zoom.
    "zoom-200-reflow": VisualProfile("zoom-200-reflow", 640, 450, zoom_percent=200),
    # A 320 CSS-pixel viewport applies the corresponding 400 percent reflow
    # pressure. Full-page capture keeps vertical content reviewable.
    "zoom-400-reflow": VisualProfile("zoom-400-reflow", 320, 450, zoom_percent=400),
}


def capture_plan() -> tuple[CapturePlanEntry, ...]:
    """Select pairwise visual profiles without building a Cartesian matrix."""
    entries: list[CapturePlanEntry] = []
    for scenario in SCENARIOS:
        if QualityTool.SCREENSHOT not in scenario.tools:
            continue
        profile_ids = ["desktop-light"]
        if "dark" in scenario.profiles:
            profile_ids.append("desktop-dark")
        if "narrow" in scenario.profiles:
            profile_ids.append("narrow-light")
        if "rtl" in scenario.profiles:
            profile_ids.append("rtl-light")
        if "reduced-motion" in scenario.profiles:
            profile_ids.append("reduced-motion")
        if "forced-colors" in scenario.profiles:
            profile_ids.append("forced-colors")
        if "touch" in scenario.profiles:
            profile_ids.append("touch-light")
        if "zoom-200" in scenario.profiles:
            profile_ids.append("zoom-200-reflow")
        if "zoom-400" in scenario.profiles:
            profile_ids.append("zoom-400-reflow")
        entries.extend(CapturePlanEntry(scenario.id, VISUAL_PROFILES[profile_id]) for profile_id in profile_ids)
    return tuple(entries)


def _safe_name(value: str) -> str:
    return value.replace(".", "-").replace("/", "-")


def capture_visuals(
    output_dir: Path,
    *,
    scenario_id: str | None = None,
    profile_id: str | None = None,
) -> dict[str, object]:
    """Capture candidate PNGs and return their human-review ledger."""
    try:
        sync_playwright = import_module("playwright.sync_api").sync_playwright
    except (AttributeError, ModuleNotFoundError) as error:
        msg = "Install the citry-ui e2e group before capturing visual candidates."
        raise RuntimeError(msg) from error

    if scenario_id is not None:
        scenario_by_id(scenario_id)
    if profile_id is not None and profile_id not in VISUAL_PROFILES:
        choices = ", ".join(VISUAL_PROFILES)
        msg = f"Unknown visual profile {profile_id!r}; choose one of: {choices}."
        raise ValueError(msg)

    plan = tuple(
        entry
        for entry in capture_plan()
        if (scenario_id is None or entry.scenario_id == scenario_id)
        and (profile_id is None or entry.profile.id == profile_id)
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    captures: list[dict[str, object]] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            browser_version = browser.version
            for entry in plan:
                profile = entry.profile
                context = browser.new_context(
                    viewport={"width": profile.width, "height": profile.height},
                    color_scheme=profile.color_scheme,
                    reduced_motion=profile.reduced_motion,
                    forced_colors=profile.forced_colors,
                    has_touch=profile.touch,
                    locale="en-US",
                    timezone_id="UTC",
                )
                try:
                    page = context.new_page()
                    page.set_content(render_scenario(entry.scenario_id), wait_until="load")
                    scenario = scenario_by_id(entry.scenario_id)
                    page.wait_for_selector(scenario.ready_selector)
                    if profile.direction == "rtl":
                        page.evaluate("document.documentElement.dir = 'rtl'")
                    page.add_style_tag(
                        content="*, *::before, *::after { animation: none !important; transition: none !important; }",
                    )
                    path = output_dir / f"{_safe_name(entry.scenario_id)}--{profile.id}.png"
                    page.screenshot(path=path, full_page=True, animations="disabled")
                    captures.append(
                        {
                            "scenario": entry.scenario_id,
                            "profile": asdict(profile),
                            "file": path.name,
                            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                            "review_status": "awaiting-human-review",
                        },
                    )
                finally:
                    context.close()
        finally:
            browser.close()

    return {
        "schema": "citry-ui-visual-candidates/v1",
        "browser": {"name": "chromium", "version": browser_version},
        "playwright": version("playwright"),
        "captures": captures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture Citry UI visual candidates for human review.")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--scenario")
    parser.add_argument("--profile", choices=tuple(VISUAL_PROFILES))
    args = parser.parse_args()
    try:
        report = capture_visuals(args.output_dir, scenario_id=args.scenario, profile_id=args.profile)
    except (RuntimeError, ValueError) as error:
        parser.exit(1, f"citry-ui visual capture failed: {error}\n")
    manifest = args.output_dir / "manifest.json"
    manifest.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
