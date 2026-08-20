---
title: Error boundaries
url: https://citry.dev/v/0.4.1/concepts/error-boundaries/
description: "Keep one server-rendered failure from replacing an otherwise useful page."
---
# Error boundaries

Use an error boundary when one server-rendered part of a page may fail but the
rest can still be useful. The boundary catches a render error from that part
and inserts a fallback in its place. Content outside the boundary continues to
render.

Citry provides the
[`<c-error-fallback>` built-in](/v/0.4.1/reference/builtins/#c-error-fallback). It
handles errors raised while Citry renders HTML. It does not catch JavaScript
errors in the browser or errors from a separate HTTP request.

## Wrap a section

Put the risky content inside `<c-error-fallback>` and give it a short fallback
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


If `<c-recent-activity>` raises during rendering, the reader still sees the
heading, the fallback message, and the account settings. If it succeeds, Citry
inserts the activity and never renders the fallback.

The boundary guards its whole body, so it can contain one component, several
components, or ordinary template markup.

## What happens on error

The boundary is transparent on success: it adds no wrapper and keeps the
rendered content unchanged. On failure, it discards the guarded content and
inserts the fallback.

With no fallback, the boundary inserts nothing for the failed section:


```citry-html
<p>
  before
  <c-error-fallback>
    <c-failing />
  </c-error-fallback>
  after
</p>
```


The surrounding `before` and `after` text still renders.

Fallback attributes are text. Citry escapes ordinary strings before inserting
them, including values supplied with `c-fallback`:


```citry-html
<c-error-fallback c-fallback="unavailable_message">
  <c-risky-widget />
</c-error-fallback>
```


If `unavailable_message` contains `<strong>Unavailable</strong>`, the reader
sees those characters as text; they do not become an element. This makes a
plain or computed message safe by default.

For trusted rich markup, use a fallback fill. Never turn text from a user or
another untrusted source into trusted HTML.

## Show the error in the fallback

Use a `fallback` fill when the fallback needs markup. Because explicit fills
cannot sit beside direct body content, put the guarded content in a `default`
fill:


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


The fill receives the raised exception as `failure.error`. That is the actual
exception object, not only its message. It can help the fallback choose a
response, but do not expose raw exception details to readers in production.

Choose one fallback form. Supplying both the `fallback` attribute and a
`fallback` fill raises `RuntimeError`.

## Boundaries nest, nearest wins

The nearest boundary handles an error from its guarded content:


```citry-html
<c-error-fallback fallback="The page section failed">
  <c-error-fallback fallback="The chart failed">
    <c-sales-chart />
  </c-error-fallback>
</c-error-fallback>
```


If the chart raises, the reader sees `The chart failed`. The outer boundary
does not handle an error that the inner one already caught.

A boundary does not catch an error raised by its own fallback. That error
moves outward to the next boundary. Keep the outer fallback small and
dependable when it serves as a final safety net.

## Things to know

- The only accepted component kwarg is `fallback`; `c-fallback` is its dynamic
  expression form.
- A fallback fill may omit `data` when it does not need the exception.
- Without any boundary above it, a render error escapes to the host view. Its
  message includes the failing component path.
- `error-fallback` is a reserved built-in name, so an application cannot
  register another component under it.

For the composition rules behind the two fills, see
[Slots](/v/0.4.1/concepts/slots/). For the wider server render lifecycle, see
[Rendering](/v/0.4.1/concepts/rendering/).