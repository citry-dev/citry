---
title: Events state
description: Carry signed State between Python calls and read its public fields from Vue.
---

# Events state

The last handler ran the same query on every click. This version carries a
counter between calls so Python can load alternating choice batches.

Replace `components.py` with:

<c-include-file path="docs_site/snippets/getting_started/components_step10.py" language="citry" />

Click “Load choices” twice. The first call loads “Ocean” and “Forest”; the
second loads “History” and “Science.” “Sets loaded” moves from one to two.
Reloading the page starts over.

## Declare State

```python
class Kwargs:
    batches_loaded: int = 0

class State:
    batches_loaded: int = 0
```

[`Kwargs`][citry.Component.Kwargs] are render inputs. [`State`][citry.Component.State]
is signed, browser-carried data passed to event handlers across calls. Citry
initializes matching State fields from kwargs and then uses State defaults.
Use `state_data()` when names differ or a State value must be derived.

When every render input should survive, inheritance avoids repetition:

```python
class State(Kwargs):
    pass
```

Keep the declarations separate when some render inputs should not travel
through the browser.

## Let State decide server behavior

```python
class Events:
    def load_choices(self, state):
        choices = load_choices_from_database(state.batches_loaded)
        state.batches_loaded += 1
        return actions.Dispatch(
            "choice-picker:loaded",
            {"choices": choices},
        )
```

The first call receives zero, loads batch zero, and advances the signed value
to one. The next call receives one. Citry returns changed State with each
successful response.

## Read public State in Vue

A component with public State can read it through `$state`:

```citry-html
<output v-text="$state.batches_loaded">{{ batches_loaded }}</output>
```

The server-rendered fallback starts at the same value. After each successful
non-GET event response, the reactive `$state.batches_loaded` value updates.
Assignments to a whole public field are allowed in Vue and are queued for the
next non-GET request; they do not send a request by themselves. Nested values,
undeclared fields, and readonly State cannot be assigned. See [Browser APIs](/reference/browser-apis/#state).

The choice list stays ordinary component data because Python does not need the
browser's current selection on its next call.

## State is signed, not secret

Signing detects changes; it does not encrypt values, authenticate a person, or
authorize an operation. Never put passwords or API keys in State. Check access
inside each event handler, and keep `CITRY_SECRET` consistent across production
workers.

## Next steps

Next, [handle and validate forms](/getting-started/forms/).
