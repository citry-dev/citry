"""Executable Citry examples for the django-unicorn migration guide."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from citry import Citry, Component
from citry.ext.events import EventError, actions

citry_app = Citry(secret="docs-only-test-secret")  # noqa: S106 - executable docs fixture
citry_app.set_mounted_prefix("/citry")


@dataclass(frozen=True, slots=True)
class Product:
    name: str


def find_products(query: str) -> list[Product]:
    """Return deterministic products for the executable guide fixture."""
    return [Product(name=f"{query} shoes")]


# --8<-- [start:live-search]
class LiveSearch(Component):
    citry = citry_app

    class Kwargs:
        query: str = ""

    class State(Kwargs):
        pass

    class Events:
        def refresh(self, state):
            return LiveSearch(query=state.query)

    def template_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> dict[str, Any]:
        results = find_products(kwargs.query) if kwargs.query else []
        return {"results": results}

    template = """
      <div>
        <input
          type="search"
          :c-query.debounce.300ms="refresh"
        >
        <ul>
          <c-for each="item in results">
            <li>{{ item.name }}</li>
          </c-for>
        </ul>
      </div>
    """


# --8<-- [end:live-search]


# --8<-- [start:rating]
class RatingIn:
    stars: int


class Rating(Component):
    citry = citry_app

    class Kwargs:
        value: int = 0

    class Events:
        def rate(self, data: RatingIn):
            save_rating(data.stars)
            return Rating(value=data.stars)

    def template_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> dict[str, Any]:
        return {"value": kwargs.value}

    template = """
      <button @c-click="rate({ stars: 5 })">Five stars</button>
      <button @c-click="rate({ stars: 0 })">Clear</button>
      <output>{{ value }}</output>
    """


# --8<-- [end:rating]


# --8<-- [start:validation]
class ContactIn:
    email: str = ""


class ContactForm(Component):
    citry = citry_app

    class Events:
        def submit(self, data: ContactIn):
            if "@" not in data.email:
                raise EventError(
                    "Please fix the errors.",
                    fields={"email": "Enter a valid email address."},
                )
            return ContactForm()

    template = """
      <form @c-submit.prevent="submit">
        <input name="email">
        <span x-text="$error('save')?.fieldErrors.email"></span>
        <button type="submit">Send</button>
      </form>
    """


# --8<-- [end:validation]


# --8<-- [start:browser-event]
class Preferences(Component):
    citry = citry_app

    class Events:
        def save(self):
            save_preferences()
            return actions.Dispatch(
                "Preferences:saved",
                {"message": "Preferences saved"},
            )

    template = """
      <button @c-click="save">Save</button>
    """


# --8<-- [end:browser-event]


def save_preferences() -> None:
    """Stand-in side effect for the executable guide fixture."""


def save_rating(stars: int) -> None:
    """Stand-in side effect for the executable guide fixture."""
