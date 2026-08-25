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

Every web starter implements the same Project Explorer. Its page route sends
Python `Project` records to Citry components, Alpine opens the help panel in
the browser, and a Citry Event sends each search query to Python and updates
the project list. Because the visible behavior stays the same, you can compare
how each host starts Citry and routes requests under `/citry`.

The standalone project uses the same visual shell and data but omits the
server-backed search. It writes one self-contained document that can be opened
locally.

Each starter README shows how to install dependencies. Web starter READMEs
also show how to set the required secret. After that setup, run the project
from its own directory:

| Project | Command |
|---|---|
| Standalone | `uv run python -m app.render` |
| FastAPI | `uv run uvicorn app.main:web_app --host 127.0.0.1 --port 8000` |
| Django | `uv run python manage.py runserver 127.0.0.1:8000 --noreload` |
| Flask | `uv run flask --app app:create_app run --host 127.0.0.1 --port 8000 --no-reload` |
| Bare ASGI | `uv run uvicorn app.main:application --host 127.0.0.1 --port 8000` |
| Bare WSGI | `uv run waitress-serve --listen=127.0.0.1:8000 app.main:application` |

Read the [web framework guide](https://citry.dev/web-frameworks/) for host
setup and the [security guide](https://citry.dev/security/) before adding
private data or write operations.

## Explore a larger demo

- [Project Board](demos/project_board/) adapts the visual and component ideas
  from Citry's large benchmark into a maintainable browser application.
- The [HTMX demo](demos/htmx/) lets you search contacts as you type, edit and
  validate a contact in place, and update the team list after choosing a
  department. FastAPI handles the routes, HTMX sends requests and updates the
  page, and Citry renders each response.

## How these projects are maintained

Each project has its own `pyproject.toml`, lock file, README, application code,
and tests. CI copies each project to a temporary directory and runs its tests.
For web projects, it starts the server and clicks through the interactions in
a real browser. For the standalone starter, it opens the generated HTML file.
The web starters cover Alpine and Citry Events; the standalone starter covers
Alpine without a server. The HTMX demo runs against the same pinned HTMX file
that it serves to users.

The complete contract is in
[`docs/design/example_projects.md`](../docs/design/example_projects.md).
