---
title: Events state
url: https://citry.dev/v/0.4.2/getting-started/state/
description: "Add signed Citry State so Python can load the next set of choices on each call."
---
# Events state

The last handler ran the same database query on every click. This time Python
will remember server-side state across calls, so we can count how many times we called the endpoint.

Continue from [Call Python from a
click](/getting-started/call-python/). Keep `citry_setup.py` and `app.py`
unchanged.

## Add server-side state

Replace `components.py` with this version:

The `New in this step` comments point to four changes:

- `load_choices_from_database` returns one of the two choice batches
- a starting counter `Kwargs.batches_loaded`
- the [`State`](/v/0.4.2/reference/component/#citry-component-state) declaration and stateful handler
- the count shown in the browser

```citry
from citry_setup import citry_app

from citry import Component
from citry.ext.events import actions

# New in this step: simulate two database query results.
# Based on value from State, we return one of these two
# batches of choices.
CHOICE_BATCHES = (
    ("Ocean", "Forest"),
    ("History", "Science"),
)


def load_choices_from_database(batch: int) -> list[str]:
    choices = CHOICE_BATCHES[batch % len(CHOICE_BATCHES)]
    return list(choices)


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

    # New in this step: set the counter for the first render.
    class Kwargs:
        batches_loaded: int = 0

    class Slots:
        pass

    # New in this step: carry the counter between Python calls.
    class State:
        batches_loaded: int = 0

    class Events:
        def load_choices(self, state):
            # New in this step: read and advance the signed State.
            # NOTE: State is passed to the event handler.
            #       You can mutate the State, and it will be
            #       signed and sent back to the client.
            choices = load_choices_from_database(state.batches_loaded)
            state.batches_loaded += 1

            return actions.Dispatch(
                "choice-picker:loaded",
                {
                    "choices": choices,
                    "batches_loaded": state.batches_loaded,
                },
            )

    template = """
      {# New in this step: pass Python `batches_loaded` to JS. #}
      {# `c-x-data` sets the first browser value. #}
      {# The listener applies later values returned by Python. #}
      <section
        class="choice-picker"
        c-x-data="{
          'choices': [],
          'choice': '',
          'batchesLoaded': batches_loaded,
        }"
        @choice-picker:loaded="
          choices = $event.detail.choices;
          choice = choices[0];
          batchesLoaded = $event.detail.batches_loaded;
        "
      >
        <button
          type="button"
          :disabled="$loading('load_choices')"
          @c-click="load_choices"
        >
          Load choices
        </button>
        <span x-show="$loading('load_choices')">Loading...</span>

        {# New in this step: show the counter from Python. #}
        <p>
          Sets loaded:
          <output x-text="batchesLoaded">
            {{ batches_loaded }}
          </output>
        </p>

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

          <c-ChoiceButton
            $c-props="{ label: choice }"
            @click="
              choice = choices[
                (choices.indexOf(choice) + 1) % choices.length
              ]
            "
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

Open `http://127.0.0.1:8000/` and click “Load choices” twice. The first call
loads “Ocean” and “Forest.” The second loads “History” and “Science,” while
“Sets loaded” moves from one to two. Reload the whole page and the sequence
starts over.

## Declare State

The server needs one value from the previous call: how many choice sets have
already been loaded. Use [`State`](/v/0.4.2/reference/component/#citry-component-state) to store that info:


```python
class Kwargs:
    batches_loaded: int = 0

class State:
    batches_loaded: int = 0
```


[`Kwargs`](/v/0.4.2/reference/component/#citry-component-kwargs) and [`State`](/v/0.4.2/reference/component/#citry-component-state) answer two
different questions:

- `Kwargs` - Component input when rendered as `Comp(...)` or `<c-Comp />`
- `State` - Data private to event handlers preserved across calls.

`Kwargs.batches_loaded` gives the first render its counter. The same-named
`State.batches_loaded` gives the first Python call its counter and says that
the value must come back on later calls.

How Citry builds the initial State:

1. Pass kwargs to state with matching names, so `Kwargs.batches_loaded -> State.batches_loaded`.
2. Uses State defaults for any gaps.
3. Remaining unfilled fields raise error.

With `<c-ChoicePicker />`, both declarations use their own `0` default. If a caller
passes `batches_loaded=3`, that value starts both the render and its State.

The following would fail, because `other_field` has no default
and is not on `Kwargs`:


```python
class Kwargs:
    batches_loaded: int = 0

class State:
    batches_loaded: int = 0
    other_field: str
```


Defining [`state_data()`](/v/0.4.2/events/state/#choose-what-survives-in-state)
replaces this automatic step. It receives the resolved kwargs and slots, then
returns the initial State as a `State` instance or a dictionary. Use it when
State needs a renamed or transformed value, or a small value derived from a
richer input. `ChoicePicker` does not need it because its names already match.

This would be a valid way of manually constructing `State`:


```python
class Kwargs:
    resume_id: int

class State:
    batches_loaded: int

def state_data(self, kwargs: Kwargs, slots):
    batches_loaded = resume_batches_from_db(kwargs.resume_id)
    return {"batches_loaded": batches_loaded or 0}
```


Coming back to `<c-ChoicePicker />`, every kwarg is also State. When the two shapes are the
same, you can inherit the fields and their defaults instead of repeating them:


```python
class Kwargs:
    batches_loaded: int = 0

class State(Kwargs):
    pass
```


The following lessons use this shorthand. Keep the declarations separate when
some render inputs should not travel through the browser.

The choices themselves do not need to be in State. Python can load them again,
and Alpine already holds the selected choice for the browser interaction.

## State decides server behavior

The example now has two possible database results:


```python
CHOICE_BATCHES = (
    ("Ocean", "Forest"),
    ("History", "Science"),
)

def load_choices_from_database(batch: int) -> list[str]:
    choices = CHOICE_BATCHES[batch % len(CHOICE_BATCHES)]
    return list(choices)
```


Batch zero returns “Ocean” and “Forest.” Batch one returns “History” and
“Science.” The `% len(CHOICE_BATCHES)` part wraps back to the first set after
the last one.

The handler reads the current counter, loads that batch, and then advances the
counter for next time:


```python
class Events:
    def load_choices(self, state):
        choices = load_choices_from_database(
            state.batches_loaded
        )
        state.batches_loaded += 1
        return actions.Dispatch(
            "choice-picker:loaded",
            {
                "choices": choices,
                "batches_loaded": state.batches_loaded,
            },
        )
```


On the first click, the handler:

- receives `state.batches_loaded=0`
- loads batch zero
- sets `state.batches_loaded=1`

Citry then sends the updated State back with the response.

On the second click, the handler:

- receives `state.batches_loaded=1`
- loads batch one
- sets `state.batches_loaded=2`

The dispatched event also includes the new count because the page displays
it. State carries the value to the next Python call; the event payload makes
the value available to Alpine right now.

## Update the browser values

The picker starts its Alpine data from the value Python rendered:


```citry-html
<section
  c-x-data="{
    'choices': [],
    'choice': '',
    'batchesLoaded': batches_loaded,
  }"
>
  ...
</section>
```


The `c-` prefix makes `x-data` a
[dynamic attribute](/v/0.4.2/syntax/dynamic-attributes/). Citry evaluates the Python
expression and writes an ordinary Alpine `x-data` attribute. A picker created
with another starting count will therefore show that count in both places.

When `choice-picker:loaded` arrives, its listener updates all three browser
values:


```citry-html
@choice-picker:loaded="
  choices = $event.detail.choices;
  choice = choices[0];
  batchesLoaded = $event.detail.batches_loaded;
"
```


The new list and selected choice stay in Alpine. The counter is named
`batches_loaded` in Python and `batchesLoaded` in Alpine, following each
language's usual style:


```text
batchesLoaded = $event.detail.batches_loaded;
^^^^^^^^^^^^^                 ^^^^^^^^^^^^^^^
  Alpine var                  data from Python
```


The `batches_loaded` counter travels in State because Python needs it to
choose the next batch. Reloading the page creates a new picker at its starting
value of zero.

## State secrets

Signed State lets the server detect whether its browser-carried value was
changed. It does not hide the value, sign a person in, or decide what that
person may do.

!!! warning

     **DO NOT** put passwords, API keys, or other secrets in State. Check permissions
     inside each event handler just as you would in an ordinary web route. In
     production, keep `CITRY_SECRET` stable and give every worker the same value so
     they can read one another's signed State.

## Next steps

State is useful for values a component carries from one call to the next.
Next, [handle and validate forms](/v/0.4.2/getting-started/forms/) whose values come
from named browser controls.