# Citry Project Board demo

Project Board is a complete, deterministic browser application inspired by
the structure of Citry's large rendering benchmark. It is new application
code: it does not import the benchmark, preserve its one-file fixture layout,
or participate in benchmark measurements.

The default journey is fully local:

- search and “show completed” filters round-trip as signed Citry State;
- adding a task uses a typed form Event with server validation;
- task completion uses a custom Alpine event handled by the board's Python
  Event;
- successful mutations morph the board and dispatch a browser notification;
- a help panel and notification dismissal stay entirely in Alpine;
- lanes use slots and fills, task cards inherit a provided theme, and priority
  badges use dynamic component composition; and
- deterministic in-memory fixtures reset whenever the process restarts.

## Run it

```console
uv sync --dev
export CITRY_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
uv run uvicorn app.main:web_app --host 127.0.0.1 --port 8000
```

In PowerShell, set the variable with
`$env:CITRY_SECRET = python -c "import secrets; print(secrets.token_urlsafe(32))"`
before the same `uv run` command.

Open <http://127.0.0.1:8000/>.

The locked project uses Citry 0.4.4.

## Test it

```console
uv run pytest
```

## File map

- `app/store.py` owns deterministic task fixtures and mutation functions.
- `app/components/shell.py` owns the document shell and its slots.
- `app/components/badges.py` supplies dynamic priority components.
- `app/components/board.py` owns filters, forms, Events, actions, lanes, and
  cards.
- `app/components/page.py` composes the page.
- `app/main.py` owns FastAPI lifespan, page routing, and the `/citry` mount.

## Data and security boundaries

Rich `Task` and `LaneView` objects are render inputs and never travel as Event
State. Only `query` and `show_completed` round-trip through the browser. State
is signed but not confidential, so production handlers must still reload and
authorize every referenced record. All workers must share `CITRY_SECRET`.
Before adapting this demo for authenticated mutations, follow Citry's host
token and CSRF guidance; this fixture app has no user accounts.

For production, replace the in-memory store with a transactional database,
add per-user authorization, set an application-specific CSRF policy, use a
durable shared Citry cache for multiple workers, disable development server
settings, and add observability and deployment health checks.

## Provenance

The layout and component-composition goals were adapted from
`packages/py/citry/tests/test_benchmark_citry.py`, Citry's port of the
django-components large benchmark scenario originally associated with
django-components PR #999. No benchmark module or fixture data is imported.
This demo is covered by Citry's repository license.

The demo supports Python 3.10–3.14 and Citry 0.4.x.
