---
title: Call Python from a click
url: https://citry.dev/v/0.3.0/getting-started/call-python/
description: "Send a click to a Python event handler and show its answer without reloading the page."
---
# Call Python from a click

Your FastAPI app can render the page. Now you will add a button that reaches a
Python handler through Citry's mounted routes. Python will load the choice
picker's options without reloading the page.

Start with [Serve the page with FastAPI](/v/0.3.0/getting-started/fastapi/) if the app
is not already running.

## Load the choices from Python

Replace `components.py` with this version:

Look for the `New in this step` comments. This version:

- adds the database stand-in `load_choices_from_database()`
- adds the Python handler `ChoicePicker.Events.load_choices()`
- changes the picker so it starts empty and
fills itself from the handler's browser event.

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
      <button class="choice-button" type="button">
        Choose
        <span
          class="choice-button__label"
          x-text="clientProps.label"
        ></span>
      </button>
    """

    js = """
      $component({
        props: {
          label: { type: String, required: true },
        },
        init: ({ props, scope }) => {
          scope.clientProps = props;
        },
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
                "choice-picker:loaded",
                {"choices": choices},
            )

    template = """
      <section
        class="choice-picker"
        x-data="{
          choices: [],
          choice: '',
          setNextChoice() {
            const choices = this.choices;
            const oldChoiceIndex = choices.indexOf(this.choice);
            const nextChoiceIndex =
              (oldChoiceIndex + 1) % choices.length;
            this.choice = choices[nextChoiceIndex];
          },
          loadChoices(newChoices) {
            this.choices = newChoices;
            this.choice = newChoices[0];
          },
        }"
        @choice-picker:loaded="loadChoices($event.detail.choices)"
      >
        {# New in this step: ask Python for the choices. #}
        <button
          type="button"
          :disabled="$loading('load_choices')"
          @c-click="load_choices"
        >
          Load choices
        </button>
        <span x-show="$loading('load_choices')">Loading...</span>

        <p x-show="choices.length === 0">
          No choices loaded yet.
        </p>
        <div x-show="choices.length > 0">
          <p>
            Current choice:
            <output
              class="choice-picker__value"
              x-text="choice"
            ></output>
          </p>

          {# New in this step: cycle through the loaded choices. #}
          <c-ChoiceButton
            $c-props="{ label: choice }"
            @click="setNextChoice"
          />
        </div>
      </section>
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

Keep `citry_setup.py` and `app.py` unchanged. Uvicorn should reload the app
after you save the file.

Open `http://127.0.0.1:8000/` and click “Load choices.” The empty picker fills
with the two choices. Its existing child button can then move between them in
the browser.

## Send the click to Python

This is the line that turns an ordinary button into a server-handled action:


```citry-html
<button type="button" @c-click="load_choices">
  Load choices
</button>
```


The Alpine `@click` from the previous lesson runs JavaScript in the browser.
Citry uses the `@c-*` prefix for events that are meant to be [handled by the server](/v/0.3.0/events/bindings/).

When you click on the button with `@c-click`:

1. Alpine detects the `click` event and hands it over to Citry JS client.
2. Citry JS client sends request to the server (the FastAPI app). The payload includes which component (`ChoicePicker`) and which event was triggered (`load_choices`).
3. On the server, the routes that were installed when we mounted Citry onto FastAPI will pick up this request (`/citry/...`).
3. Citry's routing passes the request and event data to `load_choices()` event handler on the `ChoicePicker` component.

Because the page and Citry routes share the application, this request stays on the same origin.

!!! warning

    **DO NOT** blindly trust data in event handlers - anyone can send events. Your application still
    needs to authenticate people and check their permissions inside handlers. See
    [Security](/v/0.3.0/security/) for the complete trust boundaries.

## Run the matching Python method

The handler lives in the component's nested [`Events`](/v/0.3.0/reference/events/#citry-events) class:


```python
class Events:
    def load_choices(self):
        choices = load_choices_from_database()
        return actions.Dispatch(
            "choice-picker:loaded",
            {"choices": choices},
        )
```


Public methods in `Events` are handlers the browser can call. Here,
`load_choices` matches the name on the button.

The small function above the components stands in for your application's data
access:


```python
def load_choices_from_database() -> list[str]:
    return ["Ocean", "Forest"]
```


The page starts without those choices. This function runs only after the
button calls the handler. In a real application, this is where you might query
a database or call another Python service.

## Return the answer into Alpine

The handler returns an
[`actions.Dispatch(...)`](/v/0.3.0/reference/events/#citry-ext-events-actions-dispatch) action:


```python
return actions.Dispatch(
    "choice-picker:loaded",
    {"choices": choices},
)
```


This tells the browser to fire an event named `choice-picker:loaded`. The
second argument becomes that event's `detail`, so the returned list is
available as `$event.detail.choices`. Values in `detail` must be
JSON-serializable because they travel from Python to browser code.

The picker defines a small Alpine method for storing the result:


```javascript
loadChoices(newChoices) {
  this.choices = newChoices;
  this.choice = newChoices[0];
}
```


Its listener calls that method when the matching event arrives:


```citry-html
@choice-picker:loaded="loadChoices($event.detail.choices)"
```


When the event arrives, Alpine stores the whole list and selects its first
item. Citry fires the event on the calling picker's root, where this listener
can receive it. The existing `$c-props` connection then passes that selected
label to `ChoiceButton`. No HTML needs to be replaced.

## Show when Python is working

The full button also uses the Citry-specific Alpine magic [`$loading('load_choices')`](/v/0.3.0/reference/browser-apis/#loading):


```citry-html
<button
  type="button"
  :disabled="$loading('load_choices')"
  @c-click="load_choices"
>
  Load choices
</button>
<span x-show="$loading('load_choices')">
  Loading...
</span>
```


`$loading('load_choices')` is true while that handler call is in progress.
During a slower real query, the button becomes disabled and the loading message
appears. Both return to normal when the call finishes.

## Keep later choices in the browser

After Python supplies the list, another Alpine method finds the next choice:


```javascript
setNextChoice() {
  const choices = this.choices;
  const oldChoiceIndex = choices.indexOf(this.choice);
  const nextChoiceIndex =
    (oldChoiceIndex + 1) % choices.length;
  this.choice = choices[nextChoiceIndex];
}
```


The child button calls that method with an ordinary browser click:


```citry-html
<c-ChoiceButton
  $c-props="{ label: choice }"
  @click="setNextChoice"
/>
```


This uses Alpine's `@click`, so moving from “Ocean” to “Forest” does not make
another server call. The page now uses Python when it needs data and browser
code when the interaction can stay local.

## Each server call starts fresh

This first handler is stateless. Each click calls
`load_choices_from_database()` again and returns the same set. Python does not
remember that the page loaded it before. Alpine can still move between those
choices in the browser.

Here, stateless means the component has no Citry State carried from one call to
the next. A real handler can still read persistent application data from a
database, session, or another service.

That makes this pattern a good fit for refreshing a result or asking the
server for the latest version of some data. The next lesson adds State so
Python can continue from an earlier call.

Continue with [event bindings](/v/0.3.0/events/bindings/) for loading and errors, or
[event actions](/v/0.3.0/events/actions/) for the other ways a handler can update the
page.

## Remember the next call

The browser can now reach Python and receive a result. Next, [keep a value
between calls](/getting-started/state/).