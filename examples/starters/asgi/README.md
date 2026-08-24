# Citry bare ASGI starter

This project shows the framework-free boundary explicitly: a tiny root ASGI
application owns lifespan and page routing, then delegates `/citry` to Citry's
dependency-free ASGI adapter. The page still includes local Alpine behavior
and server-backed Citry Events.

## Run it

```console
uv sync --dev
export CITRY_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
uv run uvicorn app.main:application --host 127.0.0.1 --port 8000
```

In PowerShell, set the variable with
`$env:CITRY_SECRET = python -c "import secrets; print(secrets.token_urlsafe(32))"`
before the same `uv run` command.

Open <http://127.0.0.1:8000/>.

## Test it

```console
uv run pytest
```

Read `app/main.py` for the complete ASGI routing and lifespan contract. In a
real framework, its router would perform the same prefix delegation.

Rich `Project` objects stay in Python, the query is signed Citry State but
remains client input, and `tipsOpen` is browser-only Alpine state. The project
supports Python 3.10–3.14 and Citry 0.4.x. For production, share one signing
secret across workers, authorize reloaded records, add a host CSRF token before
credentialed mutations, use a shared Citry cache for multi-worker fragments,
and put the application behind your normal process manager and proxy. See the
[Events security guidance](https://citry.dev/security/).
