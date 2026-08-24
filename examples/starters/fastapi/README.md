# Citry + FastAPI starter

This complete project renders a Project Explorer from ordinary Python data.
Alpine toggles the help panel locally; a debounced Citry Event sends only the
search text to Python, reloads the rich records, and morphs the results while
the search input keeps focus.

## Run it

```console
uv sync --dev
export CITRY_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
uv run uvicorn app.main:web_app --host 127.0.0.1 --port 8000
```

In PowerShell, set the variable with
`$env:CITRY_SECRET = python -c "import secrets; print(secrets.token_urlsafe(32))"`
before the same `uv run` command.

Open <http://127.0.0.1:8000/>. Copy `.env.example` only as a reminder of the
required variable; this small starter deliberately does not add a dotenv
dependency.

## Test it

```console
uv run pytest
```

The important integration points are visible in `app/main.py`: initialize
Citry in FastAPI's lifespan, render from a normal route, and mount Citry's
runtime and Events routes under `/citry`.

## Data and production notes

| Value | Owner |
|---|---|
| Rich `Project` records | Python render inputs; reloaded for every Event |
| Search query | Signed Citry `State`; still untrusted client input |
| Help disclosure | Alpine browser state; never sent to Python |

This project supports Python 3.10–3.14 and Citry 0.4.x. In production, give
every worker the same signing secret, authorize every record reloaded by a
handler, configure your host's CSRF policy for authenticated mutations, use a
shared Citry cache for multi-worker fragments, and replace Uvicorn's
development invocation with your deployment process. See the
[Events security guidance](https://citry.dev/security/).
