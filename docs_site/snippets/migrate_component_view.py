"""Executable Citry examples for the Component.View migration guide."""

from __future__ import annotations

from typing import Any

from citry import Citry, Component
from citry.ext.events import ViewEvents, actions, event

citry_app = Citry(secret="docs-only-test-secret")  # noqa: S106 - executable docs fixture
citry_app.set_mounted_prefix("/citry")


# --8<-- [start:view-events]
class ThankYouMessage(Component):
    citry = citry_app

    class Kwargs:
        name: str

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        return {"name": kwargs.name}

    template = """
      <p id="thank-you">
        Thank you, {{ name }}!
      </p>
    """


class ContactIn:
    name: str = "stranger"


class ContactForm(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    class Events(ViewEvents):
        def post(self, data: ContactIn):
            return actions.Render(
                ThankYouMessage(name=data.name),
                target="#result",
                swap="inner",
            )

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        submit_url = self.citry.build_url(f"ext/events/e/{type(self).class_id}")
        return {"submit_url": submit_url}

    template = """
      <form method="post" c-action="submit_url">
        <input name="name">
        <button type="submit">Send</button>
      </form>
      <div id="result"></div>
    """


# --8<-- [end:view-events]


# --8<-- [start:named-event]
class NamedContactForm(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    class Events:
        def submit(self, data: ContactIn):
            return actions.Render(
                ThankYouMessage(name=data.name),
                target="#result",
                swap="inner",
            )

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        return {"submit_url": self.events.url("submit")}

    template = """
      <form
        method="post"
        c-action="submit_url"
        @c-submit.prevent="submit"
      >
        <input name="name">
        <button type="submit">Send</button>
      </form>
      <div id="result"></div>
    """


# --8<-- [end:named-event]


# --8<-- [start:named-fragments]
class LoadedFragment(Component):
    citry = citry_app

    class Kwargs:
        kind: str

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        return {"kind": kwargs.kind}

    template = """
      <section class="loaded-fragment">
        Loaded {{ kind }}
      </section>
    """


class FragmentLoader(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    class Events:
        @event(methods=("GET",))
        def preview(self):
            return actions.Render(
                LoadedFragment(kind="preview"),
                target="#fragment-target",
                swap="inner",
            )

        @event(methods=("GET",))
        def details(self):
            return actions.Render(
                LoadedFragment(kind="details"),
                target="#fragment-target",
                swap="inner",
            )

    template = """
      <nav>
        <button @c-click="preview">Preview</button>
        <button @c-click="details">Details</button>
      </nav>
      <div id="fragment-target"></div>
    """


# --8<-- [end:named-fragments]
