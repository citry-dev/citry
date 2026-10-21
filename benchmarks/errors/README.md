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
   with none, it counts only when its message names the changed file. When
   a check fails with a Python traceback, such as `reflex compile`, its
   finding points at the traceback's last frame inside the app. A
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
as errors. A build command that prints a tool's error but still succeeds,
such as Tetra's `tetrabuild`, has that error counted as a warning, because
a CI build passes.

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

`prepare` installs every framework's locked dependencies, and builds once
what a framework's setup needs, such as Tetra's own component library.
Django Rusty Templates, an experimental Rust version of Django's template engine, has
no release on PyPI, so its app's lockfile pins it to a git
commit, and `prepare` builds its Rust extension. That needs a Rust
compiler (https://rustup.rs/) unless uv has already built it.

The Citry app measures the Citry in this repository, not a release, so a
Citry release ships with its results already measured. Its lockfile
installs citry and citry-lsp from `packages/py/`, built as a release
would be, and citry-core from PyPI at the version citry pins. A change
to citry-core's Rust code is therefore measured only once a citry-core
release has it. Each run's `run.json` lists the packages built from the
repository under `from_checkout`, and the report names them with the
run's commit.

`prepare` installs those two packages again whenever a file in their
folders changes. Before it does, it checks two things and stops when
either has changed: that the app's `uv.lock` still matches their
sources, development dependency groups included, and that the
citry-core version `frameworks/citry/baseline/pyproject.toml` installs
is still the one citry pins. To fix either, update that file and run
`uv lock` in `frameworks/citry/baseline/`.

`run` takes `--framework` and `--mistake`, each repeatable, to run part of
the matrix, and `--skip-runtime` to run the static stages only. Installed
environments, working copies and the raw output of every tool are kept under
`.benchmarks/errors/` at the repository root; set `CITRY_ERRORS_CACHE` to
keep them somewhere else. Only the compact report in `results/` is
committed: `report.html`, a self-contained page with the chart and the full
table that opens straight from disk, plus `matrix.md` and `results.json`.

`run` runs several cases at once, from several frameworks side by side,
with a separate limit for each part of a case. `--static-jobs N` sets how
many cases run their static stages at once (by default half the CPUs, at
most 8), because each tool keeps several cores busy. `--jobs N` sets how
many browser checks run at once (by default one per CPU, at most 10). Its
default is the higher of the two, because on a machine with cores to
spare a browser check spends most of its time waiting for the page. A
case waits for a free slot before each part starts. The run keeps
`--jobs` plus `--static-jobs` cases going, so every slot can be busy at
once, though a slot can still sit empty while every case waits for the
other kind. Each clean app runs alone first, before any case, so the page
that every case of its framework is compared with is recorded on a quiet
machine. A framework can limit how many of its development servers run at
once with `max_servers` in `framework.toml`: Nuxt runs one at a time,
because two `nuxt dev` servers starting together can pick the same port
for their hot reload. Nuxt's static stages start no server, so several
Nuxt cases run them side by side.
`results.jsonl` lists the cases in catalogue order, whatever order they
finish in.

`run` also reuses what earlier runs stored. It keeps each case's raw tool
output and browser check in `.benchmarks/errors/results/` (not to be
confused with the committed `results/` report folder), and a later run
runs only the cases whose inputs changed: the case itself, its framework's
folder, what that framework's environment installed (for the Citry app,
the files of citry and citry-lsp it built from this repository), the
runner code that runs the tools and the browser, the installed Playwright,
the Node and Python versions, the operating system version, a few
environment variables the tools read, or the cache folder's location.
Output that may say more about the machine than the case is not kept: a
tool that timed out or was killed, a server that never answered, a journey
that stopped early, and everything from a run whose clean app for that
framework had a problem. Scoring and the report are always worked out
again from the stored output, so a change to them needs no rerun.
`run.json` in the run's folder under `.benchmarks/errors/runs/` lists the
clean apps and cases that came from earlier runs, and `--no-cache` runs
everything again. Use it after changing something outside those inputs
that could change a tool's output, such as a package installed by hand
into `.benchmarks/errors/envs/`.

On a 10-core machine with 24 GB of memory, a full run of the twelve
frameworks' 756 cases with nothing stored (`--no-cache`) takes about 14
minutes with the default limits (10 browser checks and 5 cases' static
stages at once). The clean apps take the first 2.5 minutes, one at a time.
In the cases, each of the 417 browser checks took about 13 seconds, and
the processor was at least 95% busy in every sample taken while the cases
ran (other work on the machine took part of it), so more cases at once
would not make the run faster. Each journey loads the page again, and
every framework has five journeys (FastHTML four). When those journeys ran
one after another and five cases ran at once, a browser check took about
20 seconds, the browser checks were about 85% of the run's work (8,500 of
10,000 seconds, the rest the static stages), and the same full run took
about 38 minutes, with the same cells. A rerun with nothing changed
repeats only the browser checks whose journey stops on an error page,
which are never stored: 4 cases in Jinja and FastHTML, and a few in every
other framework. It is not part of routine CI. Run it before each Citry
release, so the release ships with its results, and when a framework's
pinned versions change.

## Latest result

[`results/2026-10-21/`](results/2026-10-21/) is the run published in the
"Catching errors" section of the docs site's Benchmarks page. Open
`report.html` there in a browser for the chart and the full table;
`results.json` has the first few findings behind each cell, and the
findings that pointed away from the change without an `indirect` note.

Each report starts by naming what the run scored: the commit it started
from and the git tree of the benchmark's inputs, which are `cases/`,
`catalogue.toml`, `frameworks/` and `runner/`. The published `results/`
folder is not an input, because it changes after the run that wrote it.
When a stack of pull requests is rebased or squash-merged, as GitHub
can do when it merges them, the commit a run names may no longer exist
on the branch; the tree id stays the same as long as the inputs do. To check that a commit has the inputs
a published run scored, work out its tree id and compare:

```bash
git ls-tree --full-tree <commit>:benchmarks/errors \
  cases catalogue.toml frameworks runner | git mktree
```

`run.json` also says whether those inputs had uncommitted changes when
the run started (`inputs_changed`); then no commit has them.

"Citry" is a FastAPI app that renders the pages from its own routes and
adds Citry's routes with `citry.contrib.fastapi.mount()`, as Citry's
FastAPI starter does.
"Rusty + HTMX + Alpine" is the Django app with its templates rendered by
[Django Rusty Templates](https://github.com/LilyFirefly/django-rusty-templates),
an experimental Rust version of Django's template engine.
"django-components + HTMX + Alpine" is the Django app with the card, the
counter, the status line and the page rewritten as components of
[django-components](https://github.com/django-components/django-components),
the Django library Citry grew out of. "ReactPy" is
[ReactPy](https://github.com/reactive-python/reactpy), a Python library
for React-style components: the server runs them in Python and sends the
browser the page to show over a WebSocket. "django-unicorn" is the
Django app with its interactive parts rewritten as components of
[django-unicorn](https://www.django-unicorn.com/), which sends each click
to the server and replaces the component's HTML with the HTML the server
sends back. "Tetra" is the Django app with its interactive parts
rewritten as components of [Tetra](https://www.tetraframework.com/),
whose components the server renders and whose Alpine code in the browser
calls their Python methods on the server. "Reflex" is
[Reflex](https://reflex.dev/), which compiles components written in Python
into a React app that talks to a Python backend over a WebSocket.

Some differences between cells come from how each framework naturally
writes a part of the page, not from its tools:

- **m20:** the Django, Rusty and django-components apps' toggle script
  is a `.js` file, which VS Code's JavaScript check reads; Jinja's is
  written inline in an Alpine attribute, which nothing checks before the
  browser.
- **m13:** some apps read the state field before writing it, so a
  misspelled field fails at runtime; others only write it, so the page is
  silently wrong.
- **m14:** Citry does not hydrate an element that passes values to
  a child component; Vue builds that element's contents in the browser
  and reports no mismatch there. The details panel passes `open` to
  `Status`, so the case is missed. In Next.js and Nuxt the same mistake is a runtime
  error.
- **m17:** where the wrong type is computed differs (a Python data class,
  a server route, a page component), and so does where the type checker
  reports it.
- **m25 to m28:** Django, Rusty and Jinja write `Status` as an Alpine
  component nested inside the one that owns `open`. Alpine has no required
  or typed component inputs, so the status line reads `open` from the
  scope it shares with its parent. m25 misspells that read, which fails in
  the browser; m26 and m27 do not apply; and m28 is "prevented", because
  assigning `open` from the nested component changes the parent's value as
  intended. FastHTML's page uses plain scripts with no browser-side
  components, so it has no status line and m25 to m28 do not apply. In
  Citry, `citry check` and the editor report all four, including text
  bound to the boolean prop (m27) and a child that assigns to its own prop
  (m28).
- **m30 and m34:** most pages need no value in the hide event, and most
  never read the server's reply as data, so m30 applies to three
  frameworks and m34 to one: Citry's, Tetra's and django-unicorn's cards
  send their title when they ask to be hidden (m30), and Nuxt's page reads
  `count` from the reply (m34). The other cells are n/a.
- **m32:** Django, Rusty, Jinja, django-components and FastHTML are
  "prevented": HTMX sends form fields, which are always text, so `"1"`
  and `1` send the same request. django-unicorn is "prevented" too: it
  converts an action's argument to the type the method declares, so
  `save(amount='1')` calls `save(amount=1)`, and so is Reflex, which
  converts an event's argument the same way. Tetra passes the text to the
  method unchanged, so adding it to the total fails with a server error.
- **m35:** Citry, FastHTML, Reflex and Next.js declare the card's footer
  as required, so leaving it out is reported before the app runs;
  django-components declares it required too, and reports it when the page
  renders. A Django block is always optional, and so is a Nuxt slot whose
  type does not mark it required, so the cards silently lose their footer
  links; Jinja's macro fails when it calls the missing fill.
- **m36 and m37:** a Django block takes no arguments, so the card hands
  its footer no data of its own, and both cells are n/a. Citry's fill
  names its slot data as one record (`data="card"`), the first form its
  docs show. The editor, measured with `citry check --types`, checks
  `card` against the data type the slot declares and reports both the
  misspelled field (m36) and the number joined to text (m37). Jinja's
  m36 is an error when the page renders, because its app turns on
  `StrictUndefined` (see [Each framework's tools](#each-frameworks-tools)).
- **m38:** Django, Rusty and django-components read the session with a
  default value, so a misspelled field quietly shows 0, while the Jinja
  app reads its state without a default, so the misspelled field raises
  an error.
- **m42:** no framework's tools report a secret sent to the browser, and
  the page looks the same, so every cell is missed.
- **m43:** Nuxt reports a CSS variable whose name differs from the one
  the server sets. Its page reads the server's value with Vue's
  `v-bind('board?.accent')`, so the misspelled name reads a property the
  board data does not have, which vue-tsc reports. `citry check` and
  the editor warn that nothing sets `--acent` and suggest the
  `css_data()` key.
  Elsewhere the heading silently changes color.
- **m44:** Citry's form sends its fields to a server event, and `citry
  check` and the editor compare the field names with the ones the event
  declares, so they report `qeury`. Elsewhere nothing compares a form
  field's name with the name the server reads, so the search shows no
  `Searched:` line. In Reflex the search handler reads the field by name,
  so the misspelling raises a `KeyError` on the server.
- **m45, m48 and m61 in Citry:** both `citry` stages load the app from
  `app.main`, the module that calls `mount()`, so `citry check` asks
  FastAPI which pages and files the app serves and warns about the
  misspelled page and image (`citry.template.unknown-url`); the browser
  still gets the 404. The rule does not check a parameter type that only
  the route function declares, so m61 is first reported by FastAPI's
  422.
- **m45:** Django, Rusty, Jinja, Tetra, django-unicorn and
  django-components build the link from the route's name, so the page fails to render.
  Next.js's `typedRoutes` checks a link's path against the app's routes,
  so the editor reports it. Citry and FastHTML link by path and get a 404
  when the link is clicked. Nuxt's `typedPages` checks a link given by
  route name, but the page links by path, as Nuxt's routing docs show
  first, so its router prints only a warning in the browser. ReactPy's
  router changes the page in the browser, so the link shows the app's
  catch-all `Page not found` route, and nothing reports an error.
- **m46:** Citry checks a message's arguments in the editor. In Django,
  Tetra, django-unicorn and django-components, `{% blocktranslate %}`
  leaves the owner's name out, so the subtitle reads `Owned by ` with no
  error, while Rusty's view fills the gettext placeholder from a
  dictionary and raises a `KeyError`. The other frameworks have no
  translations built in, as for m15.
- **m48:** the misspelled image is a 404 when the page loads, except in
  Nuxt, whose build turns an image path in a template into an import and
  fails on the missing file, and in Reflex, whose development server
  answers with the app's page and status 200.
- **m50:** each card reads the board's name that the page shares with
  it, and the case misspells the key or name the card reads. Citry's and
  django-components' `inject()` raise an error for a key that no
  component above provides, and Jinja's app turns on `StrictUndefined`,
  so the page fails to render. Django, Rusty, Tetra and django-unicorn
  print a misspelled template variable as empty text, so the cards show
  `Board:` with no error. Nuxt's page provides the name under a string
  key, which vue-tsc does not check, so the cards show `Board:` and Vue
  prints only a warning that the injection was not found. In Next.js
  and ReactPy the context is a variable in the code, so a misspelled one
  is an undefined name, which the editor reports. In Reflex the name is
  a field of a state class, and pyright reports the misspelled field.
  FastHTML has no way to share the value except as an argument, so its
  cell is n/a.
- **m51:** a list key matters only where the browser updates the list in
  place. The Django, Rusty, django-components, Jinja and FastHTML pages
  render the cards on the server and only hide one in the browser, so
  the cell is n/a. Next.js's and Nuxt's ESLint rules report the missing
  key, and ReactPy's debug mode prints a warning. `citry check` and the
  editor report the missing `#c-key` before the app runs.
  django-unicorn reports nothing, and clicking Hide on the first card
  leaves Alpha on the page. Tetra reports nothing either: without a key,
  every card resumes from the same saved state when the list renders
  again, so after Hide both cards left show the title Gamma. Reflex
  keys each card by its position when it has no key of its own, and its
  cards keep no state in the browser, so nothing reports the missing key
  and the page looks the same.
- **m52:** only Nuxt and Citry report a `<div>` inside a `<p>` before the
  app runs: Nuxt's ESLint fails to parse the template, and `citry check`
  and the editor report the nesting. Next.js reports it in the browser as
  a hydration error, and React reports it in the browser in Reflex too.
  Elsewhere the browser splits the paragraph without a message.
- **m53, m54, m56 and m57:** djLint checks alt text (H013), ARIA
  attribute names (H048), repeated attributes (H037) and repeated ids
  (H053) in the Django, Rusty, django-components, Jinja, Tetra and
  django-unicorn templates (in Tetra, the page template; its components'
  templates are Python strings). It checks ARIA names only on plain
  attributes, so it misses the `:aria-expandd` binding of the Alpine
  apps (Django, Rusty, django-components and Jinja), never reads Tetra's
  details component, which is a Python string, and reports
  django-unicorn's plain `aria-expandd`. Next.js's next/image requires
  `alt` in its types, and its ESLint warns about a misspelled ARIA name,
  which React also reports in the browser. Nuxt's `strictTemplates`
  reports the unknown ARIA name. In Reflex, pyright reports the class
  given twice, because a repeated keyword is a Python syntax error, and
  React reports the misspelled ARIA name in the browser; nothing reports
  the missing alt text. `citry check` and the editor warn about the
  missing alt text and report the misspelled ARIA name even though it
  is bound (`:aria-expandd`), the repeated attribute and the repeated
  id. Nothing reports a repeated id
  in Next.js, Nuxt, FastHTML, ReactPy or Reflex.
- **m55:** a bound `aria-expanded` is typed as `true` or `false` in
  TypeScript, so Citry, Next.js and Nuxt report `yes` and `no` in the
  editor. The Alpine apps, Tetra's included, django-unicorn's `yesno`
  filter, FastHTML's script, ReactPy's attribute dictionary and Reflex's
  `aria_expanded` accept any text.
- **m58 and m59:** a loop over a number and a misspelled length filter
  or helper are type errors where the template is checked as code
  (Citry, Next.js, Nuxt, FastHTML and ReactPy). In the Django, Rusty,
  django-components, Jinja and django-unicorn templates they fail when
  the page renders. So does Tetra's loop, but Tetra compiles every
  component's template when Django starts, so the misspelled filter in
  its card list's template fails `manage.py check`. In Reflex, pyright
  reports the misspelled `length()`, and only `reflex compile` reports
  the loop over a number, because pyright cannot see the type of a field of
  a project inside the list.
- **m60:** a handler that takes one more argument than the card's event
  sends is a type error in Next.js, Nuxt, ReactPy and django-unicorn.
  Next.js reports it on the handler itself. Nuxt, ReactPy and
  django-unicorn report it where the handler is called or returned, so
  those three cells are marked `°`. In Reflex, pyright reports it too,
  where the page passes the event to the card, so its cell is marked `°`
  as well. Citry's handler is a method in the page's browser code, which
  `citry check --types` type-checks with TypeScript, but nothing compares
  its parameters with what the card's `hide` event sends. FastHTML's
  handler is browser JavaScript, which nothing checks. In both, the
  missing reason only prints as `undefined`. The Django, Rusty,
  django-components and Jinja apps hide a card with an inline statement,
  so the cell is n/a. Tetra's handler is a Python method that
  `@public.listen` subscribes to the event; when the class is defined,
  Tetra checks that such a method takes exactly one argument, so the
  second argument fails `manage.py check`.
- **m61:** the project route takes a numeric id. Django, Rusty,
  django-components, django-unicorn, Tetra and Jinja build the link from
  the route's name, and building it with `alpha` fails when the page
  renders. Citry's FastAPI route and FastHTML's route check the number
  only when the link is followed: FastAPI answers with a 422 validation
  error, and FastHTML with a 404. ReactPy's router shows the app's
  `Page not found` route and Nuxt's route check shows Nuxt's 404 page,
  both in the browser and with no error, and Next.js's and Reflex's
  route parts take any text, so their pages read `Project alpha`.
- **m62:** TypeScript in Next.js, pyright in Reflex, and `citry check` and
  the editor in Citry report `disabled="false"`; Nuxt's types accept the
  text. Everywhere else the search button is silently disabled.
- **m63:** Nuxt's vue-tsc and ESLint report a `v-model` on the form,
  and so do `citry check` and the editor. `reflex
  compile` reports that a form has no `on_change` event, at the first
  line of the form's call, so Reflex's cell is marked `°`. In the other
  apps nothing reports the binding. Alpine's `x-model` and React's
  `onChange` in Next.js read the value from the field's `input` event,
  which bubbles up to the form, so typing still updates the line; only
  the state no longer flows back into the field, which the page never
  needs. django-unicorn and FastHTML read a value from the form itself,
  which a form does not have, so the line stops following the typing.
  The browser check cannot show the difference: the `search` journey
  records the page only after the form is submitted, which loads the
  page again or, in Citry, renders the search form again, so only
  Next.js's record still shows the typed text; ReactPy's record, like
  the others, shows no difference. Whether or not the line follows the
  typing, these cells read "never" and count as missed.

[#207](https://github.com/citry-dev/citry/issues/207) tracks the gaps
the first 24 mistakes found in Citry; the later gaps m30, m50, m60 and
m61 are not in it yet.

Rusty's cells match Django's except four:

- **m08:** Django Rusty Templates raises an error when the page reads a
  misspelled attribute of an existing object (`owner.nmae`), where Django
  prints an empty string. This is the only mistake the two template
  engines handle differently.
- **m46:** with no `{% blocktranslate %}`, Rusty's view fills the
  subtitle's gettext placeholder from a dictionary, so the misnamed
  argument raises a `KeyError`; Django's tag prints the name as empty
  text.
- **m05 and m35:** n/a. The version this benchmark pins has no
  `{% extends %}` or `{% block %}`, so the card writes its own footer
  link, and the page has no footer to misspell or leave out. For the
  same reason the page fills nothing in the card, so m36 and m37 are n/a
  in both apps.

Two cases are written differently but end as Django's do. With no
`{% translate %}` tag, the view translates the heading with Django's
`gettext`, so a misspelled message id (m15) is missed. With no
`{% extends %}`, the m47 case misspells the page template's path in the
view, which fails at runtime.

django-components' cells differ from Django's in these places
([`frameworks/django-components/`](frameworks/django-components/) holds
its app and notes):

- **m02, m04, m05 and m35:** django-components checks each component's
  inputs and slots when it renders, so a misspelled or missing input or
  slot gives a server error on the first page load, where the Django app
  shows a different page with no error. Nothing reports these before the
  app runs.
- **m03 and m49:** the wrong-typed input and the misspelled `tone` choice
  give a server error on the first page load, but only because the app
  turns on django-components' documented type checking (Pydantic models
  with the djc-ext-pydantic extension), following the rule on stricter
  settings below. Without it, the card would show the text `card.count`
  in place of the number, and the first card would silently lose its
  border.
- **m12:** the page's script reads values only from the data
  `get_js_data()` sends it, so reading a `secret_token` that was never sent
  leaves the API line blank, with no error. The Django app's script looks
  the value up by element id and fails when the element is missing.
- **m36 and m37:** unlike a Django block, a django-components slot hands
  data to its fill (`{% slot "footer" title=title count=count %}`), which
  the fill reads through `data="footer"`, so both mistakes apply. Nothing
  checks what a template fill reads from that data, so a misspelled field
  prints as empty text and a count joined with text through `add` prints
  an empty value in place of the count; both are missed.
- **m50:** the page provides the board's name with `{% provide %}`, and
  the card's `inject()` raises an error for the misspelled key, so the
  page fails to render. The Django app's card reads a template variable
  that the include passes on, which prints as empty text when misspelled.

m25 to m28 end as in the Django app. django-components hands a component
its inputs once, when the server renders it, and `open` changes in the
browser, so the Status component's markup is still the Django app's
nested Alpine component.

In ReactPy ([`frameworks/reactpy/`](frameworks/reactpy/) holds its app
and notes) the server runs every component in Python and sends the
browser the elements to show over a WebSocket, and a click runs a Python
handler on the server. The main differences from FastHTML's cells, the
other framework here that writes its page as Python functions:

- **m02, m04, m05, m25, m26, m29 and m35:** ReactPy's `@component`
  decorator is typed so that pyright accepts any arguments in a call to a
  component. A misspelled or missing input, footer or callback raises a
  `TypeError` only when the component renders, which shows as a server
  error, with the error text in place of the component (debug mode is on;
  without it the component is empty). FastHTML's components are plain
  typed functions, so pyright reports m02, m04, m05 and m35 in the editor;
  FastHTML has no status line (m25, m26) and misses m29.
- **m37:** for the same reason the page's footer lambda gets no parameter
  types, so treating `count` as text fails only when the card renders.
- **m17, m27 and m49:** nothing checks an argument's type or allowed
  choice, before or while the app runs. A count passed as text prints the
  same text, so m17 is missed; a status line given text in place of a
  boolean (m27) and the misspelled `tone` (m49) change the page without an
  error.
- **m28:** the status line's click handler assigns `False` to `open`,
  which in Python makes a new local name, and ruff reports that the name
  is never used. FastHTML has no status line.
- **m18, m32 and m33:** the Add button's handler runs on the server and
  calls `save(amount=1)`. The amount is a Python argument, not a field
  in a request, so pyright reports a misspelled, wrong-typed or missing
  amount in the editor.
- **m06, m24 and m47:** the Add button's handler, the card's hide
  callback and the card's module are Python names, so pyright reports a
  misspelled one in the editor. FastHTML names its handler by URL and its
  hide event by a string, so it reports m06 only at runtime and misses
  m24, and its page has no second file to import.
- **m19 and m20:** the conditional that shows the details text and the
  toggle's click handler are Python code, so their syntax errors are
  Python syntax errors, which pyright and ruff report.
- **m45:** the About link goes through ReactPy-Router, which changes the
  page in the browser. A link to a misspelled path shows the app's
  catch-all `Page not found` route, and nothing reports an error, where
  FastHTML's link gets a 404 from the server.
- **m12 and m40:** the API line is a ReactPy JavaScript component that
  reads the API base from its props. Reading a prop the server did not
  pass shows `API: undefined` with no error. (A second prop that carries
  the secret, m42, reaches the browser unnoticed, as in every framework.)
- **m50:** the page shares the board's name through a ReactPy context,
  and pyright and ruff report the misspelled name of the context in the
  editor.
  FastHTML has no way to share it, so its cell is n/a.
- **m51:** ReactPy updates the card list in the browser, so leaving out
  the key applies here, and debug mode prints a warning for it.
  FastHTML's server-rendered list has no keys, so its cell is n/a.
- **m56:** the repeated `class_name` is a repeated key in a Python
  dictionary, which ruff reports and Python accepts, keeping the last
  value. FastHTML's repeated `cls=` keyword is a syntax error, which
  pyright reports in the editor.
- **m60:** the card's `on_hide` callback is typed, so pyright reports
  a hide handler that takes a reason where `make_hide` returns it.
  FastHTML's hide listener is browser JavaScript, which nothing checks.
- **m61:** the router checks the project id in the browser and shows the
  app's `Page not found` route with no error, while FastHTML's route
  answers `/projects/alpha` with a 404.

m14 and m34 are n/a, as in FastHTML and the Django and Jinja apps:
ReactPy 1.1.0 renders nothing on the server, and no browser code reads a
reply to the click. m46 is n/a as in FastHTML, because ReactPy has no
translations.

The django-unicorn app ([`frameworks/unicorn/`](frameworks/unicorn/)
holds it and its notes) is the Django app with the cards, the counter,
the details with their status line, and the search form turned into
[django-unicorn](https://www.django-unicorn.com/) components. Each click
sends the component's state to the server, which runs a Python method
and sends back the component's new HTML, so the page loads neither HTMX
nor Alpine. The saved count lives in the page, not in the session, so
after a reload the page shows `Saved: 0`, as Citry's does. Its cells
differ from Django's in these places:

- **m06:** django-unicorn ignores a click whose action names a method
  the component does not have, and prints nothing, so a misspelled `save`
  leaves the count at 0, where the Django app's `{% url %}` fails.
- **m21:** the details text is shown with Django's `{% if %}` tag, so the
  misspelled tag leaves its `{% endif %}` without a match, which djLint
  reports. The Django app's case misspells Alpine's `x-show`, which
  nothing checks.
- **m24, m29 and m30:** pyright reports all three. The card asks the card
  list to hide it from Python, through `self.parent` as django-unicorn's
  docs show, after checking that the parent is the card list. So pyright
  sees the call, its method name and its argument. The Django app sends an
  Alpine event that nothing checks, and its event carries no value, so its
  m30 is n/a. Written with django-unicorn's `$parent.hide(...)` in the
  markup instead, the three cases would be missed. pyright reports m29 at
  the call in the card, so its cell is marked `°`.
- **m39:** the saved total is a typed field of the counter component, so
  pyright reports text stored in it. The Django app keeps the total in
  the session, which nothing checks.
- **m25 to m28:** the status line is a django-unicorn component that
  receives `open` from the details each time the server renders them
  again, so all four mistakes can be written, where the Django app's
  Alpine version has no inputs (m26, m27) or shares its parent's state
  (m28). django-unicorn checks neither the names nor the types of a
  component's inputs, so all four are missed. The Django app's m25 is a
  browser error instead, because its Alpine markup reads the undefined
  name `opne`; here the value is stored under the misspelled name, which
  nothing reads.
- **m05, m20 and m35:** n/a. django-unicorn has no slots, so the card
  writes its own footer link and the page fills nothing in it. No
  JavaScript defines the toggle: the Details button uses django-unicorn's
  built-in `$toggle('open')` action.
- **m51:** the card list renders each card as a child component, with
  the `key` django-unicorn's docs give a child in a loop, so the
  mistake applies. Nothing reports it, and clicking Hide on the first
  card leaves Alpha on the page. The Django app's cards are plain
  server-rendered markup, so its cell is n/a.
- **m54:** the Details button writes `aria-expanded` as a plain
  attribute, so djLint's H048 reports the misspelled name. The Django
  app binds it with Alpine's `:aria-expanded`, which djLint does not
  read as an ARIA attribute.
- **m60:** the card list's `hide` method is called from Python, so
  pyright reports the missing reason at the card's `self.parent.hide(...)`
  call (marked `°`). The Django app's Alpine wrapper hides itself with
  an inline statement, so its cell is n/a.

m42 is missed as everywhere, but in django-unicorn's own form: the counter
keeps the token as an ordinary class attribute, and django-unicorn writes
every public attribute of a component into the page for its browser
script.

The Tetra app ([`frameworks/tetra/`](frameworks/tetra/) holds it and its
notes) is the Django app with the API line, the
card list, the cards, the counter, the details with their status line and
the search form turned into [Tetra](https://www.tetraframework.com/)
components. Each component is a Python class whose template and script
are strings in the class. The server renders it, and in the browser it
becomes an Alpine component. Its Alpine code can call the class's public
methods on the server. The attributes it declares with `public(...)`, its
public attributes, are Alpine data in the browser, and they travel back
to the server with each such call. A page passes a component its
values in the component's tag, such as `{% Card title=... %}`, and Tetra
hands them to the component's `load()` method when it renders it. The
saved count lives in the page, as in django-unicorn, so after a reload the
page shows `Saved: 0`. Its cells differ from Django's in these places:

- **m01 and m59:** the card list uses the card as a template tag,
  `{% Card %}`, and counts the cards with `|length` in its own template,
  because only the card list holds the cards. Tetra compiles every
  component's template when Django starts, so the misspelled tag and the
  misspelled filter fail `manage.py check`. The Django app's misspelled
  `{% include %}` and filter fail only when the page renders.
- **m02 and m04:** a misspelled or missing `title` in the card's tag
  leaves `load()` without its `title` argument, so it raises a
  `TypeError` when the page renders, where the Django app's page shows no
  title and no error.
- **m18:** n/a. Tetra sends a public method's arguments in order, with
  no names, so the request has no field to misspell.
- **m20 and m22:** the details' script and the card's template are
  strings in the component's Python class, as Tetra's tutorial writes
  them, so neither VS Code's JavaScript check nor djLint reads them. Tetra
  builds the scripts with esbuild, a JavaScript bundler, when its build
  command, `manage.py tetrabuild`, runs. The script's syntax error makes
  the command print esbuild's error, but the command still exits
  successfully, so the build stage counts it as a warning (m20). The
  error points at a copy of the script Tetra makes for esbuild, so the
  cell is marked `°`. The unclosed element is missed (m22). The Django
  app's script and template are files, which those tools check.
- **m30 and m32:** the card sends its title with the `hide` event, so
  m30 applies. The case sends the card's count instead, and the card
  list stores that number in `hidden`, which is declared as a list of
  strings. Tetra checks public attributes against their declared types
  when it writes a component's state into the page, so the call fails
  with a server error. In the m32 case the Add button calls `save('1')`,
  and Tetra passes the text on unchanged, so adding it to the total fails
  with a server error. In the Django app, HTMX sends the amount as form
  text and the view converts it with `int()`, so its m32 is prevented.
- **m36 and m37:** Tetra renders a slot's content with the card's own
  variables, so the fill reads the card's `title` and `count`, and both
  mistakes apply. Tetra's docs do not describe this; passing the list's
  `card` to the fill instead, which they do describe, would make both
  n/a, as in the Django app. Nothing checks what a fill reads, so both
  are missed.
- **m39:** the saved total is a typed public attribute of the counter, so
  pyright reports text stored in it. The Django app keeps the total in
  the session, which nothing checks.
- **m51:** the card list renders each card as a component and renders
  the list again on the server after Hide, so a key matters. Without
  one, every card resumes from the same saved state, and after Hide
  both cards left show the title Gamma, with no message. The Django app's
  cell is n/a.
- **m60:** the card list's `hide` handler is a method that
  `@public.listen` subscribes to the card's event. When the class is
  defined, Tetra checks that such a method takes exactly one argument,
  so a second argument fails `manage.py check`. The Django app
  hides a card with an inline statement, so its cell is n/a.

m30 and m41 are runtime errors (m41 is one in the Django app too), but in
Tetra only because the app gives its public attributes types, following
the rule on stricter settings below. In a trial run without the types on
`api_base` and `hidden`, both were missed.


In Reflex ([`frameworks/reflex/`](frameworks/reflex/) holds its app and
notes) the page is written as Python functions, as in ReactPy, but Reflex
compiles them into a React app. Its development server serves that app
with Vite, and the browser sends each click to a Python backend over a
WebSocket. pyright, ruff and `reflex compile` report 38 of its 54 ported
mistakes before the app runs, so only 16 cases needed the browser check.
Where its cells, or the reason behind them, differ from ReactPy's:

- **m02, m04, m05, m25, m26, m29 and m35:** the card and the status line
  are plain typed Python functions, so pyright reports a misspelled or
  missing input, footer or callback in the editor, where ReactPy's
  `@component` hides them until the component renders.
- **m17, m27 and m49:** pyright also checks the types of those inputs,
  including the `Literal` choices of `tone`.
- **m08 and m31:** only `reflex compile` reports them. pyright accepts any
  attribute of a state field that holds an object, such as `owner.nmae`,
  and any keyword on a component, such as `on_clik`; Reflex's compile step
  checks both.
- **m13:** pyright accepts an assignment to any attribute of a state in
  an event handler, because Reflex's state class defines `__setattr__`,
  so `self.cuont += amount` fails only when Add is clicked.
- **m10:** Reflex passes a keyword it does not know, such as `titel`, on
  as a CSS property, so the board silently loses its tooltip.
- **m12:** the page reads the backend-only field that holds the secret,
  and Reflex writes its value into the compiled page, so the API line
  shows the secret with no error.
- **m44:** the search handler reads `form_data["q"]`, so a misspelled
  field name raises a `KeyError` on the server when the form is
  submitted; ReactPy reads the URL and silently shows no `Searched:` line.
- **m45:** Reflex's router shows its own `404: Page not found` page in the
  browser, with no error.
- **m48:** in development, React Router's handler in the Vite server
  answers a misspelled file path with the app's page and status 200, so
  the image shows broken, nothing reports an error, and the case reads
  as "silently wrong".
- **m09:** pyright reports `type="sumbit"`, because Reflex types a
  button's `type` as its allowed values; `reflex compile` reports it too.
- **m21:** the conditional is the component `rx.cond`, so pyright reports
  a misspelled `rx.cnod`; ReactPy writes the condition as plain Python,
  so its cell is n/a.
- **m37:** the footer gets the count as a typed `Var[int]`, so pyright
  reports joining it to text with `+`.
- **m40:** the API line reads a typed state field, so pyright reports the
  misspelling.
- **m18, m32 and m41:** prevented. Reflex builds an event's payload from
  the handler's own parameter names, so the page never writes the field
  name `amount`; it converts the text `"1"` to the number the handler
  declares, as django-unicorn does; and it sends a `pathlib.Path` to the
  browser as its text.

m03, m14, m15, m30, m34 and m46 are n/a, for the same reasons as in
ReactPy: the inputs are Python arguments, nothing is rendered on the
server, Reflex has no translations, the hide event already carries the
card's title, and no browser code reads the reply to a click. m51 to m63
are described with the other frameworks above.

## The reference page

Every baseline app serves this page at `/`, using its framework's normal way
of writing each part. The visible text must match exactly, because the
runner's [browser check](#the-browser-check) clicks the same buttons in
every framework.

| Part | What the page does | Used by |
| --- | --- | --- |
| Heading | An `<h1>` reading `Projects`. Where the framework has translations built in, with nothing extra to install, the text comes from the message `board.title`. The server sets its color, blue, as the CSS variable `--accent`, which the stylesheet reads (Nuxt's stylesheet reads the server's value with Vue's `v-bind()` instead). This is unrelated to the card's `accent` tone | m15, m43, m57 |
| Subtitle | `Owned by Ada` under the heading. Where translations are built in, it comes from a message that takes the owner's name as an argument | m46 |
| Board wrapper | A `<div class="board" id="board" title="Board">` around everything below. The stylesheet makes `.board` text `rgb(0, 128, 0)` | m10, m11, m16, m56, m57 |
| Avatar | An `<img>` of the owner from the app's static files, `avatar.svg`, with the alt text `Ada` | m48, m53 |
| Owner | `Owner: Ada`, read in the template from a server object `owner` with a `name` attribute | m07, m08, m52 |
| Project count | `Projects: 3`, counted in the template with the template language's length filter or helper (`projects.length` in JavaScript) | m59 |
| Public setting | `API: /api`. The server passes the public value `/api` to browser-side code, which renders it. The server also holds `SECRET_TOKEN = "s3cr3t"`, which never reaches the browser | m12, m40, m41, m42 |
| Cards | Three cards from server data: Alpha 3, Beta 5, Gamma 8. Each is rendered by a reusable `Card` with a required string input `title` and a required number input `count`, and shows `Alpha: 3 tasks`. Where the framework matches list items by key when it updates the list in place, each card has a key made from its project | m01 to m04, m17, m22, m23, m47, m51, m58 |
| Card tone | The card takes an input `tone` with the choices `plain` and `accent`. The server data marks Alpha as featured, the page passes `accent` for a featured project and `plain` for the others, and the stylesheet gives an accent card a blue border | m49 |
| Card footer | The page fills the card's `footer` slot (or block, or child region) with a link `Open Alpha (3)` to `#alpha`. The card hands its `title` and `count` back to the fill, which builds the link text from them | m05, m35, m36, m37 |
| Board name | Each card shows `Board: Projects` under its title. The page makes the board's name available to everything inside it without passing it to each card as an input, in the framework's own way: provide/inject, a React context, a template context that included templates, imported macros and components read, or shared state. FastHTML has no such way, so its cards leave the line out | m50 |
| Card hide | Each card has a `Hide` button. It tells the page through an event or callback named `hide`, and the page then hides that card | m24, m29, m30, m60 |
| Counter | `Saved: 0` and an `Add` button. Add sends `{amount: 1}` to a server handler, route or action named `save`. The server adds `amount` to a value kept in a state field named `count`, and the page then shows `Saved: 1` | m06, m13, m18, m32, m33, m34, m38, m39 |
| Details | A `Details` button toggles browser-side state named `open` and reports it through `aria-expanded`. While open, the text `Details are visible` shows | m14, m19, m20, m21, m31, m54, m55 |
| Status | Inside Details, a browser-side `Status` component with a required boolean input `open` shows `Status: open` or `Status: closed`. Its `Close` button tells Details to close through an event or callback named `close` | m25 to m28 |
| Search form | `<form role="search">` with a search field named `q` and `<button type="submit">Search</button>`. A line `Searching for: ...` repeats what is typed, and submitting `alpha` shows `Searched: alpha` | m09, m44, m62, m63 |
| Links | An `About` link to the route `about` at `/about`, whose page reads `About this board`, and a `Project 1` link to `/projects/1`, whose page reads `Project 1`. The project route takes a numeric id, declared as a number where the router can | m45, m61 |

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
saved count survives a new page load. Citry, django-unicorn and Tetra
keep the count in the page, and ReactPy keeps it in component state on the server,
which lasts only while that page is open. So their clean pages show
`Saved: 0` again after the reload, while the other frameworks keep the
count on the server and show `Saved: 1`. Reflex keeps it in state on the
server for each browser tab, and a reload stays in the same tab, so it
shows `Saved: 1` too.

**Every other journey** starts from a fresh load of the page in a new
browser context, with no cookies or storage left from an earlier journey,
runs its own steps, and records the page once at its end. The server is not
restarted between journeys, so FastHTML, Jinja, Next.js and Nuxt, which
keep the count in server memory, show `Saved: 1` in every later journey.
Django, Django Rusty Templates and django-components keep it in the
browser's session, and Reflex in state for each browser tab, so a new
browser context starts from `Saved: 0`, as every journey does in Citry,
django-unicorn, Tetra and ReactPy. The default journey runs first and
alone, because in every clean app its `Add` is the only step that saves
anything on the server. Because it ends first, the clean app and the case
start each other journey from the same server state, apart from what the
mistake itself changed. The other journeys then run at the same time,
each in its own browser context. That roughly halves a browser check's
time, because most of a journey is waiting for the page to settle. Each
journey's browser messages are kept apart and joined in the order
`framework.toml` lists the journeys, so the record does not depend on
which journey logged first. ReactPy 1.1.0 fails when it renders two pages
at the same moment (its server logs `RuntimeError: Hook stack is in an
invalid state`), so its `framework.toml` sets `journeys_at_once = false`,
a `[runtime]` key that is true by default, and its journeys run one after
another. Every case runs every journey of its framework, so a mistake is
compared on every part of the page any journey reaches. Every framework
lists three more journeys:
`search` types `alpha` into the search field and presses Enter, and
`about` and `project` click the `About` and `Project 1` links. Every
framework except FastHTML, which has no status line, also lists a `status`
journey, which clicks `Details`, `Close`, and `Details` again. In
django-unicorn each of those clicks sends a request to the server, so its
`status` journey waits half a second between clicks for the reply.

A framework lists its journeys in `framework.toml`, by name, because the
selectors differ between frameworks. This shortened example lists the
default journey and the search journey, which types into the search field
and submits it (the real default journeys also click `Details` and
`Hide`):

```toml
[runtime.journeys]
default = [
  { action = "click", selector = "button:text-is('Add')" },
  { action = "wait", ms = 500 },
]
search = [
  { action = "fill", selector = "form[role=search] input", text = "alpha" },
  { action = "press", selector = "form[role=search] input", key = "Enter" },
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
attribute, whether it is disabled, and, for an image, whether it loaded.
Before it records the page, the runner waits up to two seconds for any
image that is still loading, so a slow image is not taken for a broken
one. Before the two records are compared, any sequence of 16 or more hex
digits in an `id` or `aria-*` value is blanked, because a framework makes
such an id up on every render: Citry mounts each interactive page into an
element with a random `citry-vue-...` id. The border color is read where
the journey leaves the mouse and the focus, so a button under the pointer
after the last click shows its hover color, the same in both runs when the
page is the same. A mistake whose only effect is outside these, such as a
value typed into a field that no text on the page repeats, reads as
"never".

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
with its default rules; for the templates of Django, Rusty,
django-components, django-unicorn and Jinja, and Tetra's page templates,
djLint; for Nuxt, the official
`@nuxt/eslint` module; for Next.js, the ESLint its starter installs; for
Reflex, `reflex compile --dry`, which builds every page without running
the app.
Each tool keeps its default rules (for a linter, the rules its framework's
preset turns on), except for the stricter settings below
and five changes that the clean app needs and that such projects
commonly make: FastHTML's main.py turns off ruff's star-import rules
(F403, F405), Nuxt's ESLint config turns off
`vue/multi-word-component-names`, the django-components app silences
one pyright check on the two lines where a component declares its `View`
class the way the django-components docs write it, the Tetra app
silences one pyright check on each line that declares a typed public
attribute, because pyright reads `public(...)` as returning a `Public`
object rather than a value of the declared type, and the Reflex app
silences one pyright check on the line that reads the project number
from the page's URL as `rx.State.project_id`, as Reflex's docs write it,
because pyright cannot see a var Reflex adds when it registers the page.

When a framework has a setting that turns on a stricter check, and other
frameworks here have the same kind of check, the benchmark turns it on in
that framework's app, so the frameworks are compared like for like. Each
framework's notes name every setting changed from the default, and the
settings considered and left off, with the reason. These are on:

| Framework | Setting | What it adds |
| --- | --- | --- |
| Jinja | `undefined=StrictUndefined` | Printing a name the template was not given, using it in `{% if %}` or looping over it raises an error, as Citry reports an unknown template name |
| django-components | Pydantic models for `Kwargs`, `Slots` and the data classes, with djc-ext-pydantic and `extra='forbid'` | Input and data types are checked when a component renders (Citry, Next.js, Nuxt and FastHTML check them before the app runs); unknown input names are rejected, as with django-components' default classes |
| Tetra | A type annotation on every public attribute (Tetra has no setting for this; it checks only annotated attributes) | Tetra checks each public attribute's value against its type when it writes the component's state into the page, as django-components' Pydantic models check its data when a component renders |
| Nuxt | `vueCompilerOptions.strictTemplates` | vue-tsc reports an unknown component, element, attribute, directive or component event, the same kinds of names Next.js's tsc checks (Citry also checks these names before the app runs, and only warns about an unknown component event) |
| Nuxt | `experimental.typedPages` | vue-tsc checks a `<NuxtLink>` or router call that names a route against the app's routes |
| Next.js | `typedRoutes` | tsc checks a link's path against the app's routes, as the Django, Rusty, Jinja, Tetra, django-unicorn and django-components apps check a link's route when the page renders |
| Next.js | `noUncheckedIndexedAccess`, `noImplicitOverride` and `verbatimModuleSyntax` in tsconfig.json | tsc treats a value read by index as possibly missing, requires `override` on a method that replaces its parent's, and requires `import type` for an import used only as a type; the tsconfig Nuxt generates turns all three on |
| ReactPy | `REACTPY_DEBUG_MODE=1` | ReactPy checks each element and attribute it sends and warns about a list item without a key, like React's development checks in Next.js |

In Citry, Django, Django Rusty Templates, FastHTML, django-unicorn and
Reflex, none of the settings adds a kind of check the other frameworks make, so
they keep their defaults; their notes list the settings considered.

Each linter keeps the rules its framework's preset turns on (or its own
defaults, where the framework has no preset); a rule outside the preset
is a project's own choice, not a framework setting. Every Python stack
keeps pyright's standard mode, because its strict mode fails code that
the frameworks' docs write: it reports 43 errors in the clean Django
app, 65 in the django-components app and 3 in the Citry app, mostly
parameters written without a type, as django-components' docs write
`get_template_data(self, args, kwargs, slots, context)`, and values
whose type pyright cannot work out. One of the Citry app's three is its
FastAPI lifespan function: Citry's FastAPI guide annotates it as
returning `AsyncIterator`, and strict mode reports that annotation as
deprecated. ruff's unused-argument rules (ARG), the counterpart of ESLint's
unused-variable check, would report arguments the frameworks require a
method to accept, 14 times in the clean Citry app and 24 times in the
django-components app.

| Stage | What it measures |
| --- | --- |
| `editor` | What the recommended editor setup shows. Measured with the command-line form of the same engine: TypeScript's `tsc` for the TypeScript editor service, `vue-tsc` for the Vue extension, pyright in Pylance's standard type-checking mode, and `citry check --types` for Citry's language server, which runs the same checks |
| `check` | The check command the framework's docs tell developers to run, such as `manage.py check` or `citry check`, and the linters listed above |
| `build` | The production build, when the framework has one |

Each baseline pins exact versions in its own lockfile, and those versions are
part of the result. The Citry app is the exception: it installs citry and
citry-lsp from this repository's sources, so a report names the commit it
measured instead of a release.

## What the result does not show

- The editor stage uses each engine's command-line form, not a running
  editor. Where the two differ, the difference is noted in
  `framework.toml`.
- Whether a message is easy to understand is not scored, only whether one
  appears and where it points.
- Each framework's cases were written by Citry's maintainers. Corrections from
  each framework's users are welcome; see
  [#151](https://github.com/citry-dev/citry/issues/151).
