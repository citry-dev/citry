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

Django Rusty Templates, django-components, Tetra, django-unicorn, Reflex and
ReactPy are the next ones to add. They are named here as not yet measured;
the report covers only the six above. The choice was made before any result
was seen.

### Fairness rules

- At least half of the mistakes come from outside Citry's own rule list: from
  #158 and from what other frameworks' tools check. `citry-errors validate`
  enforces this.
- Each framework's tools are its official starter's tools plus the linters
  and type checker most of its projects add: pyright in standard mode and
  ruff for every Python stack, djLint for Django and Jinja templates, and
  ESLint for Nuxt and Next.js. A framework that relies on the language's own
  checks, such as FastHTML's typed Python functions, gets credit for what
  those checks catch. Each tool keeps its default rules. A stricter setting
  is not in the published results; it can be added later as a separately
  labeled run.
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
| A mistake has no port in some framework | `validate` lists it. In a run the cell shows `-`, so a gap is visible rather than counted |
| The clean app produces an error in some stage, or its page fails | The run continues, but every cell for that framework is marked `!`, because a case's finding could not be told apart from what was already there |
| A tool times out | The stage counts as neither a catch nor a miss. When it comes before the stage the cell shows, so that it could have reported the mistake earlier, the cell is marked `~` |
| The development server never answers | The case counts as a runtime error, because a developer starting the app would see the failure. A server that is only slower than the framework's `ready_timeout` is counted the same way, so the timeout is set well above the clean app's start time |
| A tool reports the mistake more than `window` lines from the change, or in another file | It counts only when the case's `indirect` note says why it comes from the mistake and names its rule code, and the cell is marked `°`. Otherwise it is listed in `results.json` under `unconfirmed_indirect` and does not count, because a change can also cause side-effect findings, such as a variable it left unused |
| A tool crashes on a case | The runner takes the first file and line under the working copy that the whole output names, and scores the failure like any located finding. A failure that names no such file counts only when the end of its output names the changed file; otherwise it is listed as unconfirmed, because it could be an unrelated failure such as a build that could not reach the network. A Citry app that fails to import always counts: the check imports it the same way every run and needs no network |
| A tool's output format changes | The parser finds nothing and the stage looks silent. The runner's tests cover each parser on small made-up outputs in the tools' formats, and a cell that suddenly changes after a version bump is checked against the raw output |

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
  colors, display and visibility, after the load, after the clicks and after
  a reload.** A mistake whose only effect is outside these, such as
  a broken keyboard shortcut, would read as "never".

## Cost

A full run installs each framework once, then runs every tool for every case
and starts every development server once per case. It takes tens of minutes,
most of it in the Next.js and Nuxt builds. It is not part of routine CI. Its
result changes only when a case, a pinned version or Citry changes, so it is
run at each Citry release. The runner's own tests run in seconds on small
made-up tool output and need no network.
