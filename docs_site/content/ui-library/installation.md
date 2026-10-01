---
title: Install and register Citry UI
description: Add the Citry UI package and register its components with a Citry instance.
---

# Install and register Citry UI

Add the separate [`citry-ui`](https://pypi.org/project/citry-ui/){: target="_blank" rel="noopener"} package to your application:

```console
uv add citry-ui
```

Register the library once with the [`Citry`][citry.Citry] instance that renders your
application. Components use the default `citry` instance unless they set a
`citry` class attribute to another instance, so most applications register
the library there:

```python
import citry_ui
from citry import citry

citry.register_library(citry_ui)
```

Registration makes tags such as [`<c-CButton>`](/ui-library/components/button/) and [`<c-CTabs>`](/ui-library/components/tabs/) available to
every component that renders through that `Citry` instance. If your
application creates its own instance, such as `app = Citry()`, call
`app.register_library(citry_ui)` instead. A component that renders through
an instance without the library fails with `NotRegistered: No component
registered as 'cbutton'`.

While working on Citry UI templates without a host application, select the
library manifest directly in VS Code:

```json
{
  "citry.app": "citry_ui:__citry_library__"
}
```

The editor then reads the Citry UI component names, inputs, slots, and template
data from the manifest. Select the application's configured `Citry` instance
when its own components or configuration are also needed.

## Use a component in a template

After the library is installed, you can reference the components in the template:

```citry
from citry import Component

class SaveActions(Component):
    template = """
      <c-CButton type="submit">
        Save changes
      </c-CButton>
    """
```

## Compose a component from Python

You can even import the components directly, and compose them in Python:

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

!!! note "Render a library component outside a template"

    Inside a template, Citry renders `save_button` through the component's
    own `Citry` instance. To render it on its own, pass the instance
    explicitly. Without it, Citry raises `LibraryComponentContextError`:

    ```python
    from citry import citry
    from citry_ui import CButton

    save_button = CButton(
        type="submit",
        slots={"default": "Save changes"},
    )

    html = str(save_button.render(citry=citry))
    ```
