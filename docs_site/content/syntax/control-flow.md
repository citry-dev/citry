---
title: Control flow
description: Render parts of a template conditionally or repeat them with citry's if/elif/else and for/empty, in both tag and shorthand attribute forms.
---

# Control flow

Citry gives you two control-flow tools for templates: conditionals
(`if` / `elif` / `else`) and loops (`for` / `empty`). Each one comes in two
forms that do the same thing:

- A **tag form**, where the control flow is its own `<c-*>` element wrapping
  the content.
- A **shorthand attribute form**, where you put a `c-*` attribute directly on
  the element you want to show or repeat.

Use the tag form when you want to wrap several elements at once, and the
shorthand when you are toggling or repeating a single element.

## Conditionals

### Tag form

Wrap each branch in its own tag. The first branch whose condition is truthy
renders; the rest are skipped. `<c-elif>` and `<c-else>` are optional.

```html
<c-if cond="is_visible">
  <div class="panel">Content</div>
</c-if>
<c-elif cond="is_admin">
  <div class="panel">Admin content</div>
</c-elif>
<c-else>
  <c-Login />
</c-else>
```

The branches must be **adjacent siblings**. Whitespace between them is fine
(it is dropped when the branches are grouped), but any other content between
two branches is a parse error.

Conditions use normal Python truthiness, not identity. `[0]` is truthy
because it is a non-empty list; `[]` is falsy. When a `<c-if>` is falsy and
has no matching `<c-else>`, it renders nothing.

### Shorthand form

Put `c-if`, `c-elif`, or `c-else` on a regular element or component. Each one
controls just that single element. `c-else` takes no value.

```html
<div c-if="is_visible" class="panel">Content</div>
<div c-elif="is_admin" class="panel">Admin content</div>
<c-Login c-else />
```

When the condition is false, the element renders nothing at all.

## Loops

### Tag form

`<c-for>` repeats its body once per item. The `each` clause names the loop
variable and the iterable. An optional `<c-empty>` sibling renders when the
iterable produced zero items.

```html
<c-for each="i in items">[{{ i }}]</c-for><c-empty>none</c-empty>
```

With `items=[1]` this renders `[1]`; with `items=[]` it renders `none`.

Loop output is escaped like any other expression. If `x` is `<b>`, then
`{{ x }}` renders `&lt;b&gt;`.

### Shorthand form

Put `c-for` on the element you want to repeat, and `c-empty` on the element
to show when there are no items.

```html
<ul>
  <li c-for="item in items">{{ item.name }}</li>
  <li c-empty>No items found</li>
</ul>
```

The loop variable is in scope for the rest of that same element too, so you
can use it in other attributes on the repeated element (for example a `c-bind`
on the same `<li>`).

### The each clause is a real comprehension

The text inside `each` is a genuine Python comprehension clause, so anything
you can write after `for` in a comprehension works here.

Unpack multiple targets, including dict items:

```html
<c-for each="k, v in d.items()">{{ k }}:{{ v }} </c-for>
```

With `d={'x': 1, 'y': 2}` this renders `x:1 y:2 `.

Filter items with an `if`:

```html
<c-for each="x in xs if x % 2 == 0">{{ x }}</c-for>
```

With `xs=[1, 2, 3, 4]` this renders `24`.

Note that a single target over tuples binds the **whole** tuple. With
`pairs=[(1, 2), (3, 4)]`, writing `each="p in pairs"` and `{{ p }}` renders
`(1, 2)(3, 4)`. Write `each="k, v in pairs"` to unpack each pair.

## The loop variable is only what you name

The only variables bound inside a `<c-for>` are the targets you write in
`each`. There is no automatic `loop` object, so there is no `loop.index`,
`loop.first`, or similar. The loop targets are scoped to the loop body: they
do not leak out, and an outer variable of the same name keeps its value after
the loop.

To number your items, compute the index in Python with `enumerate` and pass it
in through your `template_data`. See
[Expressions](/syntax/expressions/) for why the template side stays simple:
expressions cannot call Python builtins, so work like this belongs in the
component.

```citry
class Cart(Component):
    template = """
      <ul>
        <li c-for="row in rows">{{ row.i }}: {{ row.name }}</li>
      </ul>
    """

    def template_data(self, kwargs, slots):
        rows = [{"i": i, "name": name} for i, name in enumerate(kwargs["items"])]
        return {"rows": rows}
```

## Combining if and for on one element

When you put both `c-if` and `c-for` on the same element, the `if` wraps the
`for`. If the condition is false, the element renders nothing and the loop
does not run at all.

## Related pages

- [Expressions](/syntax/expressions/) for what you can write inside `cond`,
  `each`, and `{{ }}`.
- [Dynamic attributes](/syntax/dynamic-attributes/) for binding attributes
  such as `c-bind` on a looped element.
