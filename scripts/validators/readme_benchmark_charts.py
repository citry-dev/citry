"""
The README's benchmark chart must show the run the docs site shows.

The README carries the error benchmark chart as PNG files, drawn by
`python -m docs_site.scripts.benchmark_images` from
`docs_site/data/error_prevention.json`. When a new benchmark run replaces that
data, the docs site redraws its charts on the next build, but the README keeps
the old images and the old counts in its alt text until someone reruns the
script. This check rebuilds the README block from the data and fails when the
two differ, so the README cannot fall behind the site unnoticed.

It also checks that each linked image exists and still holds the bytes its
name's hash was taken from. A released package's PyPI page loads these files
from `main`, so a file that was changed in place would change that page too.

The check does not compare pixels. After a change to the chart's style, with
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
_RERUN = "rerun `uv run --no-sync python -m docs_site.scripts.benchmark_images`"


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
    try:
        start, end = helper.find_block(readme)
    except ValueError as exc:
        return [f"README.md: {exc}"]
    block = readme[start:end]
    line = readme.count("\n", 0, start) + 1

    names = helper.image_names_in(block)
    parsed = {name: helper.parse_image_name(name) for name in names}
    themes = sorted(info["theme"] for info in parsed.values() if info)
    if themes != sorted(helper.THEMES) or not all(parsed.values()):
        return [f"README.md:{line} benchmark chart block must link one light and one dark image; {_RERUN}"]

    problems: list[str] = []
    data = helper.load_data()
    for name, info in parsed.items():
        if info is None:
            continue
        if info["run"] != data["run"]:
            problems.append(
                f"README.md:{line} shows benchmark run {info['run']}, but the data has run {data['run']}; {_RERUN}"
            )
            continue
        path: Path = helper.ASSET_DIR / name
        if not path.is_file():
            problems.append(f"README.md:{line} links {name}, which is not in docs/assets/benchmarks/; {_RERUN}")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[: helper.HASH_LENGTH]
        if digest != info["hash"]:
            problems.append(
                f"docs/assets/benchmarks/{name} changed after it was written, and released PyPI pages "
                f"still load it. Restore it with `git checkout -- docs/assets/benchmarks/{name}`, "
                f"then {_RERUN} to save a changed chart under a new name"
            )
    if problems:
        return problems

    light = next(name for name, info in parsed.items() if info and info["theme"] == "light")
    dark = next(name for name, info in parsed.items() if info and info["theme"] == "dark")
    if block != helper.readme_block(data, light_name=light, dark_name=dark):
        problems.append(f"README.md:{line} benchmark chart block does not match the data; {_RERUN}")
    return problems
