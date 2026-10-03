---
title: Slots
description: Add replaceable regions to a component, with defaults, named fills, and data supplied by the component.
---

# Slots

Use a slot when a component should draw the frame while each use of it
supplies what goes inside. A modal, for example, always renders its border,
body, and button row, but every page that uses it puts in a different
message and different buttons.

A slot is a place in the component's template where each use of the
component can insert content. The content that goes into a slot is called
a fill.

If you have not used a slot yet, start with
[Add slots](/getting-started/add-slots/).

## `<c-slot>` and `Slots`

Put a [`<c-slot>`](/reference/builtins/#c-slot) tag where the content should
appear. A slot without a name is the `default` slot. Give any other slot a
`name`:

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

The nested [`Slots`][citry.Component.Slots] class lists the slots the
component accepts, each annotated with [`SlotInput`][citry.SlotInput]. A
slot without a default must be filled. `SlotInput | None = None` makes it
optional.

Without a `Slots` class, a component accepts any slot name. With one, Citry
rejects a fill for a slot the class does not list, and a `<c-slot name="...">`
with a fixed name that the class does not list.

## `<c-fill>` in templates

When a component has only a default slot, put the content between its
opening and closing tags:

```citry-html
<c-Modal>
  <p>Your report is ready.</p>
</c-Modal>
```

To fill a named slot, wrap each fill in a
[`<c-fill>`](/reference/builtins/#c-fill) tag:

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

Use one form or the other. Once the body has a `<c-fill>` tag, everything
in it other than whitespace must be inside a `<c-fill>`, including the
default slot's content.

## `<c-slot>` fallback

Content inside `<c-slot>` is a fallback. Citry shows it when the slot is not
filled:

```citry-html
<button type="button">
  <c-slot>Continue</c-slot>
</button>
```

```citry-html
<c-Button />
<c-Button>Save changes</c-Button>
```

The first button says `Continue`, and the second says `Save changes`.

## What a fill can read

A fill is written in the template that uses the component, so it reads
that template's variables. A fallback is written in the component, so it reads the
component's variables:

```citry-html
<!-- Inside ProfileCard: the fallback reads ProfileCard's data. -->
<c-slot name="title">{{ default_title }}</c-slot>
```

```citry-html
<!-- In the page: the fill reads the page's page_title. -->
<c-ProfileCard>
  <c-fill name="title">{{ page_title }}</c-fill>
</c-ProfileCard>
```

Vue expressions in the browser follow the same rule. See
[Understand slot scope](/vue/slots/#understand-slot-scope).

## `SlotData` for fills { #pass-data-from-the-component-to-the-fill }

Sometimes the component holds data that the fill should format. A list
component can hand each item and its position to the fill, and let the page
decide how a row looks.

Extra attributes on `<c-slot>` become data for the fill. Use the `c-` prefix
to pass the value of a Python expression:

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

The fill names a variable for that data with `data="..."`:

```citry-html
<c-ItemList c-items="items">
  <c-fill name="item" data="row">
    {{ row.index + 1 }}. {{ row.item["name"] }}
  </c-fill>
</c-ItemList>
```

`row` is a read-only [`SlotData`][citry.SlotData] record. Read a field as an
attribute, such as `row.index`, or with brackets for a key that is not a
valid Python name, such as `row["aria-label"]`.

A fill can also unpack just the fields it needs, and rename them:

```citry-html
<c-ItemList c-items="items">
  <c-fill name="item" data="{ item, index as position }">
    {{ position + 1 }}. {{ item["name"] }}
  </c-fill>
</c-ItemList>
```

Typing the slot as `SlotInput[RowData]` documents which fields the
component passes, and lets Citry reject an unpacked field name that
`RowData` does not have. Add `**rest` at the end to collect the fields you
did not name. [`<c-fill>`](/reference/builtins/#c-fill) lists the full
unpacking syntax.

## `slots=` from Python { #fill-slots-from-python }

When Python code builds the component, pass the fills in a `slots`
mapping:

```python
modal = Modal(
    slots={
        "default": "Your export is ready.",
        "actions": "Download",
    },
)
html = str(modal)
```

Citry escapes plain strings, so they appear as text. A `None` value leaves
the slot unfilled. The [`Slot`][citry.Slot] reference covers other kinds of
fill, such as a function that renders the content or HTML you have already
marked safe.

## Wrap the fallback { #wrap-the-fallback-instead-of-replacing-it }

A fill normally replaces the fallback. To keep the fallback and add markup
around it, give the fallback a variable name with `fallback="..."`, then
insert that variable in the fill:

```citry-html
<c-Card>
  <c-fill name="title" fallback="original">
    <strong>{{ original }}</strong>
  </c-fill>
</c-Card>
```

`{{ original }}` renders the slot's fallback content at that point.

## `Slots` default fills

A default other than `None` in the `Slots` class acts as a fill that the
component supplies itself. It takes priority over the fallback inside
`<c-slot>`:

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

When a page does not fill `title`, Citry shows `Notice`, not
`Fallback title`. A `None` default means no fill, so a fallback inside
`<c-slot name="details">` would still show.

## `required` on `<c-slot>` { #require-a-slot-conditionally }

A slot without a default in the `Slots` class must always be filled. When a
slot is needed only if a certain part of the template renders, add
`required` to that `<c-slot>` instead:

```citry-html
<c-if cond="show_details">
  <c-slot name="details" required />
</c-if>
```

If `show_details` is false, the slot does not render and nothing is checked.
If it is true and there is no fill, Citry raises `RuntimeError`.

When a Python expression decides whether the slot is required, use
`c-required`:

```citry-html
<c-slot
  name="details"
  c-required="account.must_supply_details"
/>
```

A truthy result behaves like `required`, and a falsy result leaves the slot
optional.

## `c-name` dynamic slots { #compute-slot-names }

Use `c-name` when the slot names depend on the component's data. This table
header creates one slot per column:

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

A template that uses the component can then fill `header-name`, `header-age`, and so on.
`<c-fill c-name="...">` computes the name of a fill the same way.

Prefer fixed names when the set of slots is known in advance. They are
easier to find and Citry can check them.

!!! note "Computed names and a `Slots` class"

    When the component has a `Slots` class, a computed fill name must be
    listed in it, or Citry raises `TypeError` when the component renders. Names with dashes,
    such as `header-name`, cannot be Python field names, so they work only
    in a component without a `Slots` class. Citry does not check a slot's
    computed name against the class: if the name is not listed, no fill can
    reach that slot, and it always shows its fallback. Two computed fills
    that produce the same name raise `RuntimeError`.

## `c-bind` on slots { #spread-slot-and-fill-settings }

`<c-slot>` and `<c-fill>` accept a `c-bind` mapping, so the settings can come
from one Python value. On `<c-slot>`, the keys `name` and `required` set
those options, and every other key becomes data for the fill:

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

When the mapping and an attribute set the same option, the one written
later in the tag wins.

!!! note "`None` values and invalid keys in a slot or fill mapping"

    A `c-bind` expression that evaluates to `None` changes nothing. Inside
    the mapping, `None` is a value: it makes `required` false, is passed to
    the fill as data, leaves out a fill's `data` or `fallback` variable, and
    is not allowed for `name`. A key that is not a string, or that the tag
    does not accept, raises an error.
    [`c-bind`](/syntax/attributes/#c-bind-spread) describes how
    mappings are applied on other tags.

## Next steps

- [Provide and inject](/concepts/provide-and-inject/) shares a value with
  every component inside a part of the page.
- [Content and slots](/vue/slots/) shows which component's data a Vue
  expression inside a fill reads.
- [Inputs and validation](/concepts/inputs-and-validation/) covers
  component inputs in more depth.
