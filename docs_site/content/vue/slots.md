---
title: Content and slots
description: See which component's Vue data the content you pass into another component reads, and how to keep that content working in the browser.
---

# Content and slots

You pass content into another component, such as a title into a `Panel`,
and that content uses Vue data: a `v-text`, a `@click`, a `v-model`. This
page shows which component's data the content reads in the browser, how
a component passes its own Vue or Python data into that content, and how
to keep it working when a component moves content around.

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
fill, unless `Panel` passes them to it; see [Scoped slots](#slot-limits). [What a fill can read](/concepts/slots/#what-a-fill-can-read) covers
the same rule for Python expressions.

## `v-if` around a slot { #v-if-around-a-slot }

To show a slot only when a Vue condition holds, put `v-if` on a
`<template>` around it, or `v-show` on an element around it:

```citry-html
<template v-if="expanded">
  <c-slot name="details" />
</template>
```

A `v-if` on `<c-slot>` itself fails when the template loads. `<c-slot>`
turns every attribute except `name`, `required`, and `:` slot props into
Python data for the fill, so the condition could never reach the browser.
A `:` slot prop, such as `:row="row"`, passes Vue data instead; see
[Scoped slots](#slot-limits).

## `<template #name>` slots { #vue-slot-syntax }

Vue fills a named slot with `<template #name>` or `<template v-slot:name>`.
Inside a Citry component tag, the template fails when it loads, on every
page, because Citry fills slots only from `<c-fill>`. Without the check,
the content would land in the default slot and the named slot would keep
its fallback.

```citry-html
<!-- Fails: Vue slot syntax inside a Citry component tag. -->
<c-Panel>
  <template #title>Report</template>
</c-Panel>

<!-- Works: name the slot with c-fill. -->
<c-Panel>
  <c-fill name="title">Report</c-fill>
</c-Panel>
```

The same goes for `<template v-slot>` and `<template #default>`, which
name the default slot. It also goes for slot syntax on another element,
such as `<div #title>`, and for `#[expr]`; for `#[expr]`, write
`<c-fill c-name="...">` with a Python expression instead. `v-slot` on
the component tag itself, as in `<c-Panel v-slot="p">`, fails too.

`v-slot` on `<c-fill>` itself is different: it reads Vue slot props; see
[Pass Vue data](#scoped-slots).

The check covers Citry component tags, including `<c-component>`, and
looks through `<c-provide>` and `<c-cache>` to the tag around them. `<template #name>` still
works inside a Vue component that a [Vue plugin](/vue/plugins/) registers,
and inside `<c-element is="my-widget">`, which renders the tag you name,
so it can be a plugin's Vue component.

Directly inside a `<c-fill>`, `<template #name>` loads, because a
transparent component (one with `transparent = True`, such as
`<c-provide>`) can pass that content on to a Vue component that Citry
cannot see when the template loads. Inside an ordinary component's fill
it still does nothing: a page with Vue drops the `<template>` wrapper and
shows its content in that fill, and a page without Vue shows nothing.

To pass a slot template through a transparent component of your own,
write its default fill out:

```citry-html
<my-widget>
  <c-Themed>
    <c-fill name="default">
      <template #header>Report</template>
    </c-fill>
  </c-Themed>
</my-widget>
```

## Scoped slots { #slot-limits }

A component can pass data to the content a caller puts in its slot. Vue
calls this a scoped slot. A slot can pass two kinds of data, and each kind
has one attribute on `<c-slot>` and one on `<c-fill>`. Use Python data when Python knows the
value at render time. Use Vue data when the value changes in the browser.

### Pass Vue data { #scoped-slots }

When the value exists only in the browser, such as each row of a list the
browser filters, pass it with a `:` binding on `<c-slot>`:

```citry-html
{# Inside FilteredList #}
<template v-for="row in visible" :key="row.id">
  <li><c-slot name="item" :row="row" /></li>
</template>
```

The fill reads it with `v-slot`, in Vue expressions:

```citry-html
<c-FilteredList>
  <c-fill name="item" v-slot="{ row }">
    <span v-text="prefix + row.title"></span>
  </c-fill>
</c-FilteredList>
```

Inside the fill, `row` comes from the slot, and `prefix` from the outer
component, as in any fill. When the list changes in the browser, the fill
follows it.

The `:` binding on `<c-slot>` and the `v-slot` value on `<c-fill>` are
part of the template, so only the template author writes them. Request
data reaches the fill only as values, such as the slot prop `row` or the
outer component's `prefix`.

!!! warning "Vue does not check HTML, URLs, or attribute names"

    Do not bind request data, or text a site visitor saved, with
    `v-html` or with a URL binding such as `:href` or `:src`, in a fill
    or anywhere else. Vue inserts the HTML as it is and does not check a
    URL's scheme, so that text could run as script on the page. Show
    visitor text with `v-text`. On the server, allow only `https:` or
    `http:` URLs and paths on your own site.

    Do not pass a whole object with `v-bind="..."` when its keys
    come from request data or from something a visitor saved. Vue
    sets each key on the element, whatever it is: as an attribute,
    as a property such as `innerHTML`, or as an event handler such
    as `onclick`. Bind each value you need to an attribute you name
    in the template, such as `:title="row.title"`.

`<c-slot>` also accepts `v-bind:row`. `v-slot` takes one object pattern,
such as `{ row }`, or one name, such as `props`, which then holds every
prop. Other forms fail; see [Slot syntax errors](#scoped-slot-errors).

When the server knows the values the slot passes, such as rows from
`js_data()`, it writes the fill with them, so the page shows the fill
before Vue starts. A part of the fill that reads a value only the browser
knows is built in the browser instead; see
[Browser-built parts](/vue/server-rendering/#parts-vue-builds-in-the-browser).
A `v-slot` pattern that nests one pattern in another, such as
`{ row: { title } }`, or gives a default, such as `{ row = {} }`, makes Vue
build the element around the `<c-slot>` in the browser.

### Pass Python data { #pass-python-data }

When Python computes the value at render time, for example each item of a
Python list, write it on `<c-slot>` as a plain attribute for text
(`item="x"`) or as a `c-` attribute for a Python expression
(`c-item="item"`):

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

### Mix Vue and Python data { #use-both-kinds }

A slot can pass both kinds, and a fill can read both, under different
names:

```citry-html
{# The slot passes Python item and Vue row #}
<c-slot
  name="item"
  c-item="item"
  :row="row"
/>

{# The fill reads them as d and row #}
<c-fill
  name="item"
  data="d"
  v-slot="{ row }"
>
  <span c-title="d.item" v-text="row.title"></span>
</c-fill>
```

`d` exists only in Python expressions, and `row` only in Vue
expressions. The editor and `citry check` report a mix-up:

- A Vue expression cannot read `d`:
  [`citry.vue.python-variable`](/ide/diagnostics/#citry.vue.python-variable)
  or
  [`citry.vue.unknown-variable`](/ide/diagnostics/#citry.vue.unknown-variable).
  To show a Python value, write it with a `c-*` attribute, as
  `c-title` does, instead of a Vue expression.
- A Python expression cannot read `row`:
  [`citry.template.unknown-variable`](/ide/diagnostics/#citry.template.unknown-variable).

### Slot syntax errors { #scoped-slot-errors }

These forms fail when the template loads, each with a message that says
what to write instead.

On `<c-slot>`:

- a dynamic name, such as `:[key]`;
- a modifier, such as `:row.prop`;
- the object form `v-bind="props"`;
- a prop with no value, such as `:row` alone;
- the prop names `name` and `key`, which Vue and Citry use for the slot
  itself, and names that start with `c-`, which Citry reads as Python
  attributes;
- `c-:row`, which would let a Python value choose the browser's code.

On `<c-fill>`:

- `#name` or `v-slot:name`, because `name="..."` chooses the slot;
- any other Vue directive, such as `v-if` or `@click`; put it on an
  element inside the fill;
- `v-slot` with no value, in capitals (`V-SLOT`), with a modifier, or as
  `c-v-slot`;
- a `v-slot` value that is not valid JavaScript;
- several parameters, such as `a, b`;
- an array pattern, such as `[row]`;
- a `...props` or a default value for the whole pattern; write `props`
  or `{ row }` instead;
- a comma after the pattern, as in `{ row },`;
- a comment;
- an `&` character, as in `&amp;`;
- a default value that is not a literal, such as `{ row = empty }` or
  `{ row = make() }`; a literal default such as `{ row = null }` or
  `{ row = 'none' }` works;
- a computed key, such as `{ [name]: row }`;
- reading a prop named `key`, as in `{ key }`, which holds Citry's own
  key for the slot.

On both tags:

- a `{{ ... }}` inside a `:` prop or a `v-slot` value, which would let
  Python text choose the browser's code;
- a name that starts with `$`, `_`, or `citry`, which Citry keeps for its
  own slot props;
- one name used twice: two props such as `:row-data` and `:rowData` (Vue
  writes prop names in camelCase, so these are the same name), a Vue prop
  and Python slot data such as `:row` with `c-row`, or a `v-slot` name that
  the fill's `data="..."` or `fallback="..."` also names.

### Errors when rendering { #scoped-slot-limits }

These cases fail with an error when the page renders.

**`:` props or `v-slot` in `c-bind`.** A `c-bind` dict with a key such
as `":row"` or `"v-slot"` fails, because Python data must not choose the
code the browser runs. A `c-bind` key that matches the name of a `:`
prop on the same `<c-slot>` fails too, and so does a `data` or
`fallback` name on `<c-fill>` that the fill's `v-slot` also uses.

**Components that render their slot in place.** `<c-provide>`,
`<c-cache>`, `<c-element>`, and components with `transparent = True`
copy their slot content into the template around them. They have no Vue
slot to pass Vue data through, so a `:` slot prop or a `v-slot` fill
there fails. In a transparent component of your own, pass Python slot
data instead. To fill a slot of a plugin's Vue component, use
`<template #name>` inside `<c-element>`, as in
[`<template #name>` slots](#vue-slot-syntax). A component with
[`simple = True`](/performance/simple-components/) takes only unnamed
content in an empty `<c-slot />`, so it cannot pass slot data of either
kind.

**Citry components in a fill for a `v-for` slot.** When a component's
`<c-slot>` sits inside a Vue `v-for`, as in `FilteredList` above, any
fill for it that holds a Citry component fails, with or without
`v-slot`. Citry prepares each component once on the server, and Vue
would render the fill once per row:

```citry-html
<!-- Fails: a Citry component inside the fill. -->
<c-fill name="item" v-slot="{ row }">
  <c-Badge :label="row.title" />
</c-fill>

<!-- Works: plain elements only. -->
<c-fill name="item" v-slot="{ row }">
  <span class="badge" v-text="row.title"></span>
</c-fill>
```

To keep the component, loop with Citry's `c-for` around the `<c-slot>`
instead of Vue's `v-for`, and pass each row as Python slot data. The list
then changes only when the server renders the component again. If the
component must follow browser data, render that part inside the
component that owns the list, or send the value up with an event (see
[Listen to child events](/vue/props-and-events/#listen-to-child-events)).

**A fill passed on through Python.** A component can hand a fill it
received on to another component from Python, by wrapping it in a
[`Slot`][citry.Slot] function, such as
`Slot(lambda ctx: fill(ctx.data))`, where `fill` is the slot the
component received. When the fill uses `v-slot` and the
other component's `<c-slot>` has `:` props, the render fails, because a
Python `Slot` cannot pass Vue props on. Pass the fill to that component in
a template instead.

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
