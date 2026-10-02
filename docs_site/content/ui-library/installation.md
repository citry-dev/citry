---
title: Install and register Citry UI
description: Add the Citry UI package and register its components with a Citry instance.
---

# Install and register Citry UI

To use Citry UI components such as `<c-CButton>` in your templates,
install the package and register it once with Citry.

## Install the package

Add [`citry-ui`](https://pypi.org/project/citry-ui/){: target="_blank" rel="noopener"}
to your application:

```console
uv add citry-ui
```

## Register the library

Register Citry UI with the [`Citry`][citry.Citry] instance that renders
your components. Most applications use the default instance, `citry`:

```python
import citry_ui
from citry import citry

citry.register_library(citry_ui)
```

Every component that renders through that instance can now use tags such
as [`<c-CButton>`](/ui-library/components/button/) and
[`<c-CTabs>`](/ui-library/components/tabs/).

If your application creates its own instance, such as `app = Citry()`,
call `app.register_library(citry_ui)` instead. A component uses the
default instance unless it sets a `citry` class attribute to another one.

If a component renders through an instance that does not have the
library, rendering fails with a `NotRegistered` error such as
`No component registered as 'cbutton'`.

## Use in a template { #use-a-component-in-a-template }

Write the component's tag in a template:

```citry
from citry import Component


class SaveActions(Component):
    template = """
      <c-CButton type="submit">
        Save changes
      </c-CButton>
    """
```

## Create it in Python { #compose-a-component-from-python }

You can also import a component class, create it in Python, and pass it
to a template:

```citry
from citry import Component
from citry_ui import CButton

save_button = CButton(
    type="submit",
    slots={"default": "Save changes"},
)


class SaveActions(Component):
    def template_data(self, kwargs, slots):
        return {"save_button": save_button}

    template = """
      <div>
        {{ save_button }}
      </div>
    """
```

### Render it standalone { #render-a-library-component-outside-a-template }

Inside a template, Citry renders `save_button` with the template's
`Citry` instance. To render it on its own, pass the instance with
`citry=`. Without it, Citry raises `LibraryComponentContextError`:

```python
from citry import citry

html = str(save_button.render(citry=citry))
```

## Edit Citry UI in VS Code { #edit-citry-ui-in-vs-code }

This applies only when you work on Citry UI's own templates without an
application around them. Point the VS Code extension at the library
directly:

```json
{
  "citry.app": "citry_ui:__citry_library__"
}
```

The editor then reads Citry UI's component names, inputs, slots, and
template data. When you also need your application's own components or
settings, point `citry.app` at your application's `Citry` instance
instead.
