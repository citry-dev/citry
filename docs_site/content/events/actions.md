---
title: Event actions
description: Return Citry event actions in order, rerender the calling component, and notify browser code.
---

# Event actions

An event handler can rerender its calling component, return data, dispatch a
browser event, change browser history, or navigate. Return one result for one
effect, or a list when effects must happen in order.

## Rerender the calling component

```python
class Events:
    def refresh(self):
        return actions.Render(TaskList(tasks=load_tasks()))
```

A Render action updates one component on the page or an explicit marker in
place. Omitting `target` selects the calling instance. Use a known
`render:<id>` address for another component on the page or a caller-relative
`mark:<name>` address for a marker. A component element returned directly is
equivalent to `actions.Render(element)`.

One response may update several independent targets when their Render actions
form one contiguous group. Every action in that group must be immediate and
blocking: omit `delay` or use `0`, and do not set `wait=False`. Otherwise
the call fails and nothing on the page changes: the browser rejects a
response that puts another action between two Renders, defers one of them,
targets the same component instance twice, or targets both a component and a
component inside it. The handler has already run by then, so any database
writes it made stay. The server does not check the order or targets of
these Render actions, so assert the returned list in a test of the handler.

## Dispatch a browser event

[`actions.Dispatch`][citry.ext.events.actions.Dispatch] sends one bubbling DOM
`CustomEvent` under the exact given name. The event starts at the first
element of the component that called the handler and bubbles up through its
ancestors to `document`. A component with several top-level elements fires it
once, from the first of them, so a listener on `document` hears it once. When
the component renders no element, the event starts at the component's root
DOM node instead. Dispatch always starts at the calling component; it cannot
select another component.

Prefix the event name with the component name, as in `TaskRow:saved`. Names
that start with `citry:` belong to Citry's own events, so `actions.Dispatch`
raises `ValueError` for them.

```python
return actions.Dispatch("TaskRow:saved", {"title": title})
```

Inside the component's own JavaScript, listen with the `onEvent` function
that `onServerRender` receives. It hears the Dispatch actions that this
component's own handlers return. Citry removes the listener before
`onServerRender` runs again and when the component unmounts:

```js
$component({
  onServerRender({ component, onEvent }) {
    onEvent("TaskRow:saved", (detail) => {
      component.showSaved(detail);
    });
  },
});
```

To hear a Dispatch from a child component, or from code outside the
component, listen on an ancestor element, on `document`, or with
[`Citry.events.on`](/reference/browser-apis/#citry-events-on).

## Return actions in order

| Return value | Browser result |
|---|---|
| `MyComponent(...)` or `actions.Render(...)` | Update the calling component in place. |
| `dict` or `actions.Data(value)` | Resolve an imperative `$sendEvent` Promise. |
| `actions.Dispatch(name, detail)` | Dispatch a bubbling browser event. |
| `actions.Redirect(url)` | Navigate. |
| `actions.PushUrl(url)` / `actions.ReplaceUrl(url)` | Change browser history without navigation. |
| `actions.Download(...)` | Download a file. The handler must use `@event(bundle=False)`; see [Download a file from one event](/events/http/#download-a-file-from-one-event). |
| `None` | Acknowledge the call. State the handler changed still reaches `$state`. |

The browser applies a list of actions one at a time, in list order. Each
action waits for the one before it, so a Dispatch placed after a Render runs
once the new HTML is on the page. Give an action `delay=<seconds>` to wait
before applying it, or `wait=False` to let the actions after it start without
waiting for it. `actions.Data` always waits, because it resolves the caller's
Promise, so `actions.Data(value, wait=False)` raises `ValueError`.

Order decides which listeners hear a Dispatch when the same response
rerenders the component that listens. A Dispatch placed before the Render
reaches the listeners of the current render. A Dispatch placed after it
reaches the listeners that `onServerRender` added when it ran for the new
render, before its first `await`. When the Render targets a component that
contains the caller, put the Dispatch before the Render, without `delay` or
`wait=False`; otherwise the browser rejects the whole response.

Actions after a Redirect race the navigation, so put the Redirect last, or
give it `delay` and `wait=False` when something must show first:
`actions.Redirect(url, delay=5, wait=False)`.

A declarative `@c-*` binding does not expose a Data result. Use `$sendEvent`
when browser code owns the Promise. Use Dispatch when a declarative call must
notify a listener.

## Preserve identity in rendered lists

Vue matches unkeyed siblings by position. Give repeated items a stable
application key so surviving component and element instances correspond to the
same domain record after the calling component renders again:

```citry-html
<c-for each="item in items">
  <c-TaskRow
    #c-key="item.id"
    c-task="item"
  />
</c-for>
```

Use a database primary key, stable slug, or another domain identifier. Do not
use a Citry occurrence ID, which belongs to one render. Keys must be unique
among the repeated siblings that can compete with one another. Put the key on
the component or element whose identity should follow the record.

An Events update can address the calling component, another component
occurrence, or an explicit marker. Do not rely on a key to move browser-owned
DOM across arbitrary wrappers, parents, or nesting depths. Keep a keyed item at
the same structural position across renders.
