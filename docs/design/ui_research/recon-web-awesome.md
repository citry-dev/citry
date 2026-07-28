# Phase 4 dossier: Web Awesome

**Snapshot:** 2026-07-23. **Studied line:** Web Awesome 3.10.0, with
Shoelace 2.x only as migration lineage. **Evidence scope:** current official
documentation, repository/source and release metadata, and the Web Awesome and
archived Shoelace trackers. No runtime reproduction was performed. Repository
counts are not treated as adoption evidence.

Evidence labels are **Docs**, **Source/release**, **Maintainer report**, **User
report**, and **Inference**. Confidence and counterevidence are stated for
material findings. Complaint grades follow the
[Phase 3 protocol](candidate-map.md#52-complaint-sample-and-confidence).

## 1. Product snapshot, boundary, dependencies, and maintenance

Web Awesome 3.10.0 is a Lit-based web-component library. Core is MIT licensed;
Pro has a separate paid license and includes some themes, patterns, Figma
assets, form controls, page/video/toast families, and data visualization.
[Core license](https://webawesome.com/license/),
[component catalog](https://webawesome.com/docs/components/), and
[installation](https://webawesome.com/docs/), **Docs and Source/release, high
confidence.** The free/pro boundary is visible per catalog item, but Pro's
redistribution terms were not audited here. **Unresolved:** whether every
future category stays available in Core.

The npm distribution is `@awesome.me/webawesome`. Consumers can use an
autoloading project/CDN, import individual modules, bundle `dist`, or self-host
the self-contained `dist-cdn` build. Component source uses Lit; icons can use a
Font Awesome kit but that is optional. **Docs, high. Counterevidence:** direct
custom elements work without a framework adapter; **unresolved:** normalized
dependency and payload measurements were not reproduced.

The current site identifies 3.10.0 and the tracker/release history is active.
Shoelace was archived in March 2026 and points users to Web Awesome, so it is
lineage rather than a second current candidate.
[Shoelace archive](https://github.com/shoelace-style/shoelace), **Source
observation, high.** This establishes a migration event, not adoption.

## 2. Normalized inventory

| Citry category | Web Awesome 3.10.0 |
|---|---|
| Actions | Button, button group, copy button, dropdown and dropdown item |
| Form controls | Checkbox/group, color picker, input, number input, radio/group, rating, select/option, slider, switch, textarea, time input; Combobox, date input/picker, and file input are Pro |
| Layout/content | Accordion/item, card, details, dialog, divider, drawer, page, scroller, split panel |
| Navigation | Breadcrumb/item, tab group/tab/panel, tree/item |
| Feedback | Badge, callout, progress bar/ring, skeleton, spinner, tag, tooltip; toast is Pro |
| Media/data | Avatar, carousel, comparison, icon, Markdown, QR code; charts are Pro; Data Grid is planned, not shipped |
| Helpers | Animation, formatters, include, observers, popover/popup, relative time, random content |
| Utilities | Themes, palettes, design tokens, native-element styles, CSS utilities, framework wrappers, SSR tooling |

Source: [current catalog](https://webawesome.com/docs/components/), **Docs,
high. Counterevidence:** Pro materially expands breadth; **unresolved:** planned
Data Grid has no usable contract and is excluded from the shipped inventory.

## 3. Composition, behavior, and frozen slice

Components use custom-element attributes/properties, DOM methods, custom
events, slots, CSS custom properties, custom states, and versioned CSS Parts.
Shadow DOM encapsulates internal markup while slots compose light-DOM content.
[Customizing](https://webawesome.com/docs/customizing) and
[Select API](https://webawesome.com/docs/components/select/), **Docs, high.**
Events are mostly lifecycle/value notifications; reviewed docs do not promise
one suite-wide reason/cancel schema. **Docs observation, medium-high;
unresolved:** per-event cancellation must be audited component by component.

| Frozen probe | Verified finding | Evidence and status |
|---|---|---|
| Button | Styled custom element with appearances, sizes, loading/disabled states, slots, methods, events, properties, and Parts | [Button](https://webawesome.com/docs/components/button/), Docs, high |
| Field/Input | Form-associated controls expose label/hint slots or attributes, name/value, validity, native form participation, states, and Parts | [Forms](https://webawesome.com/docs/form-controls), Docs, high |
| Dialog | Uses an internal native `dialog`, controlled `open`, initial focus, light dismiss, cancelable show/hide lifecycle, slots, and Parts | [Dialog](https://webawesome.com/docs/components/dialog/), Docs, high; nested-dialog policy unresolved |
| Combobox/searchable Select | Core Select owns option values, multiple selection, lazy option loading, tags, methods, events, and listbox Parts; the distinct search-first Combobox is Pro | [Select](https://webawesome.com/docs/components/select/), [catalog](https://webawesome.com/docs/components/), Docs, high |
| Tabs | Compound tab group/tab/panel identified by names; supports orientation, placement, controlled active tab, and automatic/manual keyboard activation | [Tab group](https://webawesome.com/docs/components/tab-group/), Docs, high |
| Table/Data Table | Native table styles exist, but no component or stateful grid ships; Data Grid is only planned | [Catalog](https://webawesome.com/docs/components/), Docs, high |
| Advanced form/collection | Strong individual controls but no repeatable form collection/workflow engine in Core; Pro patterns are not a runtime collection API | Catalog observation, high; paid patterns not audited |
| Provider/context | No general provider. Theme uses inherited CSS variables/classes; locale/direction use document or component attributes | [Themes](https://webawesome.com/docs/themes), [localization](https://webawesome.com/docs/localization/), Docs, high |

Option `value` and tab/panel names are explicit item identity. Slotted content
stays in the light DOM, while internal nodes remain behind the shadow root.
**Docs, high. Counterevidence:** methods and properties allow deeper control;
**unresolved:** server-generated IDs and identity across Citry morphs remain
application responsibilities.

### Ambient-context audit

| Question | Finding |
|---|---|
| Values carried | Theme/palette/brand through inherited CSS; language and direction through `lang`/`dir`; base path and optional icon kit through setup APIs |
| Nesting and shadowing | CSS classes/variables follow normal DOM cascade. Per-component locale requires `lang`/`dir` on the component itself rather than an arbitrary ancestor |
| Defaults and overrides | Document language defaults component strings, with English fallback; component attributes override locally |
| Reactive update | Localization observes document changes; component-local attributes update the element. Theme variables update through CSS |
| SSR/client agreement | SSR is experimental; current docs list locale, direction, base-path, icon, chart, QR, timing, and slot-detection limitations |
| Portal/teleport | No general logical portal provider was found. Popup placement stays a component concern; DOM inheritance remains decisive |
| Cleanup | Custom-element connection owns listeners/update lifecycle, but dynamic definitions and async imports require timing discipline |
| Diagnostics | Hydration errors and failed imports surface in runtime tooling; no missing-locale/theme-provider diagnostic was found |

Sources: [localization](https://webawesome.com/docs/localization/) and
[SSR](https://webawesome.com/docs/ssr/), **Docs, high. Counterevidence:** CSS
and DOM attributes are simpler than a provider runtime. Unresolved is how
context behaves across an application-owned teleport. Citry likely needs
`$provide`/`$inject` for non-CSS values and `$component.init()` for client
upgrade timing, not a copy of Web Awesome's document observers.

## 4. Customization ladder and styled/headless implications

| Level | Web Awesome contract | Citry reading |
|---|---|---|
| Tokens | Global design tokens, themes, palettes, brands, and component custom properties | Strong semantic and component token precedent |
| Variants | Attributes such as appearance, size, orientation, placement, and state | Coherent styled surface |
| Parts | Public `::part()` names are documented as a versioned API | Stable named parts should exist in both Citry modes |
| State | Reflected properties, custom states, ARIA/native state, and lifecycle events | Share state vocabulary between headless and styled packages |
| Markup | Slots customize content, but shadow internals are not replaceable | Safer defaults, bounded structural control |
| Behavior | Methods/properties/events control the installed runtime | Headless reuse is not independently packaged |
| Source | Installed npm package; consumers can fork but ordinary branding does not require it | Prefer centralized updates over application copies |

The library's [customization guide](https://webawesome.com/docs/customizing)
says public Parts are protected until a major release, **Docs, high.** An open
tracker report shows documentation and naming can still be inconsistent across
components, so the guarantee does not prove completeness. **Counterevidence,
grade D for the unverified individual report; unresolved:** full 3.10.0 Part
consistency.

Web Awesome is styled and behavior-complete, not headless. Shadow DOM makes a
second headless mode particularly difficult because behavior is coupled to
internal templates. Citry should adopt named Parts and tokens, but keep
headless behavior as a first-class server/client contract rather than asking
users to neutralize a styled shadow tree.

## 5. Accessibility, input modes, locale, and visual preferences

Web Awesome publishes an accessibility commitment rather than universal
conformance. It says browser and assistive-technology support for web
components continues to evolve. The browser policy covers the latest two major
versions and explicitly names NVDA with Chrome/Firefox and VoiceOver with
Safari. [Accessibility](https://webawesome.com/docs/resources/accessibility/)
and [browser support](https://webawesome.com/docs/resources/browser-support/),
**Docs claim, high confidence as posture, not an independent audit.**

The components use native elements, ARIA, keyboard/focus behavior, and touch
handling. Localization loads product translations, follows document `lang`,
and supports component-local `lang`/`dir`; it does not translate consumer
content. [Localization](https://webawesome.com/docs/localization/), **Docs,
high.** Reduced-motion, forced-colors, zoom, IME, and RTL results were not
found as a suite-wide published matrix. **Unresolved, medium confidence.**
Resolved ARIA and mobile screen-reader issues in section 9 are
counterevidence to treating the posture as a conformance guarantee.

## 6. Forms, validation, submission, and async state

Form controls are form-associated custom elements and participate in standard
form data and constraint validation. The default theme intentionally does not
style validity; custom states let applications choose feedback policy.
[Form controls](https://webawesome.com/docs/form-controls), **Docs, high.**
This preserves native submission once components are upgraded.

Counterevidence is the official SSR statement that form controls cannot be
hoisted from shadow DOM and components are not meant to function without
JavaScript. [SSR goals](https://webawesome.com/docs/ssr/#goals-of-ssr), **Docs,
high.** Loading and remote option workflows are component-specific. There is
no suite-level server-error mapping, pending-form protocol, or repeatable
collection model. **Docs observation, medium-high; unresolved:** exact
pre-upgrade submission behavior by browser.

## 7. Trust and security boundaries

Ordinary string attributes and text slots retain browser/framework escaping,
but several APIs intentionally cross trust boundaries. Select's `getTag()` can
return trusted HTML and warns that unsanitized input causes XSS. Include fetches
and inserts remote HTML; `allow-scripts` is false by default and the docs warn
that trusted content is required even without scripts.
[Select custom tags](https://webawesome.com/docs/components/select/#custom-tags)
and [Include](https://webawesome.com/docs/components/include/), **Docs, high.**

No suite-wide URL allowlist, remote-result sanitizer, file-upload threat model,
generated-ID policy, or CSP nonce provider was found. **Docs observation,
medium. Counterevidence:** risky APIs carry direct warnings; **unresolved:**
Pro File Input, Markdown sanitization, and strict-CSP behavior need dedicated
tests before reuse. Citry must type trusted HTML explicitly and keep URL,
upload, and remote-result policy outside generic attribute forwarding.

## 8. Assets, runtime, SSR, performance, and upgrades

Consumers may autoload components, cherry-pick imports, bundle, or use the
self-contained CDN distribution. A base path locates component assets. Themes
and icons are separately selectable. [Installation](https://webawesome.com/docs/),
**Docs, high.** This is a meaningful no-framework option, but it still requires
client JavaScript and custom-element upgrade.

SSR uses experimental Lit tooling and Declarative Shadow DOM. Its documented
goal is a visual approximation with lower layout shift, not progressive
enhancement. Consumers must select an SSR loader, order hydration support,
wait for definition plus `updateComplete`, add `with-*` hints for conditional
slots, and work around Turbo behavior. [SSR](https://webawesome.com/docs/ssr/),
**Docs, high.** Counterevidence is that native server HTML can still host the
components. Unresolved are normalized payload, CSP, hydration under Citry
morphs, and the Core-to-Pro upgrade path.

Shoelace migration and major Web Awesome changes renamed elements, attributes,
themes, and component composition. [Changelog](https://webawesome.com/docs/resources/changelog)
and [migration](https://webawesome.com/docs/resources/migrating-from-shoelace/),
**Docs, high.** Stable Parts reduce CSS risk within a major but do not remove
custom-element API and SSR migration costs.

## 9. Material shortcomings and complaint evidence

| ID | De-duplicated pattern | Window, status, workflow, workaround, and grade |
|---|---|---|
| WA-1 | Conditional slots and SSR/CSR timing add author-visible hint attributes | Dynamic dialog/drawer/callout/form slots could stay hidden; report opened 2026-05-07 and closed for the 2026-06-30 release. `with-*` was the workaround. [Issue 2369](https://github.com/shoelace-style/webawesome/issues/2369) plus [SSR](https://webawesome.com/docs/ssr/), grade B for defect, A for current architectural cost |
| WA-2 | Slow touch activation can fail in installed iOS PWAs | Unverified user report opened 2026-05-18 and still open at snapshot. It names iOS 26.5, iPhone 12 Mini, standalone PWA mode, and “latest” Web Awesome docs rather than an exact package version. No assignee, milestone, linked development, maintainer confirmation, verified workaround, or later update date was visible. If reproducible, dropdown selection fails with small finger drift and has high impact. [Issue 2409](https://github.com/shoelace-style/webawesome/issues/2409), grade D |
| WA-3 | Native validation integration differs on Safari | Unverified user report opened 2026-06-14 and still open at snapshot. It names macOS Safari 26.5 but no Web Awesome package version. No assignee, milestone, linked development, maintainer response, verified workaround, or later update date was visible. Application focus/scroll handling is only a proposed mitigation. If reproducible, hidden validation feedback has medium-high impact. [Issue 2504](https://github.com/shoelace-style/webawesome/issues/2504), grade D |
| WA-4 | Public Part surfaces are inconsistently named/documented | Unverified user audit opened 2026-07-10 and still open at snapshot. It compares multiple form-control Part names but gives no exact affected package version. No assignee, milestone, linked development, maintainer response, verified workaround, or later update date was visible. Per-component inspection is the provisional mitigation. If verified, customization drift has medium impact. [Issue 2624](https://github.com/shoelace-style/webawesome/issues/2624), grade D |
| WA-5 | ARIA/mobile screen-reader regressions occur despite the accessibility posture | Scroller used a disallowed ARIA attribute and Rating failed with TalkBack; both were fixed by the snapshot. [Issue 2364](https://github.com/shoelace-style/webawesome/issues/2364) and [issue 2205](https://github.com/shoelace-style/webawesome/issues/2205), grade C recurring pattern, retained as resolved history rather than current universal defect |

No prevalence claim is made. WA-1 and WA-5 include maintainer-closed evidence,
which is counterevidence to weak maintenance. WA-2 to WA-4 remained open at
the snapshot but are grade-D test leads only. They cannot support a Phase 5
conclusion unless stronger evidence independently establishes the mechanism.
Free and Pro components share foundations, but no complaint was silently
generalized to unreviewed Pro code.

### Complaint search log

Window: 2024-07-23 through 2026-07-23. Exact tracker queries:

- `repo:shoelace-style/webawesome is:issue created:2024-07-23..2026-07-23 accessibility OR aria OR focus`
- `repo:shoelace-style/webawesome is:issue created:2024-07-23..2026-07-23 slot OR SSR OR hydration`
- `repo:shoelace-style/webawesome is:issue created:2024-07-23..2026-07-23 form OR select OR iOS`
- `repo:shoelace-style/webawesome is:issue created:2024-07-23..2026-07-23 theme OR migration OR Shoelace`
- `repo:shoelace-style/shoelace is:issue created:2024-07-23..2026-07-23 accessibility OR aria OR focus`
- `repo:shoelace-style/shoelace is:issue created:2024-07-23..2026-07-23 form OR select OR slot`

The last Shoelace query returned a tracker/API error during collection. It is
logged as searched but unavailable and did not support a retained finding.

## 10. Citry conclusions

### Adopt or re-derive

- A large, polished default catalog with explicit free/paid boundaries.
- Semantic tokens, component variables, versioned Parts, slots, custom states,
  native forms, and individual module imports.
- Honest accessibility, browser, SSR, and trusted-HTML documentation.
- Product translation that reacts to language/direction without translating
  application content.

### Do not transfer directly

- Shadow-DOM templates as the only behavior implementation or client upgrade
  as a prerequisite for useful server-rendered controls.
- Experimental Lit SSR, `with-*` author hints, or document observers as Citry's
  server/client agreement model.
- Trusted-HTML and remote-include APIs without explicit capability types.
- Core component names whose expected breadth is paywalled without prominent
  package-level signaling.

### Pressure on Citry contracts

Web Awesome pressures Citry to stabilize Parts, states, item values, form
association, and pre/post-open event semantics across styled and headless
implementations. `$component.init()` needs deterministic upgrade and cleanup
under morphing. The `$provide`/`$inject` exploration must test nested locale,
direction, theme, portal root, and CSP values without assuming CSS inheritance
can carry all of them. Citry's styled package should match this level of polish
while its headless package remains usable as meaningful server HTML before
client behavior attaches.
