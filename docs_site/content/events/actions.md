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
| `MyComponent(...)` or `actions.Render(...)` | Re-renders the component whose handler ran, or puts a different component in its place. See [`Render` the component](#re-render-the-component). |
| `actions.Dispatch(name, detail)` | Fires a browser event that JavaScript can listen for. See [`Dispatch` browser events](#notify-browser-code-that-something-happened). |
| `dict` or `actions.Data(value)` | Gives the value to the JavaScript that called `$sendEvent`. See [`Data` for JavaScript](#send-data-to-javascript). |
| `actions.Redirect(url)` | Navigates to another page. See [`Redirect` to a page](#redirect-to-a-page). |
| `actions.PushUrl(url)` / `actions.ReplaceUrl(url)` | Changes the address bar without loading a page. See [`PushUrl`, `ReplaceUrl`](#change-the-url). |
| `actions.Download(...)` | Downloads a file. See [`Download` a file](#download-a-file). |
| `None` | Nothing visible. State changes still reach `$state`. See [`None` skips re-render](#return-nothing). |

The examples below import the actions with
`from citry.ext.events import actions`.

## `Render` the component { #re-render-the-component }

Return the component with its new inputs. Citry renders it on the server and
the browser updates the component whose handler ran, in place:

```python
class Events:
    def add(self, data: TaskIn):
        create_task(data.title)
        tasks = load_tasks()
        return TaskList(tasks=tasks)
```

Returning `TaskList(...)` is the same as returning
`actions.Render(TaskList(...))`. Use the `actions.Render` form when you need
its options, such as `target` (below).

The new render gets only the inputs you pass. See
[Access State in handlers](/events/state/#access-state-in-handlers).
A value every render needs from the request, such as the current user,
can come from one app-wide function (experimental). See
[Pass request values](#give-every-render-the-request-values).

## `#c-key` for list items { #keep-list-items-matched-to-their-records }

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

## `Render` another component { #swap-in-a-different-component }

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

## `<c-mark>` partial update { #update-one-part-of-the-page }

To replace only part of the component, wrap that part in `<c-mark>` with a
name:

```citry-html
<c-mark name="cart-badge">
  <c-CartBadge c-count="cart.count" />
</c-mark>
```

Then render into it with `target="mark:<name>"`:

```python
badge = CartBadge(count=cart.count)
return actions.Render(badge, target="mark:cart-badge")
```

The name is looked up in the template of the component whose handler ran. To
update another component instead, use `target="render:<id>"`. The render ID
is the value of that component's `id` in the browser; see
[Browser APIs](/reference/browser-apis/).

## Pass request values { #give-every-render-the-request-values }

A page view often passes `render()` values from the request.
`template_globals={"user": user}` lets every template read `user`, and
`provides={"locale": locale}` lets any component read the locale with
[`inject()`](/concepts/provide-and-inject/) (see
[Add render-wide values](/concepts/rendering/#add-values-for-one-whole-render)).
A component that a handler returns gets neither, because no view renders
it. A template that reads `user` then fails the call with
`handler_error`.

A `_render_inputs` function fixes this. It returns the keyword
arguments Citry passes to `.render()` for each component a `Render`
renders: the same `template_globals=` and `provides=` you pass when you
render a component yourself. When the function returns this:

```python
{
    "template_globals": {"user": user},
    "provides": {"locale": user.locale},
}
```

Citry renders the returned component as if you had written:

```python
TaskList(tasks=tasks).render(
    template_globals={"user": user},
    provides={"locale": user.locale},
)
```

Citry calls the function with the call's
[`EventRequest`][citry.ext.events.EventRequest], the same object a
handler gets as its `request` parameter. Type its return value as
[`RenderInputs`][citry.ext.events.RenderInputs], so your type checker
checks the keys and their types. Set it for every component in
`extensions_defaults["events"]` (the leading `_` is part of the name,
as in the other Events options):

```python
from citry.ext.events import EventRequest, RenderInputs


def render_inputs(request: EventRequest) -> RenderInputs:
    # On Django, request.native is the HttpRequest.
    user = request.native.user
    return {
        "template_globals": {"user": user},
        "provides": {"locale": user.locale},
    }


citry = Citry(
    extensions_defaults={"events": {"_render_inputs": render_inputs}},
)
```

Or set it for one component on its `Events` class. Define the function
outside the class and assign it:

```citry
class TaskList(Component):
    class Events:
        _render_inputs = render_inputs

        def add(self, data: TaskIn):
            ...
```

The component's own value wins over the one in `extensions_defaults`.
Set `_render_inputs = None` on a component to turn the app-wide function
off for it.

!!! warning "Experimental"

    `_render_inputs` and `RenderInputs` are experimental. They may change
    in a minor release without a deprecation period.

Return either key or both. When a name is set in several places, a
component's `template_data()` wins over these globals, and these globals
win over the Citry instance's `template_globals`.

Citry calls the function once for each event call that returns a
component, after the handler has run (or after the extension that
answered the call). It uses the function of the component whose handler
ran, and every `Render` in that call gets the same values. That includes
a [`<c-mark>` update](#update-one-part-of-the-page) and a
[different component](#swap-in-a-different-component) the handler
returns. Citry does not call it:

- for a component the handler renders itself, such as
  `return Card(...).render(template_globals=...)`, which keeps the
  values the handler passed;
- for a call it rejects before the handler runs, such as one that fails
  the CSRF check or carries a State token that does not verify.

The function sees the event call, not the page request, so
`request.path` is the URL of the event route. A value your page view
builds from the page's path, such as the active link in a menu, comes
out different here. Keep such a value in
[State](/events/state/) instead.

Only your app's code sets this function; do not let request data choose
it. The values it returns may come from the request, as they can in a
page render, and a template escapes them when it prints them, like any
other value. A [cached component](/performance/caching/) that reads a
per-user value must name it in `Cache.vary()`, or it shows one user's
value to another.

Under Citry's ASGI adapter, including the FastAPI mount, Citry calls the
function on the event loop, where it also renders, even when the handler
is a plain `def`. A slow function delays every other request on that
server, so do not wait on slow I/O or query a database in it.

`Citry(...)` raises `ValueError` when the app-wide value is neither a
function nor `None`, is an `async def` function, or does not take
exactly one argument. Defining a component raises `ValueError` for the
same problems in its `Events` value, which includes a method written
inside the class, because a method also expects `self`.

The call fails with the error code `handler_error` when:

- the function raises;
- the function returns anything but a dict with the keys
  `template_globals` and `provides`, each a dict or `None`.

The handler has already run, so anything it saved stays saved. An
`EventError` raised by the function answers with its own status instead.

## `Dispatch` browser events { #notify-browser-code-that-something-happened }

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

!!! warning "Choose the event name yourself"

    Never build the name from request data (a query parameter, form
    field, or header). A name such as `click` or `submit` runs the
    page's own listeners for that event, including
    [`@c-*` bindings](/events/bindings/) that call the server. If the
    component's first element is a `<form>`, Firefox also submits that
    form to its `action` on a `submit` event, and a listener cannot
    cancel it.

## `Data` for JavaScript { #send-data-to-javascript }

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

## Skip the call queue { #skip-the-queue-for-a-read-only-call }

Calls from one Vue app go to the server one at a time, so a slow call
holds up the ones after it. A handler that only reads, such as a spell
check while the user types, can skip the line. Declare it with
[`@event(detached=True)`][citry.ext.events.event]:

```python
from citry.ext.events import event


class SpellCheckIn:
    text: str


class Events:
    @event(detached=True)
    def spell_check(self, data: SpellCheckIn):
        return {"typos": find_typos(data.text)}
```

Declaring the handler is not enough on its own: a call without
`wait: false` still waits its turn. Pass it where you send the call:

```js
const result = await this.$sendEvent(
  "spell_check",
  {text: this.draft},
  {wait: false},
);
```

This `wait` is an option of `$sendEvent`. It is not the `wait=False` that
actions take (see [Action lists](#return-several-actions-in-order)).

In exchange, a detached handler must leave the page and State as they are.
It may read State and return data, a `Dispatch`, a `Redirect`, a
`PushUrl` or `ReplaceUrl`, or a `Download` (which also needs
`bundle=False`). These calls fail:

- The handler returns a component or `actions.Render`, or changes State:
  the `$sendEvent` Promise rejects with a `handler_error`, and the server
  log names the handler. The handler has already run, so anything it
  saved stays saved.
- `wait: false` on a handler without `detached=True` rejects the Promise
  with a `TypeError` before anything is sent.

The handler reads State from the token the browser sends with the call.
Changes the browser has not sent yet are not in it: they stay in the
browser for the next call to a handler that is not detached, so pass text
the user is still typing as an argument, as above.

The server may run a detached call while another call from the same page
is running, so do not let the handler rely on what that call writes.

## `Redirect` to a page { #redirect-to-a-page }

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

The URL must use `http:` or `https:`, or have no scheme at all, as in
`/projects/` or `?page=2`. An empty URL, a URL with a control character,
or any other scheme raises `ValueError` when you create the action.

A relative URL, such as `"?page=2"` or `"next"`, is relative to the page
the visitor is on, with or without JavaScript. Without JavaScript, the
server reads that page's address from the `Referer` header, which browsers
send by default. A `<base href>` element on the page does not change
where a relative URL leads. Use a path that starts with `/` instead when
your page sets a `Referrer-Policy` that stops the browser sending the full
address. With no `Referer`, the visitor lands next to the handler's URL,
usually on a "not found" page, and for a form that posts, the server logs
a warning. With only the site's address, the URL resolves against the
home page, with no warning.

!!! warning "Check a URL that comes from the request"

    A URL taken from the request, such as a `next` parameter, can point to
    another site. Check it before you redirect to it. A prefix check such
    as `url.startswith("/")` is not enough, because browsers treat
    `//other.example` and `/\other.example` as addresses on another site.
    [`local_url_or()`][citry.ext.events.local_url_or] reads the URL the
    way a browser does and swaps one that leaves your site for a fallback:
    `actions.Redirect(local_url_or(data.next, "/"))`. See
    [Check redirect URLs](/security/#check-redirect-urls).

If a redirect with another scheme reaches the browser another way, such
as through browser code you wrote that calls `Citry.events.applyActions()`,
the browser stays on the page and the call fails: the Promise that
`applyActions()` returns rejects with an error that says why. A redirect
action marked `wait: false` does not hold up the call, so its error
cannot reach the Promise: Citry logs it to the console and the Promise
resolves.

## `PushUrl`, `ReplaceUrl` { #change-the-url }

[`actions.PushUrl`][citry.ext.events.actions.PushUrl] and
[`actions.ReplaceUrl`][citry.ext.events.actions.ReplaceUrl] change the
address bar without loading a page, for example so the open task has its
own link:

```python
class Events:
    def open_task(self, data: TaskRef):
        task = load_task(data.id)
        detail = TaskDetail(task=task)
        return [
            actions.Render(detail, target="mark:detail"),
            actions.PushUrl(f"/tasks/{task.id}/"),
        ]
```

Use a same-origin URL that your server also serves, so a reload or a shared
link opens the same task.

`PushUrl` adds a history entry, so Back returns to the previous address.
`ReplaceUrl` replaces the current entry. Either way, Back and Forward change
only the address: Citry does not restore the earlier HTML or State.

## `Download` a file { #download-a-file }

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

## Send your own response { #send-your-own-response }

A `bundle=False` handler can return a
[`RouteResponse`][citry.RouteResponse] to set the status, headers, and
body itself. Like a download, it must leave State unchanged. Citry does
not check the header names, header values, or `content_type` you give
it, and not every web server refuses a line break (`\r` or `\n`) in a
header. Reject line breaks and other control characters in any value
that comes from request data.

## `None` skips re-render { #return-nothing }

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
[`_public`](/events/state/#public) and [`_model`](/events/state/#model).

## Action lists { #return-several-actions-in-order }

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

A delayed action is dropped when the page applies a newer result for the
same component first. It is also dropped when the component is removed.
If the same component makes another call within those three seconds, the
old `Toast:hide` does not run, so that call's handler should return its
own `Toast:hide`. A delayed Redirect is the exception to the newer-result
rule: it still runs.

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
