"""
The README's advisory section must show the numbers in its data file.

The README section "Monitoring vulnerabilities across the ecosystem" is
written by `python -m docs_site.scripts.advisory_watch` from
`docs_site/data/advisory_watch.json`: the sentence with the total, two SVG
files (light and dark), the alt text with every project's count, and the
note with the as-of month. The landing page draws the same graphic from the
same data on every build, but the README keeps whatever the script last
wrote. This check redraws the block and both SVGs from the data and fails
when they differ, so the README cannot fall behind the site unnoticed.

The SVGs are drawn without a browser, so the same data always gives the
same bytes. That lets the check compare each linked file with a fresh
drawing, and also make sure no file was changed after it was written: a
released package's PyPI page loads these files from `main`. Last, it makes
sure the landing page still has a section with the README's heading.
"""

import hashlib
import importlib.util
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[2]
# Loaded by file path, as validate.py loads this module: the docs_site package
# is not on the import path here, and advisory_watch needs nothing from it.
_HELPER_PATH = REPO_ROOT / "docs_site" / "scripts" / "advisory_watch.py"
_RERUN = "rerun `uv run --no-sync python -m docs_site.scripts.advisory_watch`"


def _helper() -> ModuleType:
    spec = importlib.util.spec_from_file_location("advisory_watch", _HELPER_PATH)
    if spec is None or spec.loader is None:
        msg = f"could not load {_HELPER_PATH}"
        raise ImportError(msg)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check() -> list[str]:
    helper = _helper()
    readme = helper.README_PATH.read_text(encoding="utf-8")
    problems = _check_block(helper, readme)
    landing_path: Path = helper.LANDING_PATH
    headings = {line.strip() for line in landing_path.read_text(encoding="utf-8").splitlines()}
    if f"## {helper.HEADING}" not in headings:
        where = landing_path.relative_to(REPO_ROOT).as_posix()
        problems.append(
            f"{where}: has no '## {helper.HEADING}' section, but the README's advisory block repeats it; "
            f"restore the heading, or change HEADING in docs_site/scripts/advisory_watch.py and {_RERUN}"
        )
    return problems


def _check_block(helper: ModuleType, readme: str) -> list[str]:
    """Return the problems with the README block and the files it links."""
    try:
        start, end = helper.find_block(readme)
    except ValueError as exc:
        return [f"README.md: {exc}"]
    line = readme.count("\n", 0, start) + 1
    data = helper.load_data()
    try:
        helper.check_data(data)
    except ValueError as exc:
        return [f"{helper.DATA_PATH.relative_to(REPO_ROOT).as_posix()}: {exc}"]

    problems: list[str] = []
    # A file whose bytes no longer match its name was edited in place, which
    # would also change every released PyPI page that loads it.
    for name in helper.image_names_in(readme[start:end]):
        path: Path = helper.ASSET_DIR / name
        info = helper.parse_image_name(name)
        if info is None or not path.is_file():
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[: helper.HASH_LENGTH]
        if digest != info["hash"]:
            problems.append(
                f"docs/assets/advisories/{name} changed after it was written, and released PyPI pages "
                f"still load it. Restore it with `git checkout -- docs/assets/advisories/{name}`, then {_RERUN}"
            )

    names = {}
    for theme in helper.THEMES:
        content = helper.file_svg(data, theme)
        names[theme] = helper.image_name(data, content, theme)
        if not (helper.ASSET_DIR / names[theme]).is_file():
            problems.append(f"README.md:{line} the {theme} advisory graphic for the current data is missing; {_RERUN}")
    expected = helper.readme_block(data, light_name=names["light"], dark_name=names["dark"])
    if readme[start:end] != expected:
        problems.append(f"README.md:{line} advisory block does not match the data; {_RERUN}")
    return problems
