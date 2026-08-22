# Infinite Scroll

**Status:** accepted implementation contract for the first production pass.
Research refreshed 2026-08-21.

## 1. Purpose and boundary

`CInfiniteScroll` is a progressive-enhancement boundary that asks an
application for another page of records. It does not virtualize, paginate,
render, key, or retain the records. Its default slot can therefore contain an
ordinary list, Data Grid, Virtual List, or any other server-owned result.

```html
<c-CInfiniteScroll action_name="feed_action" c-has_more="has_more">
  {{ rendered_feed }}
</c-CInfiniteScroll>
```

The server output always includes a real Load more submit button when
`action_name` is supplied. JavaScript may additionally call `onLoadMore` when
the sentinel approaches the viewport. A consumer may use the button without
automatic observation, but observation never submits a form implicitly.

## 2. Prior art and rejected shortcuts

The W3C Intersection Observer model supplies asynchronous intersection
notifications without a scroll handler. htmx's current infinite-scroll example
keeps page loading in the application request layer. Citry adopts those
boundaries while retaining an explicit native button for keyboard, assistive
technology, no-script use, retry, and deterministic testing.

Infinite Scroll differs from Virtual List: this family decides when to request
more data, while Virtual List decides which already-known records occupy the
DOM. Combining the two is supported by composition, not by merging their
state machines. Scroll listeners, automatic form submission, DOM cloning, and
an implicit network client are rejected.

## 3. Anatomy and semantics

```text
div root
|- div content (aria-busy) -> default slot
|- div status (aria-live=polite, aria-atomic=true)
|  |- error, loading, or end text
|- button Load more / Retry
`- span sentinel (aria-hidden)
```

The root is a generic region only when `aria_label` is supplied. The default
slot remains meaningful server HTML without JavaScript. `aria-busy` belongs to
the content wrapper, leaving its sibling status available to announce pending
work. The status is stable and polite. Loading is not announced repeatedly.
The sentinel is never focusable and never substitutes for the button.

## 4. Inputs and state

Server inputs are `id`, `aria_label`, `has_more`, `loading`, `error`,
`disabled`, `auto`, `root_margin`, `threshold`, `action_name`, `action_value`,
five message overrides, and ordinary root `class_`, `style`, and `attrs`.
`root_margin` is a nonempty Intersection Observer margin string. `threshold`
is a finite number from zero through one.

Client props mirror `hasMore`, `loading`, `error`, `disabled`, and `auto`, and
add `onLoadMore`. Invalid reactive values are diagnosed once and retain the
last valid value. Effective states are reflected as `data-loading`,
`data-error`, `data-end`, `data-disabled`, and `data-auto`.

One request may be pending at a time. Automatic observation pauses in the
error state so retry remains an explicit user action. The request lock clears
when loading changes, the error changes, `hasMore` changes, nested server
content changes, or a returned Promise settles. The lock suppresses overlapping
requests. It does not suppress a later serial request if the sentinel remains
intersecting after the owner updates content or state. The owner must append
enough content to move the boundary, or set `hasMore=False` when no continuation
remains.

## 5. Requests, forms, and callbacks

`onLoadMore(detail)` receives `{reason, sourceEvent}`. `reason` is `button`,
`intersection`, or `retry`; intersection has a null `sourceEvent`. A callback
may return a Promise. Callback errors are isolated and reported.

With `action_name`, the visible action is a named submit button using
`action_value` and `formnovalidate`. It therefore works without JavaScript and
does not let an incomplete form block loading. If both a callback and named
action are present, button activation calls the callback and still retains the
normal submit behavior unless the application prevents the source event.

The observer invokes only `onLoadMore`. It never clicks the button or submits
a form. Without a callback, `auto` leaves the native button as the only request
path.

## 6. Internationalization

The component defines source messages for Load more, Retry, Loading, load
error, and end of results. Initial output uses server `tr()`. Stable text uses
`$c-tr` only while the corresponding message override retains its catalog
default. Explicit label overrides remain fixed application text. No message
has variables.

## 7. Styling and environments

Public parts are `infinite-scroll`, `content`, `status`, `action`, and
`sentinel`. Public variables cover status gap, action surface, border, radius,
focus, and muted text. Narrow layouts wrap safely. Forced colors preserve the
button boundary and focus ring. Reduced motion removes transitions. Print
hides the action and sentinel while retaining content and an error or end
message.

## 8. Lifecycle, performance, and security

The family creates at most one Intersection Observer and one Mutation Observer
per mounted instance. It has no global listeners or scroll polling. Repeated
initialization is idempotent. Cleanup disconnects both observers, removes the
button listener, and releases reactive effects. The runtime never executes
HTML, constructs selectors from consumer data, or owns transport credentials.

## 9. Acceptance and documentation

Evidence covers useful no-script output, named native actions, callback detail,
observer requests, duplicate suppression, reactive loading/error/end states,
Promise release, disabledness, i18n overrides, cleanup, narrow layout, reduced
motion, forced colors, axe, snippets, API schema, generated catalog, and
browser execution. Family browser tests execute every shipped preview and
prove its enabled action changes visible content or state without navigating
the static preview. The deliberately unbounded automatic preview proves four
separate user-triggered observer cycles, no spontaneous request between those
scrolls, and a fifth successful cycle while the end state remains absent.

The public guide owns six examples: basic server loading, automatic callbacks,
Virtual List composition, error and retry, native form actions, and accessible
state guidance. The structured API ends with every translation key.

## 10. Compatibility classification

Inputs, callback detail, native form behavior, message keys, parts, public CSS
variables, and reflected state are stable API. Exact spacing, colors, and
observer scheduling may evolve without changing the contract.
