"""CSP compatibility contract for every production Citry UI component."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from pathlib import Path

import citry_ui
import citry_ui.components as component_package
from citry import Citry, LibraryComponent
from citry._app_selection import CheckAppSelection
from citry._checker import check_project
from citry._diagnostic_catalog import CSP_INCOMPATIBLE_BROWSER_CODE
from citry_ui.components import COMPONENTS


def _production_component_definitions() -> frozenset[type[LibraryComponent]]:
    definitions: set[type[LibraryComponent]] = set()
    excluded_packages = {"quality", "snippets", "tests"}

    for module_info in pkgutil.walk_packages(
        component_package.__path__,
        prefix=f"{component_package.__name__}.",
    ):
        if excluded_packages.intersection(module_info.name.split(".")):
            continue
        module = importlib.import_module(module_info.name)
        definitions.update(
            value
            for value in vars(module).values()
            if inspect.isclass(value)
            and issubclass(value, LibraryComponent)
            and value is not LibraryComponent
            and value.__module__ == module.__name__
        )

    return frozenset(definitions)


def test_every_production_component_template_is_alpine_csp_compatible() -> None:
    """Keep public and internally registered UI components safe for strict CSP."""
    discovered = _production_component_definitions()
    declared = frozenset(COMPONENTS)

    assert discovered == declared, (
        "Every production LibraryComponent must be in the Citry UI manifest so "
        "the CSP compatibility check covers it. "
        f"Missing from manifest: {sorted(item.__name__ for item in discovered - declared)!r}; "
        f"missing from discovery: {sorted(item.__name__ for item in declared - discovered)!r}"
    )

    engine = Citry(autodiscover=False, security_csp="strict")
    installation = engine.register_library(citry_ui)
    assert frozenset(installation.definitions) == discovered

    report = check_project(
        CheckAppSelection(spec="citry-ui-csp-ci", engine=engine),
        Path.cwd(),
    )
    assert report.app_failure is None
    findings = [finding for finding in report.findings if finding.code == CSP_INCOMPATIBLE_BROWSER_CODE]
    details = "\n".join(f"- {finding.origin}: {finding.message}" for finding in findings)

    assert findings == [], f"Citry UI production templates must support Alpine's CSP build:\n{details}"
