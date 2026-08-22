---
title: Infinite Scroll
url: https://citry.dev/v/0.4.3/ui-library/components/infinite-scroll/
description: "Request more server-owned results automatically while retaining a real Load more fallback."
---
# Infinite Scroll

`CInfiniteScroll` owns the request boundary around results. Your application
still owns the records, request, response, item identity, and rerender.

## Keep a server fallback

Set `action_name` inside a form to render a named Load more submit button. It
uses `formnovalidate`, so unrelated incomplete fields do not block pagination.


### Load another result page

[Open the rendered preview](/v/0.4.3/ui-library/components/infinite-scroll/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InfiniteScrollAtAGlance(Component):
    template = """
      <section x-data>
        <form @submit.prevent>
          <c-CInfiniteScroll
            aria_label="Activity feed"
            action_name="feed_action"
            c-auto="False"
            $c-props="{loading, hasMore, onLoadMore: loadNextPage}"
          >
            <ol>
              <li>Created the project</li>
              <li>Invited the design team</li>
              <li>Published the brief</li>
              <template x-for="activity in moreActivities" :key="activity.id">
                <li x-text="activity.label"></li>
              </template>
            </ol>
          </c-CInfiniteScroll>
        </form>
        <output aria-live="polite" x-text="`Loaded ${3 + moreActivities.length} activities`">
          Loaded 3 activities
        </output>
      </section>
    """

    js = """
      $component(({ scope }) => {
        const pages = [
          [
            { id: 4, label: 'Received legal approval' },
            { id: 5, label: 'Scheduled the launch' },
          ],
          [
            { id: 6, label: 'Opened early access' },
            { id: 7, label: 'Collected the first responses' },
          ],
        ];
        scope.moreActivities = [];
        scope.loading = false;
        scope.hasMore = true;
        let page = 0;
        scope.loadNextPage = detail => {
          // This static preview handles the named action locally. A server page
          // lets the submit continue and returns the next keyed result page.
          detail.sourceEvent?.preventDefault();
          if (scope.loading || !scope.hasMore) return;
          scope.loading = true;
          return new Promise(resolve => setTimeout(() => {
            scope.moreActivities.push(...pages[page]);
            page += 1;
            scope.hasMore = page < pages.length;
            scope.loading = false;
            resolve();
          }, 220));
        };
      });
    """


preview = InfiniteScrollAtAGlance()
preview  # noqa: B018
````


The preview intercepts the named action and appends two bounded dummy pages so
you can exercise the complete state change here. In an application, let the
named submit continue and return the next keyed result page from the server.

## Keep loading automatically

Pass `onLoadMore` through `$c-props`. When the sentinel reaches `root_margin`,
the callback receives `{reason: 'intersection', sourceEvent: null}`. Button
activation uses `button` or `retry` and includes the native event.


### Observe the result boundary

[Open the rendered preview](/v/0.4.3/ui-library/components/infinite-scroll/_previews/automatic/)

````citry
# ruff: noqa: E501 - embedded Citry template attributes remain readable as authored HTML

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InfiniteScrollAutomatic(Component):
    template = """
      <section x-data>
        <p>Scroll to the end of the clipped result feed.</p>
        <c-CInfiniteScroll
          aria_label="Search results"
          c-style="{'max-block-size': '12rem', 'overflow': 'auto', 'overflow-anchor': 'none', 'padding-inline-end': '0.25rem'}"
          $c-props="{loading, hasMore, onLoadMore: loadNextPage}"
        >
          <ol>
            <li>Search result 1</li><li>Search result 2</li><li>Search result 3</li><li>Search result 4</li>
            <li>Search result 5</li><li>Search result 6</li><li>Search result 7</li><li>Search result 8</li>
            <template x-for="result in moreResults" :key="result.id">
              <li x-text="result.label"></li>
            </template>
          </ol>
        </c-CInfiniteScroll>
        <output aria-live="polite" x-text="`Loaded ${8 + moreResults.length} results`">
          Loaded 8 results
        </output>
      </section>
    """

    js = """
      $component(({ scope }) => {
        scope.moreResults = [];
        scope.loading = false;
        scope.hasMore = true;
        let nextResult = 9;
        scope.loadNextPage = () => {
          if (scope.loading) return;
          scope.loading = true;
          return new Promise(resolve => setTimeout(() => {
            const page = Array.from({ length: 4 }, () => {
              const id = nextResult++;
              return { id, label: `Search result ${id}` };
            });
            scope.moreResults.push(...page);
            scope.loading = false;
            resolve();
          }, 260));
        };
      });
    """


preview = InfiniteScrollAutomatic()
preview  # noqa: B018
````


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


### Load outside a virtualized collection

[Open the rendered preview](/v/0.4.3/ui-library/components/infinite-scroll/_previews/virtual-list/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InfiniteScrollVirtualList(Component):
    template = """
      <section x-data>
        <c-CInfiniteScroll
          aria_label="Audit log"
          c-auto="False"
          $c-props="{loading, hasMore, onLoadMore: loadSnapshot}"
        >
          <div x-bind:hidden="expanded">
            <c-CVirtualList aria_label="Loaded audit records" c-viewport_size="180">
              <c-CVirtualListItem item_key="event-1">Signed in</c-CVirtualListItem>
              <c-CVirtualListItem item_key="event-2">Changed billing contact</c-CVirtualListItem>
              <c-CVirtualListItem item_key="event-3">Exported report</c-CVirtualListItem>
            </c-CVirtualList>
          </div>
          <div hidden x-bind:hidden="!expanded">
            <c-CVirtualList aria_label="Loaded audit records" c-viewport_size="180">
              <c-CVirtualListItem item_key="event-1">Signed in</c-CVirtualListItem>
              <c-CVirtualListItem item_key="event-2">Changed billing contact</c-CVirtualListItem>
              <c-CVirtualListItem item_key="event-3">Exported report</c-CVirtualListItem>
              <c-CVirtualListItem item_key="event-4">Created an API token</c-CVirtualListItem>
              <c-CVirtualListItem item_key="event-5">Updated tax details</c-CVirtualListItem>
              <c-CVirtualListItem item_key="event-6">Invited a reviewer</c-CVirtualListItem>
            </c-CVirtualList>
          </div>
        </c-CInfiniteScroll>
        <output aria-live="polite" x-text="expanded ? 'Showing 6 audit records' : 'Showing 3 audit records'">
          Showing 3 audit records
        </output>
      </section>
    """

    js = """
      $component(({ scope }) => {
        scope.expanded = false;
        scope.loading = false;
        scope.hasMore = true;
        scope.loadSnapshot = () => {
          if (scope.loading || !scope.hasMore) return;
          scope.loading = true;
          return new Promise(resolve => setTimeout(() => {
            scope.expanded = true;
            scope.hasMore = false;
            scope.loading = false;
            resolve();
          }, 220));
        };
      });
    """


preview = InfiniteScrollVirtualList()
preview  # noqa: B018
````


This static preview swaps from a three-record server snapshot to a six-record
snapshot. A real owner returns the newly rendered keyed collection.

## Show errors and retry

Set `error=True` after a failed request. The same stable action becomes Try
again, and its callback reason becomes `retry`. Automatic observation pauses
until that explicit retry or another state change clears the error.


### Offer a retry path

[Open the rendered preview](/v/0.4.3/ui-library/components/infinite-scroll/_previews/error-retry/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InfiniteScrollErrorRetry(Component):
    template = """
      <section x-data>
        <c-CInfiniteScroll
          aria_label="Orders"
          c-auto="False"
          $c-props="{loading, error, hasMore, onLoadMore: retryPage}"
        >
          <ul>
            <li>Order #1042</li>
            <li>Order #1041</li>
            <template x-for="order in recoveredOrders" :key="order.id">
              <li x-text="order.label"></li>
            </template>
          </ul>
        </c-CInfiniteScroll>
        <output aria-live="polite" x-text="recovered ? 'Orders recovered' : 'Last request failed'">
          Last request failed
        </output>
      </section>
    """

    js = """
      $component(({ scope }) => {
        scope.recoveredOrders = [];
        scope.loading = false;
        scope.error = true;
        scope.hasMore = true;
        scope.recovered = false;
        scope.retryPage = () => {
          if (scope.loading || !scope.hasMore) return;
          scope.error = false;
          scope.loading = true;
          return new Promise(resolve => setTimeout(() => {
            scope.recoveredOrders.push(
              { id: 1040, label: 'Order #1040' },
              { id: 1039, label: 'Order #1039' },
            );
            scope.recovered = true;
            scope.hasMore = false;
            scope.loading = false;
            resolve();
          }, 260));
        };
      });
    """


preview = InfiniteScrollErrorRetry()
preview  # noqa: B018
````


## Use named form actions

The observer never submits a form. A named action remains explicit and useful
without a browser runtime.


### Submit a real Load more action

[Open the rendered preview](/v/0.4.3/ui-library/components/infinite-scroll/_previews/server-action/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InfiniteScrollServerAction(Component):
    template = """
      <form x-data @submit.prevent="loadServerPage($event)">
        <label>Search query <input name="query" required /></label>
        <c-CInfiniteScroll
          aria_label="Server search results"
          action_name="result_action"
          action_value="next:2"
          c-auto="False"
          $c-props="{loading, hasMore}"
        >
          <ol>
            <li>Camera body comparison</li>
            <li>Lens mount guide</li>
            <template x-for="result in moreResults" :key="result.id">
              <li x-text="result.label"></li>
            </template>
          </ol>
        </c-CInfiniteScroll>
        <output aria-live="polite" x-text="acceptedAction">Waiting for a named action</output>
      </form>
    """

    js = """
      $component(({ scope }) => {
        scope.moreResults = [];
        scope.loading = false;
        scope.hasMore = true;
        scope.acceptedAction = 'Waiting for a named action';
        scope.loadServerPage = event => {
          const submitter = event.submitter;
          if (!submitter || scope.loading || !scope.hasMore) return;
          scope.acceptedAction = `${submitter.name}=${submitter.value}`;
          scope.loading = true;
          setTimeout(() => {
            scope.moreResults.push(
              { id: 3, label: 'Mirrorless travel kit' },
              { id: 4, label: 'Low-light autofocus test' },
            );
            scope.hasMore = false;
            scope.loading = false;
          }, 240);
        };
      });
    """


preview = InfiniteScrollServerAction()
preview  # noqa: B018
````


The preview reports the accepted submitter name and value, then appends its
dummy response without leaving the frame. A production form sends that named
action to its application endpoint.

## Announce bounded state

Give a mixed page an `aria_label`. Loading, error, and end messages use a
polite status. The sentinel is hidden from assistive technology and the button
stays keyboard reachable.


### Name and finish a result feed

[Open the rendered preview](/v/0.4.3/ui-library/components/infinite-scroll/_previews/accessibility/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InfiniteScrollAccessibility(Component):
    template = """
      <c-CInfiniteScroll aria_label="Completed notifications" c-has_more="False">
        <ul><li>Backup completed</li><li>Invoice sent</li></ul>
      </c-CInfiniteScroll>
    """


preview = InfiniteScrollAccessibility()
preview  # noqa: B018
````


The five default strings are Citry UI messages. Explicit label inputs opt that
one output out of catalog-driven browser updates.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CInfiniteScroll server inputs

Server inputs are passed in a template through `<c-CInfiniteScroll ... />` or in Python
through `CInfiniteScroll(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="infinite-scroll-input-cinfinite-scroll-server-inputs-id"></span>`id` | `str | None` | generated | Sets the root ID. |
| <span id="infinite-scroll-input-cinfinite-scroll-server-inputs-aria-label"></span>`aria_label` | `str | None` | `None` | Names the root and gives it region semantics. |
| <span id="infinite-scroll-input-cinfinite-scroll-server-inputs-has-more"></span>`has_more` | `bool` | `True` | Controls whether another page exists. |
| <span id="infinite-scroll-input-cinfinite-scroll-server-inputs-loading"></span>`loading` | `bool` | `False` | Shows pending state and suppresses requests. |
| <span id="infinite-scroll-input-cinfinite-scroll-server-inputs-error"></span>`error` | `bool` | `False` | Shows error state while changing the action to Retry and pausing automatic observation. |
| <span id="infinite-scroll-input-cinfinite-scroll-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables requests and the action. |
| <span id="infinite-scroll-input-cinfinite-scroll-server-inputs-auto"></span>`auto` | `bool` | `True` | Enables Intersection Observer requests when a callback exists and no loading error disabled or end state blocks them. |
| <span id="infinite-scroll-input-cinfinite-scroll-server-inputs-root-margin"></span>`root_margin` | `str` | `"0px 0px 240px 0px"` | Sets the observer prefetch margin. |
| <span id="infinite-scroll-input-cinfinite-scroll-server-inputs-threshold"></span>`threshold` | `float` | `0` | Sets a finite observer threshold from zero through one. |
| <span id="infinite-scroll-input-cinfinite-scroll-server-inputs-action-name"></span>`action_name` | `str | None` | `None` | Makes the action a named submit button when supplied. |
| <span id="infinite-scroll-input-cinfinite-scroll-server-inputs-action-value"></span>`action_value` | `str` | `"load-more"` | Sets the submit button value. |
| <span id="infinite-scroll-input-cinfinite-scroll-server-inputs-load-more-label"></span>`load_more_label` | `str` | `"Load more"` | Overrides Load more text. |
| <span id="infinite-scroll-input-cinfinite-scroll-server-inputs-retry-label"></span>`retry_label` | `str` | `"Try again"` | Overrides Retry text. |
| <span id="infinite-scroll-input-cinfinite-scroll-server-inputs-loading-label"></span>`loading_label` | `str` | `"Loading more results"` | Overrides pending status text. |
| <span id="infinite-scroll-input-cinfinite-scroll-server-inputs-error-label"></span>`error_label` | `str` | `"More results could not be loaded"` | Overrides error status text. |
| <span id="infinite-scroll-input-cinfinite-scroll-server-inputs-end-label"></span>`end_label` | `str` | `"No more results"` | Overrides end status text. |
| <span id="infinite-scroll-input-cinfinite-scroll-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#infinite-scroll-interface-class-value)) | `None` | Adds root classes. |
| <span id="infinite-scroll-input-cinfinite-scroll-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#infinite-scroll-interface-style-value)) | `None` | Adds root styles. |
| <span id="infinite-scroll-input-cinfinite-scroll-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed root attributes. |

</div>

#### CInfiniteScroll client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CInfiniteScroll />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="infinite-scroll-input-cinfinite-scroll-client-inputs-has-more"></span>`hasMore` | `boolean` | Uses the server value. | Reactively controls whether another page exists. |
| <span id="infinite-scroll-input-cinfinite-scroll-client-inputs-loading"></span>`loading` | `boolean` | Uses the server value. | Reactively controls pending state. |
| <span id="infinite-scroll-input-cinfinite-scroll-client-inputs-error"></span>`error` | `boolean` | Uses the server value. | Reactively controls retry state. |
| <span id="infinite-scroll-input-cinfinite-scroll-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server value. | Reactively disables requests. |
| <span id="infinite-scroll-input-cinfinite-scroll-client-inputs-auto"></span>`auto` | `boolean` | Uses the server value. | Reactively enables observation. |
| <span id="infinite-scroll-input-cinfinite-scroll-client-inputs-on-load-more"></span>`onLoadMore` | `function` | The observer stays inactive and the native button remains available. | Receives each load request and may return a Promise. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CInfiniteScroll slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="infinite-scroll-slot-cinfinite-scroll-slots-default"></span>`default` | no | `{}` ([`CInfiniteScrollDefaultSlotData`](#infinite-scroll-interface-cinfinite-scroll-default-slot-data)) | Empty result content. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CInfiniteScroll events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="infinite-scroll-event-cinfinite-scroll-events-load-more"></span>`onLoadMore` | `(detail: CInfiniteScrollLoadDetail) => void | Promise<void>` ([`CInfiniteScrollLoadDetail`](#infinite-scroll-interface-cinfinite-scroll-load-detail)) | An enabled action is activated or its observed sentinel intersects. | `{reason, sourceEvent}` ([`CInfiniteScrollLoadDetail`](#infinite-scroll-interface-cinfinite-scroll-load-detail)) | Requests data without mutating result content or submitting from the observer. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CInfiniteScroll CSS variables

Apply these variables to `CInfiniteScroll` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="infinite-scroll-css-cinfinite-scroll-css-gap"></span>`--cui-infinite-scroll-gap` | `length` | Gap among content status action and sentinel. | `0.875rem` |
| <span id="infinite-scroll-css-cinfinite-scroll-css-border"></span>`--cui-infinite-scroll-action-border` | `complete border` | Action boundary. | `Adaptive 1px neutral` |
| <span id="infinite-scroll-css-cinfinite-scroll-css-surface"></span>`--cui-infinite-scroll-action-surface` | `color` | Action surface. | `Canvas` |
| <span id="infinite-scroll-css-cinfinite-scroll-css-radius"></span>`--cui-infinite-scroll-action-radius` | `length` | Action corners. | `0.625rem` |
| <span id="infinite-scroll-css-cinfinite-scroll-css-focus"></span>`--cui-infinite-scroll-focus` | `color` | Action focus ring. | `Highlight` |
| <span id="infinite-scroll-css-cinfinite-scroll-css-muted"></span>`--cui-infinite-scroll-muted` | `color` | Status text. | `Adaptive muted CanvasText` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CInfiniteScroll attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="infinite-scroll-attribute-cinfinite-scroll-attributes-aria-busy"></span>`aria-busy` | Content | `true | false` | Reflects loading without delaying sibling status announcements. |
| <span id="infinite-scroll-attribute-cinfinite-scroll-attributes-data-loading"></span>`data-loading` | Root | `present | absent` | Reflects loading. |
| <span id="infinite-scroll-attribute-cinfinite-scroll-attributes-data-error"></span>`data-error` | Root | `present | absent` | Reflects visible retry state. |
| <span id="infinite-scroll-attribute-cinfinite-scroll-attributes-data-end"></span>`data-end` | Root | `present | absent` | Reflects exhausted results. |
| <span id="infinite-scroll-attribute-cinfinite-scroll-attributes-data-disabled"></span>`data-disabled` | Root | `present | absent` | Reflects disabled requests. |
| <span id="infinite-scroll-attribute-cinfinite-scroll-attributes-data-auto"></span>`data-auto` | Root | `present | absent` | Reflects observation preference. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CInfiniteScroll selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="infinite-scroll-selector-cinfinite-scroll-selectors-root"></span>`[data-citry-ui-part="infinite-scroll"]` | Root | Request boundary and state destination. |
| <span id="infinite-scroll-selector-cinfinite-scroll-selectors-content"></span>`[data-citry-ui-part="content"]` | Content div | Server-owned results. |
| <span id="infinite-scroll-selector-cinfinite-scroll-selectors-status"></span>`[data-citry-ui-part="status"]` | Polite status | Pending error and end announcements. |
| <span id="infinite-scroll-selector-cinfinite-scroll-selectors-action"></span>`[data-citry-ui-part="action"]` | Native button | Explicit Load more or Retry path. |
| <span id="infinite-scroll-selector-cinfinite-scroll-selectors-sentinel"></span>`[data-citry-ui-part="sentinel"]` | Hidden span | Intersection observation target. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="infinite-scroll-interface-reason"></span>`CInfiniteScrollReason` | `Literal["button", "intersection", "retry"]` |
| <span id="infinite-scroll-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="infinite-scroll-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |

</div>

<span id="infinite-scroll-interface-cinfinite-scroll-default-slot-data"></span>

#### `CInfiniteScrollDefaultSlotData`

Empty dataclass: `{}`.

<span id="infinite-scroll-interface-cinfinite-scroll-load-detail"></span>

#### `CInfiniteScrollLoadDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="infinite-scroll-interface-cinfinite-scroll-load-detail-reason"></span>`reason` | `CInfiniteScrollReason` ([`CInfiniteScrollReason`](#infinite-scroll-interface-reason)) | - | Button intersection or retry request source. |
| <span id="infinite-scroll-interface-cinfinite-scroll-load-detail-source-event"></span>`sourceEvent` | `object | None` | - | Native click Event or null for intersection. |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CInfiniteScroll translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="infinite-scroll-translation-cinfinite-scroll-translations-load-more"></span>`citry-ui-infinite-scroll-load-more` | Labels the ordinary load action. | `None.` | `load_more_label` | Stable `$c-tr` text. |
| <span id="infinite-scroll-translation-cinfinite-scroll-translations-retry"></span>`citry-ui-infinite-scroll-retry` | Labels the retry action. | `None.` | `retry_label` | Stable `$c-tr` text. |
| <span id="infinite-scroll-translation-cinfinite-scroll-translations-loading"></span>`citry-ui-infinite-scroll-loading` | Announces a pending request. | `None.` | `loading_label` | Stable `$c-tr` text. |
| <span id="infinite-scroll-translation-cinfinite-scroll-translations-error"></span>`citry-ui-infinite-scroll-error` | Announces a failed request. | `None.` | `error_label` | Stable `$c-tr` text. |
| <span id="infinite-scroll-translation-cinfinite-scroll-translations-end"></span>`citry-ui-infinite-scroll-end` | Announces exhausted results. | `None.` | `end_label` | Stable `$c-tr` text. |

</div>