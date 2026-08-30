# Citry standalone starter

This project renders an interactive HTML file without running a web server.
Python builds the project cards and bundles the page's CSS and JavaScript.
After you open the file, Alpine keeps the help button working entirely in the
browser.

## What this starter shows

- Python `Project` records pass through typed Citry component inputs.
- Slots fill the page shell with its heading and project list.
- `template_data()` gives each template the values it renders.
- `js_data()` gives Alpine the browser-only `tipsOpen` value.
- Citry places the component CSS, JavaScript, and browser runtime into one HTML
  document.
- Running the render command twice with unchanged inputs produces the same
  file.

This starter has no Citry Events. A local file has no HTTP route that can call
a Python Event handler after the render command finishes.

## Requirements

- Python 3.10 through 3.14
- [uv](https://docs.astral.sh/uv/)

The project accepts Citry 0.4.4 or newer within the 0.4.x release line. Its
lockfile pins the version exercised by the tests.

## Render the page

These commands work in macOS, Linux, and PowerShell:

```console
uv sync --dev
uv run python -m app.render
```

Open `_build/index.html` in a browser. You should see six project cards, and
the help button should open without a network connection or running Python
process.

Run the render command again whenever you change the data or components. With
unchanged inputs, it produces the same document each time.

## Test the project

```console
uv run pytest
```

## Remove the environment, test cache, and build

On macOS or Linux:

```console
rm -rf .venv .pytest_cache _build
```

In PowerShell:

```powershell
Remove-Item -Recurse -Force `
  -ErrorAction SilentlyContinue .venv, .pytest_cache, _build
```

## Find the important code

| File | What it does |
|---|---|
| `app/render.py` | Initializes Citry, renders reproducible output, and writes `_build/index.html`. |
| `app/citry_app.py` | Creates the Citry instance and configures component autodiscovery. |
| `app/components/` | Keeps the page shell, card, explorer, and page in separate component modules. |
| `app/data.py` | Defines the sample projects shown on the page. |
| `tests/test_standalone.py` | Checks deterministic output and confirms the document uses no external assets. |

## Follow the data

| Step | What happens |
|---|---|
| Render command to page | `render_document()` loads the `Project` records and passes them to `ProjectPage`. |
| Parent to child | Typed component inputs pass the records from `ProjectPage` to `ProjectExplorer` and each `ProjectCard`. |
| Component to template | `template_data()` exposes only the values each template renders. |
| Python to browser | `js_data()` creates the browser-only `tipsOpen` value. |
| Components to document | Document serialization embeds the CSS, JavaScript, and Citry runtime in the HTML file. |

## Choose a web starter when Python must respond

The generated page can keep running browser-side Alpine interactions, but it
cannot call Python after the file opens. Choose the FastAPI, Django, Flask,
ASGI, or WSGI starter when a click or form submission needs a Python response.
Those projects mount Citry's HTTP routes and show the same project list with
server-backed search.

## Prepare the page for publishing

- Remember that every value rendered into the page becomes part of the HTML
  file. Do not include secrets or data the reader should not receive.
- Serve the file with an HTML content type and the security headers required
  by your hosting environment.
- Render a fresh file whenever the source data or components change.

Read the [installation guide](https://citry.dev/getting-started/installation/)
and [Alpine syntax guide](https://citry.dev/syntax/alpine/) before extending
the starter.
