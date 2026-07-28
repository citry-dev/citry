"""Verify inherited schemas and extension declarations for a LibraryComponent experiment."""

from __future__ import annotations

import json
import sys
from dataclasses import is_dataclass
from typing import Any

from citry import Citry, Component, Events


class LibraryDefinition:
    """Minimal inert definition shaped like the proposed LibraryComponent."""

    class Kwargs:
        label: str

    class Slots:
        default: object

    class Events(Events):
        def activate(self) -> None:
            return None

    class Dependencies:
        js = "/library-component-probe.js"

    def helper(self) -> str:
        return "definition"

    def template_data(self, kwargs: Kwargs, slots: Any) -> dict[str, Any]:  # noqa: ARG002
        return {"value": f"{super().helper()}:{kwargs.label}"}


class HelperBase:
    """Prove that multiple inheritance preserves zero-argument super()."""

    def helper(self) -> str:
        return "helper"


def run_probe() -> dict[str, object]:
    """Create one concrete class and report the declaration-normalization result."""
    app = Citry(autodiscover=False)

    class Bound(LibraryDefinition, HelperBase, Component):
        citry = app
        name = "LibraryComponentProbe"
        template = """
          <p>{{ value }}</p>
        """

    render_error: str | None = None
    try:
        str(Bound(label="probe", slots={"default": "body"}))
    except TypeError as error:
        render_error = str(error).splitlines()[1]

    result: dict[str, object] = {
        "dependencies_inherited": Bound.get_dependencies().js == ("/library-component-probe.js",),
        "events_derived": Bound.Events is not LibraryDefinition.Events,
        "kwargs_dataclass": is_dataclass(Bound.Kwargs),
        "mro": [item.__name__ for item in Bound.__mro__],
        "render_error": render_error,
        "slots_dataclass": is_dataclass(Bound.Slots),
    }
    expected = {
        "dependencies_inherited": True,
        "kwargs_dataclass": True,
        "slots_dataclass": True,
        "render_error": None,
    }
    mismatches = {key: (result[key], value) for key, value in expected.items() if result[key] != value}
    if mismatches:
        msg = f"LibraryComponent declaration probe regressed: {mismatches!r}"
        raise RuntimeError(msg)
    return result


if __name__ == "__main__":
    sys.stdout.write(json.dumps(run_probe(), indent=2, sort_keys=True) + "\n")
