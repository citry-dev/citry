---
title: Error boundaries
description: Keep one server-rendered failure from replacing an otherwise useful page.
---

# Error boundaries

Without an error boundary, one component that raises an exception while
rendering stops the whole page from rendering. When the rest of the page is
still useful, wrap the risky part in
[`<c-error-fallback>`](/reference/builtins/#c-error-fallback). If that part
fails, Citry shows a fallback in its place and renders everything else as
usual.

An error boundary catches errors raised while Citry renders HTML on the
server. It does not catch JavaScript errors in the browser, or errors in an
event handler's own code.

## Wrap a section that may fail

Put the risky content inside `<c-error-fallback>` and give it a short
message:

```citry-html
<main>
  <h1>Account</h1>

  <c-error-fallback fallback="Recent activity is unavailable">
    <c-recent-activity />
  </c-error-fallback>

  <c-account-settings />
</main>
```

If `<c-recent-activity>` raises, the reader sees the heading, the message
`Recent activity is unavailable`, and the account settings. If it succeeds,
the page shows the activity, and the boundary adds no HTML of its own.

The boundary can wrap one component, several components, or any template
markup.

Without a `fallback`, a failed section shows nothing, and the content
around it still renders.

## Show markup in the fallback

Citry escapes the `fallback` text, including a value from
`c-fallback="message"`, so HTML tags in it show as text. For a fallback with
markup, put the content in two fills: the guarded content in the `default`
fill, and the fallback in the `fallback` fill:

```citry-html
<c-error-fallback>
  <c-fill name="default">
    <c-recent-activity />
  </c-fill>

  <c-fill name="fallback" data="failure">
    <section role="alert">
      <h2>Recent activity is unavailable</h2>
      <p>Try again in a moment.</p>
    </section>
  </c-fill>
</c-error-fallback>
```

`data="failure"` gives the fallback the exception that was raised, as
`failure.error`. Use it to choose what to show, but do not show raw
exception details to readers in production. Leave out `data` when you do
not need the exception.

Never turn text from users or other untrusted sources into markup in a
fallback.

Use either the `fallback` attribute (or its expression form `c-fallback`)
or a `fallback` fill, not both. Using both raises `RuntimeError`.

## Nest boundaries

When boundaries are nested, the nearest one around the failing content
handles the error:

```citry-html
<c-error-fallback fallback="The page section failed">
  <c-error-fallback fallback="The chart failed">
    <c-sales-chart />
  </c-error-fallback>
</c-error-fallback>
```

If the chart raises, the reader sees `The chart failed`, and the rest of the
outer section renders normally.

An error raised by a fallback itself goes to the next boundary out. Keep an
outer fallback small and simple so that it does not fail too.

## When no boundary catches an error

A render error that no boundary catches reaches your web framework's view
or route, like any other exception. Its message includes the path of
components that led to the failing one.

The name `error-fallback` is reserved for this built-in, so you cannot
register your own component under it. For the rules behind the two fills,
see [Slots](/concepts/slots/).
