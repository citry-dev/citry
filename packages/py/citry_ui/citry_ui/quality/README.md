# Citry UI quality workspace

This directory owns shared Phase 7.5 infrastructure that does not belong in
the `citry-ui` wheel. Component-specific docs, scenarios, screenshots, and
focused tests live with their component family. Cross-family tools and composed
workflows live here.

## Evidence budget

Each profile states the decision it protects and uses the smallest scenario
sample that can falsify that decision. Pull requests run deterministic Python
checks, the ready Chromium profile, docs projection, asset budgets, and wheel
inventory. Scheduled or release-candidate workflows own broader browser,
visual, host, Lighthouse, and scaling work. A local exploratory profile stops
within five minutes unless a concrete failure needs a narrower follow-up.

## Tool ownership

| Phase 7.5 area | Tool and input | Repository output | Current status |
|---|---|---|---|
| State catalog | `quality/scenarios.py` | Machine-readable scenario manifest | Ready |
| Standalone pages | `quality/routes.py` | Complete HTML per ready scenario | All catalog routes ready |
| Semantics and accessibility | Playwright plus pinned `axe-core` | Focused assertions, active-state scans, and owned incomplete results | Chromium profile ready |
| Visual candidates | `quality/capture_visuals.py` | Human-reviewable PNG plus deterministic metadata | Harness ready; approval remains human |
| HTML | Pinned Nu Html Checker over rendered route files | Scenario-labelled diagnostics | All routes wired to CI; local Java required |
| Complete-page audit | Dedicated Lighthouse config | Reports for the Orbit form and Ledger dashboard | CI configured; first hosted run pending |
| CSS coexistence | Pinned Bootstrap and compiled Tailwind output | Computed-style and operability assertions before and after Citry CSS | Tabs and both compositions ready |
| Assets and scaling | `quality/asset_report.py`, frozen budgets, and `quality/scaling.py` | Compressed thresholds and diagnostic scaling records | Ready |
| Hosts | Shared compositions through Django and FastAPI, plus ASGI and WSGI smoke tests | Host-labelled behavior record | Ready |
| Distribution | `quality/qualify_wheel.py` and clean CI environments | Wheel inventory, offline pip/uv lifecycle, uninstall, and browser smoke | CI configured; local inventory passes |
| Public docs | Component-owned `api.md` and `snippets/` projection | `/ui-library/components/*` | Every family has a checked live module |
| Exit record | `quality/exit_record.py` | Versioned scenario, tool, result, limitation, and manual-task manifest | Ready |

“Configured” is not a pass. The exit record accepts explicit CI results and
keeps visual approval, assistive-technology review, real-device samples, and
multi-release lifecycle work separate from automated evidence.
[`MANUAL_QUALIFICATION.md`](MANUAL_QUALIFICATION.md) defines the bounded visual,
keyboard, assistive-technology, and real-device sessions for that evidence.

## Commands

```console
uv run --no-sync python -m citry_ui.quality.scenarios
uv run --no-sync python -m citry_ui.quality.routes tabs.overview --output /tmp/tabs.html
uv run --no-sync python -m citry_ui.quality.asset_report
uv run --no-sync python -m citry_ui.quality.scaling --counts 1,10,100 --samples 1
uv run --no-sync python -m citry_ui.quality.exit_record --inspect-browser
pnpm install --frozen-lockfile --filter citry-dev-tooling
pnpm run citry-ui:quality-css
uv run --no-sync python -m citry_ui.quality.validate_html \
  /tmp/tabs.html --scenario tabs.overview
uv build --wheel packages/py/citry_ui --out-dir /tmp/citry-ui-dist
uv run --no-sync python -m citry_ui.quality.qualify_wheel \
  /tmp/citry-ui-dist/citry_ui-0.2.0-py3-none-any.whl
uv run --no-sync python -m citry_ui.quality.capture_visuals \
  /tmp/citry-ui-visuals --scenario tabs.overview --profile desktop-light
```

The wheel command accepts an explicit artifact path, so every command can run
from the repository root. HTML qualification requires Java 17 or newer. CI
installs that runtime explicitly; it does not use `vnu-jar`'s convenience Java
downloader.

Scaling measurements are diagnostic on purpose. Cross-machine timing is too
variable for a useful hard gate, while asset bytes, interaction budgets, and
cleanup behavior already have focused thresholds. The scheduled workflow
captures the full pairwise visual plan and the bounded scaling counts as CI
artifacts without putting generated reports into the wheel.
