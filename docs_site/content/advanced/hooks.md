---
title: Component hooks
description: Replace a component render or adjust the JavaScript and CSS tags it contributes.
---

# Component hooks

Sometimes a component needs Python logic that its template cannot express:
show a placeholder instead of the template when there is no data, turn an
error into a friendly message, or add an attribute to the script tags it
brings. A hook is a method that Citry calls at a fixed point while it
renders the component, so your code can change the result.

A component has two hooks:

- `on_render()` replaces the component's output, or reacts after it
  renders.
- `on_dependencies()` changes the script and style tags the component adds
  to the page.

To change every component in an application at once, write an
[`Extension`][citry.Extension] instead.

## Replace the output

Citry calls `on_render()` after it prepares the component's data and before
it renders the template. Return `None` to render the template as usual.
Return anything else to use it as the component's whole output.

This table shows a message instead of an empty table:

```citry
from citry import Component


class Table(Component):
    class Kwargs:
        rows: list[str] | None = None

    def template_data(self, kwargs: Kwargs, slots):
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

`Table()` shows the message. `Table(rows=["Ada", "Alan"])` renders the
table.

`on_render()` can return:

- a string of HTML;
- a component, such as `Message(text="Hello")`;
- a [`CitryRender`][citry.CitryRender] that was already rendered;
- a [`Slot`][citry.Slot], which Citry renders without data;
- a [`ComponentLike`][citry.ComponentLike].

Because `None` means "render the template", return `""` to show nothing.

The hook can read `self.kwargs`, `self.slots`, `self.parent`, and
[`self.inject()`][citry.Component.inject]. To pass values to the template,
use [`template_data()`][citry.Component.template_data] instead.

!!! warning "Citry does not escape a returned string"

    Citry inserts a string from `on_render()` as HTML. Never build it from
    user input. Put user values in a template or a component input, where
    Citry escapes them.

## Show a failure message

For most error handling, wrap the part that may fail in the built-in
`<c-error-fallback>` tag; see
[Error boundaries](/concepts/error-boundaries/). Use `on_render()` when
deciding what to show needs Python code.

Add `yield` to `on_render()`. Code before the `yield` runs before the
template. The `yield` waits until the component and everything inside it
has rendered, then gives you a `(result, error)` pair:

```python
def on_render(self):
    result, error = yield

    if error is not None:
        return "<p>Could not load this section.</p>"
    return None
```

When rendering succeeds, `result` is the rendered
[`CitryRender`][citry.CitryRender] and `error` is `None`. When it fails,
`result` is `None` and `error` is the exception.

After the `yield`, you can:

- return new content to replace the result;
- raise an exception;
- return `None` to keep a successful result, or to let the error continue
  to the components around this one.

## Change asset tags

`on_dependencies()` receives the script and style tags that one rendered
component adds to the page. Those are its own `js` and `css`, the files in
its [`Dependencies`](/advanced/dependency-files/) class, and the
stylesheet that holds its `css_data()` values. Change the lists in place,
or return a new `(scripts, styles)` pair. Return `None` to keep them as
they are.

This component adds `crossorigin` to its external scripts:

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

The hook is a classmethod. Citry calls it when it turns the render into
HTML, once for each time the component appears on the page.

Removing the component's own script stops its browser code from running.
Remove an entry only when the same code reaches the page another way.

## Less common cases

### Cached renders

When [component caching](/performance/caching/) finds a stored result,
Citry reuses it and does not run the data methods, the template, or
`on_render()`. If the hook's result depends on something other than the
component's inputs, make that value part of the cache key, or the stored
result outlives the condition that produced it.

### Avoid `str(result)`

Do not call `str(result)` just to look at the HTML. The render is still
linked to the components and slot content around it, and turning it into a
string inside the hook may fail. If you do return serialized HTML, it
replaces the result, and Citry adds this component's marker attribute to
it.

### Yield more than once

Instead of a bare `yield`, you can yield new content. Citry renders it and
sends back a new `(result, error)` pair, so one hook can try several
outputs in turn. The [`on_render()` reference][citry.Component.on_render]
describes every step.

### Duplicate tags

The hook runs before Citry removes tags that several components share.
When two components add the same script, the first one wins, together with
any attribute the hook added. Stylesheets follow stricter rules; see
[Order and duplicates](/advanced/dependency-files/#order-files-and-handle-duplicates).

### Change page-wide tags

The hook sees only this component's tags. An extension's
`on_dependencies()` hook sees the tags of every component on the page, and
can also add scripts that run before all others. Citry adds its own
browser runtime after that hook, so neither hook sees it. See
[Add scripts and styles](/advanced/extensions/#add-scripts-and-stylesheets-to-a-page).

## Next steps

- [Component JS and CSS](/advanced/js-and-css-dependencies/) adds
  code and styles to one component.
- [Dependency files](/advanced/dependency-files/) adds libraries and shared
  files.
- [Place JavaScript and CSS](/advanced/asset-placement/) chooses where the
  tags go in the page.
- [Rendering](/concepts/rendering/) explains how a component becomes HTML.
