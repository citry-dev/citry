# Citry bare WSGI starter

This project shows how Citry runs directly on WSGI without a web framework.
The root application serves the page and sends requests under `/citry` to
Citry's WSGI application. The page still includes Alpine in the browser and a
synchronous Citry Event that calls Python.

## What this starter shows

- A small WSGI application passes Python `Project` records to a Citry
  component.
- Typed inputs pass projects between components. Slots fill the page shell
  with its heading and project list.
- Alpine opens the help panel without sending a request.
- A debounced Citry Event sends the search query to Python and replaces the
  project list with the matches.
- The root WSGI application delegates `/citry` and initializes Citry before
  Waitress starts its worker threads.

## Requirements

- Python 3.10 through 3.14
- [uv](https://docs.astral.sh/uv/)

The project accepts Citry 0.4.4 or newer within the 0.4.x release line. Its
lockfile pins the version exercised by the tests.

## Run the project

On macOS or Linux:

```console
uv sync --dev
export CITRY_SECRET="$(
  uv run python -c 'import secrets; print(secrets.token_urlsafe(32))'
)"
uv run waitress-serve \
  --listen=127.0.0.1:8000 app.main:application
```

In PowerShell:

```powershell
uv sync --dev
$env:CITRY_SECRET = uv run python -c `
  "import secrets; print(secrets.token_urlsafe(32))"
uv run waitress-serve `
  --listen=127.0.0.1:8000 app.main:application
```

Open <http://127.0.0.1:8000/>. You should see six project cards. The help
button opens immediately, and searching for `incident` leaves only Beacon.

The app reads `CITRY_SECRET` directly from the environment. `.env.example`
records the variable name, but the running starter does not load `.env` files.
The committed VS Code setup uses that example file only for Citry's isolated
editor discovery worker.

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
| `app/main.py` | Serves `/`, delegates `/citry` to Citry, and initializes Citry. |
| `app/citry_app.py` | Creates the shared Citry instance with the signing secret. |
| `app/components.py` | Defines the page, search Event, Alpine state, and styles. |
| `app/data.py` | Defines the sample projects and filters them. |
| `tests/test_app.py` | Calls the WSGI application and checks the page, runtime, and missing routes. |

## Follow the data

| Step | What happens |
|---|---|
| WSGI request to page | The `/` branch loads the trusted `Project` records and passes them to `ProjectPage`. |
| Parent to child | Typed component inputs pass the records from `ProjectPage` to `ProjectExplorer` and each `ProjectCard`. |
| Component to template | `template_data()` exposes only the values each template renders. |
| Python to browser | `js_data()` creates the browser-only `tipsOpen` value. |
| Browser to Python | `State.query` carries the search text to the `refresh` Event handler. |
| Python to page | The handler loads the matching records and returns a new `ProjectExplorer`. Citry replaces the existing explorer with it. |

## Start Citry with bare WSGI

`app/main.py` initializes Citry when Waitress imports the module, before the
server starts worker threads. For requests under `/citry`, the root
application moves the prefix from `PATH_INFO` to `SCRIPT_NAME` before it calls
Citry. That keeps generated URLs under the prefix the application serves.

The search handler is a normal synchronous function so it runs directly in a
WSGI worker.

## Prepare the project for production

The sample search only reads fixed local data. Citry signs `State` against
tampering, but the browser can read it. Never put secrets in `State`.

Before adding private data or write operations:

- give every worker the same `CITRY_SECRET`;
- treat `State` as browser input and check that the current user may access
  every record the handler loads;
- add your host application's CSRF token to authenticated write operations;
- use a shared Citry cache when several workers render component updates; and
- tune Waitress and your proxy for the traffic and timeouts you expect.

Read the [bare ASGI and WSGI guide](https://citry.dev/web-frameworks/#bare-asgi-and-wsgi),
[Events guide](https://citry.dev/events/), and
[security guide](https://citry.dev/security/) before extending the starter.
