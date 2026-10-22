---
title: Secrets
description: Wrap API tokens and passwords in Secret so Citry refuses to send them to the browser, and citry check warns before the page runs.
---

# Secrets

Everything `js_data()` returns ends up in the page source, where any
visitor can read it. A natural first attempt sends an API token along
with the other settings:

```python
API_TOKEN = os.environ["API_TOKEN"]


def js_data(self, kwargs, slots):
    # Wrong: every visitor can read the token in the page source
    return {"apiBase": "/api", "token": API_TOKEN}
```

The browser needs the data the token unlocks, not the token itself.

## Keep tokens off the page { #keep-tokens-off-the-page }

Wrap the token in [`Secret`][citry.Secret] where you load it, read it on the server
with `get_secret_value()`, and send the browser only the result:

```citry
import os

from citry import Component, Secret

API_TOKEN = Secret(os.environ["API_TOKEN"])


class Board(Component):
    def template_data(self, kwargs, slots):
        # Right: the token is used on the server only
        token = API_TOKEN.get_secret_value()
        return {"rows": load_rows(token)}

    def js_data(self, kwargs, slots):
        return {"apiBase": "/api"}

    template = """
      <ul>
        <c-for each="row in rows">
          <li>{{ row }}</li>
        </c-for>
      </ul>
    """
```

On the server a `Secret` is safe to pass around. In a template,
`{{ token }}` shows `***`. You can also pass it to a child component;
annotate the child's `Kwargs` field as `Secret[str]` so a plain string
passed there is rejected.

!!! warning "A plain string is not detected"

    Citry knows a value is secret only when you wrap it. A token kept in
    a plain `str` is sent like any other string, and so is the result of
    `get_secret_value()` once you return it from `js_data()` or write it
    into a template.

## What rendering refuses { #rendering-refuses-a-secret }

If a `Secret` ends up anywhere in the dicts and lists `js_data()`
returns, Citry refuses to send it. Rendering the page raises a
`TypeError` that names the component and the key, before any HTML is
sent:

```text
TypeError: Board.js_data()["token"] holds a citry.Secret, and Citry
never sends a Secret to the browser, where anyone could read it in
the page source. ...
```

Citry also refuses a `Secret` in these cases:

- A `Secret` inside a dataclass instance, used as a dict key, or put in
  a set is refused, but the `TypeError` then does not name the key.
- Rendering fails with `ValueError` when `css_data()` or a
  [State](/events/state/) field holds a `Secret`, whether or not the
  component has CSS.

## Catch secrets early { #check-for-secrets }

[`citry --app ... check`](/advanced/cli/#check-component-templates)
reports a `Secret` that `js_data()` returns before the page runs, as
the
[`citry.js-data.unsupported-type`](/ide/diagnostics/#citry.js-data.unsupported-type)
warning. It finds one when it can see where the value comes from:

- a module-level `Secret` that `js_data()` puts in its result, such as
  `{"token": API_TOKEN}`, or a `JsData` field annotated `Secret[str]`;
- an attribute stored on a module or a plain class, such as
  `config.API_TOKEN`. It skips an attribute whose reading runs code, such
  as a property or Django's lazy `settings`.

Without `--types`, `citry check` does not see a `Secret` that a call
returns, such as `get_token()`. The Citry editor extension and
`citry check --types`
report one when the type checker can tell the call returns a `Secret`.

## Less common cases

### Cached child components { #cached-child-components }

Passing a `Secret` to a child that uses the
[render cache](/performance/caching/) raises
[`CacheKeyError`][citry.ext.cache.CacheKeyError], because the default
cache key is built from all of the child's kwargs and a `Secret` cannot
be part of a key. Return values that are not secret, such as a user id,
from the child's `Cache.vary()`, or leave the child uncached.

### Pydantic `Kwargs` { #pydantic-kwargs }

When you pass a `Secret` to a child whose `Kwargs` is a Pydantic model,
Pydantic's error for a plain string prints that string. Turn that off in
the model's config:

```python
from pydantic import BaseModel, ConfigDict

from citry import Secret


class Kwargs(BaseModel):
    # Keeps a plain string passed as `token` out of the error
    model_config = ConfigDict(hide_input_in_errors=True)

    token: Secret[str]
```

## See also

- [Security](/security/) for what else Citry does to keep a page safe.
- [Component options](/vue/component-options/#seed-browser-data-from-python)
  for what `js_data()` sends to the browser.
