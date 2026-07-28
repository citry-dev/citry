---
title: Update the page from a handler
description: Return Citry event actions in order, render into page targets, and preserve browser state across updates.
---

# Update the page from a handler

An event handler can replace its own component, render somewhere else, return
data, dispatch a browser event, change browser history, or navigate. Return one
result for one effect, or return a list when the effects must happen in order.

## Update another part of the page

[`actions.Render`][citry.ext.events.actions.Render] places a rendered component
into a CSS target. This handler updates the cart badge, then dispatches a
browser event:

```citry
from citry.ext.events import actions


class CartIn:
    product_id: int


class AddToCart(Component):
    citry = citry_app

    class Events:
        def add(self, data: CartIn):
            cart = add_item(data.product_id)
            return [
                actions.Render(
                    CartBadge(count=cart.count),
                    target="#cart-badge",
                    swap="inner",
                ),
                actions.Dispatch(
                    "AddToCart:updated",
                    {"count": cart.count},
                ),
            ]

    template = """
      <button @c-click="add({ product_id: 42 })">
        Add to cart
      </button>
    """
```

Event names are exact strings. Prefix application events with the component
name, such as `MyCard:submit` or `AddToCart:updated`. Names beginning with
`citry:` belong to the runtime.

## Return actions in the order they must happen

A handler can return one result. It can combine ordinary actions in a list,
which Citry applies in order. A download is the exception: it must be the only
result of an unbundled handler.

| Return value | Browser result |
|---|---|
| `MyComponent(...)` | Render and morph over the calling instance. |
| [`actions.Render(...)`][citry.ext.events.actions.Render] | Render into an explicit target with the selected swap. |
| `dict` or [`actions.Data(value)`][citry.ext.events.actions.Data] | Resolve the caller's promise with JSON data. |
| [`actions.Dispatch(name, detail)`][citry.ext.events.actions.Dispatch] | Dispatch a bubbling browser `CustomEvent`. |
| [`actions.Redirect(url)`][citry.ext.events.actions.Redirect] | Navigate the page. |
| [`actions.PushUrl(url)`][citry.ext.events.actions.PushUrl] | Add a browser history entry without navigating. |
| [`actions.ReplaceUrl(url)`][citry.ext.events.actions.ReplaceUrl] | Replace the current browser history URL without navigating. |
| [`actions.Download(...)`][citry.ext.events.actions.Download] | Download a file by itself. See [dedicated download responses](/events/http/#download-a-file-from-one-event). |
| `None` | Acknowledge the call without a visible action. |

Order matters when one action removes the audience of another. This version
may remove the listener before it receives the event:

```python
return [
    actions.Render(ClosedDialog(), target="#dialog"),
    # Too late if the render removed the listener.
    actions.Dispatch("Editor:closed"),
]
```

Dispatch first when the old subtree must hear it:

```python
return [
    actions.Dispatch("Editor:closed"),
    actions.Render(ClosedDialog(), target="#dialog"),
]
```

History actions only update the address and history stack. They preserve the
page's existing `history.state`, do not fire `popstate`, and do not restore
component HTML or State when the user later chooses Back or Forward. Use a
client router when URL history must restore page content.

## Understand shared and independent render targets

If one `Render` action's selector matches several elements, Citry inserts one
logical component instance in all of them. The placements share one State and
one token. A later self-render updates every placement together.

This is ideal for one cart count shown in both desktop and mobile navigation:

```citry-html
<span class="cart-badge-slot"></span>
<!-- ... -->
<span class="cart-badge-slot"></span>
```

```python
return actions.Render(
    CartBadge(count=cart.count),
    target=".cart-badge-slot",
    swap="inner",
)
```

The natural first mistake is expecting one of those badges to gain independent
State. It cannot: both placements are views of the same instance.

When each region must evolve independently, return one render action per
target. Each action renders a distinct component instance:

```python
return [
    actions.Render(
        RegionStatus(region="desktop"),
        target="#desktop-status",
        swap="inner",
    ),
    actions.Render(
        RegionStatus(region="mobile"),
        target="#mobile-status",
        swap="inner",
    ),
]
```

## Preserve identity when lists or parents re-render

Without a key, morphing matches siblings by position. If a list reorders, a
focused input, caret, or client-owned widget can remain at the old position
instead of following its item. Put `#c-key` on reorderable `<c-for>` items:

```citry-html
<c-for each="item in items">
  <article #c-key="item.id">
    <input c-value="item.title">
  </article>
</c-for>
```

An interactive child under a parent that can re-render also needs a component
key, so its client State follows the same domain object:

```citry-html
<c-for each="item in items">
  <c-todo-row
    #c-key="item.id"
    item="item"
  />
</c-for>
```

An element key only matches within one sibling window. The same key cannot move
a node between parents or nesting depths. This conditional changes depth, so
the input is recreated:

```citry-html
<c-if cond="editing">
  <input #c-key="'draft'" />
</c-if>
<c-else>
  <div class="highlight">
    <input #c-key="'draft'" />
  </div>
</c-else>
```

Keep the keyed node at the same tree position in every branch:

```citry-html
<div c-class="'highlight' if not editing else ''">
  <input #c-key="'draft'" />
</div>
```

Keys must be unique among the siblings that can compete. A component key must
also be unique for that component class within the rendered update region.

For manually fetched HTML rather than an event result, see
[HTML fragments](/advanced/html-fragments/).
