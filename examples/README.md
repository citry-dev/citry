# Citry example projects

These are complete projects you can copy, run, test, and adapt. They are
separate from the smaller examples embedded in the Citry documentation.

## Choose a starter

| Project | Use it when | Server Events | Local Alpine |
|---|---|---:|---:|
| [Standalone](starters/standalone/) | You want to render a self-contained HTML file without a web server. | No | Yes |
| [FastAPI](starters/fastapi/) | Your application uses FastAPI or Starlette-style mounting. | Yes | Yes |
| [Django](starters/django/) | Your application uses Django views, URL patterns, and middleware. | Yes | Yes |
| [Flask](starters/flask/) | Your application uses a Flask application factory. | Yes | Yes |
| [Bare ASGI](starters/asgi/) | You need the protocol adapter without a framework. | Yes | Yes |
| [Bare WSGI](starters/wsgi/) | You need the synchronous protocol adapter without a framework. | Yes | Yes |

Every web starter implements the same Project Explorer. Python supplies rich
project records, Alpine opens a help panel without a request, and a debounced
Citry Event filters the projects on the server and morphs the result in place.
The repeated behavior makes the host-specific routing and startup differences
easy to compare.

The standalone project uses the same visual shell and data but omits the
server-backed search. It writes one self-contained document that can be opened
locally.

## Explore a larger demo

- [Project Board](demos/project_board/) adapts the visual and component ideas
  from Citry's large benchmark into a maintainable browser application.

## How these projects are maintained

Each project has its own `pyproject.toml`, lock file, README, application code,
and tests. Repository qualification copies it outside the monorepo, runs its
own tests, starts its documented server, fetches the rendered page and Citry
runtime, and exercises the Alpine and Events journey in a browser.

The complete contract is in
[`docs/design/example_projects.md`](../docs/design/example_projects.md).
