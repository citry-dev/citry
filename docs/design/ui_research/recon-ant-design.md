# Phase 4 dossier: Ant Design

**Snapshot:** 2026-07-23. **Studied line:** `antd` 6.5.1. **Evidence
scope:** current official documentation, the 6.5.1 tagged source tree, release
and license metadata, and issue-tracker reports created in the Phase 3
complaint window. No local runtime reproduction was performed.

Evidence labels are **Docs**, **Source/release**, **Maintainer report**, **User
report**, and **Inference**. Confidence grades follow the
[Phase 3 protocol](candidate-map.md#52-complaint-sample-and-confidence). Every
material limitation below names counterevidence or an unresolved boundary;
absence from this survey is not evidence of absence.

## 1. Product snapshot

Ant Design is a styled, general-purpose React suite. Version 6.5.1 is MIT
licensed, requires React and React DOM 18 or newer, and depends on a broad
family of `@rc-component/*` behavior packages, Ant's CSS-in-JS and icon
packages, and utilities including Day.js. The exact dependency and license
metadata is frozen in the
[6.5.1 package manifest](https://github.com/ant-design/ant-design/blob/6.5.1/package.json).
**Source/release, high confidence. Counterevidence:** individual dependency
versions may move after this tag, but cannot change this snapshot.
**Unresolved:** a complete transitive license and payload audit was not run.

The package has no paid component boundary in the reviewed catalog. Ant
Design Pro and ecosystem products add application scaffolding and specialist
features, but the core component source remains MIT. The repository and
[6.5.1 source tree](https://github.com/ant-design/ant-design/tree/6.5.1/components)
show active development and a broad test surface. **Source/release, high
confidence. Counterevidence:** repository activity does not prove support
quality for every family. **Unresolved:** no maintainer staffing or support
SLA was found.

Ant Design is an especially relevant styled-suite reference because it offers
usable defaults, a wide catalog, ambient configuration, per-component tokens,
and complex data/form controls in one product. It is not a headless library:
semantic part styling and component render hooks do not amount to a stable,
style-free behavior package. **Docs plus inference, high confidence, based on
the [theme contract](https://ant.design/docs/react/customize-theme/) and
[component catalog](https://ant.design/components/overview/).
Counterevidence:** many components accept `classNames`, `styles`, slots, and
custom render functions. **Unresolved:** whether a small subset can be made
reliably unstyled without private CSS was not reproduced.

## 2. Normalized full inventory

The inventory normalizes public families from the current catalog and tagged
component tree. Internal style, version, row/column alias, and compatibility
directories are not counted as separate products. **Docs and source, high
confidence:** [catalog](https://ant.design/components/overview/) and
[tagged tree](https://github.com/ant-design/ant-design/tree/6.5.1/components).
**Counterevidence:** the docs sometimes present a subcomponent, such as
`FloatButton.BackTop`, where source history retains a separate directory.
**Unresolved:** experimental status and exact export aliases should be checked
before quantitative heatmap scoring.

| Citry category | Ant Design families |
|---|---|
| Foundations | ConfigProvider, App, theme algorithms and tokens, typography, icon integration, locale packs |
| Layout | Layout, Grid, Row, Col, Flex, Space, Splitter, Divider, Masonry |
| Actions | Button, FloatButton, BackTop, Segmented, link and icon-button forms |
| Forms | Form, Input, TextArea, Search, Password, OTP, InputNumber, Checkbox, Radio, Switch, Slider, Select, AutoComplete, Cascader, TreeSelect, Mentions, Rate, ColorPicker, DatePicker, TimePicker, Upload, Transfer |
| Navigation | Anchor, Breadcrumb, Dropdown, Menu, Pagination, Steps, Tabs, Tour |
| Feedback | Alert, Message, Notification, Progress, Result, Skeleton, Spin |
| Overlays | Modal, Drawer, Popconfirm, Popover, Tooltip, Dropdown, ColorPicker and picker popups |
| Data display | Avatar, Badge, BorderBeam, Calendar, Card, Carousel, Collapse, Descriptions, Empty, Image, List, QRCode, Statistic, Table, Tag, Timeline, Tree, Typography, Watermark |
| Utilities | Affix, ConfigProvider, App, locale support, theme, responsive grid, portal-container configuration |
| Specialist or adjacent | Calendar/date and color controls are deep general-suite features; QRCode and Watermark are distinctive utilities. Charts, maps, rich text, domain grids, and media editors are not core families. |

Breadth is a genuine product advantage, but several entries share lower-level
`rc-*` dependencies and overlay/collection machinery. Component count must
not be read as independent behavior implementations. **Source/inference,
high confidence from the
[package dependencies](https://github.com/ant-design/ant-design/blob/6.5.1/package.json).
Counterevidence:** shared infrastructure can improve consistency as well as
create correlated defects. **Unresolved:** exact shared dependency ownership
per component was not mapped.

## 3. Architecture, delivery, and composition

Ant Design is an installed React runtime, not source-copy distribution. Its
components render HTML through React, use React context for configuration, and
use CSS variables with runtime style infrastructure. The 6.0.0 generation makes CSS
variables the default and documents a zero-runtime static-style extraction
option, but zero-runtime styling does not remove React or turn the library
into server-rendered Citry templates. [6.0.0 migration](https://ant.design/docs/react/migration-v6/)
and [theme customization](https://ant.design/docs/react/customize-theme/),
**Docs, high confidence. Counterevidence:** SSR and extracted CSS can reduce
runtime style work. **Unresolved:** no representative bundle or SSR benchmark
was run.

Composition has four recurring shapes:

1. Conventional props and callbacks for compact components such as Button.
2. Compound or nested data APIs for Menu, Tabs, Form, Table, and descriptions.
3. Controlled/uncontrolled state pairs such as `value`/`defaultValue` and
   change callbacks.
4. Named semantic DOM parts exposed through `classNames` and `styles`, plus
   component-specific render callbacks.

The public Select contract illustrates value identity, search, option render,
popup render, semantic part classes/styles, controlled open state, virtual
scroll, loading, and multiple-selection modes.
[Select](https://ant.design/components/select/), **Docs, high confidence.
Counterevidence:** APIs vary across old and new component generations.
**Unresolved:** there is no suite-wide reason-bearing/cancelable event model.

Portals and detached React roots are central to overlays and feedback. Normal
overlay descendants can obtain provider values, while static `message`,
`notification`, and `Modal.*` calls create roots outside the caller's context.
The official theme guide recommends hook APIs with a `contextHolder` or the
`App` wrapper. [Theme static-method warning](https://ant.design/docs/react/customize-theme/#consume-design-token)
and [ConfigProvider](https://ant.design/components/config-provider/), **Docs,
high confidence. Counterevidence:** `holderRender` and global configuration
cover some static calls. **Unresolved:** nested portals, shadow roots, and
cross-document targets were not reproduced.

## 4. Customization ladder and styled/headless implications

| Level | Ant Design mechanism | Assessment for Citry |
|---|---|---|
| Global tokens | Seed, map, and alias design tokens; light, dark, compact, and composable algorithms | Strong model for a coherent default and derived semantic tokens |
| Theme variants | `ConfigProvider.theme`, algorithms, CSS-variable prefixes, hashed-class control | Powerful, but provider and runtime-style complexity must not transfer automatically |
| Component variants | Component tokens, sizes, status, semantic colors, variants, component defaults | Strong breadth; vocabulary consistency varies by family |
| Per instance | Props, ordinary DOM attributes where supported, `className`, `style`, semantic `classNames` and `styles` | Good escape hatches; forwarding rules are not uniform enough to assume |
| Parts and structure | Semantic DOM keys, item/column render callbacks, popup render, icon slots | More control than a closed widget, less than a documented headless part tree |
| Behavior | Controlled state, callbacks, ConfigProvider defaults, virtual-scroll switches | Extensive, but component-specific rather than one state-machine contract |
| Full ownership | Open source fork or wrapper | Possible, but not the intended customization path |

Sources: [theme customization](https://ant.design/docs/react/customize-theme/),
[ConfigProvider](https://ant.design/components/config-provider/), and
[Select semantic DOM](https://ant.design/components/select/). **Docs, high
confidence. Counterevidence:** some older families do not expose equally
complete semantic parts. **Unresolved:** a complete family-by-family part and
attribute-forwarding matrix is not published.

The most transferable idea is the token pipeline: small seed changes derive a
coherent system while component tokens permit local refinement. Citry should
also keep stable semantic part names. Citry should not present “remove Ant's
CSS” as a headless equivalent. A real Citry headless surface must guarantee
semantic structure, behavior, and state attributes without requiring authors
to override a styled implementation. **Inference, high confidence from the
documented styling architecture. Counterevidence:** Ant's CSS variables and
semantic parts can support extensive visual replacement. **Unresolved:** how
much DOM equality styled and headless Citry should promise remains Phase 5
work.

## 5. Frozen comparison slice

| Probe | Current Ant Design contract and finding | Evidence and qualification |
|---|---|---|
| Button | Styled variants, sizes, loading, danger, icon placement, link-like forms, and grouping are integrated. DOM-level replacement is not the primary API. | [Button](https://ant.design/components/button/), Docs, high. Counterevidence: `href`, icons, classes, and styles cover common composition. Unresolved: exact press normalization across pointer and keyboard was not reproduced. |
| Field and Input | Form.Item carries label, help, validation status, dependencies, layout, and value plumbing; Input adds variants, affixes, clear, count, and status. | [Form](https://ant.design/components/form/) and [Input](https://ant.design/components/input/), Docs, high. Counterevidence: the store-driven Form abstraction is optional. Unresolved: native no-JS submission parity is not a documented primary workflow. |
| Dialog | Modal integrates portal rendering, focus, mask, async close/loading, and static plus hook APIs. | [Modal](https://ant.design/components/modal/), Docs, high. Counterevidence: hook APIs repair provider context. Unresolved: focus restoration through Citry morphs is not transferable evidence. |
| Combobox or searchable Select | Select provides search, custom filtering, async loading patterns, multiple/tags modes, virtualization, option identity, popup customization, and controlled state. | [Select](https://ant.design/components/select/), Docs, high. Counterevidence: `virtual={false}` simplifies DOM exposure. Unresolved: current screen-reader reports below prevent treating documented ARIA as verified conformance. |
| Tabs | Item data, active identity, positioning, editable cards, overflow navigation, indicator, and semantic parts are integrated. | [Tabs](https://ant.design/components/tabs/), Docs, high. Counterevidence: custom tab bars expose additional structure. Unresolved: RTL and deletion focus behavior were not reproduced. |
| Table or DataTable | Table includes columns, sorting, filters, selection, expansion, fixed and virtual layouts, editable/custom cells, tree data, and responsive behavior. | [Table](https://ant.design/components/table/), Docs, high. Counterevidence: virtual and fixed modes add constraints. Unresolved: performance and assistive-technology behavior for dense combinations require a prototype. |
| Complex form/collection workflow | Form.List, dependencies, dynamic controls, validation, Upload, Transfer, editable tables, and server/API submission patterns cover substantial application work. | [Form](https://ant.design/components/form/) and [Upload](https://ant.design/components/upload/), Docs, high. Counterevidence: uploads still require application transport and trust policy. Unresolved: graceful no-JS behavior is not promised. |
| Provider/ambient context | ConfigProvider carries theme, direction, locale, popup container, component defaults, size, disabled state, CSP nonce, and rendering policy. | [ConfigProvider](https://ant.design/components/config-provider/), Docs, high. Counterevidence: static APIs escape ordinary context. Unresolved: reactive nested-provider and portal matrices were not independently tested. |

## 6. Provider and ambient-context audit

| Question | Finding |
|---|---|
| Values carried | Theme/tokens, direction, locale, component defaults, global size/disabled state, popup target, CSP nonce, icon prefix, empty rendering, and some virtualization policy. |
| Nesting and shadowing | React context supports nested providers and descendant overrides; theme objects can inherit unless explicitly disabled. Exact precedence across every component-level default is not uniform. |
| Defaults and overrides | Library defaults, ConfigProvider values, component props, semantic styles, and inline styles form a multi-level cascade. Issue AD-3 below shows inconsistent style merge order. |
| Reactive updates | Provider prop changes flow through React rendering. CSS variables can reduce style recalculation, but update cost was not benchmarked. |
| Server/client agreement | SSR is supported in the React ecosystem; CSS-variable and extraction modes address style delivery. This does not prove agreement under Citry fragments or Alpine initialization. |
| Portals | Normal React portals preserve logical context, but static APIs create separate roots and require hooks, `App`, `holderRender`, or global configuration. DOM direction and popup-container effects still need explicit verification. |
| Lifecycle and cleanup | React owns effect and portal cleanup. Citry's morph/remove/reconnect lifecycle needs its own contract and tests. |
| Diagnostics | `ConfigProvider.useConfig` exposes selected ambient values. No general missing-provider, cross-root, or provider-cycle diagnostic was found. |

Evidence: [ConfigProvider](https://ant.design/components/config-provider/) and
[theme customization](https://ant.design/docs/react/customize-theme/),
**Docs, high for the published API; medium for lifecycle implications.
Counterevidence:** React context behavior is mature, and `App` deliberately
addresses static feedback. **Unresolved:** provider shadowing, teleport targets,
and server/client snapshots need direct Phase 5 prototypes.

This provider is useful pressure on Citry's prospective client-side
provide/inject design. Theme, direction, density, generated-ID roots, portal
policy, and future locale are descendant concerns; static feedback also shows
why a global escape hatch cannot silently pretend to have local context.
Whether Citry expresses this through `$component.init()` methods or
`$provide`/`$inject` magics remains open. **Inference, high confidence.
Counterevidence:** CSS custom-property inheritance can carry many theme values
without JavaScript context. **Unresolved:** the minimum reactive context set
must be prototyped rather than copied from React.

## 7. Accessibility and international interaction

Ant components publish keyboard, semantic DOM, RTL, locale, and accessibility
APIs, but the reviewed official material does not provide a component-by-
component browser, keyboard, and screen-reader conformance matrix. The open
Select, TreeSelect, and Pagination reports in section 10 are material
counterevidence to broad accessibility assumptions. [Select](https://ant.design/components/select/),
[ConfigProvider](https://ant.design/components/config-provider/), and
[issue 58072](https://github.com/ant-design/ant-design/issues/58072), **Docs
and user reports, medium confidence for actual quality. Unresolved:** manual
NVDA, VoiceOver, keyboard, zoom, and forced-colors tests are required.

RTL and packaged locale data are mature product features. Direction can be
provided globally, and many calendar, pagination, and empty-state strings have
locale packs. This is useful breadth evidence, not a recommendation to freeze
Citry translation keys now. [ConfigProvider](https://ant.design/components/config-provider/),
**Docs, high confidence. Counterevidence:** third-party date-library locale
configuration may also be necessary. Unresolved:** mixed-direction nesting and
logical-property completeness were not audited.

Reduced motion, touch target quality, IME behavior, mobile virtual keyboards,
and forced colors are not stated as suite-level guarantees in the sources
reviewed. **Unresolved, low confidence due to documentation absence.** Ant's
responsive and mobile behavior examples are counterevidence to any claim that
these cases are wholly ignored, but examples do not establish coverage.

## 8. Forms, async behavior, and content trust

Ant Form is primarily a controlled React form store layered over real input
elements. It supports field registration, validation rules, dependencies,
dynamic lists, feedback, initial values, reset, submit callbacks, and server
errors through application state. [Form](https://ant.design/components/form/),
**Docs, high confidence. Counterevidence:** inputs can be used without Form and
retain native element behavior. Unresolved:** a systematic matrix for native
submission, browser validation, disabled fields, reset, autofill, and no-JS
fallback was not found.

Loading and error states exist across Button, Select, Table, Upload, Modal,
Result, Alert, Spin, Message, and Notification, but async request ownership is
application code. Search result freshness, cancellation, retry, and stale
response rejection are not one suite-wide contract. [Select](https://ant.design/components/select/)
and [Upload](https://ant.design/components/upload/), **Docs plus inference,
high confidence. Counterevidence:** individual demos show debouncing and custom
requests. Unresolved:** whether examples consistently reject stale results was
not audited.

React escapes ordinary text children. Ant accepts URLs, render callbacks,
uploaded files, image sources, QR data, arbitrary option content, and ordinary
DOM attributes in component-specific places; no general sanitizer or safe-URL
policy was found. Upload defines selection and transport hooks but the
application must enforce filename, MIME, size, preview, authorization, and
server validation. [Upload](https://ant.design/components/upload/) and
[QRCode](https://ant.design/components/qr-code/), **Docs plus inference,
medium-high confidence. Counterevidence:** explicit render APIs are necessary
for trusted rich UI. Unresolved:** protocol filtering and raw-HTML escape
hatches need source-level security audit.

Generated IDs and ARIA relationships are runtime-owned by React and component
internals. Attribute forwarding varies by family and semantic part. This is a
warning for Citry to define typed root and part attributes rather than a raw
JavaScript string channel. **Inference, medium confidence from public APIs.
Counterevidence:** semantic `classNames`/`styles` improve part targeting.
Unresolved:** full attribute routing was not inventoried.

## 9. Assets, CSP, payload, SSR, and upgrades

- Ant ships JavaScript, CSS/runtime-style infrastructure, and an icon package;
  it does not require application fonts. Icon inclusion and tree-shaking still
  need a measured build. [Package manifest](https://github.com/ant-design/ant-design/blob/6.5.1/package.json),
  **Source, high for dependencies; unresolved for payload.**
- CSS-in-JS supports CSP nonces through ConfigProvider and version 6 documents
  CSS variables, hashed styles, static extraction, and zero-runtime styling.
  [ConfigProvider CSP](https://ant.design/components/config-provider/) and
  [theme customization](https://ant.design/docs/react/customize-theme/),
  **Docs, high. Counterevidence:** inline positioning styles and application
  code may still affect strict CSP. Unresolved: a strict policy was not run.**
- SSR belongs to React rendering and style extraction. The result still needs
  hydration and React lifecycle; it is not a no-JavaScript or Citry-native
  delivery model. **Inference, high. Counterevidence:** server HTML can render
  initial visuals. Unresolved: hydration mismatch rate was not measured.**
- The 6.0.0 generation raises the React floor, moves fully to CSS variables, removes
  deprecated APIs, updates semantic DOM, and provides migration guidance and
  tooling. [Migration guide](https://ant.design/docs/react/migration-v6/),
  **Docs, high. Counterevidence:** a documented checklist and codemods reduce
  work. Unresolved: cost varies with wrapper depth and deprecated usage.**

The library is unsuitable for direct reuse because Citry forbids a second
component runtime and requires prebuilt wheel assets with no Node build for
consumers. Its token model, semantic part vocabulary, breadth, and migration
discipline remain valuable reference mechanisms. **Inference, high confidence
from the Citry charter and Ant delivery contract.**

## 10. Material shortcomings and complaint register

The window is 2024-07-23 through 2026-07-23. Reports are de-duplicated by
underlying mechanism. Resolved history is not scored as a current defect.

| ID | Pattern | Window evidence, affected workflow, response, workaround, and status | Classification |
|---|---|---|---|
| AD-1 | Virtualized selection widgets can expose incorrect or missing screen-reader option semantics | [Issue 58346](https://github.com/ant-design/ant-design/issues/58346), opened 2026-06-12 against 6.4.4 and open at snapshot, reports wrong announced option position in the official Select demo. [Issue 56070](https://github.com/ant-design/ant-design/issues/56070), opened 2025-12-04 against 5.27.6 and open/inactive, reports TreeSelect option name/role/state absent with NVDA; the reporter says disabling virtualization did not repair it. A linked lower-level Select issue exists. Workaround is not verified. Impact is high for non-visual selection. | Recurring current defect reports, grade C. Counterevidence: reports span different major versions and components, and no current 6.5.1 reproduction was run. Unresolved: exact fixed/affected versions and assistive-technology matrix. |
| AD-2 | Static feedback APIs do not inherit local provider context or popup targets | [Official theme documentation](https://ant.design/docs/react/customize-theme/#consume-design-token) states that static methods create a separate React root. [Issue 54870](https://github.com/ant-design/ant-design/issues/54870), opened 2025-09-04 against 4.24.16 and closed, is one user manifestation. Maintained workarounds are hook APIs plus `contextHolder`, `App`, or `holderRender`. Theme, locale, prefix, and popup placement can otherwise surprise callers. | Current deliberate architectural limitation, grade A. Counterevidence: first-party workarounds are documented. Unresolved: which static methods honor which global overrides in 6.5.1. |
| AD-3 | Customization precedence is not consistent across component families | [Issue 58470](https://github.com/ant-design/ant-design/issues/58470), opened 2026-06-23 and open with an assignee at snapshot, shows differing merge order among ConfigProvider component style, `styles.root`, and style props. A linked pull request is in progress. Workaround is component-specific ordering or higher-specificity styling, both fragile. | Maintainer-tracked current bug, grade B. Counterevidence: the semantic styles API is a substantial improvement over private descendant selectors. Unresolved: merge-order fix version and whether all families receive one rule. |
| AD-4 | Major-version semantic-DOM cleanup makes wrapper and override upgrades expensive | [6.0.0 migration](https://ant.design/docs/react/migration-v6/) deliberately removes deprecated APIs and changes semantic parts. [Issue 56035](https://github.com/ant-design/ant-design/issues/56035), opened 2025-12-02 and still open/confirmed as a bug at snapshot, reports a Drawer `styles.content` path missing from types and migration guidance. Workarounds depend on replacement part APIs. | Current upgrade friction with one confirmed documentation/API gap, grade A for planned breaking scope and B for the gap. Counterevidence: migration checklist and tooling exist. Unresolved: prevalence across real applications. |
| AD-5 | Accessibility remediation remains uneven outside the headline controls | [Issue 58072](https://github.com/ant-design/ant-design/issues/58072), opened 2026-05-20 and open, identifies naming/role/state problems across previous/next, ellipsis, size changer, and quick-jumper Pagination controls. It complements AD-1 but affects a distinct navigation widget. No verified workaround or released fix was found. | Current single report plus official demo reference, grade D alone; retained as a high-impact test target, not a suite-wide conclusion. Counterevidence: the issue is labeled partly as a feature request. Unresolved: reproduction and fix status in 6.5.1. |

### Complaint search log

Exact GitHub issue queries used for the required layer were:

- `repo:ant-design/ant-design is:issue created:>=2024-07-23 accessibility aria`
- `repo:ant-design/ant-design is:issue created:>=2024-07-23 cssinjs performance SSR`
- `repo:ant-design/ant-design is:issue created:>=2024-07-23 ConfigProvider context modal message`
- `repo:ant-design/ant-design is:issue created:>=2024-07-23 v6 migration breaking`
- `repo:ant-design/ant-design is:issue created:>=2024-07-23 select keyboard`

The issue pages linked in AD-1 through AD-5 were then opened directly and
checked for creation date, reported version, status, maintainer classification,
and workarounds. No credible current broad security, CSP, or payload complaint
survived this sample. That is an evidence gap, not a positive finding.

## 11. Citry conclusions

### Adopt or re-derive

- A seed-to-semantic-to-component token pipeline with light, dark, compact,
  density, and brand derivation.
- Stable semantic part names and documented style precedence across global,
  component, instance, and state layers.
- A first-party suite broad enough for ordinary application work, including
  strong Table, Form, feedback, and navigation stories.
- An explicit application-level provider for theme, direction, density,
  portal policy, and future locale concerns, with nested override tests.
- Hook-like locally rooted feedback APIs rather than context-blind global
  static calls.
- Migration checklists and mechanical assistance when accessibility markup or
  public parts must change.

### Do not transfer directly

- React, `rc-*`, CSS-in-JS, or detached React roots as a second client runtime.
- A styled implementation whose CSS must be removed to simulate headless use.
- Component-specific style precedence or undocumented attribute routing.
- Store-first forms that obscure native submission, browser reset, autofill,
  and progressive enhancement.
- Virtualization as an invisible default without a verified accessibility and
  performance decision per collection size.

### Pressure on Citry's public contracts

Ant Design pressures Citry to define nested ambient values, portal target
ownership, logical context across teleports, reactive theme changes, and
diagnostics when a static/global action lacks local context. It also pressures
the template API to support named semantic parts, stable item identity,
reason-bearing state changes, and a documented style cascade shared by styled
and headless exports.

The client context prototype must compare `provide()`/`inject()` methods inside
`$component.init()` with `$provide`/`$inject` magics. Tests should cover nested
theme/direction overrides, removal and reparenting, fragments, morphing,
portaled dialogs, globally triggered toasts, and missing-provider diagnostics.
CSS custom properties should carry visual tokens where inheritance is enough;
JavaScript context should be reserved for behavioral values. **Inference, high
confidence from AD-2 and the provider audit. Counterevidence:** a purely CSS
theme can avoid much client context. Unresolved: the minimum public contract
and whether portal state belongs to core Citry or `citry-ui`.

The highest-risk transfer questions for Phase 5 are native form preservation
under a rich Form API, accessible non-virtual and virtual collection modes,
stable semantic part versioning, and whether server-driven Citry Events can
express loading, cancellation, validation, and stale-result rejection without
copying React store architecture.
