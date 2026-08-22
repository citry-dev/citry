---
title: Infinite Scroll
description: Request more server-owned results automatically while retaining a real Load more fallback.
---

# Infinite Scroll

`CInfiniteScroll` owns the request boundary around results. Your application
still owns the records, request, response, item identity, and rerender.

## Keep a server fallback

Set `action_name` inside a form to render a named Load more submit button. It
uses `formnovalidate`, so unrelated incomplete fields do not block pagination.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cinfinite_scroll/snippets/at_a_glance.py" title="Load another result page" />

The preview intercepts the named action and appends two bounded dummy pages so
you can exercise the complete state change here. In an application, let the
named submit continue and return the next keyed result page from the server.

## Keep loading automatically

Pass `onLoadMore` through `$c-props`. When the sentinel reaches `root_margin`,
the callback receives `{reason: 'intersection', sourceEvent: null}`. Button
activation uses `button` or `retry` and includes the native event.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cinfinite_scroll/snippets/automatic.py" title="Observe the result boundary" />

Update `loading`, `error`, or `hasMore` from application state. Only one request
may be in progress at a time. A state change, nested content append, or returned
Promise settling releases that request lock and permits a later request.

The automatic preview uses a clipped result feed. Scroll that feed to its end
to append another four generated results. It deliberately has no final page,
so every fresh trip to the end loads more. Production code sets `hasMore=False`
when its data source returns no continuation.

## Compose with Virtual List

Infinite Scroll answers when to load. Virtual List answers which known items
to render. Nest either component in the default slot without sharing their
state machines.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cinfinite_scroll/snippets/virtual_list.py" title="Load outside a virtualized collection" />

This static preview swaps from a three-record server snapshot to a six-record
snapshot. A real owner returns the newly rendered keyed collection.

## Show errors and retry

Set `error=True` after a failed request. The same stable action becomes Try
again, and its callback reason becomes `retry`. Automatic observation pauses
until that explicit retry or another state change clears the error.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cinfinite_scroll/snippets/error_retry.py" title="Offer a retry path" />

## Use named form actions

The observer never submits a form. A named action remains explicit and useful
without a browser runtime.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cinfinite_scroll/snippets/server_action.py" title="Submit a real Load more action" />

The preview reports the accepted submitter name and value, then appends its
dummy response without leaving the frame. A production form sends that named
action to its application endpoint.

## Announce bounded state

Give a mixed page an `aria_label`. Loading, error, and end messages use a
polite status. The sentinel is hidden from assistive technology and the button
stays keyboard reachable.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cinfinite_scroll/snippets/accessibility.py" title="Name and finish a result feed" />

The five default strings are Citry UI messages. Explicit label inputs opt that
one output out of catalog-driven browser updates.

<!-- UI_LIBRARY_API_REFERENCE -->
