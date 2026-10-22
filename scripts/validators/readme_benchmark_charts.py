"""
The README's benchmark charts must show the runs the docs site shows.

The README carries two benchmark charts as PNG files, the error chart and the
speed chart, drawn by `python -m docs_site.scripts.benchmark_images` from
`docs_site/data/error_prevention.json` and
`docs_site/data/benchmark_time_to_interactive.json`. When a new benchmark run
replaces that data, the docs site redraws its charts on the next build, but
the README keeps the old images and the old numbers in its alt text until
someone reruns the script. This check rebuilds each README block from the
data and fails when the two differ, so the README cannot fall behind the site
unnoticed.

Each block also names the Citry version the run measured, from
`VERSION_NOTES` and `SPEED_VERSION_NOTES` in `benchmark_readme.py`, so a new
run fails here until someone adds its note. The check also makes sure each
linked image exists and still holds the bytes its name's hash was taken from.
A released package's PyPI page loads these files from `main`, so a file that
was changed in place would change that page too. Last, it makes sure the
landing page still has a section with each block's heading, since the README
repeats the landing page's two benchmark sections.

The check does not compare pixels. After a change to a chart's style, with
the same run and data, the old images still pass, so rerun the script
yourself.
"""

import hashlib
import importlib.util
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[2]
# Loaded by file path, as validate.py loads this module: the docs_site package
# is not on the import path here, and benchmark_readme needs nothing from it.
_HELPER_PATH = REPO_ROOT / "docs_site" / "scripts" / "benchmark_readme.py"


def _rerun(chart: str) -> str:
    """Return the advice that fixes a stale block: the command that redraws this chart."""
    return f"rerun `uv run --no-sync python -m docs_site.scripts.benchmark_images {chart}`"


def _helper() -> ModuleType:
    spec = importlib.util.spec_from_file_location("benchmark_readme", _HELPER_PATH)
    if spec is None or spec.loader is None:
        msg = f"could not load {_HELPER_PATH}"
        raise ImportError(msg)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check() -> list[str]:
    helper = _helper()
    readme_path: Path = helper.README_PATH
    readme = readme_path.read_text(encoding="utf-8")
    problems: list[str] = []
    for chart in helper.CHARTS:
        problems += _check_block(helper, readme, chart)
    problems += _check_landing_headings(helper)
    return problems


def _check_block(helper: ModuleType, readme: str, chart: str) -> list[str]:
    """Return the problems with one chart's README block."""
    try:
        start, end = helper.find_block(readme, chart)
    except ValueError as exc:
        return [f"README.md: {exc}"]
    block = readme[start:end]
    line = readme.count("\n", 0, start) + 1
    rerun = _rerun(chart)

    names = helper.image_names_in(block)
    parsed = {name: helper.parse_image_name(name) for name in names}
    themes = sorted(info["theme"] for info in parsed.values() if info)
    # An image of the other chart in this block would pass every later check
    # against its own data, so the chart in the name must match too.
    charts = {info["chart"] for info in parsed.values() if info}
    if themes != sorted(helper.THEMES) or not all(parsed.values()) or charts != {chart}:
        return [
            f"README.md:{line} {chart} benchmark chart block must link one light and one dark {chart} image; {rerun}"
        ]

    problems: list[str] = []
    data = helper.load_data(chart)
    run = helper.run_id(chart, data)
    for name, info in parsed.items():
        if info is None:
            continue
        if info["run"] != run:
            problems.append(
                f"README.md:{line} shows {chart} benchmark run {info['run']}, but the data has run {run}; {rerun}"
            )
            continue
        path: Path = helper.ASSET_DIR / name
        if not path.is_file():
            problems.append(f"README.md:{line} links {name}, which is not in docs/assets/benchmarks/; {rerun}")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[: helper.HASH_LENGTH]
        if digest != info["hash"]:
            problems.append(
                f"docs/assets/benchmarks/{name} changed after it was written, and released PyPI pages "
                f"still load it. Restore it with `git checkout -- docs/assets/benchmarks/{name}`, "
                f"then {rerun} to save a changed chart under a new name"
            )
    if problems:
        return problems

    light = next(name for name, info in parsed.items() if info and info["theme"] == "light")
    dark = next(name for name, info in parsed.items() if info and info["theme"] == "dark")
    try:
        expected = helper.readme_block(chart, data, light_name=light, dark_name=dark)
    except ValueError as exc:
        # The data cannot be drawn as it is, for example a run with no
        # version note or a case without a result.
        return [f"README.md:{line} {exc}"]
    if block != expected:
        problems.append(f"README.md:{line} {chart} benchmark chart block does not match the data; {rerun}")
    return problems


def _check_landing_headings(helper: ModuleType) -> list[str]:
    """Return a problem for each README heading the landing page no longer has."""
    landing_path: Path = helper.LANDING_PATH
    headings = {line.strip() for line in landing_path.read_text(encoding="utf-8").splitlines()}
    where = landing_path.relative_to(helper.REPO_ROOT).as_posix()
    return [
        f"{where}: has no '## {heading}' section, but the README's {chart} benchmark block repeats it; "
        "restore the heading, or change HEADINGS in docs_site/scripts/benchmark_readme.py to match "
        f"and {_rerun(chart)}"
        for chart, heading in helper.HEADINGS.items()
        if f"## {heading}" not in headings
    ]
