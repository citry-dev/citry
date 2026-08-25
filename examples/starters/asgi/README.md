# Citry bare ASGI starter

This project shows how Citry runs directly on ASGI without a web framework.
The root application handles startup and the page route, then sends requests
under `/citry` to Citry's ASGI application. The page still includes Alpine in
the browser and a Citry Event that calls Python.

## What this starter shows

- A small ASGI application passes Python `Project` records to a Citry
  component.
- Typed inputs pass projects between components. Slots fill the page shell
  with its heading and project list.
- Alpine opens the help panel without sending a request.
- A debounced Citry Event sends the search query to Python and replaces the
  project list with the matches.
- The root ASGI application owns lifespan and delegates `/citry` itself.

## Requirements

- Python 3.10 through 3.14
- [uv](https://docs.astral.sh/uv/)

The project accepts Citry 0.4.3 or newer within the 0.4.x release line. Its
lockfile pins the version exercised by the tests.

## Run the project

On macOS or Linux:

```console
uv sync --dev
export CITRY_SECRET="$(
  uv run python -c 'import secrets; print(secrets.token_urlsafe(32))'
)"
uv run uvicorn app.main:application --host 127.0.0.1 --port 8000
```

In PowerShell:

```powershell
uv sync --dev
$env:CITRY_SECRET = uv run python -c `
  "import secrets; print(secrets.token_urlsafe(32))"
uv run uvicorn app.main:application --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000/>. You should see six project cards. The help
button opens immediately, and searching for `incident` leaves only Beacon.

The app reads `CITRY_SECRET` directly from the environment. `.env.example`
records the variable name, but this starter does not load `.env` files.

## Test the project

```console
uv run pytest
```

## Remove the environment and test cache

On macOS or Linux:

```console
rm -rf .venv .pytest_cache
```

In PowerShell:

```powershell
Remove-Item -Recurse -Force `
  -ErrorAction SilentlyContinue .venv, .pytest_cache
```

## Find the important code

| File | What it does |
|---|---|
| `app/main.py` | Handles ASGI lifespan, serves `/`, and delegates `/citry` to Citry. |
| `app/citry_app.py` | Creates the shared Citry instance with the signing secret. |
| `app/components.py` | Defines the page, search Event, Alpine state, and styles. |
| `app/data.py` | Defines the sample projects and filters them. |
| `tests/test_app.py` | Calls the ASGI application and checks the page, runtime, and missing routes. |

## Follow the data

| Step | What happens |
|---|---|
| ASGI request to page | The `/` branch loads the trusted `Project` records and passes them to `ProjectPage`. |
| Parent to child | Typed component inputs pass the records from `ProjectPage` to `ProjectExplorer` and each `ProjectCard`. |
| Component to template | `template_data()` exposes only the values each template renders. |
| Python to browser | `js_data()` creates the browser-only `tipsOpen` value. |
| Browser to Python | `State.query` carries the search text to the `refresh` Event handler. |
| Python to page | The handler loads the matching records and returns a new `ProjectExplorer`. Citry replaces the existing explorer with it. |

## Start Citry with bare ASGI

The root `application()` handles ASGI lifespan messages and calls
`citry_app.initialize()` during startup. It also changes `root_path` before it
passes `/citry` requests to Citry, so Citry generates URLs under the same
prefix that the root application serves.

The search handler stays synchronous so the same component also works on
WSGI. ASGI hosts also support asynchronous Citry Event handlers when your
application needs them.

## Prepare the project for production

The sample search only reads fixed local data. Citry signs `State` against
tampering, but the browser can read it. Never put secrets in `State`.

Before adding private data or write operations:

- give every worker the same `CITRY_SECRET`;
- treat `State` as browser input and check that the current user may access
  every record the handler loads;
- add your host application's CSRF token to authenticated write operations;
- use a shared Citry cache when several workers render component updates; and
- run the application through your normal process manager and proxy.

Read the [bare ASGI and WSGI guide](https://citry.dev/web-frameworks/#bare-asgi-and-wsgi),
[Events guide](https://citry.dev/events/), and
[security guide](https://citry.dev/security/) before extending the starter.
