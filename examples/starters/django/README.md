# Citry + Django starter

This project shows how a Django view renders Citry components and how a Citry
Event updates them after the page loads. Open the help panel to see an
interaction that stays in the browser, then search to call Python and update
the project cards without reloading the page.

## What this starter shows

- A Django view passes Python `Project` records to a Citry component.
- Typed inputs pass projects between components. Slots fill the page shell
  with its heading and project list.
- Alpine opens the help panel without sending a request.
- A debounced Citry Event sends the search query to Python and replaces the
  project list with the matches.
- Django serves Citry's browser runtime and Event routes under `/citry` while
  its CSRF middleware protects Event requests.

## Requirements

- Python 3.10 through 3.14
- [uv](https://docs.astral.sh/uv/)

The project accepts Citry 0.4.4 or newer within the 0.4.x release line. Its
lockfile pins the version exercised by the tests.

## Run the project

On macOS or Linux:

```console
uv sync --dev
export DJANGO_SECRET_KEY="$(
  uv run python -c 'import secrets; print(secrets.token_urlsafe(32))'
)"
uv run python manage.py runserver 127.0.0.1:8000 --noreload
```

In PowerShell:

```powershell
uv sync --dev
$env:DJANGO_SECRET_KEY = uv run python -c `
  "import secrets; print(secrets.token_urlsafe(32))"
uv run python manage.py runserver 127.0.0.1:8000 --noreload
```

Open <http://127.0.0.1:8000/>. You should see six project cards. The help
button opens immediately, and searching for `incident` leaves only Beacon.

The app reads `DJANGO_SECRET_KEY` directly from the environment. Citry uses
that same value to sign Event state. `.env.example` records the variable name,
but the running starter does not load `.env` files. The committed VS Code setup
uses that example file, including `DJANGO_SETTINGS_MODULE`, only for Citry's
isolated editor discovery worker.

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
| `config/settings.py` | Configures Django, the signing secret, and CSRF middleware. |
| `config/urls.py` | Routes `/` to the page view and `/citry` to Citry. |
| `project_explorer/apps.py` | Initializes Citry during Django startup. |
| `project_explorer/citry_app.py` | Creates the shared Citry instance and configures component autodiscovery. |
| `project_explorer/views.py` | Renders the page and ensures the browser receives a CSRF cookie. |
| `project_explorer/components/` | Keeps the page shell, card, explorer, and page in separate component modules. |
| `project_explorer/data.py` | Defines the sample projects and filters them. |
| `tests/test_app.py` | Checks the page, Citry runtime, CSRF cookie, and missing routes. |

## Follow the data

| Step | What happens |
|---|---|
| Django view to page | `home()` loads the trusted `Project` records and passes them to `ProjectPage`. |
| Parent to child | Typed component inputs pass the records from `ProjectPage` to `ProjectExplorer` and each `ProjectCard`. |
| Component to template | `template_data()` exposes only the values each template renders. |
| Python to browser | `js_data()` creates the browser-only `tipsOpen` value. |
| Browser to Python | `State.query` carries the search text to the `refresh` Event handler. |
| Python to page | The handler loads the matching records and returns a new `ProjectExplorer`. Citry replaces the existing explorer with it. |

## Start Citry with Django

Django calls `ProjectExplorerConfig.ready()` during application startup. That
method imports the components before it initializes Citry, so registration is
complete before Django handles a page or Event request. `config/urls.py`
mounts the same Citry instance under `/citry`.

The page view uses `ensure_csrf_cookie` because the first Event POST needs
Django's CSRF cookie even though the page itself only handles a `GET` request.
The search handler remains synchronous so it works in Django's normal request
flow.

## Prepare the project for production

The sample search only reads fixed local data. Citry signs `State` against
tampering, but the browser can read it. Never put secrets in `State`.

Before adding private data or write operations:

- give every worker the same `DJANGO_SECRET_KEY`;
- turn off `DEBUG` and configure `ALLOWED_HOSTS` for your deployment;
- keep Django's CSRF middleware and configure secure cookie settings;
- treat `State` as browser input and check that the current user may access
  every record the handler loads;
- share Django and Citry caches when several workers render component
  updates; and
- run Django through a production WSGI or ASGI server.

Read the [Django integration guide](https://citry.dev/web-frameworks/#django),
[Events guide](https://citry.dev/events/), and
[security guide](https://citry.dev/security/) before extending the starter.
