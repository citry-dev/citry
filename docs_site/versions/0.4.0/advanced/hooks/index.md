---
title: Component hooks
url: https://citry.dev/v/0.4.0/advanced/hooks/
description: "Replace a component render or adjust the JavaScript and CSS tags it contributes."
---
# Component hooks

Hooks let one component change its own render or asset tags. Use them when a
normal data method or template cannot express the job clearly.

Citry provides two component hooks:

- `on_render()` can replace a render or recover from an error.
- `on_dependencies()` can adjust the component's scripts and styles.

For behavior that spans an application, use an
[`Extension`](/v/0.4.0/reference/extensions/#citry-extension) instead.

## Replace output with `on_render()`

On an uncached render, `on_render()` runs after Citry has prepared the
component's data and before it renders the template. Return `None` to continue
with the template. Return content to use it as the component's whole output.

This table shows a placeholder instead of an empty table:


```citry
from citry import Component


class Table(Component):
    class Kwargs:
        rows: list[str] | None = None

    def template_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> dict[str, list[str]]:
        return {"rows": kwargs.rows or []}

    def on_render(self):
        if not self.kwargs.rows:
            return "<p>No data yet</p>"
        return None

    template = """
      <table>
        <tr c-for="row in rows">
          <td>{{ row }}</td>
        </tr>
      </table>
    """
```


`Table()` inserts the placeholder. `Table(rows=["Ada", "Alan"])` continues
to the template.

The replacement may be:

- a string;
- a composed element such as `Message(text="Hello")`;
- an existing [`CitryRender`](/v/0.4.0/reference/rendering/#citry-citryrender);
- a [`Slot`](/v/0.4.0/reference/slots/#citry-slot), called without data; or
- a [`ComponentLike`](/v/0.4.0/reference/component-libraries/#citry-componentlike).

Because `None` means “continue,” return an empty string to insert nothing.

!!! warning

    Citry trusts a string returned from `on_render()` as component markup. It
    is not escaped. Never build that string by joining untrusted input. Put
    user-controlled values in a template, component inputs, or another API
    that escapes them.

Values needed by the template belong in
[`template_data()`](/v/0.4.0/reference/component/#citry-component-template-data). The hook already has
access to `self.kwargs`, `self.slots`, `self.parent`, and
[`self.inject()`](/v/0.4.0/reference/component/#citry-component-inject).

### Component caching skips the hook

A successful component-cache hit reuses the completed output. Citry does not
run data methods, the template, slots, or `on_render()` again.

If a hook's result depends on something outside the declared component inputs,
that value must also vary the cache key. Otherwise a cached result can outlive
the condition that produced it. See [Caching](/v/0.4.0/advanced/caching/).

## Observe completion or recover from an error

Add `yield` to make `on_render()` a two-phase generator. Code before the yield
runs before the template. Once the component and its children settle, the
yield receives `(result, error)`:


```python
def on_render(self):
    result, error = yield

    if error is not None:
        return "<p>Could not load this section.</p>"
    return None
```


Exactly one value is present:

- on success, `result` is the live
  [`CitryRender`](/v/0.4.0/reference/rendering/#citry-citryrender) and `error` is `None`;
- on failure, `result` is `None` and `error` is the exception.

After the yield, you may:

- return new content to replace the current result;
- raise an exception; or
- return `None` to keep a successful result or let an error continue upward.

Do not call `str(result)` merely to inspect it. The render still carries live
relationships between components and slot content, and it may not be safe to
serialize from inside this hook. If you return serialized HTML, you also take
responsibility for replacing the live result with that string.

You can yield replacement content and receive another `(result, error)` pair,
which supports multi-stage rendering. The generated
[`on_render()` reference](/v/0.4.0/reference/component/#citry-component-on-render) contains the complete
generator protocol.

For ordinary error recovery, prefer the built-in `<c-error-fallback>` tag.
See [Error boundaries](/v/0.4.0/concepts/error-boundaries/). A custom hook is useful
when recovery itself needs Python logic.

## Adjust a component's asset tags

`on_dependencies()` is a classmethod. At serialization time, Citry calls it
once for each rendered instance with that instance's scripts and styles. The
lists include:

- the component's own `js` and `css`;
- entries from its nested `Dependencies` class; and
- values generated from `js_data()` and `css_data()`.

Mutate the lists, or return a `(scripts, styles)` pair to replace them. Return
`None` to leave them unchanged.

This component adds `crossorigin` to the external scripts it contributes:


```citry
from citry import Component
from citry.ext.dependencies import Script, Style


class Chart(Component):
    class Dependencies:
        js = ["https://cdn.example.com/chart.js"]

    @classmethod
    def on_dependencies(
        cls,
        scripts: list[Script],
        styles: list[Style],
    ):
        for script in scripts:
            if script.url:
                script.attrs["crossorigin"] = "anonymous"
        return (scripts, styles)

    template = """
      <div class="chart"></div>
    """
```


This hook runs before Citry removes duplicates across components. When two
entries share a URL or inline content, the first one wins, including any
attributes the hook added.

Removing a component's own script can stop its browser behavior. Drop an
entry only when the same behavior is supplied somewhere else.

An extension `on_dependencies()` hook can adjust the collected component
lists after duplicates are removed. Citry may add its required browser
runtime and initialization tags afterward, so this hook is not a complete
document-level CSP surface. See [Extensions](/v/0.4.0/advanced/extensions/) for the
application-wide hook.

## Next steps

- [Component JavaScript and CSS](/v/0.4.0/advanced/js-and-css-dependencies/) covers
  primary assets and per-render data.
- [Dependency files](/v/0.4.0/advanced/dependency-files/) covers libraries, shared
  files, and custom tags.
- [Place JavaScript and CSS](/v/0.4.0/advanced/asset-placement/) controls where the
  collected tags go.
- [Rendering](/v/0.4.0/concepts/rendering/) explains the larger compose, render, and
  serialize process.