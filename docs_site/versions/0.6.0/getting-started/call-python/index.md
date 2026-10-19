---
title: Call Python from a click
url: https://citry.dev/v/0.6.0/getting-started/call-python/
description: "Send a click to a Python event handler and show its answer without reloading the page."
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

```citry
from citry_setup import citry_app

from citry import Component
from citry.ext.events import actions


# New in this step: stand in for a database query.
def load_choices_from_database() -> list[str]:
    return ["Ocean", "Forest"]


class ChoiceButton(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <button
        class="choice-button"
        type="button"
        @click="$emit('select')"
      >
        Choose
        <span
          class="choice-button__label"
          v-text="label"
        ></span>
      </button>
    """

    js = """
      $component({
        props: {
          label: { type: String, required: true },
        },
        emits: ['select'],
      });
    """


class ChoicePicker(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    # New in this step: handle the button click in Python.
    class Events:
        # Method name matches @c-click.
        def load_choices(self):
            choices = load_choices_from_database()
            # Tell the client to dispatch a custom browser event
            # with the loaded choices.
            return actions.Dispatch(
                "ChoicePicker:loaded",
                {"choices": choices},
            )

    template = """
      <section class="choice-picker">
        {# New in this step: ask Python for the choices. #}
        <button
          type="button"
          :disabled="$loading('load_choices')"
          @c-click="load_choices"
        >
          Load choices
        </button>
        <span v-show="$loading('load_choices')">Loading...</span>

        <p v-show="choices.length === 0">
          No choices loaded yet.
        </p>
        <div v-show="choices.length > 0">
          <p>
            Current choice:
            <output
              class="choice-picker__value"
              v-text="choice"
            ></output>
          </p>

          {# New in this step: cycle through the loaded choices. #}
          <c-ChoiceButton
            :label="choice"
            @select="setNextChoice"
          />
        </div>
      </section>
    """

    js = """
      $component({
        data() {
          return { choices: [], choice: '' };
        },
        methods: {
          setNextChoice() {
            const oldChoiceIndex = this.choices.indexOf(this.choice);
            this.choice = this.choices[
              (oldChoiceIndex + 1) % this.choices.length
            ];
          },
          loadChoices(newChoices) {
            this.choices = newChoices;
            this.choice = newChoices[0];
          },
        },
        onServerRender({ component, onEvent }) {
          // Citry removes this listener before onServerRender
          // runs again and when the component unmounts.
          onEvent('ChoicePicker:loaded', (detail) => {
            component.loadChoices(detail.choices);
          });
        },
      });
    """


class TutorialPage(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Reading room</title>
        </head>
        <body>
          <main>
            <h1>Reading room</h1>
            <c-ChoicePicker />
          </main>
        </body>
      </html>
    """

```

Keep `citry_setup.py` and `app.py` as they are. Open
`http://127.0.0.1:8000/` and click “Load choices.”

## Send clicks to Python


```citry-html
<button type="button" @c-click="load_choices">Load choices</button>
```


Vue's `@click` runs code in the browser. Citry's `@c-click` sends the click
to the server and runs the event handler with that name,
`ChoicePicker.Events.load_choices`. Other browser events work the same way
with an `@c-` prefix, as [Bind events in templates](/v/0.6.0/events/bindings/) shows.

!!! warning "Check permissions in every event handler"

    Anyone can send a request to an event handler, just as they can to any
    route, so treat everything it receives as untrusted. Check who the
    user is and what they may do inside the handler.

## Send the result back

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


[`actions.Dispatch`](/v/0.6.0/reference/events/#citry-ext-events-actions-dispatch) tells the browser to
fire an event with that name, and attach the dictionary as the event's
`detail`. The dictionary must be JSON-serializable. Start the name with the
component's name, as in `ChoicePicker:loaded`, so it does not clash with
events from other components.

## Listen for the result

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


[`onServerRender`](/v/0.6.0/reference/browser-apis/#on-server-render) is a `$component` option. Citry runs it
when the component first appears on the page, and again each time Python
sends new HTML for the component. It receives [`onEvent`](/v/0.6.0/reference/browser-apis/#on-server-render-on-event), which
listens only for events dispatched by this component's own Python handlers, and passes your
callback the event's `detail`.

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

!!! note "Other ways to get a result back"

    `@c-click` does not give your JavaScript the handler's return value.
    When component code needs a value back, call
    [`$sendEvent`](/v/0.6.0/reference/browser-apis/#send-event) and return
    [`actions.Data`](/v/0.6.0/reference/events/#citry-ext-events-actions-data) from the handler.

    The dispatched event also bubbles up the page from the component's
    first element, so page scripts outside the component can listen for
    it. Event names that start with `citry:` are reserved for Citry's own
    events, and `actions.Dispatch` rejects them.

## Show progress

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


While this component's `load_choices` call runs, the button is disabled
and the “Loading...” text shows.

## Next steps

Next, [keep values between Python calls](/v/0.6.0/getting-started/state/).