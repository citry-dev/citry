# Citry + Flask starter

This application-factory project renders an interactive Project Explorer from
ordinary Python records. Alpine handles the help disclosure locally, while a
debounced Citry Event sends search State to Python and morphs fresh results.

## Run it

```console
uv sync --dev
export CITRY_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
uv run flask --app app:create_app run --host 127.0.0.1 --port 8000 --no-reload
```

In PowerShell, set the variable with
`$env:CITRY_SECRET = python -c "import secrets; print(secrets.token_urlsafe(32))"`
before the same `uv run` command.

Open <http://127.0.0.1:8000/>.

## Test it

```console
uv run pytest
```

`app/__init__.py` keeps the three host concerns together: create Flask, mount
Citry under `/citry`, and initialize it before returning the application.

## Data and production notes

Rich `Project` objects stay in Python, the query is signed Citry State but
remains client input, and `tipsOpen` is browser-only Alpine state. The project
supports Python 3.10–3.14 and Citry 0.4.x. In production, share one signing
secret across workers, authorize reloaded records, add a host CSRF token before
credentialed mutations, use a shared Citry cache for multi-worker fragments,
and serve Flask through a production WSGI server. See the
[Events security guidance](https://citry.dev/security/).
