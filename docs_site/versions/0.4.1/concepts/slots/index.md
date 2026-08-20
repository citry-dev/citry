---
title: Slots
url: https://citry.dev/v/0.4.1/concepts/slots/
description: "Add replaceable regions to a component, with defaults, named fills, and data supplied by the component."
---
# Slots

Use slots when a component should own the surrounding layout while another
template chooses what appears inside it. A modal can always render its frame,
for example, while each use supplies a different message and set of actions.

If you have not used a slot yet, start with
[Add flexible content](/v/0.4.1/getting-started/add-slots/). This page explains the
full composition model and the choices you have when designing a component.

## Define the places another template can fill

Add the [`<c-slot>` built-in](/v/0.4.1/reference/builtins/#c-slot) wherever the
component should accept content. An unnamed slot is the `default` slot. Give
other slots a `name`:


```citry
from citry import Citry, Component, SlotInput

c = Citry()


class Modal(Component):
    citry = c

    class Slots:
        default: SlotInput
        actions: SlotInput | None = None

    template = """
      <section class="modal">
        <div class="modal__body">
          <c-slot />
        </div>
        <footer class="modal__actions">
          <c-slot name="actions" />
        </footer>
      </section>
    """
```


The inner [`Slots` class](/v/0.4.1/reference/component/#citry-component-slots) describes the names this
component accepts. [`SlotInput`](/v/0.4.1/reference/slots/#citry-slotinput) describes content for one
slot. A field without a default must be filled when the component is used;
`SlotInput | None = None` makes that field optional.

Without a `Slots` class, a component accepts any slot name. Declaring one gives
the component a closed, checked interface: Citry rejects undeclared outlets
and fills.

## Choose one way to fill a component

There are two valid shapes for content inside a component tag.

For a component with only a default fill, put the content directly in the
body:


```citry-html
<c-Modal>
  <p>Your report is ready.</p>
</c-Modal>
```


The body fills the `default` slot.

When you need a named slot, use only
[`<c-fill>` tags](/v/0.4.1/reference/builtins/#c-fill) in the body:


```citry-html
<c-Modal>
  <c-fill name="default">
    <p>Delete this draft?</p>
  </c-fill>
  <c-fill name="actions">
    <button type="button">Keep it</button>
    <button type="submit">Delete it</button>
  </c-fill>
</c-Modal>
```


Do not mix direct body content with `<c-fill>` tags. Once you use one explicit
fill, every non-whitespace part of the body must belong to a fill. This keeps
it clear which slot owns each piece of content.

## Supply fallback content

Content inside `<c-slot>` is a fallback. Citry inserts it only when no fill is
available:


```citry-html
<button type="button">
  <c-slot>Continue</c-slot>
</button>
```



```citry-html
<c-Button />
<c-Button>Save changes</c-Button>
```


The first button says `Continue`; the second says `Save changes`.

There are three related rules worth keeping separate:

- A `Slots` field without a default must be supplied when the component is
  used.
- A non-`None` field default is itself a fill. It wins over the fallback body
  inside `<c-slot>`.
- `required` on `<c-slot>` raises only if that outlet actually renders without
  a fill.

This component supplies a default fill from its schema:


```citry
from citry import Component, SlotInput


class Notice(Component):
    class Slots:
        title: SlotInput = "Notice"
        details: SlotInput | None = None

    template = """
      <aside>
        <h2><c-slot name="title">Fallback title</c-slot></h2>
        <c-slot name="details" />
      </aside>
    """
```


With no `title` fill, Citry inserts `Notice`, not `Fallback title`. The `None`
default on `details` means no fill, so its in-template fallback would still be
available.

Use `required` when the requirement depends on whether the outlet is reached:


```citry-html
<c-if cond="show_details">
  <c-slot name="details" required />
</c-if>
```


If `show_details` is false, that slot does not render and cannot raise. If it
is true and no fill exists, Citry raises `RuntimeError`.

### Require a slot conditionally

Use `c-required` when the requirement itself comes from a Python expression:


```citry-html
<c-slot
  name="details"
  c-required="account.must_supply_details"
/>
```


Citry evaluates the expression when the outlet renders. A truthy result has
the same behavior as the bare `required` marker; a falsy result leaves the
slot optional. As with `required`, an outlet in a branch that does not render
cannot raise a missing-fill error.

## Know which scope a fill uses

A template-authored fill belongs to the template that uses the component. Its
Python expressions keep that template's variables. A fallback belongs to the
component that defines the slot and uses that component's variables.


```citry-html
<!-- Inside ProfileCard: fallback uses ProfileCard data. -->
<c-slot name="title">{{ default_title }}</c-slot>
```



```citry-html
<!-- This fill uses the surrounding template's page_title. -->
<c-ProfileCard>
  <c-fill name="title">{{ page_title }}</c-fill>
</c-ProfileCard>
```


The same ownership rule applies to Alpine expressions. See
[Understand slot scope](/v/0.4.1/concepts/client-interactivity/#understand-slot-scope)
for the browser side.

## Scoped slots: passing data to the fill

Sometimes the component owns information that the surrounding template needs
to format. A list component can expose the current row and its position
without deciding how either should look.

Extra attributes on `<c-slot>` become scoped slot data. Use `c-*` for Python
expressions:


```citry
from citry import Component, SlotInput


class RowData:
    item: dict[str, str]
    index: int


class ItemList(Component):
    class Kwargs:
        items: list[dict[str, str]]

    class Slots:
        item: SlotInput[RowData]

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,
    ) -> dict[str, object]:
        return {
            "items_with_index": list(enumerate(kwargs.items)),
        }

    template = """
      <ul>
        <c-for each="index, item in items_with_index">
          <li>
            <c-slot
              name="item"
              c-item="item"
              c-index="index"
            />
          </li>
        </c-for>
      </ul>
    """
```


The fill opts in with `data="..."`:


```citry-html
<c-ItemList c-items="items">
  <c-fill name="item" data="row">
    {{ row.index + 1 }}. {{ row.item["name"] }}
  </c-fill>
</c-ItemList>
```


The value is an immutable [`SlotData`](/v/0.4.1/reference/slots/#citry-slotdata) record. Identifier keys
support attribute access, as in `row.index`. It also behaves like a mapping,
so use brackets for keys such as `row["aria-label"]`.

Typing the slot as `SlotInput[RowData]` documents what the outlet supplies and
lets Citry catch unknown fields in direct destructuring patterns. A fill can
name only the fields it needs:


```citry-html
<c-ItemList c-items="items">
  <c-fill name="item" data="{ item, index as position }">
    {{ position + 1 }}. {{ item["name"] }}
  </c-fill>
</c-ItemList>
```


Use `**rest` last to collect fields you did not name. For the complete binding
grammar and errors, see [`<c-fill>`](/v/0.4.1/reference/builtins/#c-fill).

## Filling slots from Python

Pass a `slots` mapping when Python, rather than another template, assembles
the component:


```citry
html = str(
    Modal(
        slots={
            "default": "Your export is ready.",
            "actions": "Download",
        },
    )
)
```


Citry converts each accepted value to a lazy, repeatable
[`Slot`](/v/0.4.1/reference/slots/#citry-slot). Ordinary strings are escaped. A `None` value means the
slot was not filled. See the [Slot Reference](/v/0.4.1/reference/slots/#citry-slot) for callable fills,
safe rendered values, and metadata used by extensions.

## Dynamic slot names

Use `c-name` when the available slot names genuinely depend on component data.
This table creates one outlet per column:


```citry-html
<c-for each="column in columns">
  <th>
    <c-slot
      c-name="'header-' + column['key']"
      c-label="column['title']"
    >
      {{ column["title"] }}
    </c-slot>
  </th>
</c-for>
```


The template using the component can fill `header-name`, `header-age`, or any
other name produced by the expression. `<c-fill c-name="...">` can compute
fill names too.

A computed name must still appear in the component's declared `Slots` schema.
If two dynamic fills resolve to the same name, Citry raises `RuntimeError`.
Prefer literal names when the interface is fixed; they are easier to discover
and check.

## Spread slot and fill settings

`<c-slot>` and `<c-fill>` are the two structural tags that accept `c-bind`.
The expression must produce a mapping, and Citry applies its keys in source
order with the directly authored attributes.

On `<c-slot>`, the mapping may provide `name` and `required`. Every other key
becomes data exposed by that slot:


```citry-html
<c-slot
  c-bind="{
    'name': active_slot,
    'required': require_active_slot,
    'item': current_item,
  }"
/>
```


On `<c-fill>`, the accepted keys are `name`, `data`, and `fallback`:


```citry-html
<c-fill
  c-bind="{
    'name': active_slot,
    'data': 'slot_data',
  }"
>
  {{ slot_data }}
</c-fill>
```


A later source wins for the same setting. A spread that evaluates to `None`
leaves the current settings unchanged. Inside a mapping, `None` is still a
value: it makes `required` false, remains available as slot data, omits a
fill's `data` or `fallback` binding, and is invalid for `name`. Non-string or
unsupported keys raise an error. See
[`c-bind`](/v/0.4.1/syntax/dynamic-attributes/#c-bind-spread) for mapping evaluation
and ordering on ordinary HTML elements and component inputs.

## Wrapping the fallback

A fill normally replaces the fallback. To wrap it instead, bind the fallback
to a variable and insert that variable inside the fill:


```citry-html
<c-Card>
  <c-fill name="title" fallback="original">
    <strong>{{ original }}</strong>
  </c-fill>
</c-Card>
```


The `original` value is a [`Slot`](/v/0.4.1/reference/slots/#citry-slot), so inserting it renders the
slot's fallback at that point.

## Next steps

- [Provide and inject](/v/0.4.1/concepts/provide-and-inject/) passes data through a
  whole rendered subtree.
- [Client interactivity](/v/0.4.1/concepts/client-interactivity/) explains ownership
  when slots contain Alpine expressions.
- [Inputs and validation](/v/0.4.1/concepts/inputs-and-validation/) covers typed
  component inputs in more depth.