# Citry + HTMX patterns demo

Already using HTMX? You can keep it. This example shows how to render HTMX
responses with Citry, including the CSS and JavaScript used by each component.

The FastAPI application includes three common HTMX interactions:

- Filter contacts as you type without allowing a slow response to overwrite a
  newer one.
- Replace one contact row with its form, show validation errors, and save
  changes in the same row.
- Choose a department and show its teams.

FastAPI reads the request and updates the data. HTMX sends each request and
updates the matching row or list. Citry renders the HTML and includes the CSS
and JavaScript each component needs.

If you are starting a new Citry application, try
[Citry Events](https://citry.dev/events/) first. It is built into Citry and is
usually the simpler choice. This demo is for adding Citry to an existing HTMX
application without rewriting its interactions. Do not attach both HTMX and
Citry Events to the same button, input, or form. This demo uses HTMX for every
server interaction.

The search for `ada` deliberately takes 750 ms. Type Ada and then Grace to see
`hx-sync="this:replace"` cancel the slower request. Real applications need this
when one search sometimes takes longer than the next.

## Run it

```console
uv sync --dev
uv run uvicorn app.main:web_app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000/>.

HTMX 2.0.10 is checked into `app/static/`, so the application does not contact
a CDN or any other external service while it runs.

The locked project uses Citry 0.5.0.

## Test it

Check component templates with the app registry, then run the tests:

```console
uv run citry --app app.citry_app:citry_app check
uv run pytest
```

[The included GitHub Actions workflow](.github/workflows/check.yml) runs
these checks on pushes and pull requests when you copy this project, including
its hidden directories, to the root of your own repository. It installs the
locked dependencies before checking templates and running tests.

Citry's repository checks also copy the project to a temporary directory,
start the server, and run all three interactions in a real browser.

## File map

- `app/data.py` stores the sample contacts, departments, and teams in memory.
- `app/components/` keeps each Citry component returned by the routes in its
  own module.
- `app/routes.py` defines the page and fragment routes.
- `app/main.py` creates the FastAPI application, initializes Citry, and mounts
  the static and Citry routes.
- `app/static/htmx.min.js` contains the pinned HTMX runtime.
- `app/static/citry-mark.svg` contains the Citry mark used in the page header.
- `app/static/demo.css` styles the page around the Citry components.
- `tests/test_app.py` checks the page, routes, form errors, and saved changes.

## Return the whole Citry response

Each interactive row route serializes the complete row component with
`serialize(deps_strategy="fragment")`. Search results compose those trusted,
final Citry fragment strings inside plain server-rendered list wrappers. They
are inserted as final HTML and are never compiled as Vue template source.

Each contact row keeps a plain `.contact-row-host` wrapper in the page. The
Edit, Save, and Cancel requests target the nearest wrapper and replace its
contents, so the form opens in the row where you chose Edit. The wrapper remains outside the row's Vue app, so replacing its contents
unmounts one complete app without changing unrelated rows.

Load HTMX and `/citry/citry.js` once on the full page. Put a
plain `<div>` around the area HTMX will update, and replace the contents of
that `<div>` with `hx-swap="innerHTML"`. Keep the wrapper outside the HTML
returned by the route. `innerHTML` then replaces its contents while leaving
the wrapper on the page.

Do not use `hx-select` to take only part of the response, and do not split one
response across out-of-band swaps. Avoid inserting these responses directly
into `<tbody>` or `<select>`. Each of those approaches can discard the data
Citry needs to set up the component.

`ContactDetail` and `ContactForm` process their mounted Vue root with HTMX.
This is necessary because Vue creates their controls after HTMX's initial page
scan. Keep `hx-swap="innerHTML"` on the persistent unmanaged row wrapper.

The application uses separate URLs for full pages and HTMX responses. If one
URL returns different HTML based on the `HX-Request` header, also return
`Vary: HX-Request`. Otherwise, a cache may return the HTMX response when the
browser asked for the full page, or the other way around.

## Before using this pattern in production

The sample contacts live in memory and reset whenever the server restarts. A
real application also needs persistent storage and, if users can sign in,
authentication and authorization. Protect any request that changes data and
uses cookies against CSRF. If several server processes can render components,
configure a [Citry cache](https://citry.dev/advanced/cache-backends/) they all
share.

Keep HTMX pinned and review upgrades before deploying them. Test your Content
Security Policy too: HTMX runs scripts found in swapped HTML by default, and
Citry loads the scripts declared by each component.

## Credits and licenses

This demo is based on the
[`iwanalabs/django-htmx-components`](https://github.com/iwanalabs/django-htmx-components)
examples published by Dylan Castillo (`dylanjcastillo`). The original project
uses Django; this version uses FastAPI and Citry. The original project is MIT
licensed and credits Matt Butterfield and Iwana Labs. The checked-in HTMX
runtime uses the Zero-Clause BSD license. See
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) for both notices.

The demo supports Python 3.10–3.14, Citry 0.5.0 or newer, and HTMX 2.0.10.
