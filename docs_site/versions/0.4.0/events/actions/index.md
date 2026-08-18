---
title: Event actions
url: https://citry.dev/v/0.4.0/events/actions/
description: "Return Citry event actions in order, render into page targets, and preserve browser state across updates."
---
# Event actions

An event handler can replace its own component, render somewhere else, return
data, dispatch a browser event, change browser history, or navigate. Return one
result for one effect, or return a list when the effects must happen in order.

## Update another part of the page

[`actions.Render`](/v/0.4.0/reference/events/#citry-ext-events-actions-render) places a rendered component
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

String-based listeners such as `$onEvent` preserve that exact case. HTML
attribute names are lowercased, so use lowercase event names when listening
with an Alpine `@name` attribute.

## Choose where to listen for Dispatch

[`actions.Dispatch`](/v/0.4.0/reference/events/#citry-ext-events-actions-dispatch) sends its browser
event back to the component instance whose handler returned it. It does not
fire from the button or form that started the call.

The delivery path is:

1. The server puts the calling component's render ID on the action.
2. The browser finds that instance's current first root.
3. It dispatches a bubbling DOM `CustomEvent` from that root.

For a single-root component, this makes a listener on the root straightforward:


```citry-html
<section @signup:sent="email = $event.detail.email">
  ...
</section>
```


The event moves upward through the DOM. It never moves down into the root's
children. A component with several roots still dispatches only once, from its
first live root, so the same logical event does not reach page-wide listeners
several times.

| Listener | What receives the event |
|---|---|
| `@name` on the first root | The root receives it directly. |
| `@name` on a DOM ancestor | The event bubbles to the ancestor. |
| `@name` inside the first root | Nothing; events do not bubble downward. |
| `@name` on another root of the same component | Nothing; only the first root dispatches. |
| [`$onEvent(name, fn)`](/v/0.4.0/reference/browser-apis/#on-event) | Only events targeting this component instance. |
| `$component`'s `onEvent(name, fn)` | The same instance-scoped events, with component cleanup. |
| [`Citry.events.on(name, fn)`](/v/0.4.0/reference/browser-apis/#citry-events-on) | Matching events from every instance, plus instance-less events. |

A plain DOM listener on an ancestor also hears same-named events from nested
components. The instance-scoped `$onEvent` and `onEvent` helpers normally
filter those out, so they are the safer default for reusable and multi-root
components. If two nested components share the very same root element, that
element belongs to both instances and both subscriptions receive the event.
When Citry connects a newly rendered component to the same logical instance,
these subscriptions keep following it even though its render ID changed. Their
callbacks receive the event's `detail` value directly, rather than the whole
DOM event.

`$onEvent` returns a function that removes its subscription. The `onEvent`
member provided to [`$component`](/v/0.4.0/reference/browser-apis/#component) ties the subscription to that
component initializer's cleanup automatically.

Both instance-scoped helpers listen through `document`. A DOM listener that
stops propagation before the event reaches `document` also prevents those
helpers, and `Citry.events.on`, from receiving it.

If the calling instance has been removed or has no live root by the time the
action runs, Citry drops the event instead of silently dispatching it from
`document`. Calls with no component instance are the exception: their
`Dispatch` events start at `document`. [`Citry.events.on`][citry-events-on]
receives them, but component-local DOM listeners, `$onEvent`, and
`$component`'s `onEvent` do not.

## Return actions in the order they must happen

A handler can return one result. It can combine ordinary actions in a list,
which Citry applies in order. A download is the exception: it must be the only
result of an unbundled handler.

| Return value | Browser result |
|---|---|
| `MyComponent(...)` | Render and morph over the calling instance. |
| [`actions.Render(...)`](/v/0.4.0/reference/events/#citry-ext-events-actions-render) | Render into an explicit target with the selected swap. |
| `dict` or [`actions.Data(value)`](/v/0.4.0/reference/events/#citry-ext-events-actions-data) | Resolve an imperative caller's Promise with JSON data. |
| [`actions.Dispatch(name, detail)`](/v/0.4.0/reference/events/#citry-ext-events-actions-dispatch) | Dispatch a bubbling browser `CustomEvent`. |
| [`actions.Redirect(url)`](/v/0.4.0/reference/events/#citry-ext-events-actions-redirect) | Navigate the page. |
| [`actions.PushUrl(url)`](/v/0.4.0/reference/events/#citry-ext-events-actions-pushurl) | Add a browser history entry without navigating. |
| [`actions.ReplaceUrl(url)`](/v/0.4.0/reference/events/#citry-ext-events-actions-replaceurl) | Replace the current browser history URL without navigating. |
| [`actions.Download(...)`](/v/0.4.0/reference/events/#citry-ext-events-actions-download) | Download a file by itself. See [dedicated download responses](/v/0.4.0/events/http/#download-a-file-from-one-event). |
| `None` | Acknowledge the call without a visible action. |

### Choose Data or Dispatch for browser code

[`actions.Data`](/v/0.4.0/reference/events/#citry-ext-events-actions-data) is a one-call return value.
Browser code receives it only when it owns the Promise from an imperative
call:


```js
const result = await sendEvent("preview");
```


A declarative binding such as `@c-click="preview"` starts the same handler,
but the template does not receive that Promise or its Data value. Return
[`actions.Dispatch`](/v/0.4.0/reference/events/#citry-ext-events-actions-dispatch) when browser code must
react to the result of a declarative call. A handler may return both when it
supports both callers:


```python
return [
    actions.Data({"preview_id": preview.id}),
    actions.Dispatch(
        "Preview:ready",
        {"previewId": preview.id},
    ),
]
```


`Data` must settle the caller before later actions continue, so
`actions.Data(value, wait=False)` is rejected. A Data wire action does not
carry `wait`; receiving that field with either value is invalid. `delay`
remains available when the Promise should resolve later.

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
    c-item="item"
  />
</c-for>
```


Element and component keys operate at different levels. An element key only
matches within one sibling window. The same element key cannot move a node
between parents or nesting depths. This conditional changes depth, so the
input is recreated:


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


Component tags are virtual nodes bounded by Citry's ownership comments. Citry
matches their direct logical children top-down. It reserves keyed children by
`(component class, key)`, then pairs the remaining unkeyed positions. An
unkeyed pair keeps identity only when both positions hold the same component
class; Citry does not scan ahead for another same-class child. A keyed child
can therefore move across ordinary wrappers or change between single-root,
multi-root, text-only, and empty output while its component State remains
attached to that child. Use a key for insertion, deletion, or reorder. An
unmatched component is opaque: an equal key deeper inside it cannot leak out
and match elsewhere.

Element keys must be unique among the siblings that can compete. Component
keys must be unique among direct children of the same logical parent and
component class. If duplicate component keys occur, Citry warns and matches
them in invocation order.

`#c-key` needs a non-empty Python expression. You may put it directly on an
HTML element or component tag. An element key becomes `data-citry-key` on that
element. A component key stays on the component's virtual ownership range and
is never copied onto its rendered roots, so a child's own root may carry an
independent element `#c-key`. When the expression evaluates to `None`, Citry
records no key, exactly as if the flag were absent. This lets a component
expose an optional key as an ordinary input. `False`, `0`, and `""` remain
keys.

With `swap="morph"`, a matched component range keeps both logical State and
the physical DOM wherever the morph can preserve it. With `swap="replace"`,
the logical component and State still match by key, but all physical nodes and
range comments are replaced.

The flag cannot arrive through `c-bind`, and structural built-in tags such as
`<c-if>` reject it. Transparent component tags such as `<c-provide>` may carry
it: the key identifies their virtual comment-bounded range just like any other
component range. Equivalent caller-supplied slot regions inside a matched
component also morph their contents, so ordinary element keys keep working
there; an added, removed, or otherwise uncorrelated slot region is replaced
atomically. Put the key on the HTML or component node whose identity should
survive. For why a key belongs on the tag, read
[Template flags](/v/0.4.0/syntax/dynamic-attributes/#c-template-flags).

## Leave a browser-owned subtree alone

Some browser libraries take complete ownership of an element's descendants.
Put the bare `#c-ignore` marker on that element to keep a morph update from
changing it or anything inside it:


```citry-html
<div class="chart" #c-ignore>
  <canvas></canvas>
</div>
```


When an event response morphs an ancestor, Citry leaves this `<div>` and its
subtree as they are in the browser. Use this for a widget that has its own
rendering lifecycle, not for content that Citry should keep up to date.

`#c-ignore` takes no value and cannot be passed through `c-bind`. It may belong
to either an ordinary element subtree or a logical component range.

Write it on a component tag when the complete component should remain exactly
as it is in the browser:


```citry-html
<c-BrowserOwnedChart #c-ignore />
```


Citry retains the old comment-delimited range rather than copying the flag to
a rendered root. This works for single-root, multi-root, text-only, and empty
components and keeps their old DOM, State, props, callbacks, bindings, fills,
and dependencies together. Surrounding ranges and elements may still update.

A flag written on an HTML root inside the component's own template remains an
ordinary element flag. It keeps only that root subtree; sibling roots from the
same component can still update:


```citry-html
<div #c-ignore>
  <canvas></canvas>
</div>
<output>{{ status }}</output>
```


Citry uses the old rendered side as the policy source. Adding `#c-ignore` in a
new response takes effect on the following morph. Removing it from an already
ignored range is sticky—the old range is still retained—until the range is
removed, explicitly replaced, or stops corresponding because its class or key
changed. `swap="replace"` is explicit replacement and bypasses ignore.

If the caller only wants one physical wrapper kept, ordinary element ignore is
still appropriate:


```citry-html
<div #c-ignore>
  <c-BrowserOwnedChart />
</div>
```


For manually fetched HTML rather than an event result, see
[HTML fragments](/v/0.4.0/advanced/html-fragments/).