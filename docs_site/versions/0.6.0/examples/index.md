---
title: Examples
url: https://citry.dev/v/0.6.0/examples/
description: "Runnable Citry components, each rendered live with its source."
---
# Examples

Each example is a small, working Citry component that solves one common
task. Find the task you have, copy the code, and adapt it.

Every example page has three tabs: **Component** shows the component,
**Page** shows a complete page that uses it, and **Live demo** shows the
result. Each example has its own tests, and the docs build runs it to make
the live demo, so the code works as shown.

## Components

- [Card](/v/0.6.0/examples/card/) - accept an input, render content, and add CSS.
- [Slots](/v/0.6.0/examples/slots/) - offer named areas with fallback content.
- [Provide and inject](/v/0.6.0/examples/provide-inject/) - share data with a subtree.
- [Error boundary](/v/0.6.0/examples/error-fallback/) - show a safe fallback after an
  error.
- [Recursion](/v/0.6.0/examples/recursion/) - let a component render itself.

## Template syntax

- [Control flow](/v/0.6.0/examples/control-flow/) - use conditions, loops, and an empty
  state.

## Browser and server

- [Tabs](/v/0.6.0/examples/tabs/) - ship JavaScript with a component.
- [Form submission](/v/0.6.0/examples/form-submission/) - handle a form in the browser.
- [Fragments](/v/0.6.0/examples/fragments/) - load rendered HTML and its assets on
  demand.

## Try an example live { #try-an-example }

This example uses component State and a Python event handler. Select
**Try live** to edit it, run it in your browser, and use the result.



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
                "WelcomeCard:welcomed",
                {"greetings": state.greetings},
            )

    def state_data(
        self,
        kwargs: Kwargs,
        slots: Slots,
    ) -> dict[str, int]:
        return {"greetings": kwargs.greetings}

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,
    ) -> dict[str, str | int]:
        return {
            "greetings": kwargs.greetings,
            "name": kwargs.name.strip().title(),
        }

    def css_data(
        self,
        kwargs: Kwargs,
        slots: Slots,
    ) -> dict[str, str]:
        return {"accent": kwargs.accent}

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, int]:
        return {"greetings": kwargs.greetings}

    template = """
      <article
        class="welcome-card"
        @WelcomeCard:welcomed="greetings = $event.detail.greetings"
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
          <output v-text="greetings">{{ greetings }}</output>
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



## Start a full project { #start-from-a-complete-project }

The examples above are small so they fit on a docs page. To start an
application, copy one of the
[starter projects](https://github.com/citry-dev/citry/tree/citry@0.6.0/examples){: target="_blank" rel="noopener"}
instead. Each has its own `pyproject.toml`, lockfile, server command, and
tests.

There are starters for standalone rendering, FastAPI, Django, Flask, bare
ASGI, and bare WSGI. Every web starter builds the same page, so you can
compare how each framework connects to Citry.

Two larger demos sit beside them. Project Board is a task board where
components, Vue, and Python handlers work together. The HTMX demo shows
an existing HTMX application that keeps HTMX for requests and page
updates, while Citry renders the HTML, CSS, and JavaScript that each
route returns.