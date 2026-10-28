"""
Check committed files that are exact copies of another file, or that record which Vue version they were generated from.

No check here rebuilds these files: the copies have no build step, the HTML
attribute module's generator downloads live standards, which CI cannot do, and
the DOM member table's own check needs that generator's separate install.
Each check is a byte or text comparison that needs only the standard library,
which lets the early "Generated files" CI job run it without installing the
workspace.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Each pair is (copy, original). The copy must hold the same bytes.
EXACT_COPIES: tuple[tuple[str, str], ...] = (
    # Browsers ask for /favicon.svg, and the site's icon artwork is citry-icon.svg.
    ("docs_site/static/img/favicon.svg", "docs_site/static/img/citry-icon.svg"),
    # The htmx demo serves its own copy of the logo, so the demo runs without the docs site.
    ("examples/demos/htmx/app/static/citry-mark.svg", "docs_site/static/img/citry-mark.svg"),
)

HTML_ATTRIBUTE_VALUES = "packages/py/citry/citry/_html_attribute_values.py"
VUE_TYPES_INVENTORY = "packages/py/citry_lsp/citry_lsp/types/inventory.json"
# The generator writes this line into the module header from the Vue types it read.
_VUE_TYPES_LINE = re.compile(r"^- @vue/runtime-dom (\S+) types,", re.MULTILINE)

DOM_MEMBERS = "crates/citry_vue_compiler/src/dom_members.rs"
# The generator writes this line into the table's header from the Vue it tested against.
_DOM_MEMBERS_VUE_LINE = re.compile(r"^// - @vue/runtime-dom (\S+)$", re.MULTILINE)


def _missing(root: Path, *relatives: str) -> list[str]:
    return [f"{relative} is missing" for relative in relatives if not (root / relative).is_file()]


def _check_exact_copies(root: Path) -> list[str]:
    problems = []
    for copy, original in EXACT_COPIES:
        missing = _missing(root, copy, original)
        if missing:
            problems.extend(missing)
        elif (root / copy).read_bytes() != (root / original).read_bytes():
            problems.append(f"{copy} differs from {original}; copy {original} over it")
    return problems


def _check_html_attribute_vue_version(root: Path) -> list[str]:
    # The generator reads Vue's DOM event names from the Vue types copied into
    # citry_lsp, so a Vue bump that refreshes those types must also regenerate
    # the module.
    missing = _missing(root, HTML_ATTRIBUTE_VALUES, VUE_TYPES_INVENTORY)
    if missing:
        return missing
    header = (root / HTML_ATTRIBUTE_VALUES).read_text(encoding="utf-8")
    match = _VUE_TYPES_LINE.search(header)
    if match is None:
        return [f"{HTML_ATTRIBUTE_VALUES} does not name the @vue/runtime-dom version it was generated from"]
    shipped = json.loads((root / VUE_TYPES_INVENTORY).read_text(encoding="utf-8"))["vue"]
    if match.group(1) != shipped:
        return [
            f"{HTML_ATTRIBUTE_VALUES} was generated from @vue/runtime-dom {match.group(1)}, "
            f"but {VUE_TYPES_INVENTORY} holds Vue {shipped}; "
            "run python scripts/generate_html_attribute_values.py"
        ]
    return []


def _check_dom_members_vue_version(root: Path) -> list[str]:
    # The table records what Vue's client render leaves in the page for each
    # element and attribute name, so a Vue bump must regenerate it.
    missing = _missing(root, DOM_MEMBERS, VUE_TYPES_INVENTORY)
    if missing:
        return missing
    header = (root / DOM_MEMBERS).read_text(encoding="utf-8")
    match = _DOM_MEMBERS_VUE_LINE.search(header)
    if match is None:
        return [f"{DOM_MEMBERS} does not name the @vue/runtime-dom version it was generated from"]
    shipped = json.loads((root / VUE_TYPES_INVENTORY).read_text(encoding="utf-8"))["vue"]
    if match.group(1) != shipped:
        return [
            f"{DOM_MEMBERS} was generated from @vue/runtime-dom {match.group(1)}, "
            f"but {VUE_TYPES_INVENTORY} holds Vue {shipped}; "
            "run pnpm --dir tools/dom-members run refresh"
        ]
    return []


def check(root: Path = ROOT) -> list[str]:
    """Return one problem for each copy or recorded version that no longer matches."""
    problems = [
        *_check_exact_copies(root),
        *_check_html_attribute_vue_version(root),
        *_check_dom_members_vue_version(root),
    ]
    # Two checks read the same inventory, so a missing one would be reported twice.
    return list(dict.fromkeys(problems))


if __name__ == "__main__":
    found = check()
    for problem in found:
        sys.stderr.write(f"{problem}\n")
    if not found:
        sys.stdout.write("Copied files and the recorded Vue version are current.\n")
    sys.exit(1 if found else 0)
