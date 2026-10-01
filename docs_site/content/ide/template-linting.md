---
title: Template linting
description: Configure unknown template, Vue, and component JavaScript names, leftover Alpine attributes, and invalid HTML attribute values, consistently across Citry tools.
---

# Template linting

Citry reports a free template root that is not available from the component's
template data, a lexical `c-for` or `c-fill` binding, or a known global. The
rule code is `citry.template.unknown-variable`, and its default severity is an
error.

Citry applies the same strict default to browser code that it can prove belongs
to a component:

- `citry.vue.unknown-variable` checks free roots in Vue expressions.
- `citry.component-js.unknown-variable` checks free names inside a
  `$component` callback or configuration object's `onServerRender` callback.

The component JavaScript rule catches a missing binding, such as an
undeclared `settings` name inside an `onServerRender` callback:

```javascript
$component({
  onServerRender({ component }) {
    component.ready = settings.ready;
  },
});
```

Use an instance value such as `component.ready` instead of an undeclared
name, or declare a real project global through the lint settings when another
script supplies that name.

A misspelled instance value is an error by default too. When the component's
`js_data()` keys are known and its Vue Options are written out in the source,
`citry.component-js.unknown-member` reports a `component.<name>` or
`this.<name>` read that names no `js_data()` key, prop, `data()` key, `setup`
binding, method, computed value, or injection:

```javascript
// js_data() returns {"likes": ...}
$component(({ component }) => {
  // error: Component instance member 'like' is not defined
  // by this component.
  console.log(component.like);
});
```

Options that merge in `mixins` or `extends` turn this check off, because
their names are not in the source. A plugin that adds an instance property
should name it with a `$` prefix, such as `$api`; the rule reports an
unprefixed name it cannot find.

A Vue binding that reads a Python loop variable never sees the loop value.
Python runs the `c-for` loop on the server, but Vue evaluates `:title` later
in the browser, where `item` does not exist:

```citry-html
<!-- Vue looks up `item` in browser state. -->
<li c-for="item in items" :title="item"></li>

<!-- Python sets the attribute for each item. -->
<li c-for="item in items" c-title="item"></li>
```

Citry reports each such read once. When Citry knows all of the component's
browser names, the read is a `citry.vue.unknown-variable` error whose message
says the name is a Python variable. When it cannot know them all, for
example because the Vue Options use `mixins`, or when you set
`rule_unknown_vue_variable="ignore"`, the read is a
`citry.vue.python-variable` warning that suggests the `c-` attribute form.

The warning also fires when the component's browser data, such as a
`js_data()` key, defines the same name. Vue then shows the component's value
instead of the loop value without any error, so the message names both
meanings and suggests the `c-` attribute or renaming one of them.

Both cover names from `c-for` loops and `c-fill` bindings in every Vue
expression, including `v-text`, `v-show`, and `@click`. Neither reports the
read when a Vue `v-for` or slot alias of the same name encloses the
expression, because Vue then reads its own loop or slot value.

See the diagnostic reference entries for
[template variables](/ide/diagnostics/#citry.template.unknown-variable),
[Vue variables](/ide/diagnostics/#citry.vue.unknown-variable),
[Python variables in Vue expressions](/ide/diagnostics/#citry.vue.python-variable),
[component JavaScript variables](/ide/diagnostics/#citry.component-js.unknown-variable),
[component instance members](/ide/diagnostics/#citry.component-js.unknown-member),
[Alpine attributes](/ide/diagnostics/#citry.template.alpine-attribute),
and [`x-cloak`](/ide/diagnostics/#citry.template.alpine-cloak)
for their stable messages and reporting surfaces.

The application owns this policy. `citry check` and the language server use
the same settings, so there is no separate VS Code lint preference.

## Configure the application

Pass one [`LintSettings`][citry.LintSettings] object to [`Citry`][citry.Citry]:

```python
from collections.abc import Callable
from typing import Annotated

from citry import Citry, LintSettings

app = Citry(
    template_globals={
        "site_name": "Citry",
    },
    lint=LintSettings(
        rule_unknown_template_variable="error",
        template_variables={
            "request": Annotated[
                "django.http.HttpRequest",
                "The current framework request.",
            ],
            "url_for": Callable[[str], str],
        },
        rule_unknown_vue_variable="error",
        vue_variables={
            "$analytics": Annotated[
                "myapp.browser.Analytics",
                "Analytics available as a custom Vue magic.",
            ],
        },
        rule_unknown_component_js_variable="error",
        component_js_globals={
            "featureFlags": Annotated[
                "myapp.browser.FeatureFlags",
                "Flags installed by the host page.",
            ],
        },
        rule_unknown_component_js_member="error",
        rule_vue_python_variable="warning",
        rule_alpine_attribute="warning",
        rule_alpine_cloak="error",
        rule_invalid_attribute_value="warning",
    ),
)
```

Each `rule_*` field accepts `"ignore"`, `"warning"`, or `"error"`.
`rule_vue_python_variable`, `rule_alpine_attribute`, and
`rule_invalid_attribute_value` default to `"warning"`; `rule_alpine_cloak`
and the `rule_unknown_*` fields default to `"error"`.
`rule_unknown_component_js_member` sets the severity of
`citry.component-js.unknown-member`. When one JavaScript file serves several
components, the strictest of their severities applies, so every one of them
must set `"ignore"` to silence the rule for that file.

Every key already present in `Citry.template_globals` is known automatically.
Citry conservatively infers ordinary scalar, homogeneous-container, and
importable object types from their runtime values. You do not repeat those
keys in the lint settings merely to suppress a diagnostic.

`template_variables` is analysis metadata. It does not inject a runtime value.
Use it for request-scoped or framework-provided names that enter the render by
another integration. A plain annotation supplies a type. `Annotated[T,
"description"]` also supplies hover documentation. Qualified string
annotations are resolved by the language server in the selected project
environment.

`vue_variables` and `component_js_globals` follow the same annotation
convention and also supply analysis metadata only. Use `vue_variables` for
custom Vue magics or values supplied to a Vue scope outside Citry. Use
`component_js_globals` for project scripts that make a real global available
inside `$component`. Citry passes `onServerRender` one object with
`component` and the other callback fields; server defaults, props, refs,
i18n and event helpers are reached through those fields or the `component`
instance. Listing one of those names as a global would hide a real initializer
bug.

## Override one component

Use a nested `Lint` declaration when one component has a different contract:

```citry
from typing import Annotated

from citry import Component


class AccountCard(Component):
    class Lint:
        rule_unknown_template_variable = "warning"
        rule_unknown_component_js_variable = "warning"
        rule_unknown_component_js_member = "warning"
        template_variables = {
            "account_context": Annotated[
                "myapp.accounts.AccountContext",
                "Context added by the account page integration.",
            ],
        }
        component_js_globals = {
            "accountClient": Annotated[
                "myapp.browser.AccountClient",
                "Client installed by the account page.",
            ],
        }
```

Nested `Lint` declarations compose through component inheritance. The nearest
rule wins, variable mappings merge by name, and `Lint = None` clears inherited
component overrides and returns to the application policy.

`Lint` is a nested component configuration class, not a Citry extension. It
does not install hooks or commands. Citry captures it while defining the
component and combines it with inherited lint declarations.

Go to Definition and Go to Declaration link a lint-only variable to its exact
authored dictionary key when the selected application uses a direct `Citry`
assignment or simple settings aliases. Component variables link to the nested
`Lint` class that supplied the effective value, including inherited and
library-component declarations. Computed mappings and factory-built settings
remain valid at runtime but have no guessed navigation target.

## Find leftover Alpine attributes

Citry uses Vue, so an Alpine attribute left in a template does nothing.
Citry renders `x-data` or `x-on:click` unchanged, and nothing in the browser
reads it. `citry check` and the editor report each `x-*` attribute on an
HTML element as a `citry.template.alpine-attribute` warning:

```citry-html
{# Warning: nothing reads x-data or x-on:click #}
<div x-data="{ open: false }">
  <button x-on:click="open = !open">Menu</button>
</div>
```

Move the state into the component's `js_data()` or `$component`, and write
the listener as a Vue `@click`. See [Vue in templates](/syntax/vue/).

A leftover `x-cloak` does real harm. Nothing removes the attribute any
more, so an app CSS rule such as `[x-cloak] { display: none }` hides the
element for good. Citry reports it as a `citry.template.alpine-cloak`
error. Delete both the attribute and the CSS rule; the served HTML already
contains the content.

Only HTML elements and `<c-element>` are checked. On a component tag, an
`x-*` attribute is an ordinary Python keyword argument.

When another library on the page reads `x-*` attributes, turn the warning
off for the whole application:

```python
from citry import Citry, LintSettings

app = Citry(
    lint=LintSettings(rule_alpine_attribute="ignore"),
)
```

Or turn it off for the components that use that library:

```citry
from citry import Component


class DatePicker(Component):
    class Lint:
        rule_alpine_attribute = "ignore"
```

Only Alpine's own directive names are reported, such as `x-data`,
`x-on:click`, or `x-intersect`. Other `x-*` names, such as the browser
attribute `x-webkit-airplay`, are ordinary HTML and pass.

A template that several components use is reported unless every one of
them sets `"ignore"`. These two rules do not depend on a component's data,
so `citry check --static` and an editor without a loaded app still run
them. They cannot read your settings there, so they use the default
severities: a leftover `x-cloak` is an error even when your settings
ignore it. Run `citry --app <module>:<app> check` in CI so the check
reads your `LintSettings` and each component's `Lint` class.

Two related template mistakes are not lint rules, so no setting turns
them off: an Alpine-only event modifier such as `@click.outside`, and
`v-once` or `v-memo`. Both fail when the template loads, on every page,
with a message that shows what to write instead. See
[Vue in templates](/syntax/vue/).

## Find invalid HTML attribute values

Some HTML attributes accept only a few keywords. `draggable` takes `"true"`
or `"false"`, and `<input type>` takes a type the browser knows. The
browser ignores any other value or falls back to a default, so the page
renders without an error and the attribute silently does nothing.
`citry check` and the editor report such a value as a
`citry.template.invalid-attribute-value` warning and suggest the closest
valid keyword:

```citry-html
{# Warning: 'treu' is not a valid value; did you mean 'true'? #}
<div draggable="treu">Drag me</div>

{# Warning: did you mean 'datetime-local'? #}
<input type="datetime" name="start">
```

The keywords come from the HTML Standard. The check covers:

- attributes every element accepts, such as `dir`, `hidden`,
  `contenteditable`, `draggable`, `spellcheck`, `translate`, `inputmode`,
  `enterkeyhint`, `autocapitalize`, and `popover`;
- `type` on `<input>`, `<button>`, `<ol>`, `<li>`, and `<ul>`;
- `method`, `enctype`, and `autocomplete` on `<form>`;
- `loading`, `decoding`, `fetchpriority`, `crossorigin`, and
  `referrerpolicy` on the elements that take them, such as `<img>`;
- `preload` on `<audio>` and `<video>`, `kind` on `<track>`, `wrap` on
  `<textarea>`, and `scope` on `<th>`.

Letter case does not matter, so `type="Email"` passes. The exception is
the list markers of `type` on `<ol>` and `<li>`, where `"a"` and `"A"` are
different. An attribute that accepts an empty value, such as `hidden`,
`crossorigin`, or `contenteditable`, may also be written with no value at
all.

`target` and `formtarget` take any window name, so only a name that starts
with an underscore is checked. `target="_new"` is reported, because the
only valid names with an underscore are `_blank`, `_self`, `_parent`, and
`_top`. The `name` of an `<iframe>` or `<object>` may not start with an
underscore at all.

Only values written directly in the template are checked. A bound value
such as `c-dir` or `:draggable`, a component tag, `<c-element>`, a custom
element such as `<my-widget>`, and elements inside `<svg>` or `<math>` are
not. Attributes that take a list of words, such as `rel`, `sandbox`, or
`autocomplete` on `<input>`, are not checked either.

When a script on the page reads its own values from one of these
attributes, turn the warning off for the components that use it:

```citry
from citry import Component


class LegacyWidget(Component):
    class Lint:
        rule_invalid_attribute_value = "ignore"
```

Like the Alpine rules, this rule needs no component data, so
`citry check --static` and an editor without a loaded app run it with the
default severity. Without a loaded app they also cannot tell which values
an extension's template syntax produces, so such a value may be reported
there but not by `citry --app <module>:<app> check`.

## Understand open schemas

Citry tracks known fields separately from whether they exhaust the normalized
runtime mapping:

| Namespace | Configured `error` | Configured `warning` | Configured `ignore` |
| --- | --- | --- | --- |
| Closed schema | error | warning | no finding |
| Pydantic `extra="allow"` | warning | warning | no finding |
| Unknown or absent schema | error | warning | no finding |

A Pydantic schema that explicitly allows extras can accept an undeclared name
at runtime, so Citry does not call it a definite error. It remains a warning
because relying on arbitrary undeclared keys makes a template contract harder
to understand. Unknown and absent schemas stay strict by default. Declare a
real variable or choose a component override when dynamic data is intentional.

Plain schema classes, dataclasses, NamedTuples, and Pydantic models that ignore
or forbid extras are closed.

## Run the batch check

Unknown-variable linting requires a complete component registry:

```console
citry --app myproject.app:app check
```

Warnings are printed and included in JSON output but do not make the command
fail. Any error exits with status 1. `citry check --static` cannot prove which
component owns a template or browser asset, so it intentionally performs
syntax checks without these namespace rules. It still reports leftover
Alpine attributes, with the default severities.

Extensions that add template data can publish detached namespace metadata with
[`TemplateNamespaceContribution`][citry.TemplateNamespaceContribution]. An
extension can enumerate variables or report that it preserves unenumerated
extras, but it cannot weaken the application's selected rule severity.
