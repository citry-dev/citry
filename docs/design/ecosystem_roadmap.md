# Citry ecosystem roadmap

**Status (2026-08-11): research-backed roadmap guidance.** This document
records the ecosystem evidence used to evaluate the public
[Roadmap](https://github.com/citry-dev/citry/issues/79). It identifies recurring
application jobs and recommends how they should affect Citry's priorities. It
does not turn package popularity into an automatic commitment to implement a
first-party feature.

The dated [Citry UI component inventory](ui_component_inventory.md) records
product decisions through 2026-08-09, while the current source registration is
already ahead of it. The event and transport baseline is recorded in the
[Events design](events.md). Section 5 reconciles those implemented but not
necessarily released capabilities before identifying gaps.

## 1. Decision summary

The roadmap passes the most important ecosystem check: its main tracks address
jobs that recur across Vue, Django, Livewire/Laravel, React, and Rails.

The strongest recurring jobs are:

- accessible UI primitives and coherent styled component families;
- forms, validation, and field integration;
- tables, filtering, sorting, pagination, and admin workflows;
- uploads, storage integration, and media handling;
- internationalization;
- testing, debugging, and component-development tooling;
- styling-system integration; and
- rich text, charts, and date/time input.

This evidence is consistent with the current emphasis on Citry UI contracts,
accessibility, reusable patterns, forms, data display, CRUD/admin workflows,
ecosystem integrations, and diagnostics. The public roadmap's order still
comes from Citry prerequisites and product decisions, not download rank.

It does not establish an exact total ordering. Download counts measure package
activity, not Citry user demand or architectural fit. Framework built-ins hide
demand that would otherwise appear in package traffic. Some popular packages
solve jobs Citry already supports, while others assume a hydrated client
runtime that Citry deliberately does not use.

The resulting roadmap guidance is:

1. Keep the current near-term Citry UI foundation work first.
2. Validate forms, tables, and admin workflows through real Citry applications
   before freezing generated APIs.
3. Treat the remaining upload-execution work as a product flow spanning
   transport, validation, storage, progress, and failure recovery. Native file
   intake is already implemented.
4. Keep rich-text editing as long-term specialist work. A bounded adapter
   experiment remains an unranked hypothesis until a Citry application needs
   it.
5. Keep charts as a separate product track, after the core display and input
   contracts are stable.
6. Retain generic incremental-response support as a Citry product hypothesis,
   with LLM output as one use case rather than an AI-specific component
   product. Ecosystem examples establish precedent, not priority.
7. Keep the separately planned server-initiated push work distinct from
   request-scoped streaming.
8. Research email output and later PDF output as constrained rendering
   adapters. Do not infer first-party ownership from server-framework package
   counts alone.
9. Audit recurring browser utilities against Citry's SSR, Alpine, and Events
   model before adding a general utilities package.
10. Build package discovery or a registry only when maintained Citry
    extensions create an actual discovery problem.

## 2. Research question and method

The research asked whether Citry's roadmap reflects work that framework users
actually adopt, and whether obvious recurring jobs are missing.

The evidence is a representative ecosystem snapshot taken on 2026-08-11. It
uses:

- official ecosystem directories and documentation;
- exact npm download windows where available;
- Packagist package statistics;
- rolling-month PyPI Stats data backed by the PyPI public dataset;
- official RubyGems lifetime download data;
- official framework surveys; and
- repository and plugin-directory activity where it adds a different signal.

The measurements are intentionally not combined into one score. npm, PyPI,
Packagist, RubyGems, repository stars, directories, and surveys have different
populations and counting rules. Package suites can double-count the same
application, CI and transitive installs inflate downloads, and lifetime counts
favor older packages. Survey percentages may measure preference rather than
adoption. Directory size measures supply and discoverability, not unmet demand.

Built-in framework capabilities create a second important limit. Django's
admin, forms, authentication, email, and internationalization; Laravel's
validation, [queues](https://laravel.com/docs/12.x/queues), storage, and
broadcasting; and Rails'
[Active Job](https://guides.rubyonrails.org/active_job_basics.html),
[Active Storage](https://guides.rubyonrails.org/active_storage_overview.html),
[Action Text](https://guides.rubyonrails.org/action_text_overview.html), and
Action Cable can all be heavily used without producing corresponding
third-party package downloads. Weak external-package traffic therefore cannot
establish that a job is unimportant.

The evidence is used in three steps:

1. Identify recurring application jobs within each ecosystem.
2. Check whether the same jobs recur across ecosystems with different runtime
   models.
3. Compare those jobs with Citry's existing capabilities and architecture,
   then name only the remaining product gap.

## 3. Ecosystem evidence

### 3.1 Vue and Nuxt

Vue provides the closest component-oriented comparison, but many popular Vue
packages assume long-lived client state and a hydrated application. The useful
signal for Citry is the recurring job, not the implementation model.

The candidate set came from the official
[Vue ecosystem themes](https://vuejs.org/ecosystem/themes),
[awesome-vue](https://github.com/vuejs/awesome-vue), and the
[Nuxt module directory](https://nuxt.com/modules). Exact npm downloads below
cover July 2026.

| Exact npm package | July 2026 npm downloads | Job signaled |
|---|---:|---|
| [`@vueuse/core`](https://api.npmjs.org/downloads/point/2026-07-01:2026-07-31/%40vueuse%2Fcore) | 38,428,842 | Reusable browser and state utilities |
| [`@vue/test-utils`](https://api.npmjs.org/downloads/point/2026-07-01:2026-07-31/%40vue%2Ftest-utils) | 18,113,575 | Component testing |
| [`vue-i18n`](https://api.npmjs.org/downloads/point/2026-07-01:2026-07-31/vue-i18n) | 14,608,527 | Internationalization |
| [`reka-ui`](https://api.npmjs.org/downloads/point/2026-07-01:2026-07-31/reka-ui) | 6,206,661 | Accessible headless primitives |
| [`@tiptap/vue-3`](https://api.npmjs.org/downloads/point/2026-07-01:2026-07-31/%40tiptap%2Fvue-3) | 5,909,528 | Rich-text editing |
| `@headlessui/vue` | 5,439,442 | Accessible headless primitives |
| `unplugin-vue-components` | 5,409,653 | Component discovery and imports |
| [`vee-validate`](https://api.npmjs.org/downloads/point/2026-07-01:2026-07-31/vee-validate) | 4,538,411 | Forms and validation |
| `vuetify` | 4,323,057 | Integrated styled UI system |
| [`vue-chartjs`](https://api.npmjs.org/downloads/point/2026-07-01:2026-07-31/vue-chartjs) | 4,073,524 | Charts |
| [`@tanstack/vue-table`](https://api.npmjs.org/downloads/point/2026-07-01:2026-07-31/%40tanstack%2Fvue-table) | 3,890,588 | Data tables |
| `@vuepic/vue-datepicker` | 3,027,449 | Date/time input |
| `primevue` | 3,025,381 | Integrated styled UI system |
| `@tanstack/vue-query` | 2,848,797 | Async server-state handling |
| `@nuxtjs/i18n` | 2,442,589 | Framework-level internationalization |
| `@nuxt/ui` | 2,112,560 | Integrated application UI |
| `@nuxt/image` | 1,803,038 | Image optimization and delivery |
| `vue-filepond` | 324,479 | File uploads |

The recurring activity is clear for utilities, testing, internationalization,
accessible primitives, styled suites, forms, tables, rich text, charts, and
date/time input. The Nuxt directory contains more than 319 modules, which shows
an established supply and discovery surface for framework-integrated
extensions. That count measures neither installs nor unmet demand and does not
by itself justify a Citry registry.

Vue-native transactional email is a weak signal. For example,
[`@vue-email/render`](https://api.npmjs.org/downloads/point/2026-07-01:2026-07-31/%40vue-email%2Frender)
recorded 67,971 July downloads, and the
[Vue Email repository](https://github.com/vue-email/vue-email) describes the
project as experimental. This says little about email demand in server
applications, where the capability may live outside the Vue layer.

### 3.2 Django

Django is a useful comparison for server-rendered applications and for product
areas the framework already owns. The
[2025 Django Developers Survey](https://lp.jetbrains.com/django-developer-survey-2025/)
had 4,655 respondents. Its third-party package percentages below are selections
among respondents' five favorite packages, not package adoption rates.

| Survey signal | Share selecting it among five favorites | Job signaled |
|---|---:|---|
| Django REST Framework | 49% | API construction |
| Django Debug Toolbar | 27% | Diagnostics and performance inspection |
| django-celery | 26% | Background-work preference signal |
| django-cors-headers | 19% | Cross-origin integration |
| django-filter | 18% | Filtering and query controls |
| django-allauth | 18% | Authentication workflows |
| pytest-django | 15% | Testing integration |

The same survey separately reported pytest-django use by 30% of respondents.
It also found Django's built-in admin and authentication useful to 75% and 69%
of respondents respectively. These built-ins are evidence for the underlying
jobs even though they reduce third-party package traffic.

Rolling-month PyPI Stats add package-activity evidence:

| Package | Rolling-month downloads | Job signaled |
|---|---:|---|
| [django-filter](https://pypistats.org/api/packages/django-filter/recent) | 16,731,647 | Filtering |
| django-extensions | 13,775,649 | Development utilities |
| django-storages | 12,380,949 | Storage integration |
| django-redis | 12,203,287 | Cache integration |
| [django-debug-toolbar](https://pypistats.org/api/packages/django-debug-toolbar/recent) | 8,723,705 | Diagnostics |
| [django-formtools](https://pypistats.org/api/packages/django-formtools/recent) | 3,818,214 | Multi-step and advanced forms |
| [django-crispy-forms](https://pypistats.org/api/packages/django-crispy-forms/recent) | 3,044,646 | Form rendering and layout |
| [django-import-export](https://pypistats.org/api/packages/django-import-export/recent) | 2,860,893 | Admin import and export |
| django-widget-tweaks | 1,370,682 | Form-widget presentation |
| Wagtail | 1,058,068 | Content administration |
| django-tables2 | 946,281 | Data tables |

The [Django Packages forms grid](https://djangopackages.org/grids/g/forms/)
lists 89 packages. The direct Citry fit is forms and rendering, admin and
internal tools, tables and filters, import/export workflows, template
components, styling integrations, and diagnostics.

Django 6.0 includes template partials. Citry's differentiation cannot rest on
partials alone; it lies in typed component contracts, explicit slots,
colocation, asset ownership, event integration, and diagnostics.

Email and PDF require care. Django's built-in email support hides much of the
job, and packages such as Anymail measure delivery-provider integration rather
than component rendering. django-weasyprint is much smaller than the table,
filter, and import/export packages above. The ecosystem establishes that
server applications produce email and documents, but not that Citry should own
the delivery or document engine.

### 3.3 Livewire and Laravel

Livewire is the closest comparison for server-driven interaction. Laravel also
provides a mature package market for complete application workflows. The
figures below are monthly Packagist downloads at the research snapshot.

| Package or project | Monthly downloads | Job signaled |
|---|---:|---|
| Livewire core | 5,517,579 | Server-driven interaction |
| [spatie/laravel-permission](https://packagist.org/packages/spatie/laravel-permission.json) | 5,176,387 | Roles and permissions |
| [barryvdh/laravel-dompdf](https://packagist.org/packages/barryvdh/laravel-dompdf.json) | 4,901,386 | PDF generation |
| [maatwebsite/excel](https://packagist.org/packages/maatwebsite/excel.json) | 4,678,488 | Spreadsheet import and export |
| Laravel Fortify | 4,029,842 | Authentication workflows |
| Blade Icons | 3,642,337 | Icon integration |
| [Filament](https://packagist.org/packages/filament/filament.json) | 3,052,856 | Admin panels, forms, and tables |
| [Laravel Reverb](https://packagist.org/packages/laravel/reverb.json) | 2,776,424 | Server-initiated realtime delivery |
| [Spatie Media Library](https://packagist.org/packages/spatie/laravel-medialibrary.json) | 2,145,950 | Upload and media lifecycle |
| [Laravel AI](https://packagist.org/packages/laravel/ai.json) | 1,506,902 | Model-provider integration |
| Spatie Translatable | 1,239,900 | Localized data |
| Flux | 1,119,624 | Livewire UI components |
| Livewire Pest | 449,354 | Interactive-component testing |

[Filament's plugin directory](https://filamentphp.com/plugins?sort=popular)
listed 938 plugins from 440 authors, while the project had about 31,800 GitHub
stars. This makes Filament a useful case study of one integrated product that
combines admin/CRUD, forms, tables, filtering, bulk actions, exports,
permissions, uploads, media, and rich-content workflows. The aggregate plugin
count and metapackage activity do not measure demand for each constituent job.
The separate PDF and spreadsheet package activity shows recurring
server-output usage, though framework ownership still needs a separate
decision.

Livewire's [`wire:stream`](https://livewire.laravel.com/docs/4.x/wire-stream)
provides incremental output during one active HTTP request. The principal
example is AI output, but this mechanism is distinct from Reverb's
server-initiated realtime delivery. Direct Livewire AI-chat products remain
small. The useful Citry conclusion is to investigate a generic incremental
response primitive, with LLM output as an example, rather than to prioritize an
AI-specific product.

### 3.4 React cross-check

React is not an architectural template for Citry. It is a large independent
sample that helps reveal recurring browser-facing jobs. The figures below are
npm downloads from 2026-07-11 through 2026-08-09.

| Exact npm package | Downloads in the window | Job signaled |
|---|---:|---|
| `lucide-react` | 381,157,697 | Icons |
| `@radix-ui/react-dialog` | 278,881,807 | Accessible dialog primitive |
| `@tanstack/react-query` | 253,740,234 | Async server state |
| `react-hook-form` | 236,211,568 | Forms and validation |
| `recharts` | 221,297,525 | Charts |
| `@testing-library/react` | 205,548,249 | User-oriented testing |
| `@dnd-kit/core` | 87,290,825 | Drag and drop |
| `storybook` | 81,437,309 | Component development and documentation |
| `@tanstack/react-table` | 70,995,666 | Data tables |
| `react-i18next` | 58,701,260 | Internationalization |
| `@tiptap/react` | 51,674,602 | Rich-text editing |
| `react-dropzone` | 50,640,743 | File intake and uploads |
| `@mui/material` | 41,120,109 | Integrated styled UI system |
| `react-datepicker` | 20,083,039 | Date/time input |

The [State of React 2025 libraries survey](https://2025.stateofreact.com/en-US/libraries/)
received roughly 2,700 answers per item. It reported TanStack Query used by
68.1% of respondents, MUI by 57.2%, and shadcn/ui by 56.1%. shadcn/ui rose from
about 20% to 56% in two years. These are self-selected survey results, but they
show substantial respondent experience with coherent, adaptable component
systems. They do not establish why respondents adopted them or how Citry
should rank its work.

The React and Vue utility signals require a Citry-specific audit. VueUse,
TanStack Query, and similar libraries assume client-owned state and lifecycle.
Citry combines server rendering, Alpine behavior, and Events, so the correct
question is which user jobs remain awkward after those existing layers are
used, not whether Citry should reproduce client-framework APIs.

### 3.5 Rails cross-check

RubyGems provides lifetime downloads, so the figures below are durable category
signals rather than current market-share measurements.

| Package | Lifetime downloads | Job signaled |
|---|---:|---|
| [Devise](https://rubygems.org/gems/devise) | 290.6 million | Authentication |
| Kaminari | 267.6 million | Pagination |
| [CarrierWave](https://rubygems.org/gems/carrierwave) | 139.9 million | Uploads |
| [Ransack](https://rubygems.org/gems/ransack) | 115.4 million | Search and filtering |
| Pundit | 107.3 million | Authorization |
| [Prawn](https://rubygems.org/gems/prawn) | 100.8 million | PDF generation |
| [Simple Form](https://rubygems.org/gems/simple_form) | 96.8 million | Form construction |
| CanCanCan | 93.5 million | Authorization |
| [WickedPDF](https://rubygems.org/gems/wicked_pdf) | 84.4 million | HTML-to-PDF output |
| Formtastic | 62.7 million | Form construction |
| ViewComponent | 61.2 million | Server-rendered components |
| [ActiveAdmin](https://rubygems.org/gems/activeadmin) | 50.0 million | Admin and CRUD |
| letter_opener_web | 49.6 million | Email preview and development |
| Pagy | 41.8 million | Pagination |

Rails independently reinforces the durability of authentication,
authorization, admin, forms, filtering, pagination, uploads, document output,
and server-rendered component jobs. The age of several packages and the
lifetime metric prevent conclusions about current implementation preferences.

## 4. Cross-ecosystem findings

### 4.1 Recurring jobs supported by multiple sources

The following jobs recur through multiple independent ecosystems and
measurement types:

- **Forms and validation.** Form construction, field rendering, validation,
  and framework integration are consistently prominent.
- **Tables, filtering, pagination, and admin.** These appear as individual
  packages and as integrated products such as Django admin, Filament, and
  ActiveAdmin.
- **Coherent UI systems.** Headless primitives and styled component families
  have repeated package and survey activity in Vue, React, and Livewire. The
  metrics do not establish accessibility as the reason for adoption, but the
  products make accessibility part of the job Citry must qualify.
- **Uploads and media.** Upload intake, storage, progress, preview, and media
  lifecycle recur across browser and server ecosystems.
- **Internationalization.** i18n is prominent in Vue and React, built into
  Django, and represented in Laravel packages.
- **Testing and diagnostics.** Component testing, framework testing adapters,
  debug toolbars, and development environments are durable needs.
- **Rich text, charts, and date/time.** Each recurs in client ecosystems. That
  establishes a job to evaluate, not transferability to Citry's runtime.

These findings corroborate that the jobs recur. They do not prove that Citry
should own every layer or establish when any one job should ship.

### 4.2 Real jobs with conditional Citry ownership

- **Authentication and permissions** are central application jobs. Citry
  already provides event guards and host security integration. The remaining
  Citry work is permission-aware admin patterns and host examples, not a new
  identity or generic authorization system.
- **Email** is a real server-application job. Citry may usefully own a bounded
  component vocabulary and compatibility-oriented renderer while delivery,
  queues, and provider integration remain host responsibilities.
- **PDF and reports** are real jobs. Citry may own an adapter from a constrained
  component vocabulary to an external document engine, but should not assume
  ownership of layout or PDF generation before a prototype proves value.
- **Imports and exports** belong naturally to admin workflows. Existing Events
  download support means the likely gap is higher-level workflow composition,
  formats, validation, and progress, not a new generic download primitive.
- **Browser utilities** have high package activity in client ecosystems. Only
  utilities that remain awkward under Citry's SSR, Alpine, and Events model
  should become first-party work.
- **Incremental responses** have useful API precedent. The evidence does not
  establish broad demand or priority. If Citry pursues its existing product
  hypothesis, a generic capability is more defensible than a dedicated
  LLM-chat component.
- **RSS, sitemap, and Open Graph images** are common publishing outputs, but
  package traffic is especially unreliable because frameworks and deployment
  platforms often provide them. The census neither raises nor lowers their
  current roadmap placement.

Open Graph image generation is not XML. It means producing an image referenced
by social metadata such as `og:image`, usually from a template or page data.
The docs site already renders such social-card templates to PNG. Atom/RSS and
sitemap generation produce XML, and the docs site already has Atom and sitemap
serializers. Product work would generalize those existing pipelines. The three
outputs can share routing, caching, build, and preview tooling, but they need
different permitted vocabularies and output rules.

### 4.3 Evidence that should not rank the roadmap

Some roadmap decisions require Citry-specific evidence rather than ecosystem
package popularity:

- WebAssembly component support;
- smaller wire or DOM deltas;
- optional server-initiated pub/sub delivery;
- ports to other host languages;
- editor integrations for smaller editor populations; and
- the exact shape of the extension registry.

These may be valuable, but package counts from other runtime models do not
measure their value to Citry. Performance work needs profiles and real
application traces. Compatibility work needs named integration demand.
Registry work needs a sufficiently large maintained package population.

## 5. Citry baseline

Roadmap gaps must be described relative to capabilities that already exist.
The dated
[UI component inventory](ui_component_inventory.md#3-current-production-baseline)
records, among other families:

- Form, Field, Input, Textarea, native Select, Checkbox, Radio, Switch, and
  remote Combobox with request ordering;
- semantic Table and Pagination;
- Icon with a registered catalog;
- Progress, Spinner, Alert, Dialog, Popover, Menu, Toast, and other production
  families; and
- responsive layout and application-surface primitives.

The tracked source has advanced beyond that 2026-08-09 inventory. The
[current registration surface](../../packages/py/citry_ui/tests/test_citry_ui_registration.py)
also includes `CFileInput`, `CDropTarget`, `CSelect`, `CListbox`,
`CMultiSelect`, `CTree`, `CCarousel`, `CEditable`, `CStepper`, `CSplitter`,
`CToolbar`, `CNavigationMenu`, `CHoverCard`, and `CAlertDialog`. These are
implemented source capabilities, not a claim that a compatible public
artifact has been released.

In particular, the
[file-input contract](../../packages/py/citry_ui/citry_ui/components/cfile_input/api.md)
already owns native file selection, accessible drop behavior, and Form
semantics. It deliberately does not read, preview, validate, remove, or upload
files. The remaining gap is the upload lifecycle and its application-facing
state, not file intake.

The [Events design](events.md) already specifies host-neutral authorization
guards, CSRF integration, latest-wins queue and response handling, request
bundling, typed errors, polling, loading/error state, timeout behavior, and
cancellation/drop semantics. A received server call can still execute even
when a newer call causes its eventual response to be ignored. The Events guide
also documents a
[download action and CSV export example](../../docs_site/content/events/http.md#downloads).

Consequently, the roadmap should not describe table foundations, an icon
registry, authorization boundaries, request-ordering basics, or a generic
download hook as missing. Remaining work should name a higher-level job, such
as server-driven table query coordination, permission-aware admin actions, or
validated import/export workflows.

`State._storage = "server"` already keeps event state in cache-backed server
storage across requests. A separate connection-scoped live-session state
feature is not currently on the roadmap. Server-initiated push remains a
separate transport capability and does not require inventing another general
state-storage mode first.

## 6. Roadmap implications

### 6.1 Near term

Keep the public roadmap's near-term sequence unchanged:

1. Publish and release-harden the current Citry, LSP, editor, formatter, and UI
   work already in flight.
2. Stabilize the shared field contract, theme tokens, state presentation,
   accessibility primitives, and qualification across existing UI families.
3. Harden the implemented i18n foundation and finish current non-localized UI
   work before localized advanced inputs depend on it.

The ecosystem evidence corroborates that the underlying UI, field, i18n, and
tooling jobs recur. It does not justify moving advanced inputs or specialist
products ahead of release and prerequisite work.

### 6.2 Forms, data display, and CRUD/admin

Keep CRUD/admin as one epic with two independently testable subtracks:

1. **Data display:** server-side sorting, filtering, pagination, selection,
   bulk actions, empty/loading/error states, and export workflows built on the
   existing Table, Pagination, and Events contracts.
2. **Form builder:** opinionated data-driven fields, schema-generated forms,
   nested/repeated inputs, validation mapping, conditional fields, and
   create/edit workflows built on the shared Field and Form contracts.

The popularity of forms does not prove demand for a schema-generated builder
or determine its API. Prototype at least one real schema source, with Pydantic
as an early integration candidate, before freezing a general contract.

The admin epic should be judged by complete workflows, including permissions,
imports/exports, uploads/media, validation, destructive-action confirmation,
and recovery from partial failure. These are acceptance concerns, not reasons
to duplicate low-level capabilities already present in Citry.

### 6.3 Upload execution and media

Build the mid-term upload lifecycle on the implemented `CFileInput` and
`CDropTarget` selection family. Keep three owners explicit:

- the UI presentation composes accessible errors, previews, and `CProgress`,
  displays transport state, and emits cancel or retry intent without executing
  those operations itself;
- the transport executes multipart or staged transfer, cancellation, and
  retry, enforces size and timeout policy, and reports progress and failure;
  and
- host integrations cover durable storage, authorization, scanning,
  transformations, cleanup, and media metadata.

This split keeps storage-provider policy out of a UI component while still
supporting a coherent end-to-end product.

### 6.4 Date/time, charts, and rich text

Keep localized date/time controls in the mid-term Citry UI track, after the
i18n work ratifies locale resolution, parsing, formatting, time zones, and
server/browser agreement. Timezone conversion and persistence policy must
remain explicit rather than being hidden in display widgets.

Keep charts and visualizations as a separate track. Mid-term research and
prototypes should define data, accessibility, theming, SSR/fallback,
responsiveness, and asset-loading contracts. Production stays long term and
conditional on those prototypes and application evidence.

Keep rich-text editing as long-term specialist work. The client-adapter package
activity in Vue and React does not establish fit with Citry. A bounded adapter
experiment is an optional, unranked hypothesis only when a named application
needs it. Such an experiment would have to decide document format,
sanitization ownership, SSR behavior, editor loading, asset cost, controlled
updates, collaboration exclusions, and Form integration.

### 6.5 Email, PDF, feeds, and generated images

Research email as a constrained output target. A plausible Citry boundary is a
permitted component vocabulary with named inputs and slots that renders to
email-safe HTML, including inline CSS, table-compatible layouts, plain-text
fallback, preview, and compatibility tests. Delivery, queues, bounce handling,
and provider credentials stay with the host application.

Keep PDF/report output as long-term work. A permitted vocabulary could protect
pagination, headers/footers, tables, page sizes, print CSS, and deterministic
assets while an external engine performs generation. The work should proceed
only if a prototype is more useful than ordinary HTML/print composition.

The docs site already contains an
[Atom feed serializer](../../docs_site/_internal/build.py),
[sitemap serializer](../../docs_site/_internal/seo.py), and
[component-to-PNG social-card pipeline](../../docs_site/_internal/social_cards.py).
Productization would extract typed records, validation, routing helpers, and a
supported configuration surface from those site-local implementations. The
outputs can share build, caching, asset, and preview tooling, but should not
share one vocabulary. The census does not change their current long-term
roadmap placement or rank them relative to email and PDF.

### 6.6 Incremental responses and server push

The public roadmap retains a generic incremental-response primitive as its own
mid-term product hypothesis. `wire:stream` provides API precedent, not broad
demand evidence or a priority score. The proposed Citry component would define
the initiating endpoint, request inputs, headers or host authorization
integration, visible pending/error/completed states, and optional
pre/post-processing. The server-side handler may call an LLM or any other
streaming source and relay bounded output to the client.

The design must decide framing, cancellation, reconnect behavior, backpressure,
timeouts, partial-output errors, sanitization, morph interaction, and testing.
Direct browser-to-provider requests should be evaluated separately because
they expose different credential, CORS, abuse, and data-governance risks.

The public roadmap separately retains server-initiated pub/sub push as a
mid-term product hypothesis. Reverb measures a different job and does not rank
Citry's implementation. Push covers events that originate without an active
browser request and should not be conflated with incremental output from one
request. Both hypotheses need Citry application evidence before their detailed
priority is frozen.

### 6.7 Tooling and ecosystem

The ecosystem census adds no reason to override the prerequisite order in the
[extension design](extensions.md), the
[extensions roadmap](extensions_roadmap.md), and the public roadmap:

1. Build Scoped CSS and the ColorLogger extension-authoring tutorial first,
   deciding conditional hooks only when Scoped CSS proves a need.
2. Complete the asset-compiler, component-introspection, and live-reload work
   that later authoring integrations consume.
3. Preserve the extensions roadmap's later sequence of head-tag injection,
   inline CSS, Tailwind, Storybook, and bounded Pydantic work. Tailwind waits
   for its scanner and asset prerequisites.
4. Develop testing helpers, component previews and documentation, tracing,
   diagnostics, and the host debug-toolbar work on their named foundations.
5. Limit new Pydantic work to the form-metadata and mapping gaps not covered by
   Citry's existing Pydantic v1/v2 schemas, validation, introspection, Events,
   and OpenAPI support.
6. Build discovery or registry tooling only after maintained third-party
   packages make discovery costly.
7. Keep additional editor integrations, including Neovim, Zed, and Helix,
   later unless contributor evidence changes.

The maintainer decision to omit speculative JavaScript, PHP, Go, or Rust host
products from the public roadmap is independent of this census. Package
popularity provides no evidence for or against those ports, and rebuilding the
Python product surface in another host language would be a separate major
undertaking.

### 6.8 Runtime and infrastructure

Keep most runtime and infrastructure work below product-surface work until
measurements identify a concrete limit. Smaller wire or DOM deltas need traces
from real Citry applications. WebAssembly support needs named compatibility or
performance cases. The public roadmap's mid-term server-push hypothesis is a
separate product decision; this census cannot rank it, and its detailed design
should start from actual collaboration, notification, or job-progress use
cases.

## 7. Falsifiers and next evidence

This roadmap guidance should change if Citry-specific evidence contradicts it.
The next useful evidence is not another package census. It is a set of bounded
product experiments:

1. Build a real filtering, sorting, pagination, selection, and export screen
   using existing Table, Pagination, and Events. Record repeated application
   code and missing contracts.
2. Build one create/edit workflow from a Pydantic model. Measure how much
   schema generation is genuinely reusable and where explicit author control
   is necessary.
3. Dogfood a permission-aware admin surface with bulk and destructive actions,
   uploads, and recoverable validation failures.
4. Prototype a file flow from selection through progress, cancellation,
   validation, durable storage, and cleanup.
5. If the streaming hypothesis advances, prototype a generic
   incremental-response component against both an LLM and a non-LLM streaming
   endpoint before freezing its priority or API.
6. Prototype one transactional email and one paginated report. Compare the
   constrained vocabulary with ordinary Citry HTML composition and reject the
   adapter if it adds little safety or compatibility value.
7. Inventory browser behaviors repeatedly reimplemented in Citry applications
   before proposing a utilities package.
8. Define a registry threshold, such as a minimum number of maintained
   external packages and repeated user reports of discovery difficulty, before
   building central discovery infrastructure.

Evidence that would lower a priority includes low reuse across two real
applications, an API dominated by host-specific policy, unacceptable asset or
maintenance cost, inaccessible behavior that cannot be made reliable, or an
existing Citry composition that already solves the job clearly.

## 8. Evidence limits and maintenance

This is a dated research record, not a live popularity dashboard. Package
counts will change, and some source APIs report rolling windows whose exact
dates differ from the fixed npm windows. Re-run the census only when a roadmap
decision depends on current ecosystem movement.

Do not use the tables to claim cross-ecosystem market share. Do not add the
figures together. Do not infer unique users. Do not treat a plugin-directory
count as direct demand. When updating this document, preserve the measurement
type and date next to each claim and distinguish built-in capabilities from
third-party package activity.

The roadmap should ultimately be ordered by the combination of recurring user
jobs, Citry-specific application evidence, architectural fit, prerequisite
contracts, maintenance cost, and failure risk. Ecosystem activity answers only
the first of those questions.
