# Citry bare WSGI starter

This project shows the synchronous, framework-free boundary explicitly: a
small root dispatcher serves the page and delegates `/citry` to Citry's WSGI
adapter. Its Citry Event handler is intentionally a plain `def`, so it works in
a synchronous WSGI worker.

## Run it

```console
uv sync --dev
export CITRY_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
uv run waitress-serve --listen=127.0.0.1:8000 app.main:application
```

In PowerShell, set the variable with
`$env:CITRY_SECRET = python -c "import secrets; print(secrets.token_urlsafe(32))"`
before the same `uv run` command.

Open <http://127.0.0.1:8000/>.

## Test it

```console
uv run pytest
```

Read `app/main.py` for `SCRIPT_NAME`/`PATH_INFO` prefix delegation and the
required initialize-before-workers ordering.

Rich `Project` objects stay in Python, the query is signed Citry State but
remains client input, and `tipsOpen` is browser-only Alpine state. The project
supports Python 3.10–3.14 and Citry 0.4.x. For production, share one signing
secret across workers, authorize reloaded records, add a host CSRF token before
credentialed mutations, configure a shared Citry cache for multi-worker
fragments, and tune Waitress or your chosen WSGI server for the deployment.
See the [Events security guidance](https://citry.dev/security/).
