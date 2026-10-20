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
   framework under `cases/<mistake>/<framework>/`. Its `port.toml` lists the
   text edits that write the mistake into the baseline's files, and names
   the line that carries the mistake.
3. The runner copies the clean app, applies the case's edits to the copy,
   and runs that framework's tools, listed in
   `frameworks/<framework>/framework.toml`.
   A tool's finding counts if the clean app did not produce it and it
   points within `window` lines of the mistake line (three by default). A
   failing command with no location takes the first file and line its output names;
   with none, it counts only when its message names the changed file. A
   finding elsewhere can still come from the change: a
   parser reports an unclosed tag at the outer element, and a type checker
   reports a wrong value where it is used. It can also be a side effect, such
   as a variable the change left unused. So a finding elsewhere counts only
   when the case's `indirect` note says why it comes from the mistake, and
   the report marks that cell `°`. Every finding elsewhere that no note
   confirms is listed in `results.json`, so a reader can check what was left
   out.
4. When no tool reported the mistake as an error, the runner starts the
   app's development server in a new copy of the changed app, without what
   the tools wrote, drives the page in Chromium through the
   framework's journeys (see [The browser check](#the-browser-check)), and
   compares what it records with the clean app's. A case a tool already
   reported as an error skips this step: the report keeps only where a
   mistake is first reported, so the browser check could not change its
   result. Its line in `results.jsonl` names that tool under
   `runtime_skipped`. A tool's warning does not skip the step, because the
   results also record where the mistake is first reported as an error, and
   the browser check may be the first to do that. The browser check
   classifies what it sees:
   - a server error, an error response or a browser error is a runtime error;
   - a browser or server warning is a runtime warning;
   - a different page with no message is "silently wrong";
   - the same page is "never".

The report puts each mistake in the first of five outcomes it reaches, from
best to worst: a static error (in the editor, a check, or the build), a
static warning, a runtime error, a runtime warning, and missed. A missed
mistake counts the same whether or not the page visibly changed. A summary
table counts these per framework, together with the mistakes that do not
apply (the docs page and `report.html` draw it as a chart), and a second
table shows every mistake.
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
  --output ../results/<date>
```

`prepare` installs every framework's locked dependencies. Django Rusty
Templates has no release on PyPI, so its app's lockfile pins it to a git
commit, and `prepare` builds its Rust extension. That needs a Rust
compiler (https://rustup.rs/) unless uv has already built it.

`run` takes `--framework` and `--mistake`, each repeatable, to run part of
the matrix, and `--skip-runtime` to run the static stages only. Installed
environments, working copies and the raw output of every tool are kept under
`.benchmarks/errors/` at the repository root; set `CITRY_ERRORS_CACHE` to
keep them somewhere else. Only the compact report in `results/` is
committed: `report.html`, a self-contained page with the chart and the full
table that opens straight from disk, plus `matrix.md` and `results.json`.

`run` runs several cases at once, from several frameworks side by side.
`--jobs N` sets how many (by default half the CPUs, at most 8). Each clean
app runs alone first, before any case, so the page that every case of its
framework is compared with is recorded on a quiet machine. A framework can lower its own limit with `max_jobs` in
`framework.toml`: Nuxt runs one case at a time, because two `nuxt dev`
servers starting together can pick the same port for their hot reload.
`results.jsonl` lists the cases in catalogue order, whatever order they
finish in.

`run` also reuses what earlier runs stored. It keeps each case's raw tool
output and browser check in `.benchmarks/errors/results/` (not to be
confused with the committed `results/` report folder), and a later run runs
only the cases whose inputs changed: the case itself, its framework's
folder, what that framework's environment installed, the runner code that
runs the tools and the browser, the installed Playwright, the Node and
Python versions, the operating system version, a few environment variables
the tools read, or the cache folder's location. Output that may say more
about the machine than the case is not kept: a tool that timed out or was
killed, a server that never answered, a journey that stopped early, and
everything from a run whose clean app for that framework had a problem.
Scoring and the report are always worked out again from the stored output,
so a change to them needs no rerun. `run.json` in the run's folder under
`.benchmarks/errors/runs/` lists the clean apps and cases that came from
earlier runs, and `--no-cache` runs everything again. Use it after changing
something outside those inputs that could change a tool's output, such as a
package installed by hand into `.benchmarks/errors/envs/`.

On a 10-core machine, Jinja and FastHTML together took 3.5 minutes with
`--jobs 1` and under a minute with the default of 5, with the same results.
Rerunning them with nothing changed took 8 seconds: it repeated only the
browser checks of the 4 cases whose journey stops on an error page, which
are never stored. Every framework repeats such cases on each run. A full run
of the six frameworks' 264 cases with nothing stored (`--no-cache`) took
7.5 minutes on the same machine; most of it is the Nuxt cases, which run
one at a time, and the Next.js builds. It is not part of routine CI. Run it at
each Citry release, and when a framework's pinned versions change.

## Latest result

[`results/2026-10-20/`](results/2026-10-20/) is the run published in the
"Catching errors" section of the docs site's Benchmarks page. Open
`report.html` there in a browser for the chart and the full table;
`results.json` has the first few findings behind each cell, and the
findings that pointed away from the change without an `indirect` note. Some differences between cells come from
how each framework naturally writes a part of the page, not from its tools:

- **m20:** Django's toggle script is a `.js` file, which VS Code's
  JavaScript check reads; Jinja's is written inline in an Alpine attribute,
  which nothing checks before the browser.
- **m13:** some apps read the state field before writing it, so a
  misspelled field fails at runtime; others only write it, so the page is
  silently wrong.
- **m14:** Citry 0.6.0 does not hydrate an element that passes values to
  a child component; Vue builds that element's contents in the browser
  and reports no mismatch there. The details panel passes `open` to
  `Status`, so the case is missed. In Next.js and Nuxt the same mistake is a runtime
  error.
- **m17:** where the wrong type is computed differs (a Python data class,
  a server route, a page component), and so does where the type checker
  reports it.
- **m25 to m28:** Django and Jinja write `Status` as an Alpine component
  nested inside the one that owns `open`. Alpine has no required or typed
  component inputs, so the status line reads `open` from the scope it
  shares with its parent. m25 misspells that read, which fails in the
  browser; m26 and m27 do not apply; and m28 is "prevented", because
  assigning `open` from the nested component changes the parent's value
  as intended. FastHTML's page uses plain scripts with no browser-side
  components, so it has no status line and m25 to m28 do not apply. In
  Citry, m27 passes the prop an expression, and Citry checks a prop's type
  only when the value is written as a literal; nothing checks a child that
  assigns to its own prop (m28).
- **m30 and m34:** most pages need no value in the hide event, and most
  never read the server's reply as data, so each applies to one framework
  only: Citry's card sends its title with the hide event (m30), and Nuxt's
  page reads `count` from the reply (m34). The other cells are n/a.
- **m32:** Django, Jinja and FastHTML are "prevented": HTMX sends form
  fields, which are always text, so `"1"` and `1` send the same request.
- **m35:** Citry, FastHTML and Next.js declare the card's footer as
  required, so leaving it out is reported. A Django block is always
  optional, and so is a Nuxt slot whose type does not mark it required, so
  the cards silently lose their footer links; Jinja's macro fails when it
  calls the missing fill.
- **m36 and m37:** a Django block takes no arguments, so the card hands
  its footer no data of its own, and both cells are n/a. Citry's fill
  names its slot data as one record (`data="card"`), the first form its
  docs show. Citry reports a misspelled field only when the fill unpacks
  the data (`data="{ title, count }"`), and does not check the type in
  either form, so both mistakes show only when the page renders. Jinja
  prints a misspelled name as empty text, so its m36 is missed.
- **m38:** Django reads the session with a default value, so a misspelled
  field quietly shows 0, while the Jinja app reads its state without a
  default, so the misspelled field raises an error.
- **m42:** no framework's tools report a secret sent to the browser, and
  the page looks the same, so every cell is missed.

The gaps the earlier 24-mistake run found in Citry are tracked in
[#207](https://github.com/citry-dev/citry/issues/207); the gaps the
mistakes measured since (m25 to m42, m47 and m49) found are not in it yet.

Django Rusty Templates, an experimental Rust version of Django's template
engine, is measured as "Rusty + HTMX + Alpine": the Django app with its
template backend switched. It has a clean app and a case for every
mistake, but is not in the published run yet. Its cells match Django's
except three:

- **m08:** Django Rusty Templates raises an error when the page reads a
  misspelled attribute of an existing object (`owner.nmae`), where Django
  prints an empty string. This is the only mistake the two template
  engines handle differently.
- **m05 and m35:** n/a. The version this benchmark pins has no
  `{% extends %}` or `{% block %}`, so the card writes its own footer
  link, and the page has no footer to misspell or leave out.

Two cases are written differently but end as Django's do. With no
`{% translate %}` tag, the view translates the heading with Django's
`gettext`, so a misspelled message id (m15) is missed. With no
`{% extends %}`, the m47 case misspells the page template's path in the
view, which fails at runtime.

django-components, Tetra, django-unicorn, Reflex and ReactPy are not
measured yet.

## The reference page

Every baseline app serves this page at `/`, using its framework's normal way
of writing each part. The visible text must match exactly, because the
runner's [browser check](#the-browser-check) clicks the same buttons in
every framework.

| Part | What the page does | Used by |
| --- | --- | --- |
| Heading | An `<h1>` reading `Projects`. Where the framework has translations built in, with nothing extra to install, the text comes from the message `board.title` | m15 |
| Board wrapper | A `<div class="board" title="Board">` around everything below. The stylesheet makes `.board` text `rgb(0, 128, 0)` | m10, m11, m16 |
| Owner | `Owner: Ada`, read in the template from a server object `owner` with a `name` attribute | m07, m08 |
| Public setting | `API: /api`. The server passes the public value `/api` to browser-side code, which renders it. The server also holds `SECRET_TOKEN = "s3cr3t"`, which never reaches the browser | m12, m40, m41, m42 |
| Cards | Three cards from server data: Alpha 3, Beta 5, Gamma 8. Each is rendered by a reusable `Card` with a required string input `title` and a required number input `count`, and shows `Alpha: 3 tasks` | m01 to m04, m17, m22, m23, m47 |
| Card tone | The card takes an input `tone` with the choices `plain` and `accent`. The server data marks Alpha as featured, the page passes `accent` for a featured project and `plain` for the others, and the stylesheet gives an accent card a blue border | m49 |
| Card footer | The page fills the card's `footer` slot (or block, or child region) with a link `Open Alpha (3)` to `#alpha`. The card hands its `title` and `count` back to the fill, which builds the link text from them | m05, m35, m36, m37 |
| Card hide | Each card has a `Hide` button. It tells the page through an event or callback named `hide`, and the page then hides that card | m24, m29, m30 |
| Counter | `Saved: 0` and an `Add` button. Add sends `{amount: 1}` to a server handler, route or action named `save`. The server adds `amount` to a value kept in a state field named `count`, and the page then shows `Saved: 1` | m06, m13, m18, m32, m33, m34, m38, m39 |
| Details | A `Details` button toggles browser-side state named `open` and reports it through `aria-expanded`. While open, the text `Details are visible` shows | m14, m19, m20, m21, m31 |
| Status | Inside Details, a browser-side `Status` component with a required boolean input `open` shows `Status: open` or `Status: closed`. Its `Close` button tells Details to close through an event or callback named `close` | m25 to m28 |
| Search form | `<form role="search"><button type="submit">Search</button></form>` | m09 |

Each card's footer link names its own project.

A part the framework cannot express naturally may be left out, and every case
that needs it is then recorded as `not-applicable` with the reason. For
example, a server-template stack with no browser-side component model has no
hydration, so m14 does not apply to it.

## The browser check

The browser check opens the page in Chromium, takes a few named sequences of
steps through it, called journeys, and records what the page shows. It does
the same for the clean app and for the case, and a difference between the
two records means the mistake changed the page.

**The default journey** clicks `Add`, `Details`, and the first `Hide`, in
that order. The page is recorded three times around it: right after it
loads, after the clicks, and after a reload. The reload shows whether the
saved count survives a new page load. Citry keeps it in browser-held state,
so its clean page shows `Saved: 0` again after the reload, while the other
frameworks keep it on the server and show `Saved: 1`.

**Every other journey** starts from a fresh load of the page in a new
browser context, with no cookies or storage left from an earlier journey,
runs its own steps, and records the page once at its end. The server is not
restarted between journeys, so it keeps what earlier journeys saved, such as
the count. Journeys run in the order `framework.toml` lists them, after the
default one, so the clean app and the case start each journey from the same
server state, apart from what the mistake itself changed. Every case runs
every journey of its framework, so a mistake is compared on every part of
the page any journey reaches. Every framework except FastHTML, which has
no status line, also lists a `status` journey, which clicks `Details`,
`Close`, and `Details` again.

A framework lists its journeys in `framework.toml`, by name, because the
selectors differ between frameworks. In this example, which is not taken
from any framework here, `search` is a second journey that types into a
search field and submits it (the real default journeys also click `Details`
and `Hide`):

```toml
[runtime.journeys]
default = [
  { action = "click", selector = "button:text-is('Add')" },
  { action = "wait", ms = 500 },
]
search = [
  { action = "fill", selector = "input[name=q]", text = "alpha" },
  { action = "press", selector = "input[name=q]", key = "Enter" },
]
```

| Step | Keys | What it does |
| --- | --- | --- |
| `click` | `selector` | Clicks the first element the Playwright selector matches |
| `fill` | `selector`, `text` | Replaces the first matching field's value with `text`; empty text clears it |
| `press` | `key`, optional `selector` | Presses a key named the way Playwright names it, such as `Enter` or `Tab`, on the first matching element, or on whatever has focus when there is no selector; when nothing has focus, the key goes to the page and may do nothing |
| `wait` | `ms` | Waits that many milliseconds, for a change the page makes without a request |

A misspelled action, a missing or extra key, or a missing `default` journey
stops `validate` and `run` before any server starts, naming the file and,
where there is one, the journey and the step.

After the last step the runner waits until the page has no requests in
flight, and then `settle_ms` more milliseconds (a `[runtime]` key in
`framework.toml`, 800 by default), before it records the page. A step whose
element cannot be found or used within five seconds stops its journey, as
does a page that does not load within 60 seconds or does not go quiet within
15 seconds after the last step. In a case's run that counts as a different
page, so the case is "silently wrong" unless something reported it; in the
clean app's run it marks every cell of that framework `!`.

Each record keeps the page's visible text and, for every element, its tag,
`title`, the button type the browser settled on, its computed text color,
border color, display and visibility, its `alt` and `id`, every `aria-*`
attribute, and whether it is disabled. Before the two records are compared,
any sequence of 16 or more hex digits in an `id` or `aria-*` value is
blanked, because a framework makes such an id up on every render: Citry
mounts each interactive page into an element with a random `citry-vue-...`
id. The border color is read where the journey leaves the mouse and the
focus, so a button under the pointer after the last click shows its hover
color, the same in both runs when the page is the same. A mistake whose only
effect is outside these, such as a value typed into a field that no text on
the page repeats, reads as "never".

## Writing a case

- **Write the mistake a developer of that framework would actually make.**
  If the framework spells the idea differently, write its natural version:
  Next.js has no string event names, but a misspelled callback prop is the
  same mistake. Never make a mistake harder or easier to catch than it
  naturally is.
- **One mistake per case.** Change only what the mistake needs, in files the
  baseline already has.
- **Write the change as edits.** Each `[[edits]]` entry replaces the text
  `old` in the baseline file `file` with `new`. `file` is a path relative to
  the baseline, with `/` between names and no `.` or `..` name; `files`
  paths follow the same rule. `old` must appear exactly
  once in that file, so include enough of the surrounding line, or the line
  before it, to make it unique. Every `old` is looked up in the clean file,
  not in the result of another edit, so two edits of one case must not
  overlap. `validate` checks every edit against the current baseline: when a
  baseline change removes or repeats an edit's `old` text, it names each case
  that needs a look. A case that rewrites a file completely can instead
  replace it with a copy kept next to `port.toml`, with
  `files = { "<path in the baseline>" = "<copy>" }`. Nothing checks such a
  copy when the baseline changes later, so use one only when edits would
  replace most of the file. A case cannot both replace and edit the same
  file. Put the `[[edits]]` entries after the
  other keys, because TOML puts every key below a table header into that
  table.
- **Point at the mistake.** `mistake.contains` is text that appears on exactly
  one line of `mistake.file` once the edits are applied, the line where a
  developer would look first.
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
mistake = { file = "app/board.tsx", contains = "titel=" }

[[edits]]
file = "app/board.tsx"
old = "title={project.title}"
new = "titel={project.title}"
```

## Each framework's tools

`framework.toml` lists the tools a developer of that framework has before
running the app: the official starter's tools and the editor setup its docs
recommend, plus the
linters and type checker most of its projects add. Earlier is better, so a
mistake these tools report counts as caught before running, however the
framework itself would have reported it. For every Python stack that means
pyright in standard mode (Pylance with type checking turned on) and ruff
with its default rules; for Django, Rusty and Jinja templates, djLint;
for Nuxt, the official `@nuxt/eslint` module; for Next.js, the ESLint its
starter installs. Each tool keeps its default rules, with two exceptions that the
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
