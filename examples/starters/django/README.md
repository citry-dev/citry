# Citry + Django starter

This project serves the same interactive Project Explorer as the other web
starters using Django views, URL patterns, application startup, and CSRF
middleware. The help panel is local Alpine state; debounced search is a signed
Citry Event that reloads rich project records in Python.

## Run it

```console
uv sync --dev
export DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
uv run python manage.py runserver 127.0.0.1:8000 --noreload
```

In PowerShell, set the variable with
`$env:DJANGO_SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(32))"`
before the same `uv run` command.

Open <http://127.0.0.1:8000/>. Citry derives its signing secret from Django's
`SECRET_KEY`, and the page view ensures the CSRF cookie used for Event POSTs.

## Test it

```console
uv run pytest
```

See `project_explorer/apps.py` for initialization,
`project_explorer/citry_app.py` for secret reuse, and `config/urls.py` for the
Citry route include.

## Data and production notes

| Value | Owner |
|---|---|
| Rich `Project` records | Python render inputs; reloaded for every Event |
| Search query | Signed Citry `State`; still untrusted client input |
| Help disclosure | Alpine browser state; never sent to Python |

This project supports Python 3.10–3.14 and Citry 0.4.x. For production, turn
off `DEBUG`, set real `ALLOWED_HOSTS`, keep CSRF middleware and secure cookie
settings, authorize reloaded records, share Django and Citry caches across
workers, and run Django behind a production server. See the
[Django and Citry security guidance](https://citry.dev/security/).
