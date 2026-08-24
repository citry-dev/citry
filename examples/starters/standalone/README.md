# Citry standalone starter

This project renders a complete HTML document without running a web server.
Python supplies the project records; Alpine powers the help disclosure in the
browser. There are deliberately no Citry Events because a local file has no
server transport to call.

## Run it

```console
uv sync --dev
uv run python -m app.render
```

Open `_build/index.html` in a browser. The document includes its Citry,
component, and Alpine dependencies, so it does not need a CDN or a running
Python process.

## Test it

```console
uv run pytest
```

Start with `app/components.py` to see explicit component inputs, parent-to-child
data flow, slots and fills, `template_data()`, `js_data()`, Alpine expressions,
component CSS, and document dependency placement.

The project supports Python 3.10–3.14 and Citry 0.4.x. Python records exist for
one render, `template_data()` exposes simple template values, and `js_data()`
seeds only the browser-local disclosure state. If you later need Python calls
after the file opens, move to one of the web starters and add the Citry HTTP
transport rather than trying to hide a server inside this build.
