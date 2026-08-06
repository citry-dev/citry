# Phase 4 dossier: django-formset

**Snapshot:** 2026-07-23. **Studied line:** django-formset 2.2.4, released
2026-03-30. **Evidence scope:** current official documentation, the 2.2.4
release/source, PyPI metadata, and the public issue tracker. Development
releases for 2.3 are excluded. No runtime reproduction was performed and no
adoption inference is made.

Evidence labels are **Docs**, **Source/release**, **Maintainer report**, **User
report**, and **Inference**. Material findings state confidence,
counterevidence, and unresolved status. Complaint grades follow the
[Phase 3 protocol](candidate-map.md#52-complaint-sample-and-confidence).

## 1. Product snapshot, boundary, dependencies, and maintenance

django-formset 2.2.4 is an MIT-licensed Django form renderer and browser
runtime. Its stable metadata supports Python 3.10 through 3.13 and Django 5.1,
5.2, and 6.0. The browser side is written in TypeScript and distributed as
JavaScript without a third-party JavaScript runtime dependency.
[PyPI](https://pypi.org/project/django-formset/) and
[installation](https://django-formset.fly.dev/installation/), **Docs and
Source/release, high confidence.** The frequent 2.2 patch releases and 2.3
development releases are evidence of maintenance, not compatibility or
adoption. **Unresolved:** the eventual 2.3 contract and migration cost.

No paid component or runtime capability boundary was identified in the 2.2.4
package metadata, MIT source license, or official documentation. The studied
forms, collections, widgets, custom-element runtime, and CSS-framework
renderers are part of the open package rather than a commercial tier.
Applications still own the licensing and cost of any separately selected CSS
framework, service, font, or rich-text integration. [PyPI](https://pypi.org/project/django-formset/)
and [source license](https://github.com/jrief/django-formset/blob/2.2.4/LICENSE),
**Source and docs observation, high confidence for django-formset itself;
unresolved for optional application dependencies.**

The product boundary is specialist rather than suite-wide: it turns Django
forms, collections, and widgets into rich server-backed workflows. It does not
ship a general page-layout, navigation, feedback, or data-display component
system. It instead renders against Bootstrap 5, Bulma, Foundation 6, Tailwind,
or UIkit CSS through framework-specific renderers.
[CSS framework installation](https://django-formset.fly.dev/installation/#css-framework),
**Docs, high. Counterevidence:** dialog, stepper, calendar, upload, and
rich-text families reach beyond ordinary fields; **unresolved:** exact
compatibility with newer framework releases than those documented.

## 2. Normalized inventory

| Citry category | django-formset 2.2.4 |
|---|---|
| Actions | Button and Activator widgets with chained client actions |
| Form controls | All standard Django widgets; enhanced select, dual selector, slug, date/datetime/range, decimal-unit, country, phone, and rich-text widgets |
| Layout/content | Form collections, nested collections, dialogs, model-form dialogs, and steppers |
| Navigation | Stepper workflow navigation; no general breadcrumbs, menu, navbar, or tabs family |
| Feedback | Field errors and server feedback, success/error messages, upload progress; no general alert/toast catalog |
| Data | Select query results and JSON-backed collections; no general Table or Data Table |
| Advanced workflows | Async upload, conditional expressions, dynamic/sortable siblings, nested collections, partial step submission, dialog CRUD, admin integration |
| Utilities | Five CSS-framework renderers, JavaScript gettext catalog, dark-mode adaptation |

Sources: [default widgets](https://django-formset.fly.dev/default-widgets/),
[form collections](https://django-formset.fly.dev/form-collections/),
[collection fields](https://django-formset.fly.dev/collection-fields/), and
[documentation catalog](https://django-formset.fly.dev/), **Docs, high.** The
table records documented families, not a claim that every combination is
equally mature. **Unresolved:** there is no published normalized support
matrix across browsers, CSS renderers, and nested workflow combinations.

## 3. Composition, behavior, and frozen slice

The server renders a `<django-formset>` custom element around Django forms.
That element owns client validation, JSON submission through `fetch`, server
feedback, and the activation of enhanced widgets. Its `endpoint`,
`csrf-token`, `force-submission`, and `withhold-feedback` attributes configure
the request and feedback boundary.
[Custom element](https://django-formset.fly.dev/django-formset/), **Docs,
high.** This is an application-local form controller, not a general provider.

Actions are authored as expression strings, while widgets and collections use
Django field names, collection paths, and model values as identity. Client
source dynamically imports optional behavior for selectize, dialogs, dates,
steppers, and rich text.
[Button actions](https://django-formset.fly.dev/buttons/),
[2.2.4 client source](https://github.com/jrief/django-formset/blob/2.2.4/client/django-formset.ts),
**Docs and Source observation, high. Counterevidence:** central lazy loading
keeps optional code out of the initial graph; **unresolved:** stability of
action-string grammar and identity during every nested reorder.

| Frozen probe | Verified finding | Evidence and status |
|---|---|---|
| Button | `Button` and `Activator` can submit, partially submit, reload, disable, show a spinner, and open or close workflows through action chains | [Buttons](https://django-formset.fly.dev/buttons/), Docs, high |
| Field/Input | All standard Django widgets render as ordinary HTML; enhanced alternatives opt into the client runtime | [Default widgets](https://django-formset.fly.dev/default-widgets/), Docs, high |
| Dialog | Dialog forms are nested in `FormCollection`, rendered with native `dialog`, and opened or closed through activators and expressions; modal and non-modal forms are supported | [Dialog forms](https://django-formset.fly.dev/dialog-forms/), Docs, high; nested path defects appear in section 9 |
| Combobox/searchable Select | Selectize supports searchable single/multiple selection and remote model queries without jQuery or Select2 | [Selectize](https://django-formset.fly.dev/selectize/), Docs, high; remote authorization guidance unresolved |
| Tabs | No general Tabs component. Stepper is a sequential form workflow, not an interchangeable tab pattern | [Form stepper](https://django-formset.fly.dev/form-stepper/), Docs observation, high |
| Table/Data Table | No general table or stateful data grid ships. Collections and admin integration do not supply a generic grid contract | [Documentation catalog](https://django-formset.fly.dev/), Docs observation, medium-high |
| Advanced form/collection | Nested and sortable `FormCollection` siblings, JSON collection fields, dialog model forms, and step-level partial validation are first-class | [Form collections](https://django-formset.fly.dev/form-collections/), [collection fields](https://django-formset.fly.dev/collection-fields/), Docs, high |
| Provider/context | `<django-formset>` carries endpoint, CSRF, submission, and feedback settings to its contained forms. Theme and language follow CSS/Django rather than a generic context API | [Custom element](https://django-formset.fly.dev/django-formset/), Docs, high |

### Ambient-context audit

| Question | Finding |
|---|---|
| Values carried | Endpoint, CSRF token, submission policy, and feedback policy on the custom element; locale through Django gettext; visual values through the selected CSS framework |
| Nesting and shadowing | Form and collection path nesting is explicit. No general nearest-provider shadowing contract was found |
| Defaults and overrides | Custom-element attributes have documented defaults; widgets and renderer settings override server-side behavior |
| Reactive update | Client controllers react to form and widget state. No documented reactive ambient-value API exists |
| SSR/client agreement | The server owns initial HTML and constraints; the custom element upgrades that markup and submits JSON |
| Portal/teleport | Native dialogs remain in their rendered DOM location. No logical portal provider or teleport contract was found |
| Cleanup | Custom-element lifecycle and widget controllers own listeners; dynamic-insertion failure in section 9 shows activation is not universally self-healing |
| Diagnostics | Field/server errors are displayed, but no missing-context or duplicate-initialization diagnostic was found |

Sources: [custom element](https://django-formset.fly.dev/django-formset/),
[JavaScript catalog setup](https://django-formset.fly.dev/installation/#javascript-catalog),
and [dialog forms](https://django-formset.fly.dev/dialog-forms/), **Docs, high
for documented behavior, medium for absence findings.** This mainly pressures
`$component.init()` to activate, re-activate, and dispose behavior under Citry
morphs. `$provide`/`$inject` remains necessary for generic theme, direction,
services, and portal values, but django-formset does not establish that API.

## 4. Customization ladder and styled/headless implications

| Level | django-formset contract | Citry reading |
|---|---|---|
| Tokens | Styling comes primarily from a selected CSS framework plus django-formset additions | Do not mistake framework compatibility for a coherent Citry token system |
| Variants | Renderer choice and widget/configuration kwargs change presentation and behavior | Keep server kwargs typed and shared between modes |
| Parts | Templates and CSS selectors expose structure, but no suite-wide named-parts versioning contract was found | Citry needs explicit stable Parts |
| State | Native validity, Django errors, custom-element attributes, action expressions, and widget controllers | Preserve one state/event vocabulary across styled and headless forms |
| Markup | Django renderers and widgets own generated markup; applications can subclass or replace them | Useful server-rendered escape hatch, with upgrade cost |
| Behavior | One browser controller plus dynamically imported optional modules | Strong specialist runtime, not independently packaged headless behavior |
| Source/build | Wheel assets work without a Node build; custom CSS can be compiled separately | Strong no-build precedent |

Sources: [installation](https://django-formset.fly.dev/installation/) and
[styling](https://django-formset.fly.dev/styling/), **Docs, high.** The library
is neither a complete styled design system nor a headless suite. Its widgets
render semantically meaningful HTML and can use several visual frameworks, but
the enhanced behavior, custom element, and form renderer are one integrated
product. **Inference, high. Counterevidence:** default Django widgets need no
special client implementation; **unresolved:** how many enhanced widgets
remain useful with the library CSS removed.

## 5. Accessibility, input modes, locale, and visual preferences

Native HTML controls and native `dialog` provide a sound platform baseline.
The custom widgets also contain ARIA and focus code, and the server supplies
translated strings through Django's JavaScript catalog.
[Default widgets](https://django-formset.fly.dev/default-widgets/),
[dialog forms](https://django-formset.fly.dev/dialog-forms/), and
[installation](https://django-formset.fly.dev/installation/#javascript-catalog),
**Docs and Source observation, medium-high.** These mechanisms are not a
suite-wide accessibility conformance result.

No published keyboard table, screen-reader/browser matrix, touch or IME test
record, reduced-motion policy, forced-colors audit, or RTL matrix was found.
Dark mode is supported by adapting the custom elements, but the docs do not
ship the user's mode switch. [Dark mode](https://django-formset.fly.dev/dark-mode/),
**Docs, high for dark-mode scope and medium for absence findings.** Date input
behavior can vary by browser and device, which is counterevidence to assuming
one uniform interaction. **Unresolved:** focus restoration for nested dialogs,
keyboard sorting, RTL action layout, mobile screen-reader use, 400% zoom, and
high-contrast behavior require reproduction.

## 6. Forms, validation, submission, and async state

Forms are the core strength. The browser derives client constraints from
Django fields, blocks invalid submission unless `force-submission` is set,
sends JSON through `fetch`, and displays server errors beside the controls.
The server view returns structured errors with HTTP 422 for invalid data.
[Custom element](https://django-formset.fly.dev/django-formset/) and
[2.2.4 view source](https://github.com/jrief/django-formset/blob/2.2.4/formset/views.py),
**Docs and Source observation, high.** Native form semantics remain in the
rendered controls, but ordinary browser submission is not the enhanced
wrapper's default transport. Issue 201 in section 9 is direct counterevidence
for traditional-view interoperability.

Stepper actions can partially validate one step on the server and defer full
submission until the end. Collections serialize nested forms and siblings as
JSON. File widgets upload to temporary storage before final form submission,
and remote Selectize fields query the endpoint asynchronously.
[Stepper](https://django-formset.fly.dev/form-stepper/),
[collections](https://django-formset.fly.dev/form-collections/), and
[file upload](https://django-formset.fly.dev/uploading/), **Docs, high.**
Loading/error behavior is feature-specific rather than one general async state
contract. **Unresolved:** disabled-JavaScript submission for enhanced forms,
out-of-order remote results, cancellation, upload cleanup, and focus after
server error replacement.

## 7. Trust and security boundaries

The form controller requires a CSRF token and sends it in the request header;
the Django server remains the final validation authority. Client MIME checks
are only early feedback, as the upload finding in section 9 shows.
[Custom element](https://django-formset.fly.dev/django-formset/) and
[issue 251](https://github.com/jrief/django-formset/issues/251), **Docs and
User report, high for the boundary.** Citry should preserve both server
validation and typed client errors rather than treating browser checks as a
security gate.

Dialog prologue/epilogue HTML may require Django `mark_safe`, and the rich-text
guide warns that storing arbitrary submitted HTML is a security risk.
[Dialog forms](https://django-formset.fly.dev/dialog-forms/) and
[rich text](https://django-formset.fly.dev/richtext/), **Docs, high.** These
are explicit trusted-content boundaries. Remote Selectize results, action and
conditional expression strings, URLs, arbitrary forwarded attributes,
temporary files, and generated IDs also require threat tests. **Inference,
medium-high.** No central sanitizer, URL allowlist, upload-retention threat
guide, strict-CSP guidance, or generated-ID collision policy was found.
**Unresolved:** authorization and query limits for remote results, rich-text
sanitization ownership, and CSP behavior of dynamic module imports.

## 8. Assets, runtime, SSR, performance, and upgrades

The wheel ships a modular ES2020 entry file at `formset/js/django-formset.js`.
Optional features are dynamically imported. A monolithic build is available;
the docs report about 22 kB for the default modular build and about 258 kB for
the monolithic build after minification and gzip. These are publisher figures,
not local measurements. [Installation](https://django-formset.fly.dev/installation/),
**Docs claim, high as stated and unreproduced.** There is no required Node
build or external browser library.

CSS is extracted for the chosen Bootstrap, Bulma, Foundation, Tailwind, or
UIkit renderer. Optional collection and Bootstrap extras add CSS. The runtime
must be able to read matching style rules, so cross-origin styles need
appropriate access; translated browser messages require the Django JavaScript
catalog. **Docs, high. Counterevidence:** the modular build limits initial
code; **unresolved:** icon/font ownership, exact per-widget chunks, strict CSP,
offline install, and normalized cold-start cost.

Initial HTML is server rendered, but rich behavior depends on custom-element
upgrade and fetch. The library does not claim client hydration of a virtual
DOM. Upgrade risk spans Django renderer markup, Python widgets/views, CSS
framework output, custom-element attributes, action grammar, and browser
modules. **Docs and Inference, medium-high.** Citry needs wheel compatibility,
asset-manifest, and markup-version policies before depending on such a
specialist package.

## 9. Material shortcomings and complaint evidence

| ID | De-duplicated pattern | Window, status, workflow, workaround, and grade |
|---|---|---|
| DF-1 | The JSON/fetch controller does not naturally reuse traditional request/response views | Opened 2025-02-05 and open at the snapshot. A user wanted built-in Django login/password views without rewriting them for the mixin endpoint. Keep ordinary forms outside the enhanced controller or write an adapter. The report alone is grade D, but the mandatory endpoint/mixin design is [current documented behavior](https://django-formset.fly.dev/django-formset/), so the architectural limitation is grade A. [Issue 201](https://github.com/jrief/django-formset/issues/201) |
| DF-2 | Interactive validation feedback cannot be fully disabled for every workflow | Opened 2025-02-17 and open at the snapshot. Validation on blur was reported as disruptive; `withhold-feedback` suppresses categories but is not documented as a complete validation-off switch. [Issue 205](https://github.com/jrief/django-formset/issues/205) and [feedback settings](https://django-formset.fly.dev/django-formset/), preference/search lead, grade D; not used in synthesis |
| DF-3 | Dynamically inserted forms may miss widget activation | Opened 2026-06-23 and open at the snapshot with an HTMX popover reproducer. A newly inserted Selectize field stayed plain unless compatible formset code had already loaded. Preload the feature or manually coordinate initialization. The tagged entry module scans the initial document and collection templates, corroborating the activation boundary. [Issue 270](https://github.com/jrief/django-formset/issues/270) and [2.2.4 entry source](https://github.com/jrief/django-formset/blob/2.2.4/client/django-formset.ts), current limitation, grade A |
| DF-4 | Nested collection paths can break dialog actions | Opened 2026-01-21 and open at the snapshot. `induce_open` and `induce_close` failed when a fieldset added another path level. Flattening or application-specific path changes are provisional workarounds. The report is labeled as a bug in the project tracker. [Issue 260](https://github.com/jrief/django-formset/issues/260), current defect report, grade B |
| DF-5 | File-type client prechecks allow a temporary upload before server rejection in one selection path | Opened 2025-12-06 and closed 2025-12-27, but 2.2.4 source still calls the MIME check for drag/drop and not for the file-input change handler. Final Django validation still rejects the file, so this is temporary-upload exposure rather than a final-validation bypass. [Issue 251](https://github.com/jrief/django-formset/issues/251) and [2.2.4 upload source](https://github.com/jrief/django-formset/blob/2.2.4/client/django-formset/FileUploadWidget.ts), current source-backed limitation, grade A |

No prevalence claim is made. Open issues are user reports unless a maintainer
or current source confirms them; their grades do not turn them into universal
defects. DF-2 is retained only as a search lead and has documented partial
counterevidence through `withhold-feedback`. DF-5's closed tracker state is
counterevidence, but the 2.2.4 tagged source retains the reported path.

### Complaint search log

Window: 2024-07-23 through 2026-07-23. Exact tracker queries:

- `repo:jrief/django-formset is:issue created:2024-07-23..2026-07-23 accessibility OR focus OR keyboard`
- `repo:jrief/django-formset is:issue created:2024-07-23..2026-07-23 collection OR sortable OR nested`
- `repo:jrief/django-formset is:issue created:2024-07-23..2026-07-23 upload OR CSP OR CSRF OR security`
- `repo:jrief/django-formset is:issue created:2024-07-23..2026-07-23 validation OR selectize OR dialog`

## 10. Citry conclusions

### Adopt or re-derive

- Server-rendered native fields with enhanced widgets layered on top.
- Django constraints as the source for client feedback, with authoritative
  server validation and structured field errors.
- Nested collection paths, stable item identity, partial step submission,
  temporary upload lifecycle, and model-form dialogs as advanced probes.
- One installable wheel with static assets, lazy optional modules, no required
  Node build, and explicit CSS-renderer adapters.
- An initialization contract that handles first load, fragment insertion,
  morphing, removal, and feature modules not present at page startup.

### Do not transfer directly

- A specialist form controller as Citry's general component provider.
- JSON/fetch-only enhancement that makes traditional Django views difficult to
  reuse or leaves no meaningful disabled-JavaScript path.
- String action grammar, trusted HTML, or broad remote-query behavior without
  typed capabilities and explicit threat policies.
- Styling delegated to several external CSS frameworks in place of Citry's own
  coherent styled default and headless counterpart.

### Pressure on Citry contracts

django-formset pressures Citry's Field/Input, Combobox, Dialog, collection,
validation, upload, and async contracts much more than its general catalog.
`$component.init()` must be deterministic when fragments arrive after startup,
must preserve active state through morphs, and must dispose per-widget work.
The provider exploration still needs `$provide`/`$inject` for theme,
direction, services, portal roots, and nested defaults because a form wrapper
does not solve ambient context. Styled and headless versions should share
field paths, collection identity, errors, actions, focus rules, and server
submission semantics while remaining usable before optional client behavior
attaches.
