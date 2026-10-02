---
title: Event actions
description: Decide what the page does after a Citry event handler runs, from re-rendering the component to notifying browser code, redirecting, or downloading a file.
---

# Event actions

Your Python handler ran. Now the page should change: show the new data, swap
in a confirmation, tell other browser code what happened, change the URL, or
send a file. What the handler returns decides what the browser does next.

Return one value for one effect, or a list of values to apply in order:

| Return value | What the browser does |
|---|---|
| `MyComponent(...)` or `actions.Render(...)` | Re-renders the component whose handler ran, or puts a different component in its place. See [Re-render the component](#re-render-the-component). |
| `actions.Dispatch(name, detail)` | Fires a browser event that JavaScript can listen for. See [Notify browser code](#notify-browser-code-that-something-happened). |
| `dict` or `actions.Data(value)` | Gives the value to the JavaScript that called `$sendEvent`. See [Send data to JavaScript](#send-data-to-javascript). |
| `actions.Redirect(url)` | Navigates to another page. See [Redirect to a page](#redirect-to-a-page). |
| `actions.PushUrl(url)` / `actions.ReplaceUrl(url)` | Changes the address bar without loading a page. See [Change the URL](#change-the-url). |
| `actions.Download(...)` | Downloads a file. See [Download a file](#download-a-file). |
| `None` | Nothing visible. State changes still reach `$state`. See [Return nothing](#return-nothing). |

The examples below import the actions with
`from citry.ext.events import actions`.

## Re-render the component

Return the component with its new inputs. Citry renders it on the server and
the browser updates the component whose handler ran, in place:

```python
class Events:
    def add(self, data: TaskIn):
        create_task(data.title)
        return TaskList(tasks=load_tasks())
```

Returning `TaskList(...)` is the same as returning
`actions.Render(TaskList(...))`. Use the `actions.Render` form when you need
its options, such as `target` (below).

The new render gets only the inputs you pass. See
[Pass every input](/events/state/#pass-every-input-when-a-handler-renders-again).

## Keep list items matched { #keep-list-items-matched-to-their-records }

When a re-render adds, removes, or reorders list items, Vue matches the old
and new items by position unless they have a key. Without one, what the user
typed into a row, or a row's open or focused state, can end up on a different
record. Give each repeated item a key with `#c-key`:

```citry-html
<c-for each="item in items">
  <c-TaskRow
    #c-key="item.id"
    c-task="item"
  />
</c-for>
```

Use a value that identifies the record and stays the same between renders,
such as a database id or a slug. Keys must be unique within the list. Put the
key on the component or element that should follow the record.

A key works only among items under the same parent. It cannot move an item
into a different parent or wrapper element.

## Swap in a component { #swap-in-a-different-component }

A handler can return a different component from the one whose handler ran. The
new one takes its place. Here a handler on `SignupForm` swaps the form for a
`Confirmation`:

```python
class Events:
    def submit(self, data: SignupIn):
        save_signup(data.email)
        return Confirmation(email=data.email)
```

After the swap:

- **Nothing from the old component carries over.** What the user typed into
  `SignupForm` and its child components is gone. `Confirmation` starts fresh,
  so pass it everything it needs.
- **The parent's props, listeners, and `ref` for the old component do not
  apply.** The parent wrote them on `<c-SignupForm>`, so `Confirmation` does
  not receive them, and the `ref` reads `null`. Directives such as `v-show`
  stay with the place on the page, so they apply to `Confirmation`.
- **Reloading the page shows the original component again.** The swap happens
  only in the open browser tab.

!!! warning "The outermost component cannot be replaced"

    The component your Python code renders for the page (or for an HTML
    fragment you insert) cannot be swapped for a different one. The call
    fails with an error that names both components, and the page keeps the
    old one. With an `@c-*` call, the error appears in the browser console.
    Move the part that changes into a child component, or wrap it in a
    `<c-mark>` region as described next.

## Update part of the page { #update-one-part-of-the-page }

To replace only part of the component, wrap that part in `<c-mark>` with a
name:

```citry-html
<c-mark name="cart-badge">
  <c-CartBadge c-count="cart.count" />
</c-mark>
```

Then render into it with `target="mark:<name>"`:

```python
return actions.Render(
    CartBadge(count=cart.count),
    target="mark:cart-badge",
)
```

The name is looked up in the template of the component whose handler ran. To
update another component instead, use `target="render:<id>"`. The render ID
is the value of that component's `id` in the browser; see
[Browser APIs](/reference/browser-apis/).

## Notify browser code { #notify-browser-code-that-something-happened }

Sometimes other code in the browser needs to react to the handler: your
component's JavaScript shows a toast, or a header badge refreshes.
[`actions.Dispatch`][citry.ext.events.actions.Dispatch] fires a DOM
`CustomEvent` with that name and data:

```python
return actions.Dispatch("TaskRow:saved", {"title": title})
```

Start the name with your component's name, as in `TaskRow:saved`. Names that
start with `citry:` are reserved for Citry, so `actions.Dispatch` raises
`ValueError` for them.

The event starts at the first element of the component whose handler ran and
bubbles up to `document`. It fires once, even when the component has several
top-level elements.

In the component's own JavaScript, listen with the `onEvent` function that
`onServerRender` receives. Citry removes the listener before `onServerRender`
runs again and when the component unmounts:

```js
$component({
  onServerRender({ component, onEvent }) {
    onEvent("TaskRow:saved", (detail) => {
      component.showSaved(detail);
    });
  },
});
```

To hear the event anywhere else, such as in a parent component or page
script, listen on an ancestor element, on `document`, or with
[`Citry.events.on`](/reference/browser-apis/#citry-events-on).

## Send data to JavaScript

When your JavaScript calls a handler with `$sendEvent`, return a `dict` or
[`actions.Data`][citry.ext.events.actions.Data]:

```python
class Events:
    def count_matches(self, data: SearchIn):
        return {"count": count_tasks(data.query)}
```

The `$sendEvent` Promise resolves with that value:

```js
const result = await this.$sendEvent(
  "count_matches",
  {query: "invoice"},
);
console.log(result.count);
```

Wrap any other JSON value in `actions.Data(value)`. A bare list would be
read as a list of actions, so wrap a list too: `actions.Data(["a", "b"])`.
A handler can return at most one Data value; a second one makes the call
fail.

An `@c-*` attribute in a template does not receive the value. To let browser
code react to such a call, return `actions.Dispatch` instead.

## Redirect to a page

[`actions.Redirect`][citry.ext.events.actions.Redirect] makes the browser
load another page:

```python
class Events:
    def delete(self, data: DeleteIn):
        delete_project(data.id)
        return actions.Redirect("/projects/")
```

When a plain HTML form posts to the handler's URL, the same action becomes a
real HTTP redirect. See [Event routes](/events/routes/).

## Change the URL

[`actions.PushUrl`][citry.ext.events.actions.PushUrl] and
[`actions.ReplaceUrl`][citry.ext.events.actions.ReplaceUrl] change the
address bar without loading a page, for example so the open task has its
own link:

```python
class Events:
    def open_task(self, data: TaskRef):
        task = load_task(data.id)
        return [
            actions.Render(
                TaskDetail(task=task),
                target="mark:detail",
            ),
            actions.PushUrl(f"/tasks/{task.id}/"),
        ]
```

Use a same-origin URL that your server also serves, so a reload or a shared
link opens the same task.

`PushUrl` adds a history entry, so Back returns to the previous address.
`ReplaceUrl` replaces the current entry. Either way, Back and Forward change
only the address: Citry does not restore the earlier HTML or State.

## Download a file

Return [`actions.Download`][citry.ext.events.actions.Download] on its own,
and mark the handler with
[`@event(bundle=False)`][citry.ext.events.event]:

```python
from citry.ext.events import actions, event


class Events:
    @event(bundle=False)
    def export_orders(self):
        return actions.Download(
            make_orders_csv(),
            "orders.csv",
            content_type="text/csv; charset=utf-8",
        )
```

The file is the whole HTTP response. By default, the browser may send several
calls in one request; `bundle=False` makes it send this call on its own.

Call the handler as usual, from `@c-*`, `$sendEvent`, or
[`Citry.events.send`][Citry.events.send]. With `$sendEvent` or
`Citry.events.send`, the Promise resolves with `undefined` once the browser
starts saving the file.

A download cannot be combined with other actions in a list, and its handler
must not change State, because the file response has no room for the new
State. Either mistake makes the call fail.

## Return nothing

A handler that returns `None` does not re-render the component. Use it when
the handler only saves something, or only changes State:

```python
class Events:
    def toggle_editing(self, state):
        state.editing = not state.editing
```

The new State still reaches the browser, so Vue parts that read
`$state.editing` update. Server-rendered HTML stays as it was. Only fields
the browser can read reach `$state`; see
[Limit browser access](/events/state/#limit-what-the-browser-can-read-and-change).

## Run several actions { #return-several-actions-in-order }

Return a list to do several things. The browser applies the actions one at a
time, in list order, and each waits for the one before it. A Dispatch after a
Render therefore runs once the new HTML is on the page:

```python
tasks = load_tasks()
return [
    TaskList(tasks=tasks),
    actions.Dispatch("TaskList:changed", {"count": len(tasks)}),
]
```

Two options change the timing of any action except Download:

- `delay=<seconds>` waits before applying it.
- `wait=False` lets the actions after it start without waiting for it.
  `actions.Data` always waits, so `actions.Data(value, wait=False)` raises
  `ValueError`.

Here a toast appears at once and hides three seconds later:

```python
return [
    actions.Dispatch("Toast:show", {"text": "Saved"}),
    actions.Dispatch("Toast:hide", delay=3, wait=False),
]
```

A delay on an action that waits keeps the call running, so `$loading()`
stays true and later calls wait for it. Add `wait=False` to a
delayed action that only tidies up.

Put a Redirect last. Actions after it may not run before the browser leaves
the page. To show something first, give the Redirect a delay and
`wait=False`:

```python
return [
    actions.Dispatch("Toast:show", {"text": "Goodbye"}),
    actions.Redirect("/", delay=5, wait=False),
]
```

!!! note "Update several separate parts of the page in one response"

    You can update several separate parts of the page in one response by
    returning several Renders next to each other in the list. They must not
    have another action between them, use `delay` or `wait=False`, target
    the same place twice, or target both a component and something inside
    it. Otherwise the call fails and nothing on the page changes, although
    the handler has already run.

!!! note "A Dispatch before or after a Render reaches different listeners"

    When a response re-renders the component that listens, a Dispatch placed
    before the Render reaches the listeners of the old render. A Dispatch
    placed after it reaches the listeners that `onServerRender` added for
    the new render.

    If the Render replaces a component that contains the one whose handler
    ran, put the Dispatch first and do not give it `delay` or `wait=False`.
    Otherwise the call fails.
