# Citry UI component previews and public examples

**Status: shared contract validated through Tabs. Implementation increments 1
through 5 completed 2026-08-05. Tabs human polish and live testing remain.**
This document defines the reusable public-preview and example contract for
Citry UI component pages. Each component specification owns its concrete
example catalog and feature coverage.

## 1. Reader outcome and reference pattern

A component page must let the reader see and operate the component before it
asks them to open an editor or study a large API table. Prose and reference
tables cannot communicate visual concepts such as variants, density, layout,
feedback, motion, and interactive transitions on their own.

Vuetify's component pages use a useful progression:

1. a rendered usage example establishes the component's appearance and basic
   behavior;
2. the usage example exposes a small configuration panel where that helps;
3. visually meaningful inputs and behaviors receive focused headings and
   rendered examples; and
4. source stays available without displacing the result.

The current Vuetify Tabs source page, for example, has separate examples for
alignment, growth, fixed sizing, direction, pagination, mobile presentation,
dynamic Tabs, and custom slots. Its configurable usage example lets the reader
change direction, colors, growth, and indicator behavior while it derives
matching source. See the
[Tabs page](https://vuetifyjs.com/en/components/tabs/), its
[authored page source](https://github.com/vuetifyjs/vuetify/blob/master/packages/docs/src/pages/en/components/tabs.md),
and the
[usage configurator](https://github.com/vuetifyjs/vuetify/blob/master/packages/docs/src/examples/v-tabs/usage.vue).

Citry UI should adopt that result-first learning model without copying
Vuetify's Vue API, Material-specific features, or documentation components.

## 2. One example, three presentations

A public component example has one component-owned Python module and three
presentations:

- **Preview:** an always-visible rendered result. It is interactive as soon as
  its preview document loads and never requires the reader to open an editor.
- **Source:** a collapsed, copyable view of the same Python module.
- **Live editor:** an opt-in handoff to the existing live-code or Playground
  runtime for experimentation.

The preview teaches appearance and behavior. The source teaches composition.
The editor is an optional workbench, not the price of seeing the component.
Playwright remains the browser verification tool; the docs preview does not
become a journey runner.

The docs site now provides this component-owned directive:

```citry-html
<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctabs/snippets/at_a_glance.py"
  title="Tabs at a glance"
/>
```

Its public behavior is:

- render the preview before the source controls;
- provide **Show code**, **Copy**, and **Try live** actions;
- collapse source by default for every example;
- render preview content one type step below the surrounding docs prose;
- use the docs code-block surface behind rendered content and follow the
  explicit or system light/dark theme without relaxing the iframe sandbox;
- give every iframe a specific accessible title;
- lazy-load examples below the first viewport;
- resize the iframe to its content instead of introducing nested vertical
  scrolling; and
- keep useful prose and source in the Markdown or LLM projection when the
  interactive preview is unavailable.

The preview is built from the repository's `citry_ui` source and serialized
with Citry's document dependencies. That gives the static docs a real
interactive component without loading Python in the reader's browser. The
existing browser Python runtime is still used when the reader chooses
**Try live**. Each example module exposes one explicit preview object and ends
with that same object so the build renderer and live editor execute the same
code.

Preview pages live at an internal route below the component page, for example
`/ui-library/components/tabs/_previews/variants/`. They are supporting
documents, not navigation entries or `/examples/` recipes. Source stays beside
the component family under `snippets/` and stays out of the wheel.

The module exposes its rendered value through the explicit name `preview` and
ends with that same expression so server rendering and the live editor share
one execution contract:

```python
preview = NightSkyGuide()

preview
```

The preview value must use Citry's default instance. This is the same runtime
used by browser snippets and lets the docs builder compose the preview into its
standalone document without a second registration context.

The filename derives the private route segment, converting underscores to
hyphens. The catalog maps the owning `api.md` source to the public component
slug, so neither the module nor the directive repeats a route. Source
disclosures are collapsed initially so the result remains the visual focus.

Increment 1 built the preview document, source disclosure, copyable highlighted
code, private route, iframe resizing, and Markdown/LLM projection. Increment 2
converted the first composed Tabs module and connected the same source to the
existing lazy inline editor. The local authoring server exposes **Try live**
through its workspace `citry-ui` wheel. Deployed docs keep the build-rendered
result and source until a published `citry-ui` wheel joins the pinned browser
runtime.

## 3. Demo controls

Controls belong to the example when they clarify a configuration or behavior.
They render in an open, collapsible section below the demo header and above the
sandboxed preview. This placement identifies them as documentation tooling,
not component content. Each component family gets one deliberate configurator
where useful; focused examples can use no controls or only the ones that matter.

The snippet declares `preview_controls` explicitly. The docs do not infer a
generic control panel from component metadata. The current schema supports
selects and checkboxes, validates every option and default during the build,
and sends current values to the matching preview through `postMessage`. The
preview opts in by handling the `citry-ui-preview-controls` Window event.

Controls may use any documented public surface, including client props and CSS
variables. Match the control to the value:

- select or radio group for an enum;
- checkbox for a boolean;
- range input only for a supported continuous number; and
- color control for a public theme token.

The first implementation provides selects and checkboxes. Add another control
kind only when a component has the matching public value shape. Do not invent
docs-only component inputs. For Tabs, density is discrete, so a select is more
truthful than a size slider.

Changing a control updates the rendered result immediately. Where useful, the
card may also show the effective source fragment. A control must not hide
important states behind an undocumented default, and the result must remain
understandable with a keyboard and at a narrow viewport.

## 4. Example-card and page constraints

- The result is first. A reader encounters the usable component before a large
  code block or API table.
- Adjacent prose must add a decision, action, contrast, constraint, or meaning
  not obvious from the heading and preview. Drop empty announcements such as
  "the example below shows the component."
- Write for scanning: front-load the result, prefer short high-information
  sentences, and use headings, lists, or tables when they improve retrieval.
  Concision must not remove required context.
- Choose one recognizable theme for the entire component page, such as space,
  food, books, nature, or science. Vary themes across pages, not within one page.
  Do not mix unrelated motifs inside one scenario.
- Avoid generic workplace, dashboard, team, account, or settings copy unless
  the domain requires it. Avoid placeholder text disguised as realism.
- Use color deliberately through documented public surfaces. Prefer accents,
  focus treatments, and borders over large tinted card backgrounds. Preserve
  contrast in light and dark themes.
- A side-by-side comparison is preferable when memory across toggle states
  would make the distinction harder to see.
- A control is preferable when the change itself is the lesson, such as client
  prop precedence or controlled selection.
- Each example owns a narrow and wide layout. Relevant theme examples cover
  light and dark. Direction-sensitive examples cover LTR and RTL.
- Example-specific CSS styles the setting around the component. It must not
  reach into private `.cui-*` selectors or private variables.
- Preview controls and examples produce no console errors. The first usage
  example, configurator, one primary keyboard example, and one theme example
  receive focused browser checks. Existing component tests continue to own the
  exhaustive state machine.
- Loading all examples must not trigger a separate Python runtime per preview.
  Build-rendered previews are the baseline; editor activation stays lazy.

Not every reference input needs a visual heading. IDs, accessible-name
plumbing, and raw attribute maps may be important without being intrinsically
visual. The composition example and API reference can own them. Every visual
or interactive contract appears in at least one rendered example, and each
component specification maintains a traceable coverage catalog as inputs are
added.

Prepare the example catalog as part of component design, before runtime work.
It defines the reader task, one page-wide fixture theme, draft composition and
copy, visual states, interaction, controls, narrow and environmental cases,
source-module name, and contract coverage for every example. Implementation
may refine the presentation, but it must not discover the component's public
surface by improvising documentation after the runtime is built.

## 5. Implementation increments

1. **Completed:** add the build-rendered preview directive, internal preview
   route, source disclosure, text projection, and one smoke test.
2. **Completed:** convert the first component family's existing snippet into a
   result-first usage example and verify static build, development server,
   keyboard access, and narrow layout.
3. **Completed:** add that family's at-a-glance sampler and configuration
   example. Review the rendered page before authoring the remaining focused
   examples.
4. **Completed:** add the remaining examples in conceptual-section order, with
   targeted browser checks rather than duplicating the complete component
   behavior suite.
5. **Completed:** fold the Tabs pilot lessons into this shared contract and the
   component-family workflow. Apply the method to each later family only after
   refreshing its own research, specification, and example catalog. Tabs still
   needs final human content and visual polish plus live browser testing before
   release.
