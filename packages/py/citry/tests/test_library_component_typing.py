"""Static authoring contract for engine-neutral library definitions."""

from typing import Any

from citry import LibraryComponent


class CTypedNotice(LibraryComponent):
    """Exercise APIs inherited from Component only for static authoring."""

    template = "{{ value }}"

    def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
        self.provide("typed-notice", value=kwargs)
        return {"value": self.inject("typed-notice")}


def test_library_definition_remains_inert() -> None:
    assert CTypedNotice.template == "{{ value }}"
