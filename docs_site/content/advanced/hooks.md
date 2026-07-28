---
title: Component hooks
description: Use on_render to replace, post-process, or recover a component's output, and on_dependencies to adjust the JS and CSS tags it contributes.
---

# Component hooks

A component hook lets you step into a single component's render. Hooks are
methods you add to your [Component][citry.Component] subclass, and each one runs
as part of that component's own render, for that component only. (For hooks that
span the whole app, reach for an [Extension][citry.Extension]; see
[Extensions](/advanced/extensions/).)

There are two:

- `on_render` replaces or post-processes what the component renders.
- `on_dependencies` adjusts the JS and CSS tags the component contributes to the
  page.

## Replace or post-process output with `on_render`

`on_render` runs on every render of the component, after `template_data` and
just before the template renders. Return `None` (the default) to render the
template as usual, or return content to use that as the component's whole output
instead. When you return content, the template is not rendered at all.

Everything the hook needs is on `self`: `self.kwargs`, `self.slots`,
`self.parent`, and `self.inject(...)`. To feed values into the template, use
`template_data`; `on_render` is for replacing or wrapping the output, not for
passing template variables.

The content you return can be any of:

- a string, used exactly as given (it is your component's own output, so it is
  not autoescaped)
- a composed element like `OtherComponent(title="hi")`, the
  [CitryElement][citry.CitryElement] you get from calling a component
- an already-rendered [CitryRender][citry.CitryRender]
- a [Slot][citry.Slot], invoked with no data

Because `None` means "no replacement", return an empty string to output nothing
at all.

### Replace the output

The simplest form returns a value directly. Here a table shows a placeholder
when it has no rows, and otherwise renders its template as usual:

```citry
from citry import Component


class Table(Component):
    class Kwargs:
        rows: list[str] | None = None

    template = """
      <table>
        <tr c-for="row in rows">
          <td>{{ row }}</td>
        </tr>
      </table>
    """

    def template_data(self, kwargs: Kwargs, slots):
        return {"rows": kwargs.rows or []}

    def on_render(self):
        if not self.kwargs.rows:
            return "<p>No data yet</p>"
        return None
```

`Table()` renders `<p>No data yet</p>`, while `Table(rows=["Ada", "Alan"])`
renders the table.

### See the finished output

Add a `yield` and `on_render` becomes a generator with two phases. The code
before the yield runs just before the template renders; the code after it runs
once the component and everything inside it has finished:

```python
def on_render(self):
    # Before: runs just before the template renders.
    result, error = yield

    # After: the whole subtree has settled.
    ...
```

The yield hands back a `(result, error)` pair once the output has settled:

- On success, `result` is the finished [CitryRender][citry.CitryRender] and
  `error` is `None`.
- On failure, `result` is `None` and `error` is the exception that was raised.

Exactly one of the two is set. After the yield you have three choices:

1. Return new content, and it becomes the final output. If the render had
   failed, that error is dropped.
2. Raise, and your exception becomes the component's error.
3. Return `None` (or a bare `return`), and the current result stands: a success
   keeps its output, a failure keeps bubbling up.

You can also `yield` more than once. Each `yield <content>` swaps in that
content, renders it, and hands back a fresh `(result, error)` pair, so you can
build the output in stages.

### Post-process the finished HTML

`result` is a [CitryRender][citry.CitryRender], not a string. Call `str(result)`
to read the finished HTML, then decide what to output. This feed inspects its
rendered output and shows a placeholder when nothing came through:

```citry
class Feed(Component):
    class Kwargs:
        posts: list[str] | None = None

    template = """
      <ul class="feed">
        <li c-for="post in posts">{{ post }}</li>
      </ul>
    """

    def template_data(self, kwargs: Kwargs, slots):
        return {"posts": kwargs.posts or []}

    def on_render(self):
        # Before: runs just before the template renders.
        result, error = yield

        # After: the whole subtree has settled.
        if error is not None:
            return None
        if "<li" not in str(result):
            return '<p class="feed-empty">Nothing here yet.</p>'
        return None
```

`Feed()` renders the placeholder, while `Feed(posts=["hi", "yo"])` renders the
list.

Build the replacement from fresh markup, as above, or return `None` to keep what
rendered. Handing your component's own serialized HTML straight back as its
output would repeat the marker on its root element, so prefer new markup or
`None`.

### Catch a failing child

The after phase fires even when a child failed to render, so `on_render` can
contain the error and show a fallback in its place:

```citry
class Profile(Component):
    template = """
      <b>{{ user.name }}</b>
    """


class Card(Component):
    template = """
      <section>
        {{ body }}
      </section>
    """

    def template_data(self, kwargs, slots):
        return {"body": Profile()}

    def on_render(self):
        result, error = yield
        if error is not None:
            return "<p>Could not load this card.</p>"
        return None
```

If `Profile` raises while rendering (here `user` is never provided), `Card`
catches it and renders `Could not load this card.` instead of failing the whole
page.

This is the idea behind an error boundary, and citry already ships one as the
`<c-error-fallback>` component. Reach for
[Error boundaries](/concepts/error-boundaries/) first, and drop to `on_render`
only when you need custom recovery logic.

### Route to another component

Because `on_render` can return a composed element, it can pick which component
to render based on the inputs:

```citry
class OldChart(Component):
    template = """
      <div>old chart</div>
    """


class NewChart(Component):
    template = """
      <div>new chart</div>
    """


class Chart(Component):
    class Kwargs:
        beta: bool = False

    def on_render(self):
        if self.kwargs.beta:
            return NewChart()
        return OldChart()
```

`Chart()` renders `OldChart`, while `Chart(beta=True)` renders `NewChart`.

## Adjust JS and CSS with `on_dependencies`

`on_dependencies` is a classmethod hook that adjusts the JS and CSS tags this
component contributes, and only this component's. It runs when the page is
serialized, once for each rendered instance of the component.

```python
@classmethod
def on_dependencies(
    cls,
    scripts: list[Script],
    styles: list[Style],
) -> tuple[list[Script], list[Style]] | None:
    ...
```

The two lists hold this component's [Script][citry.ext.dependencies.Script] and
[Style][citry.ext.dependencies.Style] entries: its own `js` and `css`, anything in its
`Dependencies` class, and the per-instance variables generated from `js_data`
and `css_data`. Return a `(scripts, styles)` pair to replace the lists, mutate
them in place, or return `None` (the default) to leave them untouched.

Use it to add attributes, reorder entries, or drop ones you know are already
loaded elsewhere. Removing a component's own entries can stop it working in the
browser, so this hook is for adjusting tags rather than removing behavior.

For example, add a CSP nonce to every tag this component emits (`get_nonce()` is
your own helper that returns the current request's nonce):

```citry
from citry import Component
from citry.ext.dependencies import Script, Style


class Panel(Component):
    template = """
      <div class="panel"></div>
    """
    js = """
      console.log("panel ready");
    """
    css = """
      .panel {
        color: red;
      }
    """

    @classmethod
    def on_dependencies(cls, scripts: list[Script], styles: list[Style]):
        # Add a CSP nonce to every tag this component emits.
        for dep in [*scripts, *styles]:
            dep.attrs["nonce"] = get_nonce()
        return (scripts, styles)
```

Each rendered `Panel` now emits its `<style>` and `<script>` tags with a `nonce`
attribute.

To adjust the whole page's tags at once (every component's, after duplicates are
removed) rather than one component's, write an [Extension][citry.Extension] with
an `on_dependencies` method instead. See [Extensions](/advanced/extensions/).

## Where to go next

- [Error boundaries](/concepts/error-boundaries/) for the built-in, no-code way
  to catch render errors.
- [Rendering](/concepts/rendering/) for the compose, render, and serialize model
  that `on_render` plugs into.
- [JS and CSS dependencies](/advanced/js-and-css-dependencies/) for how the
  [Script][citry.ext.dependencies.Script] and [Style][citry.ext.dependencies.Style] entries are collected and
  placed.
- [Extensions](/advanced/extensions/) for hooks that run across the whole app.
