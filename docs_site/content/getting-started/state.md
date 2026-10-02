---
title: Keep values between calls
description: Carry signed State between Python calls and read it from Vue.
---

# Keep values between calls

An event handler often needs to remember something from the last call: which
page of results it showed, which filter is on, how many items it loaded. The
handler does not keep anything between calls on its own. In this step, a
counter survives from one call to the next, so Python can load a different
batch of choices on each click.

Citry keeps such values in the component's **State**. Citry sends State to
the browser with the rendered component, and the browser sends it back with
the next call.

## Replace the components

Replace `components.py` with:

<c-include-file path="docs_site/snippets/getting_started/components_step10.py" language="citry" />

Click “Load choices” twice. The first call loads “Ocean” and “Forest”; the
second loads “History” and “Science.” “Sets loaded” goes from one to two.
Reloading the page starts over.

## Declare State

```python
class Kwargs:
    batches_loaded: int = 0

class State:
    batches_loaded: int = 0
```

[`Kwargs`][citry.Component.Kwargs] are the inputs for one render.
[`State`][citry.Component.State] holds the values that event handlers
receive on each call. On the first render, Citry fills each State field from
the input with the same name. A field with no matching input uses its own
default.

When every input should be kept, make `State` inherit from `Kwargs` instead:

```python
class State(Kwargs):
    pass
```

Keep the two classes separate when some inputs should not go to the browser.
When names differ or a value must be computed, fill State with
`state_data()`, as [Event state](/events/state/) shows.

## Read and change State in a handler

```python
class Events:
    def load_choices(self, state):
        choices = load_choices_from_database(state.batches_loaded)
        state.batches_loaded += 1
        return actions.Dispatch(
            "ChoicePicker:loaded",
            {"choices": choices},
        )
```

The handler receives State through its `state` parameter. The first call
gets zero, loads batch zero, and sets the value to one. Citry sends the
changed State back with the response, so the next call gets one.

## Show State in the browser

The template reads State through `$state`:

```citry-html
<output v-text="$state.batches_loaded">{{ batches_loaded }}</output>
```

Python renders the starting value inside the tag. After each call that
changes State, `$state.batches_loaded` updates, and Vue shows the new value.

The list of choices stays in ordinary Vue data, because Python does not need
the browser's current choice on its next call.

!!! note "Changing State from the browser"

    Browser code can also assign a whole field, as in
    `$state.batches_loaded = 0`. The page shows the new value at once, but
    the assignment does not send a request: Citry sends the value with the
    component's next event call (calls sent as GET requests are the
    exception). You cannot assign a nested value, or a field that `State`
    does not let the browser change. See
    [`$state`](/reference/browser-apis/#state) for the full rules.

## Keep secrets out of State

State is signed, not secret. Citry signs it with `CITRY_SECRET` so it can
tell when someone has changed it, but anyone who opens the page can read the
values. Signing also does not identify the user or grant permission.

Never put passwords or API keys in State, and check access inside each event
handler. In production, every worker needs the same `CITRY_SECRET`.

## Next steps

Next, [handle and validate forms](/getting-started/forms/).
