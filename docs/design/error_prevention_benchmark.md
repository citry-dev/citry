# Error-prevention benchmark

Status: implemented in [`benchmarks/errors/`](../../benchmarks/errors/README.md)
for issue [#158](https://github.com/citry-dev/citry/issues/158). The plan for
extending it with more mistakes and frameworks is in
[error_prevention_benchmark_plan.md](error_prevention_benchmark_plan.md).

## What it is for

Citry's main promise is that it catches mistakes before a user meets them:
typos in component, input and event names, wrong types, invalid HTML, Vue
code that reads Python-only names. The performance benchmarks say nothing
about that. This benchmark writes the same mistakes in Citry and in other
frameworks and records how early each framework reports them. The aim is to
measure the claim, and to find where Citry misses.

The README describes how a run works and how to write a case. This document
records the decisions behind it and how it behaves when something goes wrong.

## Decisions

### What is measured

For each mistake and framework the runner records the earliest of these
outcomes:

1. **Editor:** the recommended editor setup shows it.
2. **Check:** a documented check command, or a linter most projects add, reports it.
3. **Build:** the production build fails on it.
4. **Runtime error:** the server raises, returns an error status, or the
   browser logs an error.
5. **Runtime warning:** only a warning is printed.
6. **Silently wrong:** nothing reports it, and the page looks or behaves
   differently.
7. **Never:** nothing reports it, and the page looks the same.

When a tool reports a case's mistake as an error (outcomes 1 to 3), the
runner still runs every tool but skips the browser check, because nothing
the browser shows can come earlier. The case's results name the tool that
caught it. A tool's warning alone does not skip the browser check: the
results also record where the mistake is first reported as an error (see
"Warnings" below), and the browser check can still be the first to do that.
In the run of 2026-10-20, 63 of 134 cases would have skipped it, which would
have taken about 38% off the run's time.

There is no combined score across mistakes. A single number would hide which
mistakes each framework catches, the same reason the interaction benchmarks
publish separate tables
([framework_interaction_benchmarks.md](framework_interaction_benchmarks.md)).

### The open questions in #158

- **Mistakes a framework's design prevents.** These are recorded as `P`
  ("prevented") and counted separately. They are neither a catch nor a miss.
  Where the framework has a natural version of the mistake, the case uses that
  instead. Next.js has no string event names, but a developer can misspell a
  callback prop, and a type checker catching that is a real catch. This
  follows [ai_development_benchmarks.md](ai_development_benchmarks.md): record
  the property, do not invent a contrived bug.
- **Warnings.** The report keeps warnings apart from errors, both before
  running and at runtime: the chart has five outcomes (static error, static
  warning, runtime error, runtime warning, missed) plus the mistakes that do
  not apply, and the table marks a warning-only report with
  `w`. Counting only errors, or warnings like errors, would favor whichever
  framework reports at the chosen level: Citry's invalid-attribute rule is a
  warning by default, and many Vue and React problems are only
  development-mode console warnings.
- **Tool versions.** Each baseline pins exact versions in its own lockfile.
  They are bumped together, as one recorded change, at a Citry release run.
  A version bump changes what a framework catches, so the result belongs to
  the versions recorded with it.
- **Development or production runtime.** The runtime stage uses each
  framework's development server, because that is where a developer meets
  the mistake, and development builds keep the warnings that production
  builds remove. Citry always runs Vue's production build in the browser, so
  it gets no Vue warnings. That is part of its result, not an exception to the
  rule.
- **Paid editors.** PyCharm Professional's template inspections are left out
  of the published tables, because the recommended free setup is VS Code.
  They can be added later as a separately labeled run.

### Which frameworks are measured first

The first version measures Citry, Django templates with HTMX and Alpine,
Jinja with HTMX and Alpine, FastHTML, Nuxt with TypeScript, and Next.js with
TypeScript.

- The first four are the pilot group from
  [ai_development_benchmarks.md](ai_development_benchmarks.md): the server-side
  Python stacks closest to Citry.
- Nuxt and Next.js are the TypeScript frameworks with the strongest editor
  tooling. Citry's browser side is Vue, so Nuxt is its closest relative.

Six more were chosen before any result was seen: Django Rusty Templates,
django-components, Tetra, django-unicorn, Reflex and ReactPy. Django Rusty
Templates, an experimental Rust version of Django's template engine, is
measured as the Django app with its template backend switched
(`frameworks/rusty`). django-components, the project Citry grew out of, is
measured as the Django app with the page's parts turned into components
(`frameworks/django-components`). ReactPy, whose components are Python
functions that the server runs while the browser shows what they return, is
measured with its Starlette backend served by uvicorn, as in the
performance benchmark in `benchmarks/web` (`frameworks/reactpy`). Tetra, django-unicorn and
Reflex are not measured yet.

### Fairness rules

- At least half of the mistakes come from outside Citry's own rule list:
  from #158, from what other frameworks' tools check, and from the
  maintainer's list of hand-offs. That list names the places where a web
  app passes data from one part to another, such as server data into
  browser code or a browser request to a server handler, and asks at each
  one whether a misspelled name, a missing value or a wrong type is
  reported. It was written from how web apps move data, not from Citry's
  rules; entries from it that came from Citry's own rules or notes (m41,
  m42) are still marked `citry-inventory`. The list is kept as the
  hand-off matrix in section 2 of
  [error_prevention_benchmark_plan.md](error_prevention_benchmark_plan.md).
  `citry-errors validate` enforces the half.
- Each framework's tools are its official starter's tools plus the linters
  and type checker most of its projects add: pyright in standard mode and
  ruff for every Python stack, djLint for the Django, Django Rusty
  Templates, django-components and Jinja templates, and ESLint for Nuxt and
  Next.js. A framework that relies on the language's own checks, such as
  FastHTML's typed Python functions, gets credit for what those checks
  catch. Each tool keeps its default rules.
- When a framework has a setting that turns on a stricter check, and other
  frameworks here have the same kind of check, its app turns the setting on,
  so the frameworks are compared like for like (decided on 2026-10-20; see
  the plan's decisions). The framework's notes name every setting changed
  from the default. The django-components and ReactPy apps are set up this
  way; the apps measured before them are set up under the rule in a later
  change.
- Each case is written the way a developer of that framework would naturally
  make the mistake. A case is not changed after its result is seen, except to
  fix a case that did not express its mistake.
- The catalogue is frozen before a published run. Each run records the
  commit it started from and whether the benchmark folder had uncommitted
  changes, and the report prints both, so the cases it scored can be read
  back from that commit.
- A report that points away from the change counts only with an `indirect`
  note on the case. These notes are written after reading the tool output,
  so they are the one place where a result informs a case. To keep that in
  check, each note must name the mechanism (where the tool reports this kind
  of mistake) and the rule codes it covers, so it cannot let an unrelated
  finding through (a code such as `build` or `pyright`, which a tool gives
  every finding of a kind, covers that whole kind, which suits a syntax
  error that breaks the rest of the file); a reviewer other than the case's author checks every
  note; and `results.json` lists both the findings each note accepted and
  every finding elsewhere that no note covers.

### How a case changes the clean app

A case lists text edits to the baseline's files: each one replaces an `old`
text, which must appear exactly once in the clean file, with a `new` one.
The reference page will grow as mistakes are added, and each addition edits
the same files the cases change. A case that kept a full copy of such a file
would go on testing the old page without any warning. `validate` instead
reports an edit whose `old` text it cannot find exactly once, and names the
case. A case that rewrites a file completely can still replace it with a full
copy, but nothing checks that copy against later baseline changes, so a
copy is only for a case where edits would replace most of the file.

Every `old` text is looked up in the clean file, never in the result of
another edit. So the order of a case's edits does not matter, and one edit
cannot create or hide the text another one needs.

### How the browser check drives the page

The browser check takes named journeys through the page: sequences of
clicks, typing, key presses and waits. The runner records the page, meaning
its visible text and a few properties of each element, three times around
the default journey: after the load, after its clicks and after a reload.
Every other journey loads the page fresh, runs its steps and records the
page once. A form submit or a link click replaces
the page, so it gets a journey of its own instead of joining the default
one, where it would change the page that every existing case is compared on.

- **Journeys live in `framework.toml`, not in the catalogue or a case.**
  Selectors differ by framework (some match a button with `has-text`,
  others with `text-is`, and each framework writes its buttons
  differently), as do the waits a framework needs, so the
  framework owns them. A case cannot choose its journeys: every case runs
  every journey of its framework, so a case cannot skip the journey where
  its mistake shows, and a journey added later covers every existing case
  without editing it. Each journey adds one page load and its
  steps to every case of that framework.
- **Each journey starts in a new browser context**, with no cookies or
  storage from an earlier journey. The server is not restarted, so
  journeys run in a fixed order, the default one first, and the clean app
  and every case start each journey from the same server state, apart from
  what the case's mistake itself saved.
- **What a record holds.** For each element: tag, `title`, the button type
  the browser settled on, computed text color, border color, display and
  visibility, `alt`, `id`, every `aria-*` attribute, and the disabled state.
  The disabled state is what the browser applies, so `disabled="false"`
  counts as disabled, as it does for the user. A border color that neither
  the page nor the browser's defaults set follows the text color, so it
  adds a difference only where one of them sets it. It is read with the
  hover and focus the last click left behind: in FastHTML, Pico gives the
  button under the pointer another border color but the same text color.
  Two runs of the same page leave the pointer on the same element, so this
  adds a difference only when the case moves what sits under the pointer.
  Any sequence of 16 or
  more hex digits in an `id` or `aria-*` value is blanked before the
  comparison: Citry mounts each interactive page into an element whose
  `citry-vue-` id ends in 32 random hex digits, new on every render, so
  without the blanking no two Citry records would match. A mistake that
  changes only `alt`, `id`, an `aria-*` attribute, the disabled state or a
  border color reads as "silently wrong". Like "never", that counts as
  missed.

## How it behaves when something goes wrong

| Problem | What happens |
| --- | --- |
| A case (`port.toml`) replaces or edits a file the clean app does not have, or its mistake text is not on exactly one line after the edits | `validate` reports it with the case's folder, and `run` stops the whole run with an error, writing no results |
| An edit's `old` text is not in the clean file, or appears there more than once (a repeat that overlaps the first match counts) | The same: `validate` names the case and quotes the text, and `run` stops before running anything. This is how a baseline change shows which cases need a look |
| Two edits of one case change overlapping text | The same. There is no single result for two replacements of the same characters. Edits that share no characters are allowed, even when one ends where the next begins |
| A case both replaces a file with a copy and edits it, gives an edit an empty `old` text, gives one whose `new` equals its `old`, has neither edits nor copies, or gives `edits` or `files` the wrong shape | Loading fails with the file named. Each of these is a mistake in the case: edits to a copied file have no single meaning, empty text matches everywhere, and an edit that changes nothing leaves the clean app as it is |
| A case names a path that could reach outside the case's folder or the baseline: an edit's `file`, a `files` path or the copy it names is absolute, has a `.` or `..` name, a backslash, a drive letter such as `C:` or a control character, or has an empty name or one ending in a dot or space (which Windows drops) | Loading fails with the port file and the path named, so `validate` and `run` stop before writing anything. Loading also fails when a copy next to `port.toml` is a symbolic link that leads out of the case folder, or when one file is named twice with different letter case, which macOS and Windows treat as the same file |
| A baseline path passes those checks but resolves outside the baseline through a symbolic link, or lies in a folder the working copy leaves out, such as `node_modules` | `validate` names the case's folder and the path, and `run` stops before running anything. Without the first check the case's edits would be applied to a file read through the link; without the second the run would fail partway through |
| The baseline changes in a file that a case replaces with a full copy | Nothing reports it: the copy keeps the old version of the whole file, so the case tests a page that differs from the clean app in more than its mistake. Cases therefore use edits unless they rewrite most of a file |
| A `framework.toml` or `port.toml` has an unknown or missing key | Loading fails with the file and key named. A typo cannot silently change what is measured |
| A framework's journeys are not a table, have no `default` journey, or include an empty journey or one whose name does not start with a lowercase letter followed by lowercase letters, digits and `-` | Loading fails with the file and, where there is one, the journey named, so `validate` and `run` stop before any server starts |
| A step is not a table, has an unknown action, a missing key, a key its action does not use (such as `ms` on a click), an empty or non-text selector or key, text that is not a string, or an `ms` that is not a whole number above 0 | Loading fails as above, with the file, the journey and the step named. A key another action uses would otherwise be ignored without a word |
| In a case, a journey step cannot find or use its element within five seconds, or the page does not load within 60 seconds or go quiet within 15 seconds after the last step | The journey stops, the page is recorded where it stopped, and the case counts as "silently wrong" unless something reported it. The evidence holds the error, plus the journey's name for a journey other than the default. When the default journey stops, the reload record is skipped as well |
| A journey step fails in the clean app | Every cell of that framework is marked `!`, as for any other clean-app problem, because the case's journey could not be compared with a working one |
| A step leaves the page mid-navigation, so it cannot be recorded | The journey counts as failed, as above, with the reason in the record |
| A developer-written `id` or `aria-*` value contains 16 or more hex digits in a row, such as a content hash or a long number | That part is blanked like a generated id, so a mistake that changes only it reads as "never" |
| A `press` step with no selector runs when nothing has focus | The key goes to the page and may do nothing, in the clean app and the case alike, so nothing reports that the journey did less than intended |
| A framework makes up an `id` or `aria-*` value on every render in a form other than 16 or more hex digits in a row | Nothing blanks it, so the clean app and every case differ and every case of that framework that nothing reported reads as "silently wrong". It shows as that framework's "never" cells all moving to "silently wrong" in one run; the fix is to extend the blanking in `compare.py` |
| A mistake has no port in some framework | `validate` lists it. In a run the cell shows `-`, so a gap is visible rather than counted |
| The clean app produces an error in some stage, or its page fails | The run continues, but every cell for that framework is marked `!`, because a case's finding could not be told apart from what was already there |
| A tool times out | The stage counts as neither a catch nor a miss. When it comes before the stage the cell shows, so that it could have reported the mistake earlier, the cell is marked `~` |
| The development server never answers | The case counts as a runtime error, because a developer starting the app would see the failure. A server that is only slower than the framework's `ready_timeout` is counted the same way, so the timeout is set well above the clean app's start time |
| A tool reports the mistake more than `window` lines from the change, or in another file | It counts only when the case's `indirect` note says why it comes from the mistake and names its rule code, and the cell is marked `°`. Otherwise it is listed in `results.json` under `unconfirmed_indirect` and does not count, because a change can also cause side-effect findings, such as a variable it left unused |
| A tool crashes on a case | The runner takes the first file and line under the working copy that the whole output names, and scores the failure like any located finding. A failure that names no such file counts only when the end of its output names the changed file; otherwise it is listed as unconfirmed, because it could be an unrelated failure such as a build that could not reach the network. A Citry app that fails to import always counts: the check imports it the same way every run and needs no network |
| A tool's output format changes | The parser finds nothing and the stage looks silent. The runner's tests cover each parser on small made-up outputs in the tools' formats, and a cell that suddenly changes after a version bump is checked against the raw output |
| Two workers start development servers at the same moment | They get different ports. Ports come from 20000-24677: below the range the operating system gives to outgoing connections, and below 24678, where `nuxt dev` looks for a free hot-reload port (24678 to 24698). The runner keeps each port reserved until its server stops |
| Another program takes a server's port after the runner checked it was free | The server cannot listen. When its log says the address is in use, the runner starts it again on another port, trying up to three ports in all. After that the case counts as a runtime error, as for any server that never answers, and its browser check is not stored |
| Two `nuxt dev` servers start together | Each picks a port for its server-side hot reload from the same 21 ports, so both can pick the same one. Nuxt's `max_jobs = 1` runs its cases, static stages included, one at a time; other frameworks' cases still run beside the Nuxt case |
| Parallel cases slow each other down | The clean apps run alone, before any case, so the page every case is compared with is recorded on a quiet machine. A case's browser check waits a fixed `settle_ms` after the page goes quiet, so a page that is still changing after that under load can read as "silently wrong". The development server's `ready_timeout` and each tool's timeout are minutes, far above a case's normal time, but the browser's own limits are seconds (five per step, 15 for the page to go quiet), so heavy load could make a journey fail and read as "silently wrong". A run with `--jobs 1` and one with the default gave the same cells for Jinja and FastHTML; a cell that changes between the two would point at this |
| A case raises an unexpected error on its worker, such as a runner bug | No new case starts, the cases already running finish and stop their servers, and the run stops with that error and no `results.jsonl`. The cases that finished are stored, so the next run starts where this one stopped |
| The tools write into the working copy, such as a production build | The development server starts from a fresh copy of the case, so the browser check sees the same files whether the tools ran in this run or their output was stored by an earlier one |
| The run is stopped with Ctrl-C | No new case starts, and each running case stops before its next tool or browser check, so the run ends once the tools and browser checks already started have finished. Nothing that finishes after Ctrl-C is stored, because the signal also reaches the tools the running cases started. A tool killed by a signal is never stored either, whenever that happens |
| A run stops while it stores a case's output | The entry's key file is written last, so the next run finds no key, ignores the entry and runs the case again |
| A stage times out, or a tool is killed by a signal | None of the case's output is stored, because it may only show that the machine was busy, so the next run runs the case again |
| A case's development server never answers, or one of its journeys stops early | Its tool output is stored, but its browser check is not, so the next run checks the browser again: a step that ran out of time may only show that the machine was busy |
| The clean app has a problem in some stage or in its browser check | Nothing of that framework is stored in this run, neither the clean app nor its cases: a broken environment fails every case the same way, and its output must not be reused after the environment is fixed |
| A stored entry is damaged | A missing server log reruns only the browser check; an unreadable key, stage or browser-check file reruns the whole case, and the runner names the entry it ignored |
| Two runs use the same cache folder at once | The second stops at the start with a message naming the folder, because both would write the same working copies and stored output. `CITRY_ERRORS_CACHE` gives the second its own folder, which starts with no installed frameworks and no stored output |
| Something outside the stored output's key changes a tool's output: an environment variable, a package installed by hand into an environment, a system tool such as `sh`, or anything a tool reads from the network | The stored output no longer matches what the tools would print, and nothing reports it. `--no-cache` runs everything again; a run meant for publishing can use it to rule this out. The key covers the case, its framework's folder (lockfiles included) and, when a command names a file in it by absolute path, where it is, the Python version and packages its environment installed, the runner code that runs the tools and the browser, the installed Playwright (which fixes the Chromium build), the Node version and the runner's Python version, the operating system version, a few variables the tools read (`CI`, `FORCE_COLOR`, `NO_COLOR`, `NODE_ENV`, `NODE_OPTIONS`, `PYTHONWARNINGS`, `TERM`), and the cache folder's location |
| A scoring rule changes so that a stored case's static error stops counting | Whether to skip the browser check is decided again on every run, so the case gets its browser check on the next run. The stored stage output is reused |

## What could make a result wrong

- **The editor stage is measured with each engine's command-line form**
  (`tsc`, `vue-tsc`, pyright, `citry check --types`), not a running editor.
  The engines are the same, but an editor can run fewer checks (Citry's
  language server skips ty while another Python file has unsaved changes), or
  different ones. A known difference is noted in that framework's
  `framework.toml`.
- **Citry's maintainers wrote every framework's cases.** Reviewing each
  framework's cases and tools before publishing is part of the process, and
  corrections from each framework's users are invited
  ([#151](https://github.com/citry-dev/citry/issues/151)).
- **The page comparison sees text, element types, button types, tooltips,
  text and border colors, display, visibility, `alt`, `id`, `aria-*` and
  the disabled state, at the points the journeys record.** A mistake whose
  only effect is outside these, or in a part of the page no journey
  reaches, such as a keyboard shortcut no journey presses, reads as
  "never".

## Cost

A full run installs each framework once, then runs every tool for every case
and starts the development server for each case that no tool reported as an
error. Cases run side by side, `--jobs` at a time, and a run repeats only
the cases whose inputs changed since an earlier run stored them. Jinja and
FastHTML together (42 cases) took 211 seconds with `--jobs 1` and 54 seconds
with `--jobs 5` on a 10-core machine. Running every browser check as well,
one case at a time, took about 280 seconds. A rerun with nothing changed
took 8 seconds, because the browser checks of the 4 cases whose journey
stops on an error page are never stored and run again. A full run of the
eight frameworks (392 cases) with nothing stored took about 20 minutes
with the default `--jobs 5`, most of it the Nuxt cases, which run one at
a time. It is not part of routine CI. Its result changes only when a
case, a pinned version or Citry changes, so it is run at each Citry
release. The runner's own tests run in seconds on small made-up tool
output and need no network.
