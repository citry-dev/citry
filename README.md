<!-- Absolute URL so the logo also renders on PyPI, which serves this README from
     outside the repository and cannot resolve a repo-relative path. -->
<img src="https://raw.githubusercontent.com/citry-dev/citry/main/docs/assets/citry-wordmark.png" alt="Citry" width="170">

# Citry: Python frontend engineered for AI agents.

[![PyPI - Version](https://img.shields.io/pypi/v/citry)](https://pypi.org/project/citry/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/citry)](https://pypi.org/project/citry/)
[![License](https://img.shields.io/pypi/l/citry)](https://github.com/citry-dev/citry/blob/main/LICENSE)
[![CI](https://github.com/citry-dev/citry/actions/workflows/repo--check.yml/badge.svg)](https://github.com/citry-dev/citry/actions/workflows/repo--check.yml)
[![Docs](https://img.shields.io/badge/docs-citry.dev-8a2be2)](https://citry.dev/)
[![Discord](https://img.shields.io/badge/Discord-join%20chat-5865F2?logo=discord&logoColor=white)](https://discord.gg/NaQ8QPyHtD)

Citry is a fully typed frontend framework for Python with server events and
Vue. One component can own its HTML, browser behavior, CSS, translations,
and Python event handlers, so you can build an interactive interface without
maintaining a separate frontend application. It is inspired by Vue and
Livewire.

Citry works with FastAPI, Django, Flask, Starlette, ASGI, and WSGI
applications.

**Citry is in public beta.** It supports Python 3.10 through 3.14.

[Read the docs](https://citry.dev/docs/) ·
[Try the playground](https://citry.dev/playground/) ·
[Explore examples](https://citry.dev/examples/) ·
[Install the VS Code extension](https://marketplace.visualstudio.com/items?itemName=citry-dev.citry) ·
[Browse Citry UI](https://citry.dev/ui-library/)

<!-- benchmark-chart:errors start -->
<!-- Written by `python -m docs_site.scripts.benchmark_images` from
     docs_site/data/error_prevention.json. Rerun it rather than
     editing this block by hand. -->

## Catch mistakes early

We built the same app in 12 frameworks and made the same 63 mistakes in
each.

More green = earlier feedback = better

<picture>
  <source
    media="(prefers-color-scheme: dark)"
    srcset="https://raw.githubusercontent.com/citry-dev/citry/main/docs/assets/benchmarks/errors-20261021T182412Z-6029e02e32b8-dark.png"
  >
  <img
    src="https://raw.githubusercontent.com/citry-dev/citry/main/docs/assets/benchmarks/errors-20261021T182412Z-33f45034c4c4-light.png"
    alt="Bar chart of how the mistakes that apply to each framework ended. Mistakes reported before the app runs: Citry 54 of 61, Next.js (TypeScript) 45 of 57, Reflex 38 of 54, Nuxt (TypeScript) 39 of 58, ReactPy 24 of 56, FastHTML 20 of 48, django-unicorn 12 of 55, Tetra 9 of 57, Rusty + HTMX + Alpine 6 of 50, Django + HTMX + Alpine 6 of 52, django-components 6 of 54, Jinja + HTMX + Alpine 5 of 51."
    width="720"
  >
</picture>

Citry 0.6.1, measured before its release. Each bar counts only the
mistakes that apply to that framework.
[How we measured](https://citry.dev/about/benchmarks/#errors-how-we-measured)
<!-- benchmark-chart:errors end -->

<!-- benchmark-chart:speed start -->
<!-- Written by `python -m docs_site.scripts.benchmark_images` from
     docs_site/data/benchmark_time_to_interactive.json. Rerun it rather than
     editing this block by hand. -->

## As fast as Next.js

Time until a page with 1,400 entries is usable, the second time the
server builds it.

<picture>
  <source
    media="(prefers-color-scheme: dark)"
    srcset="https://raw.githubusercontent.com/citry-dev/citry/main/docs/assets/benchmarks/speed-composed-70d4a8802900-90d576e71b4a-dark.png"
  >
  <img
    src="https://raw.githubusercontent.com/citry-dev/citry/main/docs/assets/benchmarks/speed-composed-70d4a8802900-7fe8bbd937c4-light.png"
    alt="Bar chart of the time until the page is usable, fastest first: Nuxt 230 ms, Rusty + HTMX + Alpine 294 ms, Jinja + HTMX + Alpine 300 ms, Citry 323 ms, Next.js 324 ms, Tetra 326 ms, Django + HTMX + Alpine 342 ms, Reflex 409 ms, django-components 475 ms, django-unicorn 508 ms, FastHTML 667 ms, ReactPy 910 ms."
    width="720"
  >
</picture>

Citry 0.6.0, one run per framework. Shorter is faster.
[How we measured](https://citry.dev/about/benchmarks/#how-the-numbers-were-taken)
<!-- benchmark-chart:speed end -->

## Watch the tutorial:

<a href="https://www.youtube.com/watch?v=d3nPqvDdNB0">
  <img
    src="https://i.ytimg.com/vi/d3nPqvDdNB0/maxresdefault.jpg"
    alt="Watch the 50-minute Citry and Django code-along on YouTube"
    width="720"
  >
</a>

## Start with one component

Install Citry:

```console
python -m pip install citry
```

Or add it to a `uv` project:

```console
uv add citry
```

Define a component in ordinary Python. Typed inputs catch misspellings and
missing values, while `template_data()` chooses exactly what the template can
read:

```citry
from citry import Component


class Welcome(Component):
    class Kwargs:
        name: str
        messages: list[str]

    def template_data(self, kwargs, slots):
        return {
            "name": kwargs.name,
            "messages": kwargs.messages,
        }

    def css_data(self, kwargs, slots):
        return {"accent": "tomato"}

    template = """
      <section class="welcome">
        <h1>Welcome back, {{ name }}!</h1>
        <ul>
          <li c-for="message in messages">
            {{ message }}
          </li>
          <li c-empty>Nothing new yet.</li>
        </ul>
      </section>
    """

    css = """
      .welcome {
        border-top: 3px solid var(--accent);
      }
    """


html = str(
    Welcome(
        name="Ada",
        messages=["Build finished", "Report ready"],
    )
)
```

Components compose through HTML-like tags. Static inputs look like ordinary
HTML attributes; prefix an input with `c-` when its value is a Python
expression:

```citry-html
<main>
  <c-Welcome name="Ada" c-messages="user.inbox" />
</main>
```

That is most of the template language:

1. `<c-Name>` renders a component or a built-in control-flow tag.
2. A `c-` attribute evaluates a Python expression.

Continue with the
[step-by-step tutorial](https://citry.dev/getting-started/installation/) or
read the [template syntax guide](https://citry.dev/syntax/).

## Build the whole interface in Python

Citry gives each part of an interface a clear home:

| What you need | What Citry provides |
| --- | --- |
| Reusable UI | Components, typed inputs, slots, composition, and error boundaries |
| Browser behavior | Vue expressions, component JavaScript, CSS, and managed assets |
| Python interactions | Server events, forms, persistent State, and targeted HTML updates |
| Internationalization | Fluent catalogs, locale-aware formatting, and server/browser translations |
| Production control | Caching, HTML fragments, strict CSP support, CSRF hooks, and debug tooling |
| Editor help | Highlighting, completion, navigation, diagnostics, and safe formatting |

Learn these features through the
[component guides](https://citry.dev/concepts/components/),
[Events documentation](https://citry.dev/events/), and
[advanced guides](https://citry.dev/advanced/js-and-css-dependencies/).

Need ready-made application components? Install
[Citry UI](https://citry.dev/ui-library/) for accessible forms, dialogs,
navigation, feedback, data display, theming, and translated default labels:

```console
python -m pip install citry-ui
```

## Connect a web application

Mount Citry on the web framework that already serves your application. For
example, with FastAPI or Starlette:

```python
from citry import citry
from citry.contrib.fastapi import mount


mount(app, citry)
citry.initialize()
```

Citry includes adapters for:

| Host | Integration |
| --- | --- |
| FastAPI / Starlette | `citry.contrib.fastapi.mount()` |
| Django | `citry.contrib.django.urlpatterns()` |
| Flask | `citry.contrib.flask.mount()` |
| Any ASGI application | `citry.contrib.asgi.asgi_app()` |
| Any WSGI application | `citry.contrib.wsgi.wsgi_app()` |

The [web-framework guide](https://citry.dev/advanced/web-frameworks/) shows the right
startup and routing setup for each host.

Want a complete project instead of an integration excerpt? Copy the
[FastAPI starter](https://github.com/citry-dev/citry/tree/citry%400.6.0/examples/starters/fastapi)
or choose from the
[standalone, Django, Flask, ASGI, and WSGI starter matrix](https://github.com/citry-dev/citry/tree/citry%400.6.0/examples).
The collection also includes complete Project Board and
[HTMX integration](https://github.com/citry-dev/citry/tree/citry%400.6.0/examples/demos/htmx)
demos. Each project has its own dependencies, lockfile, and tests. Every web
starter includes a browser interaction powered by Citry Events. The HTMX demo
uses HTMX for every request and page update.

## Use the editor and command line

The free
[Citry extension for VS Code](https://marketplace.visualstudio.com/items?itemName=citry-dev.citry)
understands the HTML, Python, JavaScript, CSS, and Fluent inside a component.
It provides completion, hover help, navigation, references, diagnostics, and
safe formatting. The same extension is available from
[Open VSX](https://open-vsx.org/extension/citry-dev/citry).

Citry also installs a command-line checker:

```console
citry check --static
```

Point it at an application for registered component contracts and template
data:

```console
citry --app myproject.app:citry_app check
```

See the [VS Code guide](https://citry.dev/ide/vscode/) and
[CLI reference](https://citry.dev/advanced/cli/) for setup and CI usage.

## Work with a coding agent

Point your agent at [Citry's documentation index](https://citry.dev/llms.txt)
and your project's setup and test commands. The
[AI coding agents guide](https://citry.dev/getting-started/ai-agents/) includes
instructions for existing projects and explains the agent files included in
the current starter projects. You do not need to install a Citry skill.

## Performance

The [benchmarks page](https://citry.dev/about/benchmarks/) shows how long
a page with 1,400 rendered entries takes to become usable in Citry and
eleven other frameworks, including Django with HTMX and Alpine,
django-components, Next.js and Nuxt.

## Get help and contribute

- [Documentation](https://citry.dev/docs/)
- [Examples](https://citry.dev/examples/)
- [API reference](https://citry.dev/reference/)
- [Release notes](https://citry.dev/releases/)
- [Discord](https://discord.gg/NaQ8QPyHtD)
- [GitHub Discussions](https://github.com/citry-dev/citry/discussions)
- [Issue tracker](https://github.com/citry-dev/citry/issues)
- [Contributing guide](https://github.com/citry-dev/citry/blob/main/CONTRIBUTING.md)
- [Sponsor Citry](https://github.com/sponsors/JuroOravec)

Citry continues the component work begun in
[django-components](https://github.com/django-components/django-components)
and
[django-components/djc-core](https://github.com/django-components/djc-core).

## License

[MIT](https://github.com/citry-dev/citry/blob/main/LICENSE)
