---
title: Error boundaries
url: https://citry.dev/v/0.3.1/concepts/error-boundaries/
description: "Wrap a section in c-error-fallback so a render error shows a fallback instead of breaking the page."
---
# Error boundaries

One widget throws while rendering, and instead of a graceful fallback the whole
page turns into a 500. An error boundary contains that blast radius: wrap the
risky section, and if it fails, the reader sees fallback content while the rest
of the page renders as normal.

Citry ships one built-in boundary, the `<c-error-fallback>` component. You do
not register or import anything to use it.

## Wrap a section

Put the content you want to guard inside `<c-error-fallback>` and give it a
`fallback` string to show on error.


```citry
from citry import Component

class Page(Component):
    template = """
      <c-error-fallback fallback="Could not load widget">
        <c-Widget />
      </c-error-fallback>
    """
```


If `<c-Widget>` raises while rendering, the boundary shows
`Could not load widget` in its place. Anything outside the boundary is
untouched, so the page still loads.

The guarded content is just the tag body (its default slot), so it can be a
single component, a whole block of markup, or several components together.

## What happens on error

When the guarded content raises, the boundary catches the error and swaps in the
fallback. When it renders cleanly, the boundary is invisible: you get exactly
the guarded content, and no fallback runs.

With no fallback at all, the boundary renders nothing (an empty string) on error
and keeps its neighbours:


```citry
template = """
  <main>
    before
    <c-error-fallback>
      <c-failing />
    </c-error-fallback>
    after
  </main>
"""

# When <c-failing> raises, the output is "beforeafter": the boundary
# contributes nothing, and the surrounding text still renders.
```


## Show the error in the fallback

For a richer fallback, fill the `fallback` slot instead of passing the
attribute. The slot receives the raised exception as slot data under the key
`error`.

A fill cannot sit next to other content, so when you use the `fallback` fill the
guarded content moves into an explicit `default` fill:


```citry
template = """
  <main>
    <c-error-fallback>
      <c-fill name="default">
       <c-failing />
      </c-fill>
      <c-fill name="fallback" data="d">
        <p>Caught: {{ d.error }}</p>
      </c-fill>
    </c-error-fallback>
  </main>
"""

# When the default content fails, the fallback fill renders and d.error
# is the actual raised exception object (renders e.g. "Caught: boom").
```


Give only one of the two. Passing both the `fallback` attribute and a
`fallback` fill raises a `RuntimeError`.

## Boundaries nest, nearest wins

You can put a boundary inside another boundary. When content fails, the nearest
boundary above it handles the error, and boundaries further out never see it.


```citry
template = """
  <main>
    <c-error-fallback fallback="outer">
      <c-error-fallback fallback="inner">
        <c-failing />
      </c-error-fallback>
    </c-error-fallback>
  </main>
"""

# The inner boundary catches the error, so the output contains "inner",
# not "outer".
```


One case does travel outward: if the fallback content itself raises, the
boundary that produced it does not catch its own fallback. That error bubbles up
to the next boundary above, which is where you would put a plainer, safer
fallback.

## Things to know

- The tag is `<c-error-fallback>` (kebab-case). The name `error-fallback` is
  reserved, so registering your own [Component](/v/0.3.1/reference/component/#citry-component) under it raises
  [AlreadyRegistered](/v/0.3.1/reference/citry/#citry-alreadyregistered).
- The only attribute is `fallback` (a plain string). Any other attribute, such
  as `<c-error-fallback bogus="x">`, is rejected.
- The value delivered to the `fallback` slot under `error` is the real
  exception object, not a message string, so you can branch on its type.
- With no boundary anywhere above it, a render error escapes to your view as
  usual, and its message names the failing child so you can find it.

Boundaries pair well with the rendering model in
[Rendering](/v/0.3.1/concepts/rendering/) and with [Slots](/v/0.3.1/concepts/slots/), since the
fallback is itself a slot.