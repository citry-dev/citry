---
title: Template linting
description: Catch template mistakes before the page renders, such as unknown names, typos in attributes, tags, events, and directives, invalid HTML, Vue errors, and server event arguments the server would reject. Choose how strict each check is.
---

# Template linting

Some template mistakes show up only when the page renders, and some never
raise an error at all:

- A misspelled variable fails only when the page renders.
- A Vue binding can read a Python loop variable the browser never sees.
- The browser silently ignores a misspelled attribute such as `titel`, or
  a value it does not accept.
- A misspelled `c-if` renders the element anyway.
- A broken Vue expression, or a `<div>` inside a `<p>`, stops a component
  that uses Vue from rendering.

Citry's lint rules find these mistakes in the editor and in `citry check`,
before anyone opens the page.

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
| [`citry.template.invalid-attribute-value`](/ide/diagnostics/#citry.template.invalid-attribute-value) | An HTML attribute value the browser does not accept, or any value on a boolean attribute, such as `disabled="false"` | error |
| [`citry.template.misspelled-directive`](/ide/diagnostics/#citry.template.misspelled-directive) | A typo in a directive, such as `c-iff` or `v-iff` | error |
| [`citry.template.misspelled-attribute`](/ide/diagnostics/#citry.template.misspelled-attribute) | A typo in an attribute name, such as `titel` | error |
| [`citry.template.misspelled-element`](/ide/diagnostics/#citry.template.misspelled-element) | A typo in a tag name, such as `<dvi>` | error |
| [`citry.template.unknown-aria-attribute`](/ide/diagnostics/#citry.template.unknown-aria-attribute) | An `aria-*` name that ARIA does not define | error |
| [`citry.vue.misspelled-event`](/ide/diagnostics/#citry.vue.misspelled-event) | A typo in a DOM event name, such as `@clik` | warning |
| [`citry.vue.invalid-expression`](/ide/diagnostics/#citry.vue.invalid-expression) | A Vue expression that is not valid JavaScript | error |
| [`citry.browser.invalid-model-target`](/ide/diagnostics/#citry.browser.invalid-model-target) | `v-model` on an element that holds no value | error |
| [`citry.browser.undeclared-component-event`](/ide/diagnostics/#citry.browser.undeclared-component-event) | A listener for an event the child component does not declare | warning |
| [`citry.template.invalid-nesting`](/ide/diagnostics/#citry.template.invalid-nesting) | A block such as `<div>` inside a `<p>` | error |
| [`citry.template.duplicate-id`](/ide/diagnostics/#citry.template.duplicate-id) | Two elements with the same `id` | error |
| [`citry.template.missing-image-alt`](/ide/diagnostics/#citry.template.missing-image-alt) | An `<img>` without alt text | warning |
| [`citry.browser.missing-component-key`](/ide/diagnostics/#citry.browser.missing-component-key) | A component that `<c-for>` repeats without `#c-key`, on a page that uses Vue | error |
| [`citry.browser.prop-assignment`](/ide/diagnostics/#citry.browser.prop-assignment) | A component that assigns to one of its own props | error |
| [`citry.browser.unknown-server-event-field`](/ide/diagnostics/#citry.browser.unknown-server-event-field) | A key in `@c-*` arguments that the handler does not accept | error |
| [`citry.browser.missing-server-event-field`](/ide/diagnostics/#citry.browser.missing-server-event-field) | `@c-*` arguments without a field the handler requires | error |
| [`citry.browser.incompatible-server-event-field`](/ide/diagnostics/#citry.browser.incompatible-server-event-field) | A literal in `@c-*` arguments of a type the handler rejects | error |
| [`citry.browser.unknown-form-field`](/ide/diagnostics/#citry.browser.unknown-form-field) | A control in a submitted form whose `name` the handler does not accept | error |
| [`citry.browser.missing-form-field`](/ide/diagnostics/#citry.browser.missing-form-field) | A submitted form without a control for a field the handler requires | error |
| [`citry.css.misspelled-variable`](/ide/diagnostics/#citry.css.misspelled-variable) | A `var(--name)` that misspells a `css_data()` key | warning |

## Fix unknown names

A template variable must come from the component's template data, a `c-for`
or `c-fill` binding around it, or a global you configured. Anything else is an
error:

```citry-html
{# error: Template variable 'usr' is not available
   in this template. #}
<p>{{ usr.name }}</p>
```

Vue expressions follow the same idea. A name in `:title`, `v-text`, or
`@click` must be something the component sends to the browser, such as a
`js_data()` key, or a Vue or Citry helper:

```citry-html
{# error: Vue variable 'submitting1' is not available
   in this component. #}
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
provides the name, [declare it](#declare-outside-names).

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

Citry runs this check only when it can see every `js_data()` key and every
Vue Options section in the source. It skips names that start with `$` or
`_`, so a Vue plugin that adds a property to every component should name it
with a `$` prefix, such as `$api`. An unprefixed plugin property, such as
`this.axios`, is reported.

## Python loops in Vue

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
message says the name is a Python variable. Otherwise, or when you set
`rule_unknown_vue_variable` to `"ignore"`, it reports a
`citry.vue.python-variable` warning that suggests the `c-` attribute.

The warning also fires when the component's browser data has a name equal to
the loop variable. Vue then shows the browser value instead of the loop
value, with no error, so the message suggests the `c-` attribute or renaming
one of them.

The same applies to `c-fill` bindings and to every Vue expression, including
`v-text`, `v-show`, and `@click`. A Vue `v-for` or slot alias with the same
name around the expression is fine, because Vue then reads its own value.

## Declare outside names

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

## Change rule severity { #change-how-strict-a-rule-is }

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
        rule_invalid_attribute_value="error",
        rule_misspelled_directive="error",
        rule_misspelled_attribute="error",
        rule_misspelled_element="error",
        rule_unknown_aria_attribute="error",
        rule_misspelled_event="warning",
        rule_invalid_vue_expression="error",
        rule_invalid_model_target="error",
        rule_undeclared_component_event="warning",
        rule_invalid_nesting="error",
        rule_duplicate_id="error",
        rule_missing_image_alt="warning",
        rule_missing_component_key="error",
        rule_prop_assignment="error",
        rule_unknown_server_event_field="error",
        rule_missing_server_event_field="error",
        rule_incompatible_server_event_field="error",
        rule_misspelled_css_variable="warning",
    ),
)
```

`LintSettings` also has two translation rules:
`rule_i18n_missing_param_type`
([Change type warnings](/i18n/workflow/#make-a-missing-type-an-error-or-ignore-it))
and `rule_i18n_cross_language_fallback`
([Change fallback warnings](/i18n/workflow/#change-fallback-warnings)).

`LintSettings` and a component's nested `Lint` class also accept
`check_input_types`, which is not a lint rule. It controls the check that
raises `TypeError` when a component renders with an input of the wrong
type, and `citry check` and the editor ignore it
([Turn the check off](/concepts/inputs-and-validation/#turn-the-check-off)).

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

## Alpine leftovers { #find-leftover-alpine-attributes }

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

## Invalid attribute values { #find-invalid-html-attribute-values }

Some HTML attributes accept only a few keywords. `draggable` takes `"true"` or
`"false"`, and `<input type>` takes a type the browser knows. The browser
ignores any other value or falls back to a default, so the attribute silently
does nothing. Citry reports such a value as a
`citry.template.invalid-attribute-value` error and suggests the closest
valid keyword:

```citry-html
{# Error: 'treu' is not a valid value; did you mean 'true'? #}
<div draggable="treu">Drag me</div>

{# Error: did you mean 'datetime-local'? #}
<input type="datetime" name="start">
```

A boolean attribute, such as `disabled`, `required`, or `checked`, is on
whenever it is present, whatever its value. So `disabled="false"` still
disables the button. Citry reports any value other than an empty one or
the attribute's own name:

```citry-html
{# Wrong: the button is disabled, because 'false' still
   turns the attribute on #}
<button disabled="false">Search</button>

{# Right: leave the attribute out to turn it off #}
<button>Search</button>

{# Right: let Vue add or remove it #}
<button :disabled="searching">Search</button>
```

`disabled="true"` is reported too, because the value does nothing: write
`disabled` on its own. A bound JavaScript boolean, such as
`:disabled="false"`, is fine, but the string `:disabled="'false'"` is
reported, and the message suggests binding the boolean instead.
`draggable`, `spellcheck`, and `contenteditable` take `"true"` and
`"false"` as keywords, so they are not boolean attributes.

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
  [below](#window-names-meta-tags).
- boolean attributes, such as `disabled`, `required`, and `checked`, on
  the elements that take them.

Letter case does not matter, so `type="Email"` passes. An attribute that
accepts an empty value, such as `hidden`, may also be written with no value.

A Vue binding whose value is one JavaScript string is checked too, because it
sets the same text:

```citry-html
{# Error: 'rlt' is not a valid value; did you mean 'rtl'? #}
<div :dir="'rlt'">...</div>
```

When a script on the page reads its own values from one of these attributes,
turn the rule off for the components that use it:

```citry
from citry import Component


class LegacyWidget(Component):
    class Lint:
        rule_invalid_attribute_value = "ignore"
```

## Misspelled directives { #find-misspelled-directives }

Citry reads only its own directive names, such as `c-if` and `c-for`. Any
other `c-` name on an HTML element sets an ordinary attribute from the
Python value, so a typo does not fail. The element below always shows up,
whatever `show` is:

```citry-html
{# Error: 'c-iff' is not a Citry directive, so it renders an
   HTML attribute named 'iff'. Did you mean 'c-if'? #}
<div c-iff="show">Details</div>

{# Right: the element renders only when show is true #}
<div c-if="show">Details</div>
```

Citry reports a `c-` name as a `citry.template.misspelled-directive` error
when the part after `c-` is not an attribute of that element and it looks
like a directive:

- `if`, `elif`, `else`, `for`, `empty`, or `bind` with two neighboring
  letters swapped, one letter typed twice, or one letter left out, such
  as `c-fro`, `c-iff`, or `c-ele`;
- a directive in other letter case, such as `c-If`;
- a spelled-out `c-elif`, such as `c-else-if` or `c-elseif`;
- `c-show`, which you write as `c-if`, or a Vue directive written with
  `c-`, such as `c-model`, which you write as `v-model`;
- `c-key` or `c-ignore`, which you write as `#c-key` or `#c-ignore`.

A different letter, or an extra letter that is not a double, does not
count as a typo, because it usually makes an ordinary word: `c-kind` is
not read as `c-bind`, and `c-form` or `c-fork` not as `c-for`. A name one
letter short of a directive is not reported when it is itself a word or a
single letter, such as `c-or`, `c-bid`, `c-bin`, or `c-f`.

An attribute the element really has is never reported, in any letter case:
`c-id`, `c-ID`, `c-form` on `<input>`, and every `c-data-*` and `c-aria-*`
name pass. `<c-element>` accepts the attributes of every element. A custom
element such as `<my-button>` can define its own attributes, so there
`c-show`, `c-model`, `c-key`, and `c-ignore` pass; typos such as `c-iff`
or `c-If` are still reported. Component tags and elements inside `<svg>`
or `<math>` are skipped; on a component tag, a `c-` name is a Python
keyword argument.

An attribute named like a directive, such as `for` on `<label>`, cannot
take `c-`, because `c-for` is always the loop. Pass it through `c-bind`.

When the attribute really is meant for the browser, such as a `show`
attribute that a page script reads (`c-show` on a `<div>` is reported, with
`c-if` as the suggestion), pass it through `c-bind`, which this rule does not read:

```citry-html
<div c-bind="{'show': expanded}">...</div>
```

### Vue directives { #misspelled-vue-directives }

A typo such as `v-iff` renders on the server, then stops the page in the
browser with an error that names the missing directive. Vue reads any
`v-*` name it does not know as a custom directive, and none is registered
under that name:

```citry-html
{# Error: 'v-iff' is not a Vue directive, so Vue looks for
   a custom directive of that name and the page fails in
   the browser. Did you mean 'v-if'? #}
<p v-iff="open">Details</p>

{# Right #}
<p v-if="open">Details</p>
```

Citry reports a `v-*` name that is one typing slip from a Vue directive:
two neighboring letters swapped, one letter typed twice, or one letter
left out, such as `v-iff`, `v-shwo`, `v-IFF`, or `v-modle`. It also
reports a spelled-out `v-else-if`, such as `v-elif` or `v-elseif`. It
checks every tag, component tags included, except elements inside
`<svg>` or `<math>`, or inside an element with `v-pre`, which Vue does
not compile.

A name that is itself a word, such as `v-tex`, `v-mode`, or `v-one`, is
not reported. Neither is a typo of `v-once` or `v-memo`, because Citry
does not support those two directives.

If you register your own directive whose name is one typing slip from a
Vue directive, set `rule_misspelled_directive = "ignore"` in the `Lint` class
of the components that use it. This also turns off the `c-` directive
checks for those components.

## Misspelled HTML names { #find-misspelled-html-names }

The browser raises no error for an attribute, tag, or event name it does
not know. A typo such as `titel` for `title` leaves the
element without its tooltip, and `@clik` for `@click` leaves the button
without a working listener.

Most of these rules report a name that is one typing slip from a real
one: two neighboring letters swapped, one letter typed twice, or one
letter left out. The ARIA rule reports every unknown name.

### Attribute names { #misspelled-attribute-names }

```citry-html
{# Error: 'titel' is not an attribute of <div>, so the
   browser ignores it. Did you mean 'title'? #}
<div titel="Board">...</div>

{# Right #}
<div title="Board">...</div>
```

A binding is checked by the attribute it sets, so `:titel`,
`v-bind:titel`, and `c-titel` are reported too. Letter case does not
matter. A `c-` name that looks like a directive, such as `c-fro`, is
reported as a [misspelled directive](#find-misspelled-directives)
instead.

These are not checked:

- names with a hyphen or a colon, such as `data-*` or `hx-*`;
- a binding with a modifier, such as `:titel.prop`;
- component tags, `<c-element>`, custom elements such as `<my-widget>`,
  and elements inside `<svg>` or `<math>`;
- `<slot>`, where a binding is a slot prop.

When a page script really reads an attribute with a reported name, rename it
to `data-<name>`, or set `rule_misspelled_attribute = "ignore"` for that
component.

### Element names { #misspelled-element-names }

The browser renders an unknown tag as an element with no styles or
behavior, with no error.

```citry-html
{# Error: <dvi> is not an HTML element. Did you mean <div>? #}
<dvi class="board">...</dvi>

{# Right #}
<div class="board">...</div>
```

Only a lowercase tag with no hyphen and no `c-` prefix is checked, and
only when it is one typing slip from an HTML element. Any other unknown
tag, such as `<widget>`, is not reported, because a Vue plugin may
register a component under that name. If a plugin registers a name that
is one typing slip from an HTML element, set
`rule_misspelled_element = "ignore"` for the components that use it.

### ARIA attributes { #unknown-aria-attributes }

Browsers and screen readers ignore an `aria-*` name that WAI-ARIA does not
define, so the element loses the state or label you meant to give it:

```citry-html
{# Error: ':aria-expandd' is not an ARIA attribute.
   Did you mean 'aria-expanded'? #}
<button :aria-expandd="open">Menu</button>

{# Right #}
<button :aria-expanded="open">Menu</button>
```

Every unknown `aria-*` name is reported, not only typos, because ARIA
does not let a page invent its own names. The message suggests the
closest ARIA attribute when one is close. Bindings such as `:aria-*` and
`c-aria-*` are checked too. Component tags are skipped, because there the
name is an input. To keep a custom value on an element, store it in a
`data-*` attribute.

### Event names { #misspelled-event-names }

```citry-html
{# Warning: 'clik' is not a DOM event, so this listener
   never runs. Did you mean 'click'? #}
<button @clik="toggle()">Menu</button>

{# Right #}
<button @click="toggle()">Menu</button>
```

This rule is a warning by default, because a page can dispatch events
with any name. It checks listeners on HTML elements whose event name is
all lowercase letters. A name with a hyphen, a colon, or a capital
letter, such as `@item-added`, is a custom event and is not reported.
Neither are `scrolled` and `touched`, which are ordinary words. Component
tags and custom elements are skipped. For a listener on a component tag,
see [Component event names](#find-misspelled-component-events).

If the page really dispatches a custom event with such a name, set
`rule_misspelled_event = "ignore"` for that component.

## Vue compile errors { #find-vue-compile-errors }

Citry compiles a component's Vue code on the server when the component
renders. A broken expression or a misplaced `v-model` stops that
compiler, so the component fails to render with a `ValueError` that may
not point at the line in your template. The lint rules report these
mistakes at their place in the template, before anything renders.

The Vue rules (invalid expressions, `v-model` targets, Vue directive
typos, and DOM event names) skip everything inside an element with
`v-pre`, because Vue does not compile it.

### Invalid expressions { #invalid-vue-expressions }

```citry-html
{# Error: The Vue expression in 'v-if' is not valid
   JavaScript, so Vue cannot compile this template. #}
<p v-if="open &&">Details</p>

{# Right #}
<p v-if="open && ready">Details</p>
```

Citry checks every Vue expression, such as the value of `v-if`, `:title`,
`v-for`, or `@click`, and the arguments of a server call such as
`@c-click="rate({ stars: 5 })"`. It decodes character references first, as Vue
does, so `a &amp;&amp; b` passes. A listener may hold statements, such as
`@click="count++; save()"`, or a function.

It does not check:

- a `:title` with no value, which Vue reads as `:title="title"`;
- anything inside an element with `v-pre`;
- a dynamic slot name, such as `#[name]`;
- the value of a custom directive. A value there that is not valid
  JavaScript still stops the render; the lint does not report it.

### `v-model` targets { #invalid-v-model-targets }

`v-model` binds the value of an `<input>`, `<textarea>`, or `<select>`.
On any other HTML element, the template fails to compile:

```citry-html
{# Error: v-model does not work on <form>, which holds no
   value. #}
<form v-model="query">
  <input type="search" name="q">
</form>

{# Right: bind the input that holds the value #}
<form>
  <input v-model="query" type="search" name="q">
</form>
```

A custom element such as `<my-picker>` is reported too. Bind its value
property and listen for its change event instead. Component tags,
PascalCase Vue components, and `<c-element>` are not reported, because
they decide for themselves what `v-model` binds.

## Component event names { #find-misspelled-component-events }

A listener on a child component for an event the child never emits
silently does nothing. Vue passes the listener to the child's root
element, where it runs only if that element fires a DOM event with that
name:

```citry-html
{# Warning: Component 'c-card' does not declare event
   'hdie' in its emits option. Did you mean 'hide'? #}
<c-Card @hdie="hideCard"></c-Card>

{# Right #}
<c-Card @hide="hideCard"></c-Card>
```

Citry compares each listener on a component tag with the events the
child declares in `emits`, or through an `on<Event>` prop, and suggests a
declared event that is one typing slip away. A DOM event name, such as
`@click`, is not reported, because the child's root element may fire it.
Citry checks only when the child's `emits` is an array of strings or an
object whose keys are written as plain names, not computed.

This rule reads each child's `emits`, so it needs your application:
`citry --app ... check` reports it, and the editor reports it once it has
loaded your application. It is a warning by default. To make an
undeclared listener fail `citry check`, set
`rule_undeclared_component_event = "error"`. See
[Emitted event names](/ide/vscode/#emitted-event-names) for the checks on
the child's side.

## Blocks inside `<p>` { #find-invalid-nesting }

A `<p>` cannot hold a block element such as `<div>`, `<ul>`, or `<h2>`.
The browser closes the paragraph just before the block, so the page has a
different structure from your template, and your CSS may no longer
match. In a component that uses Vue, the template fails to compile, so the
component fails to render.

```citry-html
{# Error: <div> cannot be inside <p>. The browser closes
   the <p> before it. #}
<p>Owner: <div>{{ owner.name }}</div></p>

{# Right: use an inline element, or make the outer one a div #}
<p>Owner: <span>{{ owner.name }}</span></p>
```

Citry reports the elements that the HTML Standard says close an open
`<p>`, including `<div>`, `<ul>`, `<ol>`, `<table>`, `<h1>` to `<h6>`,
`<section>`, another `<p>`, and obsolete blocks such as `<center>` and
`<xmp>`. It finds them through inline elements such as `<span>`, custom
elements, `c-if` and `c-for` blocks, and a `<c-slot>` fallback.

It does not look inside `<button>`, `<table>`, `<template>`, `<svg>`,
`<math>`, a component tag, or `<c-element>`, or inside `<noscript>`,
whose content the browser reads as text when scripts run.

## Duplicate ids { #find-duplicate-ids }

An `id` must be unique in the page. When two elements share one, a
label's `for`, `aria-labelledby`, a `#fragment` link, and
`getElementById` find only the first:

```citry-html
{# Error: Another element in this template already has
   id 'board'. #}
<div id="board">
  <h1 id="board">Board</h1>
</div>

{# Right #}
<div id="board">
  <h1 id="board-title">Board</h1>
</div>
```

Citry reports a literal `id` only when both elements always render. It
skips an element that may render zero or several times: one that has, or
sits inside, any of these:

- `c-if`, `c-elif`, `c-else`, `c-for`, or `c-empty`, as a tag or an
  attribute;
- `v-if`, `v-else-if`, `v-else`, or `v-for`;
- a `c-fill`, a `<c-slot>` fallback, or a component tag's body;
- a `<template>`.

So `c-if` and `c-else` branches may share an id. `v-show` does not count,
because a hidden element is still in the page.

The same id in two different templates is not reported, even when both
render on one page.

## Images without alt text { #find-images-without-alt-text }

A screen reader reads out the file name of an `<img>` that has no alt
text, or nothing useful at all, and a broken image shows no text in its
place:

```citry-html
<div class="profile">
  {# Warning: <img> has no alt text. #}
  <img src="/static/avatar.svg">
</div>

<div class="profile">
  {# Right: describe the image #}
  <img src="/static/avatar.svg" alt="Ada's avatar">
  {# Right: a decoration that screen readers skip #}
  <img src="/static/divider.svg" alt="">
</div>
```

An image passes when it has `alt` in any form (`alt`, `c-alt`, `:alt`, or
`v-bind:alt`), an `aria-label` or `aria-labelledby`, or
`role="presentation"` or `role="none"`. An image with a `c-bind` or
`v-bind` spread is skipped, because the spread may add `alt`.

The rule is a warning by default. To make it fail `citry check`, set
`rule_missing_image_alt = "error"`.

An `<img>` that is the template's only top-level element may get its
`alt` from the parent: Vue passes the attributes written on a component's
tag to that element when the component has browser code. An `<img>`
directly inside a single top-level `c-if`, `c-elif`, and `c-else` chain
counts as that element too. Citry reports such an image only with your
application loaded, and only for a component with no browser code (no
`js`, `js_data()`, `State`, or event handlers).

## Loops without `#c-key` { #find-repeated-components-without-keys }

On a page that uses Vue, each component that `<c-for>` repeats needs a
[`#c-key`](/syntax/attributes/#c-key). Without one, the page fails to
render as soon as the loop has two items:

```citry-html
{# Error: <c-Card> repeats inside <c-for> but has no
   #c-key. This page uses Vue, and the render fails
   when the loop has two items. #}
<c-for each="project in projects">
  <c-Card c-title="project.title" />
</c-for>

{# Right #}
<c-for each="project in projects">
  <c-Card
    #c-key="project.slug"
    c-title="project.title"
  />
</c-for>
```

A page uses Vue when any component on it has component JavaScript,
`js_data()` that returns data, an `Events` class, or a Vue attribute such
as `v-if`, `@click`, or `:title` in its template. Citry reports a repeated
component when the component whose template has the loop, or the
repeated component, is one of those. It cannot see the rest of the page,
so a loop on a page that uses Vue only because of another component is
not reported.

A component inside a keyed component, such as `<c-Card>` in the body of
`<c-List #c-key="...">`, needs no key of its own. A component with
`transparent = True` or `simple = True` is not reported, because it
renders into its caller's HTML. A `<c-component>` that picks its
component at render time needs a key too, but Citry does not check it.
This rule needs your application, so only `citry --app ... check`
reports it.

## Assignments to props { #find-prop-assignments }

A component cannot change a prop it receives. Vue keeps the old value and
only logs a warning in the browser console, so the button below does
nothing:

```citry-html
{# Error: Prop 'open' is read-only, so this assignment
   does not change it. #}
<button @click="open = false">Close</button>

{# Right: ask the parent to change it #}
<button @click="$emit('close')">Close</button>
```

Citry reads the props from the component's `$component({ props })` and
reports an assignment to one of them in the component's own template:
`=`, `+=` and the other assignment operators, `++`, `--`, and
`v-model="open"`. It reports `this.open = false` in the component's
JavaScript too, but only as a warning, because it finds that assignment by
reading the text. Changing a field of an object prop, such as
`open.count = 1`, is allowed and not reported.

`citry --app ... check` reports this rule, and the editor reports it once
it has loaded your application.

## Server event arguments { #check-server-event-arguments }

The server checks the arguments of an `@c-*` call against the handler's
`data` class before the handler runs, and rejects the whole call on any
mistake. Citry compares the arguments you write in the template with that
class:

```citry
class SaveIn:
    amount: int


class Counter(Component):
    class Events:
        def save(self, data: SaveIn):
            ...

    template = """
      {# Error: Server event 'save' has no field
         'amont'. Did you mean 'amount'? #}
      <button @c-click="save({amont: 1})">Add</button>

      {# Error: Server event 'save' rejects this value
         for field 'amount': Expected int, got str. #}
      <button @c-click="save({amount: '1'})">Add</button>

      {# Error: Server event 'save' requires field
         'amount', which this call does not send. #}
      <button @c-click="save()">Add</button>

      {# Right #}
      <button @c-click="save({amount: 1})">Add</button>
    """
```

Citry checks what it can read from the template:

- each key of an object literal, even next to a `...` spread;
- a literal value, such as `'1'`, `true`, or `null`, and both results of a
  condition such as `wide ? 2 : 'all'`, with the server's own rules. The
  browser sends the arguments as JSON, so a string is not turned into a
  number. A handler that accepts `GET` may get them as a query string,
  where `'2'` fits an `int` field, so a value is reported there only when
  both ways fail;
- a required field, when the object has no `...` spread and no computed
  key, such as `{[name]: 1}`.

A call with no arguments is reported only on an element that cannot
contain a form, such as `<button>`. On a `<form>`, on an element that may
hold one, or for the `submit` event, the browser may send the form's
fields instead. When that binding is an `@c-submit` on the `<form>`
itself, [the form field rules](#check-form-fields) check the fields. A
Pydantic `data` class is not checked, because Pydantic converts values
and may read a field under another name.

Each mistake has its own setting: `rule_unknown_server_event_field`,
`rule_missing_server_event_field`, and
`rule_incompatible_server_event_field`. These rules need your
application: `citry --app ... check` reports them, and so does the editor
once it has loaded your application. While a handler or its `data` class
has unsaved changes, the editor stops checking calls to that handler
until you save the file.

### Form fields { #check-form-fields }

A form whose `@c-submit` names only the handler, as in `search` or
`search()`, sends its named controls as the handler's arguments, with or
without JavaScript. Citry compares each control's `name` with the
handler's `data` class:

```citry
class SearchIn:
    q: str


class Search(Component):
    class Events:
        def search(self, data: SearchIn):
            ...

    template = """
      {# Error: Server event 'search' requires field
         'q', but no control in this form has that
         name. #}
      <form @c-submit.prevent="search">
        {# Error: The form sends field 'qeury', which
           server event 'search' does not declare. #}
        <input name="qeury" />
      </form>

      {# Right #}
      <form @c-submit.prevent="search">
        <input name="q" />
      </form>
    """
```

Citry checks each `<input>`, `<select>`, `<textarea>`, and submit
`<button>` with a `name` written in the template. A submit button sends
its name only when it submits the form, and a checkbox only when it is
checked, so such a mistake fails only those submits.

Citry leaves out a control that the browser may not send with this form,
or may send under another name:

- a disabled control, including one inside a disabled `<fieldset>` or
  with a bound `:disabled`;
- a control tied to another form by its `form` attribute;
- a file input, a button that cannot submit, and a button whose click
  is prevented, as in `@click.prevent`;
- a control whose `type` or `name` is written as an expression, or that
  has an attribute spread such as `v-bind="attrs"`.

It also leaves out the host's CSRF field, such as Django's
`csrfmiddlewaretoken`, because the server removes it before it checks the
`data` class ([CSRF in forms](/security/#csrf-tokens-in-forms)). An image
button, `<input type="image">`, sends where it was clicked as `x` and
`y`, or `go.x` and `go.y` for `name="go"`, so Citry checks those names
instead.

A required field without a control is reported only when the template
shows every control the form can send. The check is off for a form that
holds a component, custom element, slot, `<template>`, loop, `v-html`,
`#c-ignore` content, attribute spread, or a `name` written as an
expression. It is also off when the form has an `id`, because a control
elsewhere could join the form with its `form` attribute.

Each mistake has its own setting: `rule_unknown_form_field` and
`rule_missing_form_field`. Like the argument rules, they need your
application.

## Misspelled CSS variables { #find-misspelled-css-variables }

Each key that `css_data()` returns becomes a CSS custom property with the
same name, such as `--accent` for the key `accent`. A typo in `var()` reads
a property that nothing sets, so the browser ignores the declaration:

```citry
class Board(Component):
    def css_data(self, kwargs, slots):
        return {"accent": "blue"}

    css = """
      h1 {
        /* Warning: Nothing sets --acent, so the browser
           ignores this declaration. Did you mean
           --accent, from css_data()? */
        color: var(--acent);
      }
    """
```

Citry reports a `var(--name)` in the component's own CSS only when the
name is one typing slip from a `css_data()` key, so a variable that a site
stylesheet or a parent component sets is left alone. A `var()` with a
fallback value, such as `var(--acent, blue)`, and a property the same CSS
sets itself are not reported, and neither is a component whose
`css_data()` keys Citry cannot all read. The rule is a warning by default
and needs your application, so only `citry --app ... check` reports it.

## Check rules in CI

Run the check against your application, so it knows every component and
reads your `LintSettings` and each component's `Lint` class:

```console
citry --app myproject.app:app check
```

Warnings are printed, and included in `--format json` output, but do not fail
the command. Any error exits with status 1. See
[Command line](/advanced/cli/#check-component-templates).

## Less common cases

### Without a loaded app

`citry check --static`, and an editor that has not loaded your application,
do not know every component's template data. They skip the unknown-name
rules, the [component event](#find-misspelled-component-events) rule,
which reads each child's `emits`, and the rules for
[repeated components](#find-repeated-components-without-keys),
[prop assignments](#find-prop-assignments),
[server event arguments](#check-server-event-arguments), and
[CSS variables](#find-misspelled-css-variables).

They still run every rule that reads only the template: the Alpine,
attribute-value, and misspelled-directive rules, and the rules for
[misspelled HTML names](#find-misspelled-html-names),
[Vue compile errors](#find-vue-compile-errors),
[blocks inside `<p>`](#find-invalid-nesting),
[duplicate ids](#find-duplicate-ids), and
[images without alt text](#find-images-without-alt-text). An `<img>`
that is a template's only top-level element is never reported there,
because these tools cannot tell whether the component has browser code.

They cannot read your `LintSettings`, but
they do read the `Lint` class of the component that declares an inline
`template`, without running your code:

- A rule set to a plain string, such as
  `rule_misspelled_directive = "ignore"`, applies as written.
- A `Lint` inherited from a component class in the same file applies too,
  and `Lint = None` drops it, as with a loaded application.
- A subclass in the same file whose only base is that component, and that
  sets neither `template` nor `template_file`, renders the same template.
  The strictest severity among those components applies, as in
  [shared templates](#shared-templates).

A rule keeps its default severity when neither the component nor a
component class it inherits from in the same file sets it, or when the
value cannot be read from the source: a name imported from
another module, a value computed at run time, a `Lint` class with its own
base class, or a `Lint` assigned inside an `if`. In the editor, a
template file, and a template whose closing quotes are not typed yet, use
the defaults too, because no `Lint` class can be read for them. The one
exception to the defaults: an invalid attribute value is a warning there,
so a value that a page script reads cannot fail the check when only
`LintSettings` turns the rule off.

To keep a name that is really meant for the browser out of the check, pass
it through `c-bind`. These tools also cannot tell which values an
extension's template syntax produces, so they may report a value that
`citry --app ... check` does not.

### Imported base classes { #templates-the-check-cannot-find }

When a component extends a class from another module of your project,
the file alone does not show that the class is a component:

```citry
from app.base import BaseCard


class Card(BaseCard):
    template = """
      <article>{{ title }}</article>
    """
```

`citry --app ... check`, with or without `--types`, and an editor that has
loaded your application find `Card` among your registered components and
check its template.

Without your application, Citry skips the template.
`citry check --static` lists each skipped template as a note, and the
editor marks the class name with an information message
([`citry.check.template-not-checked`](/ide/diagnostics/#citry.check.template-not-checked)).
Nothing is wrong with the code. To have the editor check the template, give
it your application, for example with the `citry.app` setting in
[VS Code](/ide/vscode/).

The editor finds these classes by the names they had when it loaded your
application. A class you add or rename keeps the message until the editor
loads your application again, which VS Code does when you save a Python
file.

### Shared templates

When several components use the same template or JavaScript file, Citry
applies the strictest severity among them. To silence a rule for that file,
every one of those components must set it to `"ignore"`. The
[server event argument](#check-server-event-arguments) rules check a call
in a shared template only when all those components use the same `data`
class for its handler.

### Data with extra keys

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

### Mixins and extends

The unknown member check needs every name the component defines. When the
component's Vue Options use `mixins` or `extends`, those names are not in
the source, so Citry skips the check. A Python loop variable read by Vue is then
reported as the `citry.vue.python-variable` warning.

### Unchecked attributes

The attribute-value check does not look at a bound value that is not one
string, such as `:dir="direction"` or `c-dir`, or at a binding with a
modifier such as `.prop`. It also skips component tags, `<c-element>`,
custom elements such as `<my-widget>`, elements inside `<svg>` or `<math>`,
and attributes that take a list of words, such as `rel`, `sandbox`, or
`autocomplete` on `<input>`.

For `type` on `<ol>` and `<li>`, letter case matters: `"a"` and `"A"` are
different list markers.

When the editor or `citry check --types` also runs TypeScript, a bound value
that Vue's types reject is reported once, by this rule, at this rule's
severity.

### Window names, meta tags

`target` and `formtarget` accept any window name, so Citry checks only names
that start with an underscore. The valid ones are `_blank`, `_self`,
`_parent`, and `_top`, so `target="_new"` is reported. The `name` of an
`<iframe>` or `<object>` may not start with an underscore at all.

`http-equiv` on `<meta>` is checked against the values browsers act on:
`content-type`, `default-style`, `refresh`, `x-ua-compatible`, and
`content-security-policy`. Browsers ignore a header name such as
`Cache-Control` there, so the message says to send it as an HTTP header:

```citry-html
{# Error: browsers ignore this; send Cache-Control as a header. #}
<meta http-equiv="Cache-Control" content="no-cache">
```

### Alpine load errors

An Alpine-only event modifier such as `@click.outside`, and `v-once` or
`v-memo`, are not lint rules, so no setting turns them off. The template
fails to load, with a message that shows what to write instead. See
[Vue in templates](/syntax/vue/).

### Navigate declared names

In the editor, go to definition on a name declared in `template_variables`
opens its key in your `LintSettings`, when the settings are written directly
in the `Citry(...)` call or through a simple variable. A name declared in a
component's `Lint` class opens that class, including an inherited one.
Settings built by a function still work, but have no definition to open.

### Extension variables

An extension that adds template variables can describe them with
[`TemplateNamespaceContribution`][citry.TemplateNamespaceContribution], so
Citry knows them. It can list the names, or say that it adds names it cannot
list. It cannot lower the severity your application chose.
