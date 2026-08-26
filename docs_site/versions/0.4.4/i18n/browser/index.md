---
title: Browser i18n
url: https://citry.dev/v/0.4.4/i18n/browser/
description: "Use explicit client providers for small live translations while keeping ordinary server-rendered text simple."
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
its Alpine values as soon as the element initializes. Changing `toast.title`
retranslates the attribute even if the locale has never changed; changing the
provider locale retranslates it with the latest values.

Square brackets select the HTML attribute to write. With no brackets, the
destination is `textContent`. A dot is reserved for a Fluent message attribute,
so the complete form is
`$c-tr:message.fluent-attribute[html-attribute]`. Citry permits only a small,
documented set of safe HTML attribute destinations.

Like other flexible Citry attributes, a translation binding may be written
directly, as `c-$c-tr:...="expression"`, or returned as a `$c-tr:...` key from
`c-bind`. The binding is valid only on the final literal HTML element that owns
the text or attribute. Citry removes the directive and emits an opaque checked
binding ID; it never sends the directive expression as an unchecked DOM
protocol.

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

### Let an Alpine expression own the whole value


```citry-html
<c-i18n tag="section" client>
  <span x-text="$i18n.tr('my-app-account-title')"></span>
  <button @click="$i18n.switchLocale('cs-CZ')">Čeština</button>
</c-i18n>
```


Alpine owns the `<span>` text. Calling `switchLocale()` replaces the provider's
readonly context, so the expression runs again.

Use this general Alpine form when the expression itself owns more than a
translation binding. For a stable server-rendered text or attribute,
`$c-tr` avoids duplicating that broader ownership logic.

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


An application may put every translated field under Alpine, but a large number
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

`$i18n` resolves the nearest client provider at the element where the Alpine
expression runs. It is the concise form of Citry's ordinary browser
provide/inject lookup.

## Use the browser service

The service exposes:

- readonly `context` and `status` values;
- `tr()` and `resolve()`;
- `bind()` for browser-created or custom destinations;
- `ensureMessages()`;
- `switchLocale()`;
- named operations under `format`; and
- strict number and percent operations under `parse`.

Translate a message or attribute:


```citry-html
<button
  x-text="$i18n.tr('my-app-account-actions')"
  x-bind:aria-label="$i18n.tr(
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
  x-text="$i18n.format.number(
    '12345.50',
    { format: 'measurement' },
  )"
></output>
```


Browser parsing supports numbers and percentages. See
[Parse localized input](/v/0.4.4/i18n/parsing/) for the exact result shape and the
current temporal boundary.

## Bind a browser-created or custom destination

`$component` callbacks receive `i18n` from the same nearest provider. Use
`bind()` when there is no stable HTML text or attribute for `$c-tr` to own:


```javascript
$component(({ i18n, state, toast }, control) => {
  const binding = i18n.bind({
    message: "my-app-toast-dismiss",
    values: () => ({ title: state.toastTitle }),
    onChange(text) {
      toast.update({ dismissLabel: text });
    },
  });

  control.registerCleanup(binding.dispose);
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
- Use `$i18n.tr()` when an Alpine expression already owns the complete value,
  not merely its translation.
- Use `i18n.bind()` for browser-created values, custom objects, native
  properties, or callbacks that have no stable HTML destination.

Keep message IDs literal when possible so Citry can preload and check their
exact outputs. Keep the named-values object explicit instead of hiding it
behind a computed spread when editor validation is useful. Do not add both
`x-text` and `$c-tr` to the same text destination; that gives two browser
systems ownership of the same value. Dispose imperative bindings whose
lifetime is shorter than their component, and use `refresh()` only for
ordinary non-reactive state.

## Let Citry preload literal message names

Citry finds literal `$i18n.tr()` and `$i18n.resolve()` calls in Alpine
expressions, checked `$c-tr` declarations, and literal `i18n` calls in
component JavaScript. A bounded object-literal
`i18n.bind({ message: "...", output: "...", ... })` contributes its exact
output too. Citry includes those outputs and their referenced messages and
private terms in the browser artifact.

A message reference is transitive. If message A includes public message B,
loading A also includes B and the private terms needed to format the selected
result.

Static analysis does not need to find server-side `tr()` calls for browser
updates. Their rendered output stays server-owned.

## Load a dynamic message before calling tr

In a mounted application, load a dynamic public ID before the synchronous
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
  <span x-text="$i18n.tr('my-app-live-title')"></span>

  <c-i18n tag="section">
    {{ tr("my-app-fixed-server-copy") }}
  </c-i18n>
</c-i18n>
```


The switch does not walk the whole document. Another client provider elsewhere
has its own service and switches independently.

## Inserted fragments add their own requirements

A fragment rendered under an existing client provider carries the message
requirements and checked binding records used by its browser expressions. When
Citry Events adopts that fragment, and the provider has already switched away
from the fragment's server-rendered locale, Citry loads the provider's
current-locale closure and reconciles the fragment's bound text and attributes
before Alpine or component callbacks activate. The ownership rule is Citry's
logical provider route, including slots and teleports; it is not DOM
`closest()`.

When the browser commits the fragment, Citry adds its requirement and binding
reference counts to the provider. Removing or morphing it removes them again.
A failed current-locale load leaves the old live region unchanged and activates
none of the incoming fragment.

Direct host `innerHTML` insertion still gets eventual inert-manifest discovery
from Citry's permanent observer, but a synchronous host insertion cannot wait
for current-locale loading before other browser code sees those nodes. Use the
Citry Events fragment action path when pre-activation locale reconciliation is
required.

This follows the same fragment lifecycle as Citry's other browser metadata.
The i18n extension does not send every public message in the project merely
because one fragment may arrive later.