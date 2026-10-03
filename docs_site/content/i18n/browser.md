---
title: Browser i18n
description: Use explicit client providers for small live translations while keeping ordinary server-rendered text simple.
---

# Browser i18n

Most translated text is rendered on the server and arrives as plain
HTML. That is the right default: to change the language of the page,
render it again in the new locale.

Some parts of a page need translations in the browser instead: a widget
with its own language switcher, or Vue code that builds text from data
that changes. This page shows how to enable translations in one part of
the page, how to translate text from Vue, and how to keep
server-rendered text up to date when the language changes.

## Choose who translates

Each piece of text has one owner, and only that owner updates it:

- **Server `tr()`** for most text. The browser receives a plain string
  and never changes it. To show another language, render the page
  again.
- **`$i18n.tr()`** when a Vue expression builds the whole value, not just
  its translation.
- **`$c-tr`** for server-rendered text or an attribute that the browser
  should translate again when the language or its values change.
- **`$i18n.bind()`** for a destination with no fixed place in the HTML,
  such as an element your JavaScript creates.

## Switch from the server

Put the locale in the URL, a form field, a cookie, or another request
input, and render the page again:

```python
from citry.ext.i18n import make_context


def account_page(locale: str):
    context = make_context(app, locale=locale)
    page = Page()
    return page.render(
        provides={"citry_i18n": context},
    )
```

One server render updates every server-translated text. Moving all of a
page's text into Vue instead also works, but many Vue expressions add
work in the browser and can delay the page becoming interactive.

## Enable browser i18n

Wrap that part in `<c-i18n>` with the bare `client` attribute and a
`tag`:

```citry-html
<c-i18n
  tag="main"
  client
>
  ...
</c-i18n>
```

This is a client provider: the element whose content can translate and
switch language in the browser. Citry renders a real `<main>` element
with the `lang` and `dir` attributes, and updates them when the language
changes. The browser loads the i18n code only when the page contains a
client provider.

In Vue expressions and component JavaScript inside it, `$i18n` gives you
the provider's translation service. With nested providers, `$i18n` is
the nearest one. Outside every client provider, or inside a provider
without `client`, `$i18n` is `null`.

The service offers:

- `tr()` and `resolve()` to translate a message;
- `switchLocale()` to change the language;
- `format` for numbers, dates, and other values, and `parse` for
  numbers and percentages;
- `ensureMessages()` to load messages whose ID is only known at runtime;
- `bind()` to keep a custom destination translated;
- `subscribe()`, which runs a callback now and after each language
  change, and returns a function that stops it;
- the read-only `context` (the current locale and direction) and
  `status`.

## Translate in Vue

Call `$i18n.tr()` in a Vue binding. Pass variables as an object, and
choose a Fluent attribute with `{ attr: ... }`:

```citry-html
<c-i18n tag="section" client>
  <button
    v-text="$i18n.tr('my-app-account-actions')"
    :aria-label="$i18n.tr(
      'my-app-account-actions',
      { name: accountName },
      { attr: 'aria-label' },
    )"
  ></button>
  <button @click="$i18n.switchLocale('cs-CZ')">
    Čeština
  </button>
</c-i18n>
```

When the language changes, Vue runs these expressions again.

`resolve()` takes the same arguments. Besides the text, it returns the
locale actually used, its direction, and whether it was a fallback.

## Translate server text

`$c-tr` lets the server render the first value with `tr()`, and the
browser translate it again later. Use it when the text has a fixed
place in the HTML:

```citry-html
<c-i18n tag="section" client>
  <span $c-tr:my-app-loading>
    {{ tr("my-app-loading") }}
  </span>
</c-i18n>
```

The message ID follows `:`. Without brackets, `$c-tr` sets the
element's text.

To translate an HTML attribute instead, name it in square brackets. The
value is a JavaScript object with the message's variables:

```citry-html
<button
  c-aria-label="tr('my-app-toast-dismiss', title=toast.title)"
  $c-tr:my-app-toast-dismiss[aria-label]="{ title: toast.title }"
>
  Dismiss
</button>
```

The page first shows the server value. Once the element is mounted, the
browser translates it again whenever the language changes or a Vue
value in the object changes, such as `toast.title`.

Leave out the value when the message has no variables that change in
the browser.

Citry checks the variables: a missing or unknown one is an error, and so
is a value whose type Citry can tell is wrong.

## Switch the language

`switchLocale(locale)` changes the language of one client provider: the
one `$i18n` refers to at that call. Other client providers on the page
keep their language.

The provider first loads every message the new locale needs. Then it
changes its context and its `lang` and `dir` attributes together. If
loading fails, the old language stays.

Nested client providers follow the parent's language, unless they set
their own `locale`. A provider without `client` inside a client provider
keeps its server-rendered language and needs a real `tag`:

```citry-html
<c-i18n tag="main" client>
  <span v-text="$i18n.tr('my-app-live-title')"></span>

  <c-i18n tag="section">
    {{ tr("my-app-fixed-server-copy") }}
  </c-i18n>
</c-i18n>
```

## Format and parse

`$i18n.format` uses the same named profiles as the server:

```citry-html
<output
  v-text="$i18n.format.number(
    '12345.50',
    { format: 'measurement' },
  )"
></output>
```

`$i18n.parse` reads numbers and percentages only. See
[Format values](/i18n/formatting/#format-values-in-the-browser) and
[Parse localized input](/i18n/parsing/#parse-numbers-and-percentages-in-the-browser).

## Load IDs from variables

Citry sends the browser only the messages the page uses. It finds them
by reading message IDs written literally in your code, such as
`$i18n.tr('my-app-account-title')`.

When the ID comes from a variable, the browser cannot know it in
advance. With Citry mounted in one of its
[web framework integrations](/advanced/web-frameworks/), load the message from
the server before calling `tr()`:

```javascript
await $i18n.ensureMessages(messageKey);
result = $i18n.tr(messageKey);
```

The server rejects the whole request if it names an unknown or private
message, comes from an older catalog version, or asks for too many
messages.

For a static page with no server to ask, list every possible ID on the
component:

```citry
class DynamicNotice(Component):
    citry = app

    class I18n:
        client_messages = (
            "my-app-notice-success",
            "my-app-notice-error",
        )
```

Listing a message includes all its attributes. Literal IDs do not need
to be listed.

## Bind text in JS

Use `bind()` when the text has no fixed place in the HTML for `$c-tr`,
such as an element or property your JavaScript manages. Here it keeps
an `aria-label` translated from an
[`onServerRender`](/concepts/client-interactivity/#react-after-a-server-render)
callback, which runs after each server render of the component:

```javascript
$component({
  onServerRender({ component }) {
    const target = component.$refs.toast;
    const i18n = component.$i18n;
    if (!(target instanceof HTMLElement) || !i18n) return;

    const binding = i18n.bind({
      message: "my-app-toast-dismiss",
      values: () => ({ title: component.toastTitle }),
      onChange(text) {
        target.setAttribute("aria-label", text);
      },
    });

    return () => binding.dispose();
  },
});
```

`onChange` runs at once, and again when the language changes or a
reactive value read in `values()` changes. If `values()` reads ordinary
JavaScript state that Vue does not track, call `binding.refresh()` after
changing it. Call `dispose()` when the destination goes away before the
component does.

For a one-time translation that should not update, call `i18n.tr()`.

## Less common cases

### Which IDs are found

Citry sends the browser every message it finds written literally in:

- `$i18n.tr()` and `$i18n.resolve()` calls in Vue expressions;
- `$c-tr` bindings;
- `component.$i18n` calls in a `$component` callback, and `this.$i18n`
  calls in a method, computed property, `data()`, lifecycle hook,
  `provide()`, or `watch` handler;
- calls on a variable that holds the service, such as
  `const i18n = component.$i18n`, then `i18n.tr(...)`. A `let` or `var`
  also works when it is assigned only once;
- `bind()` calls whose options are written as an object literal.

Messages that a found message includes come along too.

Citry does not follow the service through destructuring
(`const { bind } = component.$i18n`), a copy (`const other = i18n`),
optional chaining (`component?.$i18n`), or your own helper function, and
it cannot read an ID built at runtime. Such a call fails in the browser
with an error that names the message. Load the message with
`ensureMessages()` or list it in `client_messages`.

Messages used only by server `tr()` calls are not sent to the browser,
because their output is final HTML.

### The full $c-tr syntax

```text
$c-tr:message.fluent-attribute[html-attribute]
```

The message ID is required. `.fluent-attribute` picks a Fluent attribute
of the message, and `[html-attribute]` picks the HTML attribute to set;
both are optional.

The HTML attribute must be one of `alt`, `aria-description`,
`aria-label`, `aria-placeholder`, `aria-roledescription`,
`aria-valuetext`, `placeholder`, or `title`.

Empty names, empty or unclosed brackets, extra punctuation, uppercase
spellings, and other HTML attributes are errors. Rendering,
`citry check`, and the editor all report them.

### Add `$c-tr` from Python

To decide during the server render whether to add the binding, use the
`c-` prefix, `c-$c-tr:...="python_expression"`, or return a `$c-tr:...`
key from `c-bind`. The Python value must be:

- a string, which is the browser expression for the variables object;
- `True`, for a binding without variables (an empty string means the
  same);
- `None` or `False`, for no binding.

Any other value raises `TypeError`. The binding must be on a plain HTML
element that holds the text or attribute itself, not on a component
tag.

### Avoid `v-text` with `$c-tr`

That gives two browser mechanisms ownership of the same text. Give each
text one owner.

### Translate new content

When an [Events](/events/) handler (server code that runs after a
browser event) renders part of the page again, the new content
brings the messages and `$c-tr` bindings it uses, and the replaced
content releases its own. Content rendered inside a client provider
keeps using that provider.

An [HTML fragment](/advanced/html-fragments/) that you insert yourself
starts its own Vue app outside every other Citry Vue app, so no client
provider on the page reaches it. Wrap the fragment's content in its own
`<c-i18n client>` provider when it needs browser translations.
