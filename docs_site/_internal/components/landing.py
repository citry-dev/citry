"""Citry-owned components for the project landing page."""

from __future__ import annotations

import base64
import functools
import importlib
import json
import re
from typing import TYPE_CHECKING, Any

from markupsafe import Markup, escape
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name

from citry import Component
from docs_site._internal.project import current_docs_project
from docs_site._internal.util import flatten_for_markdown
from docs_site.snippets.landing.status_card import StatusCard

if TYPE_CHECKING:
    from collections.abc import Callable

# The walkthrough reads this file and marks the line ranges below. Line numbers
# are the one fragile part, so `test_walkthrough_stops_point_at_the_right_lines`
# checks that each range still contains the text it claims to explain.
_TOUR_PATH = "docs_site/snippets/landing/product_card.py"

# A stop's ``text`` is markup, not plain prose: naming an attribute or a method
# reads better as code than in quotes, and the note is rendered as HTML.
_TOUR_STOPS: tuple[dict[str, Any], ...] = (
    {
        "id": "kwargs",
        "label": "Inputs",
        "lines": (4, 7),
        "anchor": "class Kwargs",
        "title": "Declared inputs",
        "text": (
            "Every input this component accepts, with its type and any default. "
            "Passing an unknown name, or leaving out a required one, is reported "
            "when the component renders rather than quietly producing a gap in "
            "the page."
        ),
    },
    {
        "id": "slots",
        "label": "Slots",
        "lines": (9, 11),
        "anchor": "class Slots",
        "title": "Openings the caller fills",
        "text": (
            "Named places a caller passes markup into. <code>body</code> is "
            "required and <code>footer</code> is optional, so the contract covers "
            "content as well as data."
        ),
    },
    {
        "id": "state",
        "label": "State",
        "lines": (13, 14),
        "anchor": "class State",
        "title": "State that survives a call",
        "text": (
            "Server-side state available across Python event handler calls. "
            "Travels between the server and the browser. "
            "Inheriting <code>Kwargs</code> makes the <code>State</code> "
            "carry the same fields."
        ),
    },
    {
        "id": "events",
        "label": "Events",
        "lines": (16, 21),
        "anchor": "class Events",
        "title": "Python that runs on interaction",
        "text": (
            "A public method here can be called from the browser "
            'using <code>@c-event="like"</code>. <code>like</code> '
            "reads the current state and renders the updated component, "
            "which the browser then displays."
        ),
    },
    {
        "id": "data",
        "label": "Data",
        "lines": (23, 33),
        "anchor": "def template_data",
        "title": "Use Python variables in templates, JS, and CSS",
        "text": (
            "<code>template_data</code> prepares template variables, "
            "<code>js_data</code> sends data to JS script as JSON, and "
            "<code>css_data</code> creates CSS variables scoped to this "
            "one instance."
        ),
    },
    {
        "id": "alpine",
        "label": "Browser state",
        "lines": (36, 39),
        "anchor": "x-data",
        "title": "State that never leaves the page",
        "text": (
            "<code>x-data</code> holds what only the browser cares about. Opening "
            "and closing the card needs no server, so it never asks one."
        ),
    },
    {
        "id": "slot-body",
        "label": "Slot",
        "lines": (40, 40),
        "anchor": '<c-slot name="body"',
        "title": "Where filled content lands",
        "text": (
            "<code>&lt;c-slot&gt;</code> marks the spot the caller's content drops "
            "into, inside markup this component still controls."
        ),
    },
    {
        "id": "control",
        "label": "Control flow",
        "lines": (42, 51),
        "anchor": "c-for",
        "title": "A loop, a child, and the empty case",
        "text": (
            "<code>&lt;c-for&gt;</code> repeats a child component, "
            "while <code>&lt;c-empty&gt;</code> runs when there are no tags at all. "
            "The child component <code>&lt;c-Tag&gt;</code> receives "
            "<code>label</code> as Python value, and <code>highlight</code> "
            "as Alpine (browser) value through <code>$c-props</code>. "
            "You can listen to children's Alpine events with regular <code>@click</code>."
        ),
    },
    {
        "id": "handlers",
        "label": "Bindings",
        "lines": (53, 55),
        "anchor": "@c-click",
        "title": "Alpine and Python, side by side",
        "text": (
            "<code>@click</code> stays in the browser for instant feedback, while "
            "<code>@c-click</code> calls the Python handler set in the value, <code>like</code>."
        ),
    },
    {
        "id": "slot-footer",
        "label": "Fallback",
        "lines": (57, 59),
        "anchor": '<c-slot name="footer"',
        "title": "What shows when nobody fills it",
        "text": (
            "Content between the tags is the fallback for an optional slot, so a "
            "caller who skips it still gets something sensible."
        ),
    },
    {
        "id": "js",
        "label": "Script",
        "lines": (63, 68),
        "anchor": "$component",
        "title": "A script scoped to this component",
        "text": (
            "<code>$component</code> receives this instance's elements and whatever "
            "<code>js_data</code> returned, so the script never has to find its own "
            "component with a selector."
        ),
    },
    {
        "id": "css",
        "label": "Style",
        "lines": (70, 78),
        "anchor": "var(--accent)",
        "title": "Styles reading Python values",
        "text": (
            "<code>var(--accent)</code> reads the custom property "
            "<code>css_data</code> produced, and it is scoped to this instance, so "
            "two cards on one page can differ without a second stylesheet."
        ),
    },
    {
        "id": "deps",
        "label": "Assets",
        "lines": (80, 82),
        "anchor": "class Dependencies",
        "title": "Third-party scripts and styles",
        "text": (
            "Libraries this component needs. Citry loads each script only once per page, "
            "however many components may use it."
        ),
    },
    {
        "id": "render",
        "label": "Render",
        "lines": (85, 88),
        "anchor": "str(ProductCard",
        "title": "Rendering is a function call",
        "text": (
            "Rendering returns ordinary HTML. This makes components "
            "easy to integrate with web frameworks, or test with plain Python."
        ),
    },
)


# One mounting example per supported host. Each names the adapter it calls, and
# `_check_host_entrypoints` confirms that callable still exists at build time, so
# a renamed adapter fails the page instead of publishing a dead instruction.
_HOST_CASES: tuple[dict[str, Any], ...] = (
    {
        "id": "fastapi",
        "label": "FastAPI",
        "blurb": "Also Starlette",
        "file": "main.py",
        "entrypoint": ("citry.contrib.fastapi", "mount"),
        "code": (
            "from contextlib import asynccontextmanager\n"
            "\n"
            "from fastapi import FastAPI\n"
            "\n"
            "from citry import citry\n"
            "from citry.contrib.fastapi import mount\n"
            "\n"
            "\n"
            "@asynccontextmanager\n"
            "async def lifespan(_app: FastAPI):\n"
            "    citry.initialize()\n"
            "    yield\n"
            "\n"
            "\n"
            "app = FastAPI(lifespan=lifespan)\n"
            "mount(app, citry)"
        ),
    },
    {
        "id": "flask",
        "label": "Flask",
        "blurb": "The same call shape",
        "file": "app.py",
        "entrypoint": ("citry.contrib.flask", "mount"),
        "code": (
            "from flask import Flask\n"
            "\n"
            "from citry import citry\n"
            "from citry.contrib.flask import mount\n"
            "\n"
            "app = Flask(__name__)\n"
            'mount(app, citry, prefix="/citry")\n'
            "citry.initialize()"
        ),
    },
    {
        "id": "django",
        "label": "Django",
        "blurb": "Added to your URL conf",
        "file": "urls.py",
        "entrypoint": ("citry.contrib.django", "urlpatterns"),
        "code": (
            "from django.urls import path\n"
            "\n"
            "from citry import citry\n"
            "from citry.contrib.django import urlpatterns as citry_urls\n"
            "\n"
            "urlpatterns = [\n"
            '    path("", home_view),\n'
            '    *citry_urls(citry, prefix="/citry"),\n'
            "]"
        ),
    },
    {
        "id": "asgi",
        "label": "Bare ASGI",
        "blurb": "No framework required",
        "file": "asgi.py",
        "entrypoint": ("citry.contrib.asgi", "asgi_app"),
        "code": (
            "from citry import citry\n"
            "from citry.contrib.asgi import asgi_app\n"
            "\n"
            "citry.initialize()\n"
            "app = asgi_app(citry)"
        ),
    },
    {
        "id": "wsgi",
        "label": "Bare WSGI",
        "blurb": "For synchronous stacks",
        "file": "wsgi.py",
        "entrypoint": ("citry.contrib.wsgi", "wsgi_app"),
        "code": (
            "from citry import citry\n"
            "from citry.contrib.wsgi import wsgi_app\n"
            "\n"
            "citry.initialize()\n"
            "application = wsgi_app(citry)"
        ),
    },
)


# One answer per problem a product runs into once it is carrying real traffic,
# real rules, and more than one team. Each names the page that documents it,
# and `_check_depth_docs` confirms that page still exists at build time.
_DEPTH_CASES: tuple[dict[str, Any], ...] = (
    {
        "id": "cache",
        "label": "Caching",
        "blurb": "The same subtree, rebuilt on every request",
        "note": Markup(
            '<div class="landing-picker__note">'
            "<p>Two scopes, one backend. <code>Component.Cache</code> caches every call to a component class, while <code>&lt;c-cache&gt;</code> caches one named region inside a template, adding no wrapper element of its own.</p>"
            "<p>A miss always renders normally. Cache hit behaves the same in both the browser and server. <code>version</code> retires old entries on deploy.</p>"
            "</div>",
        ),
        "file": "product_card.py",
        "doc": "advanced/caching.md",
        "code": (
            "class ProductCard(Component):\n"
            "    class Kwargs:\n"
            "        product_id: int\n"
            "\n"
            "    class Slots:\n"
            "        pass\n"
            "\n"
            "    # Cache every time this component is called\n"
            "    class Cache:\n"
            "        enabled = True\n"
            "        ttl = 300\n"
            "        version = 1\n"
            "\n"
            '    template = """\n'
            "      <div>\n"
            "        {# Cache only this region #}\n"
            '        <c-cache key="expensive">\n'
            "          <c-ExpensiveUI />\n"
            "        </c-cache>\n"
            "      </div>\n"
            '    """\n'
        ),
    },
    {
        "id": "const",
        "label": "Const optimization",
        "blurb": "Don't re-render markup that never varies",
        "note": Markup(
            '<div class="landing-picker__note">'
            "<p>Most of a template does not change between renders. <code>Const</code> marks an input as fixed, so the markup that depends on it is rendered once and reused.</p>"
            "<p>A <code>Const</code> value works like the value it wraps in ordinary template expressions. Marking one is a promise that it will not change between renders.</p>"
            "</div>",
        ),
        "file": "dashboard.py",
        "doc": "advanced/const-optimization.md",
        "code": (
            "from citry import Const\n\n# The parts that never vary are rendered once and reused\nCard(cols=Const(3))"
        ),
    },
    {
        "id": "extensions",
        "label": "Extensions",
        "blurb": "Verify, modify, or extend all components at once",
        "note": Markup(
            '<div class="landing-picker__note">'
            "<p>An extension installs on a <code>Citry</code> instance and sees every component through it, so a rule holds without editing each component or remembering to call anything.</p>"
            "<p>Hooks cover the render lifecycle, components' JS and CSS scripts, and more. An extension can also carry per-component config, store state for the duration of a render, and add its own URL endpoints and CLI commands.</p>"
            "</div>",
        ),
        "file": "timing.py",
        "doc": "advanced/extensions.md",
        "code": (
            "from citry import Citry, Extension\n"
            "\n"
            "\n"
            "class TimingExtension(Extension):\n"
            '    name = "timing"\n'
            "\n"
            "    def on_component_rendered(self, ctx):\n"
            "        record(type(ctx.component).__name__)\n"
            "        return None  # keep the original render\n"
            "\n"
            "\n"
            "app = Citry(extensions=[TimingExtension])"
        ),
    },
    {
        "id": "fragments",
        "label": "HTML fragments",
        "blurb": "Partial page updates. Works with HTMX.",
        "note": Markup(
            '<div class="landing-picker__note">'
            "<p>Easily integrate with HTMX. Instead of rendering a full page, render only small HTML to update one region.</p>"
            "<p>Fragments carry their own JS and CSS. Citry loads whatever that region needs. Duplicate assets are never loaded twice.</p>"
            "</div>",
        ),
        "file": "views.py",
        "doc": "advanced/html-fragments.md",
        "code": (
            'card = Card(title="Welcome")\n'
            "\n"
            "# The browser gets the markup and whatever JS and CSS it still needs\n"
            'card.render().serialize(deps_strategy="fragment")'
        ),
    },
    {
        "id": "libraries",
        "label": "Component libraries",
        "blurb": "Share and publish components across projects",
        "note": Markup(
            '<div class="landing-picker__note">'
            "<p>Share components across different projects as component libraries with <code>LibraryComponent</code>. An application installs the package's manifest into the <code>Citry</code> instance that should have it.</p>"
            "<p>Ideal for design systems or publishing to registries.</p>"
            "</div>",
        ),
        "file": "acme_ui/badge.py",
        "doc": "advanced/component-libraries.md",
        "code": (
            "from citry import (\n"
            "    ComponentLibrary,\n"
            "    LibraryComponent,\n"
            "    SlotInput,\n"
            "    citry,\n"
            ")\n"
            "\n"
            "# Define library components\n"
            "class AcmeBadge(LibraryComponent):\n"
            "    class Kwargs:\n"
            '        tone: str = "neutral"\n'
            "\n"
            "    class Slots:\n"
            "        default: SlotInput | None = None"
            "\n"
            "\n"
            "# Create Library\n"
            "acme_library = ComponentLibrary(\n"
            '    name="acme",\n'
            "    components=[AcmeBadge],\n"
            ")\n"
            "\n"
            "# Register library with Citry\n"
            "citry.register_library(acme_library)"
        ),
    },
)


def _check_depth_docs() -> None:
    """Fail the build when a promoted capability lost the page that explains it."""
    for case in _DEPTH_CASES:
        page = current_docs_project().runtime.content_dir / case["doc"]
        if not page.is_file():
            message = f"Landing page promotes {case['label']!r}, but {case['doc']} is gone."
            raise RuntimeError(message)


def _check_host_entrypoints() -> None:
    """Fail the build when a host example names an adapter that moved."""
    for case in _HOST_CASES:
        module_name, attribute = case["entrypoint"]
        module = importlib.import_module(module_name)
        if not hasattr(module, attribute):
            message = f"Landing page names {module_name}.{attribute}, which no longer exists."
            raise RuntimeError(message)


def _as_markdown_block(html: str) -> Markup:
    """Wrap generated markup so the markdown pass leaves it alone."""
    return Markup(f"\n\n{flatten_for_markdown(html)}\n\n")  # noqa: S704 - generated in this module


class LandingPickerMarkup(Component):
    """
    A list of rows beside one panel each: the page's shared picker.

    Every panel ships in the HTML, so a reader without JavaScript gets all of
    them. Each case supplies a highlighted snippet, and ``extra`` adds anything
    that belongs under it, which is how the reliability section puts a real
    error message beneath its code.
    """

    transparent = True

    class Kwargs:
        cases: list

    class Slots:
        pass

    template = """
      <div class="landing-picker" data-landing-picker>
        <div
          c-for="case in cases"
          class="landing-picker__item"
        >
        <button
          class="landing-picker__row"
          type="button"
          c-data-picker-case="case['id']"
          c-aria-pressed="'true' if case['first'] else 'false'"
          c-class="{
            'landing-picker__row': True,
            'is-active': case['first'],
          }"
        >
          <span class="landing-picker__number">
            {{ case['number'] }}
          </span>
          <span>
            <strong>{{ case['label'] }}</strong>
            <br><span class="landing-picker__blurb">
              {{ case['blurb'] }}
            </span>
          </span>
          <svg
            class="landing-picker__caret"
            viewBox="0 0 16 16"
            aria-hidden="true"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M4 6l4 4 4-4"/>
          </svg>
        </button>
        <div
          class="landing-picker__panel"
          c-data-picker-panel="case['id']"
        >
          {{ case['note'] }}
          <div class="landing-code landing-picker__code">
            <div class="landing-code__bar">
              <span class="landing-code__dot"></span>
              <span>{{ case['file'] }}</span>
            </div>
            {{ case['code'] }}
          </div>
          {{ case['extra'] }}
        </div>
        </div>
      </div>
    """


def _picker_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Number the rows and mark the one that opens first."""
    return [
        {
            **case,
            "number": f"{number:02d}",
            "first": number == 1,
            "note": case.get("note", Markup("")),
            "extra": case.get("extra", Markup("")),
        }
        for number, case in enumerate(cases, start=1)
    ]


class LandingHostsMarkup(Component):
    """One mounting example per host, switched by the list beside it."""

    transparent = True

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        _check_host_entrypoints()
        return {
            "picker": Markup(  # noqa: S704 - markup from this module
                str(
                    LandingPickerMarkup(
                        cases=_picker_cases(
                            [
                                {
                                    "id": case["id"],
                                    "label": case["label"],
                                    "blurb": case["blurb"],
                                    "file": case["file"],
                                    "code": Markup(_highlight(case["code"])),  # noqa: S704
                                }
                                for case in _HOST_CASES
                            ],
                        ),
                    ),
                ),
            ),
        }

    template = """
      {{ picker }}
    """


class LandingDepthMarkup(Component):
    """The capabilities a team reaches for after the first version ships."""

    transparent = True

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        _check_depth_docs()
        return {
            "picker": Markup(  # noqa: S704 - markup from this module
                str(
                    LandingPickerMarkup(
                        cases=_picker_cases(
                            [
                                {
                                    "id": case["id"],
                                    "label": case["label"],
                                    "blurb": case["blurb"],
                                    "file": case["file"],
                                    "note": case["note"],
                                    "code": Markup(_highlight(case["code"])),  # noqa: S704
                                }
                                for case in _DEPTH_CASES
                            ],
                        ),
                    ),
                ),
            ),
        }

    template = """
      {{ picker }}
    """


class LandingDepth(Component):
    """Place the advanced-capability picker into the page."""

    transparent = True

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {"depth": _as_markdown_block(str(LandingDepthMarkup()))}

    template = """
      {{ depth }}
    """


class LandingHosts(Component):
    """Place the host examples into the page, flushed left for the markdown pass."""

    transparent = True

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        markup = _as_markdown_block(str(LandingHostsMarkup()))
        return {"hosts": markup}

    template = """
      {{ hosts }}
    """


class LandingTourMarkup(Component):
    """The annotated walkthrough: one component's source beside its explanations."""

    transparent = True

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        source = (current_docs_project().runtime.repo_root / _TOUR_PATH).read_text(encoding="utf-8")
        return {
            "file_name": _TOUR_PATH.rsplit("/", 1)[-1],
            "code": Markup(_tour_code(source, _TOUR_STOPS)),  # noqa: S704 - pygments output
            # Each line is its own block so a highlight can span the full width,
            # which means the rendered text carries no newline characters. The
            # copy button reads the original source from here instead. It is
            # encoded because the markup this component emits passes through
            # whitespace handling that would otherwise rewrite the blank lines.
            "source": base64.b64encode(source.encode()).decode(),
            # A note names attributes and methods, which read better as code than
            # in quotes, so its text is markup written in this module.
            "stops": [
                {**stop, "text": Markup(stop["text"])}  # noqa: S704 - written above, not user input
                for stop in _TOUR_STOPS
            ],
        }

    template = """
      <div class="landing-tour" data-landing-tour c-data-tour-source="source">
        <div class="landing-code landing-tour__code">
          <div class="landing-code__bar">
            <span class="landing-code__dot"></span>
            <span>{{ file_name }}</span>
          </div>
          {{ code }}
        </div>
        <div class="landing-tour__notes">
          <p class="landing-tour__hint" data-tour-hint>
            Point at a marked line to see what it does.
          </p>
          <div
            c-for="stop in stops"
            class="landing-tour__note"
            c-data-tour-note="stop['id']"
          >
            <span class="landing-tour__note-label">{{ stop['label'] }}</span>
            <strong>{{ stop['title'] }}</strong>
            <p>{{ stop['text'] }}</p>
          </div>
        </div>
      </div>
    """


class LandingTour(Component):
    """
    Place the annotated walkthrough into the page, flushed left.

    Every note is server-rendered, so a reader without JavaScript gets the whole
    explanation as a list under the code. The script then shows one note at a
    time as the reader moves across the source.
    """

    transparent = True

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        markup = _as_markdown_block(str(LandingTourMarkup()))
        return {"tour": markup}

    template = """
      {{ tour }}
    """


class LandingDiagnosticMarkup(Component):
    """
    Every captured error, its snippet, and the row that selects it.

    The rows and the panels come from one list, so the page cannot name a case
    it does not show. Each panel carries the real message under its code.
    """

    transparent = True

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        cases = []
        for case in json.loads(_render_diagnostics()):
            message = (
                '<div class="landing-diagnostic">'
                f'<p class="landing-diagnostic__mutation"><span>{escape(case["blurb"])}</span></p>'
                f'<span class="landing-diagnostic__type">{escape(case["type"])}</span>'
                f"<pre>{escape(case['message'])}</pre>"
                "</div>"
            )
            cases.append(
                {
                    "id": case["id"],
                    "label": case["label"],
                    "blurb": case["blurb"],
                    "file": f"{case['id']}.py",
                    "code": Markup(case["code"]),  # noqa: S704 - pygments output
                    "extra": Markup(message),  # noqa: S704 - escaped above
                },
            )
        return {
            "picker": Markup(str(LandingPickerMarkup(cases=_picker_cases(cases)))),  # noqa: S704
        }

    template = """
      {{ picker }}
    """


class LandingDiagnostic(Component):
    """
    Place every captured error into the page, server-rendered.

    The panels are flushed left because they land inside a markdown block:
    indented HTML there is read as a code block and printed as source instead
    of rendered. Each error message sits in a ``<pre>``, so the carets Citry
    draws under the offending token keep their columns.
    """

    transparent = True

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        panel = _as_markdown_block(str(LandingDiagnosticMarkup()))
        return {"panel": panel}

    template = """
      {{ panel }}
    """


# Each case is one mistake a reader can recognise, paired with the smallest code
# that causes it. The build runs this exact source, so the snippet on the page
# and the message under it can never describe different things.
_ERROR_CASES: tuple[dict[str, Any], ...] = (
    {
        "id": "input",
        "label": "Missing input",
        "blurb": "Rejected as the component is called",
        "code": (
            "card = StatusCard(\n"
            "    complete=18,\n"
            "    total=25,\n"
            ")\n"
            "\n"
            "# Rendering is where the component's inputs are checked\n"
            "str(card)"
        ),
        "expected": TypeError,
        "contains": "missing 1 required positional argument: 'title'",
    },
    {
        "id": "misspelled",
        "label": "Misspelled input",
        "blurb": "Rejected, and the name you meant is offered",
        "code": ('card = StatusCard(\n    titel="Deploy preview",\n    complete=18,\n    total=25,\n)\n\nstr(card)'),
        "expected": TypeError,
        "contains": "Did you mean 'title'?",
    },
    {
        "id": "template",
        "label": "Unknown template value",
        "blurb": "Pointed at the line that asked for it",
        "code": (
            "class Greeting(Component):\n"
            "    class Kwargs:\n"
            "        name: str\n"
            "\n"
            "    def template_data(self, kwargs, slots):\n"
            '        return {"name": kwargs.name}\n'
            "\n"
            '    template = "<p>Hello, {{ naem }}!</p>"\n'
            "\n"
            'str(Greeting(name="Ada"))'
        ),
        "expected": KeyError,
        "contains": "naem",
    },
    {
        "id": "isolation",
        "label": "Data stays in its component",
        "blurb": "A child never inherits the parent's variables",
        "code": (
            "class Child(Component):\n"
            '    template = "<span>{{ user_name }}</span>"\n'
            "\n"
            "class Parent(Component):\n"
            "    def template_data(self, kwargs, slots):\n"
            '        return {"user_name": "Ada"}\n'
            "\n"
            '    template = "<div>{{ user_name }}<c-child /></div>"\n'
            "\n"
            "str(Parent())"
        ),
        "expected": KeyError,
        "contains": "user_name",
    },
    {
        "id": "unknown",
        "label": "Unknown component",
        "blurb": "Named at the tag that asked for it",
        "code": (
            "class Page(Component):\n"
            '    template = """\n'
            '      <c-StatusCrad title="Deploy preview" />\n'
            '    """\n'
            "\n"
            "str(Page())"
        ),
        "expected": Exception,
        "contains": "statuscrad",
    },
    {
        "id": "mismatched",
        "label": "Mismatched tags",
        "blurb": "The parser names the tag it expected to close",
        "code": ('class Broken(Component):\n    template = "<div><span>Deploy preview</div>"\n\nstr(Broken())'),
        "expected": SyntaxError,
        "contains": "Mismatched tags",
    },
    {
        "id": "unsafe",
        "label": "Unsafe expression",
        "blurb": "Template expressions cannot reach the interpreter",
        "code": (
            "class Danger(Component):\n    template = \"<i>{{ __import__('os').system('ls') }}</i>\"\n\nstr(Danger())"
        ),
        "expected": Exception,
        "contains": "unsafe",
    },
)


def _tour_code(source: str, stops: tuple[dict[str, Any], ...]) -> str:
    """
    Highlight the walkthrough source and tag each line with the stop it belongs to.

    Pygments' ``linespans`` wraps every rendered line in its own span, which is
    what makes this possible: a triple-quoted template is one token spanning
    many lines, so splitting the highlighted HTML by newline would cut tags in
    half. The line spans are added by the formatter, after tokenizing, so they
    always land between lines rather than inside a token.
    """
    html = highlight(source, get_lexer_by_name("citry"), HtmlFormatter(linespans="tourline"))
    line_to_stop: dict[int, tuple[str, bool]] = {}
    for stop in stops:
        first, last = stop["lines"]
        for number in range(first, last + 1):
            line_to_stop[number] = (stop["id"], number == first)

    def tag(match: re.Match[str]) -> str:
        number = int(match.group(1))
        found = line_to_stop.get(number)
        if found is None:
            # Every line becomes a block, marked or not, so the block layout is
            # what breaks lines. A mix of block and inline lines would run the
            # inline ones together once their newlines are gone.
            return f'<span id="tourline-{number}" class="landing-tour__line">'
        stop_id, is_first = found
        start = ' data-tour-start=""' if is_first else ""
        return f'<span id="tourline-{number}" class="landing-tour__line is-marked" data-tour="{stop_id}"{start}>'

    html = re.sub(r'<span id="tourline-(\d+)">', tag, html)
    # Pygments keeps each line's newline inside its span. A block-level line
    # already ends its own row, so the newline is dropped rather than moved:
    # left anywhere in the flow it renders as a second, empty row.
    return html.replace("\n</span>", "</span>")


def _clean(message: str) -> str:
    """
    Drop build-machine detail a reader cannot act on.

    A component defined inside one of these snippets has no source file, so the
    location Citry names for it points at the interpreter rather than anything
    the reader could open.
    """
    text = message.replace(str(current_docs_project().runtime.repo_root) + "/", "")
    # Citry names a component's location two ways: in parentheses after the
    # template's name, and inline for a parse error. Both point at the
    # interpreter for a class defined in one of these snippets.
    text = re.sub(r"\s*\((?:builtins|<string>)::[^)]+\)", "", text)
    return re.sub(r"(?:builtins|<string>)::", "", text)


def _highlight(code: str) -> str:
    """Colour one snippet with the same lexer the page's code blocks use."""
    return highlight(code, get_lexer_by_name("citry"), HtmlFormatter())


def _capture(render: Callable[[], object], expected: type[Exception], contains: str) -> tuple[str, str]:
    """
    Run a deliberately broken render and return the real error class and text.

    The page tells readers that a mistake which stops being reported fails this
    build, so checking that *something* raised is not enough: a different error,
    or the same error with its guidance dropped, would still publish a label
    that no longer matches the message. The build fails unless the expected
    error arrives carrying the words the page promises.
    """
    try:
        render()
    except expected as error:
        # KeyError stringifies as the repr of its argument, which would show the
        # message's newlines and carets as literal escapes. Read the text itself.
        text = error.args[0] if isinstance(error, KeyError) and error.args else str(error)
        text = str(text)
        if contains not in text:
            message = (
                f"Landing page diagnostic lost its detail: expected {contains!r} "
                f"in the {expected.__name__} Citry raised, got:\n{text}"
            )
            raise RuntimeError(message) from error
        return type(error).__name__, text
    message = (
        f"Landing page diagnostic no longer raises {expected.__name__}; the reliability claim on the page is stale."
    )
    raise RuntimeError(message)


@functools.cache
def _render_diagnostics() -> str:
    """Run every listed mistake and collect the error Citry raised for it."""
    captured = []
    for case in _ERROR_CASES:
        code = case["code"]
        # The snippet is a constant written above, and running it is the whole
        # point: the reader is looking at the source that produced the message.
        namespace: dict[str, Any] = {"Component": Component, "StatusCard": StatusCard}
        error_type, message = _capture(
            lambda code=code, namespace=namespace: exec(code, namespace),  # noqa: S102
            case["expected"],
            case["contains"],
        )
        captured.append(
            {
                "id": case["id"],
                "label": case["label"],
                "blurb": case["blurb"],
                "code": _highlight(code),
                "type": error_type,
                # A build machine's checkout path is not useful to a reader, and
                # a snippet defined here has no file of its own to point at.
                "message": _clean(message),
            },
        )
    return json.dumps(captured, separators=(",", ":"))


class LandingPage(Component):
    """Purpose-built landing layout with a component-generated canvas field."""

    class Kwargs:
        content_html: Any
        searchable: bool = True
        pagefind_weight: Any = None
        repo_url: str = ""

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "content_html": kwargs.content_html,
            "searchable": kwargs.searchable,
            "pagefind_weight": kwargs.pagefind_weight,
            "repo_url": kwargs.repo_url,
        }

    template = """
      <div class="landing-shell" data-landing-root>
        <a class="landing-skip" href="#landing-main">Skip to content</a>
        <main id="landing-main" class="landing-main">
          <article
            class="landing-content"
            c-data-pagefind-body="searchable"
            c-data-pagefind-weight="pagefind_weight"
          >
            {{ content_html }}
          </article>
        </main>
        <footer class="landing-footer">
          <span>Citry is free and open source under the
          <a href="/community/license/">MIT license</a>.</span>
          <span class="landing-footer__links">
            <!-- The footer is not a markdown context, so it takes the row
                 directly rather than the wrapped-for-markdown form. -->
            <c-social-links-markup variant="landing-social--footer" />
          </span>
        </footer>
      </div>
    """

    css = """
      .citry-landing-page {
        overflow-x: hidden;
      }

      .citry-landing__nav-drawer {
        display: none;
      }

      .landing-shell {
        --landing-bg: #f4f8fc;
        --landing-bg-deep: #e5eef8;
        --landing-ink: #0b1729;
        --landing-muted: #4e6076;
        --landing-faint: #70849c;
        --landing-line: rgb(21 69 112 / 14%);
        --landing-panel: rgb(255 255 255 / 100%);
        --landing-panel-solid: #f9fbfe;
        --landing-blue: #276df2;
        --landing-cyan: #00a9a6;
        --landing-violet: #7457ef;
        --landing-warm: #df6d46;
        min-height: 100vh;
        background:
          radial-gradient(circle at 16% 12%, rgb(39 109 242 / 12%), transparent 28rem),
          radial-gradient(circle at 86% 28%, rgb(0 169 166 / 9%), transparent 34rem),
          var(--landing-bg);
        color: var(--landing-ink);
      }

      [data-theme="dark"] .landing-shell {
        --landing-bg: #050914;
        --landing-bg-deep: #0a1122;
        --landing-ink: #f3f7ff;
        --landing-muted: #a7b6cc;
        --landing-faint: #7588a5;
        --landing-line: rgb(127 181 255 / 15%);
        --landing-panel: rgb(11 19 36 / 100%);
        --landing-panel-solid: #0b1324;
        --landing-blue: #6d9eff;
        --landing-cyan: #4de0d5;
        --landing-violet: #a18aff;
        --landing-warm: #ff9776;
      }

      @media (prefers-color-scheme: dark) {
        :root:not([data-theme="light"]) .landing-shell {
          --landing-bg: #050914;
          --landing-bg-deep: #0a1122;
          --landing-ink: #f3f7ff;
          --landing-muted: #a7b6cc;
          --landing-faint: #7588a5;
          --landing-line: rgb(127 181 255 / 15%);
          --landing-panel: rgb(11 19 36 / 100%);
          --landing-panel-solid: #0b1324;
          --landing-blue: #6d9eff;
          --landing-cyan: #4de0d5;
          --landing-violet: #a18aff;
          --landing-warm: #ff9776;
        }
      }

      .landing-skip {
        position: fixed;
        top: 0.75rem;
        left: 0.75rem;
        z-index: 100;
        padding: 0.65rem 0.9rem;
        border-radius: 0.5rem;
        background: var(--landing-ink);
        color: var(--landing-bg);
        transform: translateY(-160%);
      }

      .landing-skip:focus {
        transform: translateY(0);
      }

      .landing-main {
        position: relative;
        padding-top: 4rem;
      }

      .landing-content {
        position: relative;
        z-index: 2;
      }

      /* A class that sets `display` beats the [hidden] default, which would
         otherwise leave every panel on screen once the script hides one. */
      .landing-shell [hidden] {
        display: none !important;
      }

      .landing-content a {
        color: inherit;
        text-underline-offset: 0.2em;
      }

      .landing-content .heading-anchor,
      .landing-content .heading-anchor:visited {
        color: inherit;
        text-decoration: none;
      }

      .landing-hero,
      .landing-section,
      .landing-final {
        width: min(76rem, calc(100% - 3rem));
        margin-inline: auto;
      }

      .landing-hero {
        position: relative;
        min-height: min(54rem, calc(100svh - 4rem));
        display: grid;
        align-content: center;
        padding: clamp(4.5rem, 10vh, 8rem) 0 6rem;
      }

      /* A blueprint grid behind the hero, drawn entirely in CSS: two repeating
         line gradients and one accent glow, with no payload and no script. It
         bleeds past the page column to reach the window edges, and the mask
         fades it out before it reaches the copy, so contrast is never the
         reader's problem. */
      .landing-hero::before {
        content: "";
        position: absolute;
        z-index: -1;
        inset: -8rem -50vw -6rem;
        background:
          radial-gradient(
            circle at 14% 6%,
            color-mix(in srgb, var(--landing-blue), transparent 76%),
            transparent 42%
          ),
          repeating-linear-gradient(
            90deg,
            transparent 0 2.25rem,
            var(--landing-line) 2.25rem calc(2.25rem + 1px)
          ),
          repeating-linear-gradient(
            180deg,
            transparent 0 2.25rem,
            var(--landing-line) 2.25rem calc(2.25rem + 1px)
          );
        mask-image: radial-gradient(
          130% 105% at 6% 0%,
          rgb(0 0 0 / 90%) 0%,
          rgb(0 0 0 / 40%) 46%,
          transparent 76%
        );
        pointer-events: none;
      }

      .landing-hero__grid {
        display: grid;
        grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.95fr);
        gap: clamp(2rem, 5vw, 4.5rem);
        align-items: start;
      }

      .landing-hero__copy {
        min-width: 0;
      }

      .landing-hero__code {
        min-width: 0;
        margin-top: -2.5rem;
      }

      .landing-hero__code pre {
        max-height: 35rem;
        font-size: 0.72rem;
      }

      .landing-eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 0.55rem;
        margin: 0 0 1.4rem;
        padding: 0.45rem 0.75rem;
        border: 1px solid var(--landing-line);
        border-radius: 999px;
        background: var(--landing-panel);
        color: var(--landing-muted);
        font-family: var(--font-mono);
        font-size: 0.75rem;
        letter-spacing: 0.055em;
        text-transform: uppercase;
      }

      .landing-eyebrow::before {
        content: "";
        width: 0.48rem;
        height: 0.48rem;
        border-radius: 50%;
        background: var(--landing-cyan);
        box-shadow: 0 0 1rem var(--landing-cyan);
      }

      /* Sized for a sentence rather than a phrase: the cap holds it to three
         lines beside the code panel instead of stacking one word per row. */
      .landing-content .landing-hero h1 {
        max-width: 15ch;
        margin: 0;
        font-size: clamp(2.9rem, 5.6vw, 4.6rem);
        font-weight: 700;
        line-height: 1;
        letter-spacing: -0.03em;
        text-wrap: balance;
      }

      .landing-hero__lede {
        max-width: 43rem;
        margin: 2rem 0 0;
        color: var(--landing-muted);
        font-size: clamp(1.12rem, 2vw, 1.4rem);
        line-height: 1.62;
      }

      .landing-hero__lede strong {
        color: var(--landing-ink);
        font-weight: 620;
      }

      .landing-actions {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.75rem;
        margin-top: 2rem;
      }

      /* Two weights, not two boxes. The primary action is a solid, slightly
         raised control; the secondary is quiet until the pointer reaches it, so
         the pair reads as a decision rather than a toolbar. */
      .landing-button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.45rem;
        height: 3rem;
        padding: 0 1.15rem;
        border: 1px solid transparent;
        border-radius: 0.55rem;
        background: transparent;
        color: var(--landing-muted);
        font-size: 0.95rem;
        font-weight: 550;
        letter-spacing: -0.01em;
        text-decoration: none;
        transition: color 140ms ease, background 140ms ease, box-shadow 140ms ease;
      }

      .landing-content .landing-button:hover,
      .landing-content .landing-button:focus-visible {
        background: color-mix(in srgb, var(--landing-ink), transparent 94%);
        color: var(--landing-ink);
      }

      .landing-button:focus-visible {
        outline: 2px solid var(--landing-blue);
        outline-offset: 2px;
      }

      /* The arrow leans forward on hover, so the button answers the pointer
         without the whole control jumping under it. */
      .landing-button__arrow {
        width: 0.85rem;
        height: 0.85rem;
        flex: none;
        transition: transform 160ms ease;
      }

      .landing-button:hover .landing-button__arrow,
      .landing-button:focus-visible .landing-button__arrow {
        transform: translateX(0.15rem);
      }

      .landing-content .landing-button--primary {
        padding: 0 1.35rem;
        background: var(--landing-blue);
        color: #fff;
        font-weight: 600;
        /* A hairline of light along the top edge and a shadow tinted with the
           button's own colour, so it sits on the page rather than on top of it. */
        box-shadow:
          inset 0 1px 0 rgb(255 255 255 / 22%),
          0 6px 16px -8px color-mix(in srgb, var(--landing-blue), transparent 25%);
        transition: 0.2s;
      }

      .landing-content .landing-button--primary:hover,
      .landing-content .landing-button--primary:focus-visible {
        background: color-mix(in srgb, var(--landing-blue), #000 12%);
        color: #fff;
        box-shadow:
          inset 0 1px 0 rgb(255 255 255 / 22%),
          0 10px 12px -10px color-mix(in srgb, var(--landing-blue), transparent 10%);
      }

      [data-theme="dark"] .landing-content .landing-button--primary:hover,
      [data-theme="dark"] .landing-content .landing-button--primary:focus-visible {
        background: color-mix(in srgb, var(--landing-blue), #fff 12%);
      }

      /* The channels the project actually lives on, under the install line. */
      .social-links {
        display: flex;
        align-items: center;
        gap: 0.25rem;
      }

      .landing-social {
        margin-top: 0.9rem;
        margin-left: -0.5rem;
      }

      .social-links__link {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 2.25rem;
        height: 2.25rem;
        border-radius: 0.5rem;
        color: var(--landing-faint);
        transition: color 140ms ease, background 140ms ease;
      }

      .landing-content .social-links__link:hover,
      .landing-content .social-links__link:focus-visible {
        background: color-mix(in srgb, var(--landing-ink), transparent 94%);
        color: var(--landing-ink);
      }

      .landing-social--footer {
        margin-left: 0.25rem;
      }

      .landing-social--footer .social-links__link {
        width: 1.9rem;
        height: 1.9rem;
      }

      /* Reads as a terminal line rather than a form field: a prompt mark, the
         command, and a copy control that only colours in on hover. */
      .landing-install {
        display: flex;
        width: fit-content;
        max-width: 100%;
        align-items: center;
        gap: 0.9rem;
        margin-top: 1.1rem;
        padding: 0 0.5rem 0 1rem;
        min-height: 3.25rem;
        border: 1px solid var(--landing-line);
        border-radius: 0.6rem;
        background: var(--landing-panel-solid);
      }

      .landing-install code {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        min-width: 0;
        overflow-x: auto;
        color: var(--landing-ink);
        font-family: var(--font-mono);
        font-size: 0.92rem;
        white-space: nowrap;
      }

      .landing-install code::before {
        content: "$";
        color: var(--landing-blue);
        user-select: none;
      }

      .landing-copy {
        display: inline-flex;
        align-items: center;
        flex: none;
        min-height: 2.25rem;
        padding: 0 0.7rem;
        border: 0;
        border-radius: 0.4rem;
        background: transparent;
        color: var(--landing-faint);
        cursor: pointer;
        font: inherit;
        font-size: 0.78rem;
        transition: background 140ms ease, color 140ms ease;
      }

      .landing-copy:hover,
      .landing-copy:focus-visible {
        background: color-mix(in srgb, var(--landing-blue), transparent 90%);
        color: var(--landing-ink);
      }

      .landing-sponsors {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.75rem 1.5rem;
        margin: 1.5rem 0 0;
        padding: 0;
        list-style: none;
      }

      .landing-sponsors a {
        color: var(--landing-ink);
        font-size: 1.05rem;
        font-weight: 640;
        text-decoration: none;
      }

      .landing-sponsors a:hover {
        color: var(--landing-blue);
      }

      .landing-section {
        padding: clamp(5rem, 10vw, 9rem) 0;
        border-top: 1px solid var(--landing-line);
      }

      /* A full-width band on the deeper surface. Breaking out of the page
         column stops every section from arriving at the same width and tone;
         the page hides sideways overflow, so the viewport-width trick here
         cannot introduce a horizontal scrollbar. */
      .landing-section--band {
        width: auto;
        margin-inline: calc(50% - 50vw);
        padding-inline: max(1.5rem, calc(50vw - 38rem));
        border-top: 0;
        background: var(--landing-bg-deep);
      }

      /* The facts section is deliberately the quietest one on the page. */
      .landing-section--plain {
        padding: clamp(3.5rem, 7vw, 5.5rem) 0;
      }

      .landing-content .landing-section--plain h2 {
        max-width: 34ch;
        font-size: clamp(1.4rem, 2.2vw, 1.9rem);
        letter-spacing: -0.015em;
      }

      .landing-section--plain .landing-trust-grid {
        margin-top: 2rem;
        gap: clamp(1.5rem, 4vw, 3rem);
        align-items: start;
      }

      .landing-section__kicker {
        margin: 0 0 1rem;
        color: var(--landing-blue);
        font-family: var(--font-mono);
        font-size: 0.76rem;
        font-weight: 650;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      .landing-content .landing-section h2,
      .landing-content .landing-final h2 {
        max-width: 18ch;
        margin: 0;
        color: var(--landing-ink);
        font-size: clamp(2.1rem, 3.6vw, 3.5rem);
        line-height: 1.06;
        letter-spacing: -0.025em;
        text-wrap: balance;
      }

      .landing-content .headerlink {
        color: var(--landing-faint);
        font-size: 0.4em;
        text-decoration: none;
        vertical-align: middle;
        opacity: 0;
      }

      .landing-content h2:hover .headerlink,
      .landing-content .headerlink:focus-visible {
        opacity: 1;
      }

      .landing-section__intro {
        max-width: 42rem;
        margin: 1.4rem 0 0;
        color: var(--landing-muted);
        font-size: 1.1rem;
        line-height: 1.7;
      }

      .landing-proof-grid,
      .landing-error-grid,
      .landing-human-grid,
      .landing-trust-grid {
        display: grid;
        grid-template-columns: minmax(0, 1.15fr) minmax(17rem, 0.85fr);
        gap: clamp(2rem, 6vw, 5.5rem);
        align-items: start;
        margin-top: 3rem;
      }

      .landing-proof-grid > *,
      .landing-error-grid > *,
      .landing-human-grid > *,
      .landing-trust-grid > * {
        min-width: 0;
      }

      .landing-code {
        overflow: hidden;
        min-width: 0;
        max-width: 100%;
        border: 1px solid var(--landing-line);
        border-radius: 0.9rem;
        background: var(--landing-panel-solid);
        box-shadow: 0 2rem 6rem rgb(18 48 84 / 10%);
      }

      .landing-code__bar {
        display: flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.7rem 0.9rem;
        border-bottom: 1px solid var(--landing-line);
        color: var(--landing-faint);
        font-family: var(--font-mono);
        font-size: 0.7rem;
      }

      .landing-code__dot {
        width: 0.42rem;
        height: 0.42rem;
        border-radius: 2px;
        background: var(--landing-blue);
      }

      .landing-code__bar span:last-child {
        margin-left: 0.15rem;
      }

      .landing-code .highlight,
      .landing-code pre {
        margin: 0;
        border: 0;
        border-radius: 0;
        background: transparent;
      }

      .landing-code pre {
        overflow: auto;
        padding: 1.25rem;
        font-size: 0.78rem;
        line-height: 1.65;
      }

      .landing-error-list {
        display: grid;
        gap: 0.6rem;
      }

      /* The caret only means something where a row opens its own panel, so it
         is absent from the layout until the list becomes an accordion. */
      .landing-picker__caret {
        display: none;
        width: 1rem;
        height: 1rem;
        align-self: center;
        color: var(--landing-faint);
        transition: transform 160ms ease;
      }

      .landing-picker__row {
        user-select: text;
        display: grid;
        grid-template-columns: 1.75rem 1fr;
        gap: 0.7rem;
        width: 100%;
        padding: 0.5rem 0.85rem;
        border: 1px solid transparent;
        border-radius: 0.7rem;
        background: transparent;
        color: var(--landing-muted);
        cursor: pointer;
        font: inherit;
        text-align: left;
      }

      .landing-picker__row:hover,
      .landing-picker__row:focus-visible,
      .landing-picker__row.is-active {
        border-color: var(--landing-line);
        background: var(--landing-panel);
        color: var(--landing-ink);
      }

      .landing-picker__number {
        color: var(--landing-warm);
        font-family: var(--font-mono);
        font-size: 0.76rem;
      }

      .landing-picker__blurb {
        font-size: 0.85rem;
      }

      /* The annotated walkthrough: source on the left, one explanation on the
         right. Marked lines carry a dot in the gutter so a reader can see where
         there is something to point at. */
      .landing-tour {
        display: grid;
        grid-template-columns: minmax(0, 1.35fr) minmax(16rem, 0.65fr);
        gap: clamp(1.5rem, 4vw, 3rem);
        align-items: start;
        margin-top: 3rem;
      }

      .landing-tour__code {
        min-width: 0;
      }

      .landing-tour__code pre {
        max-height: none;
        padding-left: 1.9rem;
        font-size: 0.78rem;
      }

      .landing-tour__line {
        position: relative;
        display: block;
        min-height: 1.2rem;
        cursor: help;
        transition: background 140ms ease;
      }

      .landing-tour__line:hover,
      .landing-tour__line.is-active {
        background: color-mix(in srgb, var(--landing-blue), transparent 88%);
        box-shadow: inset 2px 0 0 var(--landing-blue);
      }

      .landing-tour__line[data-tour-start]::before {
        content: "";
        position: absolute;
        left: -1.15rem;
        top: 0.52em;
        width: 0.42rem;
        height: 0.42rem;
        border-radius: 50%;
        background: var(--landing-blue);
        box-shadow: 0 0 0 0 color-mix(in srgb, var(--landing-blue), transparent 40%);
        animation: landing-tour-pulse 2.6s ease-out infinite;
      }

      @keyframes landing-tour-pulse {
        0%, 70% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--landing-blue), transparent 40%); }
        100% { box-shadow: 0 0 0 0.42rem color-mix(in srgb, var(--landing-blue), transparent 100%); }
      }

      .landing-tour__notes {
        position: sticky;
        top: 5.5rem;
        display: grid;
        gap: 0.9rem;
        min-width: 0;
      }

      .landing-tour__hint {
        margin: 0;
        color: var(--landing-faint);
        font-family: var(--font-mono);
        font-size: 0.72rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
      }

      .landing-tour__note {
        padding: 1.1rem 1.2rem;
        border: 1px solid var(--landing-line);
        border-radius: 0.9rem;
        background: var(--landing-panel-solid);
        box-shadow: 0 1rem 2.5rem rgb(12 30 56 / 14%);
      }

      [data-theme="dark"] .landing-tour__note {
        box-shadow: 0 1rem 2.5rem rgb(0 0 0 / 45%);
      }

      .landing-tour__note-label {
        display: block;
        margin-bottom: 0.5rem;
        color: var(--landing-blue);
        font-family: var(--font-mono);
        font-size: 0.7rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }

      .landing-tour__note strong {
        display: block;
        font-size: 1.02rem;
      }

      .landing-tour__note p {
        margin: 0.5rem 0 0;
        color: var(--landing-muted);
        font-size: 0.88rem;
        line-height: 1.6;
      }

      .landing-tour__note code {
        padding: 0.08em 0.32em;
        border-radius: 0.3rem;
        background: color-mix(in srgb, var(--landing-blue), transparent 88%);
        color: var(--landing-ink);
        font-family: var(--font-mono);
        font-size: 0.85em;
        white-space: nowrap;
      }

      /* A panel belongs to the row above it on a small screen and to a column
         beside the list on a large one. The markup keeps each panel next to its
         own row either way; here the panels are lifted out of the flow so the
         rows stay stacked tight against each other. A panel left in the grid
         would span every row and hand its height back to them as gaps. */
      .landing-picker {
        --landing-picker-rail: 20rem;
        --landing-picker-gutter: clamp(1.5rem, 4vw, 3rem);
        /* Held as one value: a minifier may drop the space between a var() and
           a following function, which would make the declaration invalid. */
        --landing-picker-columns: 20rem minmax(0, 1fr);
        position: relative;
        display: grid;
        grid-template-columns: var(--landing-picker-columns);
        gap: 0.4rem var(--landing-picker-gutter);
        align-content: start;
        /* Room for the tallest panel before the script measures the real one. */
        min-height: 26rem;
        margin-top: 3rem;
      }

      .landing-picker__item {
        display: contents;
      }

      .landing-picker .landing-picker__row {
        grid-column: 1;
      }

      .landing-picker .landing-picker__panel {
        position: absolute;
        top: 0;
        left: calc(var(--landing-picker-rail) + var(--landing-picker-gutter));
        right: 0;
      }

      .landing-diagnostics {
        display: grid;
        gap: 1rem;
        /* Both the wrapper and each panel need this. A grid item defaults to
           min-width:auto, which grows to the widest line of the error text and
           pushes the whole card past the right edge of the page instead of
           letting the message scroll inside it. */
        min-width: 0;
      }

      .landing-diagnostic {
        min-width: 0;
        padding: 1.2rem;
        border: 1px solid color-mix(in srgb, var(--landing-warm), transparent 60%);
        border-radius: 0.85rem;
        background: color-mix(in srgb, var(--landing-warm), transparent 92%);
        font-family: var(--font-mono);
        font-size: 0.78rem;
        line-height: 1.65;
      }

      .landing-diagnostic__type {
        display: block;
        margin-bottom: 0.7rem;
        color: var(--landing-warm);
        font-weight: 700;
      }

      .landing-diagnostic__mutation {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin: 0 0 1rem;
        padding-bottom: 0.9rem;
        border-bottom: 1px solid color-mix(in srgb, var(--landing-warm), transparent 75%);
        color: var(--landing-faint);
        font-size: 0.72rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
      }

      .landing-diagnostic__blurb {
        margin-left: auto;
        color: var(--landing-muted);
        letter-spacing: 0;
        text-transform: none;
      }

      /* The snippet sits above its error as its own card, styled like every
         other code block on the page. */
      .landing-picker__panel {
        display: grid;
        min-width: 0;
      }

      /* Context for the snippet under it: what the capability is and what it
         does not promise, before the reader gets to the code. */
      .landing-picker__note {
        margin-bottom: 0.6rem;
        padding: 1.1rem 1.2rem;
        border: 1px solid var(--landing-line);
        border-radius: 0.9rem;
        background: var(--landing-panel);
      }

      .landing-picker__note p {
        margin: 0;
        color: var(--landing-muted);
        font-size: 0.9rem;
        line-height: 1.65;
      }

      .landing-picker__note p + p {
        margin-top: 0.7rem;
      }

      .landing-picker__note code {
        padding: 0.08em 0.32em;
        border-radius: 0.3rem;
        background: color-mix(in srgb, var(--landing-blue), transparent 88%);
        color: var(--landing-ink);
        font-family: var(--font-mono);
        font-size: 0.85em;
        white-space: nowrap;
      }

      .landing-picker__code {
        min-width: 0;
      }

      /* The real message carries its own line breaks and carets, so it keeps
         its whitespace and scrolls sideways rather than rewrapping. */
      .landing-diagnostic pre {
        overflow-x: auto;
        margin: 0;
        padding: 0;
        border: 0;
        background: transparent;
        color: var(--landing-ink);
        font-size: 0.72rem;
        line-height: 1.6;
        tab-size: 2;
      }

      .landing-flow {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0;
        margin: 3rem 0 0;
        padding: 0;
        list-style: none;
      }

      .landing-flow li {
        position: relative;
        min-height: 10rem;
        padding: 1.2rem;
        border: 1px solid var(--landing-line);
        background: var(--landing-panel);
      }

      .landing-flow li:nth-child(n + 2) {
        border-left: 0;
      }

      .landing-flow li:first-child {
        border-radius: 0.9rem 0 0 0.9rem;
      }

      .landing-flow li:last-child {
        border-radius: 0 0.9rem 0.9rem 0;
      }

      .landing-flow__step {
        display: block;
        color: var(--landing-blue);
        font-family: var(--font-mono);
        font-size: 0.7rem;
      }

      .landing-flow strong {
        display: block;
        margin-top: 1.6rem;
        font-size: 1.15rem;
      }

      .landing-flow p {
        margin: 0.55rem 0 0;
        color: var(--landing-muted);
        font-size: 0.88rem;
        line-height: 1.55;
      }

      .landing-capabilities {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        margin: 3rem 0 0;
        padding: 0;
        border-top: 1px solid var(--landing-line);
        list-style: none;
      }

      .landing-capabilities li {
        padding: 1.35rem 1.35rem 1.35rem 0;
        border-bottom: 1px solid var(--landing-line);
      }

      .landing-capabilities li + li {
        padding-left: 1.35rem;
        border-left: 1px solid var(--landing-line);
      }

      .landing-capabilities strong {
        display: block;
        color: var(--landing-ink);
      }

      .landing-capabilities span {
        display: block;
        margin-top: 0.65rem;
        color: var(--landing-muted);
        font-size: 0.88rem;
        line-height: 1.55;
      }

      .landing-human-note,
      .landing-trust-card {
        height: 100%;
        padding: 1.4rem;
        border: 1px solid var(--landing-line);
        border-radius: 0.9rem;
        background: var(--landing-panel);
      }

      .landing-trust-card h3 {
        margin: 0;
        font-size: 1rem;
      }

      .landing-trust-card ul {
        margin: 1rem 0 0;
        padding-left: 1.1rem;
        color: var(--landing-muted);
      }

      .landing-trust-card li {
        margin-top: 0.65rem;
        line-height: 1.55;
      }

      .landing-human-note blockquote {
        margin: 0;
        color: var(--landing-ink);
        font-size: clamp(1.25rem, 2.5vw, 1.8rem);
        line-height: 1.4;
        letter-spacing: -0.025em;
      }

      .landing-human-note footer {
        margin-top: 1.4rem;
        color: var(--landing-muted);
        font-size: 0.84rem;
      }

      /* The acknowledgment grid reads as one texture of faces, so the portraits
         are much smaller here than on the People page and sit close together. */
      .landing-shell .user-list {
        gap: 0.55rem;
        margin-top: 1.5rem;
      }

      .landing-shell .user .avatar-wrapper {
        width: 2.4em;
        height: 2.4em;
      }

      .landing-shell .user .avatar-wrapper img {
        filter: saturate(0.85);
      }

      .landing-human-links {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem 1.2rem;
        margin-top: 1.5rem;
        color: var(--landing-muted);
        font-size: 0.88rem;
      }

      .landing-final {
        padding: clamp(7rem, 14vw, 13rem) 0;
        text-align: center;
      }

      .landing-content .landing-final h2 {
        max-width: 13ch;
        margin-inline: auto;
      }

      .landing-final p {
        max-width: 38rem;
        margin: 1.3rem auto 0;
        color: var(--landing-muted);
        font-size: 1.08rem;
        line-height: 1.7;
      }

      .landing-final .landing-actions,
      .landing-final .landing-install {
        justify-content: center;
        margin-inline: auto;
      }

      .landing-footer {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        width: min(76rem, calc(100% - 3rem));
        margin-inline: auto;
        padding: 1.5rem 0 2.5rem;
        border-top: 1px solid var(--landing-line);
        color: var(--landing-faint);
        font-size: 0.78rem;
      }

      .landing-footer__links {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
      }

      @media (max-width: 900px) {
        .landing-tour {
          grid-template-columns: 1fr;
          position: relative;
        }

        .landing-tour__notes {
          position: static;
        }

        /* On a narrow screen the note follows the line it explains, so the
           reader never has to scroll away from the code to read it. */
        .landing-tour__notes.is-floating {
          position: absolute;
          left: 0;
          right: 0;
          z-index: 3;
          pointer-events: none;
        }

        .landing-tour__notes.is-floating .landing-tour__hint {
          display: none;
        }

        .landing-tour__notes.is-floating .landing-tour__note {
          box-shadow: 0 1rem 2.5rem rgb(6 18 38 / 28%);
        }

        /* The code panel keeps its place beside the copy, just smaller, until
           the columns get too narrow to read either of them. */
        .landing-hero__grid {
          grid-template-columns: minmax(0, 1fr) minmax(0, 0.85fr);
          gap: 1.5rem;
        }

        .landing-hero__code pre {
          padding: 0.9rem;
          font-size: 0.7rem;
          line-height: 1.5;
        }

        .landing-proof-grid,
        .landing-error-grid,
          .landing-human-grid,
        .landing-trust-grid {
          grid-template-columns: 1fr;
        }

        .landing-flow {
          grid-template-columns: 1fr;
        }

        .landing-flow li:nth-child(n + 2) {
          border-top: 0;
          border-left: 1px solid var(--landing-line);
        }

        .landing-flow li:first-child {
          border-radius: 0.9rem 0.9rem 0 0;
        }

        .landing-flow li:last-child {
          border-radius: 0 0 0.9rem 0.9rem;
        }

        .landing-capabilities {
          grid-template-columns: repeat(2, 1fr);
        }

        .landing-capabilities li:nth-child(3) {
          padding-left: 0;
          border-left: 0;
        }
      }

      @media (max-width: 720px) {
        .landing-hero__grid {
          grid-template-columns: 1fr;
        }

        .landing-hero__code {
          display: none;
        }
      }

      @media (max-width: 600px) {
        /* One column, and each panel sits under its own row, so a reader never
           has to look elsewhere on the page for the answer. */
        .landing-picker {
          grid-template-columns: 1fr;
          min-height: 0;
        }

        .landing-picker__item {
          display: block;
        }

        /* Back into the flow, directly under the row that opened it. */
        .landing-picker .landing-picker__panel {
          position: static;
          margin: 0.6rem 0 1.2rem;
        }

        .landing-picker .landing-picker__row {
          grid-template-columns: 1.75rem 1fr auto;
        }

        .landing-picker .landing-picker__caret {
          display: block;
        }

        .landing-picker .landing-picker__row.is-active .landing-picker__caret {
          transform: rotate(180deg);
          color: var(--landing-blue);
        }

        .landing-hero,
        .landing-section,
        .landing-final,
        .landing-footer {
          width: min(100% - 2rem, 76rem);
        }

        .landing-hero {
          min-height: 42rem;
          padding-top: 4rem;
        }

        .landing-hero__copy {
          width: 100%;
        }

        .landing-content .landing-hero h1 {
          font-size: clamp(2.6rem, 11vw, 3.6rem);
        }

        .landing-actions {
          align-items: stretch;
        }

        .landing-button {
          flex: 1 1 100%;
        }

        .landing-install {
          width: 100%;
          justify-content: space-between;
        }

        .landing-capabilities {
          grid-template-columns: 1fr;
        }

        .landing-capabilities li + li,
        .landing-capabilities li:nth-child(3) {
          padding-left: 0;
          border-left: 0;
        }

        .landing-footer {
          flex-direction: column;
        }

      }

      @media (max-width: 768px) {
        .citry-landing__nav-drawer {
          display: block;
          position: fixed;
          top: 0;
          left: 0;
          bottom: 0;
          z-index: 70;
          transform: translateX(-100%);
        }

        body.djc-drawer-open .citry-landing__nav-drawer {
          transform: translateX(0);
        }
      }

      @media (prefers-reduced-motion: reduce) {
        .landing-shell *,
        .landing-shell *::before,
        .landing-shell *::after {
          scroll-behavior: auto !important;
          transition-duration: 0.01ms !important;
          animation-duration: 0.01ms !important;
          animation-iteration-count: 1 !important;
        }
      }
    """

    js = """
      $component(({ els }) => {
        const root = els[0];
        root.querySelectorAll('[data-copy-install]').forEach((button) => {
          button.addEventListener('click', async () => {
            try {
              await navigator.clipboard.writeText('pip install citry');
              button.textContent = 'Copied';
              window.setTimeout(() => { button.textContent = 'Copy'; }, 1400);
            } catch (_error) {
              button.textContent = 'Select command';
            }
          });
        });

        // Every picker on the page works the same way: a list of rows, and one
        // panel per row. All the panels ship in the HTML, so without this script
        // a reader still gets every one of them; with it, they get one at a time.
        // Below the stacked breakpoint each panel sits under its own row, so the
        // list behaves as an accordion and a second tap on an open row closes it.
        const stacked = window.matchMedia('(max-width: 600px)');

        root.querySelectorAll('[data-landing-picker]').forEach((picker) => {
          const rows = Array.from(picker.querySelectorAll('[data-picker-case]'));
          const panels = Array.from(picker.querySelectorAll('[data-picker-panel]'));
          if (!rows.length || !panels.length) return;
          let openCase = rows[0].dataset.pickerCase;

          function show(id) {
            openCase = id;
            panels.forEach((panel) => {
              panel.hidden = panel.dataset.pickerPanel !== id;
            });
            rows.forEach((row) => {
              const selected = row.dataset.pickerCase === id;
              row.classList.toggle('is-active', selected);
              row.setAttribute('aria-pressed', selected ? 'true' : 'false');
            });
            // Beside the list a panel is out of the flow, so the container has
            // to be told how much room the visible one needs.
            const shown = panels.find((panel) => !panel.hidden);
            picker.style.minHeight = shown && !stacked.matches ? `${shown.offsetHeight}px` : '';
          }

          show(openCase);
          rows.forEach((row) => {
            const id = row.dataset.pickerCase;
            row.addEventListener('click', () => {
              // Closing is only useful where the panel covers the next row.
              if (stacked.matches && openCase === id) show(null);
              else show(id);
            });
            row.addEventListener('mouseenter', () => {
              if (!stacked.matches) show(id);
            });
            row.addEventListener('focus', () => {
              if (!stacked.matches) show(id);
            });
          });
          stacked.addEventListener('change', () => {
            if (!stacked.matches && !openCase) show(rows[0].dataset.pickerCase);
            else show(openCase);
          });
        });

        // The walkthrough. Every note is already in the page; pointing at a
        // marked line narrows them to the one that explains it.
        const tourRoot = root.querySelector('[data-landing-tour]');
        if (tourRoot) {
          // The shared copy button reads textContent, and the walkthrough has no
          // newlines left in its markup, so it answers with the real source.
          tourRoot.addEventListener('click', (event) => {
            const button = event.target.closest && event.target.closest('.djc-code-copy');
            if (!button) return;
            event.stopPropagation();
            const encoded = tourRoot.dataset.tourSource || '';
            const bytes = Uint8Array.from(atob(encoded), (char) => char.charCodeAt(0));
            navigator.clipboard.writeText(new TextDecoder().decode(bytes));
          }, true);
        }

        const tour = root.querySelector('[data-landing-tour]');
        if (tour) {
          const lines = Array.from(tour.querySelectorAll('[data-tour]'));
          const notes = Array.from(tour.querySelectorAll('[data-tour-note]'));
          const hint = tour.querySelector('[data-tour-hint]');

          function showStop(id) {
            notes.forEach((note) => {
              note.hidden = note.dataset.tourNote !== id;
            });
            lines.forEach((line) => {
              line.classList.toggle('is-active', line.dataset.tour === id);
            });
            if (hint) hint.hidden = Boolean(id);
          }

          // Below the two-column layout the notes would sit under the code,
          // off screen from the line they explain, so they follow the line as a
          // floating card instead.
          const narrow = window.matchMedia('(max-width: 900px)');
          const notesBox = tour.querySelector('.landing-tour__notes');

          function placeNotes(line) {
            if (!notesBox) return;
            if (!narrow.matches) {
              notesBox.classList.remove('is-floating');
              notesBox.style.removeProperty('top');
              return;
            }
            notesBox.classList.add('is-floating');
            const code = tour.querySelector('.landing-tour__code');
            const top = line.offsetTop + line.offsetHeight - (code ? code.scrollTop : 0);
            notesBox.style.top = `${Math.max(0, top)}px`;
          }

          let openStop = null;

          function activate(line, fromTap) {
            const id = line.dataset.tour;
            // On a narrow screen the note covers the text under it, so tapping
            // the same line again puts it away.
            if (fromTap && narrow.matches && openStop === id && notesBox
                && notesBox.classList.contains('is-floating')) {
              notesBox.classList.remove('is-floating');
              openStop = null;
              return;
            }
            openStop = id;
            showStop(id);
            placeNotes(line);
          }

          if (lines.length && notes.length) {
            showStop(lines[0].dataset.tour);
            lines.forEach((line) => {
              line.setAttribute('tabindex', '0');
              line.addEventListener('mouseenter', () => activate(line, false));
              line.addEventListener('focus', () => activate(line, false));
              // Touch has no hover, so a tap has to do the same thing.
              line.addEventListener('click', () => activate(line, true));
            });
            narrow.addEventListener('change', () => {
              if (!narrow.matches && notesBox) {
                notesBox.classList.remove('is-floating');
                notesBox.style.removeProperty('top');
              }
            });
            // Tapping away from the code puts the notes back out of the way.
            document.addEventListener('click', (event) => {
              if (!narrow.matches || !notesBox) return;
              if (!tour.contains(event.target)) notesBox.classList.remove('is-floating');
            });
          }
        }

      });
    """
