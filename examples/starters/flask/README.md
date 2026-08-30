# Citry + Flask starter

This project shows how a Flask route renders Citry components and how a Citry
Event updates them after the page loads. Open the help panel to see an
interaction that stays in the browser, then search to call Python and update
the project cards without reloading the page.

## What this starter shows

- A Flask route passes Python `Project` records to a Citry component.
- Typed inputs pass projects between components. Slots fill the page shell
  with its heading and project list.
- Alpine opens the help panel without sending a request.
- A debounced Citry Event sends the search query to Python and replaces the
  project list with the matches.
- A Flask application factory mounts Citry's browser runtime and Event routes
  under `/citry`.

## Requirements

- Python 3.10 through 3.14
- [uv](https://docs.astral.sh/uv/)

The project accepts Citry 0.4.6 or newer within the 0.4.x release line. Its
lockfile pins the version exercised by the tests.

## Run the project

On macOS or Linux:

```console
uv sync --dev
export CITRY_SECRET="$(
  uv run python -c 'import secrets; print(secrets.token_urlsafe(32))'
)"
uv run flask --app app:create_app run \
  --host 127.0.0.1 --port 8000 --no-reload
```

In PowerShell:

```powershell
uv sync --dev
$env:CITRY_SECRET = uv run python -c `
  "import secrets; print(secrets.token_urlsafe(32))"
uv run flask --app app:create_app run `
  --host 127.0.0.1 --port 8000 --no-reload
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
| `app/__init__.py` | Creates Flask, serves `/`, mounts `/citry`, and initializes Citry. |
| `app/citry_app.py` | Creates the shared Citry instance and configures component autodiscovery. |
| `app/components/` | Keeps the page shell, card, explorer, and page in separate component modules. |
| `app/data.py` | Defines the sample projects and filters them. |
| `tests/test_app.py` | Checks the page, Citry runtime, and missing routes. |

## Follow the data

| Step | What happens |
|---|---|
| Flask route to page | `home()` loads the trusted `Project` records and passes them to `ProjectPage`. |
| Parent to child | Typed component inputs pass the records from `ProjectPage` to `ProjectExplorer` and each `ProjectCard`. |
| Component to template | `template_data()` exposes only the values each template renders. |
| Python to browser | `js_data()` creates the browser-only `tipsOpen` value. |
| Browser to Python | `State.query` carries the search text to the `refresh` Event handler. |
| Python to page | The handler loads the matching records and returns a new `ProjectExplorer`. Citry replaces the existing explorer with it. |

## Start Citry with Flask

`create_app()` registers the page route, mounts the shared Citry instance under
`/citry`, and then initializes it before returning the Flask app. This order
ensures every component and route exists before the server handles a request.

The search handler is synchronous because Flask's normal request flow is
synchronous and the same handler also works in the other starters.

## Prepare the project for production

The sample search only reads fixed local data. Citry signs `State` against
tampering, but the browser can read it. Never put secrets in `State`.

Before adding private data or write operations:

- give every worker the same `CITRY_SECRET`;
- treat `State` as browser input and check that the current user may access
  every record the handler loads;
- add your host application's CSRF token to authenticated write operations;
- use a shared Citry cache when several workers render component updates; and
- serve Flask through a production WSGI server and your usual proxy setup.

Read the [Flask integration guide](https://citry.dev/web-frameworks/#flask),
[Events guide](https://citry.dev/events/), and
[security guide](https://citry.dev/security/) before extending the starter.
