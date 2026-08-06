# Getting started journey design

**Status (2026-07-26): revised after maintainer review. The complete FastAPI
path is required. Install Citry is implemented as the first review-sized
slice; the later pages remain at design stage.**

## Decision

Getting started should teach one useful layer at a time:

```text
Install Citry
  -> Build your first component
  -> Use data in components
  -> Build a page from components
  -> Add flexible content
  -> Add browser behavior
  -> Connect components in the browser
  -> Serve the page with FastAPI
  -> Call Python from a click
  -> Events state
  -> Handle and validate forms
  -> Replace part of the page from Python
       -> choose a next goal in Examples, Docs, or Reference
```

All twelve steps form the required path. FastAPI is the one teaching host so a
reader can follow a continuous example without stopping to choose a framework.
It is not a claim that FastAPI is Citry's preferred or only host. The FastAPI
page points to **Docs > Guides > Web frameworks** for Django, Flask, Starlette,
bare ASGI, and bare WSGI setup.

The path deliberately reaches beyond server rendering. It gives the reader a
taste of the whole Citry workflow: Python builds the first page, Alpine handles
instant browser behavior, Citry passes browser values and handlers across
component boundaries, a browser action calls Python, State carries a value to
the next call, a typed form reports an error, and a returned render replaces a
chosen part of the page.

This is still a journey, not a tour of every feature. By the end, a reader
should have earned the practical mental model “Livewire for Python” from what
they built. The tutorial should not use that comparison as a slogan or assume
the reader already knows Livewire.

## Evidence used

This proposal combines:

- the ranked reader jobs in [`reader_jobs.md`](reader_jobs.md), especially
  clean installation, first component, composition, host integration, browser
  updates, and secure Events;
- all seven current Getting started pages and their current navigation;
- current component rendering, browser runtime, `$component`, host adapter,
  fragment, and Events implementation and tests;
- the accepted teaching pattern in
  [`Your first component`](../../../docs_site/content/getting-started/your-first-component.md);
- the official beginner journeys for
  [Vue](https://vuejs.org/guide/quick-start.html),
  [React](https://react.dev/learn),
  [Alpine](https://alpinejs.dev/start-here),
  [Django](https://docs.djangoproject.com/en/6.0/intro/tutorial01/),
  [FastAPI](https://fastapi.tiangolo.com/tutorial/first-steps/), and
  [htmx](https://htmx.org/docs/).

The comparable journeys agree on a useful rhythm: show a complete result, let
the reader change it, explain the new mechanism, and show how to confirm it
worked. They branch when setup genuinely differs, not whenever the product
offers another option.

## What the journey must achieve

By the end of the required path, a new reader should be able to:

- install Citry and confirm that the installed package works;
- recognize a component, its HTML, its named options, and the places where
  another page can insert content;
- use components together to make a complete page;
- write one small render check that looks for meaningful output rather than
  Citry's generated attributes;
- add one visible Alpine interaction and use `$component` to reach values that
  Python prepared for that component;
- pass reactive browser values and a handler into a child component without
  confusing those values with Python render inputs;
- run the same example through FastAPI with the correct Citry initialization,
  mounting, and signing setup;
- follow one complete interaction from a person's action, through a Citry
  request and Python handler, to a visible browser result;
- keep a value across server calls with State and explain that the browser
  carries a signed value rather than trusted private server storage;
- submit and validate a typed form and show useful loading and error feedback;
- replace a chosen part of the page with HTML rendered in Python and find the
  other actions a handler may return;
- explain, in ordinary language, what runs in Python, what runs in the browser,
  and how Citry joins the two;
- choose a next path without learning Citry's internal transport or rendering
  architecture.

Getting started does not need to teach every kind of input, slot, dependency,
Alpine directive, Event action, fragment update, host adapter, or rendering
strategy. It teaches one representative path through each necessary layer and
links to Docs, Examples, and Reference for the complete choices.

## Page sequence

Each page has one visible result and one main new idea. Existing URLs stay in
place when they still describe the job. New URLs and redirects are proposed
where the current address would misname the new page.

| Step | Page and URL plan | What the reader makes | New ideas | Required checkpoint |
| --- | --- | --- | --- | --- |
| 1 | **Install Citry** at `/getting-started/installation/` | A tiny rendered proof after installing the package | Package installation and one supported render command | The command exits successfully and prints the stated HTML |
| 2 | **Build your first component** at `/getting-started/your-first-component/` | The existing Card with content and a colored border | Component, template, one named option, one replaceable content area, component CSS | The rendered Card has the chosen words and color; the missing-input example produces the stated helpful error |
| 3 | **Use data in components** at `/getting-started/data-in-components/` | A component that turns Python data into a useful list or choice | Deepen the Card's typed `Kwargs` with automatic template variables, expressions, a small condition or loop, defaults, and `template_data()` only for a derived value | Changing the Python data changes the stated text, attributes, and repeated content; a missing or misspelled name is fixed in context |
| 4 | **Build a page from components** at `/getting-started/components-in-templates/` | A complete page that uses more than one component | `<c-Name>` tags, literal attributes, `c-name="expression"` dynamic values, nesting, registration only as far as the example needs it, and one meaningful render assertion | The page renders its parent and child components with the expected content, and the small test detects a changed result |
| 5 | **Add flexible content** at `/getting-started/adding-slots/` | A component with a named area and useful fallback content | Deepen the Card's default slot with named slots, fills, fallback content, and a more useful typed `Slots` shape | The reader sees both the supplied-content and fallback versions |
| 6 | **Add browser behavior** at a new `/getting-started/browser-interactivity/` URL | A details panel that opens immediately in the browser | Plain Alpine, then component JavaScript, `$component`, and `js_data()` | A plain-Alpine-only component works by itself with no other runtime trigger; separately, two `$component` instances keep their own Python-provided browser data |
| 7 | **Connect components in the browser** at a new `/getting-started/client-props-and-handlers/` URL | A parent controls a focused child action | Declared client props, `$c-props`, a handler on a component tag, and the parent and child scope boundary | A changed parent value reaches the child reactively, and the child's action runs the handler in the parent scope |
| 8 | **Serve the page with FastAPI** at a new `/getting-started/fastapi/` URL | The same page running from a minimal FastAPI application | The exact Citry instance, imports before initialization, FastAPI lifespan setup, `HTMLResponse`, mounting, and a signing secret | The page and a Citry-owned route both return successfully from the ASGI server |
| 9 | **Call Python from a click** at a new `/getting-started/call-python/` URL | A browser action that visibly completes after a Python handler runs | `class Events`, one `@c-click`, the request-handler-response path, loading feedback, and `actions.Dispatch` | The click reaches Python and the returned browser event changes the intended result without replacing HTML or reloading the page |
| 10 | **Events state** at a new `/getting-started/state/` URL | A value that survives repeated server-handled actions | `class State`, deriving initial State from `Kwargs`, a refreshed signed token, and a dispatch carrying the visible result | Repeated actions use the previous signed value, the returned browser event shows the new value without replacing HTML, and a fresh page load starts from the stated initial value |
| 11 | **Handle and validate forms** at a new `/getting-started/forms/` URL | A small form with a success result and an inline validation error | Typed handler data, `@c-submit.prevent`, `EventError`, `$error`, `$loading`, and a success dispatch | Invalid input shows the promised field error; corrected input reports success without replacing HTML or reloading the page |
| 12 | **Replace part of the page from Python** at a new `/getting-started/server-rendered-updates/` URL | A chosen panel replaced with freshly rendered HTML | `actions.Render`, an explicit target and one swap mode, fragment asset delivery, and the boundary between a component return and a targeted render | The action replaces only the intended panel and any required Citry assets continue to work after insertion |

Use action-led navigation labels, even when the source filename remains for URL
stability. `Parametrising components` is precise but makes a new reader decode
the task. `Use data in components` says what they can do and makes room for
the small amount of template logic needed by the next page.

## Page gate matrix

This matrix fills the page-level fields required by the Stage 4 gate. The
sequence table above owns each page's observable acceptance check.

| Page | Primary job and situation | Prerequisite | Navigation placement | Important dependency |
| --- | --- | --- | --- | --- |
| Install Citry | `JOB-023`, learning from a clean environment | A supported Python and operating-system target plus access to the promised package artifact | **Docs > Getting started**, first | Accepted package and platform support scope |
| Build your first component | `JOB-002`, learning after installation | An installed compatible Citry environment; basic HTML is helpful but not required for copying the example | **Docs > Getting started**, second | Accepted Card source and first-component tests |
| Use data in components | `JOB-003`, building a useful data-driven component | The first component result and the Python values the example will display | **Docs > Getting started**, third | Template expressions, `c-if` or `c-for`, and the plain-schema runtime-type boundary |
| Build a page from components | `JOB-003` and the first checkpoint for `JOB-012`, building and testing composition | A working data-driven component, its import or registration path, and basic Citry template syntax | **Docs > Getting started**, fourth | Component-tag lookup, literal and dynamic inputs, document serialization, and a render assertion |
| Add flexible content | `JOB-003`, building a component that accepts different content shapes | Working composition and the default slot introduced by the Card | **Docs > Getting started**, fifth | Named fills, fallback content, and typed `Slots` |
| Add browser behavior | `JOB-003`, adding immediate behavior before a server is involved | The component path, a complete rendered document, and a browser | **Docs > Getting started**, sixth | `$component`, `js_data()`, the pinned Alpine runtime, and the activation prerequisite recorded below |
| Connect components in the browser | `JOB-003` and `JOB-009`, connecting reusable browser behavior | A working component-local interaction and a parent with a child component | **Docs > Getting started**, seventh | Declared client props, `$c-props`, relocated handlers, and exact source-scope rules |
| Serve the page with FastAPI | `JOB-005`, integrating the tutorial application | The standalone page, FastAPI and an ASGI server, and control of application startup | **Docs > Getting started**, eighth | Exact Citry instance, import and registration order, lifespan initialization, mounting, runtime routes, and signing configuration |
| Call Python from a click | `JOB-010`, entering server-handled behavior | The mounted FastAPI application and the browser execution model | **Docs > Getting started**, ninth | Mounted Events routes, same-origin and host security behavior, handler discovery, returned dispatch, and a tested stateless round trip |
| Events state | `JOB-010`, adding server-handled continuity | The first stateless Event and a render input that can seed State | **Docs > Getting started**, tenth | State schema, token signing and validation, automatic token refresh, and a returned dispatch without a render action |
| Handle and validate forms | `JOB-010` and `JOB-012`, collecting and checking user input | The mounted Events path and the State security boundary | **Docs > Getting started**, eleventh | Typed form data, validation errors, loading and error magics, success dispatch, and host security responsibilities |
| Replace part of the page from Python | `JOB-009` and `JOB-010`, updating a chosen region | The mounted application, returned values, and the component used as the replacement | **Docs > Getting started**, twelfth and final | `actions.Render`, target resolution, one swap mode, fragment dependencies, and a journey browser test |

Installation remains the Docs top-navigation destination. Every page in this
sequence stays under **Docs > Getting started** so the required path is visible
in the sidebar. **Docs > Guides > Web frameworks** owns other host setup, and
the focused pages under **Docs > Events** own the complete Events model. The
tutorial links to the relevant Events page at first use instead of moving that
depth into Getting started.

### Why FastAPI comes before Events

A complete HTML document can carry Citry's browser runtime and component-owned
assets without a running web framework. That makes the browser interaction a
good lesson before FastAPI.

An Event is different. The browser has to call an Events HTTP route, and the
same Citry instance that owns the components has to be initialized and mounted
in a web application that can serve that route. Stateful Events also need an
appropriate signing secret and host security configuration. A supposedly
host-neutral Event tutorial would hide a real prerequisite.

FastAPI gives the continuous tutorial one exact setup to test and explain. The
page installs FastAPI and an ASGI server explicitly, uses one application
lifespan, returns Citry's document as an `HTMLResponse`, and mounts Citry's
routes. It also says that the framework is a teaching choice. The Web
frameworks guide remains under **Docs > Guides** and owns equivalent setup for
other hosts.

### Why browser behavior comes before server behavior

The reader can see where the first behavior runs without learning routes,
requests, CSRF, State tokens, or server updates at the same time. The later
Event tutorial can then say what changes: this click crosses from the browser
to Python. It should trace the click, request, handler, response, and page
update in that order.

Do not present browser state and server State as two spellings of the same
thing. The detailed boundaries belong to Client interactivity and Server
events, but the beginner journey must establish that the two execution places
exist.

### Plain Alpine must activate Citry's runtime

Current behavior is contextual and surprising. A component whose settled HTML
contains only `x-data`, `@click`, and `x-text` keeps those attributes, but
Citry emits no client graph and no Alpine runtime. The directives remain inert.
The same markup starts working if an unrelated component elsewhere on the page
uses `$component`, Events, State, or another feature that happens to load the
runtime. A template-authored slot fill is another current special case.

That means plain Alpine is not forbidden, but its behavior can change when an
unrelated component is added or removed. Getting started must not teach or
work around that defect. Before the **Add browser behavior** page is authored,
Citry should make every rendered Alpine directive activate its owning
component. Detection must include Alpine's standard forms:

- `x-*`, including `x-data`, `x-show`, `x-text`, `x-model`, and `x-bind`;
- `@*`, Alpine's event-listener shorthand;
- `:*`, Alpine's binding shorthand.

The decision belongs to settled output, not only to template source. By that
point Citry has resolved dynamic `c-x-*`, `c-@*`, and `c-:*` attributes,
`c-bind` mappings, conditions, loops, slots, cached output, and `on_render()`
replacements. The detector must inspect real start-tag attributes rather than
searching arbitrary strings, or examples shown in `<pre>`, comments, attribute
values, and script text can cause false activation.

The recommended behavior is full client-graph activation, not merely loading
Alpine globally. Citry's graph supplies the component boundary and slot
ownership rules that make Alpine behavior predictable. Loading Alpine without
the graph would let the same nested component inherit an outer `x-data` in one
page but remain isolated in another, depending on what else activated Citry.

The activation and scope rules are:

- an Alpine directive in component-authored output activates that component
  occurrence; a child-only directive activates the child branch, while an
  outer directive preserves Citry's descendant boundaries;
- an Alpine directive in a template-authored fill activates the lexical caller
  and receiver path and keeps the existing source-to-slot projection;
- an Alpine directive in detached Python slot content or a typed slot default
  activates the graph and receiver boundary needed to run it, but the detached
  region keeps an empty isolated base. It does not gain the receiver's data or
  an invented caller scope.

This changes current product behavior and therefore needs its own implementation
plan, regression tests, protocol and Alpine design updates, changelog entry,
and payload check. `document` and `fragment` output should gain the runtime and
graph when their settled output needs Alpine. A `fragment` serialization that
needs the runtime but has no mounted Citry prefix must raise the existing
missing-route error instead of emitting inert markup. The explicit `simple`
and `ignore` dependency strategies remain no-runtime modes. Existing users who
load a separate Alpine build may need to remove it to avoid two Alpine copies.

Automatic activation does not make `js_data()` globally available. That data
belongs to a component's `$component` callback, so the tutorial still uses
`$component` when it passes Python data into browser code. Plain Alpine markup
that needs no Python-provided data should work without adding an otherwise
meaningless `$component` block.

## Example strategy

Keep a recognizable mini-site across nearby pages, but do not force every
feature into one ever-growing class.

- Keep the accepted Card tutorial stable. Later pages may use that Card rather
  than silently changing the source readers just copied.
- Add one small companion component when a concept needs a clearer shape. For
  example, a page component can arrange Cards, while a panel or disclosure can
  demonstrate browser behavior.
- Repeat the minimum complete context on every page so a reader arriving from
  search can succeed. Link the prerequisite for readers who want the full
  sequence.
- Prefer familiar outcomes such as showing details, choosing an option, or
  updating a count. Do not invent a demo whose only purpose is to expose an API
  name.
- Let clarity beat continuity. A strained Card-based Event example is worse
  than a small new example that makes the browser-to-Python trip obvious.

Every page should follow this teaching loop:

1. State what the reader will see or be able to do.
2. Show the complete file or smallest honest set of files.
3. Give the exact command or browser action.
4. Show the expected result.
5. Explain only the new lines and names.
6. Show one natural mistake beside its fix when it improves recovery.
7. Recap the result and offer two or three meaningful next goals.

The detailed beginner-writing principles and examples live in
[`docs_content.md`](../docs_content.md#teach-beginner-tutorials-from-the-result-backward).

## Disposition of current pages

| Current page | Decision | Material to keep or move |
| --- | --- | --- |
| Installation | Implemented: rebuilt and narrowed | Keeps one environment setup, the recommended install, one executable render proof, focused recovery, and the next journey action. Generated attributes, framework mounting, `template_data()`, and CLI depth stay with their canonical pages. |
| Your first component | Keep as the editorial anchor | Preserve its result, pace, plain language, executable source, and focused tests. Adjust only links made stale by the new journey. |
| Components in templates | Rebuild around a complete page | Keep simple component tags and composition. Move full prop rules and `CitryElement` reuse to Concepts or Reference. |
| Parametrising components | Rebuild with typed options first | Keep required and default values. Remove the loose-dictionary-first path and ordinary-HTML dynamic-attribute detour. |
| Adding slots | Rebuild from content the reader already recognizes | Keep named areas, fills, and fallback content. Use ordinary words before `slot` and `fill`, keep Python-filled variants as later depth, and align with typed `Slots`. |
| Adding JS and CSS | Implemented: split by reader job | The beginner interaction moved to Add browser behavior. Asset files, placement, schemas, execution phases, and editor highlighting now live under Advanced JS and CSS dependencies. Hooks and template-less bases remain with their advanced owners. |
| Adding dependencies | Implemented: merged into Advanced | Supported third-party and shared-asset guidance now lives under Advanced JS and CSS dependencies, with inheritance linked to Subclassing components. |

Navigation and internal links point at the canonical owners. The redirect map
stays empty until the published site has a URL that must keep working after a
move.

## Canonical ownership after the split

| Reader question | Canonical owner | Getting started treatment |
| --- | --- | --- |
| How do I make one visible browser interaction? | New browser interaction tutorial | Teach the complete smallest path |
| What can `$component` do? | Client interactivity | Use only the one property or method the tutorial needs, then link |
| How do Citry and Alpine start, preserve scope, or handle plugins and CSP? | Alpine runtime | Say that a rendered Alpine directive starts Citry's owned runtime after the product fix; defer lifecycle and configuration details |
| How do browser values and handlers cross a component boundary? | New client props and handlers tutorial, then Client interactivity | Teach one declared prop and one parent-owned handler; link the complete contract |
| How do component JS and CSS files, placement tags, inheritance, URLs, modules, and dependency strategies work? | Advanced JS and CSS dependencies, with exact APIs in Reference | Mention only the asset form used by the example |
| How do `js_data()` and `css_data()` validate and serialize values? | Typing and validation plus Reference | Pass one obvious value and explain its visible effect |
| How do I configure my editor for embedded Citry code? | Open Stage 4 owner: a user-facing Editor setup guide under Guides, not Community development | Do not interrupt the reader's result until that owner exists |
| How does a browser action call Python? | First server Event tutorial, then Server events and Event bindings | Trace one stateless action, then add State and a form in their own steps; defer polling, files, migration depth, and the full action catalog |
| How do I mount Citry in my framework? | Web frameworks | Teach FastAPI once in the required path and link other adapters at first use |
| How does State remain trustworthy? | Keep State between calls and Security | Explain the signed, browser-carried boundary when State first appears; link the complete storage, age, and authorization rules |
| How can a handler update the page? | Final Getting started page, then Event actions and HTML fragments | Demonstrate one targeted `actions.Render`; link the other returned actions and full fragment contract |
| How do I test this? | Testing components, with an Examples recipe when useful | Give a small check on each page and link to the durable testing workflow |

## Page briefs

### Install Citry

Start from a clean-environment assumption. Choose one recommended install
command, name any supported Python prerequisite that actually blocks it, and
give a tiny proof that is independent of a host framework. Alternative package
managers and the command inventory can follow as links.

Do not make this a second first-component tutorial. Its job is to establish
that the installed artifact imports and renders, then hand the reader to the
Card.

### Use data in components

Begin with a result the reader can compare, such as a useful list changing
when the Python data changes. Describe `Kwargs` as the named options the
component accepts. Teach the preferred typed pattern first, including one
required value and one default. A matching `Kwargs` field is already available
in the template; do not teach a `template_data()` override for simple
passthrough. Introduce it only if the example computes a new value for display.

Use one expression, one dynamic HTML attribute, and only the smallest condition
or loop that the visible result needs. Link the complete syntax rules. Repeat
the first tutorial's warning that annotations help editors and type checkers
but do not reject the wrong value type at runtime.

### Build a page from components

Render more than one component inside a parent so composition solves an
obvious repetition or layout problem. Explain how Citry finds the component
tag only as far as the reader must act. Link registration and autodiscovery for
the complete lifecycle.

Avoid advanced element reuse and render identity. They answer later questions
about architecture, not the first page a reader builds.

End with one small test that renders the page with `str(...)` and checks
meaningful text or markup. Do not make generated `data-cid-*` attributes part
of the reader's contract. Fresh-instance isolation, fixtures, browser tests,
and host tests remain in the Testing guide.

### Add flexible content

Start with ordinary language: content placed between component tags appears in
the component's replaceable area. Then name that area a slot. Add one named
area and one fallback whose effect is visible.

Use `class Slots` consistently with the typed Card pattern. A compact note may
show the Python form, but it should not become a second tutorial inside the
page.

### Add browser behavior

Provide a complete document and an interaction the reader can try by opening
it. First prove the product prerequisite with a component that contains only
plain Alpine directives. Render it alone, with no `$component`, Events, State,
client binding, slot-fill activation, or unrelated component, and browser-test
the interaction. This is a required regression check, not a reader workaround.

Then introduce `$component` when browser code needs a value or action that
belongs to that Citry component. Pass one value from Python through
`js_data()`, and show that two instances keep their own value. Test this path
separately so `$component` cannot hide a regression in plain-Alpine activation.

Explain that Alpine supplies the small browser behavior Citry uses here. Do
not turn the page into an Alpine directive catalog or a client-runtime
lifecycle guide. This page depends on the plain-Alpine activation change above.
Use `$component` because the example genuinely consumes `js_data()`, not as a
hidden incantation required to make unrelated Alpine directives run.

### Connect components in the browser

Use a parent and a small child component so the boundary solves a visible
problem. Give the child one declared client prop and pass its value with
`$c-props`. Put one Alpine handler on the child component tag and show that it
runs where the parent wrote it. Use ordinary words such as “the parent page”
and “the button component” before introducing source scope or relocation.

Keep the three data paths distinct:

- `Kwargs` are Python values supplied for a server render;
- `$c-props` carries reactive browser values from a parent component to a
  child component;
- a handler written on `<c-child @click="...">` runs in the parent's Alpine
  scope even though the browser listens on the child's rendered element.

Do not turn the page into the full client graph protocol. Its browser check
must prove that the value reacts and that the handler sees the parent's data.

### Serve the page with FastAPI

Use one complete minimal FastAPI application and the same components from the
browser lessons. Install FastAPI and the selected ASGI server explicitly. Show
one Citry instance, all required component imports before initialization, the
FastAPI lifespan, an `HTMLResponse` route, Citry mounting, and the signing
secret needed by the following State lesson. Verify both the page and a
Citry-owned route.

Say plainly why HTTP routes are now needed: the next browser action has to
reach Python. Link **Web frameworks** beside the first FastAPI-specific setup
so Django, Flask, Starlette, bare ASGI, and bare WSGI users can find their path.
Do not duplicate those adapters in this tutorial.

### Call Python from a click

Start with a stateless handler so the first result does not require a State
schema or token. Earlier Stage 4 browser evidence established that this is a
valid product shape, but later Events protocol changes invalidated that test
baseline. The tutorial action needs a fresh executable browser test against
the settled protocol. Follow the interaction in the order the reader
experiences it: action, request, handler, returned result, page update. Name
`class Events` and the chosen `@c-*` attribute through what they make happen.

Keep the first call stateless because the next page deliberately teaches
State. Return `actions.Dispatch` with a small JSON detail and let an Alpine
listener display that result. This proves that Python completed while keeping
HTML replacement for the final page. The executable draft must settle the
exact action and event name.

### Events state

Add `class State` only after the reader has seen a stateless call. Seed one
field from a same-named `Kwargs` value, change it in the handler, and include
the new value in a returned dispatch so Alpine can display it. Citry also
refreshes the signed State token without returning new HTML, and the following
call sends that refreshed token back. Explain at the moment it matters that
Citry signs State carried by the browser. A signature detects changes; it does
not encrypt the value, authenticate the person, or authorize access to an
application record.

Prefer a small continuity task over a toy API tour. The visible checkpoint
must prove that the second action received the value produced by the first.

### Handle and validate forms

Use a form whose fields have an obvious useful meaning. Show a typed handler
input, `@c-submit.prevent`, a loading state, one `EventError`, and an inline
`$error` message. Demonstrate the invalid submission before the corrected one
so the recovery path is part of the tutorial rather than a footnote. Let the
successful handler dispatch a small browser event instead of replacing HTML.

Keep form security proportionate and concrete. Citry validates the declared
data and its transport boundary; the application still owns authentication,
authorization, and safe business rules.

### Replace part of the page from Python

End the required journey by replacing one named panel with
`actions.Render`. Use one explicit target and one swap mode. Trace what the
reader sees: Python renders the replacement, Citry carries the HTML and needed
assets as a fragment, and the browser changes only the chosen region.

This is the first lesson that returns new HTML. It is the right place to name
the deeper mechanism because the reader has already used returned browser
actions and State reconciliation. Link to **HTML fragments**
for manual fragment responses and insertion details. Link to **Event actions**
or the action Reference for returning a component, redirecting, dispatching a
browser event, changing a URL, returning data, and downloading a file. Do not
teach every action inline.

## Page-level acceptance checks

Before a Getting started page is ready for maintainer review, check that:

- its promised result works from the prerequisites it states;
- every complete code block is executable and formatted according to the
  component authoring rules;
- every intentionally shortened block says what was left out;
- the expected command output or browser behavior matches current Citry;
- any likely failure shown on the page is reproduced and its correction works;
- the page introduces no term before the reader needs it;
- the page owns one job and links, rather than copies, deeper contracts;
- its first screen explains the useful result instead of listing features;
- its last section says what the reader accomplished and offers meaningful
  next goals;
- its direct-link reader can identify required prior knowledge;
- its light, dark, narrow, keyboard, generated Markdown, and search
  presentations remain understandable where the page contains rich output;
- navigation and inbound links point at each page's canonical owner.

The journey also needs an end-to-end browser check across the chosen host and
all four server-interaction pages. Page-level passing tests do not prove that a
new reader can carry the same application from a local document to FastAPI,
State, validation, and a targeted update without missing setup.

## Authoring order

Write and review the pages in dependency order, one small slice at a time:

1. narrow Installation and keep the accepted Card stable;
2. write the data-driven component page, then the page-composition tutorial;
3. write slots after the composition vocabulary is settled;
4. design and implement settled-output Alpine activation, including the
   ownership, fragment, cache, compatibility, and payload checks recorded
   above;
5. build and browser-test the standalone interaction and component-boundary
   lesson before writing prose around them;
6. build the exact FastAPI application and check its startup, page, and Citry
   routes;
7. add the stateless Event, State, form, and targeted-render lessons to that
   application one at a time, with focused checks and one complete browser
   journey;
8. verify and repair the Web frameworks guide so the FastAPI teaching choice
   has honest paths to the other supported hosts;
9. move displaced JS, CSS, dependency, editor, and advanced facts only after
   their destination is verified;
10. update navigation, search projections, and next-step links
    after the page set is coherent.

The maintainer's commit remains the approval gate between review-sized waves.

Do not add a separate Getting started landing page or testing page in the
first wave. Installation is the single entry point, and each tutorial owns a
small executable checkpoint. The composition page teaches the first explicit
render assertion and links prominently to the existing Testing guide, which
keeps primary reader job `JOB-012` in the journey without adding a second
testing guide. The final page provides the deeper-learning choices. Reconsider
a landing page only if navigation testing shows that the twelve visible steps
are hard to scan; reconsider a testing tutorial if embedded checks and the
existing Testing guide leave a distinct beginner job unserved.

## Open decisions and falsifying checks

These choices should be settled with executable drafts, not prose preference:

- Choose one continuous mini-application that gives the browser, State, form,
  and targeted-update steps useful outcomes without turning into a product
  demo. The accepted Card can remain stable while companion components carry
  the later tasks.
- Choose the smallest browser interaction that genuinely uses `js_data()` and
  `$component`. Its test is separate from the required plain-Alpine-only
  regression check, so neither path can make the other pass accidentally.
- Choose the useful payload and visible result for the fixed
  `actions.Dispatch` lesson so it clearly proves Python ran without explaining
  targeted HTML replacement before the final page.
- Settle and implement the Alpine activation behavior above before claiming it
  in reader-facing prose. Falsify the detector with code samples, comments,
  raw-text elements, dynamic attributes, discarded renders, slots, fragments,
  and cached output.
- Keep **Web frameworks** discoverable from the FastAPI page, but do not treat
  another host as a substitute or rejoin path in this first wave. Equivalent
  end-to-end host journeys need their own later design and evidence.
- Test the proposed action-led labels with direct navigation tasks. If readers
  search more successfully for established terms such as “props” or “slots,”
  preserve those terms in page descriptions, headings, and search metadata
  without making the sidebar harder to understand.

This proposal is falsified if the browser-only example cannot run from a
complete document without a mounted host, if the FastAPI application cannot
support the exact Event, State, form, and fragment path promised here, if
settled Alpine activation cannot preserve Citry's documented component and
slot boundaries, or if executable drafts reveal that a page needs concepts
before the page that introduces them. Update the journey rather than hiding
those prerequisites in prose.
