---
title: Rich messages
url: https://citry.dev/v/0.4.6/i18n/rich-messages/
description: "Let translators position application-owned links and inline components without accepting translated HTML."
---
# Rich messages

Some sentences contain an application-owned link, icon, emphasis element, or
small component. Languages may place that element at different points in the
sentence.

Use `<c-trans>` for this case. It returns translated text mixed with named
Citry fills. Translators control the order, but they never provide HTML,
attributes, URLs, or component names.

## Declare structural parameters as Slot

The source message uses an ordinary Fluent variable and declares it as
`Slot`:


```fluent
# @param {str} $account_name - User accepting the terms.
# @param {Slot} $terms_link - Link to the terms page.
my-app-terms-acceptance =
    { $account_name } accepts the { $terms_link }.
```


`Slot` tells Citry that the value is application-owned structure, not text to
send through Fluent.

## Supply values and named fills

Pass scalar parameters through `c-values` and structural parameters as fills:


```citry-html
<c-trans
  message="my-app-terms-acceptance"
  c-values="{'account_name': account.name}"
>
  <c-fill name="terms_link">
    <a href="/terms">{{ tr("my-app-terms-name") }}</a>
  </c-fill>
</c-trans>
```


The `message` name is the Fluent key. `values` contains every non-`Slot`
parameter. A name cannot appear in both `values` and a fill.

Citry rejects a missing, unknown, or mistyped value or fill. Literal calls are
checked before rendering, and dynamic mappings receive the same validation at
runtime.

## Translators may move or repeat a fill

A translation may place a fill anywhere and may use it more than once:


```fluent
# @param {Slot} $terms_link - Link to the terms page.
my-app-read-terms =
    Read { $terms_link }, then review { $terms_link } again.
```


Citry invokes the lazy fill separately for every occurrence. Repeating a fill
therefore creates a distinct rendered subtree at each position; it does not
clone or move an already-rendered DOM node.

If two occurrences need different state or behavior, declare two named `Slot`
parameters instead of repeating one name.

Every reachable selector branch must use each required Slot at least once. A
Slot must appear as its own direct `{ $slot_name }` placeable. It cannot be a
selector, a formatter argument, or part of a larger Fluent expression.

## Catalog text stays text

Citry escapes every translated text segment:


```fluent
# @param {Slot} $link - Application-owned link.
my-app-safe-message = <unsafe> { $link } & text
```


The `<unsafe>` text renders as text. Only the markup supplied by the
application fill remains structural.

This is why `<c-trans>` does not accept translated HTML. A catalog cannot
create an event handler, unsafe URL, arbitrary attribute, or unexpected
component.

## Rich messages are server-owned

`<c-trans>` renders on the server. A browser `switchLocale()` does not reorder
or recreate its fills. Render the page or fragment again when a rich message
needs another locale.

The component adds no wrapper of its own, so it cannot attach a fallback
message's language to the translated text. Project checking therefore requires
equivalent-language coverage for each selectable locale used at a rich call.
A cross-language rich fallback fails rather than emitting text with incorrect
language metadata.

Use ordinary `tr()` when the result is text only. Use `<c-trans>` only when a
translator must place application-owned structure.