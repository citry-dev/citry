"""Cross-family authoring contracts learned from the Tabs production pass."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
COMPONENT_ROOT = REPO_ROOT / "packages/py/citry_ui/citry_ui/components"
SPEC_ROOT = REPO_ROOT / "docs/design/ui_components"

SPEC_HEADINGS = (
    "## 1. Purpose and product bar",
    "## 2. Prior art and complaints",
    "## 3. Public composition and anatomy",
    "## 4. Server inputs and client inputs",
    "## 5. State model",
    "## 6. Slots and slot data",
    "## 7. Callbacks, native events, and methods",
    "## 8. Semantics, keyboard, focus, and assistive technology",
    "## 9. Native forms and validation",
    "## 10. Styling and theme contract",
    "## 11. Environmental behavior",
    "## 12. Overlay and layering behavior",
    "## 13. Collections, async data, and identity",
    "## 14. Server render, morph, and cleanup",
    "## 15. Security and content trust",
    "## 16. Assets and performance",
    "## 17. Acceptance matrix",
    "## 18. Compatibility classification",
    "## 19. Public documentation contract",
    "## 20. Open decisions and deferred work",
)


@dataclass(frozen=True, slots=True)
class FamilyContract:
    package: str
    module: str
    spec: str
    reflected_attributes: frozenset[str]


FAMILIES = (
    FamilyContract(
        "cbutton",
        "cbutton.py",
        "button.md",
        frozenset(
            {
                "data-loading",
                "data-disabled",
                "data-variant",
                "data-intent",
                "data-size",
                "data-block",
                "data-loading-position",
            }
        ),
    ),
    FamilyContract(
        "cfield",
        "cfield.py",
        "field-input.md",
        frozenset(
            {
                "data-required",
                "data-disabled",
                "data-readonly",
                "data-invalid",
                "data-orientation",
                "data-density",
                "data-variant",
                "data-size",
            }
        ),
    ),
    FamilyContract(
        "cform",
        "cform.py",
        "form.md",
        frozenset(
            {
                "data-disabled",
                "data-readonly",
                "data-submitting",
                "data-validation-attempted",
            }
        ),
    ),
    FamilyContract(
        "cdialog",
        "cdialog.py",
        "dialog.md",
        frozenset({"data-open", "data-size", "data-scroll"}),
    ),
    FamilyContract(
        "ccombobox",
        "ccombobox.py",
        "combobox.md",
        frozenset(
            {
                "data-open",
                "data-loading",
                "data-empty",
                "data-error",
                "data-required",
                "data-disabled",
                "data-readonly",
                "data-invalid",
                "data-variant",
                "data-size",
                "data-value",
                "data-selected",
                "data-highlighted",
            }
        ),
    ),
    FamilyContract(
        "ctable",
        "ctable.py",
        "table.md",
        frozenset(
            {
                "data-state",
                "data-variant",
                "data-density",
                "data-striped",
                "data-hover",
                "data-sticky-header",
                "data-column-borders",
                "data-layout",
                "data-overflow",
                "data-caption-side",
                "data-row-key",
                "data-column-key",
                "data-align",
            }
        ),
    ),
)


def _family_sources(family: FamilyContract) -> tuple[str, str, str]:
    package = COMPONENT_ROOT / family.package
    return (
        (package / family.module).read_text(encoding="utf-8"),
        (package / "api.md").read_text(encoding="utf-8"),
        (SPEC_ROOT / family.spec).read_text(encoding="utf-8"),
    )


def _documented_api_surface(family: FamilyContract) -> tuple[frozenset[str], frozenset[str], frozenset[str]]:
    path = COMPONENT_ROOT / family.package / "api.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    variables = frozenset(entry["name"] for table in data["css"] for entry in table["entries"])
    attributes = frozenset(entry["name"] for table in data["attributes"] for entry in table["entries"])
    parts: set[str] = set()
    for table in data["selectors"]:
        for entry in table["entries"]:
            match = re.fullmatch(r'\[data-citry-ui-part="([a-z0-9-]+)"\]', entry["selector"])
            if match is not None:
                parts.add(match.group(1))
    return variables, attributes, frozenset(parts)


def test_every_public_component_reference_exposes_direct_class_and_style_inputs():
    for path in sorted(COMPONENT_ROOT.glob("c*/api.yml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        server_inputs = {
            table["component"]: {entry["name"] for entry in table["entries"]}
            for table in data["inputs"]
            if table["channel"] == "server"
        }

        assert set(server_inputs) == set(data["components"])
        for component, names in server_inputs.items():
            assert {"class_", "style"} <= names, f"{path.name} omits root styling inputs for {component}"


@pytest.mark.parametrize("family", FAMILIES, ids=lambda family: family.package)
def test_production_spec_uses_the_complete_authoring_template(family: FamilyContract):
    _, _, spec = _family_sources(family)
    headings = tuple(line for line in spec.splitlines() if line.startswith("## "))

    assert headings == SPEC_HEADINGS


@pytest.mark.parametrize("family", FAMILIES, ids=lambda family: family.package)
def test_runtime_public_css_contract_is_documented_in_spec_and_api(family: FamilyContract):
    source, _, spec = _family_sources(family)
    parts = frozenset(re.findall(r'data-citry-ui-part=["\']([a-z0-9-]+)', source))
    variables = frozenset(re.findall(r"(?<!_)--cui-[a-z0-9-]+", source))
    documented_variables, documented_attributes, documented_parts = _documented_api_surface(family)

    assert parts
    assert variables
    assert documented_parts == parts
    assert documented_variables == variables
    assert documented_attributes == family.reflected_attributes
    for public_name in (*sorted(parts), *sorted(variables), *sorted(family.reflected_attributes)):
        assert public_name in spec, f"{family.spec} omits {public_name}"


@pytest.mark.parametrize("family", FAMILIES, ids=lambda family: family.package)
def test_public_variables_resolve_through_private_effective_variables(family: FamilyContract):
    source, _, _ = _family_sources(family)
    variables = frozenset(re.findall(r"(?<!_)--cui-[a-z0-9-]+", source))

    for public_name in variables:
        private_name = public_name.replace("--cui-", "--_cui-", 1)
        resolution = re.compile(
            rf"{re.escape(private_name)}\s*:\s*var\(\s*{re.escape(public_name)}\s*,",
            re.MULTILINE,
        )
        assert resolution.search(source), f"{public_name} is not resolved by {private_name}"


@pytest.mark.parametrize("family", FAMILIES, ids=lambda family: family.package)
def test_owned_part_marker_follows_consumer_attribute_spread(family: FamilyContract):
    source, _, _ = _family_sources(family)
    tags = re.findall(r"<[a-zA-Z][^>]*>", source, flags=re.DOTALL)
    bound_parts = [tag for tag in tags if "c-bind=" in tag and "data-citry-ui-part=" in tag]

    assert bound_parts
    for tag in bound_parts:
        assert tag.index("c-bind=") < tag.index("data-citry-ui-part=")
