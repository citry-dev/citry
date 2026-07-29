---
title: Slots
url: https://citry.dev/v/0.3.1/concepts/slots/
description: "Define insertion points in a component and let the caller fill them, with fallbacks, required slots, and scoped data."
---
# Slots

Slots let a component accept content from its caller. Inside a component's
template you mark an insertion point with `<c-slot>`. When someone uses the
component, they fill that point with `<c-fill>` (or, for the default slot, by
passing plain body content). If a slot is left unfilled, it renders its own
body as fallback.

If you are new to slots, start with the walkthrough in
[Add flexible content](/v/0.3.1/getting-started/add-slots/). This page covers the whole
system: named and default slots, fallback content, required slots, checking
whether a slot is filled, scoped and dynamically named slots, wrapping
fallbacks, and the metadata carried on each fill.

## Named and default slots

A `<c-slot>` without a `name` is the default slot (its name is `"default"`).
Give a slot a `name` to define more than one insertion point:


```html
<!-- Modal.html: define slots -->
<div class="modal">
  <header>{{ title }}</header>
  <main>
    <c-slot />
  </main>
  <footer>
    <c-slot name="actions" />
  </footer>
</div>
```


Fill them from the caller with `<c-fill>`:


```html
<c-Modal title="Confirm">
  <c-fill name="default">
    <p>Are you sure?</p>
  </c-fill>
  <c-fill name="actions">
    <button>Cancel</button>
    <button>Confirm</button>
  </c-fill>
</c-Modal>
```


For the default slot you can skip `<c-fill>` and pass body content directly.
The bare content targets the default slot:


```html
<c-Button>Submit</c-Button>
```


## Fallback content

Whatever sits between `<c-slot>` and `</c-slot>` is fallback content. It
renders when the slot is not filled:


```html
<!-- Button.html -->
<button>
  <c-slot>
    Click me
  </c-slot>
</button>
```



```html
<c-Button />                 <!-- <button>Click me</button> -->
<c-Button>Submit</c-Button>  <!-- <button>Submit</button> -->
```


Fills render in the parent component's scope, while a fallback body renders in
the child component's own scope. So an expression like `{{ who }}` can resolve
differently depending on whether the fill or the fallback ends up rendering.
The same ownership rule applies to browser expressions: template-authored fill
content keeps its call-site Alpine scope, while fallback content uses the
receiver's scope. See [Client interactivity](/v/0.3.1/concepts/client-interactivity/#understand-slot-scope).

## Required slots

Mark a slot `required` to make an unfilled slot an error:


```html
<div><c-slot name="body" required /></div>
```


If nothing fills `body` and the slot actually renders, Citry raises a
`RuntimeError` at render time (the message names the slot and component, for
example `Slot 'body' of component 'Card' is marked as required`).

The check happens at render time, not compile time. A required slot inside a
branch that is never taken (for example a false `<c-if>`) never renders, so it
never raises.

## Checking whether a slot is filled

A required slot errors when it is empty. More often you want the gentler
behavior: render an optional wrapper only when the caller actually filled a
slot, and leave it out otherwise. Do that check in `template_data`. The
`slots` argument holds the fills the component received, so testing for a name
tells you whether that slot was filled:


```citry
from citry import Citry, Component

c = Citry()

class Panel(Component):
    citry = c
    template = """
      <section class="panel">
        <div class="panel__body"><c-slot /></div>
        <c-if cond="has_actions">
          <footer class="panel__actions">
            <c-slot name="actions" />
          </footer>
        </c-if>
      </section>
    """

    def template_data(self, kwargs, slots):
        return {"has_actions": bool(slots.get("actions"))}
```


Now the `<footer>` wrapper renders only when the caller fills `actions`:


```html
<c-Panel>Just a body.</c-Panel>
<!-- no <footer> is rendered -->

<c-Panel>
  <c-fill name="default">Body text.</c-fill>
  <c-fill name="actions"><button>OK</button></c-fill>
</c-Panel>
<!-- the <footer> wrapper is rendered -->
```


If the component declares a typed `Slots` class, `slots` is a dataclass rather
than a mapping, so `.get()` does not apply. Give the optional slot a `None`
default (`actions: SlotInput = None`) and test the field with
`slots.actions is not None`.

## Filling slots from Python

You do not have to fill slots in a template. Pass them to the component
constructor with `slots=`. Values normalize to a [Slot](/v/0.3.1/reference/slots/#citry-slot); a plain
string fills the matching `<c-slot name=...>`:


```citry
from citry import Citry, Component

c = Citry()

class Card(Component):
    citry = c
    template = """
      <div>
        <c-slot name="header">
          Fallback header
        </c-slot>
      </div>
    """

# Fill the "header" slot from Python:
html = str(Card(slots={"header": "From Python"}))
# Unfilled would render the fallback "Fallback header" instead.
```


Passing `slots={"header": None}` is the same as not passing `header` at all;
`None` fills are dropped.

## Scoped slots: passing data to the fill

Sometimes the component holds the data the fill needs, for example the current
item in a loop. Extra attributes on `<c-slot>` become slot data. Use `c-*` for
dynamic values, plain attributes for static values, or `c-bind="mapping"` to
spread a whole mapping:


```html
<!-- UserList.html -->
<ul>
  <c-for each="u in users">
    <li><c-slot name="item" c-user="u" /></li>
  </c-for>
</ul>
```


The fill opts in to that data with `data="var"`. Citry supplies an immutable
[`SlotData`](/v/0.3.1/reference/slots/#citry-slotdata) record, so identifier keys use attribute access:


```html
<c-UserList>
  <c-fill name="item" data="s">
    Hi {{ s.user }}
  </c-fill>
</c-UserList>
<!-- with users=["Ann", "Bob"] -> <li>Hi Ann</li><li>Hi Bob</li> -->
```


The same fill renders once per slot site, each time with that site's data.

Reading slot data is opt-in. A `<c-fill>` without a `data="var"` attribute
silently ignores any data the slot exposes.

`SlotData` also implements Python's mapping interface. This keeps it usable
with `c-bind`, iteration, `.items()`, and bracket access for a key that is not
a valid attribute name. For example, `data["aria-label"]` reads a hyphenated
key. A key that collides with a mapping method, such as `items`, also requires
bracket access or destructuring.

### Destructure the fields you need

Use braces when a fill needs individual fields instead of a `data` namespace:


```html
<c-TableHeadless>
  <c-fill
    name="default"
    data="{ root_attrs, table_attrs as inner_table_attrs, **rest }"
  >
    <div c-bind="root_attrs">
      <table c-bind="inner_table_attrs">
        <!-- custom table markup -->
      </table>
    </div>
  </c-fill>
</c-TableHeadless>
```


Each field name reads one slot-data key and introduces a variable with the same
name. `source as target` renames that variable. `**rest` introduces another
`SlotData` containing every field not selected earlier, in source order. Rest
must be last, but it may be the only item: `data="{ **rest }"` is valid.

The binding language is deliberately small:

- braces describe exactly one level of destructuring;
- fields are separated by commas, with an optional trailing comma;
- whitespace and newlines may appear between tokens;
- source and target names must be valid Python identifiers;
- source names and target names must each be unique;
- source spellings address literal `SlotData` mapping keys, while introduced
  target names follow Python's NFKC normalization, so compatibility spellings
  that normalize to one target count as duplicates; and
- nested patterns, dots, brackets, quoted keys, and more than one `**rest` are
  errors.

All introduced targets follow the same no-shadowing rule as a whole-data
variable or a `<c-for>` target. A destructuring pattern must be written
directly on `data`; `c-bind` cannot supply one dynamically because Citry needs
the complete target list while compiling the template. If a requested source
field is absent when the slot renders, Citry raises a `RuntimeError` naming the
field and the available keys.

When the receiving component declares that slot as `SlotInput[Shape]`, Citry
can catch an unknown source earlier. For a direct `name="..."` and direct
destructuring pattern, the parent template fails to compile if a selected
source is not an annotated field on `Shape`. Plain annotated classes are valid
shapes and require no framework base class. Aliases check the name before
`as`; `**rest` remains valid. Dynamic slot names, effective `c-bind` providers,
and unparameterized `SlotInput` declarations keep the runtime check.

## Dynamic slot names

A slot name need not be a literal. Set it with `c-name` (the dynamic form of
`name`) and the name is computed at render time. This lets a component generate
one slot per item, the way Vuetify's data table exposes a header slot for each
column its caller defines.

Give the table its columns and render a `header-<key>` slot for each one:


```citry
from citry import Citry, Component

c = Citry()

class DataTable(Component):
    citry = c

    class Kwargs:
        columns: list  # e.g. [{"key": "name", "title": "Name"}]

    template = """
      <table>
        <thead>
          <tr>
            <c-for each="col in columns">
              <th>
                <c-slot c-name="'header-' + col['key']" c-label="col['title']">
                  {{ col['title'] }}
                </c-slot>
              </th>
            </c-for>
          </tr>
        </thead>
      </table>
    """

    def template_data(self, kwargs: Kwargs, slots):
        return {"columns": kwargs.columns}
```


A caller fills the generated slots by their resulting names. The `header-name`
fill below replaces that column's header and reads the column's title through
the slot data; a column left unfilled falls back to its own title:


```html
<c-DataTable c-columns="columns">
  <c-fill name="header-name" data="d">
    <b>{{ d.label }}</b>
  </c-fill>
</c-DataTable>
<!-- name -> <b>Name</b>; age -> its plain title "Age" -->
```


Fill names can be dynamic too: a `<c-fill c-name="...">` inside a `<c-for>`
resolves one fill per item. Reach for dynamic names only when the set of slots
really depends on the input; a literal `name` is clearer everywhere else.

## Wrapping the fallback

A fill can wrap the slot's own fallback content instead of replacing it. Bind
the fallback to a variable with `fallback="var"` and render it with
`{{ var }}`:


```html
<!-- Card.html -->
<div><c-slot name="title"><h1>Fallback Title</h1></c-slot></div>
```



```html
<c-Card>
  <c-fill name="title" fallback="fb"><b>[{{ fb }}]</b></c-fill>
</c-Card>
<!-- -> <b>[<h1>Fallback Title</h1>]</b> -->
```


## Declaring slots with a typed inner class

A component can declare its slots in a `Slots` inner class. Type each field
with [SlotInput](/v/0.3.1/reference/slots/#citry-slotinput). Citry turns `Slots` into a dataclass when
the component class is created:


```citry
from citry import Component, SlotInput

class Card(Component):
    class Kwargs:
        title: str          # required
        size: int = 10      # optional

    class Slots:
        header: SlotInput

    template = """
      <div>
        {{ title }}
        <c-slot name="header" />
      </div>
    """
```


Declaring `Slots` makes it a closed schema. A `<c-slot name="X">` whose `X` is
not declared becomes a compile-time error, and a caller's `<c-fill>` for a slot
the schema does not declare is rejected too. Omitting the `Slots` class
disables these checks and accepts any fills.

For more on typing components, see
[Typing and validation](/v/0.3.1/concepts/typing-and-validation/).

## Slot content as a value: the Slot type

Under the hood every form of slot content normalizes to a [Slot](/v/0.3.1/reference/slots/#citry-slot):
a lazy, repeatable, standalone callable. You rarely construct one by hand, but
knowing how it behaves explains the escaping rules:


```python
from citry import Slot
from citry.util.html import SafeString

# A plain string is escaped when the Slot is constructed:
assert Slot("<b>hi</b>")() == "&lt;b&gt;hi&lt;/b&gt;"

# A SafeString is trusted and passes through untouched:
assert Slot(SafeString("<b>hi</b>"))() == "<b>hi</b>"

# A function receives a SlotContext and is repeatable with different data:
greet = Slot(lambda ctx: f"Hello, {ctx.data.name}!")
assert greet({"name": "John"}) == "Hello, John!"
```


A slot function receives a single `SlotContext` argument with `.data` (the
immutable `SlotData` record), `.fallback` (the slot's fallback content as a
`Slot` or `None`), and `.provides` (provide/inject data at the call site or
`None`). It returns a string, a `SafeString`, a `CitryElement`, or a
`CitryRender`.

Escaping timing depends on the input form. A plain string or scalar is escaped
when the `Slot` is constructed; a function's return value is escaped when the
`Slot` is called. A `SafeString`, a [CitryElement](/v/0.3.1/reference/rendering/#citry-citryelement), or a
[CitryRender](/v/0.3.1/reference/rendering/#citry-citryrender) is trusted and never escaped.

## Slot metadata for extensions

Every [Slot](/v/0.3.1/reference/slots/#citry-slot) carries a few fields that record where its content
came from. They are filled in when the slot is passed to a component, so a data
method (or an extension) can read them off a fill:

- `component_name`: the component the slot content was given to.
- `slot_name`: the slot the content fills.
- `source_position`: the character span of the `<c-fill>` in its template, or
  `None` for a fill passed from Python.
- `extra`: a plain dict, scratch space for an extension to attach its own
  per-slot data.


```citry
from citry import Citry, Component

c = Citry()

class Card(Component):
    citry = c
    template = """
      <div><c-slot name="header" /></div>
    """

    def template_data(self, kwargs, slots):
        header = slots["header"]
        print(header.slot_name)        # "header"
        print(header.component_name)   # the component that received it
        print(header.source_position)  # span of the <c-fill>, or None
        return {}
```


`extra` is the supported place for an extension to tag a slot without touching
its content. Set it when you build the [Slot](/v/0.3.1/reference/slots/#citry-slot), or write to it later:


```python
from citry import Slot

slot = Slot("Hello!", extra={"origin": "cms"})
slot.extra["seen"] = True
```


For the hooks an extension uses to observe slots as they render, see
[Extensions](/v/0.3.1/advanced/extensions/).

## Next steps

- [Provide and inject](/v/0.3.1/concepts/provide-and-inject/) for passing data down
  without threading it through every slot.
- [Rendering](/v/0.3.1/concepts/rendering/) for how a component tree turns into HTML.
- [Components](/v/0.3.1/concepts/components/) for the full component model.