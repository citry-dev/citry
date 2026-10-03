---
title: Content and slots
description: See which component's Vue data the content you pass into another component reads, and how to keep that content working in the browser.
---

# Content and slots

You pass content into another component, such as a title into a `Panel`,
and that content uses Vue data: a `v-text`, a `@click`, a `v-model`. This
page shows which component's data the content reads in the browser, and
how to keep it working when a component moves content around.

A slot is the place in a component's template, written `<c-slot>`, where
the content goes. A fill is the content you pass, written `<c-fill>` inside
the component's tag. [Slots](/concepts/slots/) covers both in full.

## Understand slot scope { #understand-slot-scope }

A fill reads Vue values from the template you wrote it in. A slot's
fallback, the content inside `<c-slot>` that shows when nothing fills it,
reads values from the component that defines the slot:

```citry-html
<c-Panel>
  <c-fill name="title">
    <span v-text="pageTitle"></span>
  </c-fill>
</c-Panel>
```

Here `pageTitle` comes from the outer component, the one whose template
has the `<c-Panel>` tag. `Panel`'s own values are not visible inside the
fill. [What a fill can read](/concepts/slots/#what-a-fill-can-read) covers
the same rule for Python expressions.

## `v-if` around a slot { #v-if-around-a-slot }

`<c-slot>` accepts no Vue syntax, and the template fails when it loads.
Its attributes other than `name` and `required` become data that Python
passes to the fill, so a `v-if` there could never reach the browser. Put
`v-if` on a `<template>` around the slot, or `v-show` on an element around
it:

```citry-html
<template v-if="expanded">
  <c-slot name="details" />
</template>
```

## Scoped slots { #slot-limits }

A component can hand Python data to a fill, but not its Vue values. The
Python data is computed at render time, for example each item of a list.
Write it as attributes on `<c-slot>`, plain or with `c-`:

```citry-html
{# Inside ItemList #}
<c-for each="item in items">
  <li><c-slot name="item" c-item="item" /></li>
</c-for>
```

The fill names the data with `data="..."` and reads it in Python
expressions, such as `{{ ... }}` or a `c-*` attribute:

```citry-html
<c-ItemList c-items="items">
  <c-fill name="item" data="row">
    <span c-title="row.item['name']">
      {{ row.item['name'] }}
    </span>
  </c-fill>
</c-ItemList>
```

See [`SlotData` for fills](/concepts/slots/#pass-data-from-the-component-to-the-fill)
for typing and unpacking that data.

A component cannot pass its Vue values to a fill. Vue calls this a scoped
slot, and Citry does not support it:

- A `:` binding on `<c-slot>`, such as `:selected="selected"`, fails when
  the template loads.
- `v-slot` and `#name` fail on a component tag and on `<c-fill>`.
- A Vue expression inside the fill cannot read the Python `row` either.
  The editor and `citry check` report it:
  [`citry.vue.python-variable`](/ide/diagnostics/#citry.vue.python-variable)
  or
  [`citry.vue.unknown-variable`](/ide/diagnostics/#citry.vue.unknown-variable).
  Use a `c-*` attribute, as in `c-title` above.

When the content needs a value that changes in the browser, use one of
these instead:

- **Render that part in the component.** Move the markup that reads the
  value into the component's template, or into the slot's fallback, which
  reads the component's own values. Pass what the page decides as a prop.
- **Send the value up with an event.** The component emits the value, the
  page stores it in its own data, and the fill reads it from there. See
  [Listen to child events](/vue/props-and-events/#listen-to-child-events).

## Vue data inside `CTabs` { #keep-vue-bound-group-content-inside-the-groups-tag }

Vue data reaches content through slots, which follow where the content is
written. Some components move content somewhere else while the server
renders the page. When that happens, the Vue data of the component that
wrote the content can no longer reach it.

`CTabs` from the [Citry UI library](/ui-library/) is one of them: it takes
the content of each `<c-CTab>` and `<c-CTabPanel>` inside it and renders it
in its own tab list and panels. So rendering fails when a `<c-CTab>` whose
content reads Vue data is written in a separate component that you place
inside `<c-CTabs>`.

**What you write:** `Page` holds the tabs, and `TabLabels` writes a tab
whose label is its own Vue data:

```citry
from citry import Component


class Page(Component):
    template = """
      <c-CTabs
        default_value="one"
        aria_label="Sections"
      >
        <c-TabLabels />
        <c-CTabPanel value="one">Details</c-CTabPanel>
      </c-CTabs>
    """


class TabLabels(Component):
    template = """
      <c-CTab value="one">
        <span v-text="label"></span>
      </c-CTab>
    """

    js = """
      $component({
        data() {
          return { label: "Overview" };
        },
      });
    """
```

**What `CTabs` does:** while the page renders on the server, `CTabs`
collects every `<c-CTab>` and `<c-CTabPanel>` inside its tag, including
those that a component such as `TabLabels` writes. It moves each tab's
content into a tab button in the `CTabs` template, and each panel's content
into a panel. Nothing appears where you wrote `<c-CTab>`. Simplified,
`CTabs` renders:

```citry-html
<div role="tablist">
  <button role="tab">
    <!-- moved here from TabLabels -->
    <span v-text="label"></span>
  </button>
</div>
```

**Why it fails:** in the browser, the `<span>` now sits in the `CTabs`
template, so Vue looks for `label` in the data of `CTabs`. But `label`
belongs to `TabLabels`, which is inside `CTabs`, because `Page` wrote
`<c-TabLabels />` inside `<c-CTabs>`. Vue data does not pass from a
component out to the component around it. Without a check, the label
would show nothing, so Citry stops the render with an error instead. The
error names the component that wrote the tab (`TabLabels`), the line, the
Vue code it found (`v-text="label"` on `<span>`), and `CTabs` as the
component that moves the content.

**What works:** write the `<c-CTab>` in the component that holds
`<c-CTabs>`, and define `label` there:

```citry
from citry import Component


class Page(Component):
    template = """
      <c-CTabs
        default_value="one"
        aria_label="Sections"
      >
        <c-CTab value="one">
          <span v-text="label"></span>
        </c-CTab>
        <c-CTabPanel value="one">Details</c-CTabPanel>
      </c-CTabs>
    """

    js = """
      $component({
        data() {
          return { label: "Overview" };
        },
      });
    """
```

This works because `Page` contains `CTabs`. Vue can pass content, together
with the data it reads, into a component inside the one that wrote it.
That is the slot scope rule from the top of this page.

The rule: content inside a `<c-CTab>` or `<c-CTabPanel>` that uses Vue
data, a Vue event listener, `v-model`, a `ref`, or an `@c-*` binding must be
written in the component that holds `<c-CTabs>`. Python values such as
`{{ title }}` work from any component, because the server fills them in
before `CTabs` moves anything.

To keep writing the tab in `TabLabels`, set `transparent = True` on
`TabLabels`. Citry then treats its template as if `Page` had written it, so
define `label` in `Page`. If `label` stays in `TabLabels`, Citry raises no
error, but the tab does not get that value.

Other Citry UI components that collect their item tags this way follow the
same rule: `CStepper`, `CTimeline`, `CTour`, `CSortable`, `CSplitter`,
`CTransferList`, `CVirtualList`, and `CFormCollection`.

## See also

- [Slots](/concepts/slots/) for `<c-slot>`, `<c-fill>`, fallbacks, and
  slot data in Python.
- [Props and events](/vue/props-and-events/) for passing browser values
  between components.
- [Server-rendered HTML](/vue/server-rendering/#parts-vue-builds-in-the-browser)
  for slots that Vue builds in the browser.
