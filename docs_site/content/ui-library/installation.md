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
application:

```python
import citry_ui
from citry import Citry

app = Citry()
app.register_library(citry_ui)
```

Registration makes tags such as [`<c-CButton>`](/ui-library/components/button/) and [`<c-CTabs>`](/ui-library/components/tabs/) available to
components owned by that `Citry` instance.

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

!!! note

    To render library components in Python, you need to pass a `Citry` instance:
    
    ```py
    save_button = CButton(
        type="submit",
        slots={"default": "Save changes"},
    )

    html = save_button.render(citry)
    ```
