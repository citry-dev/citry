# Phase 4 dossier: Python component packaging

**Snapshot:** 2026-07-23. **Studied units:** django-cotton-ui 0.3.2 as
the styled distribution, django-cotton 2.7.2 as its template engine, and
django-components 0.151.1 as an independent publishing and context reference.
All three are separate Python distributions. **Evidence scope:** current
official docs, PyPI metadata, source/release material, and separate tracker
searches for every named unit. No runtime reproduction was performed and no
adoption inference is made.

Evidence labels are **Docs**, **Source/release**, **Maintainer report**, **User
report**, and **Inference**. Material findings state confidence,
counterevidence, and unresolved status. Complaint grades follow the
[Phase 3 protocol](candidate-map.md#52-complaint-sample-and-confidence).

## 1. Snapshots, boundaries, dependencies, and maintenance

| Unit | Verified snapshot | Boundary and status |
|---|---|---|
| django-cotton-ui | 0.3.2, released 2026-07-07, MIT, Python 3.8+, classifier Alpha | Separate styled Django app; depends on django-cotton, ships templates plus precompiled CSS/JS, and requires Alpine 3 for interactive components. [PyPI](https://pypi.org/project/django-cotton-ui/) and [installation](https://django-cotton.com/ui/installation), Docs/Source, high |
| django-cotton | 2.7.2, released 2026-06-01, MIT, classifier Production/Stable | Template-only component engine with HTML-like tags, attributes, slots, context control, caching, and Alpine/HTMX compatibility. It is not itself a component catalog. [PyPI](https://pypi.org/project/django-cotton/) and [components](https://django-cotton.com/docs/components), Docs/Source, high |
| django-components | 0.151.1, released 2026-06-25, MIT, pre-1 | Python component classes, registries, slots, provide/inject, dependency rendering, and documented third-party library publishing. It is a comparison, not a dependency of Cotton UI. [PyPI](https://pypi.org/project/django-components/) and [component libraries](https://django-components.github.io/django-components/latest/concepts/advanced/component_libraries/), Docs/Source, high |

None has a paid component boundary in the studied package. Cotton UI's Alpha
classifier and explicit pre-1 warning are counterevidence to treating its
surface as stable. django-components also remains pre-1 despite frequent
releases. **Unresolved:** compatibility commitments after either reaches 1.0.

This packaging shape directly validates an independent Citry UI distribution:
one wheel can depend on Citry core and contain templates, Python glue, CSS, JS,
icons, and static manifests. **Inference, high.** It does not prove Cotton's
template engine or Alpine runtime should be transferred.

## 2. Normalized inventory

Cotton UI ships thirty-six documented families:

| Citry category | Cotton UI 0.3.2 |
|---|---|
| Actions | Button, dropdown actions |
| Form controls | Field, input, textarea, select, combobox, checkbox, radio, switch, range, datepicker, calendar |
| Layout/content | Accordion, card, collapse, drawer, composer, avatar, badge |
| Navigation | Breadcrumbs, nav, navbar, navlist, pagination, scrollspy, tabs |
| Overlays/feedback | Alert, dialog, dropdown, popover, toast, tooltip, progress, spinner |
| Data | Styled table; no documented stateful Data Table engine |
| Utilities | Mode toggle and theme builder |
| Specialist workflows | Composer is application-like; no file upload, tree, rich editor, or repeatable form collection documented |

Source: [installation catalog](https://django-cotton.com/ui/installation),
**Docs, high. Counterevidence:** components can be composed into more workflows;
**unresolved:** no normalized behavior/accessibility audit exists for every
family.

Cotton core contributes composition rather than visible inventory: default and
named slots, dynamic attributes/components, boolean attributes, `{{ attrs }}`
forwarding, `<c-vars>`, context isolation, and view rendering.
[Components](https://django-cotton.com/docs/components), **Docs, high.**
django-components contributes publishing infrastructure rather than this
catalog: Python component classes, registries, app discovery, templates,
static assets, slots, providers, and dependency rendering. **Docs, high.**

## 3. Composition, behavior, frozen slice, and publishing contract

Cotton UI components use `<c-ui.*>` tags or native Django template tags. Props
are template attributes/Python values; children use default/named Cotton
slots; arbitrary attributes can be forwarded with `{{ attrs }}`. Alpine data,
events, focus/collapse plugins, and the bundled UI script supply client state.
[Cotton components](https://django-cotton.com/docs/components) and
[UI installation](https://django-cotton.com/ui/installation), **Docs, high.**
There is no typed event schema, universal compound-part protocol, or declared
portal service. **Docs observation, medium-high; unresolved:** per-component
Alpine events and generated IDs require source audit.

| Frozen probe | Verified finding | Evidence and status |
|---|---|---|
| Button | Styled variants through `c-ui.button`; ordinary attributes and slot content compose it | [Installation verification](https://django-cotton.com/ui/installation#verify-it-works), Docs, high |
| Field/Input | Separate Field/Input/Textarea/Select families; native attributes can be forwarded and form semantics stay in rendered HTML | [UI catalog](https://django-cotton.com/ui/installation), [Cotton attrs](https://django-cotton.com/docs/components), Docs, high; exact error contract unresolved |
| Dialog | Styled interactive component relying on Alpine focus behavior; source markup is server-rendered | [Installation plugins](https://django-cotton.com/ui/installation#required-alpinejs-plugins), Docs, high; nested/teleported overlay policy unresolved |
| Combobox/searchable Select | Both Combobox and Select are documented catalog entries | [UI catalog](https://django-cotton.com/ui/installation), Docs, high; remote querying and item identity not established in reviewed docs |
| Tabs | Styled Tabs family; Alpine is the interaction layer | [Tabs](https://django-cotton.com/ui/components/tabs), Docs, high; controlled-state/event contract unresolved |
| Table/Data Table | Styled Table exists; no verified sort/filter/pagination/virtualization engine | [Table](https://django-cotton.com/ui/components/table), Docs observation, high |
| Advanced form/collection | No first-party repeatable collection engine found; ordinary Django forms can be composed from fields | Catalog observation, medium-high; absence does not exclude application composition |
| Provider/context | Cotton inherits Django context by default; django-components has explicit server render-scoped provide/inject | [Cotton context](https://django-cotton.com/docs/components#9-context-isolation), [provide/inject](https://django-components.github.io/django-components/latest/concepts/advanced/provide_inject/), Docs, high |

django-components documents a package as a Django app containing component
Python, templates, and static files, optionally with its own `Library` and
`ComponentRegistry`, then published with normal PyPI metadata and installed via
`INSTALLED_APPS`. [Component libraries](https://django-components.github.io/django-components/latest/concepts/advanced/component_libraries/),
**Docs, high.** This is strong evidence for `citry-ui` as a separate wheel.
**Counterevidence:** the registry contract is under active redesign;
**unresolved:** Citry should not copy registry naming before its own discovery
and namespace rules are stable.

## 4. Customization ladder and styled/headless implications

| Level | Cotton UI/Cotton contract | Citry reading |
|---|---|---|
| Tokens | CSS variables for accent, ink, surfaces, radius, shadow, focus, light/dark | Strong basis for a default styled theme |
| Variants | Component attributes such as button variant plus dark-mode/theme settings | Keep a coherent cross-family variant vocabulary |
| Parts | Template slots and consumer classes, but no suite-wide named internal-parts contract | Add explicit Citry Parts rather than rely on descendant classes |
| State | Alpine state plus native/ARIA attributes, specific to component templates | Styled and headless modes need shared state/event names |
| Markup | Slots and attributes customize within installed templates | More control than closed shadow DOM, less than application-owned source |
| Behavior | Bundled UI JS and Alpine plugins | Headless behavior is not independently packaged |
| Source/build | Precompiled assets by default; optional Tailwind rebuild scans generated source list | Good no-build baseline with advanced build escape hatch |

Source: [theming](https://django-cotton.com/ui/theming) and
[installation](https://django-cotton.com/ui/installation), **Docs, high.**
Issue 13 documents that class projection was initially uneven and cannot map a
single class attribute onto multiple internal elements. **Maintainer report,
grade B. Counterevidence:** it was closed during rapid 0.2.x work; **unresolved:**
0.3.2's exact class-merge surface was not reproduced.

Cotton UI is styled-first. Headless use means bypassing its templates and
using Cotton/Alpine directly, not selecting a supported headless form of the
same component. Citry should distribute paired styled and headless contracts,
not equate template-engine extensibility with a headless library.

## 5. Accessibility, input modes, locale, and context

Cotton UI describes itself as accessible and uses the Alpine focus plugin for
focus trapping and keyboard navigation in dialogs, drawers, menus, select,
popover, and calendar. [PyPI description](https://pypi.org/project/django-cotton-ui/)
and [required plugins](https://django-cotton.com/ui/installation#required-alpinejs-plugins),
**Docs claim, medium confidence as published posture, not independent
conformance.** No suite-wide keyboard matrix, screen-reader matrix, touch/IME
tests, forced-color support, reduced-motion policy, RTL audit, or localization
contract was found. **Unresolved, low-to-medium confidence.** Native controls
and server HTML are counterevidence to assuming poor accessibility, but not a
substitute for testing complex controls.

### Ambient-context audit

| Question | Cotton and django-components finding |
|---|---|
| Values carried | Cotton gets ordinary Django context and context-processor values; django-components provides named immutable records |
| Nesting and shadowing | Cotton can isolate fully with `only` or preserve processors with smart isolation. django-components requires render nesting; nearest same-key shadowing was not verified in reviewed docs |
| Defaults and errors | Cotton inheritance is default. django-components `inject()` raises `KeyError` unless a default is supplied |
| Reactive update | Both are server render-time values, not reactive browser context |
| SSR/client agreement | Server values must be explicitly serialized into Alpine/DOM state; no automatic agreement layer exists |
| Portal/teleport | Provider scope is template/component render ancestry. Browser relocation/overlay ancestry is not covered |
| Cleanup | Server providers end with render scope; Alpine component cleanup remains client-runtime work |
| Diagnostics | Cotton isolation is configuration/flags; django-components supplies a missing-provider exception but no cross-client diagnostic |

Sources: [Cotton context isolation](https://django-cotton.com/docs/components#9-context-isolation)
and [django-components provide/inject](https://django-components.github.io/django-components/latest/concepts/advanced/provide_inject/),
**Docs, high. Counterevidence:** Cotton's normal Django context is often enough;
**unresolved:** Citry needs one or two linked server/client context systems.
The reference strongly pressures `$provide`/`$inject`; Alpine lifecycle also
pressures `$component.init()` and disposer semantics.

## 6. Forms, validation, submission, and async state

Cotton templates can render native Django form controls, names, values,
errors, CSRF inputs, and ordinary server submission. The UI catalog adds Field
and input families but does not replace Django's validation/request model.
[Cotton form-input tutorial](https://django-cotton.com/docs/form-inputs),
**Docs, high.** Alpine behavior enhances controls, and HTMX attributes can be
forwarded, but no suite-level async form protocol, pending state, remote-error
schema, or collection submission model was found. **Docs observation,
medium-high. Counterevidence:** application-authored Alpine/HTMX can supply
these; **unresolved:** Cotton UI component-specific form association and error
focus require reproduction.

django-components can publish form components but does not impose a form
state library. That is the desired packaging separation for Citry: ship native
server-form defaults without requiring a client form store.

## 7. Trust and security boundaries

Cotton's `{{ attrs }}` and dynamic attributes are a broad forwarding boundary.
Issue 361 demonstrated attribute breakout/XSS in 2.6.2 and 2.7.0 and was closed
through PR 362; the snapshot is 2.7.2. [Issue 361](https://github.com/wrabit/django-cotton/issues/361),
**User report with reproducer and linked fix, grade B. Counterevidence:** fixed
before the studied patch release; **unresolved:** no local regression test was
run. Citry must centralize attribute escaping, reject unsafe event/URL
forwarding by default, and test every shorthand syntax.

django-components documents that component directories are separate from
static exposure and only allowed asset extensions are served; Python and
template sources are not exposed. [Security notes](https://django-components.github.io/django-components/latest/overview/security_notes/),
**Docs, high.** Version 0.148 added dependency hooks suitable for CSP nonces.
[Release 0.148](https://django-components.github.io/django-components/latest/releases/v0.148.0/),
**Docs, high.** No Cotton UI file upload, remote-result trust policy, generated
ID policy, or central CSP nonce contract was found. **Unresolved.**

## 8. Assets, runtime, performance, and upgrades

Cotton UI's wheel contains `cotton-ui.css` and `cotton-ui.min.js`; Django
staticfiles and `collectstatic` deliver them. Interactive components require
Alpine core plus collapse/focus plugins, which docs show from a CDN but can be
vendored. The no-build path is complete. A custom Tailwind 4 build runs
`cotton_ui_sources`, imports the deterministic generated source list, and
should wire it as a build pre-step.
[Installation](https://django-cotton.com/ui/installation), **Docs, high.**
This is close to Citry's desired separate wheel and precompiled-assets model.

Counterevidence is app-order sensitivity and the combined Python, Django app,
staticfiles, Alpine, plugin, and optional Tailwind upgrade surface. Cotton UI
0.3.2 remains Alpha. **Unresolved:** payload, strict CSP, offline icons/fonts,
and upgrade compatibility were not reproduced.

django-components supports inline or linked JS/CSS, dependency collection,
deduplication, and fragment metadata/lazy dependency fetch.
[Rendering JS/CSS](https://django-components.github.io/django-components/latest/concepts/advanced/rendering_js_css/),
**Docs, high.** Its open v1 umbrella work shows static export and dependency
post-processing are still evolving. Citry should define a simpler manifest and
asset deduplication contract before publishing its UI wheel.

## 9. Material shortcomings and complaint evidence

| ID | De-duplicated pattern | Window, status, workflow, workaround, and grade |
|---|---|---|
| PCP-1 | Cotton UI's class override/part projection was uneven | Maintainer-opened 2026-06-13 and closed in the 0.2.x release burst. It explicitly says one class cannot project to multiple internal elements. Use tokens, documented props, slots, or wrappers. [UI issue 13](https://github.com/wrabit/django-cotton-ui/issues/13), grade B; current exact surface unresolved |
| PCP-2 | Cotton dynamic attributes had an attribute-injection path | Reproduced on 2.6.2/2.7.0, opened and fixed 2026-06-01. Upgrade to 2.7.2 and keep escaping regression tests. [Cotton issue 361](https://github.com/wrabit/django-cotton/issues/361), grade B, resolved history |
| PCP-3 | Cotton 2.0 reran context processors per component | A page with eighty components multiplied a database-backed processor; opened 2025-03-13 and later fixed. Current docs say processor output is captured once per request. [Cotton issue 269](https://github.com/wrabit/django-cotton/issues/269) and [configuration](https://django-cotton.com/docs/configuration), grade B, resolved with strong counterevidence |
| PCP-4 | django-components publishing identity is under redesign | Open roadmap since 2025-05-19 proposes phasing out registered names and ComponentRegistry usage. Library authors must track v1/v2 migration. [Issue 1195](https://github.com/django-components/django-components/issues/1195), grade B |
| PCP-5 | django-components static dependency export is incomplete | Open v1 umbrella since 2024-12-08 still lists `collectstatic` export, inlining, public IDs, and post-processing work. Use current dependency manager or application asset build. [Issue 836](https://github.com/django-components/django-components/issues/836), grade B |

These patterns are separated by layer. Resolved Cotton histories are not
presented as current 2.7.2 defects, and django-components reports do not imply
Cotton has the same registry or asset behavior.

### Complaint metadata audit

| ID | Affected and current version | Dates and status | Maintainer response and workaround | Impact |
|---|---|---|---|---|
| PCP-1 | Reported during Cotton UI's 0.2.x release burst; the issue does not name a narrower affected version. Current 0.3.2 was not reproduced. | Maintainer opened 2026-06-13 and closed it during the 0.2.x work; a separate last-update date was not found in the retained evidence. | The maintainer-authored issue is the response. Use semantic tokens, documented props, slots, or wrappers rather than assuming one class projects to multiple nodes. | Medium customization friction. |
| PCP-2 | Cotton 2.6.2 and 2.7.0 affected; fixed release 2.7.2. | Opened and fixed 2026-06-01; closed at snapshot. | Maintainer fix and release are verified. Upgrade to 2.7.2 and retain hostile-attribute regression tests. | High security impact in affected releases. |
| PCP-3 | Cotton 2.0 behavior affected; current 2.7.2 documentation is counterevidence and current code was not reproduced. | Opened 2025-03-13 and closed after the request-scoped capture fix; the precise closure/update date was not found. | Maintainers restored once-per-request processor capture. Upgrade and test database-backed context on dense pages. | High performance impact on component-dense pages. |
| PCP-4 | Current django-components 0.151.1 is the pre-v1 baseline; the report is a v1/v2 publishing roadmap risk rather than a reproduced 0.151.1 defect. | Open since 2025-05-19; precise last-update date was not recorded in this audit. | Maintainers proposed phasing out registered names and registry coupling. Library authors should pin, follow the roadmap, and test both public identity and discovery. | High for reusable-library authors. |
| PCP-5 | Current django-components 0.151.1 remains before the proposed v1 asset contract. | Open umbrella since 2024-12-08; precise last-update date was not recorded in this audit. | Use the current dependency manager or application-owned asset build while tracking export, inlining, public-ID, and post-processing work. | High for distributable component packages. |

### Complaint search log

Window: 2024-07-23 through 2026-07-23. Exact tracker queries, run separately:

**Cotton UI**

- `repo:wrabit/django-cotton-ui is:issue created:2024-07-23..2026-07-23 accessibility OR focus OR keyboard`
- `repo:wrabit/django-cotton-ui is:issue created:2024-07-23..2026-07-23 install OR Tailwind OR Alpine OR asset`
- `repo:wrabit/django-cotton-ui is:issue created:2024-07-23..2026-07-23 form OR select OR dialog`

**Cotton**

- `repo:wrabit/django-cotton is:issue created:2024-07-23..2026-07-23 slot OR context OR attribute OR escape`
- `repo:wrabit/django-cotton is:issue created:2024-07-23..2026-07-23 package OR discovery OR cache OR security`

**django-components**

- `repo:django-components/django-components is:issue created:2024-07-23..2026-07-23 publish OR library OR registry OR autodiscovery`
- `repo:django-components/django-components is:issue created:2024-07-23..2026-07-23 asset OR dependency OR CSP OR fragment OR provide`

**Alpine interactive layer**

- `repo:alpinejs/alpine is:issue created:2024-07-23..2026-07-23 (focus OR teleport OR CSP OR cleanup)`

The young Cotton UI tracker had too little independent evidence for three
current complaint patterns. This dossier logs the shortfall and does not fill
it with weak reports. Alpine was searched because Cotton UI ships it as the
load-bearing interactive layer. No Alpine report was retained without a
verified Cotton UI outcome; Alpine-specific findings would otherwise be
double-counted or generalized beyond the Python package under review.

## 10. Citry conclusions

### Adopt or re-derive

- A separate Django/Python UI wheel depending on core, with templates, static
  assets, discovery metadata, and `collectstatic` support.
- Precompiled no-build assets plus a deterministic advanced build path.
- HTML-like components, named slots, explicit configuration props, native
  forms, semantic tokens, and server render-scoped context.
- Package-level security tests for attribute forwarding and asset exposure.
- A documented library namespace and asset deduplication manifest.

### Do not transfer directly

- Cotton, Alpine, Tailwind, or django-components registry APIs as Citry's
  public contract.
- Alpha component surfaces, arbitrary attribute forwarding, or consumer CSS
  classes as the only internal-part customization path.
- A server-only provider presented as if client descendants and teleports
  automatically share it.
- Inline dependency rendering without an explicit CSP, caching, and upgrade
  policy.

### Pressure on Citry contracts

This comparison is the clearest evidence that the UI belongs in an independent
distribution. Citry must first stabilize component discovery, namespace
collision behavior, asset manifests, package version compatibility, and
attribute escaping. `$provide`/`$inject` needs documented nesting, shadowing,
defaults, immutability, SSR serialization, client reactivity, teleport
behavior, and diagnostics. `$component.init()` needs one initialization and
cleanup contract independent of which UI wheel supplies the component. Styled
and headless variants must share props, state, events, IDs, and form behavior
rather than being unrelated templates under one package name.
