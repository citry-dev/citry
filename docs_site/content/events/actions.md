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

The Vue Events renderer addresses a component occurrence or an explicit marker
and applies a morph. Omitting `target` selects the calling instance. Use a
known `render:<id>` address for another component occurrence or a caller-relative
`mark:<name>` address for a marker. CSS selectors and other swap modes are not
supported. A component element returned directly is equivalent to
`actions.Render(element)`.

One response may update several independent targets when their Render actions
form one contiguous group. Every action in that group must be immediate and
blocking: omit `delay` or use `0`, and do not set `wait=False`. Interleaving
another action, deferring a Render, targeting the same occurrence twice, or
targeting overlapping ancestor and descendant occurrences is rejected before
the response changes State or the page.

## Dispatch a browser event

[`actions.Dispatch`][citry.ext.events.actions.Dispatch] sends one bubbling DOM
`CustomEvent` under the exact given name. It starts at the calling instance's
first connected element in its current Vue subtree, falling back to its
connected Vue root node when the subtree has no element. A multi-root component
uses one canonical carrier, so a document listener receives it once.
Dispatch is targeted to the component occurrence that invoked the server
handler; it does not select an arbitrary component or CSS target.

```python
return actions.Dispatch("task-row:saved", {"title": title})
```

Listen on the carrier or a DOM ancestor. For component lifecycle work, install
the listener in `onServerRender` and return cleanup:

```js
$component({
  onServerRender({ component }) {
    const root = component.$el;
    const receive = event => component.showSaved(event.detail);
    root.addEventListener('task-row:saved', receive);
    return () => root.removeEventListener('task-row:saved', receive);
  },
});
```

## Return actions in order

| Return value | Browser result |
|---|---|
| `MyComponent(...)` or `actions.Render(...)` | Morph the calling component. |
| `dict` or `actions.Data(value)` | Resolve an imperative `$sendEvent` Promise. |
| `actions.Dispatch(name, detail)` | Dispatch a bubbling browser event. |
| `actions.Redirect(url)` | Navigate. |
| `actions.PushUrl(url)` / `actions.ReplaceUrl(url)` | Change browser history without navigation. |
| `actions.Download(...)` | Download from an unbundled handler. |
| `None` | Acknowledge the call. |

A declarative `@c-*` binding does not expose a Data result. Use `$sendEvent`
when browser code owns the Promise. Use Dispatch when a declarative call must
notify a listener. Order matters when one action rerenders the listener: dispatch
first when the old subtree must hear the event.

## Preserve identity in rendered lists

Vue matches unkeyed siblings by position. Give repeated items a stable
application key so surviving component and element instances correspond to the
same domain record after the calling component morphs:

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
