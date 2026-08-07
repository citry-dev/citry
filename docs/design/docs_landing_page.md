# Design: Citry landing page

**Status (2026-07-29): first iteration implemented and visually inspected;
publication review remains.** Research 1, Research 2, Research 3, and Research 5
now establish the message, 1,024-component field, theme-aware cosmic-blueprint
art direction, comparison framing, and human/community direction. The live
implementation uses a bounded canvas projection with a CSS fallback, readable
server-rendered copy, and focused desktop, mobile, dark-theme, and reduced-motion
checks. Participant studies and comparative agent experiments remain later
validation work, not gates for iterating on the working page.

Related decisions live in [`docs_site.md`](docs_site.md),
[`docs_content.md`](docs_content.md), [`docs_blog.md`](docs_blog.md), the
provisional [v1 beta product charter](v1_beta_research/product_beta_charter.md),
and the proposed [IDE integration](ide_integration.md). The current page is
[`docs_site/content/index.md`](../../docs_site/content/index.md).

## What the landing page must accomplish

Citry has an unusual opportunity: its landing page can be both the explanation
and the proof. The site is built with Citry, and the page can exercise a large
component tree, component-owned browser behavior, server rendering, and precise
failure handling in front of the reader.

That opportunity does not relax the first requirement. A visitor must be able
to answer these questions from the first viewport without interpreting a brand
metaphor:

1. What is Citry?
2. Is it for Python and the web?
3. What can I build with it?
4. Why might I choose it over my current frontend approach?
5. Is it free and open source?
6. What should I do next?

The desired feeling is unbounded capability: one small component can compose
into hundreds or thousands, and the same model can grow into a rich
application. The visual language should feel expansive, precise, alive, and a
little surprising. It must not make the product itself mysterious.

## Decision principles

1. **Clarity before cleverness.** The title or its immediately adjacent sentence
   must say "frontend framework", "Python", and what it builds. A poetic line
   may follow once the category is clear.
2. **Make spectacle prove a product claim.** The component field is not generic
   decoration. Each visible cell is produced from a Citry component, and the
   page exposes that fact in a verifiable way.
3. **Show code and an outcome early.** A developer should see a small component,
   the HTML it produces, and an obvious path to run it without reading a feature
   inventory.
4. **Scope every comparison.** "Safer", "faster", "simpler", "integrated", and
   "AI-friendly" need a named baseline and a named class of work or bugs.
5. **Sell what is shipped.** The IDE linter is still a proposal. It can shape a
   future claim and benchmark track, but it cannot support launch copy today.
6. **Be candid about fit.** The page should say who benefits most and provide a
   short path to limitations and compatibility. Honest boundaries build more
   confidence than universal claims.
7. **No visual effect gets a performance or accessibility exemption.** The page
   is the product demonstration. A slow, distracting, inaccessible demo would
   prove the wrong thing.
8. **Show the people without inventing a crowd.** Named responsibility, honest
   project history, and reachable ways to participate are stronger signals than
   anonymous counters, staged testimonials, or a community size the project has
   not yet earned.

## Research method and limits

This first research pass combines three kinds of evidence:

- primary product documentation for the actual capabilities and tradeoffs of
  Django, Jinja, React, Vue, Livewire, Reflex, NiceGUI, Flet, Astro, Svelte,
  htmx, and FastAPI;
- current surveys and research about AI-assisted development and template
  failures; and
- recent developer discussions, used as qualitative demand signals rather than
  population-level facts.

The sources were checked on 2026-07-28. Search results and community threads are
not user research on Citry's own audience. That limits claims about measured
preference, but it does not prevent a reasoned first iteration. Once Citry has
real traffic, users, and stable examples, comprehension and task studies can
challenge these decisions.

An independent adversarial review ran on 2026-07-28. It found that the original
Research 1 and Research 5 plans overemphasized future experiments where the
project currently needs expert decisions. It also tightened public-data service
and redistribution terms. A separate adversarial audit shaped Research 2's
fixed payload, paired baseline, invalid-sample, lab-metric, and failure-matrix
contract before measurements ran. Those findings are incorporated below. The
document remains exploratory where visual and complete-page evidence are
missing, not because participant research must happen before the skeleton
exists.

## What developers appear to ask in 2026

The usual landing-page checklist becomes more useful when phrased as actual
evaluation questions.

### "What is this, in terms I already know?"

An evaluator is not asking for a mission statement. They are trying to classify
the product quickly: framework or library, frontend or full stack, server or
browser, language, and intended project shape.

Current framework homepages that do this well use a concrete category sentence:

- [FastAPI](https://fastapi.tiangolo.com/) calls itself a web framework for
  building APIs with Python and standard type hints.
- [Astro](https://astro.build/) calls itself a JavaScript web framework for
  fast, content-driven websites.
- [Svelte](https://svelte.dev/) follows its expressive headline with a direct
  explanation that it is a UI framework compiling HTML, CSS, and JavaScript
  components.
- [htmx](https://htmx.org/) says exactly which browser capabilities it exposes
  through HTML attributes.

The July 2026 [Nx homepage](https://nx.dev/) is a useful stress test. Its hero
uses large fragments such as "Smart", "Monorepos", and "Fast CI", plus the
abstract phrase "amplifies both developers and AI agents". A concrete sentence
eventually says that Nx optimizes builds, scales CI, and fixes failed PRs. The
[Nx introduction](https://nx.dev/docs/getting-started/intro) is clearer sooner:
it calls Nx a build system for JavaScript and TypeScript monorepos and then says
what it improves. Citry should place its equivalent concrete sentence in the
hero, not make readers hunt for it.

A Hacker News discussion of the [Ash Framework landing
page](https://news.ycombinator.com/item?id=43945477) supplies a recent version
of the same complaint: the opening did not give one reader enough reason to
continue, while the linked material felt like a firehose. This is anecdotal,
but it describes the failure mode the Citry page must test directly.

### "Can you prove the difference quickly?"

In a January 2026 discussion asking what would make someone try a [new web
framework](https://www.reddit.com/r/webdev/comments/1qbvwta/what_would_make_you_consider_trying_out_a_new_web/),
the strongest response was that a new framework must be significantly better
and prove that quickly amid a lot of noise. Other replies asked for full-stack
compatibility, fewer dependencies, less build tooling, strong opinions, and
predictable performance.

The implication is not to add more feature cards. It is to select two or three
differences and make each observable:

- introduce a typo and show the exact early error;
- render a large component field and publish its measured cost;
- show one component owning HTML, browser behavior, CSS, and a Python handler;
- show the same component mounted in a named Python host.

### "How much stack am I adopting?"

Recent discussions from Python backend developers repeatedly ask whether a
modern interface requires a separate application, build pipeline, and large
dependency graph. Examples include a January 2026 [framework-choice
thread](https://www.reddit.com/r/webdevelopment/comments/1qdopyy/which_framework_to_start_a_new_project_in_2026/),
a May 2026 discussion about [managing tools rather than building
sites](https://www.reddit.com/r/webdev/comments/1tcnil0/at_what_point_did_web_development_start_feeling/),
and a June 2026 question about [modern standards and unchecked
dependencies](https://www.reddit.com/r/webdev/comments/1uap0pj/modern_standards/).
These threads are anecdotes, but the repeated questions are useful:

- Do I need Node and a frontend build?
- Does this fit Django, FastAPI, or another host I already use?
- Is browser behavior available when I need it, without making every page a
  client application?
- Am I adopting generated frontend code that becomes difficult to debug?
- Is this mature enough for production work?

Citry has a strong answer to the first three. It must answer the last two with
evidence and beta-appropriate candor.

### "Will errors be loud and useful?"

This question matters more in AI-assisted work. The [2025 Stack Overflow
Developer Survey](https://survey.stackoverflow.co/2025/ai) reports that 46% of
respondents distrust AI-tool accuracy while 33% trust it. A 2026 empirical
study of [template-engine application
bugs](https://arxiv.org/abs/2604.27692) found abnormal rendering, including
unexpected or blank output, to be the most common symptom in its dataset, with
silent failures particularly difficult to diagnose.

This makes Citry's early, structured feedback strategically relevant. It does
not prove that Citry is the best framework for AI. It does suggest a testable
thesis: an agent can correct work faster when component contracts, template
bindings, and event schemas reject mistakes before a browser session or user
report is needed.

### "Can I trust the project?"

Evaluators look for maturity signals that fashionable homepages often bury:

- exact supported Python, host, and browser versions;
- current release status and stability policy;
- license and source link;
- testing and deployment guidance;
- security boundaries;
- upgrade and migration information;
- examples that run against the current release; and
- a visible path to support.

The provisional beta charter makes these release gates, not decorative trust
badges. The landing page should surface the concise facts and link to the full
evidence.

## The product truth we can market

The landing page needs a smaller, stronger set of claims than the current long
homepage. This section separates current evidence from ambition.

### Strong current claims

| Claim | Current evidence | Safe landing-page form |
| --- | --- | --- |
| Python frontend framework | The `citry` package is Python-first, renders HTML components, and supplies browser and server interaction | "An open-source frontend framework for Python" |
| Familiar HTML component syntax | `<c-*>` invokes components and `c-*` evaluates dynamic attributes | "Write HTML. Turn any `<c-*>` tag into a component." |
| Explicit component contracts | `Kwargs`, `Slots`, and output-data declarations validate names and required fields at defined lifecycle points | "Catch missing and misspelled component inputs early." |
| Missing template data fails loudly | Citry raises on missing expression names; it does not render the empty string used by default in Django and Jinja | "A missing value is an error, not a blank UI." |
| Isolated render context | A child receives its own data, explicit props, provides, and slot content; it does not inherit ambient parent variables | "Components receive only the data you give them." |
| Integrated UI capabilities | Components can own HTML, JavaScript, CSS, dependencies, Alpine behavior, typed server Events, forms, State, and fragments | "One component can own markup, behavior, style, and Python handlers." |
| Host flexibility | Adapters exist for FastAPI/Starlette, Django, Flask, ASGI, and WSGI | "Use the Python web server you already have." |
| No application Node build required | Citry packages and serves its browser runtime and component assets; ordinary users do not compile a React/Vue application | "No separate frontend build required." |
| Free and open source | Package metadata and repository license are MIT | "Free and open source, MIT licensed." |
| Testable as Python and in a browser | Components render to inspectable HTML; the repository exercises browser interactions | "Render, assert, and browser-test the same component." |

"Early" must remain precise. Literal component names and inputs can be checked
when templates load and Citry initializes. Python-created components validate
when constructed or rendered according to the input type. Dynamic values that
cannot be known earlier fail at render or event validation. The page must not
compress all of these into "compile-time type safety" without qualification.

### Qualified claims

| Candidate claim | Why it needs qualification | Defensible form now |
| --- | --- | --- |
| Safer than Django | Django has mature automatic HTML escaping, CSRF middleware, authentication, and many broader security protections | "Citry prevents specific template bug classes that Django deliberately renders silently." |
| One integrated solution end to end | Citry integrates the UI layer, not persistence, authentication, routing policy, hosting, or deployment | "One integrated component system from server-rendered HTML to browser interaction." |
| Faster | Current benchmarks cover particular render workloads and machines; React/Vue browser work is not the same benchmark | Publish only a named, reproducible component-render comparison near the benchmark link |
| On par with React or Vue | Citry covers many component and interaction primitives but not their client ecosystem, tooling, native targets, or adoption | "Vue-like composition for Python server-rendered interfaces" |
| On par with Livewire | The core server-driven model is comparable, while Livewire has much greater product breadth, dedicated test tooling, and ecosystem maturity | "Livewire-style server interaction for Python, with explicit component contracts" |
| Production ready | The project is still defining a v1 beta gate | Show the exact release status and supported matrix once accepted |

### Claims that must wait

- "The best Python frontend framework for AI."
- "AI-native."
- "The safest Python frontend framework."
- "Everything you need to build any application."
- unconditional performance leadership over browser frameworks.

These are research hypotheses. They become publishable only after the claim
gates later in this document pass.

## Competitive comparison

The comparison is not one race with one winner. Each product chooses a
different boundary. Citry wins when that boundary matches a Python team's job.

### Django templates

[Django 6.0 templates](https://docs.djangoproject.com/en/6.0/ref/templates/)
provide a mature presentation language within a complete web framework.
[Django security documentation](https://docs.djangoproject.com/en/6.0/topics/security/)
documents automatic HTML escaping, CSRF protection, and other protections that
Citry must not claim to supersede broadly.

The sharp Citry difference is error prevention and component boundaries.
Django's template API documents that a missing variable normally becomes an
empty string. A 2025 proposal and 2026 Google Summer of Code project on
[stricter missing-variable
handling](https://forum.djangoproject.com/t/gsoc-2026-proposal-ergonomic-control-over-missing-variables-in-django-templates/44786)
describes the resulting broken UI states and the compatibility difficulty of
changing the default.

Citry advantage:

- first-class components and slots;
- explicit, isolated inputs rather than inherited ambient context;
- loud missing values and checked literal component calls;
- component-owned browser assets and server Events;
- the same component layer across Django and non-Django hosts.

Django advantage:

- complete application framework with ORM, authentication, admin, forms,
  middleware, mature security policy, and a large ecosystem;
- long production history and operational knowledge;
- excellent fit where basic templates and includes are enough.

Landing-page conclusion: Citry complements Django as a stronger UI layer. It is
not "Django, but safer" and it is not a replacement for Django's application
services.

### Jinja

[Jinja's default `Undefined`](https://jinja.palletsprojects.com/en/stable/api/#undefined-types)
can print, iterate, and test as false, while `StrictUndefined` opts into loud
failure. Jinja supports HTML autoescaping, but its general-purpose default
requires application configuration. Its
[sandbox](https://jinja.palletsprojects.com/en/stable/sandbox/) is mature and
explicitly documents that sandboxing alone is not perfect security.

Citry advantage:

- an application component model rather than a general text-template engine;
- loud missing values as the ordinary path;
- declared props, slots, data, assets, browser ownership, and Events;
- HTML-aware component syntax.

Jinja advantage:

- focused, mature, flexible text generation;
- macros, inheritance, i18n, async rendering, and a broad integration base;
- opt-in strict and sandbox modes for teams that configure them.

Landing-page conclusion: compare against Jinja's defaults precisely. Do not
imply that Jinja cannot be configured to fail loudly or run sandboxed.

### django-components

This is the closest server-rendered component comparison and Citry's lineage.
Current [django-components typing and
validation](https://django-components.github.io/django-components/latest/concepts/fundamentals/typing_and_validation/)
also supports declared inputs and optional runtime type validation. Its slot,
asset, extension, and component capabilities are substantial.

Citry advantage:

- Django-independent core and host adapters;
- HTML-like `<c-*>` syntax as the primary language;
- one always-isolated context rule;
- integrated current Alpine ownership and typed server Events;
- the repository's reproducible component-render benchmark currently favors
  Citry on its named workload.

django-components advantage:

- native fit with Django's template engine and ecosystem;
- established Django-specific integrations and migration path;
- overlapping advanced component capabilities that make broad superiority
  claims inaccurate.

Landing-page conclusion: use the measured benchmark and framework independence,
not a claim that Citry invented typed Python components.

### React

[React](https://react.dev/) is a library for web and native user interfaces. It
has a vast component ecosystem and a client programming model. Its own docs
recommend a full-stack React framework for complete applications, and its
[existing-project guide](https://react.dev/learn/add-react-to-an-existing-project)
notes that realistic development generally uses Node tooling. React with
TypeScript provides excellent prop typing and editor feedback.

Citry advantage:

- keep the application and UI orchestration in Python;
- render useful HTML before browser JavaScript runs;
- no separate frontend application or Node build for ordinary use;
- explicit server-side component isolation and direct Python handlers;
- smaller conceptual jump for a Python/HTML team.

React advantage:

- client-heavy applications, offline behavior, native applications, and deep
  browser control;
- mature TypeScript, editor, devtools, testing, and package ecosystems;
- an enormous hiring and knowledge base.

Landing-page conclusion: Citry is not "React in Python" and should not promise
React parity. It offers a different application boundary for server-centered
Python teams.

### Vue

[Vue](https://vuejs.org/guide/introduction.html) is progressively adoptable and
can enhance static HTML, build SPAs, or power full-stack rendering. Its
[tooling](https://vuejs.org/guide/scaling-up/tooling) includes an official
language service, template type checking, browser devtools, build integration,
and first-party testing recommendations. Vue prop validation can warn at runtime,
while TypeScript and `vue-tsc` add stronger static feedback.

Citry advantage:

- Python is the server component language and ordinary orchestration layer;
- no separate API boundary is required for server-driven interaction;
- component calls, State bindings, and server handlers share one declared
  Python contract;
- the HTML-like syntax feels familiar to Vue users.

Vue advantage:

- fine-grained client reactivity and a much wider browser ecosystem;
- mature IDE support and devtools today;
- flexible adoption from a script tag through full applications.

Landing-page conclusion: "familiar to Vue developers" is fair. "Vue capability
without JavaScript" is not, because Citry intentionally uses browser JavaScript
and has a server-first model.

### Laravel Livewire

[Livewire 4 components](https://livewire.laravel.com/docs/4.x/components) join
server-side classes, Blade markup, state, and actions. Livewire also ships DOM
morphing, Alpine integration, validation, file organization options, dedicated
component tests, and browser testing. It is the closest product analogy for
Citry's server Events and browser update model.

Citry is meaningfully comparable on these core primitives:

- server components and nested composition;
- slots;
- server state and named actions;
- form collection and validation;
- loading and error state;
- DOM morphing and stable keys;
- Alpine integration;
- browser events, redirects, polling, debouncing, and throttling;
- server-rendered unit tests and browser tests.

Citry differentiates through Python, host independence, declared input and
binding contracts, expression sandboxing, and its explicit component ownership
model. Livewire remains ahead in ecosystem maturity, Laravel integration,
dedicated testing ergonomics, documentation depth, and several product
features. Citry also lacks years of production evidence at Livewire's scale.

Landing-page conclusion: the honest claim is "Livewire-style interaction for
Python web applications" or "the closest Python answer to Livewire", followed
by the concrete Citry differences. "On par with Livewire" is too broad today.

### Reflex

[Reflex](https://reflex.dev/docs/getting-started/introduction/) builds full-stack
applications in Python by compiling a React frontend and running a FastAPI
backend. It includes a database story, deployment product, component library,
AI builder, and MCP documentation access. Its current homepage already calls
the product open-source and AI-native.

Citry advantage:

- authors write familiar HTML, CSS, and optional JavaScript rather than a
  Python representation of the DOM;
- ordinary output is server-rendered HTML, without a generated React
  application as the debugging layer;
- teams keep their existing host, routing, persistence, and deployment choices;
- template and component errors can point at the authored HTML contract.

Reflex advantage:

- a broader full-stack product including generated frontend, database,
  deployment, a large UI catalog, AI builder, and current agent documentation;
- more explicit packaging for teams that want one prescribed application
  platform.

Landing-page conclusion: Citry should own "HTML-first Python frontend" and
"fits your existing Python application". Competing with Reflex on the vague
phrase "AI-native" would erase the more defensible difference.

### NiceGUI and Flet

[NiceGUI](https://nicegui.io/documentation/section_foundations) maps Python UI
objects to Vue and Quasar components and uses Socket.IO for browser/server
communication. It supplies a large ready-made Material component set.
[Flet](https://flet.dev/) maps Python to Flutter and targets web, desktop, and
mobile from one codebase.

Citry serves a different reader:

- choose Citry for standard HTML output, custom product interfaces, existing
  Python web hosts, selective browser activation, and control over the web
  platform;
- choose NiceGUI for a rich built-in widget set and a prescribed real-time
  Python/Vue architecture;
- choose Flet when cross-platform Flutter rendering matters more than native
  HTML and integration with a conventional web application.

Recent Python discussions mention complexity as applications outgrow rapid
dashboard tools, concern about framework maturity, generated layers, build
latency, and production fit. These are useful hypotheses, not proof that all
Python UI frameworks have those problems. The page should show Citry's
architecture and support status directly rather than attack a category.

## Research 5: expert competitive-positioning audit

**Status (2026-07-28): complete for iteration one.** A fair first landing page
does not need a participant comparison study or a giant feature matrix. It
needs a defensible category, a clear fit boundary, and proof for every promoted
advantage. The detailed comparison above is sufficient to make those decisions.

Use this as the lower-page fit statement:

> Choose Citry when Python already owns your application and you want a capable
> component frontend without creating a second application stack.

Follow it with reciprocal guidance: choose React or Vue when a client-heavy or
offline application and the browser ecosystem dominate; choose Livewire when
Laravel/PHP owns the application; choose Reflex, NiceGUI, or Flet when their
generated, widget-led, or cross-platform product boundary is the desired one.
This proves confidence more effectively than declaring every alternative
inferior.

The first iteration uses five comparison conclusions:

1. Against Django or Jinja templates, lead with explicit component contracts,
   isolated data, and failures that identify the authored component boundary.
   Do not call Django unsafe; Citry can run inside Django and depends on the host
   for application security.
2. Against React or Vue, lead with one Python application, ordinary server-
   rendered HTML, and no separately maintained frontend application. Do not
   claim capability parity across client-only, offline, or ecosystem-heavy work.
3. Against Livewire, describe a similar server-centered interaction goal across
   different language ecosystems. Citry is not a Python clone of Laravel's
   complete application stack.
4. Against other Python UI frameworks, own HTML-first components and host
   choice. Avoid the vague territory of "Python full stack" or "AI-native".
5. For AI-assisted development, use the reliability benefit lower on the page:
   "Fast feedback helps people and coding agents correct UI mistakes sooner."
   Leadership claims wait for public evidence.

The landing page therefore gets a short "Choose Citry when" section, not a
winner table. A future `/docs/why-citry/` page may hold task-shaped comparisons,
limitations, migrations, and reproducible evidence once those materials exist.
Comparative human or agent tasks remain useful later validation, but they are
not prerequisites for the skeleton or the initial positioning.

## Positioning

### Recommended category

> Citry is the open-source frontend framework for Python web applications.

The category is intentionally plain. The next sentence earns differentiation:

> Build components with checked inputs and isolated data using familiar HTML,
> scoped browser behavior, and Python event handlers, without maintaining a
> separate frontend application.

"Frontend framework" communicates the job. "Python web applications" avoids
confusion with desktop GUI frameworks. "Server-rendered" should appear in the
first supporting block, though putting it in every headline risks sounding
limited before the reader sees Events and Alpine.

### Primary audience

Python developers and teams building server-rendered websites and web
applications who want reusable UI and selective rich interaction without a
separate client-heavy application architecture.

This mirrors the provisional beta charter. Secondary audiences are Django
teams seeking a stronger component layer, FastAPI/Flask teams that need a
frontend, and experienced frontend developers who prefer HTML-first server
composition for a particular product.

### The integrated-solution claim

Citry should say "integrated UI system", not "complete application stack".
Citry integrates:

- templates and components;
- inputs, slots, and subtree data;
- HTML, CSS, JavaScript, and dependency delivery;
- local Alpine behavior;
- server Events, forms, State, and DOM updates;
- fragments, caching, extensions, and component introspection.

The application still chooses a web host, routing, persistence, authentication,
authorization policy, deployment, and often a design system. FastAPI plus
SQLAlchemy is one appealing stack, not Citry's only or complete required stack.
Django, Flask, ASGI, and WSGI are also supported host directions.

## Research 1: expert message audit

**Status (2026-07-28): complete for iteration one.** The project needs a clear
first build, not a pre-launch preference study. This audit combines Citry's
verified product facts with the current landing patterns used by developer
frameworks such as FastAPI, Astro, Vue, Svelte, htmx, and Reflex.

### Decision: lead with the job and language

Use this first viewport:

Eyebrow:

> FREE AND OPEN SOURCE · MIT LICENSE · PYTHON

Headline:

> Build the frontend in Python.

Supporting copy:

> Citry is an HTML-first frontend framework for Python web apps, built around
> reusable components. Write familiar HTML components with checked inputs,
> isolated data, scoped browser behavior, and Python event handlers, without
> maintaining a separate frontend application.

Primary CTA: **Build your first component**

Secondary CTA: **Explore examples**

Install control: `pip install citry`

Scope line: **Server-rendered HTML · Django, FastAPI, and Flask · No separate
frontend build**

Visual proof line, only after generation and measurement: **This field contains
1,024 Citry components.**

"Build the frontend in Python" names the task and language in six words. The
supporting sentence resolves the likely ambiguity: authors write HTML rather
than a Python representation of the DOM, the server renders useful output, and
browser behavior remains available. "Checked inputs" is more accurate for the
current product than an unqualified "typed frontend", which can imply complete
static checking across templates before the proposed linter exists.

The artwork reserves a quiet, high-contrast region for the complete copy block.
The headline and CTA appear immediately; motion never reveals or delays them.
Any Python version label is generated from the released support matrix and names
an exact range rather than using an open-ended plus sign. If a promoted example
requires a separate frontend build, the scope line is narrowed before
publication rather than preserving an absolute claim.

### Use the other directions lower on the page

Use this as the reliability-section heading:

> Catch mistakes early.

The earlier "Python frontend that catches mistakes early" was distinctive but
could classify Citry as a linter or testing tool. The reliability section has
enough context to make the same benefit precise.

Use this over the component field or capability section:

> The web is your component tree.

It carries the desired personality and scale, but "component tree" is insider
language and the phrase does not identify Python or a framework. It should not
carry the hero's explanatory burden.

Use this expressive refrain:

> One component. A thousand components. An entire interface.

"Interface" keeps the promise inside Citry's UI responsibility. "Application"
would imply that Citry supplies persistence, authentication, routing policy,
hosting, and deployment.

### Why this is the first-iteration recommendation

Current framework pages that communicate well establish a recognizable
category early, then make it tangible with code or an interactive result.
Citry should follow that information order without borrowing their visual
identity. Reflex already occupies a broad Python full-stack, AI-builder, and
deployment position. Citry is more distinct when it owns HTML-first components
inside an existing Python web application.

This is an expert recommendation, not a measured preference claim. Later, once
the page has real traffic and Citry has stable external users, a short
comprehension study can test whether visitors misclassify the product or miss
its Python, frontend, and open-source identity. That study may revise the copy;
it does not block the first skeleton.

## Decision: the page ships without the component field (2026-07-29)

The hero background is plain. The sections below it carry the demonstration
instead: an annotated walkthrough of one complete component, seven errors
captured from real renders, five host integrations, and five capabilities a
growing product runs into.

The field was designed when the page had nothing else to prove scale with, and
it was measured carefully before being built. What the finished page showed is
that it had stopped earning its place:

- its 1,024 descriptors were 27% of the page's HTML, for decoration;
- the sections above prove capability directly, and a reader trusts a real
  traceback more than an abstract grid;
- the effect read as a plain CSS pattern, which argues against the claim it
  existed to make;
- it obliged the page to carry pause, replay, and inspector controls that were
  hard to find and explained nothing once found.

The research below is kept as the record of how the decision was measured, and
the delivered-count and architecture findings still stand for anything that
revisits the idea. The strongest surviving version is the unbuilt one: cells
that respond to the hero's code panel, so the artwork is the output of the code
beside it rather than a backdrop.

Two defects found while removing it are worth carrying forward. The build's HTML
minifier dropped the space after a custom property, turning `var(--bg) 0%` into
`var(--bg)0%`, which is invalid and silently voided whole declarations including
the field's own contrast mask. Inline CSS minification is now off and a
`rendered_css` guard fails any build containing the pattern.

## Creative concept: the component field

### Core visual

A field of cells fills the page. A radial wave begins at the top-left and moves
toward the bottom-right, with a broad curved front rather than a mechanical
diagonal wipe. Each cell responds through opacity, scale, color, and depth.
The aggregate should feel like a horizon opening, not a loading skeleton.

The motion has three levels:

1. **Arrival.** One wave crosses the hero once, revealing depth and the headline
   without delaying either.
2. **Ambient state.** The field becomes mostly still. A very slow, low-contrast
   breathing pattern may remain only if the page offers a pause control and the
   effect survives accessibility testing.
3. **Intentional interaction.** Pointer, touch, or keyboard activation of a
   visible "send a wave" control creates a local ripple. The control makes the
   motion expected and repeatable.

The wave origin encodes composition: a single cell activates its neighbors,
which activate a larger field. The animation is therefore a picture of the
component tree, not an unrelated particle effect.

### Visual progression down the page

The same field can change meaning by section:

- in the hero, cells are abstract potential;
- around the first code example, a small cluster locks into the shape of a
  rendered card;
- in the error-proof section, one incorrect cell turns warm and the surrounding
  cells hold position while a precise diagnostic appears;
- in the integrated UI section, four color families represent markup, Python,
  browser behavior, and style, then converge into one component;
- near the final CTA, the field opens into a bright horizon with ample still
  space around the text.

Do not animate every scroll position continuously. Section transitions should
be short, bounded, and triggered when a section becomes meaningfully visible.

### Delight moments

1. **Component inspector.** A quiet "How is this made?" control reveals the
   actual component count, projection strategy, HTML transfer size, and a
   compact source excerpt. Add server render time only from the clean
   complete-page publication artifact, with its environment. No fabricated live
   metric.
2. **Error lens.** The reader can toggle `label` to `lable` in a tiny example.
   The visual component goes dark and a real Citry diagnostic appears at the
   authored line. Restore it and the cell rejoins the field.
3. **Wave from code.** Hovering or focusing `<c-Cell />` in the code sample
   highlights the corresponding cluster. Keyboard users get the same state on
   focus.
4. **Theme as data.** Changing one Python value shifts the whole field's accent
   through component CSS data, demonstrating data flow without a paragraph.
5. **Source honesty.** A link opens the exact landing components in the public
   repository. Dogfooding is interesting here because it proves the page, not
   because the docs happen to use Citry.
6. **Motion memory.** If a visitor pauses motion, navigation within the site
   remembers that preference locally. It is never tied to analytics or an
   account.

### Ideas to avoid

- a vague space, nebula, or AI gradient with no relationship to components;
- a long cinematic intro before product copy appears;
- a terminal typing animation that repeatedly erases readable text;
- fake counters, fake build output, or metrics sampled on the visitor's device
  and presented as general performance facts;
- requiring pointer movement to reveal basic information;
- an endless animation behind paragraphs without a pause mechanism;
- turning every decorative cell into a focus target.

## How to render hundreds or thousands of cells

The visual goal creates a deliberate technical conflict. Chrome's
[large-DOM guidance](https://developer.chrome.com/docs/lighthouse/performance/dom-size)
warns around 800 nodes and reports an excessive DOM around 1,400. Large DOMs
increase network, style, layout, interaction, and memory work. A page with
1,024 literal cells plus normal content will cross that diagnostic range.

This means the page cannot select an architecture from aesthetics alone.

### Prototype A: literal DOM components

Each `LandingCell` renders one lightweight element:

```html
<i
  class="landing-cell"
  style="--x: 12; --y: 7; --phase: 13.89"
></i>
```

One `LandingField` owns the grid and interaction. Individual cells have no
JavaScript callback, no event listener, no component runtime state, and no
accessible meaning. CSS uses custom properties computed in Python and animates
only `transform` and `opacity`, the properties recommended by
[web.dev's animation guidance](https://web.dev/articles/animations-guide).

Benefits:

- the browser DOM visibly proves that every square came from a component;
- implementation is simple and inspectable;
- the server-render performance claim is direct.

Risks:

- DOM size may damage initial rendering and interaction;
- one broad style change can recalculate every cell;
- 1,000 composited layers would be worse, so `will-change` cannot be applied to
  every cell casually;
- a full-page field may require more cells than a hero-only field.

### Prototype B: component-generated canvas projection

Python creates and renders one `LandingCell` component per logical cell. Each
cell contributes a compact descriptor to one inert data block. A single
`LandingField` client controller draws those descriptors to an
`aria-hidden="true"` canvas.

Benefits:

- thousands of logical components do not become thousands of DOM elements;
- one canvas can cover a viewport or the whole visual layer;
- pointer ripples and section transitions can update one drawing surface;
- DOM performance remains representative of a good landing page.

Risks:

- "each visible cell is a component" becomes an architectural statement, not a
  one-node-per-cell DOM fact;
- the descriptor path must genuinely render through Citry components or the
  proof is misleading;
- canvas needs a static no-script fallback and careful high-DPI sizing;
- one controller is a custom renderer, which demonstrates less of Citry's DOM
  behavior than prototype A.

### Prototype C: CSS-only field

A repeating CSS gradient can draw thousands of apparent cells with almost no
DOM. This is an excellent fallback but does not satisfy the core proof. Keep it
only as the reduced-motion or no-script background if it matches the final art
direction.

### Prototype decision and evidence

**Decision (2026-07-28): use Prototype B with exactly 1,024 logical cells.**
Python renders one transparent `LandingCell` per descriptor into one inert JSON
block. One `LandingField` controller validates the ordered block and projects it
onto an `aria-hidden` canvas. The descriptor grid has 41 columns and 25 rows.
Prototype A remains the small-count inspectable control; Prototype C is the
static fallback.

The isolated production-sized proof tested 256, 512, 1,024, 2,048, and 4,096
logical cells against the same complete hero and lower-page shell. It records
fresh and warm Citry rendering, raw and deterministic-gzip HTML, browser DOM and
listener counters, lab loading and interaction metrics, frame intervals, long
tasks, forced-GC retained state, exact descriptor hashes, and the accessibility
and fallback matrix. The complete contract, executable fixture, reviewed
artifacts, and limitations live in the
[component-field findings](docs_landing_page_research/component_field_proof/findings.md).

At the selected 1,024 count, the focused 12-round cohort found:

| Measure | Literal DOM | Canvas projection | Gate |
| --- | ---: | ---: | ---: |
| Added raw HTML | 903,634 B | 56,663 B | at most 307,200 B |
| Added deterministic-gzip HTML | 48,072 B | 11,775 B | at most 32,768 B |
| Browser elements | 1,066 | 44 | diagnostic |
| Mobile lab LCP p75 | 348 ms | 252 ms | at most 2,500 ms |
| Mobile interaction proxy p75 | 160 ms | 64 ms | at most 150 ms |
| Mobile longest task | 109 ms | 0 ms | below 100 ms |
| Mobile maximum frame gap | 116.7 ms | 50.1 ms | below 100 ms |
| CLS max | 0 | 0 | at most 0.01 |

Canvas passed every target-count gate on desktop and throttled mobile. Literal
DOM failed both payload gates and the mobile interaction, longest-task, and
frame-gap gates. The five-round scale sweep placed the cross-profile passing
frontier at 256 for literal DOM and 2,048 for canvas. Canvas at 4,096 failed its
gzip, mobile blocking, and mobile frame-gap gates. This gives 1,024 meaningful
headroom without making the selected public count depend on the edge of the
measured range.

The lab interaction measurement is a synthetic click proxy, not field INP, and
the lab loading result is not field LCP. Both reviewed artifacts record the
machine, browser, release-build attestation, seeds, fixture hash, invalid
samples, and baseline-relative values. Field Core Web Vitals must challenge the
lab result after launch. A clean complete-page target run remains a publication
gate.

### Accepted field runtime contract

- Deliver 1,024 descriptors on desktop and mobile first navigation. A static
  page cannot inspect the first viewport before delivery; responsive CSS may
  crop or soften visual detail but must not claim a smaller payload.
- Use a broad top-left radial arrival with a 1,600 ms front and 350 ms settle.
  Intentional ripples use a 550 ms front and 350 ms settle at the fixed tested
  origins.
- Ship no ambient breathing animation in iteration one. Research 3 may propose
  it only with the existing pause behavior and fresh measurement.
- Cap effective canvas DPR at two and its backing allocation at eight million
  pixels.
- Keep the CSS fallback visible until descriptor validation, canvas allocation,
  and the first static draw all succeed. Leave it visible when descriptors are
  corrupt or the 2D context is unavailable.
- Stop scheduled work while paused, hidden, offscreen, under reduced motion, or
  after controller cleanup. Remember an explicit pause for the site session.
- Expose the logical count, descriptor hash, projection strategy, and source
  proof through the proposed inspector. Copy may say "This field contains 1,024
  Citry components," but must not imply that it contains 1,024 DOM nodes.
- Reopen the architecture decision if production changes the descriptor schema,
  runtime initialization, controller, field CSS, page shell, count, timing, or
  budgets materially.

## Accessibility and motion contract

The component field is decorative. It is `aria-hidden`, cannot receive focus,
does not convey the only copy of any information, and remains behind sufficient
contrast protection for foreground content.

Required behavior:

- [`prefers-reduced-motion`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40media/prefers-reduced-motion)
  produces a stable field with no traveling wave or scroll-linked movement;
- automatic motion either stops within five seconds or has a clear pause/play
  control, following [WCAG 2.2.2](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html);
- no flash pattern approaches three flashes per second;
- pause state applies to all field effects and persists for the site session;
- the page remains understandable with the field entirely absent;
- the code demo and error lens work by keyboard and expose their state in text;
- focus, text selection, links, and scrolling never compete with the field;
- narrow screens use fewer visual details and preserve headline/CTA priority;
- forced-colors and high-contrast modes receive a plain, readable background.

If motion initialization fails, the controller leaves the server-rendered
static state in place. If canvas is unavailable, the CSS fallback remains. An
invalid persisted motion preference is ignored and the operating-system
preference wins.

## Make the project visibly human

In an AI-saturated software landscape, human trust is a product advantage.
Citry should make authorship, care, judgment, and participation visible. That
does not mean decorating the landing page with anonymous avatars or calling a
small project a movement. The honest first story is that named people are
building a promising framework in public and inviting others into specific,
useful work.

### Current foundation and launch gaps

The existing [People page](../../docs_site/content/community/people.md) is the
right foundation. It names the maintainer, special thanks, and contributors.
Its automated counts currently represent merged pull requests across Citry and
its django-components lineage, so any landing excerpt must label that history
instead of implying that every person shown is already an active Citry user.
Recognition should grow beyond code to documentation, bug reports, review,
support, design, teaching, speaking, event help, and community care.

Before the landing page invites broad participation:

- run one community-route audit across
  [Contributing](../../docs_site/content/community/contributing.md),
  [Getting help](../../docs_site/content/community/help.md),
  [AI bot policy](../../docs_site/content/community/ai-bot-policy.md), and the
  [beta charter](v1_beta_research/product_beta_charter.md). Reconcile their
  Issues, Discussions, and shared Discord promises with reality, remove the
  premature "community-maintained" description, and choose staffed destinations
  after testing them with an ordinary signed-out or non-maintainer account;
- enable a working public contribution route or describe the actual policy.
  [GitHub currently says issue creation is restricted](https://github.com/citry-dev/citry/issues);
- make the stable Getting help and Contributing pages own the canonical routes,
  then point landing CTAs through those pages instead of duplicating external
  destinations;
- replace the localhost documentation link in
  [the contributing page](../../docs_site/content/community/contributing.md);
- give conduct reports a project address, an independent conflict route, a
  response expectation, and a short enforcement process. The
  [Contributor Covenant](https://www.contributor-covenant.org/resources/)
  explicitly warns that publishing a code without the means to enforce it can
  create false confidence; and
- record minimal governance: the current lead and tie-breaker, how material
  decisions are made in public, conflicts of interest, and the responsibilities
  a future maintainer would accept.

These are trust infrastructure, not administrative polish.

### First-iteration landing section

Place a compact human section after product fit and before release/trust facts.
Its heading is:

> Built in public by people who care about Python and the web.

It contains:

- a named maintainer card with a short first-person reason for building Citry;
- one signed "Why Citry exists" note or recent blog entry;
- the accurate lineage statement, "Citry grows from django-components and the
  work of its contributors";
- a small, consented acknowledgment of real contributors without a vanity
  count;
- a primary link, **Meet the people building Citry**;
- concrete participation paths such as **Ask a question**, **Share what you
  built**, and **Help improve Citry**, but only when each destination works; and
- **Invite a Citry talk or workshop**, linking to a page with formats, audience,
  travel region, remote availability, costs, equipment, accessibility needs,
  and contact details.

The component field can support the idea without equating cells with people.
On intentional interaction, a few cells may turn into consented records such as
"documented Events", "reported an accessibility bug", or "taught a workshop".
The accompanying line can say:

> Every cell is a component. Every improvement starts with a person.

Do not ship fabricated testimonials, company logos, usage counters, a world map
of implied users, stock community photography, live avatar feeds, or empty
ambassador titles. A signed postcard-sized note from the maintainer is more
credible than simulated scale. Photographs and quotations are opt-in, retain
their context, have withdrawal paths, and are never a condition of recognition.

### Community sequence

For the first three months after the participation routes are ready:

1. Publish five to ten genuinely useful starter issues. Each names the outcome,
   relevant files, verification steps, expected skills, and a human willing to
   help.
2. Run a monthly 45-minute online **Citry open studio**: ten minutes of project
   changes, twenty minutes building or debugging one component in public, and
   fifteen minutes of questions. Publish the agenda and notes; record only with
   explicit consent.
3. Add non-code recognition to People and publish occasional human stories in
   the blog: what someone tried, what failed, what changed, and who helped.
4. Visit existing Python, Django, FastAPI, htmx, and Alpine communities before
   trying to create a Citry-only audience.
5. Recruit a second conduct responder or moderator before increasing event
   scale.

The first travel recommendation is a 10 to 20 minute talk at an existing
[Pyvo Czech Python meetup](https://pyvo.cz/en/), starting with Prague or Brno.
Pyvo already welcomes short talks and English-language participation, which
makes it a better first venue than launching a new meetup. The strongest talk
topics are:

- "Build server-rendered components in Python without a frontend build";
- "Why missing template data should fail loudly";
- "One component from Python input to browser interaction"; and
- "What Python UI frameworks can learn from React, Vue, and Livewire".

After the tutorial and example project are stable, follow with a two to three
hour hands-on lab hosted alongside an existing community. A lab needs a tested
setup path, one coach for roughly every three to five beginners, a code of
conduct, an accessible venue, and a complete take-home example. A conference
sprint becomes sensible after the talk and lab have repeat participants.

During months three to twelve, aim for one small quarterly lab or sprint,
publish participant-approved project stories, create "Built with Citry" only
when real applications exist, and recruit a second maintainer or release
helper. Track whether newcomers receive answers, make a first contribution,
return, or take responsibility. Do not optimize for chat members, stars, or
attendance alone.

Only after repeat users, repeat instructors, tested curriculum, safety capacity,
and follow-up support exist should Citry consider its own meetup series or
multi-day bootcamp. At that point the [Python Software Foundation grants
program](https://www.python.org/psf/grants/) may help fund an eligible workshop;
grant timing must follow the current published round rather than driving a
premature event. Local groups require at least two organizers so one person's
absence does not end the community.

Community copy about AI belongs in a contribution or governance policy, not the
hero. The useful principle is that AI may assist work, while a named person
remains responsible for accuracy, provenance, review, and its effect on other
people. Recognition follows human judgment and care, not generated volume.

## Proposed page structure

The page should be much shorter than the current feature inventory. Each
section earns its place by answering an evaluation question or proving a claim.

### 1. Hero: identify and invite

- open-source/Python badge;
- clear headline and category sentence;
- primary learning CTA, secondary live-proof CTA, and copyable install command;
- host compatibility line;
- component field with a bounded arrival wave;
- no rotating words or delayed headline reveal.

Reader outcome: "This is a Python frontend framework built from components, I
understand its server-centered shape, and I know where to start."

### 2. Sixty-second proof: one component, full path

Show one compact, realistic component with:

- `Kwargs` input declaration;
- a short HTML template;
- one scoped style;
- one optional local behavior or Python Event;
- rendered output beside it.

The sample must run in repository checks. Tabs can reduce visual width, but the
default state must show enough code without interaction. Avoid a 50-line class
that makes "simple" unbelievable.

**As built (2026-07-29).** The sample is a real component file under
`docs_site/snippets/landing/`. The page shows that file through
`<c-include-file />` and renders the same class for the card beside it, so the
code and the output are one source rather than two copies kept in step. The
arguments appear above the card, written from the same values the render used.
A caption states that the card was produced while the page was built, which is
only worth saying because it is true.

Reader outcome: "I can map this to Python and HTML I already know."

### 3. Reliability proof: catch UI mistakes early

Use the error lens to show three exact failures:

1. misspelled or missing component input;
2. missing template variable;
3. invalid event handler, State field, or modifier.

Say when each fails. Do not call render-time validation compile-time. Link to
typing, troubleshooting, security, and future IDE tooling only according to
current status.

**As built (2026-07-29).** The page shows six cases, chosen to cover the
different moments Citry rejects work and to lead with what other Python template
layers do not do at all:

| Case | Raised | Why it earns a place |
| --- | --- | --- |
| Missing input | `TypeError` | The contract is checked as the component renders |
| Misspelled input | `TypeError` | Offers the name you meant |
| Unknown template value | `KeyError` | Points a caret at the line that asked |
| Data stays in its component | `KeyError` | A child never inherits a parent's variables |
| Unknown component | `NotRegistered` | Names the tag that asked for it |
| Unsafe expression | `SecurityError` | Template expressions cannot reach the interpreter |

The isolation case is the strongest of these, because it is the one a Django or
Jinja author expects to succeed: the same template silently prints nothing
there, while Citry names the component path (`Parent > Child`) and the missing
variable.

The invalid-event case is deferred. An invalid binding only fails once a handler
answers a call, and this page is a static build with no server to call, so
showing one would mean staging an error rather than catching one.

Kwarg *types* are deliberately absent from this section. A declared `int` that
receives a string renders without complaint today, so the page would be
promising a check that does not exist.

Nothing here is written by hand. Each case owns the smallest snippet that causes
it, the build executes that exact source, and the page prints the snippet beside
the text Citry raised. The build fails when a mistake stops raising, and also
when the expected error arrives without the words the page promises, so a label
can never outlive the message it describes.

Reader outcome: "Citry gives both humans and coding agents a short correction
loop."

### 4. Optional example highlights

Show at most three complete outcomes that do not look like variations of the
same component demo. A game, a data-rich public-interest dashboard, and a
spreadsheet or creative tool would establish breadth quickly. Each highlight
links to its canonical page under Examples, where readers can use the live
demo, inspect the source, read the constraints, and run the example.

This section is optional because it must earn its page weight. Do not add empty
cards for concepts that have not been built, measured, and tested. The detailed
candidate backlog and selection contract are defined in [Example showcase
backlog](#example-showcase-backlog).

Reader outcome: "This component model can produce serious tools and playful
experiences, not only documentation widgets."

### 5. Integrated UI: one component owns the path

Use a small flow, not a grid of generic benefits:

```text
Python inputs -> HTML component -> scoped browser behavior
              -> CSS and assets -> Python event -> DOM update
```

Explain that Citry manages the UI path while the application keeps its chosen
host, data layer, and authentication. Link to FastAPI, Django, Flask, Events,
and the security boundary.

Reader outcome: "I can build interaction without splitting one feature across
two applications."

### 6. Capability horizon: grow without switching models

Use the visual field to group capabilities by reader value:

- composition: props, slots, provide/inject, fragments;
- interaction: Alpine, State, Events, forms, loading/error states, morphing;
- operation: assets, caching, extensions, testing, host adapters;
- performance: Rust parser and named reproducible benchmark.

Each group links to one focused journey. Avoid one card per feature.

Reader outcome: "The simple first example is not the limit of the framework."

### 7. Fit: choose Citry when

Use direct statements:

Choose Citry when:

- your product and team are centered on Python and server-rendered HTML;
- you want a component model stronger than template includes;
- you want rich interaction without a separate client application;
- explicit inputs and loud failures matter;
- you want to keep FastAPI, Django, Flask, ASGI, or WSGI.

Consider React or Vue when a client-only/offline application, native target,
large frontend hiring pool, or deep browser package ecosystem dominates.
Consider Livewire when the application is Laravel/PHP. Consider Reflex,
NiceGUI, or Flet when their generated or cross-platform UI model is the desired
product boundary.

Reader outcome: "The project respects my constraints and is not pretending to
fit every job."

### 8. People: built in public

Show the named maintainer, one signed reason for building Citry, accurate
django-components lineage, a small contributor acknowledgment, and verified
ways to participate. Link to People and invite a talk or workshop. Add an event
only when it has a real date, timezone, agenda, conduct policy, registration
path, and host.

Reader outcome: "I know who is responsible, why they care, and how I can reach
or help the project."

### 9. Trust and open source

Show only verified facts:

- MIT license and GitHub source;
- exact current release status;
- supported Python/host/browser matrix;
- test and benchmark links;
- security reporting and limitations;
- support, governance, and security paths.

Logos and testimonials wait for permission and real adoption evidence.
Download counts, company use, and performance figures need a visible source and
measurement date.

### 10. Final CTA

Repeat one action, not a new sales pitch:

> Build your first component.

Include the install command and a secondary link to a complete example. Let the
field open and become still around the CTA.

## Open landing-page work (2026-07-29)

These are decided in direction but blocked on things that do not exist yet.
Nothing here should ship as a mock-up of a capability Citry does not have; the
page's whole argument is that what it shows is real.

### The UI library section needs a UI library

The intended section replaces the old capability list: a browser mock-up whose
left panel scrolls through available components, where a reader drags one onto
the page area and sees it land. It is a strong idea because it demonstrates
composition by doing it rather than listing primitives.

To build it honestly, the following must exist first:

1. A real component library package with a stable import path, so the panel
   lists components that a reader can actually install and use. Roughly 12 to 20
   components is the minimum for the panel to look like a library rather than a
   sample: layout (stack, grid, card), form controls (input, select, checkbox,
   button), feedback (alert, badge, spinner, toast), navigation (tabs, menu,
   breadcrumb), and data display (table, list, avatar).
2. A per-component preview that renders standalone at a small size, plus the
   snippet that produces it, so the drop area can show both the result and the
   code that made it.
3. A machine-readable index of the library (name, category, preview, snippet)
   that the landing build reads. Without it the section becomes a hand-kept
   list that goes stale, which is the failure this page keeps designing out.
4. A decision on what the drop actually produces: the accumulated snippet is the
   valuable output, because it turns a toy into something a reader can paste.

Until those exist the section stays out. A drag-and-drop demo of components
nobody can install would be the most damaging thing the page could contain.

Sharing is a one-line claim, not a section: anyone can publish a component
package others install. It needs a real published example before it earns space.

### The example gallery needs examples

The intended replacement for the fit section is a carousel of real screenshots
that links into Examples, with each image opening its own example. The framing
is "see for yourself" rather than a list of adjectives, and the existing title
can stay.

This is blocked on the [example showcase backlog](#example-showcase-backlog)
below. To fill a carousel without padding, three to five built examples are
needed, and they should not look like variations of one another. The strongest
first set from that backlog:

1. a game (pixel garden or an original word grid) for immediate, memorable play;
2. a data workbench (shelter outcomes or earthquake atlas) for dense
   composition and honest real-data handling;
3. a spreadsheet or component observatory for direct manipulation and depth.

Each needs the showcase manifest, generated still preview, and revision
checksum the selection contract already specifies. The build must fail on a
stale or missing preview rather than shipping a screenshot that no longer
matches the example.

### Hero and identity work still open

- **The headline is not yet the product's claim.** "Build the frontend in
  Python" describes what Django and Jinja have done for twenty years, so it
  cannot be the thing that makes a reader stop. The distinctive claim is the
  combination the walkthrough already proves: one file holds inputs, server
  state, Python handlers, markup, browser behavior, and styles, and mistakes in
  any of them are reported rather than rendered blank. A replacement headline
  should come from that, and the supporting sentence ("Citry is an HTML-first
  component framework for Python web applications") is already right and stays.
- **Hero copy contrast.** The headline, supporting text, actions, and install
  command currently sit over the field with too little separation to read
  comfortably. The field is decorative and must yield: the copy needs a
  guaranteed contrast floor against every part of the artwork behind it.
- **The field does not read as components.** A uniform grid reads as one CSS
  background, which argues against the claim it exists to prove. It needs
  variation that suggests individually rendered cells: differing arrival, size,
  or grouping, and ideally a visible relationship between one cell and the
  cluster it activates.
- **The field controls are unusable.** Pause, replay, and the inspector are
  present for the motion contract but are effectively invisible and unexplained.
  Either they become a deliberate, findable control cluster, or the motion is
  reduced to the point where only the reduced-motion contract governs it.

### Sections to add above the walkthrough

- **A short recorded video**, placed before the walkthrough, so a reader who
  will not read code still sees the product work. Suggested beats, each shown
  rather than narrated: start from an empty file; write a component with one
  input and render it; misspell the input and show the error naming it; add a
  slot and fill it; add a Python handler and click it in the browser; add a
  scoped style; end on the finished interface. Two to three minutes, no
  interface tour, no roadmap, and the code must be readable at the recorded
  size.
- **A social-trust band** above the video. This one only becomes honest when
  there is something true to put in it. Until real adopters exist, the
  defensible version shows provenance rather than logos: the django-components
  lineage, the maintainer, and the public repository. Company logos, download
  counters, and testimonials wait for permission and evidence, per the trust
  rules above.

## Example showcase backlog

The landing page may curate examples, but Examples owns them. This follows the
existing information architecture in [`docs_site.md`](docs_site.md): Examples
is the permanent, code-first cookbook. Each accepted Example owns a showcase
manifest with its title, short value statement, capability label, canonical
route, data attribution, and generated preview. The landing configuration stores
only selected example IDs and order. An explicitly landing-owned crop may alter
framing but not the underlying preview or copy. The example page owns the
runnable source, live demo, prerequisites, explanation, failure behavior,
tests, and links to Docs and Reference.

The aim is not to assemble a gallery of familiar cards and counters. A small
portfolio should demonstrate that the same component model can support play,
dense information, direct manipulation, and unusual browser experiences.

### Candidate examples

| Concept | What the reader can do | What it proves | Data or asset direction | Main risk |
| --- | --- | --- | --- | --- |
| Daily word-grid game | Solve one deterministic five-letter puzzle, share a text result, and replay archived puzzles | Repeated components, keyboard input, State, transitions, persistence, accessibility, and deterministic tests | Use a reviewed, redistributable word list committed with its license and version | A direct Wordle clone feels derivative; the interaction and visual identity need a Citry-specific idea |
| Pixel garden or small tactics game | Move through a compact tile world, collect or grow objects, and complete a short objective | Hundreds of components, keyboard and touch controls, local browser behavior, server persistence, sprite assets, and stable keyed updates | Create original pixel art for Citry or use a verified CC0 asset pack with attribution | A component per pixel can create an irresponsible DOM; component-per-tile is only a candidate architecture until the example-specific performance gate passes |
| DOM sprite laboratory | Toggle between sprite-sheet, component-per-tile, and component-per-pixel renderings and inspect their measured cost | Citry rendering at unusual scale and an honest explanation of browser tradeoffs | Original tiny sprites and committed benchmark fixtures | This is an engineering experiment, not the recommended way to build a game; unsupported cell counts must be rejected or capped |
| Shelter outcomes workbench | Explore cat and dog outcomes by time, age, breed, and outcome; switch between dashboard, chart, heatmap, and table views | Dense composition, linked filters, charts, forms, table state, fragments, and accessible summaries | The City of Austin publishes a historical [Animal Center Outcomes dataset](https://data.austintexas.gov/Health-and-Community-Services/Austin-Animal-Center-Outcomes-10-01-2013-to-05-05-/9t4d-g238) with animal type, age, breed, color, date, and outcome | Categories and recording practices can change; never imply causal welfare conclusions from descriptive records |
| Earthquake atlas | Explore recent earthquakes by location, magnitude, depth, and time across a map, histogram, scatter plot, and heatmap | Real-time server fetch, caching, linked visualizations, resilient stale data, and geographic interaction | Use the official [USGS real-time GeoJSON feeds](https://earthquake.usgs.gov/earthquakes/feed/); USGS explains its [data licensing](https://www.usgs.gov/data-management/data-licensing) | A live upstream outage cannot break the example; map tiles add a second license and dependency; the page must say it is educational, not an emergency source, and link to USGS |
| Air-quality neighborhood lens | Compare particulate measurements over time and explain missing coverage instead of hiding it | Public-interest data, uncertainty states, time-series charts, filters, and careful attribution | [OpenAQ API v3](https://docs.openaq.org/about/about) requires a secret [API key](https://docs.openaq.org/using-the-api/api-key); use a controlled server refresh for one identified provider and preserve both provider and OpenAQ attribution | Coverage is incomplete and source licenses vary; the example is educational, not health advice, and must comply with the provider and [OpenAQ terms](https://docs.openaq.org/about/terms) |
| Weather mosaic | Compare forecast or historical weather for selected places as small multiples and a calendar heatmap | Server data loading, responsive charts, color scales, caching, and URL-addressable state | Open-Meteo offers JSON weather APIs, but its [terms](https://open-meteo.com/en/terms) limit the free API to non-commercial use and classify promotional activity as commercial; use a compatible paid plan, self-hosted source with verified upstream rights, or another source | Weather is not climate; service-access terms and output-data licenses need separate review, and the copy must not infer long-term conclusions from a short interval |
| Development indicators explorer | Compare one carefully chosen social indicator across countries and decades with chart, map, table, and methodology notes | Large datasets, query controls, missing values, provenance, and accessible non-visual equivalents | The [World Bank Indicators API](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392) exposes thousands of time series without an API key; verify the selected series' provider and terms | Country comparisons can mislead when definitions, coverage, or periods differ; metadata must remain beside the result |
| Exoplanet constellation | Filter confirmed planets by discovery method, size, period, and distance, then arrange them as an explorable sky of components | Unconventional data art, dense filters, details on demand, and coordinated chart views | The [NASA Exoplanet Archive TAP service](https://exoplanetarchive.ipac.caltech.edu/docs/API_resources.html) provides programmatic table access and citation guidance | A spatial-looking composition must not pretend to show literal sky position when the selected fields do not support it |
| Wild-cat biodiversity atlas | Explore public occurrence records for the cat family across regions and time, then compare recorded diversity and observation gaps | Geographic components, filters, image/details on demand, provenance, and honest missing-data states | [GBIF](https://techdocs.gbif.org/en/openapi/) provides biodiversity APIs; its [terms](https://www.gbif.org/terms) require consumers to honor each dataset's Creative Commons license | Occurrence records reflect observation effort, not population size; sensitive coordinates, media rights, duplicates, and per-record licenses need explicit handling |
| Browser spreadsheet | Edit a local table, fill cells, paste ranges, sort and filter, add formula columns, undo changes, and export CSV | Keyboard-heavy direct manipulation, focus management, selection State, validation, virtualization, events, and testing | Start with a small synthetic budget, then offer a licensed public-data snapshot such as shelter outcomes | Cap rows, ranges, paste size, and calculation work; parse a small formula language without code execution; handle CSV formula injection; state accessibility and clipboard limits |
| Component observatory | Edit a small Citry component and inspect its component tree, props, slots, assets, rendered HTML, and real diagnostic output | Citry explaining itself, error feedback, parser output, source mapping, testing, and the future linter direction | Prefer repository-owned fixtures and safe declarative edits that invoke actual Citry diagnostics | Never execute anonymous Python in the docs process; any future user-code runner needs isolated compute with no project credentials, network, or repository writes and strict resource limits |
| Cellular ecosystem | Change a few rules, release agents into a grid, and watch an ecosystem or cellular automaton evolve | Thousands of repeated cells, deterministic simulation, controls, pause/resume, and server snapshots | Original rules and visual assets; optionally encode a real dataset only when the mapping is meaningful | Continuous motion and color can become inaccessible or expensive; reduced motion needs step controls and a static summary |
| Step sequencer | Toggle a grid of notes, change tempo and instruments, and export a compact pattern | Grid composition, local reactivity, Web Audio ownership, keyboard interaction, and serialization to Python | Original short synthesized sounds or verified redistributable samples | Audio must start only after user action, expose a master stop, and provide visible state for every audible event |
| Repository time machine | Scrub through Citry's own history and watch packages, components, tests, and contributors appear as a living graph | Recursive components, graph layout, time State, large data, and transparent project history | Build a privacy-reviewed snapshot from Citry's public Git history | Commit metadata can contain personal information and bot noise; define the fields retained before publishing |

The shelter workbench can satisfy several suggestions without becoming several
nearly identical demos: its dashboard, charts, heatmaps, and spreadsheet view
share one sourced dataset and linked selection state. The earthquake atlas and
exoplanet constellation are stronger alternatives when geographic or
scientific wonder fits the visual direction better.

The game examples need an original mechanic or presentation. A word-grid game
is useful because its rules are understood quickly, but the Citry example
should add a component-oriented twist, such as clues assembled from independent
cells or a cooperative server-generated daily board. A pixel game should use
ordinary web elements deliberately. Each tile, actor, pickup, effect, and HUD
unit can be its own element and Citry component. Making every sprite pixel a
DOM element belongs only in the measured DOM sprite laboratory.

Before component-per-tile becomes the ordinary game architecture, test its
complete viewport at target counts on a low-end supported device. Apply the
landing field's DOM, transfer, memory, long-task, interaction, and reduced-
motion budgets. If it fails, keep actors and interactive objects as components
while projecting inert terrain through canvas or CSS. Unsupported map sizes
must fail configuration or clamp with a visible authoring error, not quietly
freeze the browser.

The spreadsheet accepts only a documented formula grammar and evaluates it as
data, never as Python or JavaScript. It caps rows, cells, pasted ranges,
dependency depth, recalculation work, and export size. CSV export warns or
escapes cell values beginning with formula-trigger characters. Invalid formulas
remain visible as cell errors. An oversized paste or dependency cycle is
rejected without losing the previous sheet state.

The first component observatory should offer repository-owned examples and safe
declarative edits, not arbitrary Python. If a later research project accepts
user code, it runs outside the docs process and repository with no network,
credentials, or writable project mount, plus strict CPU, memory, output, time,
and rate limits. Initialization failure, limit exhaustion, or an unavailable
runner fails closed and leaves the static example readable.

Health and hazard examples display the source update time, whether data is
preliminary or revised when the provider exposes that status, a link to the
authoritative service, and a visible statement that the page is an educational
framework demo rather than an emergency or health-decision source. Stale data
must never look live.

### Additional crossover directions

- **Visual state-machine editor:** connect states and transitions, simulate an
  event, and export the resulting Python declaration.
- **Logic-circuit playground:** compose gates from components, propagate a
  signal through the graph, and expose invalid loops or disconnected inputs.
- **Interactive fiction engine:** combine a narrative scene, inventory,
  branching State, and server-saved progress without imitating a dashboard.
- **Generative data quilt:** turn a real, licensed time series into a textile-
  inspired grid whose cells retain tooltips and a table equivalent.
- **Accessible diagram builder:** draw a flow with keyboard and pointer input,
  then inspect the semantic outline and exported SVG.
- **Data-story scrollytelling:** let a real dataset change as the reader moves
  through a short argument, with explicit controls and a complete static
  version for reduced motion.
- **Mini notebook:** compose executable-looking Markdown, chart, table, and UI
  cells from safe predefined operations, then save the document as JSON.
- **Component orchestra:** map a component tree to an opt-in audiovisual
  performance where parent and child activation can also be followed in text.

These are not commitments. The Examples backlog should eventually score them
against shipped Citry capabilities, novelty, learning value, maintenance cost,
performance, accessibility, and whether the result tells the truth about a
recommended production architecture.

### Landing-page selection contract

Feature two or three examples only after they exist. Prefer one from each row:

| Role | Preferred direction | Why it belongs |
| --- | --- | --- |
| Play | Pixel garden, original word grid, or step sequencer | Creates an immediate, memorable interaction |
| Understand | Shelter workbench, earthquake atlas, air-quality lens, or exoplanet constellation | Shows serious composition and honest real-data handling |
| Build | Spreadsheet, component observatory, state-machine editor, or diagram builder | Demonstrates direct manipulation and developer depth |

Each landing highlight contains:

- a still preview that remains meaningful without JavaScript;
- a concrete title and one sentence describing what the visitor can do;
- one outcome-specific action such as **Play**, **Explore the data**, or
  **Open the workbench**;
- a short capability label, not a dense technology inventory;
- the data date and attribution when the preview uses public data; and
- a canonical Examples URL in the current documentation version.

These fields resolve from the Example's showcase manifest. The site builder
projects its logical canonical route into the current version and generates the
still preview from the verified demo. The preview records the example revision
and data-snapshot checksum. A selected ID that is unknown, a route that cannot
be projected, or media whose recorded revision is stale fails the build. A
landing-specific crop stores only crop coordinates against that generated
image; it cannot override the Example title, attribution, or result.

Do not use an autoplay carousel. A highlight that exceeds the landing-page
performance budget becomes a static preview linking to the isolated demo.
Missing preview media, canonical URL, source attribution, or current example
verification fails the site build. If only one accepted example exists, show
one strong feature rather than padding the section with planned work. If none
exist, omit the section without leaving an empty heading.

### Public-data and asset contract

Every example that uses outside data or media records:

- the authoritative source URL and API or dataset identifier;
- the service-access terms and exact output-data or asset license as separate
  records;
- required attribution and citation text;
- retrieval date, transformation script, schema version, and snapshot checksum;
- a saved copy or immutable reference for the terms and license in force at
  acquisition;
- which claims are direct observations and which are interpretations;
- refresh cadence and the maintainer responsible for reviewing schema changes;
- privacy, safety, and representativeness limits; and
- an offline fixture small enough for deterministic tests.

The build and test suite must not require a live third-party API. A refresh job
fetches into a temporary location, validates the expected fields, record limits,
license metadata, service terms, and attribution, then produces a reviewed
snapshot. Secrets such as an OpenAQ API key remain in the controlled refresh
environment and never enter browser code, generated pages, fixtures, logs, or
copyable examples.

A timeout, rate limit, malformed response, empty result, unexpected field type,
or changed terms stops the refresh. Preserve a rejected snapshot internally for
review, but do not publish it automatically. A previously accepted snapshot may
remain public only when its recorded license grants continuing redistribution
rights for that acquired data. An unclear, bespoke, expired, revoked, or
incorrectly classified right quarantines the affected public artifact and fails
the public build until a human records a decision. Automated checks detect that
terms changed; they do not decide what legal language means.

A live example may use a bounded cache and show its last-updated time. When the
upstream service fails, it either shows an accepted, still-authorized snapshot
with a stale-data notice or a clear unavailable state. It never silently renders
zeroes.

Do not use an aggregator's convenient download as proof that every underlying
series can be redistributed. For example, [Our World in Data's reuse
guidance](https://ourworldindata.org/faqs) says that third-party data retains
the provider's terms. Verify and attribute the selected upstream dataset.

## Page and navigation architecture

The project landing page is site-scoped at `/`. Documentation remains
versioned and starts at `/docs/`.

Desired navigation behavior:

- the Citry logo links to `/`;
- the Docs tab links to `/docs/` at the root and `/v/<version>/docs/` inside a
  snapshot;
- Blog remains the last, rightmost top-navigation item;
- a snapshot root `/v/<version>/` redirects to its first versioned Docs page,
  which the current builder already supports when `/` is site-scoped;
- landing-page links to Docs use the current root version, while historical
  snapshot links stay inside their snapshot.

The navigation schema now supports an explicit non-area home declaration, so
the project home does not become a visible Docs item:

```yaml
home:
  title: Citry
  path: /
  scope: site

areas:
  - label: Docs
    scope: versioned
    items:
      - { title: Overview, path: /docs/ }
```

The loader requires all three `home` fields, rejects a non-root path or a scope
other than `site`, and includes the declaration in scope and link projection
without adding it to primary navigation. Snapshot roots redirect to the first
built versioned page. A repository that omits `home` retains the prior
area-owned root behavior.

## Rendering architecture

An ordinary docs article layout cannot produce the intended page. The source
should remain reviewable and indexable Markdown while selecting a purpose-built
Citry layout:

```yaml
---
title: Citry
description: Build checked, isolated web components in Python.
layout: landing
---
```

Implemented file ownership:

```text
docs_site/content/index.md
docs_site/_internal/components/landing.py
docs_site/tests/test_landing_component.py
```

The component owns the distinctive field, page CSS, error lens, and small
interactions. Shared header, search, tokens, and layout primitives remain in the
site shell. The content source owns the meaningful copy and section order.

`layout: landing` must:

- render the ordinary site header and footer;
- omit docs sidebar, right-hand table of contents, breadcrumbs, and previous/
  next navigation;
- omit the version picker. A visitor arriving at the project home is choosing
  whether to use Citry at all, not which release to read, and the picker belongs
  with the documentation it switches. Every docs page at the root carries it, so
  the assembly step that points pickers at the version manifest simply finds
  nothing to rewrite on this page;
- preserve canonical, Open Graph, structured data, Pagefind, sitemap, Markdown
  companion, and LLM index behavior;
- keep all meaningful copy in server-rendered HTML;
- degrade to a readable static page without JavaScript;
- use the shared base-path and publication-scope projection rules.

An unknown `layout` value is a build error naming the source and accepted
values. Missing landing data uses documented defaults only for optional copy;
required CTA destinations or proof data fail the build. Generated metrics are
read from a committed benchmark artifact with provenance. They are never guessed
or silently set to zero.

## AI positioning and evidence plan

The strongest future positioning is not that AI writes more code. It is that
Citry makes generated UI easier to verify and correct.

### Current thesis

> Citry gives humans and coding agents a short, explicit feedback loop: declared
> component inputs, isolated data flow, loud template failures, typed event
> payloads, executable examples, and ordinary Python tests.

This is a plausible architectural claim today. It should be phrased as a design
benefit, not market leadership.

### What the future IDE tooling adds

The proposed `citry check` command and language server would move several
diagnostics from initialization or rendering into the editor and CI. Once
implemented, an agent could receive structured file/line diagnostics without
starting the browser. Until then, landing copy cannot say that Citry has an IDE
linter, completion, or live template diagnostics.

### Later comparative validation

A comparative agent benchmark is useful only after Citry has stable examples,
representative tasks, and the tooling being claimed. It is not first-iteration
landing-page research. When the project is ready to test "best Python frontend
framework for AI", compare equivalent component-contract, form, event,
security, refactoring, and testing tasks against fairly configured Django,
Jinja, django-components, Reflex, NiceGUI, and a Python host with htmx/Alpine.
Keep React/TypeScript, Vue/TypeScript, and Livewire in a clearly labeled
cross-language track.

Use the same model, permissions, prompt, budget, and fresh context; repeat runs;
measure successful behavior, escaped defects, correction cycles, diagnostic
quality, human review effort, accessibility, time, tokens, and tool calls. Give
competitors their recommended strict and type-checking tools. Publish prompts,
fixtures, raw runs, environment, scoring, and mixed results. Compare current
Citry separately from the future linter/LSP so proposed tooling never receives
credit before it ships.

### Claim ladder

1. **Now, after copy review:** "Built for fast feedback" or "Catch component
   mistakes early."
2. **After a public current-tooling benchmark:** "Designed for AI-assisted
   Python UI, with measured correction-loop results." State the actual result.
3. **After linter implementation and benchmark rerun:** "AI-ready from editor to
   browser" if the tasks support it.
4. **Only after broad, independently reproducible wins:** "The best Python
   frontend framework for AI." The claim must link directly to the benchmark,
   date, competitors, and limits.

If results are mixed, publish the mixed result and use the narrower winning
claim. A superlative is not a design requirement.

## Content and claim verification

Every material landing claim should have one owner and one machine-checkable or
reviewable source:

| Claim class | Required evidence |
| --- | --- |
| Install and support | Released artifact plus compatibility matrix |
| Free/open source | Package metadata and repository license |
| Host support | Adapter tests, demo, and accepted version floor |
| Early validation | Focused failure-path tests with lifecycle named |
| Security | Security page, tests, and scoped wording |
| Performance | Reproducible benchmark artifact and methodology |
| Component count | Build-produced count from the actual landing component tree |
| AI effectiveness | Published comparative task benchmark |
| Accessibility | Automated checks plus keyboard, screen reader, zoom, contrast, and motion review |
| Adoption or testimonial | Permission and source from a real user or organization |

The landing-page content guard should reject a configured claim whose evidence
artifact is missing, stale beyond its defined review window, or inconsistent
with package metadata. It should not test exact prose. The content plan's rule
still applies: tests cover machinery, while guards report content evidence
failures at the Markdown source line.

A registered `rendered_markdown` guard now fails any build that shows Markdown
source to a reader: a literal `### Heading` or `[text](url)` in visible text
means a raw HTML wrapper is missing `markdown="1"`, so the markdown pass skipped
the block and its links stopped being links. This is worth a guard rather than a
test because the page still builds, every other check still passes, and the
damage is only visible to someone reading the rendered page. Its first run found
three reference pages printing docstring cross-references as source.

## Success criteria

### Comprehension

The first viewport directly says that Citry is an open-source, HTML-first
frontend framework for Python web applications. It names the supported host
shape, server-rendered output, and absence of a separate frontend build without
requiring the reader to decode the component-field metaphor.

The first proof and fit sections make it possible to recognize the server and
browser boundary, name a specific difference from another stack, understand
when Citry is a poor fit, and predict what **Build your first component** does.
An expert content review checks these requirements before implementation.
Short comprehension sessions can challenge the result later, once there is a
real page and real audience; they are not an acceptance gate for the skeleton.

### Conversion quality

Track meaningful actions, not only clicks:

- copy install command;
- open first-component tutorial;
- run or fork the live example;
- open compatibility or "choose Citry when";
- reach GitHub source;
- complete the first-component journey.

Analytics require a separate privacy and retention decision. After launch, once
Citry has a real audience, later evaluation can use consented sessions and
aggregate GitHub/docs signals without adding client analytics automatically.

### Technical quality

- Core Web Vitals meet the good targets;
- no horizontal scroll at supported widths and 200% zoom;
- no content or action depends on motion or JavaScript;
- reduced-motion and pause behavior pass the written contract;
- the entire landing page passes strict docs guards;
- all code examples execute against the current package;
- literal claims link to current evidence;
- the page works under the configured base path and site/snapshot model;
- the field has no unbounded timers, listeners, retained nodes, or animation
  work when offscreen or paused.

## Design work and later validation

This is the order for updating this document.

### Research 1: expert message audit

**Complete for iteration one.** Use "Build the frontend in Python" with the
selected category, scope, CTA, and install copy in
[Research 1](#research-1-expert-message-audit). Revisit it only when implemented
evidence shows a product mismatch or later audience evidence shows persistent
misclassification.

### Research 2: component-field architecture

**Complete for iteration one.** Use the component-generated canvas projection
with 1,024 logical cells in a 41-column by 25-row descriptor field. Use the
arrival, ripple, fallback, allocation, pause, and cleanup contract in
[Prototype decision and evidence](#prototype-decision-and-evidence). The
[reviewed findings](docs_landing_page_research/component_field_proof/findings.md)
and raw artifacts preserve the literal-DOM comparison and revalidation
boundary. Research 3 may change the visual treatment, not the delivered count
or architecture without reopening this decision.

### Research 3: visual concepts

**Complete for iteration one.** The implemented direction combines the cosmic
horizon and living blueprint: a deep, luminous field in dark mode and a pale
open-sky interpretation in light mode, with the same precise grid and radial
arrival. The field is bounded to the hero, while the error lens appears in the
dedicated reliability section. The initial implementation deliberately has no
ambient loop.

The three directions considered were:

1. **Cosmic horizon:** deep dark field, luminous radial activation, spacious
   editorial typography.
2. **Living blueprint:** precise grid, code-coordinate annotations, cells
   assembling into interface shapes.
3. **Open sky:** pale atmospheric field, subtle depth and color, large negative
   space, cells dissolving toward an implied horizon.

The selected hybrid was checked against "capable", "trustworthy", "Python",
"open source", "distinctive", responsive behavior, and the written motion
contract. Future visual iteration should happen on the working page.

### Research 4: implementation and claim audit

Trace every promoted statement to released behavior, a runnable example, or a
reproducible artifact. Resolve beta status, support floors, host integrations,
error lifecycle, security wording, component count, and performance. Expected
document update: approve final copy or narrow it before publication.

### Research 5: expert competitive-positioning audit

**Complete for iteration one.** Use the short fit statement and reciprocal
alternatives in
[Research 5](#research-5-expert-competitive-positioning-audit). Do not put a
comparison table, AI leadership claim, or universal framework claim on the
first page. A reproducible task comparison is later evidence work, not a
landing-page prerequisite.

### Research 6: complete implementation review

Build the complete responsive page and review the journey from first viewport
through code proof, examples, fit, people, limitations, and installation. Check
copy hierarchy, link destinations, keyboard and reduced-motion behavior,
performance budgets, small screens, static fallback, and evidence guards.
Later usage evidence may refine the section order and CTA, but the expert audit
selects the first implementation.

## Remaining decisions

1. Which exact beta or release facts will be true when the page is published?
2. Which real showcase examples are strong enough to add without padding the
   page with ordinary component cards?
3. Is the maintainer note approved as written, and should a portrait accompany
   it later?
4. When are the talk and workshop invitation details concrete enough to add a
   staffed landing-page action?
5. Does the page need a landing-specific social card before publication?

## Implemented direction

The first iteration leads with "Build the frontend in Python", the Research 1
scope and install copy, and direct Docs and Playground actions. It renders 1,024
logical Citry components through a canvas projection and bounded radial wave,
with an honest inspector that distinguishes logical components from DOM nodes
and a static CSS fallback. "The web is your component tree" appears only after
the category and one complete component have been explained.

The proof and reliability sections demonstrate rather than describe: the card is
the sample component's own output, and the three errors are the ones Citry
raised while the page was built. Both sections fail the build instead of going
stale. All three error messages are written into the page, so a reader without
JavaScript gets every one of them and the script only collapses them to one at a
time. The sections vary in width and surface rather than repeating one shape:
the integrated path runs full width on the deeper surface, and the facts section
is deliberately the quietest on the page.

Position Citry as an integrated, HTML-first UI system for Python web
applications. Lead the reliability story with exact bug classes: missing data,
misspelled component inputs, ambient context leakage, and invalid event
bindings. Present React/Vue and Livewire as different boundaries, not defeated
competitors. Present Django as a supported host whose application services
Citry does not attempt to replace.

Treat "best Python frontend framework for AI" as a high-value research target.
The architecture gives the hypothesis real substance, especially once the
linter exists, but the landing page should earn the superlative through a
public comparative benchmark.

Make the first page human at the scale the project really has: name the
maintainer, explain why Citry exists, credit its django-components lineage,
recognize real work, and offer only staffed participation routes. Begin with a
monthly online open studio and a short talk inside an existing Pyvo community.
Add a partnered hands-on lab after the tutorial is stable. Do not create a
Citry-only meetup or bootcamp until repeat participants, a second organizer,
tested curriculum, conduct capacity, and follow-up support exist.

## Source index

### Current developer needs and messaging

- [Stack Overflow 2025 AI survey](https://survey.stackoverflow.co/2025/ai)
- [New-framework evaluation discussion, January 2026](https://www.reddit.com/r/webdev/comments/1qbvwta/what_would_make_you_consider_trying_out_a_new_web/)
- [Python backend developer choosing a frontend, January 2026](https://www.reddit.com/r/webdevelopment/comments/1qdopyy/which_framework_to_start_a_new_project_in_2026/)
- [Modern web standards and dependency concerns, June 2026](https://www.reddit.com/r/webdev/comments/1uap0pj/modern_standards/)
- [Template-engine bug study, April 2026](https://arxiv.org/abs/2604.27692)
- [Ash Framework landing-page feedback](https://news.ycombinator.com/item?id=43945477)
- [Nx homepage](https://nx.dev/) and [clearer Nx introduction](https://nx.dev/docs/getting-started/intro)

### Candidate example data

- [City of Austin Animal Center Outcomes](https://data.austintexas.gov/Health-and-Community-Services/Austin-Animal-Center-Outcomes-10-01-2013-to-05-05-/9t4d-g238) and [open-data terms](https://data.austintexas.gov/stories/s/City-of-Austin-Open-Data-Terms-of-Use/ranj-cccq/)
- [USGS real-time earthquake feeds](https://earthquake.usgs.gov/earthquakes/feed/) and [data licensing](https://www.usgs.gov/data-management/data-licensing)
- [OpenAQ API](https://docs.openaq.org/about/about), [API-key handling](https://docs.openaq.org/using-the-api/api-key), [terms](https://docs.openaq.org/about/terms), and [license metadata](https://docs.openaq.org/resources/licenses)
- [Open-Meteo API](https://open-meteo.com/) and [service/data terms](https://open-meteo.com/en/terms)
- [World Bank Indicators API](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392)
- [NASA Exoplanet Archive table access](https://exoplanetarchive.ipac.caltech.edu/docs/API_resources.html)
- [GBIF data terms](https://www.gbif.org/terms) and [API reference](https://techdocs.gbif.org/en/openapi/)
- [Our World in Data reuse guidance](https://ourworldindata.org/faqs)

### Comparison sources

- [Django 6.0 templates](https://docs.djangoproject.com/en/6.0/ref/templates/)
- [Django 6.0 security](https://docs.djangoproject.com/en/6.0/topics/security/)
- [Jinja undefined types](https://jinja.palletsprojects.com/en/stable/api/#undefined-types)
- [Jinja sandbox](https://jinja.palletsprojects.com/en/stable/sandbox/)
- [React](https://react.dev/), [TypeScript](https://react.dev/learn/typescript), and [application frameworks](https://react.dev/learn/creating-a-react-app)
- [Vue introduction](https://vuejs.org/guide/introduction.html), [props](https://vuejs.org/guide/components/props), and [tooling](https://vuejs.org/guide/scaling-up/tooling)
- [Livewire 4 components](https://livewire.laravel.com/docs/4.x/components), [Alpine](https://livewire.laravel.com/docs/4.x/alpine), and [testing](https://livewire.laravel.com/docs/4.x/testing)
- [Reflex introduction](https://reflex.dev/docs/getting-started/introduction/) and [installation/agent guidance](https://reflex.dev/docs/getting-started/installation/)
- [NiceGUI foundations](https://nicegui.io/documentation/section_foundations)
- [Flet](https://flet.dev/)
- [django-components typing and validation](https://django-components.github.io/django-components/latest/concepts/fundamentals/typing_and_validation/)

### Performance and accessibility

- [Chrome large-DOM guidance](https://developer.chrome.com/docs/lighthouse/performance/dom-size)
- [How large DOMs affect interaction](https://web.dev/articles/dom-size-and-interactivity)
- [High-performance CSS animations](https://web.dev/articles/animations-guide)
- [Core Web Vitals thresholds](https://web.dev/articles/defining-core-web-vitals-thresholds)
- [Reduced motion](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40media/prefers-reduced-motion)
- [WCAG 2.2 pause, stop, hide](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html)

### Community and human project

- [GitHub Open Source Guides: building welcoming communities](https://opensource.guide/building-community/)
- [GitHub Open Source Guides: leadership and governance](https://opensource.guide/leadership-and-governance/)
- [Contributor Covenant resources and enforcement guidance](https://www.contributor-covenant.org/resources/)
- [Django community code of conduct](https://www.djangoproject.com/conduct/)
- [Pyvo Czech Python meetups](https://pyvo.cz/en/)
- [Python Software Foundation grants](https://www.python.org/psf/grants/)
- [Python Software Foundation Community Partners](https://www.python.org/psf/community-partners/)
- [All Contributors recognition model](https://github.com/all-contributors/all-contributors)
- [FastAPI People](https://fastapi.tiangolo.com/fastapi-people/)
- [Vue team and emeriti](https://vuejs.org/about/team)
