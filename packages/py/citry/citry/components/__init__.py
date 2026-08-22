"""
Built-in components.

These are ordinary citry components that ship with the engine and back the
built-in tags the README promises: ``<c-provide>``, ``<c-cache>``,
``<c-component>``, ``<c-element>``, ``<c-error-fallback>``, ``<c-js>``, and
``<c-css>``, ``<c-i18n>``, and ``<c-trans>``. The parser treats these tags as regular component tags on purpose (see
``crates/citry_template_parser/src/constants.rs``), so the whole behavior
lives in Python.

The private registry uses ``BUILTIN_COMPONENT_NAMES`` to reserve their names
and rejects user components that claim one of them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from citry.components.dynamic import make_dynamic_component, make_dynamic_element
from citry.components.error_fallback import make_error_fallback_component
from citry.components.js_css import make_css_component, make_js_component
from citry.components.provide import make_provide_component
from citry.ext.cache.components import make_cache_component
from citry.ext.i18n.components import make_i18n_component, make_trans_component

if TYPE_CHECKING:
    from citry.citry import Citry
    from citry.component import Component


def make_template_root_component(citry_instance: Citry) -> type[Component]:
    """Create the private transparent root used by ``Citry.render_template``."""
    from citry.component import Component  # noqa: PLC0415

    class TemplateRoot(
        Component,
        _citry_internal=citry_instance._registry._builtin_registration_token,
    ):
        citry = citry_instance
        transparent = True

    return TemplateRoot


def make_builtin_components(citry_instance: Citry) -> None:
    """Create and register the built-in components for one Citry instance."""
    make_provide_component(citry_instance)
    make_cache_component(citry_instance)
    make_dynamic_component(citry_instance)
    make_dynamic_element(citry_instance)
    make_error_fallback_component(citry_instance)
    make_js_component(citry_instance)
    make_css_component(citry_instance)
    make_i18n_component(citry_instance)
    make_trans_component(citry_instance)
    citry_instance._template_root_class = make_template_root_component(citry_instance)
