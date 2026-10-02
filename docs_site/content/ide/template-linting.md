---
title: Template linting
description: Find names that come from nowhere, Python variables read by Vue, leftover Alpine attributes, and invalid HTML attribute values, and choose how strict each check is.
---

# Template linting

A template can render without an error and still be wrong. A misspelled
variable renders as nothing, a Vue binding reads a Python loop variable the
browser never sees, an attribute value the browser does not accept is
silently ignored. Citry's lint rules find these mistakes in the editor and in
`citry check`, before anyone opens the page.

Your application owns the rules. You set them once on your
[`Citry`][citry.Citry] instance, and both `citry check` and the editor read
them. There is no separate editor setting.

| Rule | What it catches | Default |
| --- | --- | --- |
| [`citry.template.unknown-variable`](/ide/diagnostics/#citry.template.unknown-variable) | A template variable that comes from nowhere | error |
| [`citry.vue.unknown-variable`](/ide/diagnostics/#citry.vue.unknown-variable) | A name in a Vue expression that the component does not send to the browser | error |
| [`citry.component-js.unknown-variable`](/ide/diagnostics/#citry.component-js.unknown-variable) | An undeclared name in `$component` code | error |
| [`citry.component-js.unknown-member`](/ide/diagnostics/#citry.component-js.unknown-member) | A misspelled `this.<name>` or `component.<name>` | error |
| [`citry.vue.python-variable`](/ide/diagnostics/#citry.vue.python-variable) | A Vue expression that reads a Python loop variable | warning |
| [`citry.template.alpine-attribute`](/ide/diagnostics/#citry.template.alpine-attribute) | A leftover Alpine `x-*` attribute | warning |
| [`citry.template.alpine-cloak`](/ide/diagnostics/#citry.template.alpine-cloak) | A leftover `x-cloak`, which hides the element for good | error |
| [`citry.template.invalid-attribute-value`](/ide/diagnostics/#citry.template.invalid-attribute-value) | An HTML attribute value the browser does not accept | warning |

## Fix a name that comes from nowhere

A template variable must come from the component's template data, a `c-for`
or `c-fill` binding around it, or a global you configured. Anything else is an
error:

```citry-html
{# error: Template variable 'usr' is not available in this template. #}
<p>{{ usr.name }}</p>
```

Vue expressions follow the same idea. A name in `:title`, `v-text`, or
`@click` must be something the component sends to the browser, such as a
`js_data()` key, or a Vue or Citry helper:

```citry-html
{# error: Vue variable 'submitting1' is not available in this component. #}
<button :disabled="submitting1">Save</button>
```

Inside `$component(...)`, every name must be declared in that code,
destructured from the callback's argument, or be a browser global:

```javascript
$component({
  onServerRender({ component }) {
    // error: Component JavaScript variable 'settings' is not defined.
    component.ready = settings.ready;
  },
});
```

Usually the fix is to correct the spelling, or to read the value from the
component, such as `component.ready`. If another script on the page really
provides the name, [declare it](#declare-names-that-come-from-outside-the-component).

A misspelled member of the component is an error too. Citry reports a
`component.<name>` or `this.<name>` read that names no `js_data()` key,
prop, `data()` key, `setup` binding, method, computed value, or injection:

```javascript
// js_data() returns {"likes": ...}
$component(({ component }) => {
  // error: Component instance member 'like' is not defined
  // by this component.
  console.log(component.like);
});
```

A Vue plugin that adds a property to every component should name it with a
`$` prefix, such as `$api`. Citry does not check `$` names, but it reports an
unprefixed plugin property, such as `this.axios`.

## Fix a Vue binding that reads a Python loop variable

Python runs a `c-for` loop on the server. Vue evaluates `:title` later, in the
browser, where `item` does not exist:

```citry-html
<!-- Wrong: Vue looks up `item` in browser state. -->
<li c-for="item in items" :title="item"></li>

<!-- Right: Python sets the attribute for each item. -->
<li c-for="item in items" c-title="item"></li>
```

Citry reports this once per read. When it knows every name the component
sends to the browser, it reports a `citry.vue.unknown-variable` error whose
message says the name is a Python variable. Otherwise, it reports a
`citry.vue.python-variable` warning that suggests the `c-` attribute.

The warning also fires when the component's browser data has a name equal to
the loop variable. Vue then shows the browser value instead of the loop
value, with no error, so the message suggests the `c-` attribute or renaming
one of them.

The same applies to `c-fill` bindings and to every Vue expression, including
`v-text`, `v-show`, and `@click`. A Vue `v-for` or slot alias with the same
name around the expression is fine, because Vue then reads its own value.

## Declare names that come from outside the component

Some names reach a template or browser code from somewhere Citry cannot see,
such as a framework integration or a script on the host page. Declare them on
the application so Citry stops reporting them.

Keys in `template_globals` are known automatically, with types guessed from
their values. For other names, pass a [`LintSettings`][citry.LintSettings]:

```python
from collections.abc import Callable
from typing import Annotated

from citry import Citry, LintSettings

app = Citry(
    template_globals={"site_name": "Citry"},
    lint=LintSettings(
        template_variables={
            "request": Annotated[
                "django.http.HttpRequest",
                "The current framework request.",
            ],
            "url_for": Callable[[str], str],
        },
        vue_variables={
            "$analytics": Annotated[
                "myapp.browser.Analytics",
                "Analytics added as a custom Vue property.",
            ],
        },
        component_js_globals={
            "featureFlags": Annotated[
                "myapp.browser.FeatureFlags",
                "Flags set by the host page.",
            ],
        },
    ),
)
```

- `template_variables` are names that reach the template from another
  integration, such as a request object.
- `vue_variables` are custom Vue properties, or values that a Vue scope
  outside Citry provides.
- `component_js_globals` are real globals that a project script defines,
  available inside `$component`.

These declarations only tell the checker about the names. They do not provide
a value at runtime. Each value is a type annotation, which the editor shows on
hover. `Annotated[T, "description"]` adds a description too. The editor
resolves type names written as strings, such as `"django.http.HttpRequest"`,
in your project's environment.

Do not declare a value that `onServerRender` receives, such as props, refs,
or event helpers. Read it from the callback's argument or the `component`
instance instead. Declaring it as a global would hide the bug where you forgot
to destructure it.

## Change how strict a rule is

Each rule has a `rule_*` setting on `LintSettings` that accepts `"ignore"`,
`"warning"`, or `"error"`. Warnings are shown but do not fail `citry check`;
errors do. These are the defaults:

```python
from citry import Citry, LintSettings

app = Citry(
    lint=LintSettings(
        rule_unknown_template_variable="error",
        rule_unknown_vue_variable="error",
        rule_unknown_component_js_variable="error",
        rule_unknown_component_js_member="error",
        rule_vue_python_variable="warning",
        rule_alpine_attribute="warning",
        rule_alpine_cloak="error",
        rule_invalid_attribute_value="warning",
    ),
)
```

`LintSettings` also has `rule_i18n_missing_param_type`, described in
[Translation workflow](/i18n/workflow/#make-a-missing-type-an-error-or-ignore-it).

## Override one component

When one component works differently, give it a nested `Lint` class with the
settings to change:

```citry
from typing import Annotated

from citry import Component


class AccountCard(Component):
    class Lint:
        rule_unknown_template_variable = "warning"
        rule_unknown_component_js_member = "warning"
        template_variables = {
            "account_context": Annotated[
                "myapp.accounts.AccountContext",
                "Added by the account page integration.",
            ],
        }
        component_js_globals = {
            "accountClient": Annotated[
                "myapp.browser.AccountClient",
                "Client set up by the account page.",
            ],
        }
```

Subclasses inherit `Lint`. The nearest setting wins, and declared names merge
by name. Set `Lint = None` on a subclass to drop the inherited overrides and
use the application's settings again.

## Find leftover Alpine attributes

Citry uses Vue, so an Alpine attribute left over from older templates does
nothing. Citry renders `x-data` or `x-on:click` unchanged, and nothing in the
browser reads it. Each `x-*` attribute on an HTML element is a
`citry.template.alpine-attribute` warning:

```citry-html
{# Warning: nothing reads x-data or x-on:click #}
<div x-data="{ open: false }">
  <button x-on:click="open = !open">Menu</button>
</div>
```

Move the state into the component's `js_data()` or `$component`, and write
the listener as a Vue `@click`. See [Vue in templates](/syntax/vue/).

A leftover `x-cloak` does real harm. Nothing removes the attribute, so a CSS
rule such as `[x-cloak] { display: none }` hides the element for good. Citry
reports it as a `citry.template.alpine-cloak` error. Delete both the
attribute and the CSS rule; the HTML from the server already shows the
content.

Only Alpine's own directive names are reported, such as `x-data`,
`x-on:click`, or `x-intersect`, and only on HTML elements and
`<c-element>`. Other `x-*` names, such as `x-webkit-airplay`, are ordinary
HTML. On a component tag, an `x-*` attribute is a Python keyword argument.

When another library on the page reads `x-*` attributes, turn the warning off
for the components that use it:

```citry
from citry import Component


class DatePicker(Component):
    class Lint:
        rule_alpine_attribute = "ignore"
```

Or for the whole application, with
`LintSettings(rule_alpine_attribute="ignore")`.

## Find invalid HTML attribute values

Some HTML attributes accept only a few keywords. `draggable` takes `"true"` or
`"false"`, and `<input type>` takes a type the browser knows. The browser
ignores any other value or falls back to a default, so the attribute silently
does nothing. Citry reports such a value as a
`citry.template.invalid-attribute-value` warning and suggests the closest
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
  `<textarea>`, and `scope` on `<th>`;
- `target` and `formtarget`, `http-equiv` on `<meta>`, and `name` on
  `<iframe>` and `<object>`, as described
  [below](#window-names-and-meta-pragmas).

Letter case does not matter, so `type="Email"` passes. An attribute that
accepts an empty value, such as `hidden`, may also be written with no value.

A Vue binding whose value is one JavaScript string is checked too, because it
sets the same text:

```citry-html
{# Warning: 'rlt' is not a valid value; did you mean 'rtl'? #}
<div :dir="'rlt'">...</div>
```

When a script on the page reads its own values from one of these attributes,
turn the warning off for the components that use it:

```citry
from citry import Component


class LegacyWidget(Component):
    class Lint:
        rule_invalid_attribute_value = "ignore"
```

## Check the rules in CI

Run the check against your application, so it knows every component and
reads your `LintSettings` and each component's `Lint` class:

```console
citry --app myproject.app:app check
```

Warnings are printed, and included in `--format json` output, but do not fail
the command. Any error exits with status 1. See
[Command line](/cli/#check-component-templates).

## Less common cases

### Checks without your application loaded

`citry check --static`, and an editor that has not loaded your application,
cannot tell which component owns a template. They skip the unknown-name
rules.

They still run the Alpine and attribute-value rules, which need no component
data, but they cannot read your settings, so they use the default
severities. A leftover `x-cloak` is then an error even if your settings
ignore it. They also cannot tell which values an extension's template syntax
produces, so they may report a value that `citry --app ... check` does not.

### Templates and scripts shared by several components

When several components use the same template or JavaScript file, Citry
applies the strictest severity among them. To silence a rule for that file,
every one of those components must set it to `"ignore"`.

### Template data that allows extra keys

How strict the unknown template variable rule can be depends on the
component's template data schema:

| Template data schema | Set to `error` | Set to `warning` | Set to `ignore` |
| --- | --- | --- | --- |
| Closed | error | warning | nothing |
| Pydantic with `extra="allow"` | warning | warning | nothing |
| Unknown or none | error | warning | nothing |

A Pydantic schema that allows extra keys may receive any name at runtime, so
Citry reports an undeclared name as a warning, not an error. Plain classes,
dataclasses, NamedTuples, and Pydantic models that ignore or forbid extra
keys are closed.

### Vue Options with `mixins` or `extends`

The unknown member check needs every name the component defines. When the
Vue Options merge in `mixins` or `extends`, those names are not in the
source, so Citry skips the check. A Python loop variable read by Vue is then
reported as the `citry.vue.python-variable` warning.

### Bound values and elements the attribute-value check skips

The attribute-value check does not look at a bound value that is not one
string, such as `:dir="direction"` or `c-dir`, or at a binding with a
modifier such as `.prop`. It also skips component tags, `<c-element>`,
custom elements such as `<my-widget>`, elements inside `<svg>` or `<math>`,
and attributes that take a list of words, such as `rel` or `sandbox`.

For `type` on `<ol>` and `<li>`, letter case matters: `"a"` and `"A"` are
different list markers.

When the editor or `citry check --types` also runs TypeScript, a bound value
that Vue's types reject is reported once, by this rule, at this rule's
severity. Set the rule to `"error"` if such a value should fail a check.

### Window names and meta pragmas

`target` and `formtarget` accept any window name, so Citry checks only names
that start with an underscore. The valid ones are `_blank`, `_self`,
`_parent`, and `_top`, so `target="_new"` is reported. The `name` of an
`<iframe>` or `<object>` may not start with an underscore at all.

`http-equiv` on `<meta>` is checked against the values browsers act on:
`content-type`, `default-style`, `refresh`, `x-ua-compatible`, and
`content-security-policy`. Browsers ignore a header name such as
`Cache-Control` there, so the warning says to send it as an HTTP header:

```citry-html
{# Warning: browsers ignore this; send Cache-Control as a header. #}
<meta http-equiv="Cache-Control" content="no-cache">
```

### Alpine syntax that fails when the template loads

An Alpine-only event modifier such as `@click.outside`, and `v-once` or
`v-memo`, are not lint rules, so no setting turns them off. The template
fails to load, with a message that shows what to write instead. See
[Vue in templates](/syntax/vue/).

### Go to definition for declared names

In the editor, go to definition on a name declared in `template_variables`
opens its key in your `LintSettings`, when the settings are written directly
in the `Citry(...)` call or through a simple variable. A name declared in a
component's `Lint` class opens that class, including an inherited one.
Settings built by a function still work, but have no definition to open.

### Extensions that add template data

An extension that adds template variables can describe them with
[`TemplateNamespaceContribution`][citry.TemplateNamespaceContribution], so
Citry knows them. It can list the names, or say that it adds names it cannot
list. It cannot lower the severity your application chose.
