<!-- Absolute URL so the logo also renders on PyPI, which serves this README from
     outside the repository and cannot resolve a repo-relative path. -->
<img src="https://raw.githubusercontent.com/citry-dev/citry/main/docs/assets/citry-wordmark.png" alt="Citry" width="170">

# Citry - Refreshingly simple UI

[![PyPI - Version](https://img.shields.io/pypi/v/citry)](https://pypi.org/project/citry/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/citry)](https://pypi.org/project/citry/)
[![License](https://img.shields.io/pypi/l/citry)](https://github.com/citry-dev/citry/blob/main/LICENSE)
[![CI](https://github.com/citry-dev/citry/actions/workflows/repo--check.yml/badge.svg)](https://github.com/citry-dev/citry/actions/workflows/repo--check.yml)
[![Docs](https://img.shields.io/badge/docs-citry.dev-8a2be2)](https://citry.dev/)
[![Discord](https://img.shields.io/badge/Discord-join%20chat-5865F2?logo=discord&logoColor=white)](https://discord.gg/NaQ8QPyHtD)

Citry is a frontend framework for Python. One component can own its HTML,
browser behavior, CSS, translations, and Python event handlers, so you can
build an interactive interface without maintaining a separate frontend
application.

It feels familiar if you know HTML and Vue or React, and it works with
FastAPI, Django, Flask, Starlette, ASGI, and WSGI applications.

**Citry 0.4 is the public beta.** It supports Python 3.10 through 3.14.

[Read the docs](https://citry.dev/docs/) ·
[Try the playground](https://citry.dev/playground/) ·
[Explore examples](https://citry.dev/examples/) ·
[Install the VS Code extension](https://marketplace.visualstudio.com/items?itemName=citry-dev.citry) ·
[Browse Citry UI](https://citry.dev/ui-library/)

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
| Browser behavior | Alpine expressions, component JavaScript, CSS, and managed assets |
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

The [web-framework guide](https://citry.dev/web-frameworks/) shows the right
startup and routing setup for each host.

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
[CLI reference](https://citry.dev/cli/) for setup and CI usage.

## Performance

The current benchmark renders a large page with about 350 Citry component
markers and 986 KB of output, including browser runtimes and the component
ownership graph:

![Citry vs Django vs django-components rendering a large page. Lower is better.](https://raw.githubusercontent.com/citry-dev/citry/main/docs/assets/benchmark.png)

- Compared with django-components, Citry is about 12% slower on the first
  render and 24% faster once warm.
- Compared with a bare Django template, Citry's warm render takes about 3.5
  times as long while also running its component lifecycle, extension,
  dependency, ownership, and security work.
- Jinja2 remains the fastest no-component baseline once warm.

These are relative results from one machine. Read the
[published benchmark](https://citry.dev/about/benchmarks/) for the chart and
interpretation, or the
[benchmark repository guide](https://github.com/citry-dev/citry/blob/main/benchmarks/README.md)
to reproduce it.

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
