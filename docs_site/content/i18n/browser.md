---
title: Browser i18n
description: Use explicit client providers for small live translations while keeping ordinary server-rendered text simple.
---

# Browser i18n

Citry keeps server-owned and browser-owned translations separate. This gives
each piece of text one clear owner and avoids hidden DOM tracking.

## Choose who owns each translated value

### Render ordinary text on the server

```citry-html
<h1>{{ tr("my-app-account-title") }}</h1>
```

The browser receives a plain string. A later `switchLocale()` does not update
it because the browser does not know that the text came from `tr()`.

Use this for most page content.

### Render on the server, then keep a stable DOM destination current

Use `tr()` for the initial HTML and `$c-tr` for the explicit browser binding:

```citry-html
<c-i18n tag="section" client>
  <button
    c-aria-label="tr('my-app-toast-dismiss', title=toast.title)"
    $c-tr:my-app-toast-dismiss[aria-label]="{ title: toast.title }"
  >
    Dismiss
  </button>
  <span $c-tr:my-app-loading>
    {{ tr("my-app-loading") }}
  </span>
</c-i18n>
```

The server value remains the initial value. The checked binding starts tracking
its Vue values as soon as the element mounts. Changing `toast.title`
retranslates the attribute even if the locale has never changed; changing the
provider locale retranslates it with the latest values.

Square brackets select the HTML attribute to write. With no brackets, the
destination is `textContent`. A dot is reserved for a Fluent message attribute,
so the complete form is
`$c-tr:message.fluent-attribute[html-attribute]`. The HTML attribute must be
one of `alt`, `aria-description`, `aria-label`, `aria-placeholder`,
`aria-roledescription`, `aria-valuetext`, `placeholder`, or `title`.

Python can also decide the binding during the server render: write
`c-$c-tr:...="python_expression"`, or return a `$c-tr:...` key from `c-bind`.
The binding is valid only on the final literal HTML element that owns the text
or attribute. Citry checks the directive during the render, removes it from
the HTML, and leaves a binding ID that points to the checked binding.

The directive name has one exact grammar:

```text
$c-tr:message.fluent-attribute[html-attribute]
```

The Fluent attribute and HTML attribute are independently optional. The
message ID after `:` is always required. Empty names, empty brackets, missing
closing brackets, extra punctuation, uppercase directive spellings, and HTML
attributes outside Citry's safe destination list are errors in rendering,
`citry check`, and the language server.

The value is a JavaScript object expression containing the message's named
inputs. Citry checks literal keys and any value types it can prove from
JavaScript literals or component browser data. Missing, extra, or provably
mistyped inputs are errors:

```citry-html
<output
  c-title="tr('my-app-result-count', count=result_count)"
  $c-tr:my-app-result-count[title]="{ count: result_count }"
></output>
```

If the binding does not need live inputs, omit its value. The server-rendered
`tr()` call remains the source of the initial checked values.

For a server-conditional `c-$c-tr` or a `$c-tr` entry returned by `c-bind`, use
`True` to enable that same presence-only form and `None` or `False` to remove
it. A string supplies a reactive named-values expression. An empty string also
means presence-only, but `True` communicates that intent more clearly.

### Let a Vue expression own the whole value

```citry-html
<c-i18n tag="section" client>
  <span v-text="$i18n.tr('my-app-account-title')"></span>
  <button @click="$i18n.switchLocale('cs-CZ')">Čeština</button>
</c-i18n>
```

Vue owns the `<span>` text. Calling `switchLocale()` replaces the provider's
readonly context, so the expression runs again.

Use this general Vue form when the expression computes more than a
translation. For a stable server-rendered text or attribute, `$c-tr` keeps the
server value and only retranslates it, so you do not repeat the expression in
Vue.

### Change a whole page from the server

For a page-wide language change, put the locale in an explicit URL, form,
cookie, or other request input and render the page again:

```python
from citry.ext.i18n import make_context


def account_page(locale: str):
    context = make_context(app, locale=locale)
    return Page().render(
        provides={"citry_i18n": context},
    )
```

An application may put every translated field under Vue, but a large number
of expressions adds browser startup work and can delay interactivity. A server
rerender updates every server value through one normal render.

## Create a client provider

Add the bare `client` attribute and provide a real wrapper tag:

```citry-html
<c-i18n
  tag="main"
  client
>
  ...
</c-i18n>
```

The real element owns the browser scope and its `lang` and `dir` attributes.
The i18n browser runtime loads only when a rendered tree contains a
client-enabled provider.

`$i18n` is the service of the nearest client provider that encloses the Vue
expression. Citry passes each provider's service down to its descendants
through Vue's provide/inject, so a provider elsewhere on the page does not
affect it. Below a server-only provider, or outside every client provider,
`$i18n` is `null`.

## Use the browser service

The service exposes:

- readonly `context` and `status` values;
- `tr()` and `resolve()`;
- `bind()` for browser-created or custom destinations;
- `ensureMessages()`;
- `switchLocale()`;
- `subscribe()`, which runs a callback now and after each successful locale
  switch, and returns a function that stops it;
- named operations under `format`; and
- strict number and percent operations under `parse`.

Translate a message or attribute:

```citry-html
<button
  v-text="$i18n.tr('my-app-account-actions')"
  :aria-label="$i18n.tr(
    'my-app-account-actions',
    { name: accountName },
    { attr: 'aria-label' },
  )"
></button>
```

`resolve()` returns frozen text plus the selected locale, direction, and
fallback flag. `tr()` returns only its text.

Format values with the same named profiles as the server:

```citry-html
<output
  v-text="$i18n.format.number(
    '12345.50',
    { format: 'measurement' },
  )"
></output>
```

Browser parsing supports numbers and percentages. See
[Parse localized input](/i18n/parsing/) for the exact result shape and for
why date and time parsing runs only on the server.

## Bind a browser-created or custom destination

An `onServerRender` callback can use the same nearest provider through the
component instance. Use `bind()` when there is no stable HTML text or
attribute for `$c-tr` to own:

```javascript
$component({
  onServerRender({ component }) {
    const destination = component.$refs.toast;
    const i18n = component.$i18n;
    if (!(destination instanceof HTMLElement) || !i18n) return;

    const binding = i18n.bind({
      message: "my-app-toast-dismiss",
      values: () => ({ title: component.toastTitle }),
      onChange(text) {
        destination.setAttribute("aria-label", text);
      },
    });

    return () => binding.dispose();
  },
});
```

`onChange` runs immediately. Reactive values read by `values()` and provider
locale changes both cause another translation. Call `refresh()` only after
changing ordinary non-reactive JavaScript state, and call `dispose()` when a
destination whose lifetime is not already component-owned goes away. For a
one-time lookup that should not replay, use ordinary `i18n.tr()`.

## Use the smallest browser owner

Choose the narrowest API that owns the destination:

- Use ordinary `tr()` when a server render or page reload should change the
  text.
- Use `$c-tr` for stable `textContent` or one of Citry's allowlisted HTML
  attributes. Pair it with the initial server `tr()` value.
- Use `$i18n.tr()` when a Vue expression already owns the complete value,
  not merely its translation.
- Use `i18n.bind()` for browser-created values, custom objects, native
  properties, or callbacks that have no stable HTML destination.

Keep message IDs literal when possible so Citry can preload and check their
exact outputs. Keep the named-values object explicit instead of hiding it
behind a computed spread when editor validation is useful. Do not add both
`v-text` and `$c-tr` to the same text destination; that gives two browser
systems ownership of the same value. Dispose imperative bindings whose
lifetime is shorter than their component, and use `refresh()` only for
ordinary non-reactive state.

## Let Citry preload literal message names

Citry finds literal `$i18n.tr()` and `$i18n.resolve()` calls in Vue
expressions, checked `$c-tr` declarations, and literal calls on
`component.$i18n` or `this.$i18n` in component JavaScript. An `i18n.bind({
message: "...", output: "...", ... })` call written as an object literal
contributes its exact output too. Citry includes those outputs and their
referenced messages and private terms in the browser artifact.

In component JavaScript, Citry recognizes a call when it can prove the
receiver is the component's i18n service:

- `component.$i18n.tr(...)`, `.resolve(...)`, and `.bind(...)` in a
  `$component` callback, and `this.$i18n` in a method, computed getter or
  setter, `data()`, lifecycle hook, `provide()`, or `watch` handler;
- a variable that holds the service, such as
  `const i18n = component.$i18n`, followed by `i18n.tr(...)` or
  `i18n.bind(...)`. A `let` or `var` also works when it is declared
  once and nothing assigns it again.

Citry does not follow the service through destructuring
(`const { bind } = component.$i18n`), a copy of the variable
(`const other = i18n`), optional chaining on the component
(`component?.$i18n`), or a call to your own helper function. It also
cannot read a message ID built at runtime, such as a template string or
a variable. Citry does not send those messages to the browser, so the
call fails in the browser with an error that names the message. Load
those IDs with `ensureMessages()` or list them in `client_messages`, as
the next section shows.

A message reference is transitive. If message A includes public message B,
loading A also includes B and the private terms needed to format the selected
result.

Static analysis does not need to find server-side `tr()` calls for browser
updates. Their rendered output stays server-owned.

## Load a dynamic message before calling tr

When Citry is mounted in one of its
[web framework integrations](/web-frameworks/), the browser can ask the
server for more messages. Load a dynamic public ID before the synchronous
`tr()` call:

```javascript
await $i18n.ensureMessages(messageKey);
result = $i18n.tr(messageKey);
```

Citry sends a bounded request containing the locale, required public messages,
and current catalog revision. Unknown private IDs, stale revisions, and
oversized requests fail without returning a partial artifact.

For static output with no server endpoint, list every possible dynamic ID on
the component:

```citry
class DynamicNotice(Component):
    citry = app

    class I18n:
        client_messages = (
            "my-app-notice-success",
            "my-app-notice-error",
        )
```

Literal calls do not need to be repeated in `client_messages`. Listing a
message includes all its attributes.

## Understand what switchLocale changes

`switchLocale(locale)` affects only the provider returned by `$i18n` at that
call site. It loads and validates the target locale's known requirements, then
commits the context and wrapper `lang` and `dir` together. If loading fails, the
old context remains active.

Descendant client providers that inherit their locale follow the parent.
A descendant with an explicit locale stays fixed. A server-only provider inside
a client provider is a hard browser boundary and also needs a real `tag`:

```citry-html
<c-i18n tag="main" client>
  <span v-text="$i18n.tr('my-app-live-title')"></span>

  <c-i18n tag="section">
    {{ tr("my-app-fixed-server-copy") }}
  </c-i18n>
</c-i18n>
```

The switch does not walk the whole document. Another client provider elsewhere
has its own service and switches independently.

## Re-rendered content and inserted fragments bring their own messages

When an Events handler renders part of the page again, the new content
carries the message requirements and `$c-tr` bindings its browser
expressions use. Content rendered inside a client provider stays under that
provider, so `$i18n` and `$c-tr` there keep using the provider's service.
Replacing the content releases the requirements and bindings of the content
it replaces.

An [HTML fragment](/advanced/html-fragments/) that you insert yourself
starts its own Vue app and must go outside every other Citry Vue app, so a
client provider on the page cannot reach its content. Wrap the fragment's
content in its own `<c-i18n client>` provider when it needs browser
translations.

The i18n extension does not send every public message in the project just
because new content may arrive later; each render sends what it uses.
