---
title: Call Python from a click
description: Send a click to a Python event handler and show its answer without reloading the page.
---

# Call Python from a click

Some clicks need the server: load records from a database, save a change,
check a permission. In this step a "Load choices" button runs a Python
method, and the picker shows the choices Python sends back, without
reloading the page.

A Python method that the browser can call this way is an **event handler**.
You put event handlers in a nested `class Events` on the component.

## Replace the components

Replace `components.py` with this version:

<c-include-file path="docs_site/snippets/getting_started/components_step9.py" language="citry" />

Keep `citry_setup.py` and `app.py` as they are. Open
`http://127.0.0.1:8000/` and click “Load choices.”

## Send the click to Python

```citry-html
<button type="button" @c-click="load_choices">Load choices</button>
```

Vue's `@click` runs code in the browser. Citry's `@c-click` sends the click
to the server and runs the event handler with that name,
`ChoicePicker.Events.load_choices`. Other browser events work the same way
with an `@c-` prefix, as [Bind events in templates](/events/bindings/) shows.

!!! warning "Check permissions in every event handler"

    Anyone can send a request to an event handler, just as they can to any
    route, so treat everything it receives as untrusted. Check who the
    user is and what they may do inside the handler.

## Send the result back to the browser

The handler loads the choices and returns a browser event that carries them:

```python
class Events:
    def load_choices(self):
        choices = load_choices_from_database()
        return actions.Dispatch(
            "ChoicePicker:loaded",
            {"choices": choices},
        )
```

[`actions.Dispatch`][citry.ext.events.actions.Dispatch] tells the browser to
fire an event with that name, and attach the dictionary as the event's
details. Start the name with the component's name, as in
`ChoicePicker:loaded`, so it does not clash with events from other
components.

## Listen for the result in the component

The component listens for that event in its JavaScript:

```js
onServerRender({ component, onEvent }) {
  // Citry removes this listener before onServerRender
  // runs again and when the component unmounts.
  onEvent('ChoicePicker:loaded', (detail) => {
    component.loadChoices(detail.choices);
  });
}
```

[`onServerRender`][onServerRender] is a `$component` option. Citry runs it
when the component mounts and again each time the server renders the
component anew. It receives [`onEvent`][onEvent], which listens only for
events dispatched by this component's own Python handlers, and passes your
callback the event's details.

`loadChoices` stores the list and selects the first choice:

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

From there, the browser does the rest, as in the earlier steps: the
`<c-ChoiceButton>` child shows the current choice through `:label`, and its
`select` event moves to the next choice. Python does not render new HTML.

## Show progress while Python works

`$loading('load_choices')` is true while the call is running:

```citry-html
<button
  type="button"
  :disabled="$loading('load_choices')"
  @c-click="load_choices"
>
  Load choices
</button>
<span v-show="$loading('load_choices')">Loading...</span>
```

The button is disabled and shows its loading text only while this
component's `load_choices` call is running.

!!! note "Other ways to get a result back"

    `@c-click` does not give your JavaScript the handler's return value.
    When component code needs a value back, call
    [`$sendEvent`][$sendEvent] and return
    [`actions.Data`][citry.ext.events.actions.Data] from the handler.

    The dispatched event also bubbles up the page from the component's
    first element, so page scripts outside the component can listen for
    it. Event names that start with `citry:` are reserved for Citry's own
    events, and `actions.Dispatch` rejects them.

## Next steps

Next, [keep values between Python calls](/getting-started/state/).
