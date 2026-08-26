---
title: Examples
url: https://citry.dev/v/0.4.4/examples/
description: "Runnable Citry components, each rendered live with its source."
---
# Examples

Each recipe is executable Citry code. The component source opens first; switch
tabs to see the complete page and its live result.

## Start from a complete project

The recipes below are optimized for the documentation renderer. For an
independently copyable application with its own `pyproject.toml`, lockfile,
server command, and tests, use the
[complete starter projects](https://github.com/citry-dev/citry/tree/main/examples){: target="_blank" rel="noopener"}.
The collection includes standalone rendering, FastAPI, Django, Flask, bare
ASGI, and bare WSGI, plus the larger Project Board and HTMX integration demos.
Every web starter shows the same Alpine and server Events behavior so the
framework wiring is easy to compare. The HTMX demo instead shows how an
existing application can keep using HTMX for requests and page updates while
Citry renders the HTML, CSS, and JavaScript returned by each route.

## Try an example

This complete module uses component State and a Python event handler. Select
**Try live** to edit it in the page, run it in your browser, and interact with
the rendered result.



### Welcome card with State and Events

````citry
from citry import Component
from citry.ext.events import actions


class WelcomeCard(Component):
    class Kwargs:
        name: str
        accent: str
        greetings: int = 0

    class Slots:
        pass

    class State:
        greetings: int = 0

    class Events:
        def welcome(self, state):
            state.greetings += 1
            return actions.Dispatch(
                "welcome-card:welcomed",
                {"greetings": state.greetings},
            )

    def state_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, int]:
        return {"greetings": kwargs.greetings}

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, str | int]:
        return {
            "greetings": kwargs.greetings,
            "name": kwargs.name.strip().title(),
        }

    def css_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, str]:
        return {"accent": kwargs.accent}

    template = """
      <article
        class="welcome-card"
        c-x-data="{ 'greetings': greetings }"
        @welcome-card:welcomed="greetings = $event.detail.greetings"
      >
        <p>Welcome, <strong>{{ name }}</strong>.</p>
        <button
          type="button"
          :disabled="$loading('welcome')"
          @c-click="welcome"
        >
          Say hello from Python
        </button>
        <p>
          Replies from Python:
          <output x-text="greetings">{{ greetings }}</output>
        </p>
      </article>
    """

    css = """
      .welcome-card {
        padding: 1rem;
        border-top: 0.25rem solid var(--accent);
        border-radius: 0.5rem;
        background: #f6f3ff;
        color: #221b2f;
      }

      .welcome-card button {
        padding: 0.5rem 0.75rem;
        border: 0;
        border-radius: 0.35rem;
        background: var(--accent);
        color: white;
        cursor: pointer;
      }

      .welcome-card button:disabled {
        cursor: wait;
        opacity: 0.65;
      }
    """


WelcomeCard(name="ada lovelace", accent="#6f42c1")
````



## Components

- [Card](/v/0.4.4/examples/card/) - accept an input, render content, and add CSS.
- [Slots](/v/0.4.4/examples/slots/) - offer named areas with fallback content.
- [Provide and inject](/v/0.4.4/examples/provide-inject/) - share data with a subtree.
- [Error boundary](/v/0.4.4/examples/error-fallback/) - show a safe fallback after an
  error.
- [Recursion](/v/0.4.4/examples/recursion/) - let a component render itself.

## Template syntax

- [Control flow](/v/0.4.4/examples/control-flow/) - use conditions, loops, and an empty
  state.

## Browser and server

- [Tabs](/v/0.4.4/examples/tabs/) - ship JavaScript with a component.
- [Form submission](/v/0.4.4/examples/form-submission/) - handle a form in the browser.
- [Fragments](/v/0.4.4/examples/fragments/) - load rendered HTML and its assets on
  demand.