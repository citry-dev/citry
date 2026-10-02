---
title: Develop Citry UI
description: Set up the repository to change Citry UI itself, find a component's files, run its tests and checks, and edit its templates in VS Code.
---

# Develop Citry UI

This page is for contributors who change Citry UI itself: fix a component,
add an input, or update a component's docs page. To use Citry UI in your
application, see [Installation](/ui-library/installation/) instead.

Citry UI lives in the main Citry repository, under
`packages/py/citry_ui/`. You work on it with the same tools as the rest of
Citry.

## Set up the repository

Follow [Set up your machine](/community/development/#getting-set-up) in
the Citry development guide. It installs uv, Rust, Node.js, and pnpm,
clones the repository, and runs these two commands from the repository
root:

```sh
uv sync --all-packages
pnpm install
```

`uv sync --all-packages` installs `citry-ui` in editable mode together with
its test dependencies, so your changes take effect without a reinstall.
`pnpm install` adds the Node tools that build Citry UI's CSS and
JavaScript files and type-check its templates.

## Find a component's files

Each component family has its own directory under
`packages/py/citry_ui/citry_ui/components/`. A family is one component or
a few that work together, such as `CTabs`, `CTab`, and `CTabPanel`. The
directory name is the family's name with a `c` prefix, for example
`ctabs/` or `calert_dialog/`.

| File | What it holds |
|---|---|
| `c<name>.py` | The components: their inputs and slots, event handlers, template, and `messages` |
| `runtime.source.css`, `runtime.source.js` | Readable CSS or JavaScript, when the family keeps them in files |
| `runtime.min.css`, `runtime.min.js` | Minified files built from the source files. The package ships these |
| `api.md` | The public docs page for the family |
| `api.yml` | The API reference tables that the docs build adds below `api.md` |
| `snippets/` | Example modules that `api.md` shows as live previews |
| `tests/` | The family's browser tests |
| `quality/` | Example states for the [quality tools](#use-the-quality-tools) |
| `README.md` | Notes for maintainers |

A few families, such as Button and Dialog, keep their CSS and JavaScript
as strings in their Python module instead of in separate files.

The full design of each family, including its accessibility and keyboard
rules, lives in `docs/design/ui_components/`, in a file named after the
family with hyphens, such as `tabs.md` or `alert-dialog.md`. Update it when you
change what a component does.

The `COMPONENTS` tuple in `citry_ui/components/__init__.py` lists every
component in order. Citry UI registers only the components in that tuple,
so add a new component there.

### Edit CSS and JavaScript

When a family has `runtime.source.css` or `runtime.source.js`, edit only
the source file. Then rebuild the minified files from the repository root:

```sh
pnpm citry-ui:build-assets
```

Commit the rebuilt `.min` files with your change. To check that they
match their source files without writing anything, run:

```sh
pnpm citry-ui:check-assets
```

`python scripts/check.py` runs the same check, and fails when you edit a
source file without rebuilding.

### Change default text

The labels a component shows by default, such as a close button's
accessible name, live in the `messages` block at the end of its class.
After you add or change a message, rebuild the translation catalog that
ships with the package:

```sh
uv run --no-sync python -m citry_ui_i18n._generate_catalog
```

Every message also needs an entry in the `translations` table of the
family's `api.yml`. The package tests fail when the catalog or `api.yml`
does not match the component.

### Update the docs page

The docs page for a component is its `api.md` file. The docs site reads
it directly from the component directory, adds the API tables from
`api.yml`, and publishes it under `/ui-library/components/`. The sidebar
groups come from `docs_site/ui_library.yml`, so a new family needs an
entry there.

To preview the page while you edit, start the docs server and open the
component's page:

```sh
uv run --no-sync python -m docs_site serve
```

How to embed a live example is described in the
[docs site README]({{ repo_url }}/blob/{{ repo_edit_branch }}/docs_site/README.md#add-a-citry-ui-component-preview){: target="_blank" rel="noopener"}.

## Run the tests

Run all Citry UI tests that do not need a browser:

```sh
uv run --no-sync pytest packages/py/citry_ui/tests \
  packages/py/citry_ui/citry_ui -m "not e2e"
```

These include the checks that catch most mistakes in a component change:

- `test_component_contracts.py` checks that each component's CSS
  variables, `data-*` attributes, and parts match its `api.yml` and its
  design document.
- `test_citry_ui_type_check.py` runs `citry check --types` over every
  component, so a typo in a template expression or in the component's
  JavaScript fails the test. It needs the Node tools from
  `pnpm install`, and skips without them.
- `test_asset_budgets.py` fails when the CSS or JavaScript of all
  components together, raw or compressed, grows past a fixed size limit.
  When the growth is intended, raise the limit in the test and say why in
  your pull request.
- `test_i18n_catalog.py` checks the translation catalog and the
  translation keys in `api.yml`.

### Run the browser tests

The browser tests click through each component in Chromium. Install the
browser test dependencies and the browser once:

```sh
uv sync --all-packages --group e2e
uv run --no-sync playwright install chromium
```

Then run one family's tests, for example Tabs:

```sh
uv run --no-sync pytest \
  packages/py/citry_ui/citry_ui/components/ctabs \
  -m e2e --browser chromium
```

To run every Citry UI browser test the way CI does:

```sh
uv run --no-sync pytest \
  packages/py/citry_ui/citry_ui/components \
  packages/py/citry_ui/citry_ui/quality/tests/e2e \
  packages/py/citry_ui/tests/e2e \
  -m e2e --browser chromium -n 4 --dist loadfile
```

`-n 4` runs the tests in four parallel processes. Lower it on a machine
with fewer CPUs.

### Run all checks

Before you open a pull request, run the full repository check described
in [Run the checks](/community/development/#running-the-checks):

```sh
python scripts/check.py
```

## Use the quality tools

`packages/py/citry_ui/citry_ui/quality/` holds tools that check all
components together. They are not part of the published package. Most
families have a `quality/scenario.py` that describes example states, each
one the component rendered with particular inputs, for these tools to
check.

Common commands, run from the repository root:

```sh
# List every example state as JSON
uv run --no-sync python -m citry_ui.quality.scenarios

# Render one state as a full HTML page
uv run --no-sync python -m citry_ui.quality.routes \
  tabs.overview --output /tmp/tabs.html

# Report the size of each family's CSS and JavaScript
uv run --no-sync python -m citry_ui.quality.asset_report
```

The
[quality README]({{ repo_url }}/blob/{{ repo_edit_branch }}/packages/py/citry_ui/citry_ui/quality/README.md){: target="_blank" rel="noopener"}
lists the rest, including HTML validation, screenshots, and checks of the
built package.

## Edit Citry UI in VS Code

When you work on Citry UI's templates without an application around them,
point the [VS Code extension](/ide/vscode/) at the library directly. Add
this to your VS Code settings:

```json
{
  "citry.app": "citry_ui:__citry_library__"
}
```

The editor then reads Citry UI's component names, inputs, slots, and
template data. When you also need your application's own components or
settings, point `citry.app` at your application's `Citry` instance
instead.

## Read the component rules

Citry UI components follow stricter rules than ordinary components, for
example on how a family is designed, named, and translated. Read the
[Citry UI component policy]({{ repo_url }}/blob/{{ repo_edit_branch }}/packages/py/citry_ui/docs/component-authoring.md){: target="_blank" rel="noopener"}
before you add a component or change a component's inputs.
