# Error-prevention benchmark: plan for parts 2 and 3

Status: approved by the maintainer on 2026-10-20, with the decisions listed
at the end. Written against the benchmark as added in PR #205 (commit
`9346c7131`). PRs 1a (case edits) and 1b (runner journeys and page
comparison) are done, as described in section 7, and so are PR 2 (the
hand-off mistakes on the current page), PR 3 (browser components and slot
data), PR 4 (forms, links, assets, CSS variables and i18n arguments) and
PR 9 (Django Rusty Templates, the Django app on an experimental Rust
version of Django's template engine). PR 6 has added django-components,
with PR 3's reference-page parts and a case for each of the 44 mistakes in
the catalogue after PR 3. PRs 9 and 6 landed before PR 4, so PR 4 added its
page changes and cases to both apps, and PR 5 will too. PR 8 has added
ReactPy, with a case for each of those 44 mistakes, and then PR 4's page
changes and cases. PR 10 has added django-unicorn the same way, with PR
4's page changes and a case for each of the 49 mistakes in the catalogue
after PR 4; it is not in a published run yet. The other PRs in section 8
are planned. The published results include 1b, PR 2, PR 3, PR 9, PR 6,
PR 4 and PR 8. The benchmark itself is described in
[error_prevention_benchmark.md](error_prevention_benchmark.md) and
[`benchmarks/errors/README.md`](../../benchmarks/errors/README.md).

Part 1 (PR #205) writes 24 mistakes into 6 frameworks. This plan grows it in
two passes:

- **Part 2** follows data through every hand-off a web app makes, and asks
  at each one: does the framework know the names, notice a missing required
  value, check the type, and reject an invalid value?
- **Part 3** adds mistakes that other frameworks' own tools catch, so the set
  is not only what Citry happens to check, and adds the six frameworks the
  performance benchmark compares but this one does not measure yet.

At the end there is a split into PR-sized parts, each with its cost.

## Contents

1. [What Citry checks today (the count)](#1-what-citry-checks-today)
2. [The hand-off matrix](#2-the-hand-off-matrix)
3. [Part 2: new mistakes that fill the matrix](#3-part-2-new-mistakes-that-fill-the-matrix)
4. [Part 3: what other frameworks' tools check](#4-part-3-what-other-frameworks-tools-check)
5. [Part 3: new mistakes from that survey](#5-part-3-new-mistakes-from-that-survey)
6. [Part 3: which frameworks to add, and in what order](#6-part-3-which-frameworks-to-add)
7. [Changes the reference page and the runner need](#7-changes-the-reference-page-and-the-runner-need)
8. [PR split and cost](#8-pr-split-and-cost)
9. [Open questions for the maintainer](#9-open-questions-for-the-maintainer)

---

## 1. What Citry checks today

**Count: about 118 distinct mistake checks (114 if a render-time repeat of
a static check is not counted again). Counting only diagnostic codes: 30.**

How it was counted, from the `main` branch on 2026-10-20:

| Group | Count | What is in it |
| --- | --- | --- |
| Diagnostic catalog codes | 29 + variants = 43 | 30 codes that report a mistake in the app (see the note below the table). `parse.syntax` is expanded in the next row, so 29 here, plus the message variants that catch a different mistake: 4 extra `<c-mark>` variants, 4 extra attribute-value variants, 6 extra i18n argument variants. Variants that change only wording or severity count once |
| Checks reported as `citry.parse.syntax` | 48 | The parser rejects a template for many different mistakes under one code, in `crates/citry_template_parser/src/parser.rs`. The ones that matter most here: an unknown component input (`:4147`), a missing required input (`:4214`), the same input passed as both `title` and `c-title` (`:4342`), an unknown slot name (`:4620`), a missing required slot (`:4743`), an unknown slot-data field (`:4989`), a duplicate attribute (`:4313`), unclosed and mismatched tags (`:246`, `:405`), `c-if` together with `c-for` (`:4444`), a misplaced `c-else` (`:5168`), unknown or Alpine-only event modifiers (`:2677`) |
| Checks forwarded from ty and TypeScript | 9 families | ty runs on template expressions and `c-*` values (`citry.python.<rule>`: wrong input type, wrong `c-class`/`c-style` type, unknown attribute, wrong operator or call). TypeScript runs on Vue expressions and component JavaScript (`citry.typescript.tsNNNN`: wrong type, unknown member, wrong argument count, undefined name, syntax error). Each family counts once, not once per TypeScript code (`packages/py/citry_lsp/citry_lsp/typescript.py:81-127`) |
| Runtime checks | 18 | Errors Citry raises at render, at class definition, or when a server event arrives: Kwargs, Slots and data-class validation (`component.py:1098-1115`, `component_render.py:2924-2963`), a required slot with no fill (`nodes/__init__.py:576`), an unknown server event (404, `ext/events/dispatcher.py:706`), a payload checked against the handler's `data` type (422, `dispatcher.py:757-777`), invalid state updates, handler signature checks (`ext/events/handlers.py:420-570`), non-JSON browser data (`ext/dependencies/scripts.py:687`), `tr()` arguments at render. 4 of them repeat a static check at render, which gives the 114. The full list is below the table |

**Which catalog codes count.** The catalog
(`packages/py/citry/citry/_diagnostic_catalog.py`, generated from
`packages/protocol/diagnostics/v1/catalog.json`) has 49 codes. 19 of them
report a tooling or setup problem, not a mistake in the app: the 13
`citry.format.*` codes, `parse.value`, `parse.configuration`,
`check.template-declaration`, `check.template-language-unsupported`,
`check.template-namespace-unavailable` and `check.python-source-unreadable`.
That leaves 30. Two choices are arguable: `check.python-source-unreadable`
also fires on a Python syntax error in app code, and
`check.template-file-unreadable` (kept in the 30) is closer to a setup
problem. Either way the code count moves by one.

**The 18 runtime checks.** Kwargs built at render (unknown, missing, and
typed names); Slots built at render; TemplateData, JsData and CssData built
from the data methods; a required slot with no fill; a missing slot-data
field; a reserved `js_data` key; a value that cannot become JSON; an unknown
server event (404); a payload checked against the handler's `data` type
(422); an invalid state update from the browser; handler signatures checked
when the class is defined; State declarations checked; a State field with no
matching input and no default; `tr()` message and arguments at render; Vue
code passed through `c-bind`; a directive on a component whose child has no
single root; a `v-` directive on `c-element` with `c-is`, or Vue syntax on
`c-provide`; and an unknown custom directive, which Vue reports in the
browser.

The count was made by an agent reading the source, and the per-row
file:line references come from it. The ty rule names other than
`invalid-assignment` and `unresolved-attribute` were not checked against the
code.

**What Citry does not check.** These matter for part 2, because they mark
the hand-offs where Citry is blind. The source of each is named, because only
some are stated in the docs:

- an unknown `var(--name)` in component CSS (docs:
  `docs_site/content/ide/vscode.md:678`); CSS class names (no rule exists,
  and the 2026-10-20 run missed m16);
- a parent's listener for an event the child does not declare, when the name
  is plain lowercase such as `@hdie` (code:
  `packages/py/citry/citry/analysis.py:1511`; the docs at
  `ide/vscode.md:792` do not mention the lowercase rule);
- payload field names before the request is sent: only the 422 at runtime
  checks them, and the reference page shows that error nowhere, which is why
  m18 is "missed" for Citry (benchmark note in
  `cases/m18-payload-field/citry/port.toml`);
- HTML attribute names and element names (no rule exists; m10 and m11 were
  missed);
- the result a server event returns to the browser, injections, and non-JSON
  `JsData` values, which TypeScript sees as `any` (docs:
  `ide/vscode.md:565-585`);
- a misspelled `c-if` on a plain element, which renders as an attribute
  (inferred from `parser.rs:2997-3005`, not tested).

---

## 2. The hand-off matrix

Each row is one place where data crosses from one part of the app to
another. Each column is one kind of check. A cell names the mistakes that
test that check at that hand-off: existing ones as `m07`, new part 2 ones in
**bold**, new part 3 ones in *italics*. The last column names the Citry
checks that guard the row today.

Column meanings:

- **Name known:** a misspelled name is reported (variable, field, input,
  event, slot, route, message).
- **Required present:** leaving out something required is reported.
- **Type:** a value of the wrong type is reported.
- **Value valid:** a value of the right type but outside what is allowed is
  reported (a keyword list, a choice, a format).
- **Exposure:** the value reaches only the side that may see it (secrets,
  values the browser cannot receive).
- **Structure:** the code that carries the hand-off is well formed.

| # | Hand-off | Name known | Required present | Type | Value valid | Exposure | Structure | Citry checks today |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H1 | Server data into the server template | m07, m08, *m59* | | m23, *m58* | | | | `template.unknown-variable`, ty families |
| H2 | Server data into a component's inputs | m01, m02 | m04 | m03, m17 | **m49** | | | parse.syntax input rules, ty `invalid-assignment`, runtime Kwargs |
| H3 | Server data into browser code | **m40** | | **m41** | | m12, **m42** | | `vue.unknown-variable`, `vue.python-variable`, `js-data.*`, TypeScript |
| H4 | Server data into CSS | **m43** | | | | | | none (docs say an unknown `var(--name)` is not reported) |
| H5 | Browser data into a browser-side child component | **m25** | **m26** | **m27** | | | **m28** (child writes its input) | `browser.missing-component-prop`, `browser.incompatible-component-prop`, TypeScript |
| H6 | Events from a child to its parent, and DOM events | m24, **m29**, **m31** | | **m30**, *m60* (handler arguments) | | | | `browser.undeclared-emit`, `browser.undeclared-component-event` (warning, not for lowercase names) |
| H7 | Browser to server (handler, route, payload, reply) | m06, m18 | **m33** | **m32** | | | | `browser.unknown-server-event`; payload only at runtime (422) |
| H7b | Server reply read back in the browser | **m34** | | | | | | none (TypeScript sees the reply as `any`) |
| H8 | Slots (or children, or blocks) | m05 | **m35** | **m37** | | | | parse.syntax slot rules, runtime required-slot check |
| H8b | Data a slot passes back to its fill | **m36** | | **m37** | | | | parse.syntax unknown slot-data field |
| H9 | State kept between requests or renders | m13, **m38** | | **m39** | | | | `browser.unknown-state-field`, pyright on Python State |
| H10 | Server render and browser render agree | m14 | | | | | *m52* (nesting the browser rewrites) | none at check time |
| H11 | HTML the template writes | m10, m11, m16, *m54* | *m53* (alt text) | *m62* (boolean attribute) | m09, *m55* | | m22, *m52*, *m56*, *m57* | `template.invalid-attribute-value` (warning), parse.syntax duplicate attribute |
| H12 | Forms posted to the server | **m44** | | | | | | none |
| H13 | Routes and links | **m45** | | *m61* | | | | none |
| H14 | Translations | m15, **m46** | | | | | | `i18n.unknown-message`, `i18n.argument-invalid` |
| H15 | Files and assets the app names | **m47**, **m48** | | | | | | `check.template-file-not-found` (component template files only) |
| H16 | Browser templates and browser code | m21 | | | | | m19, m20, *m63* (two-way binding on a non-input), *m51* (list key) | TypeScript syntax, parse.syntax Vue rules, `browser.invalid-state-binding-target` |
| H17 | Shared values passed down without inputs (provide / inject / context) | **m50** | | | | | | runtime `KeyError` only |

Where the 24 existing mistakes sit: H1 has 3, H2 has 5, H3 has 1, H6 has 1,
H7 has 2, H8 has 1, H9 has 1, H10 has 1, H11 has 5, H14 has 1, H16 has 3. No
existing mistake tests H4, H5, H7b, H8b, H12, H13, H15 or H17, and the
"required present" and "value valid" columns are almost empty.

Cells left empty on purpose: "exposure" makes sense only for H3; "value
valid" makes sense only where the receiving side declares a list of allowed
values.

---

## 3. Part 2: new mistakes that fill the matrix

Written in `catalogue.toml` form. `ref` says which reference-page addition a
mistake needs (section 7); `none` means the current page is enough.

| id | Title | Hand-off, check | Origin | Needs |
| --- | --- | --- | --- | --- |
| m25-browser-input-name | Misspelled input on a browser-side component | H5 name | neutral | Ref A |
| m26-browser-input-missing | Missing required input on a browser-side component | H5 required | neutral | Ref A |
| m27-browser-input-type | Wrong-typed input on a browser-side component | H5 type | neutral | Ref A |
| m28-input-written-by-child | Child component changes an input it received | H5 structure | neutral | Ref A |
| m29-listener-name | Parent listens for a misspelled event | H6 name | neutral | none |
| m30-event-payload-type | Event sent with a payload of the wrong type | H6 type | neutral | none |
| m31-dom-event-name | Misspelled browser event name on an element | H6 name | neutral | none |
| m32-payload-type | Request payload field of the wrong type | H7 type | neutral | none |
| m33-payload-missing-field | Request payload leaves out a required field | H7 required | neutral | none |
| m34-reply-field | Browser reads a misspelled field of the server's reply | H7b name | neutral | none |
| m35-required-slot-missing | Required slot left unfilled | H8 required | neutral | none |
| m36-slot-data-name | Slot fill reads a misspelled slot-data field | H8b name | neutral | Ref B |
| m37-slot-data-type | Slot fill uses slot data as the wrong type | H8b type | neutral | Ref B |
| m38-state-read-typo | Template reads a misspelled state field | H9 name | neutral | none |
| m39-state-type | State field given a value of the wrong type | H9 type | neutral | none |
| m40-browser-value-name | Browser code reads a misspelled server value | H3 name | neutral | none |
| m41-browser-value-not-json | Server passes browser code a value the browser cannot receive | H3 type | citry-inventory | none |
| m42-secret-sent-to-browser | Server sends a secret to the browser | H3 exposure | citry-inventory | none |
| m43-css-variable-name | CSS reads a misspelled variable the server sets | H4 name | citry-inventory | Ref C |
| m44-form-field-name | Form field name differs from what the server reads | H12 name | neutral | Ref D |
| m45-link-route-name | Link to a route that does not exist | H13 name | neutral | Ref E |
| m46-i18n-argument | Translation message given a missing or misnamed argument | H14 required, type | citry-inventory | Ref C |
| m47-template-path | Misspelled path to a template or component file | H15 name | neutral | none |
| m48-asset-path | Misspelled path to a stylesheet, script or image | H15 name | neutral | Ref F |
| m49-input-choice | Component input given a value outside its allowed choices | H2 value | neutral | Ref B |
| m50-shared-value-name | Descendant reads a shared value that no ancestor provides | H17 name | neutral | Ref G (later) |

26 mistakes: 22 neutral and 4 from Citry's inventory. Neutral means the
mistake comes from #158's list, from the maintainer's hand-off list in the
part 2 request, or from another framework's tools. m41, m43, m46 and m42
come from Citry's own rule list or its own benchmark notes. The catalogue
header and the design doc name the hand-off list as a neutral source, next
to #158 and other frameworks' tools.

### Entries

```toml
[[mistake]]
id = "m25-browser-input-name"
title = "Misspelled input on a browser-side component"
category = "naming"
origin = "neutral"
description = "The details panel passes its open state to the browser-side `Status` component under a misspelled input name, for example `opne` instead of `open`."
correct = "Clicking Details changes the status line from `Status: closed` to `Status: open`."

[[mistake]]
id = "m26-browser-input-missing"
title = "Missing required input on a browser-side component"
category = "naming"
origin = "neutral"
description = "The details panel renders the browser-side `Status` component without its required `open` input."
correct = "Clicking Details changes the status line from `Status: closed` to `Status: open`."

[[mistake]]
id = "m27-browser-input-type"
title = "Wrong-typed input on a browser-side component"
category = "types"
origin = "neutral"
description = "The details panel passes `Status` its boolean `open` input as text, for example the string `\"open\"` or `String(open)`."
correct = "Clicking Details changes the status line from `Status: closed` to `Status: open`."

[[mistake]]
id = "m28-input-written-by-child"
title = "Child component changes an input it received"
category = "events"
origin = "neutral"
description = "The `Status` component has its own button that closes the panel by assigning to its `open` input, instead of telling the parent through an event."
correct = "Clicking Close in the status line hides the details text and the Details button opens it again."

[[mistake]]
id = "m29-listener-name"
title = "Parent listens for a misspelled event"
category = "events"
origin = "neutral"
description = "The card emits or calls `hide` correctly, but the page listens under a misspelled name, for example `@hdie` or `onHdie`."
correct = "Clicking Hide on the first card hides that card."

[[mistake]]
id = "m30-event-payload-type"
title = "Event sent with a payload of the wrong type"
category = "events"
origin = "neutral"
description = "The card's `hide` event carries a number, for example the card's task count, where the page expects the card's title (a string). Where the event carries no value, because the page's listener already knows which card it belongs to, this mistake does not apply."
correct = "Clicking Hide on the first card hides that card."

[[mistake]]
id = "m31-dom-event-name"
title = "Misspelled browser event name on an element"
category = "events"
origin = "neutral"
description = "The Details button listens for a misspelled browser event, for example `@clik`, `onClik`, `x-on:clik` or `hx-trigger=\"clik\"`."
correct = "Clicking Details shows the details text."

[[mistake]]
id = "m32-payload-type"
title = "Request payload field of the wrong type"
category = "events"
origin = "neutral"
description = "The Add button sends `amount` as text, for example `{amount: \"1\"}` or a value read from an element's text, where the server declares a whole number. Where the framework turns that text into a number before the server code sees it, the mistake is prevented."
correct = "Clicking Add increases the saved count from 0 to 1."

[[mistake]]
id = "m33-payload-missing-field"
title = "Request payload leaves out a required field"
category = "events"
origin = "neutral"
description = "The Add button sends its request without the `amount` field, for example an empty payload."
correct = "Clicking Add increases the saved count from 0 to 1."

[[mistake]]
id = "m34-reply-field"
title = "Browser reads a misspelled field of the server's reply"
category = "events"
origin = "neutral"
description = "Browser code that receives the server's reply to Add reads a misspelled field, for example `result.cuont` instead of `result.count`. Where the server replies with HTML that replaces part of the page, this mistake does not apply."
correct = "Clicking Add increases the saved count from 0 to 1."

[[mistake]]
id = "m35-required-slot-missing"
title = "Required slot left unfilled"
category = "naming"
origin = "neutral"
description = "The page renders a card without filling its required `footer` slot (or block, or child region)."
correct = "Each card shows the footer link the page passed in."

[[mistake]]
id = "m36-slot-data-name"
title = "Slot fill reads a misspelled slot-data field"
category = "naming"
origin = "neutral"
description = "The card hands its title and count to the `footer` slot, and the page's fill reads the title under a misspelled name, for example `slot.titel`."
correct = "Each card's footer link reads `Open Alpha (3)`, `Open Beta (5)`, `Open Gamma (8)`."

[[mistake]]
id = "m37-slot-data-type"
title = "Slot fill uses slot data as the wrong type"
category = "types"
origin = "neutral"
description = "The page's footer fill treats the card's numeric `count`, which the slot hands back, as text, for example `count + \" tasks\"` in Python or a string method such as `count.padStart(2)`."
correct = "Each card's footer link reads `Open Alpha (3)`, `Open Beta (5)`, `Open Gamma (8)`."

[[mistake]]
id = "m38-state-read-typo"
title = "Template reads a misspelled state field"
category = "naming"
origin = "neutral"
description = "The counter's text reads the saved total from a misspelled state field, for example `cuont`, while the code that updates it is correct."
correct = "Clicking Add changes the text from `Saved: 0` to `Saved: 1`."

[[mistake]]
id = "m39-state-type"
title = "State field given a value of the wrong type"
category = "types"
origin = "neutral"
description = "The Add handler stores the new total as text, for example `str(total)`, in a state field declared as a number."
correct = "Clicking Add increases the saved count from 0 to 1. (Only tools can see the wrong type; the page looks the same.)"

[[mistake]]
id = "m40-browser-value-name"
title = "Browser code reads a misspelled server value"
category = "naming"
origin = "neutral"
description = "Browser code reads the public setting the server passes to it under a misspelled name, for example `apiBsae`."
correct = "The page shows `API: /api`."

[[mistake]]
id = "m41-browser-value-not-json"
title = "Server passes browser code a value the browser cannot receive"
category = "server-browser"
origin = "citry-inventory"
description = "The server passes the public setting to browser code as an object that cannot be sent as JSON, for example a path or URL object, a set, or a date, instead of a string."
correct = "The page shows `API: /api`."

[[mistake]]
id = "m42-secret-sent-to-browser"
title = "Server sends a secret to the browser"
category = "server-browser"
origin = "citry-inventory"
description = "The server adds `SECRET_TOKEN` to the data it passes to browser code (props, JSON data, a public config key), although no browser code reads it."
correct = "The page shows `API: /api`, and the secret appears nowhere in what the browser receives. (The page comparison cannot see this; only tools can catch it.)"

[[mistake]]
id = "m43-css-variable-name"
title = "CSS reads a misspelled variable the server sets"
category = "html"
origin = "citry-inventory"
description = "The server sets the heading color as the CSS variable `--accent`, and the stylesheet reads a misspelled `var(--acent)`."
correct = "The heading is blue."

[[mistake]]
id = "m44-form-field-name"
title = "Form field name differs from what the server reads"
category = "events"
origin = "neutral"
description = "The search input is named `qeury` while the server reads the field `q` (or `query`)."
correct = "Searching for `alpha` shows `Searched: alpha`."

[[mistake]]
id = "m45-link-route-name"
title = "Link to a route that does not exist"
category = "naming"
origin = "neutral"
description = "The About link points to a misspelled route, by name (`url('abuot')`) or by path (`/abuot`), where the app defines `about`."
correct = "Clicking About opens the page that reads `About this board`."

[[mistake]]
id = "m46-i18n-argument"
title = "Translation message given a missing or misnamed argument"
category = "naming"
origin = "citry-inventory"
description = "The heading's translation message takes the owner's name as an argument, and the page passes it under a misspelled name, for example `nmae=`."
correct = "The heading reads `Projects`, and its subtitle reads `Owned by Ada`."

[[mistake]]
id = "m47-template-path"
title = "Misspelled path to a template or component file"
category = "templates"
origin = "neutral"
description = "The page names the file of its layout or of the card's script with a typo, for example an `extends` target, a `template_file`, or an import path such as `./crad`. Django's m01 port is already an include-path typo, so Django's m47 port misspells the `extends` target instead."
correct = "The page renders three project cards."

[[mistake]]
id = "m48-asset-path"
title = "Misspelled path to a stylesheet, script or image"
category = "html"
origin = "neutral"
description = "The owner's avatar image points to a misspelled static file, for example `/static/avtar.svg`."
correct = "The owner's avatar image loads."

[[mistake]]
id = "m49-input-choice"
title = "Component input given a value outside its allowed choices"
category = "types"
origin = "neutral"
description = "The card's `tone` input accepts only `plain` or `accent`, and the page passes a misspelled choice, for example `acent`."
correct = "The first card has the accent border."

[[mistake]]
id = "m50-shared-value-name"
title = "Descendant reads a shared value that no ancestor provides"
category = "naming"
origin = "neutral"
description = "The page provides the board's name to all its descendants (provide/inject, React context, Django context processor), and the card reads it under a misspelled key."
correct = "Each card shows `Board: Projects` under its title."
```

Notes on single entries:

- **m32:** some frameworks turn `"1"` into `1` on the way in. Following
  the decision on open question 3, the description uses `"1"`, and a
  framework that converts it counts as "prevented".
- **m34** and **m38** both test reading a field by name; they differ in
  where the value comes from (the reply to one request, or kept state), and
  frameworks check them with different tools. In Citry, m34 does not apply,
  because the counter reads `$state` instead of the reply.
- **m42** is the variant the Citry notes describe: the server sends the
  secret to the browser without any browser code reading it. In Next.js and
  Nuxt the m12 port already has this effect (the secret reaches the page),
  so m42 adds a new case mainly for Citry and the server-template stacks.
  It is kept because the benchmark should show a shared blind spot, not only
  Citry's wins.
- **m46** applies only where translations are built in (Citry, Django,
  Rusty, django-components and, if added, Tetra), like m15.

---

## 4. Part 3: what other frameworks' tools check

A survey of what each framework's own tools check, done by four research
agents with web search and, where noted, by running the pinned versions.
Only the checks relevant to the benchmark are listed. "Stage" is the
benchmark's stage: editor, check, build, or runtime.

### Next.js 16 and React 19

- **TypeScript and `@types/react` (editor, build).** Already measured.
  They reject unknown HTML attributes and `class`/`onclick`, which is how
  Next caught m10 and m11.
- **The Next.js TypeScript plugin (editor only).** Its rules live in
  [packages/next/src/server/typescript/rules](https://github.com/vercel/next.js/tree/canary/packages/next/src/server/typescript/rules):
  - browser-only hooks in a server component;
  - exports a page file may not have, and invalid route settings
    (`export const dynamic = 'foo'`);
  - a prop that cannot be serialized passed to a `"use client"` component;
  - `metadata` exported from a client component.

  The benchmark does not run the plugin (see `frameworks/next/framework.toml`).
  Most of these rules have no Citry equivalent, because Citry does not split
  server and client components.
- **Typed links (`typedRoutes`, editor and build).** Off by default.
  PR 4 left it off, because every app except django-components keeps its
  defaults until the later change that applies the decision on stricter
  settings. With it off, a misspelled link (m45) is a 404 when the link is
  clicked. Source: [Next.js TypeScript docs](https://nextjs.org/docs/app/api-reference/config/typescript).
- **eslint-config-next (check).** Its rules come from
  [packages/eslint-config-next](https://github.com/vercel/next.js/blob/canary/packages/eslint-config-next/src/index.ts):
  - errors: `react/jsx-key` and `jsx-no-duplicate-props`, and
    `react-hooks/rules-of-hooks`;
  - warnings: the jsx-a11y rules `alt-text`, `aria-props`, `aria-proptypes`
    and `role-has-required-aria-props`, and `@next/next/no-img-element`.

  Because the jsx-a11y rules are warnings, the accessibility mistakes below
  would score "static warning" for Next.
- **React runtime warnings (dev runtime).** Taken from React's source:
  - a missing list key or duplicate keys
  - `In HTML, <div> cannot be a descendant of <p>`, followed by a hydration
    error
  - `Invalid DOM property 'class'`
  - a `value` with no `onChange`
  - an input that switches between controlled and uncontrolled
  - `Rendered more hooks than during the previous render`

  Source files: [ReactChildFiber.js](https://github.com/facebook/react/blob/main/packages/react-reconciler/src/ReactChildFiber.js),
  [validateDOMNesting.js](https://github.com/facebook/react/blob/main/packages/react-dom-bindings/src/client/validateDOMNesting.js),
  [ReactDOMUnknownPropertyHook.js](https://github.com/facebook/react/blob/main/packages/react-dom-bindings/src/shared/ReactDOMUnknownPropertyHook.js).
- **next/image (editor, dev runtime).** `alt` is a required prop type, and
  a remote image with no width throws in `next dev`
  ([docs](https://nextjs.org/docs/app/api-reference/components/image)).
- **Not checked by anything:** a secret given the `NEXT_PUBLIC_` prefix, and
  `formData.get('amout')`, which returns `null`
  ([env docs](https://nextjs.org/docs/app/guides/environment-variables)).
  m42 and m44 test these, and Citry could do better there.

### Nuxt 4 and Vue 3.5

- **Vue compiler errors (editor, build).** From
  [compiler-core errors.ts](https://github.com/vuejs/core/blob/main/packages/compiler-core/src/errors.ts)
  and [compiler-dom errors.ts](https://github.com/vuejs/core/blob/main/packages/compiler-dom/src/errors.ts):
  - `v-else` with no adjacent `v-if`;
  - `v-model` on an invalid element, on a prop, or on a loop variable;
  - a duplicate attribute;
  - a misplaced `v-slot`, and duplicate slot names.
- **vue-tsc (editor).** It types props, emit payloads (`defineEmits`), slot
  data (`defineSlots`), and provide/inject through `InjectionKey`. A write to
  a prop from script is TS2540 (readonly). `strictTemplates` and the
  `checkUnknown*` options are off by default
  ([Vue compiler options](https://github.com/vuejs/language-tools/wiki/Vue-Compiler-Options)).
- **eslint-plugin-vue through @nuxt/eslint (check).** Nuxt combines the
  essential, strongly-recommended and recommended sets:
  - errors: `vue/no-mutating-props`, `vue/require-v-for-key`,
    `vue/no-use-v-if-with-v-for`, `vue/no-side-effects-in-computed-properties`
    and every `vue/valid-v-*` rule;
  - warnings: `vue/require-explicit-emits` and `vue/no-template-shadow`.

  The rule list is at [eslint.vuejs.org/rules](https://eslint.vuejs.org/rules/).
- **Vue dev runtime warnings.** Shown under `nuxt dev`:
  - missing or invalid prop, and a failed prop validator;
  - an emits validator that fails;
  - `injection "x" not found`;
  - `Attempting to mutate prop`;
  - duplicate keys (only on update);
  - hydration mismatches.
- **Nuxt options that are off by default.** `experimental.typedPages` (typed
  `<NuxtLink>`) and the typed message options of @nuxtjs/i18n
  ([experimental features](https://nuxt.com/docs/4.x/guide/going-further/experimental-features)).
  PR 4 left `typedPages` off too. It checks route names, and the Nuxt page
  links by path, so it would not change m45 there: vue-router prints a
  warning in the browser when the link is clicked.

### Django 6.1 and Jinja 3.1

- **`manage.py check` (check).** It checks settings and URL configuration
  only, never templates
  ([system checks](https://docs.djangoproject.com/en/dev/ref/checks/)).
- **The Django template engine (runtime).** Errors appear when a view first
  loads the template:
  - **When the template loads:** an unknown tag, an unknown filter, a wrong
    filter argument count, an unknown `{% load %}` library, or a duplicate
    block.
  - **Only if that branch renders:** `TemplateDoesNotExist` for an
    `{% include %}` or `{% extends %}`, and `NoReverseMatch` for
    `{% url "nope" %}`.
  - **Never:** a filter argument of the wrong type, a fill for a block the
    parent does not have, or a missing attribute (which prints an empty
    string). This was probed on the pinned version.
- **CSRF (runtime).** A POST form without `{% csrf_token %}` gets a 403.
- **djLint (check).** Rules beyond the H025 already measured
  ([rule list](https://djlint.com/docs/linter/)):
  - H013 (image without `alt`), H037 (duplicate attribute), H053
    (duplicate `id`);
  - H042 (label `for` with no matching id), H054 (nested interactive
    element);
  - D018 / J018 (hard-coded internal link).
- **Jinja (runtime).** It reports unknown tags and filters when the template
  loads, but stays silent inside an `{% if %}` that never runs. Macros reject
  an unknown keyword argument with a `TypeError`. `StrictUndefined` is off by
  default ([API docs](https://jinja.palletsprojects.com/en/stable/api/#jinja2.StrictUndefined)).
- **Not in the default setup.** Under the decision on stricter settings,
  each of these is turned on in the Django app when other frameworks here
  have the same kind of check; that has not been decided for any of them
  yet:
  - the [Django Language Server](https://djls.joshthomas.dev/en/latest/template-validation/)
    (djls), which reports unknown tags and filters and filter argument counts
    in the editor;
  - django-extensions [`validate_templates`](https://django-extensions.readthedocs.io/en/latest/validate_templates.html);
  - [django-stubs](https://github.com/typeddjango/django-stubs) with mypy.

### The frameworks not measured when this plan was written

- **Django Rusty Templates** (pinned commit `0725f87`): same stages as
  Django, with better messages. `{{ owner.nmae }}` raises at render where
  Django prints nothing, so m08 moves from missed to runtime error. The
  pinned parser has no `extends`, `block`, `translate`, `static`,
  `partialdef` or `json_script`, and `{% load %}` fails for any library
  with a tag that is not a simple tag, such as `i18n` and `static`
  ([repository](https://github.com/LilyFirefly/django-rusty-templates),
  [issue #2](https://github.com/LilyFirefly/django-rusty-templates/issues/2)).
  Measured in PR 9: m05 and m35 do not apply, because the card writes its
  own footer link instead of taking one from the page. m15 still applies,
  because the view can translate the heading with Django's `gettext`.
- **django-components 0.152.0**:
  - **At render:** it builds `Kwargs` and `Slots` as NamedTuples, so an
    unknown input, a missing input or an unknown slot raises a `TypeError`.
    A required slot left empty raises with a "did you mean" hint.
  - **Not at runtime by default:** value types, because NamedTuples do
    not check them. Its docs say that to check types, a project writes
    these classes as Pydantic models and installs the djc-ext-pydantic
    extension; PR 6 turns that on, under the decision on stricter settings.
  - **No static template checks:** its one system check looks only at the
    folders its settings name, and it ships no editor support.

  This was read from the installed source.
- **Tetra 0.8.5**: an unknown public method gives a 404 on the server, or a
  `ReferenceError` in the browser when Alpine calls it. Its JavaScript is
  built with esbuild, so a script syntax error shows up at build.
- **django-unicorn 0.67.0**:
  - **Unknown method:** `unicorn:click="sav"` is silently ignored.
  - **Unknown field:** `unicorn:model="cuont"` raises `UnicornViewError` and
    shows a browser error.
  - **No child-to-parent events and no slots:** m05 and m24 do not apply.

  Measuring it in PR 10 confirmed the first point (m06 is missed),
  corrected the third, left the second unmeasured, and added two
  findings. A child component calls a method
  of the component that renders it through `self.parent`, as the
  child-components docs show, so m24 applies; with the parent's type
  narrowed for pyright, pyright reports the misspelled call. The page uses
  no `unicorn:model`, so the unknown-field error is not measured. The
  tag's keyword arguments are set on the component with no check of their
  names or types, and action arguments are converted to the types the
  method's annotations name, so m32 is prevented.
- **FastHTML** (already measured): this survey found two behaviors m32 and
  m33 will expose.
  - **Wrong-typed field:** a 404, not a 400.
  - **Missing field:** a 400 "Missing required field".

  FastHTML's tag functions accept any keyword, so unknown attributes pass
  silently ([handlers docs](https://www.fastht.ml/docs/ref/handlers.html)).
- **Reflex 0.9.10**: it checks a lot when it compiles the page, measured
  with `reflex compile --dry`:
  - `ForeachVarError` for a loop over a non-list;
  - `VarTypeError` and `VarAttributeError` for wrong operations;
  - `EventHandlerArgTypeMismatchError` and `EventFnArgMismatchError` when a
    handler's arguments do not fit the browser event;
  - a `ValueError` for a misspelled event trigger (`on_clik`);
  - a `TypeError` for a wrong `Literal` or boolean prop.

  Blind spots: an unknown prop silently becomes CSS, and a backend-only var
  (`_secret`) read in markup gets its default inlined into the browser
  bundle, so m12 is a silent leak
  ([event arguments docs](https://reflex.dev/docs/events/event-arguments/),
  [base vars docs](https://reflex.dev/docs/vars/base-vars/)). pyright helps
  only when state is written as `rx.Field[...]` with `@rx.event`, so the
  baseline must use that style.
- **ReactPy 1.1.0**: `@component` hides the function's parameters from
  pyright, so wrong or missing arguments show up only when the component
  renders, as a logged `TypeError`. The component then renders empty (in
  debug mode, it shows the error text).
  Attributes are an untyped dict. The list-key warning and other checks run
  only with `REACTPY_DEBUG_MODE`. The hooks linter its docs name is not on
  PyPI ([hooks docs](https://reactpy.dev/docs/reference/hooks-api.html)).
  Measured in PR 8:
  - **Wrong or missing arguments:** a call with an unknown or missing
    argument raises a `TypeError` when the component renders. ReactPy
    logs it with a traceback, so the runner sees a server error, and
    draws the component empty, or shows the error text in its place in
    debug mode. A wrong argument type is never reported.
  - **The hooks linter:** the package the ReactPy project does publish,
    `reactpy-flake8` 0.7.0, fails to load in a fresh environment because
    it imports `pkg_resources`. It checks only where hooks are
    called, which no mistake in the catalogue tests, so it is not a stage.
  - **Debug mode:** PR 8 turns it on under the decision on stricter
    settings. It changes no cell; runs with it off gave the same 49
    cells.

### What this says about Citry's blind spots

Mistakes that other frameworks' default tools catch before running and Citry
probably does not. Each is a guess until a case runs:

- **list keys:** React's ESLint, eslint-plugin-vue;
- **accessibility attributes** (alt text, ARIA names and values, roles):
  jsx-a11y in Next, djLint H013;
- **duplicate `id`s:** djLint H053;
- **boolean attributes given a string:** TypeScript, Reflex;
- **invalid nesting:** React at runtime, and every framework through
  hydration;
- **handler arguments that do not fit the event:** Reflex at compile.

Citry already catches two of the part 3 mistakes: a duplicate attribute
(`parser.rs:4313`) and a two-way binding on an element with no value
(`citry.browser.invalid-state-binding-target`). It probably catches m58 and
m59 through ty and `template.unknown-variable`. Citry is likely ahead on
input and slot names, slot data, state fields, server events and
translation keys. Mistakes nobody's defaults catch:
misspelled links (typed routes are off by default everywhere), secrets sent
to the browser on purpose, and CSS class and variable names.

---

## 5. Part 3: new mistakes from that survey

All neutral: each comes from another framework's tool. Several research
agents proposed overlapping ideas; these are the merged ones. They are left
out when part 2 already covers them (form field name, link route, slot data
type, emit payload type, prop mutation, provide/inject) or when they apply to
one framework only (CSRF token, hooks order, side effects in a computed
value).

| id | Title | Hand-off | Caught by (other frameworks) | Needs |
| --- | --- | --- | --- | --- |
| m51-list-key-missing | Repeated browser element without a key | H16 | `react/jsx-key`, `vue/require-v-for-key`, ReactPy debug warning | none |
| m52-invalid-nesting | Block element inside a paragraph | H10, H11 | React nesting warning, hydration errors | none |
| m53-image-alt | Image without alt text | H11 | jsx-a11y `alt-text` (warning), djLint H013, next/image types | Ref F |
| m54-aria-name | Misspelled ARIA attribute | H11 | jsx-a11y `aria-props` (warning) | Ref A |
| m55-aria-value | Invalid ARIA attribute value | H11 | jsx-a11y `aria-proptypes` (warning), Vue's types for bound `aria-*` | Ref A |
| m56-duplicate-attribute | Same attribute written twice on one element | H11 | Vue `DUPLICATE_ATTRIBUTE`, `vue/no-duplicate-attributes`, `react/jsx-no-duplicate-props`, djLint H037 | none |
| m57-duplicate-id | Two elements share an id | H11 | djLint H053 | none |
| m58-loop-non-list | Loop over a value that is not a list | H1 | Reflex `ForeachVarError`, pyright, TypeScript | none |
| m59-unknown-helper | Unknown template filter or helper function | H1 | Django and Jinja when the template loads, djls | Ref H |
| m60-handler-arguments | Handler declares arguments the event does not send | H6 | Reflex `EventFnArgMismatchError`, TypeScript | none |
| m61-route-param-type | Link passes a route parameter of the wrong type | H13 | FastHTML 404, typed routers | Ref E |
| m62-boolean-attribute-string | Boolean attribute given the text "false" | H11 | TypeScript in JSX, Reflex prop types | none |
| m63-binding-on-non-input | Two-way binding on an element with no value | H16 | Vue `X_V_MODEL_ON_INVALID_ELEMENT`, `vue/valid-v-model`; Citry `browser.invalid-state-binding-target` | Ref D |

```toml
[[mistake]]
id = "m51-list-key-missing"
title = "Repeated browser element without a key"
category = "templates"
origin = "neutral"
description = "The loop that renders the cards gives each repeated card no stable key (`key`, `:key`, `#c-key`), where the framework uses keys to update a list in the browser. Where the list is rendered only on the server and never updated in the browser, this mistake does not apply."
correct = "Each card has a key made from its project's slug, and hiding the first card hides only that card."

[[mistake]]
id = "m52-invalid-nesting"
title = "Block element inside a paragraph"
category = "html"
origin = "neutral"
description = "The owner line is written as a `<p>` that contains a `<div>`, which the browser silently splits into separate elements."
correct = "The owner line is one block that reads `Owner: Ada`."

[[mistake]]
id = "m53-image-alt"
title = "Image without alt text"
category = "html"
origin = "neutral"
description = "The owner's avatar image has no `alt` attribute."
correct = "The avatar image has the alt text `Ada`."

[[mistake]]
id = "m54-aria-name"
title = "Misspelled ARIA attribute"
category = "html"
origin = "neutral"
description = "The Details button's `aria-expanded` attribute is written as `aria-expandd`."
correct = "The Details button reports whether the details are open through `aria-expanded`."

[[mistake]]
id = "m55-aria-value"
title = "Invalid ARIA attribute value"
category = "html"
origin = "neutral"
description = "The Details button's `aria-expanded` is set to a value ARIA does not allow, for example `yes` or `open`, instead of `true` or `false`."
correct = "The Details button reports whether the details are open through `aria-expanded`."

[[mistake]]
id = "m56-duplicate-attribute"
title = "Same attribute written twice on one element"
category = "html"
origin = "neutral"
description = "The board wrapper has its `class` attribute written twice, for example `class=\"cards\" ... class=\"board\"`, so the browser keeps only the first and drops the styled one."
correct = "The board text is green."

[[mistake]]
id = "m57-duplicate-id"
title = "Two elements share an id"
category = "html"
origin = "neutral"
description = "The heading and the board wrapper are both given `id=\"board\"`."
correct = "Only the board wrapper has the id `board`."

[[mistake]]
id = "m58-loop-non-list"
title = "Loop over a value that is not a list"
category = "types"
origin = "neutral"
description = "The cards loop iterates over one project's `count` (a number) instead of the list of projects."
correct = "The page renders three project cards."

[[mistake]]
id = "m59-unknown-helper"
title = "Unknown template filter or helper function"
category = "naming"
origin = "neutral"
description = "The line that counts the projects uses a misspelled filter or helper, for example `projects|lenght` or `lenght(projects)` instead of `length` or `len`. Where the count is a property of the list (`projects.length` in JavaScript), the misspelled property is the natural form."
correct = "The page shows `Projects: 3`."

[[mistake]]
id = "m60-handler-arguments"
title = "Handler declares arguments the event does not send"
category = "events"
origin = "neutral"
description = "The page's hide handler is changed to require two arguments (the title and a reason), while the card's event sends only the title."
correct = "Clicking Hide on the first card hides that card."

[[mistake]]
id = "m61-route-param-type"
title = "Link passes a route parameter of the wrong type"
category = "types"
origin = "neutral"
description = "The project link points to `/projects/alpha`, where the route declares a numeric id, for example `/projects/{id:int}`."
correct = "Clicking the project link opens the page for project 1."

[[mistake]]
id = "m62-boolean-attribute-string"
title = "Boolean attribute given the text \"false\""
category = "html"
origin = "neutral"
description = "The search button is written with `disabled=\"false\"`, which HTML treats as disabled."
correct = "The search button is enabled."

[[mistake]]
id = "m63-binding-on-non-input"
title = "Two-way binding on an element with no value"
category = "templates"
origin = "neutral"
description = "The search field's two-way binding (`v-model`, `:c-*`, `x-model`, `value` with a change handler) is put on its wrapping `<div>` instead of the `<input>`."
correct = "Typing in the search field updates the text `Searching for: ...`."
```

m59 needs a small new line on every baseline (Ref H), made in PR 5. m63
needs the search input from Ref D; m62 uses the search button that already
exists.

### Origin balance after both parts

| | Neutral | Citry inventory | Total |
| --- | --- | --- | --- |
| Part 1 (existing) | 16 | 8 | 24 |
| Part 2 | 22 | 4 | 26 |
| Part 3 | 13 | 0 | 13 |
| All | 51 | 12 | 63 |

---

## 6. Part 3: which frameworks to add

When this plan was written, the performance benchmark compared six
frameworks the error benchmark did not measure yet: Django Rusty Templates,
django-components, Tetra,
django-unicorn, Reflex and ReactPy.

Recommended order:

1. **django-components.** Citry grew out of it, and it has the same model:
   typed `Kwargs` and `Slots` classes. It checks them only when the page
   renders, while Citry checks them in the editor. That makes it the most
   direct test of Citry's main claim. Cost is medium. The baseline is the
   Django one with the card turned into a component, and the tools are the
   same as Django's. Nothing extra needs installing.
   Done in PR 6: the page, the card, the counter and the status line are
   components. One package was installed after all: djc-ext-pydantic, for
   the type checks the decision on stricter settings turns on. The 44 cases
   ran in about 95 seconds with 5 cases at a time.
2. **Reflex.** It is the Python framework with the strongest checks before
   running: its compile step checks value types, handler arguments and prop
   values. Part 3 cares most about this, because it catches things Citry
   probably does not (m58, m60, m62). Its cost is the highest:
   - A check stage with `reflex compile --dry` takes about 5 seconds per
     case.
   - The runtime stage needs a frontend build per case. This was not
     measured; expect 30 seconds to a few minutes.
   - Before porting all cases, measure one case and decide whether to run
     the runtime stage only where no static stage reported the mistake (see
     open question 4).
3. **ReactPy.** Cheap: pure Python and uvicorn, a few seconds per case, with
   pyright and ruff as the tools. It mostly shows what a Python framework
   with weak typing catches, and many cells will be runtime errors that only
   reach the server log.
   Done in PR 8. The page is built from ReactPy components, with one
   JavaScript component for the API line, and served by uvicorn as in the
   performance benchmark in `benchmarks/web`. PR 4's search field, links,
   avatar, heading color and subtitle were added after PR 4 landed; the
   extra pages use ReactPy-Router, the ReactPy project's router. Of the 49
   cases, 18 end as editor errors, 1 as a check error, 10 as runtime
   errors, 13 are missed and 7 do not apply. The runtime errors are mostly
   misspelled or missing component arguments, which pyright cannot see
   through `@component`. The 49 cases ran on their own in about 2 minutes
   with `--jobs 5`.
4. **Django Rusty Templates.** Cheap, because it copies the Django baseline
   and changes the backend. The difference from Django is small: m08 moves to
   a runtime error, and m05 and m15 do not apply. The pinned parser has no
   `extends`, `block` or `translate`, so the baseline has to drop those.
   Done in PR 9 (`frameworks/rusty`). The measurement differs from this
   estimate in two cells: m15 applies, because the view translates the
   heading with `gettext`, and m35 does not apply, because the card writes
   its own footer link. The baseline also had to work around `static`,
   `partialdef` and `json_script`. Apart from m05, m08 and m35, every cell
   matches Django's. The framework notes list each difference from the
   Django app.
5. **django-unicorn.** Low to medium cost. Several cases do not apply,
   because it has no slots and no child-to-parent events. Its unknown-method
   behavior (silently ignored) is a useful data point.
   Done in PR 10 (`frameworks/unicorn`): the card list, the cards, the
   counter, the details, the status line and the search form are
   components. Seven cases do not apply (m05, m14, m20 and m34 to m37)
   and one is prevented (m32). m24 applies after all: the card calls the
   card list's `hide` method through `self.parent`. django-unicorn has no
   stricter setting to turn on. PR 10 was written after PR 4, so it also
   adds PR 4's page parts and cases. Its 49 cases ran on their own in
   about 3 minutes with `--jobs 5`; its 44 cases took about 100 seconds
   before PR 4 added five cases and three journeys.
6. **Tetra.** Highest setup cost after Reflex: encrypted state, sessions and
   an esbuild step. The web benchmark app already solves these, so the
   baseline can start from it.

Each new framework gets `framework.toml`, a baseline, and one case for each
mistake in the catalogue at that point. So adding frameworks after the
catalogue grows makes each framework PR larger, but keeps each
catalogue PR to the frameworks measured at that point. Django Rusty
Templates (PR 9) and django-components (PR 6) came after PR 3 and add PR
3's page changes and cases themselves; PRs 4 and 5 cover them too. The
total work is the same either way; the split in section 8 keeps every PR
to one dimension.

---

## 7. Changes the reference page and the runner need

### Cases describe their mistake as edits (done in PR 1a)

Before PR 1a, every case replaced whole baseline files with full copies
(`port.toml` `files`). Counting the copies:

- **FastHTML:** 21 cases copy `main.py`.
- **Nuxt:** 18 copy `app/app.vue`.
- **Django:** 15 copy `page.html`.
- **Jinja:** 14 copy `index.html`.
- **Citry:** 13 copy `board_page.py`.
- **Next:** 11 copy `board.tsx`.

Any addition to the reference page changes those files, so every one of
those copies would have had to be rewritten by hand, and a copy that is not
rewritten silently tests the old page.

**First change, before any new mistake (PR 1a):** let a case describe its
mistake as text edits to the baseline (`edits = [{ file, old, new }]`, each
`old` found exactly once), and convert the 134 ported cases (the other 10
are `not-applicable` and have no files) with a script that diffs each copy
against its baseline file. `validate` then reports any edit whose `old` text
is no longer in the baseline, so a baseline change shows exactly which cases
need a look. Keep full-file `files` for a case that changes a file
completely. The existing `mistake = { file, contains }` line check stays as
it is: the edit must put the `contains` text on exactly one line.

PR 1a converted all 134 ported cases, and none kept a full copy. Before the
copies were removed, a one-off check confirmed that applying each case's
edits to its baseline gives its old copy byte for byte.

### Reference page additions

Each addition is written once in every baseline, in the framework's normal
style, and must not change the visible page outside its own part.

| Ref | Addition | Used by |
| --- | --- | --- |
| A | Inside Details, a browser-side `Status` component with a required boolean input `open`, showing `Status: open` or `Status: closed`, and a Close button that tells the parent through an event. The Details button gets `aria-expanded` bound to the open state. A new browser journey (below) clicks Details, Close, then Details again | m25-m28, m54, m55 |
| B | The card gets an input `tone` with the choices `plain` and `accent` (the first card is `accent`, with a border color the stylesheet sets), and the card hands its `title` and `count` back to the `footer` slot, so the page's fill builds `Open Alpha (3)` from slot data | m36, m37, m49 |
| C | The server sets the heading color through the CSS variable `--accent` (blue), and a translated subtitle `Owned by Ada` takes the owner's name as a message argument (where translations are built in) | m43, m46 |
| D | The search form gets an `<input name="q">`, with a line `Searching for: ...` that follows what is typed, and submitting `alpha` shows `Searched: alpha` | m44, m63 |
| E | An `About` link to a named route `/about` that reads `About this board`, and a project link to `/projects/1` | m45, m61 |
| F | An owner avatar `<img src="/static/avatar.svg" alt="Ada">` | m48, m53 |
| G | (later) The page provides the board name to descendants, and each card shows `Board: Projects` | m50 |
| H | A line `Projects: 3`, computed in the template with the language's length filter or helper | m59 |

Each addition needs a matching change in two places:

- **The runner's browser check: separate journeys (done in PR 1b).**
  Before PR 1b, one list of steps per framework (`framework.toml`) ran
  before the after-click snapshot and the reload snapshot. Adding a search
  submit or a link click to that list would replace the board in both
  snapshots, so every existing case would be compared on a different page.
  Instead, add named journeys. Each one starts from a fresh load of `/`, runs
  its own steps, and records its own snapshot, and the three existing
  snapshots stay as they are. The planned journeys are: Details, Close,
  Details (A); type `alpha` and submit (D); click About (E); click the
  project link (E). The runner supported only `click` and `wait`, so
  journeys also needed `fill` and `press` steps, which PR 1b added.

  Journeys are declared in `framework.toml` under
  `[runtime.journeys]`, because their selectors differ by framework; the
  old list of steps is the `default` journey, with its three snapshots at
  the same points. Every case runs every journey of its framework, so a
  case cannot choose to skip the journey where its mistake shows. PRs 3
  and 4 add the planned journeys to each framework's `framework.toml`
  together with the page part they drive, and update the README's
  sentence that every framework lists only the default journey. The
  README's "The browser check" section describes the format, and the
  design doc's error table lists its error modes.
- **The page comparison (done in PR 1b).** It read text, element type,
  button type, tooltip, color, display and visibility. PR 1b added border
  color (B), and `alt`, `id`, `aria-*` and the disabled state (m53-m57,
  m62). Without them, those cases could be caught only by tools, and no run
  could show that they express their mistake. Image load failures (F)
  already reach the browser log as errors.

  Which existing cells this can change: only a mistake that is "never"
  today can move, to "silently wrong", and both count as missed. In the
  2026-10-20 run only m09 (`type="sumbit"`) is "never": in Django, Jinja
  and FastHTML, and in Citry's result when warnings are not counted (the
  published cell is `Ew`, because the editor's warning still counts there). Its edit changes only the `type`
  text, which the browser already reads as `submit`, and none of the newly
  compared values, so the next full run should show no changed cell. Citry
  mounts an interactive page into an element whose id has 32 random hex
  digits, new on every render, so the comparison blanks any 16 or more
  hex digits in a row in an `id` or `aria-*` value. A
  change in m09 would mean a newly compared value still differs between
  two loads of the same page, and needs a look before the run is
  published. Next.js and Nuxt have no "never" cell, so this run cannot show
  whether a newly compared value changes between two loads of their clean
  pages; the first "never" case there, or a one-off run that observes each
  clean app twice, would show it.

Where a framework cannot write an addition naturally (Django and Jinja have
no browser-side components for A), the mistakes that need it are
`not-applicable` with a reason, as today.

---

## 8. PR split and cost

**Measured cost today.** The 2026-10-20 run spent these times per case (the
time from each framework's first tool output to its last in that run,
divided by its cases). Installs are not included.

| Framework | Seconds per case |
| --- | --- |
| Citry | about 11 |
| Django | 7 |
| FastHTML | 7 |
| Jinja | 6 |
| Next.js | 14 |
| Nuxt | 12 |

That is about 57 seconds per mistake across the six frameworks. Frameworks
run one after another, so the full run took about 22 minutes.

**Writing cost.** One case is one `port.toml` plus the edit, about 10 to 20
minutes each including reading the result. A reference-page addition is one
change per baseline, plus re-checking the clean page.

| PR | Contents | Cases to write | Added run time | Full run after |
| --- | --- | --- | --- | --- |
| 1a. Case edits | `edits` form for `port.toml` and a script that converts the 134 ported cases. Proof in seconds: apply each converted case to its baseline and compare the result byte for byte with the old copy. No benchmark run needed | 0 new (134 converted by script) | 0 | ~22 min |
| 1b. Runner journeys and page comparison (done; the first full run after it, published with PR 2, changed no existing cell) | Named journeys with `fill`/`press` steps, and border color, `alt`, `id`, `aria-*`, `disabled` in the page comparison. One full run; any cell that changes is listed with the run, since a wider comparison can turn a "never" into "silently wrong" (both score as missed). The run was published with PR 2, and no existing cell changed | 0 | 0 | ~22 min |
| 2. Hand-offs on the current page (done) | m29-m35, m38-m42, m47 (13 mistakes; part 2 mistakes that need no page change) | 78 (13 x 6), minus the cells that do not apply | ~12 min | ~34 min |
| 3. Browser components and slot data (done; the run changed one existing cell, Citry m14, from runtime error to missed, because the details panel now passes `open` to `Status`) | Ref A and B in all six baselines, then m25-m28, m36, m37, m49 (7 mistakes) | 42 + 12 baseline changes | ~7 min | ~41 min |
| 4. Forms, links, assets, CSS variables, i18n arguments (done, after PRs 9 and 6, so it covers eight frameworks; the run changed no existing cell) | Ref C, D, E, F, then m43, m44, m45, m46, m48 (5 mistakes) | 40 written + 8 baseline changes | ~10 min measured: the three new journeys add page loads to every case | ~20 min for eight frameworks, measured |
| 5. Other frameworks' checks (part 3) | Ref H, then m51-m63 (13 mistakes); m53-m55, m61 and m63 depend on PRs 3 and 4 | 117 + 9 baseline changes, now that there are nine frameworks | ~12 min, estimated for six frameworks before the journeys PR 4 added | ~58 min, estimated before PR 4; PR 8 measured ~22 min for nine frameworks |
| 6. django-components (done, after PR 9 and before PRs 4 and 5) | framework, baseline, one case per mistake. 44 cases, one per mistake the catalogue had then (PRs 4 and 5 add the rest); they ran on their own in about 95 seconds with `--jobs 5` | 44 written (estimate ~62) | ~1.5 min measured (estimate ~8 min) | ~10 min for eight frameworks, measured |
| 7. Reflex | framework, baseline, `reflex compile --dry` check stage; measure one case's runtime first | ~62 | unknown: 30-95 min if every case builds the frontend | see open question 4 |
| 8. ReactPy (done, after PR 4 and before PR 5; the run changed no existing cell) | framework, baseline with PR 4's page parts, one case per mistake. 49 cases, one per mistake the catalogue has after PR 4 (PR 5 adds the rest); they ran on their own in about 2 minutes with `--jobs 5` | 49 written (estimate ~62) | ~2 min measured (estimate ~6 min) | ~22 min for nine frameworks, measured |
| 9. Django Rusty Templates (done, after PR 3 and before PRs 4 and 5) | starts from the Django baseline. 44 cases, one per mistake the catalogue had then (PRs 4 and 5 add the rest); its first 37 cases ran on their own in about 1 minute with `--jobs 5` | 44 written (estimate ~62) | ~1 min measured (estimate ~7 min) | ~8.5 min for seven frameworks, measured |
| 10. django-unicorn (done, after PRs 6 and 4 and before PR 5) | framework, baseline with PR 4's page parts, one case per mistake. 49 cases, one per mistake the catalogue has after PR 4 (PR 5 adds the rest); they ran on their own in about 3 minutes with `--jobs 5`. Not in a published run yet | 49 written (estimate ~62) | ~3 min measured (estimate ~7 min) | |
| 11. Tetra | | ~62 | ~10 min | |
| (later) Ref G and m50 | provide/inject in every baseline | 1 case + 1 baseline change per framework | | |

The estimated "Full run after" times assume one case at a time; the
measured ones use `--jobs 5`, such as the eight-framework run after PR 6,
which took about 10 minutes. Row 4 counts the eight frameworks measured
when PR 4 ran, and row 5 the nine measured now. Each framework
added before one of them adds one case per mistake and one baseline change
per page addition: Django Rusty Templates (PR 9) and django-components
(PR 6) came before both, and ReactPy (PR 8) and django-unicorn (PR 10)
before PR 5.

**Stricter settings for the frameworks measured before PR 6.** The decision
on stricter settings applies to every framework, but only django-components
(PR 6), ReactPy (PR 8) and django-unicorn (PR 10) were set up under it when
they were added, and django-unicorn has no stricter setting to turn on; the
others get their own PR. Until then the published cells compare
django-components with its type checks on against the other frameworks at
their defaults. The django-components notes name the cells this changes
(m03 and m49). ReactPy's one changed setting, debug mode, changes no cell.

Each of PRs 2 to 5 should also publish a new `results/<date>/` run and update
the README's reference-page table and its notes on single cells.

**Freeze the wording before writing cases.** Writing a case includes
reading its result, so in each of PRs 2 to 5 the first commit adds only the
`catalogue.toml` entries, and the cases come in later commits. The published
run then cites that first commit, which shows the wording was fixed before
any result was seen, as the catalogue header requires. Each new-framework PR
(6 to 11) adds no catalogue entries.

**Case count per new framework.** 62: the 63 mistakes minus m50, which
waits for Ref G.

**Full run time.** At the per-case times measured above, one case at a time
with every browser check run, the full 63-mistake catalogue in 11
frameworks (all but Reflex) would take about 1.6 hours. Three runner
features cut this:

- **Several cases at once.** `run --jobs N` (default 5 on a 10-core
  machine) runs cases of every framework side by side, after each clean
  app has run alone. For Jinja and FastHTML it cut 211 seconds to 54, with
  the same results. Nuxt runs one case at a time, because two `nuxt dev`
  servers can pick the same hot-reload port, and Next.js and Nuxt builds
  have not been timed side by side yet.
- **No browser check after a static error.** A case a tool already
  reported as an error skips the browser check. In the 2026-10-20 run (24
  mistakes, six frameworks) that is 63 of 134 cases and about 38% of the
  run's time.
- **Stored output.** A rerun runs only the cases whose inputs changed, so a
  PR that adds only mistakes or a framework runs only its new cases. A PR
  that changes a baseline (PRs 3 to 5) reruns every case of that
  framework. A report change reruns nothing, and a scoring change reruns
  only the browser checks of cases whose static error stops counting.
  Browser checks whose journey stopped early are never stored, so every run
  repeats those (4 of the 42 Jinja and FastHTML cases).

The run times in the PR table above are for one case at a time with every
browser check run. With cases side by side and the skipped browser checks, a
full run with nothing stored should take about 15 to 25 minutes for 11
frameworks: skipping about 38% of the 1.6 hours leaves about 1 hour of work,
and 5 workers make that about 12 minutes; Nuxt's 62 cases, run one at a
time, and the clean apps, run alone, keep the total above that. This is an
estimate from the 2026-10-20 per-case times and the Jinja and FastHTML
measurement, to be replaced by the first full run's time. With Reflex, add
its frontend builds for the cases no tool reported, divided by the worker
count, unless Reflex needs a `max_jobs` limit.

---

## 9. Open questions for the maintainer

1. **Ref A in server-template stacks.** Django and Jinja have no
   browser-side component model. Should m25-m28 use Alpine components
   (`x-data` with a nested component) as their natural form, or be
   `not-applicable`? Alpine has no declared inputs, so the honest answer is
   probably "not applicable for m26/m27, ported for m25".
2. **Off-by-default checks.** `typedRoutes` in Next, `typedPages` in Nuxt,
   `strictTemplates` in vue-tsc, `StrictUndefined` in Jinja, and djls for
   Django all stay off under the current policy. Should one separately
   labeled "strict setup" run be planned now, so Part 3 can show what each
   framework catches at its best?
3. **Conversions that make the code work.** If a framework turns `"1"` into
   `1` (pydantic-style conversion), is m32 written with a value it cannot
   convert (as proposed), or does the conversion count as "prevented"?
4. **Reflex run time.** If one frontend build per case is too slow, the
   Reflex runtime stage could run only for cases no static stage reported.
   That changes how a runtime result is reached for one framework, so it
   needs a decision and a note in the design doc.
5. **Lint warnings.** jsx-a11y rules in Next are warnings, so m53-m55 will
   score "static warning" for Next. This is consistent with how m09 scores
   for Citry, so no change is proposed; flagged so it is not a surprise.
6. **Run cost.** A full run at each Citry release grows to about 1.6 hours
   without Reflex and 2 to 3 hours with it, and PRs 2 to 5 each publish a
   run. Is that acceptable, or should the full matrix run less often (for
   example only when a pinned version changes) with partial runs in
   between?

### Decisions (2026-10-20)

- **Stricter settings (question 2):** there is no separate "strict setup"
  run. When a framework has a setting that turns on a stricter check, and
  other frameworks here have the same kind of check, the benchmark turns
  it on in that framework's normal setup, so the frameworks are compared
  like for like. The framework notes record each setting changed from the
  default. This applies to the next published run, so the published
  results change too. (As of PR 8, django-components and ReactPy are set
  up under it; the frameworks measured before django-components follow in
  their own PR, see section 8.)
- **Conversions (question 3):** a framework that turns `"1"` into `1`
  for you counts as "prevented". Judge it case by case, with "prevented"
  as the default.
- **Reflex (question 4):** the runtime stage runs only for the cases that
  `reflex compile` did not report. The design doc notes this.
- **Run cost (question 6):** a 1.6 to 3 hour full run is acceptable for
  this round. The full matrix does not run at every release.
- **Browser-side components in Django and Jinja (question 1):** m25-m28
  use Alpine components (`x-data` with a nested component), the way those
  stacks would write them. In PR 3 only m25 could be written naturally with Alpine:
  the nested component reads `open` through Alpine's shared scope, so m25
  misspells that read, m26 and m27 do not apply (Alpine has no required or
  typed inputs), and m28 is prevented (the child's assignment changes the
  parent's value as intended). The django-components app (PR 6) writes its
  status line the same way and gets the same three outcomes, because a
  django-components component receives its inputs only when the server
  renders it.
- **Lint warnings (question 5):** Next.js's jsx-a11y warnings score
  "Static/IDE warning", as proposed.
- **Changed numbers:** expected. Turning on the stricter settings changes
  the published results in the next run.
