# Phase 4 complaint register

**Snapshot:** 2026-07-23. **Status:** complete; independent evidence gate
passed 2026-07-23.

This is the cross-library index of retained shortcomings and complaint
patterns. It is not an issue-count leaderboard. Each dossier contains the
exact search log, dates, affected versions, maintainer response, workaround,
counterevidence, and unresolved questions. Combined work units receive one
evidence weight for a shared implementation or complaint ancestry.

Confidence grades follow the frozen protocol:

- **A:** current official docs/source or current reproduction;
- **B:** current maintainer-confirmed report or accepted limitation;
- **C:** recurring independent current reports;
- **D:** one unverified report, which cannot support synthesis alone.

Classifications are current limitation, current defect, recurring friction
with workaround, resolved history, deliberate trade-off, preference, or
unverified claim. Rows that combine grades distinguish the verified mechanism
from a weaker individual report.

## Retained patterns

| ID | Work unit and layer | Classification | Grade | Impact | Normalized pattern | Primary evidence |
|---|---|---|---|---|---|---|
| RA-1 | React Aria | Deliberate trade-off | A | High for Citry's product goal | No built-in theme, visual design, layout, icons, or density system | [Current quick start](https://react-aria.adobe.com/getting-started) |
| RA-2 | React Aria | Recurring friction with partial resolution | A/B | Medium | Compound assembly is powerful but verbose; bespoke integrations can reach for internal collection/context knowledge | [Discussion 6281](https://github.com/adobe/react-spectrum/discussions/6281) |
| RA-3 | React Aria overlays | Current architectural limitation; individual failure unverified | A/D | High for non-standard hosts | Portaled overlays require document-wide visibility and mutation management, complicating native popover and custom hosts | [Issue 7067](https://github.com/adobe/react-spectrum/issues/7067) |
| RA-4 | React Aria Table | Current defect with workaround | B | High in affected keyboard workflow | Keyboard drag-and-drop can fail when table rows outnumber columns | [Issue 9000](https://github.com/adobe/react-spectrum/issues/9000) |
| RA-5 | React Aria portal/focus | Resolved history | B | Medium | Shadow DOM needed explicit portal and focus integration tests and fixes | [Issue 8675](https://github.com/adobe/react-spectrum/issues/8675) |
| BSR-1 | shadcn source delivery | Recurring friction with workaround | A/C | High | Locally edited copied components have diff, overwrite, or manual merge rather than automatic upstream updates | [Discussion 790](https://github.com/shadcn-ui/ui/discussions/790) |
| BSR-2 | shadcn bases | Deliberate trade-off | A | High during migration | Base UI, Radix, and React Aria implementations share catalog names but are not behavior- or API-compatible | [July 2026 changelog](https://ui.shadcn.com/docs/changelog) |
| BSR-3 | Radix/shadcn overlays | Recurring friction with workaround | C | High | Nested portaled controls can conflict over focus, inertness, Escape, pointer suppression, and package versions | [Radix issue 3520](https://github.com/radix-ui/primitives/issues/3520) |
| BSR-4 | Radix to Base UI | Resolved architectural limitation for default base | A/B | High under strict CSP | Radix users lacked a nonce path; Base UI now exposes explicit CSP context and controls | [Radix discussion 3130](https://github.com/radix-ui/primitives/discussions/3130) and [Base CSPProvider](https://base-ui.com/react/utils/csp-provider) |
| BSR-5 | Base UI | Deliberate trade-off | A | High for a styled suite | Visual accessibility and coherent wrappers remain consumer responsibilities | [Accessibility guide](https://base-ui.com/react/overview/accessibility) |
| VU-1 | Vuetify 4 CSS | Resolved history | B | High | CSS-layer ordering changed production output and custom overrides across 4.0 upgrades | [Issue 22752](https://github.com/vuetifyjs/vuetify/issues/22752) |
| VU-2 | Vuetify 3 Select | Resolved history | B | High | Mobile VoiceOver and TalkBack selection did not complete reliably | [Issue 22226](https://github.com/vuetifyjs/vuetify/issues/22226) |
| VU-3 | `@vuetify/v0` polymorphism | Current stable 1.0.0 defect | A | High | Non-button roots lost keyboard/form semantics and could submit forms unexpectedly | [Issue 616](https://github.com/vuetifyjs/0/issues/616) |
| VU-4 | `@vuetify/v0` ARIA | Current stable 1.0.0 defect | A | High | Optional labelled parts could leave dangling ARIA references | [Issue 608](https://github.com/vuetifyjs/0/issues/608) |
| VU-5 | `@vuetify/v0` Snackbar | Current stable 1.0.0 defect | A | Medium-high | Live-region role and synchronous initial content missed urgent or first announcements | [Issue 615](https://github.com/vuetifyjs/0/issues/615) |
| PV-1 | PrimeVue 5 product boundary | Deliberate licensing/source policy | A | High | Current packages are compiled and non-public under eligibility-, seat-, update-, and redistribution-constrained Community/Commercial terms | [v5 migration](https://primevue.dev/migration/v5) and [Community terms](https://primeui.dev/licenses/community) |
| PV-2 | PrimeVue 5 theme loading | Current defect report with workaround | B | High | One failed first theme load can suppress that component's CSS for the session | [Discussion 4835](https://github.com/orgs/primefaces/discussions/4835) |
| PV-3 | PrimeVue 4 SSR lineage | Unresolved historical defect on current closed line | C | High | Generic Vite SSR omitted initial theme styles and could flash until hydration | [Issue 7289](https://github.com/primefaces/primevue/issues/7289) |
| PV-4 | PrimeVue DataTable lineage | Recurring v4 defect; v5 unresolved | C | High | Row grouping and virtualization conflicted on the last public source line | [Issue 4109](https://github.com/primefaces/primevue/issues/4109) |
| PV-5 | PrimeVue DatePicker/forms lineage | Recurring v4 defect; v5 unresolved | C | High | Formatted partial input and submitted form representation could disagree | [Issue 7545](https://github.com/primefaces/primevue/issues/7545) |
| RN-1 | Reka overlay primitives | Resolved history | B | High | A 2.10 regression broke keyboard/focus behavior across DropdownMenu and Dialog/Combobox | [Issue 2756](https://github.com/unovue/reka-ui/issues/2756) |
| RN-2 | Reka Popover | Current defect | A | Medium | A popover without tabbables can self-dismiss in test DOMs because of FocusScope fallback | [Issue 2803](https://github.com/unovue/reka-ui/issues/2803) |
| RN-3 | Reka Toast | Current defect | A | High | Focus sentinels are focusable while ARIA-hidden | [Issue 2776](https://github.com/unovue/reka-ui/issues/2776) |
| RN-4 | Nuxt UI theming | Current defect or undocumented constraint | C | Medium-high | CSS-layer precedence can erase semantic-variable overrides after navigation | [Issue 6172](https://github.com/nuxt/ui/issues/6172) |
| RN-5 | Nuxt UI SelectMenu | Current limitation | A | Medium | Selected-value labels have less composition control than list-item labels | [Issue 4581](https://github.com/nuxt/ui/issues/4581) |
| AD-1 | Ant Select/TreeSelect | Current defect reports | C | High | Virtualized selection widgets can expose wrong or missing screen-reader option semantics | [Issue 58346](https://github.com/ant-design/ant-design/issues/58346) |
| AD-2 | Ant static services | Deliberate limitation | A | High | Static feedback APIs create a separate React root and miss local provider context | [Theme documentation](https://ant.design/docs/react/customize-theme/#consume-design-token) |
| AD-3 | Ant semantic styling | Current defect | B | Medium-high | Customization merge precedence differs across component families | [Issue 58470](https://github.com/ant-design/ant-design/issues/58470) |
| AD-4 | Ant v6 migration | Current upgrade friction | A/B | High | Semantic-DOM cleanup leaves wrapper, type, and override migration gaps | [Migration guide](https://ant.design/docs/react/migration-v6/) and [issue 56035](https://github.com/ant-design/ant-design/issues/56035) |
| AD-5 | Ant Pagination | Unverified claim/test lead | D | High if reproduced | One report identifies naming, role, and state problems across pagination controls | [Issue 58072](https://github.com/ant-design/ant-design/issues/58072) |
| M-1 | Mantine Tooltip | Current limitation | A | Medium-high | Tooltip content is not hoverable, limiting dismissible or hoverable content patterns | [Issue 9072](https://github.com/mantinedev/mantine/issues/9072) |
| M-2 | Mantine field errors | Current limitation | A | High | Conditionally mounted error nodes weaken reliable live-region announcements | [Issue 8932](https://github.com/mantinedev/mantine/issues/8932) |
| M-3 | Mantine overlays | Recurring friction with workaround | C | High | Portals, focus traps, scrolling, and mobile keyboards interact poorly in iOS collection overlays | [Issue 8928](https://github.com/mantinedev/mantine/issues/8928) |
| M-4 | Mantine color scheme | Web-platform trade-off | A | Medium | First-visit system color preference is unavailable to ordinary SSR and can cause hydration branching errors | [Color-scheme docs](https://mantine.dev/theming/color-schemes/) |
| M-5 | Mantine CSS delivery | Deliberate trade-off | A | Medium | Aggregate CSS imports include a whole selected package; per-component imports shift ordering work to applications | [Styles docs](https://mantine.dev/styles/mantine-styles/) |
| CZA-1 | Chakra SSR/providers | Current integration friction | A/D | High | Emotion, color mode, hydration, and bundler choice require framework-specific setup | [Next.js guide](https://chakra-ui.com/docs/get-started/frameworks/next-app) |
| CZA-2 | Chakra v3 migration | Deliberate major-version cost | A | High | Compound APIs, providers, snippets, and theme contracts changed together | [Migration guide](https://chakra-ui.com/docs/get-started/migration) |
| CZA-3 | Chakra recipes | Resolved-history performance pattern | B/C | High in dense views | Runtime recipe resolution has produced repeated large-list render costs | [Issue 10878](https://github.com/chakra-ui/chakra-ui/issues/10878) |
| CZA-4 | Ark/Zag Field | Maintainer-triaged report | B | High | Automatic label wiring can point hidden controls at a missing label | [Issue 3824](https://github.com/chakra-ui/ark/issues/3824) |
| CZA-5 | Ark/Zag Combobox | Recurring distributed-state risk | C | High | Visible input, portal, machine, collection, and hidden control can disagree across AT and autofill | [Zag issue 2936](https://github.com/chakra-ui/zag/issues/2936) |
| BS-1 | Bootstrap theming | Deliberate limitation | B | Medium-high | Some runtime CSS-variable changes do not retheme component states; Sass or targeted overrides remain necessary | [Issue 41652](https://github.com/twbs/bootstrap/issues/41652) |
| BS-2 | Bootstrap Sass | Current upgrade friction | B | Medium | The supported Sass customization path emits upstream deprecation warnings | [Issue 40962](https://github.com/twbs/bootstrap/issues/40962) |
| BS-3 | Bootstrap forms | Current limitation | A | High | Custom client validation feedback is not reliably accessible | [Validation docs](https://getbootstrap.com/docs/5.3/forms/validation/) |
| BS-4 | Bootstrap RTL | Current limitation | A | Medium | RTL is a separate experimental build rather than one direction-aware runtime artifact | [RTL docs](https://getbootstrap.com/docs/5.3/getting-started/rtl/) |
| BS-5 | Bootstrap responsive tables | Current limitation | A | Medium | Overflow wrappers can clip dropdowns and other overlays | [Responsive-table docs](https://getbootstrap.com/docs/5.3/content/tables/#responsive-tables) |
| WA-1 | Web Awesome slots/SSR | Resolved defect; current architecture cost | A/B | Medium-high | Conditional slots and upgrade timing require author-visible hint attributes in SSR output | [Issue 2369](https://github.com/shoelace-style/webawesome/issues/2369) |
| WA-2 | Web Awesome dropdown | Unverified current report; test lead only | D | High if reproduced | Small finger drift may prevent selection in installed iOS PWAs | [Issue 2409](https://github.com/shoelace-style/webawesome/issues/2409) |
| WA-3 | Web Awesome validation | Unverified current report; test lead only | D | Medium-high if reproduced | Safari validity reporting may not scroll an invalid custom control into view | [Issue 2504](https://github.com/shoelace-style/webawesome/issues/2504) |
| WA-4 | Web Awesome CSS Parts | Unverified current report; test lead only | D | Medium if verified | Public Part names and documentation may differ among related form controls | [Issue 2624](https://github.com/shoelace-style/webawesome/issues/2624) |
| WA-5 | Web Awesome accessibility | Resolved-history pattern | C | High | ARIA and mobile screen-reader regressions reached current components despite the accessibility posture | [Issue 2364](https://github.com/shoelace-style/webawesome/issues/2364) |
| PCP-1 | Cotton UI parts | Resolved friction; current surface unresolved | B | Medium | One class override could not project consistently to multiple internal elements | [Issue 13](https://github.com/wrabit/django-cotton-ui/issues/13) |
| PCP-2 | Cotton attributes | Resolved security defect | B | High | Dynamic attributes had an injection path fixed in Cotton 2.7.2 | [Issue 361](https://github.com/wrabit/django-cotton/issues/361) |
| PCP-3 | Cotton context | Resolved performance defect | B | High in dense pages | Context processors were rerun per component before request-scoped capture was restored | [Issue 269](https://github.com/wrabit/django-cotton/issues/269) |
| PCP-4 | django-components identity | Current roadmap risk | B | High for library authors | Registered-name and registry publishing identity is under redesign | [Issue 1195](https://github.com/django-components/django-components/issues/1195) |
| PCP-5 | django-components assets | Current limitation | B | High for distribution | Static dependency export, inlining, public IDs, and post-processing remain incomplete | [Issue 836](https://github.com/django-components/django-components/issues/836) |
| DF-1 | django-formset submission | Current architectural limitation | A/D | High | Its JSON/fetch controller does not naturally reuse traditional request/response views | [Current docs](https://django-formset.fly.dev/django-formset/) and [issue 201](https://github.com/jrief/django-formset/issues/201) |
| DF-2 | django-formset validation | Preference/search lead | D | Medium-high if reproduced | Interactive validation feedback cannot be fully disabled for every reported workflow | [Issue 205](https://github.com/jrief/django-formset/issues/205) |
| DF-3 | django-formset activation | Current limitation | A | High | Dynamically inserted forms may miss widget activation | [Issue 270](https://github.com/jrief/django-formset/issues/270) |
| DF-4 | django-formset collections | Current defect report | B | High | Nested collection paths can break dialog actions | [Issue 260](https://github.com/jrief/django-formset/issues/260) |
| DF-5 | django-formset upload | Current source-backed limitation | A | High | One file-selection path uploads before the client MIME precheck, though server validation still rejects it | [Issue 251](https://github.com/jrief/django-formset/issues/251) |

## Excluded signals

- Raw open-issue counts, star-normalized counts, reactions, and search-result
  volume are not quality evidence.
- A fixed issue is retained only when it teaches an architectural or testing
  lesson; it is not represented as a current defect.
- A documentation claim about accessibility is the project's published
  posture, not independent proof of conformance.
- A missing complaint is not evidence of user satisfaction. Search shortfalls
  stay visible in the corresponding dossier.
