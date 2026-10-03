---
title: Built-in tags
description: The c-* tags Citry provides in every component template.
---

# Built-in tags

Look up a built-in `<c-*>` tag here: what it does, its attributes, and a
short example. Every component template can use these tags without
registering or importing anything.

- **Control flow:** [`<c-if>`](#c-if), [`<c-elif>`](#c-elif),
  [`<c-else>`](#c-else), [`<c-for>`](#c-for), and
  [`<c-empty>`](#c-empty)
- **Slots:** [`<c-slot>`](#c-slot) and [`<c-fill>`](#c-fill)
- **Dynamic output:** [`<c-component>`](#c-component) and
  [`<c-element>`](#c-element)
- **Data and resilience:** [`<c-provide>`](#c-provide),
  [`<c-cache>`](#c-cache), and
  [`<c-error-fallback>`](#c-error-fallback)
- **Targeted updates:** [`<c-mark>`](#c-mark)
- **Internationalization:** [`<c-i18n>`](#c-i18n) and
  [`<c-trans>`](#c-trans)
- **Page assets:** [`<c-css>`](#c-css) and [`<c-js>`](#c-js)
- **Literal template text:** [`<c-raw>`](#c-raw)

## Control flow

<h3 id="c-if"><code>&lt;c-if&gt;</code></h3>

Render a block only when its `cond` expression is truthy. Any number of
`<c-elif>` branches and one `<c-else>` may follow it.

```citry-html
<c-if cond="is_admin">
  <p>Administrator tools</p>
</c-if>
```

[Conditions and loops](/syntax/control-flow/) covers the inline `c-if`
attribute, truthiness, and branch order.

<h3 id="c-elif"><code>&lt;c-elif&gt;</code></h3>

Add another condition to a `<c-if>` chain. The branch renders when every
earlier condition was false and its own `cond` is truthy.

```citry-html
<c-if cond="is_admin">Admin</c-if>
<c-elif cond="is_editor">Editor</c-elif>
```

<h3 id="c-else"><code>&lt;c-else&gt;</code></h3>

Add the final fallback to a `<c-if>` chain. It takes no `cond`.

```citry-html
<c-if cond="is_signed_in">Account</c-if>
<c-else>Sign in</c-else>
```

<h3 id="c-for"><code>&lt;c-for&gt;</code></h3>

Repeat a block for every item in an iterable. The `each` attribute is
written like a Python `for`: a target, `in`, and an expression.

```citry-html
<c-for each="book in books">
  <p>{{ book.title }}</p>
</c-for>
```

[Conditions and loops](/syntax/control-flow/#unpack-and-filter-values)
covers unpacking, filtering, and variable scope.

<h3 id="c-empty"><code>&lt;c-empty&gt;</code></h3>

Show an empty state when the `<c-for>` right before it has no items.

```citry-html
<c-for each="book in books">
  <p>{{ book.title }}</p>
</c-for>
<c-empty>No books yet.</c-empty>
```

## Slots

<h3 id="c-slot"><code>&lt;c-slot&gt;</code></h3>

Mark a place in a component where the template that uses it can add
content. Leave out `name` for the default slot, and name each extra slot.
Content inside the tag is shown when no content is passed.

```citry-html
<article>
  <c-slot />
  <footer>
    <c-slot name="footer">No footer supplied.</c-slot>
  </footer>
</article>
```

[Slots](/concepts/slots/) covers required slots, slot data, dynamic
names, and fallback content.

<h3 id="c-fill"><code>&lt;c-fill&gt;</code></h3>

Send a block of content to a named slot of the component you are using.
For the default slot alone, put the content directly in the component's
body instead.

```citry-html
<c-Panel>
  <c-fill name="footer">
    <a href="/help/">Get help</a>
  </c-fill>
</c-Panel>
```

## Dynamic output

<c-builtin tag="component" c-level="3" />

```citry-html
<c-component is="card" />
<c-component c-is="chosen_component" />
```

<c-builtin tag="element" c-level="3" />

```citry-html
<c-element c-is="tag" class="heading">
  {{ text }}
</c-element>
```

[Dynamic components](/advanced/dynamic-components/) has complete
examples and explains how component names differ from HTML tag names.

## Data and resilience

<c-builtin tag="provide" c-level="3" />

```citry-html
<c-provide key="theme" name="dark">
  <c-theme-label />
</c-provide>
```

[Provide and inject](/concepts/provide-and-inject/) shows how a component
reads the value.

<c-builtin tag="cache" c-level="3" />

```citry-html
<c-cache
  key="account-menu"
  c-vary="[current_user.id, locale]"
  c-ttl="300"
>
  <c-account-menu
    c-user="current_user"
    c-locale="locale"
  />
</c-cache>
```

[Caching](/performance/caching/) covers keys, expiry, and clearing
entries.

<c-builtin tag="error-fallback" c-level="3" />

```citry-html
<c-error-fallback fallback="Recent activity is unavailable">
  <c-recent-activity />
</c-error-fallback>
```

[Error boundaries](/concepts/error-boundaries/) shows a fallback with
markup and nested boundaries.

## Targeted updates

<c-builtin tag="mark" c-level="3" />

To update the marked part, return
`actions.Render(..., target="mark:<name>")` from an event handler:

```citry-html
<c-mark name="summary">
  <c-CartSummary c-cart="cart" />
</c-mark>
```

Write `name` as a plain attribute. A computed `c-name`, or a name that
breaks the rules above, raises `ValueError` when the component renders.
`<c-mark>` takes no `<c-fill>`; put the content directly inside it.

See [`<c-mark>` partial update](/events/actions/#update-one-part-of-the-page).

!!! note "You cannot name a component `mark`"

    A component class named `Mark`, or one registered as `mark`, fails when
    it is defined:

    ```text
    AlreadyRegistered: Cannot register 'Mark' as 'mark': the name is
    reserved for the built-in <c-mark> component.
    ```

    Rename the class, for example to `Highlight`, and write
    `<c-highlight>` in your templates.

## Internationalization

<c-builtin tag="i18n" c-level="3" />

Use it to set the locale for one part of the page. Add `tag` when that
part needs `lang` and `dir` attributes. To let browser code in that part
translate and format text, add the bare `client` attribute as well:

```citry-html
<c-i18n locale="ar-EG" tag="aside">
  <c-account-card />
</c-i18n>
```

See [Locales and context](/i18n/locale-context/) and
[Browser i18n](/i18n/browser/).

<c-builtin tag="trans" c-level="3" />

Use it when a translated sentence contains a link or a component, and the
translator decides where it goes:

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

See [Rich messages](/i18n/rich-messages/).

## Page assets

<c-builtin tag="css" c-level="3" />

<c-builtin tag="js" c-level="3" />

Without them, Citry puts the CSS at the end of `<head>` and the
JavaScript at the end of `<body>`. Use the tags to place them somewhere
else, such as before your own stylesheet:

```citry-html
<head>
  <c-css />
  <link rel="stylesheet" href="/static/overrides.css">
</head>
<body>
  <c-Chart c-points="[1, 2, 3]" />
  <c-js />
</body>
```

[Asset placement][dependencies-guide] explains where Citry puts the
collected files and component assets.

## Literal template text

<h3 id="c-raw"><code>&lt;c-raw&gt;</code></h3>

Keep text that looks like template syntax exactly as written. Citry does
not evaluate expressions or component tags inside `<c-raw>`.

```citry-html
--8<-- "docs_site/snippets/builtin_raw.html"
```

[Literal text](/syntax/raw/)
covers what is trusted and the exact rules.

[dependencies-guide]: /advanced/asset-placement/
