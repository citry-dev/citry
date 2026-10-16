# Django Rusty Templates, HTMX and Alpine project board

This maintained app renders the canonical project board with the official
`django_rusty_templates.RustyTemplates` Django backend at package version
0.1.0. It uses that backend for both the initial document and every HTMX board
fragment; the app has no DjangoTemplates fallback. The backend's native
`django_rusty_templates.Template.render` entry point is instrumented by the
shared render-timing helper.

Django Rusty Templates is unreleased and experimental. The dependency is pinned
to git commit `0725f875535b2fca93953a403a57df1d9b34e073` from
[LilyFirefly/django-rusty-templates](https://github.com/LilyFirefly/django-rusty-templates),
resolved on 2026-09-22. That commit's Cargo package declares version 0.1.0 and
uses the BSD-3-Clause license, retained in `assets/django_rusty_templates.LICENSE`.
Preparation builds the native extension and therefore requires a Rust toolchain
and Maturin. The exact source and license provenance is recorded in
`provenance.json`; the independent `uv.lock` records the same git revision.

The pinned upstream commit mishandles Django's `{% empty %}` branch when an
iterable resolves to an existing empty list. The maintained Rusty template is a
standard-DTL equivalent: every canonical empty branch uses
`{% if sequence %}{% for ... %}...{% endfor %}{% else %}...{% endif %}`. A
strict parity test renders the original Django app template through
`DjangoTemplates` and this variant through the configured Rusty backend at 14,
140 and 1,400 outputs across the initial state and all nine canonical action
states, requiring byte-identical output.

HTMX 2.0.10, Alpine 3.17.2, their licenses and readiness observer are retained
byte-for-byte from the Django + HTMX + Alpine app. The canonical in-memory
model, CSRF checks, action keys and five phase groups are shared with that
app. See the scenario README for the action semantics and readiness
contract.

Run locally from this directory:

```sh
uv sync --frozen --no-build --python 3.12.13
uv run --no-sync python -m unittest test_app -q
uv run --no-sync uvicorn app:application --host 127.0.0.1 --port 8000
```

Open `/?count=14&session=manual`; 140 and 1400 outputs use the same app.
The runner supplies unique sessions and operation IDs. `/health` does not render
the board.

## Server HTML render timing

The render span covers `django_rusty_templates.Template.render`, counting nested
template calls once. The board snapshot is prepared before this boundary and is
excluded. `Server-Timing: render` reports the sum of these spans and excludes
action mutation, CSRF checks, transfer and browser work. Static responses and
failed responses have no render metric. The instrumentation is benchmark
measurement against the pinned upstream package, not a framework modification.
