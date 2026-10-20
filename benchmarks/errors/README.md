# Error-prevention benchmark

This benchmark writes the same developer mistakes in Citry and in other web
frameworks, and records when each framework first tells the developer about
them: in the editor, from a command-line check, from the build, at runtime
with an error, or not at all. It answers
[#158](https://github.com/citry-dev/citry/issues/158): which mistakes each
framework catches, and how early.

It does not produce one combined score. It reports, for every mistake and
framework, the earliest stage that reported it.

## How a result is produced

1. Every framework has one small clean app in
   `frameworks/<framework>/baseline/`. All of them build the same page,
   described in [The reference page](#the-reference-page), so a mistake means
   the same thing everywhere.
2. Every mistake in [`catalogue.toml`](catalogue.toml) has one folder per
   framework under `cases/<mistake>/<framework>/`. Its `port.toml` names the
   baseline files the case replaces and the line that carries the mistake.
3. The runner copies the clean app, lays the case's files over it, and runs
   that framework's tools, listed in `frameworks/<framework>/framework.toml`.
   A tool's finding counts if the clean app did not produce it and it
   points within `window` lines of the change (three by default), or has no
   location at all. A finding elsewhere can still come from the change: a
   parser reports an unclosed tag at the outer element, and a type checker
   reports a wrong value where it is used. It can also be a side effect, such
   as a variable the change left unused. So a finding elsewhere counts only
   when the case's `indirect` note says why it comes from the mistake, and
   the report marks that cell `°`. Every finding elsewhere that no note
   confirms is listed in `results.json`, so a reader can check what was left
   out.
4. The runner then starts the app's development server, clicks through the
   page in Chromium, and compares the result with the clean app's. This
   decides the outcome when no tool reported the mistake:
   - a server error, an error response or a browser error is a runtime error;
   - a browser or server warning is a runtime warning;
   - a different page with no message is "silently wrong";
   - the same page is "never".

The report puts each mistake in the first of six outcomes it reaches, from
best to worst: an error before running (in the editor, a check, or the
build), only a warning before running, an error at runtime, only a warning
at runtime, missed with a wrong page, and missed with no visible change. A
summary table counts these per framework (the docs page draws it as a
chart), and a second table shows every mistake.
Many tools show warnings in the editor but let a build pass, so a warning
is kept apart from an error. A linter that has no severity of its own, such
as ruff or djLint, fails its command on any finding, so its findings count
as errors.

## Run it

From `benchmarks/errors/runner/`:

```bash
uv sync --frozen
uv run --no-sync citry-errors validate
uv run --no-sync citry-errors prepare
uv run --no-sync citry-errors run
uv run --no-sync citry-errors report \
  ../../../.benchmarks/errors/runs/<run-id> \
  --output ../results/<date>-<label>
```

`run` takes `--framework` and `--mistake`, each repeatable, to run part of
the matrix, and `--skip-runtime` to run the static stages only. Installed
environments, working copies and the raw output of every tool are kept under
`.benchmarks/errors/` at the repository root. Only the compact report in
`results/` is committed: `report.html`, a self-contained page with the chart
and the full table that opens straight from disk, plus `matrix.md` and
`results.json`.

A full run takes tens of minutes, mostly production builds and development
servers. It is not part of routine CI. Run it at each Citry release, and
when a framework's pinned versions change.

## Latest result

[`results/2026-10-20/`](results/2026-10-20/) is the run published on the docs
site's Error prevention page. Open `report.html` there in a browser for the
chart and the full table; `results.json` has the first few findings behind
each cell, and the findings that pointed away from the change without an
`indirect` note. Some differences between cells come from
how each framework naturally writes a part of the page, not from its tools:

- **m20:** Django's toggle script is a `.js` file, which VS Code's
  JavaScript check reads; Jinja's is written inline in an Alpine attribute,
  which nothing checks before the browser.
- **m13:** some apps read the state field before writing it, so a
  misspelled field fails at runtime; others only write it, so the page is
  silently wrong.
- **m17:** where the wrong type is computed differs (a Python data class,
  a server route, a page component), and so does where the type checker
  reports it.

Django Rusty Templates, django-components, Tetra, django-unicorn, Reflex and
ReactPy are not measured yet.

## The reference page

Every baseline app serves this page at `/`, using its framework's normal way
of writing each part. The visible text must match exactly, because the
runner's browser check clicks the same buttons in every framework.

| Part | What the page does | Used by |
| --- | --- | --- |
| Heading | An `<h1>` reading `Projects`. Where the framework has translations built in, with nothing extra to install, the text comes from the message `board.title` | m15 |
| Board wrapper | A `<div class="board" title="Board">` around everything below. The stylesheet makes `.board` text `rgb(0, 128, 0)` | m10, m11, m16 |
| Owner | `Owner: Ada`, read in the template from a server object `owner` with a `name` attribute | m07, m08 |
| Public setting | `API: /api`. The server passes the public value `/api` to browser-side code, which renders it. The server also holds `SECRET_TOKEN = "s3cr3t"`, which never reaches the browser | m12 |
| Cards | Three cards from server data: Alpha 3, Beta 5, Gamma 8. Each is rendered by a reusable `Card` with a required string input `title` and a required number input `count`, and shows `Alpha: 3 tasks` | m01 to m04, m17, m22, m23 |
| Card footer | The page fills the card's `footer` slot (or block, or child region) with a link `Open Alpha` to `#alpha` | m05 |
| Card hide | Each card has a `Hide` button. It tells the page through an event or callback named `hide`, and the page then hides that card | m24 |
| Counter | `Saved: 0` and an `Add` button. Add sends `{amount: 1}` to a server handler, route or action named `save`. The server adds `amount` to a value kept in a state field named `count`, and the page then shows `Saved: 1` | m06, m13, m18 |
| Details | A `Details` button toggles browser-side state named `open`. While open, the text `Details are visible` shows | m14, m19, m20, m21 |
| Search form | `<form role="search"><button type="submit">Search</button></form>` | m09 |

The runner's browser check records the page right after it loads, clicks
`Add`, `Details`, and the first `Hide` in that order, records the page again,
then reloads it and records it a third time. The reload shows whether the
saved count survives a new page load. Citry keeps it in browser-held state,
so its clean page shows `Saved: 0` again after the reload, while the other
frameworks keep it on the server and show `Saved: 1`. Each card's footer
link names its own project.

A part the framework cannot express naturally may be left out, and every case
that needs it is then recorded as `not-applicable` with the reason. For
example, a server-template stack with no browser-side component model has no
hydration, so m14 does not apply to it.

## Writing a case

- **Write the mistake a developer of that framework would actually make.**
  If the framework spells the idea differently, write its natural version:
  Next.js has no string event names, but a misspelled callback prop is the
  same mistake. Never make a mistake harder or easier to catch than it
  naturally is.
- **One mistake per case.** Change only what the mistake needs, in files the
  baseline already has.
- **Point at the mistake.** `mistake.contains` is text that appears on exactly
  one line of `mistake.file`, the line where a developer would look first.
- **Record what does not apply.** Use `status = "not-applicable"` when the
  mistake has no natural equivalent, and `status = "prevented"` when the
  framework's design makes it impossible to write. Both need a `reason`.
  Never drop a case because of how a framework scores on it.
- **Confirm a report that points elsewhere.** When a tool reports the
  mistake more than `window` lines from `mistake.contains`, or in another
  file, add an `[indirect]` table with a `reason` saying why that finding
  comes from the mistake, and the rule `codes` of the findings it covers.
  Only findings with those codes count; every other one is listed in
  `results.json` and not counted. Set `window` only when the mistake spans
  several lines.
- Do not change a case after seeing its result, unless the case does not
  express the mistake the catalogue describes. Record such a fix in the
  commit message.

```toml
# cases/m02-input-name/next/port.toml
status = "ported"
files = { "app/board.tsx" = "board.tsx" }
mistake = { file = "app/board.tsx", contains = "titel=" }
```

## Each framework's tools

`framework.toml` lists the tools a developer of that framework has before
running the app: the official starter's tools and the editor setup its docs
recommend, plus the
linters and type checker most of its projects add. Earlier is better, so a
mistake these tools report counts as caught before running, however the
framework itself would have reported it. For every Python stack that means
pyright in standard mode (Pylance with type checking turned on) and ruff
with its default rules; for Django and Jinja templates, djLint; for Nuxt,
the official `@nuxt/eslint` module; for Next.js, the ESLint its starter
installs. Each tool keeps its default rules, with two exceptions that the
clean app needs and that such projects commonly make: FastHTML's main.py
turns off ruff's star-import rules (F403, F405), and Nuxt's ESLint config
turns off `vue/multi-word-component-names`. An app setting that is off by
default, such as Jinja's `StrictUndefined`, stays off in the published
results.

| Stage | What it measures |
| --- | --- |
| `editor` | What the recommended editor setup shows. Measured with the command-line form of the same engine: TypeScript's `tsc` for the TypeScript editor service, `vue-tsc` for the Vue extension, pyright in Pylance's standard type-checking mode, and `citry check --types` for Citry's language server, which runs the same checks |
| `check` | The check command the framework's docs tell developers to run, such as `manage.py check` or `citry check`, and the linters listed above |
| `build` | The production build, when the framework has one |

Each baseline pins exact versions in its own lockfile, and those versions are
part of the result.

## What the result does not show

- The editor stage uses each engine's command-line form, not a running
  editor. Where the two differ, the difference is noted in
  `framework.toml`.
- Whether a message is easy to understand is not scored, only whether one
  appears and where it points.
- Each framework's cases were written by Citry's maintainers. Corrections from
  each framework's users are welcome; see
  [#151](https://github.com/citry-dev/citry/issues/151).
