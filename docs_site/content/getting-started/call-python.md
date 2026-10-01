---
title: Call Python from a click
description: Send a click to a Python event handler and show its answer without reloading the page.
---

# Call Python from a click

Now add a button that reaches a Python handler through Citry's mounted routes.
Python will load the picker choices without reloading the page.

Replace `components.py` with this version:

<c-include-file path="docs_site/snippets/getting_started/components_step9.py" language="citry" />

Keep `citry_setup.py` and `app.py` unchanged. Open
`http://127.0.0.1:8000/` and select “Load choices.”

## Send the click to Python

```citry-html
<button type="button" @c-click="load_choices">Load choices</button>
```

`@click` handles a browser interaction in Vue. Citry reserves `@c-*` bindings
for [server events](/events/bindings/). Here `@c-click` sends a request to the
mounted Citry route and calls `ChoicePicker.Events.load_choices`.

Treat all event input as untrusted. Authenticate the caller and check
permissions in the handler just as you would in any route.

## Return a browser event

```python
class Events:
    def load_choices(self):
        choices = load_choices_from_database()
        return actions.Dispatch(
            "ChoicePicker:loaded",
            {"choices": choices},
        )
```

[`actions.Dispatch`][citry.ext.events.actions.Dispatch] asks the browser to
fire an event with that name and JSON detail. Start the name with the
component's name, as in `ChoicePicker:loaded`, so it does not clash with events
from other components. Citry rejects names that start with `citry:`, because
its own browser events use that prefix.

The event fires on the calling component's first element and bubbles up the
page, so ordinary page scripts can listen for it too. Inside the component,
listen with [`onEvent`][onEvent] instead. Citry passes that function to
[`onServerRender`][onServerRender], a `$component` option that runs after the
component mounts and again after each server render. `onEvent` hears only
events that this component's own Python handlers dispatch, and passes your
callback the event detail:

```js
onServerRender({ component, onEvent }) {
  // Citry removes this listener before onServerRender
  // runs again and when the component unmounts.
  onEvent('ChoicePicker:loaded', (detail) => {
    component.loadChoices(detail.choices);
  });
}
```

The method stores the list and first choice:

```js
$component({
  data() {
    return { choices: [], choice: '' };
  },
  methods: {
    loadChoices(newChoices) {
      this.choices = newChoices;
      this.choice = newChoices[0];
    },
  },
});
```

The child receives the selected label through `:label` and emits
`select` to ask the parent to advance it. No HTML replacement is needed.

`@c-click` starts the call without exposing its Promise result. When component
code needs a returned [`actions.Data`][citry.ext.events.actions.Data] value,
call [`$sendEvent`][$sendEvent] instead.

## Loading state

`:disabled="$loading('load_choices')"` disables the button during the call,
and `v-show="$loading('load_choices')"` shows its progress text. Both values
are scoped to this component instance.

## Next steps

Next, [carry state between Python calls](/getting-started/state/).
