"""Static authoring contract for engine-neutral library definitions."""

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from typing_extensions import assert_type

from citry import CacheConfig, Citry, Component, DependenciesConfig, I18n, LibraryComponent, Slot
from citry import Events as EventsBase

if TYPE_CHECKING:
    assert_type(LibraryComponent.class_id, str)
    assert_type(LibraryComponent.definition_id, str)
    assert_type(LibraryComponent.citry, Citry)
    assert_type(LibraryComponent.transparent, bool)
    assert_type(LibraryComponent.name, str | None)
    assert_type(LibraryComponent.template, str | None)
    assert_type(LibraryComponent.template_file, str | None)
    assert_type(LibraryComponent.messages, str | None)
    assert_type(LibraryComponent.messages_file, str | None)
    assert_type(LibraryComponent.js, str | None)
    assert_type(LibraryComponent.js_file, str | None)
    assert_type(LibraryComponent.css, str | None)
    assert_type(LibraryComponent.css_file, str | None)
    assert_type(LibraryComponent.Cache, type | None)
    assert_type(LibraryComponent.Dependencies, type | None)
    assert_type(LibraryComponent.I18n, type | None)
    assert_type(LibraryComponent.Kwargs, type | None)
    assert_type(LibraryComponent.Slots, type | None)
    assert_type(LibraryComponent.State, type | None)
    assert_type(LibraryComponent.Events, type | None)
    assert_type(LibraryComponent.Lint, type | None)
    assert_type(LibraryComponent.TemplateData, type | None)
    assert_type(LibraryComponent.JsData, type | None)
    assert_type(LibraryComponent.CssData, type | None)


def _assert_materialized_authoring_types(component: LibraryComponent) -> None:
    assert_type(component.id, str)
    assert_type(component.kwargs, Any)
    assert_type(component.raw_kwargs, dict[str, Any])
    assert_type(component.slots, Any)
    assert_type(component.raw_slots, dict[str, Slot])
    assert_type(component.cache, CacheConfig)
    assert_type(component.dependencies, DependenciesConfig)
    assert_type(component.events, EventsBase[Any])
    assert_type(component.i18n, I18n)
    assert_type(component.parent, Component | None)
    assert_type(component.root, Component)
    assert_type(component.ancestors, Iterator[Component])


class CTypedNotice(LibraryComponent):
    """Exercise APIs inherited from Component only for static authoring."""

    template = "{{ value }}"

    def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
        self.provide("typed-notice", value=kwargs)
        return {"value": self.inject("typed-notice")}


def test_library_definition_remains_inert() -> None:
    assert CTypedNotice.template == "{{ value }}"
