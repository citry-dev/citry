---
title: VS Code
description: Highlight Citry templates and connect VS Code to the Citry language server.
---

# VS Code

The Citry extension highlights `template`, `js`, `css`, and `messages`
multiline strings inside Python components. It also supplies language modes for
standalone Citry templates and Fluent `.ftl` files, and starts one `citry-lsp`
process for each workspace folder. Formatter commands edit definite template,
JavaScript, and CSS sections while leaving Fluent and the selected Python
formatter unchanged.

`citry-lsp` 0.1.3 is public on PyPI. Install the extension's 0.1.2 release from
the [Visual Studio Marketplace](https://marketplace.visualstudio.com/items?itemName=citry-dev.citry),
[Open VSX](https://open-vsx.org/extension/citry-dev/citry), or the matching
[GitHub Release](https://github.com/citry-dev/citry/releases/tag/vscode-citry%400.1.2).

## See it in action

Citry completes registered components and their inputs without leaving the
Python file:

<c-image src="https://raw.githubusercontent.com/citry-dev/citry/main/packages/editors/vscode/images/autocomplete.gif" alt="Citry component autocomplete inside an inline Python template" width="960" />

Hover hints explain template values, while references and navigation connect
them to their Python definitions:

<c-image src="https://raw.githubusercontent.com/citry-dev/citry/main/packages/editors/vscode/images/refs_hints.gif" alt="Citry hover hints and references connecting a template to Python" width="960" />

## Install the language server

Install `citry-lsp` in the same Python environment as the Citry project:

```console
python -m pip install citry-lsp
```

Keeping the server in the project environment lets it import the registered
component catalog. An isolated server can still check syntax, but it cannot
know the application's component names, inputs, or slots.

Install **Citry** from the
[Visual Studio Marketplace](https://marketplace.visualstudio.com/items?itemName=citry-dev.citry)
or [Open VSX](https://open-vsx.org/extension/citry-dev/citry). Cursor, Windsurf,
VSCodium, and other compatible desktop forks can use the Open VSX release. The
same qualified VSIX is attached to the
[GitHub Release](https://github.com/citry-dev/citry/releases/tag/vscode-citry%400.1.2).

## Select the registry target

Set `citry.app` to the `module:attribute` path of either the project's
[`Citry`][citry.Citry] instance or a reusable
[`ComponentLibrary`][citry.ComponentLibrary]:

```json
{
  "citry.app": "myproject.app:citry_app"
}
```

For example, select the Citry UI library directly while working without a host
application:

```json
{
  "citry.app": "citry_ui:__citry_library__"
}
```

The library form creates an isolated registry with Citry's built-ins and that
library. It does not include host-application components, configuration, or
host-provided extensions. If the library requires one of those extensions,
expose a configured `Citry` instance that installs it and select that instance
instead.

The extension normally follows the interpreter selected by Microsoft's Python
extension. Set `citry.python` to an explicit executable when that integration
is unavailable:

```json
{
  "citry.python": "/path/to/project/.venv/bin/python"
}
```

If importing the selected app needs environment variables, point
`citry.envFile` to a dotenv file:

```json
{
  "citry.app": "myproject.app:citry_app",
  "citry.envFile": "${workspaceFolder}/.env"
}
```

Relative paths resolve from the workspace folder, and file values override
variables inherited by the Extension Host. Citry applies them only to its
isolated app-discovery worker; it does not change the environment of the
language server, Python extension, terminal, application server, or tests.
Saving, creating, or deleting the file automatically reloads the component
registry. A configured file that is missing or malformed keeps syntax-only
features available and explains the setup failure in **Citry: Show Language
Server Status**. Citry's environment adapter does not print parsed values.

For Django, include settings needed before importing the selected target. The
language server imports that module directly and does not run `manage.py`:

```ini
DJANGO_SETTINGS_MODULE=myproject.settings
DJANGO_SECRET_KEY=editor-development-secret
```

With no app configured, the status bar reports **syntax only**. Definite
inline templates and files explicitly using the Citry Template language are
still checked, but unknown components and their contracts are not inferred.

## Complete Vue expressions and component JavaScript

In a registry-owned component template, Citry connects Vue expressions to
the component's browser data:

```citry
class Search(Component):
    class JsData:
        query: str
        result_count: int

    class State:
        page: int

    template = """
      <p v-text="query.toUpperCase()"></p>
      <button @click="$state.page += 1">Next</button>
    """
```

Top-level `JsData` names complete in native Vue directives and bindings. Hover shows
their JSON-derived JavaScript type, and **Go to Definition**, **Go to
Declaration**, and **Find All References** connect them to the exact Python
field or a conservatively inferred `js_data()` dict key. Public Events
`State` fields receive the same navigation through `$state`.

A `js_data()` value that reads attributes of a Kwargs field takes its type
from the annotations of the classes it passes through:

```citry
class TaskCard(Component):
    class Kwargs:
        task: Task  # a dataclass with `lane: str`

    def js_data(self, kwargs, slots):
        return {"laneKey": kwargs.task.lane}
```

Here `this.laneKey` is a `string`. Dataclasses, NamedTuples, Pydantic
models, and plain annotated classes can be read this way, and an `Enum`
member's `.value` takes the type of its values, such as `string`. A
NamedTuple is sent as an array and a TypedDict as an object. A chain
through an optional value, such as `reviewer: Owner | None`, is untyped.
Returning a whole dataclass or other class instance, such as
`kwargs.task`, is reported as
[`citry.js-data.unsupported-type`](/ide/diagnostics/#citry.js-data.unsupported-type),
because Citry cannot prove it crosses the JSON wire.

### Work with component members in `this` and the template

Inside `$component({ ... })`, `this` has the type of the live component, and
so does each name a Vue expression in the template reads. Completion and
hover know every member, and **Go to Definition** opens where it is declared:

```citry
class Counter(Component):
    class JsData:
        step: int

    template = """
      <button @click="add()" v-text="count"></button>
    """

    js = """
      $component({
        data() { return { count: 0 }; },
        methods: {
          add() { this.count += this.step; },
        },
      });
    """
```

Hovering `this.count` or `count` in the template shows `number`, and
**Go to Definition** from either opens the `count` key in `data()`. From
`this.step`, it opens the `step` field in `JsData`.

| Member | Declared in | Go to Definition opens |
| --- | --- | --- |
| Prop | `props` | The prop's key |
| Injection | `inject` | The injected name |
| `data()` value | `data()` | The returned key |
| `setup()` binding | `setup()` | The returned key |
| Computed value | `computed` | The computed entry |
| Method | `methods` | The method |
| Browser data | `js_data()` or `JsData` | The Python field or dict key |

`this` has this type in methods, computed getters and setters, `watch`
handlers, lifecycle hooks such as `mounted()`, and `provide()`. When
`onServerRender` or `init` is part of the same object, its `component`
value gets the same type. Citry's helpers, such as `$sendEvent`,
`$loading`, and `$state`, and Vue's own `$el`, `$refs`, and `$emit` are
included. The next section describes how `$el`, `$state`, and `$emit` are
typed.

`this` in `data()` has props, injections, `js_data()` keys, and Citry's
helpers. The editor does not type the `data()` result or the methods
there.

Types come from the `$component` object as you write it. A section with the
wrong shape, such as a `computed` entry that is a number instead of a
function, can stop computed values and methods from being typed until you
fix it. A
template that several components share keeps names untyped, because each
component may declare them differently, but **Go to Definition** still lists
each component's declaration.

### Types for `$el`, `$state`, and `$emit`

`$el` takes its type from the top-level node of the component's template,
because Vue sets it to the node that the template renders first:

| Template root | Type of `$el` |
| --- | --- |
| One element, such as `<button>` | That element's type, such as `HTMLButtonElement`. `<svg>` is `SVGSVGElement` |
| `v-if` and `v-else`, or `c-if` and `c-else` | Each branch's type joined with `\|`, plus `Comment` when there is no `v-else` or `<c-else>`, because Vue then renders a comment |
| A child component tag, such as `<c-Lane>` | The child's own `$el` type |
| Text only | `Text` |
| Several nodes, `v-for`, `c-for`, a slot, or a template the editor cannot read | `Node` |

When the template renders several nodes, Vue sets `$el` to an empty marker
node placed before them, not to the first element. The marker is a text
node, or a comment on a page Vue took over from the server. To reach the elements,
use `$refs` or the `els` value in `onServerRender`. As in Vue's own types,
`$el` never includes `null`, but it is `null` until the component mounts,
for example in `data()` or `created()`.

`$state` is Citry's [Events State](/reference/browser-apis/#state) for the
component, not Vue's `data()` and not a Pinia store. Its fields come from the
component's `State` class. Every public field can be assigned unless the
`State` class sets `_model`; then only the fields it lists can be assigned,
and the rest are read-only. A component without `State` has no
fields, so completion offers none. Hovering `this.$state` says the same.

`$emit` follows the `emits` option, as Vue's `defineComponent()` does:

```javascript
$component({
  emits: {
    'drop-task'(/** @type {{taskId: number}} */ payload) {
      return true;
    },
    closed: null,
  },
});
```

- The array form, such as `emits: ['drop-task']`, limits `$emit` to the
  listed names and accepts any values after the name.
- In the object form, the validator's parameters type the values. A `null`
  validator accepts any values.
- Without `emits`, `$emit` accepts any name, as in Vue.

Completion inside `this.$emit('')` offers the declared names, and hovering
`$emit` in component JavaScript or a template shows the values each event
takes. In a parent template, a listener on the child's tag uses the same
types: `@drop-task="move($event)"` on `<c-Lane>` types `$event` as the first
value the child emits, and the parameters of an inline function such as
`@drop-task="(payload) => move(payload)"` get the emitted values' types.
Citry's `@c-drop-task` server-event binding on the same tag reads the same
`$event`. A listener for an event the child does not declare gets the DOM
event of that name, because Vue then passes the listener to the child's
root element. When the child lists its events as an array, or Citry cannot
read its `emits`, `$event` is `any`.

On an HTML element, `$event` is the DOM event of the listener's name, such
as `KeyboardEvent` for `@keydown`. A name the DOM does not define, such as
`@board:notice`, is a `CustomEvent`, so `$event.detail` works. A template
cannot cast, so `$event.target` and `$event.currentTarget` are `any`.

Citry also checks event names, in the editor and in `citry check`, when
`emits` is an array of strings or an object with plain keys:

- `this.$emit('name')`, `component.$emit('name')`, or a template's
  `$emit('name')` with a name that `emits` does not list is an error
  ([`citry.browser.undeclared-emit`](/ide/diagnostics/#citry.browser.undeclared-emit)).
  A prop named `on<Event>`, such as `onPing` for `ping`, also declares the
  event, as it does in Vue.
- A listener on a child component tag whose name the child does not declare
  is a warning
  ([`citry.browser.undeclared-component-event`](/ide/diagnostics/#citry.browser.undeclared-component-event)).
  Vue passes such a listener to the child's root element, where it runs
  only if that element dispatches a DOM event with the same name, so a
  misspelled name stays silent. A child's `on<Event>` prop also declares
  the event. Only a name with a hyphen, a colon, or an uppercase letter is
  reported, because a plain lowercase name such as `@click` is usually a
  native DOM event.

A value that does not match a validator's parameter types is a TypeScript
error; see
[TypeScript errors in component JavaScript and templates](#typescript-errors-in-component-javascript-and-templates).

### Types, checks, and navigation in component JavaScript

The component's direct `js` or resolved `js_file` receives matching types for
the complete `$component` callback context. Direct synchronous writes to
the callback's `component` value use the generated public-instance type, and
`v-for` and `v-slot` bindings receive lexical scope and exact navigation. A static
`$component({ props, onServerRender })` declaration also types its read-only props.
VS Code's installed JavaScript service supplies ordinary JavaScript member
completion, hover, and definitions; Citry keeps the Python-backed origins
authoritative. Unknown Vue expression roots are errors by default through the shared
Citry lint policy. Free names inside a `$component` initializer are also
errors by default, which catches an undeclared context value when it was
used but not destructured. Configure the severity or real host-provided
globals through `LintSettings`; see [Template linting](/ide/template-linting/).
A `component.<name>` or `this.<name>` read that names nothing the component
defines is an error. Citry checks this only when it can read every
`js_data()` key and every Vue Options section from the source.

Hovering `$component`, a destructured callback value, or a Citry Vue helper
such as `$sendEvent`, `$loading`, or `$error` shows its Citry contract and a
link to the matching browser API reference. Handler-name completion opens
inside the literal arguments to `sendEvent`, `$sendEvent`, `$loading`, and
`$error`, including from an empty string.

A literal `sendEvent()` or `$sendEvent()` name, a declarative `@c-*` handler,
and a handler passed to `$loading()` or `$error()` must match an effective
Python event handler and navigate to that method. Dynamic names are left open,
as are all `onEvent()` and `$onEvent()` names.

Native props on statically resolved child components validate
unknown keys, required props, and proven value types against the child's
static `$component({props})` declaration. A prop key hovers and navigates to
that declaration. A spread keeps explicit keys checkable but suppresses a
missing-required conclusion; dynamic component targets remain unproven. When a
`JsData` annotation or known literal value cannot cross
Citry's strict JSON wire, Citry reports `citry.js-data.unsupported-type` as a
warning and lets JavaScript tooling treat that value as `any`.

### TypeScript errors in component JavaScript and templates

The editor reports TypeScript's own errors in component JavaScript and in Vue
expressions, on the line you wrote, whether the code sits in a `.js` file, a
template file, or a string in a Python file:

```citry
class Lane(Component):
    template = """
      <button @click="startDrag('first')">Drag</button>
    """
    js = """
      $component({
        emits: {
          'drop-task'(/** @type {{taskId: number}} */ payload) {
            return true;
          },
        },
        methods: {
          clearDropTarget() {},
          startDrag(/** @type {number} */ id) {
            // A method is not a boolean.
            this.clearDropTarget = true;
            // The payload does not match the validator.
            this.$emit('drop-task', 'x');
            // One argument too many.
            this.startDrag(1, 2);
            // `$el` is the template's <button>.
            this.$el.fooBar;
          },
        },
      });
    """
```

Each of those lines, and `startDrag('first')` in the template, shows an
error with the source `Citry (ts)` and a code such as
`citry.typescript.ts2322`, where the number is TypeScript's own. Citry
reports these kinds of TypeScript errors:

| Mistake | Example | TypeScript codes |
| --- | --- | --- |
| A value of the wrong type | `this.clearDropTarget = true` | 2322, 2345, 2769, and related |
| A member that does not exist | `this.$el.fooBar` | 2339, 2551, 2353, 2561 |
| The wrong number of arguments | `this.startDrag(1, 2)` | 2554, 2555, 2556, 2575 |
| A syntax error in JavaScript inside a Python string | `const = 1` | 1000 to 1999 |
| A bound HTML attribute value of the wrong type | `:draggable="'treu'"` | 2345 |

A bound attribute such as `:draggable` or `:style` on an HTML element is
checked against Vue's types for that element's attributes, so
`:style="1"` is an error while `:style="{ color: 'red' }"` passes. A
keyword the HTML Standard lists for the attribute, such as the empty value
in `:translate="''"`, is also accepted, as the static
[attribute-value check](/ide/template-linting/#find-invalid-html-attribute-values)
accepts it. Some attributes Vue types as any string, such as `dir`, so a
bound `:dir="'sideways'"` is not reported, though the same static value
is. Vue's types are case-sensitive, so a bound `'LAZY'` is an error where
a static `"LAZY"` passes. Citry does not check an attribute Vue does not
declare, such as `data-id`, any attribute on a custom element, or a
binding with a modifier such as `.prop`.

Vue types `aria-*` attributes too. `aria-expanded` takes a boolean or
`'true'`/`'false'`, so `:aria-expanded="String(open)"` is an error because
`String()` returns any string. Bind the boolean itself:
`:aria-expanded="open"`. Vue also types `id` and `title` as strings, so
`:id="task.id"` is an error when the id is a number; bind
`:id="String(task.id)"`.

VS Code's own TypeScript runs the check, so you need no Node.js install, but
the built-in TypeScript and JavaScript Language Features extension must be
enabled. When it does not answer, the workspace folder's Citry output
channel says so once. The check uses the same types that completion and hover show, and
it runs after Citry's own diagnostics, so its errors can appear a moment
later.

Some TypeScript errors are left out on purpose:

- A mistake that Citry already reports keeps only Citry's finding. For
  example, an unknown name inside `$component` shows
  [`citry.component-js.unknown-variable`](/ide/diagnostics/#citry.component-js.unknown-variable),
  `this.startDargg()` shows
  [`citry.component-js.unknown-member`](/ide/diagnostics/#citry.component-js.unknown-member),
  and an event name `emits` does not declare shows
  [`citry.browser.undeclared-emit`](/ide/diagnostics/#citry.browser.undeclared-emit).
- An unknown name in a template follows
  [`citry.vue.unknown-variable`](/ide/diagnostics/#citry.vue.unknown-variable)
  and its lint severity, so TypeScript does not report it.
- A value Citry cannot type, such as an injection, a server event's result,
  or a `JsData` field that cannot cross the JSON wire, is `any`, so reading
  it is never an error.
- TypeScript's strict mode is off, so a `data()` value that starts as
  `null` can take any value later, and implicit `any` is not reported.
- A query by CSS selector, such as `this.$el.querySelector('#name')`, returns
  `any`, because the selector does not say which element it finds. A query
  by tag name, such as `querySelector('input')`, keeps the tag's type. A
  member of `window` that the DOM does not declare, such as `window.htmx`,
  is `any`, because a page script may add it.
- A minified file such as `runtime.min.js` is not checked.
- A `js_data()` value types its key as the value's general type, such as
  `boolean` for `False`, because Vue code may change it later.

Set `citry.typeCheck` to `false` to turn these errors off. The language
server can also run the check for other editors; it then uses the `tsc` in
your project's `node_modules` or on `PATH`. Run the same check in a terminal
or CI with [`citry check --types`](/cli/#check-types-with-typescript-and-ty).

## Navigate i18n messages and profiles

When the selected application configures i18n, Citry uses its checked catalog
index across Python, templates, Fluent, Vue expressions, and component JavaScript.
Literal message IDs complete and navigate from `tr()`,
`<c-trans message="...">`, `self.i18n.tr()`,
`Component.I18n.client_messages`, `$i18n.tr()`, and the injected component
`i18n` service. Checked `$c-tr:message.output[target]` directives and bounded
`i18n.bind({ message: "...", output: "..." })` calls use the same index. Go to
definition on a `$c-tr` message opens the selected message value, or the exact
Fluent attribute when the directive includes `.output`. Hover shows the
selected output, its typed direct and
transitive parameters, translator descriptions, and defining owner. The
catalog belongs to the selected Citry application, so a definition may live
in another component, another Python file, or a configured catalog package.

Hover an argument name such as `count` in
`tr("account-unread", count=value)` to see its `@param` type and description.
Go to definition on that argument to open the exact `@param` declaration.
The same rule works in template and Python `tr()` calls, Vue `$i18n.tr()`,
`component.$i18n.tr()` or `this.$i18n.tr()` in component JavaScript, and
literal `<c-trans>` values and fills.

Named formatter and parser profiles complete in the matching operation, such
as `fmt.number(..., format="...")`, `self.i18n.parse.percent(...)`, and
`$i18n.format.currency(...)`. Template `fmt` methods include their call
signatures and return types. A misspelled template method or a literal profile
that is not registered for that exact operation is an error. `$i18n` in a
template and `component.$i18n` or `this.$i18n` in component JavaScript
include the nested `context`, `format`, and `parse` APIs. Public
Fluent message references navigate to the same defining source; private term
references navigate within their own `messages` block.

The live diagnostics use the same Rust Fluent parser and checked app catalog.
They report unsupported `@param` types, unknown literal keys or profiles,
missing, extra, or provably mistyped message arguments, and mismatched
`<c-trans>` values or fills. `$c-tr` values receive the same named-input
checks, and malformed directive names such as `$c-tr:`, `$c-tr:notice[]`, or
`$c-tr:notice.` are errors before rendering. Component inputs complete in
both their static
form (`client`) and their expression form (`c-client`). `$i18n` receives
semantic help only inside a statically known client-enabled `<c-i18n>`
provider; a server-only nested provider blocks that scope.

These features need `citry.app`, because syntax-only mode has no complete
catalog or profile registry. Fluent syntax coloring itself remains available
without the application index. Static checks follow literal message IDs,
literal profile names, and statically named argument-object keys. A dynamic
message ID or computed argument object remains a runtime responsibility.

## Navigate from CSS variables to Python data

When the selected registry owns a component's CSS, Citry connects a
`var(--name)` use to the Python data that produces it:

```citry
from citry import Component


class Chart(Component):
    class CssData:
        chart_height: str

    css = """
    .chart {
        height: var(--chart_height);
    }
    """
```

Inside `var(--...)`, completion offers exact `CssData` names. Hover shows the
Python producer, **Go to Definition** and **Go to Declaration** open its field,
and **Find All References** lists uses in that physical stylesheet. The same
features work for direct string keys inferred conservatively from
`css_data()`, so `{"row-color": value}` is available as `--row-color`.

Both direct `css` literals and resolved `css_file` files are supported. A CSS
file shared by several components exposes only names supplied by every proven
owner. Saving or synchronizing a Python edit rechecks the schema and asset
owner before Citry returns navigation.

Citry leaves other custom properties alone. A value may come from an ancestor,
the host page, a theme, JavaScript, an extension, or another stylesheet, so an
unmatched `var(--host-token)` is not an error. VS Code's CSS service continues
to provide ordinary CSS completion, validation, and local custom-property
navigation alongside Citry's producer information.

## Associate standalone templates

Citry accepts any filename in `template_file`, so the extension does not claim
ordinary `.html` files. Add a project-specific association when appropriate:

```json
{
  "files.associations": {
    "templates/components/**/*.html": "citry-html"
  }
}
```

## Format Citry documents

The command palette exposes only two Citry formatting commands:

- **Citry: Format Document** formats every definite direct `template`, `js`,
  and `css` literal in the current Python file.
- **Citry: Format at Cursor** formats only the direct literal body containing
  the cursor.

Formatting expands Citry/HTML structure and formats embedded JavaScript and
CSS while preserving readable Python triple-quoted strings:

<c-image src="https://raw.githubusercontent.com/citry-dev/citry/main/packages/editors/vscode/images/formatting.gif" alt="Citry formatting an inline template, JavaScript, and CSS inside a Python component" width="960" />

The commands do not format `messages` blocks or standalone `.ftl` files.
Fluent syntax highlighting is available in both places, but Citry does not yet
define a Fluent formatting contract.

Both include Citry/HTML structure and Python expressions, eligible direct
JavaScript and CSS, and eligible `<script>` and `<style>` bodies. A cursor on a
`template_file`, `js_file`, or `css_file` path, a method such as
`template_data`, or unrelated Python code is outside a format region and is
refused without edits. The commands do not follow a Python declaration into
another file; open the target directly or use `citry format` for statically
resolved file assets. For a standalone JavaScript or CSS file, “directly” means
its normal language formatter; Citry does not wrap generic JS/CSS documents.

A file in the Citry Template language is one template, so either command
formats the whole document. The explicit commands also accept an HTML-mode
file that the configured registry proves is a resolved `template_file`, while
unrelated HTML is refused. Associate the file with `citry-html` to use VS
Code's standard formatter and format-on-save:

```json
{
  "[citry-html]": {
    "editor.defaultFormatter": "citry-dev.citry",
    "editor.formatOnSave": true
  }
}
```

Citry includes Prettier for deterministic embedded JavaScript and CSS
formatting. If
[Prettier for VS Code](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)
is installed and selected for that language, Citry uses its dedicated action so
your workspace Prettier configuration applies. Otherwise it uses bundled
Prettier 3.9.6 with Citry's canonical two-space indentation. Your default
formatters for standalone JavaScript and CSS files remain unchanged. The CLI
uses its explicit native Biome adapter.

Whitespace-sensitive multiline literals/comments and position-sensitive
hashbang, `@charset`, or BOM bodies are also left unchanged rather than being
unsafely reindented.

Keep the normal Python formatter selected and add Citry as an independent
save action. This uses the same whole-document Citry behavior as **Citry:
Format Document**:

```json
{
  "[python]": {
    "editor.codeActionsOnSave": {
      "source.format.citry": "explicit"
    }
  }
}
```

The Citry/HTML and built-in Python-expression, `c-for`, and `c-fill data`
passes produce the same bytes across the CLI, Python API, language server, and
extension. Embedded JavaScript/CSS output also matches when the provider,
version, and options match. For deterministic automation, configure the CLI's
explicit Biome adapter instead of relying on editor provider ordering.

## Look up Citry syntax

Hover a Citry structural tag, fixed directive, or structural attribute to see
a concise explanation and a link to its full Citry guide. This works in
syntax-only mode, so `<c-slot>`, `required`, `c-bind`, `#c-key`, and related
syntax do not require an application registry or an installed HTML provider.
Dynamic HTML attributes such as `c-class` keep using the HTML provider's
documentation for their underlying native attribute.

HTML assistance also enters parser-proven nested-template values. Use the
opposite quote for attributes inside the nested value, so a double-quoted host
contains ordinary single-quoted HTML attributes:

```html
<c-card c-body="<><input type='email' autocomplete='email' /></>" />
```

Completion, hover, and go to definition are mapped back from that isolated
fragment. For `<c-element>`, a literal target such as `is="form"` receives
form-specific attribute intelligence. A dynamic `c-is` or `c-bind` keeps only
global HTML attributes because its eventual tag is not proven. Citry returns
no forwarded result when the current parse, source map, provider response, or
document version is uncertain.

## Complete template roots

Inside a registry-owned component template, Citry completes and documents
declared `TemplateData` fields, runtime `template_globals`, and lint-only
variables in interpolations and Python-valued attributes. Global runtime values
receive conservative inferred types; explicit annotations and descriptions use
the application's [template lint settings](/ide/template-linting/).
When no `TemplateData` schema is declared, it also infers conservative roots
from direct dict keys and modelled mapping operations in `template_data()`.
The inherited implementation exposes effective `Kwargs` fields automatically.
Go to definition targets the annotated field or exact returned dict key.
Go to references lists uses of the same proven root or exact loop/fill binding
inside that physical template. Go to declaration targets the authored field,
dict key, or lexical introduction. Go to type definition targets the actual
Python class or standard-library type when every component consumer and return
path produces a safe mapped answer. Unused fill bindings target their current
neutral `Any` contract. Unsaved Python edits that change component inheritance
or template ownership are revalidated before these registry-backed results are
shown.
The live ownership proof covers direct string and `pathlib.Path(...)`
declarations. Imported constants, factories, decorators, metaclasses, and
other dynamic template selection use the loaded registry, but variable
navigation is withheld while Python source is synchronized because those
dependencies cannot be bounded safely. Save and restart the language server to
refresh that registry state.

Once a root is proven, Citry also supplies ordinary Python member and call
completion, type hover, user-member navigation, signature help, and mapped
diagnostics. This works in interpolations, Python-valued attributes, loop
clauses, and nested templates. Template conditions narrow optional and union
types, while shared templates keep only suggestions that apply to every
proven component consumer and return path.

Citry also gives every name used as a call target the standard Python function
or method syntax scope. That keeps calls such as `tr(...)`, `fmt.currency(...)`,
and application helpers visually distinct even before the language server has
enough project information to prove their types. A member that is only read,
such as `fmt.currency` without `(...)`, keeps its ordinary member scope.

The language server installs its supported Python analyzer automatically in
the same environment. If that analyzer cannot start or stops responding,
Citry reports the degradation once and keeps parser checks plus root-level
completion, hover, and navigation available. Unknown root names use the policy
configured on the `Citry` application, not a separate VS Code preference.

Open Python files use synchronized editor text, so adding or renaming a direct
key updates completion, hover, and navigation without saving or reloading the
app. Invalid source, ambiguous ownership, unsupported mapping escapes, and
roots not shared by every physical-template consumer are withheld rather than
guessed. The semantic analyzer is likewise limited to those mapped template
expressions and does not replace the Python extension for ordinary `.py` code.

### Check `c-*` values against their target's type

A `c-*` value on a component tag is a keyword argument, so it is also
checked against the child's `Kwargs` annotation. A wrong value shows a
`citry.python.invalid-assignment` error on the value:

```citry-html
{# TaskCard declares `task: Task` #}
<c-TaskCard c-task="1" />
```

ty's error names both types, here `Literal[1]` and `Task`. A missing or
unknown input is reported by the template's own input checks instead. The
check follows the annotation, not runtime validation, so a Pydantic
`Kwargs` field that turns `"1"` into `1` still reports a string passed
to an `int`. On an HTML element, `c-class` and `c-style` are checked the
same way: they take a string, a dict, a list or tuple of those, or
`None`, so `c-class="1"` is an error.

#### Fix a value whose type comes out too wide

ty reads each key of the dict that `template_data()` returns on its
own, so `{"size": "sm"}` passes `Literal["sm"]` to a
`size: Literal["sm", "md", "lg"]` input. A dict nested inside that
dict, such as each row of a list, is typed as a whole, and ty merges
its values into one union. A row's `size` then reports
`str | int` even though the template only reads the string:

```citry
class Steps(Component):
    def template_data(self, kwargs, slots):
        rows = [
            # ty types each row as dict[str, str | int]
            {"size": "sm", "index": index}
            for index in range(3)
        ]
        return {"rows": rows}

    template = """
      <c-for each="row in rows">
        <c-Step c-size="row['size']" />
      </c-for>
    """
```

Give the row a type of its own. A `TypedDict` keeps the value a plain
dict, so the template does not change:

```citry
from typing import Literal, TypedDict


class StepRow(TypedDict):
    size: Literal["sm", "md", "lg"]
    index: int


class Steps(Component):
    def template_data(self, kwargs, slots):
        rows: list[StepRow] = [
            {"size": "sm", "index": index}
            for index in range(3)
        ]
        return {"rows": rows}
```

A value computed by a function typed `-> str` is `str`, not one of the
input's choices. Annotate the function or variable with the `Literal`
type it really returns, or wrap the value in `typing.cast()` when the
check before it has already narrowed it.

## Keep template strings from becoming f-strings

Pylance can add an `f` prefix when you type `{` in a Python string. Its
`python.analysis.autoFormatStrings` setting is off by default. If your profile
or workspace enables it, add this workspace setting:

```json
{
  "python.analysis.autoFormatStrings": false
}
```

The setting applies to every Python file in the VS Code window. Pylance does
not provide a per-literal exception. Citry does not reverse editor changes, so
deliberate f-strings remain untouched. Editors without Pylance do not need this
setting.

## Current limits

- Highlighting of deeply nested or unfinished expressions is best effort.
- Parsing stops after the first syntax error.
- General Python-file analysis remains the responsibility of the configured
  Python extension; Citry analyzes only mapped template expressions.
- Embedded CSS receives highlighting, completion, hover, and formatting
  through VS Code providers, but Citry cannot request its diagnostics through
  VS Code's public API. Embedded JavaScript reports the TypeScript errors
  listed in
  [TypeScript errors in component JavaScript and templates](#typescript-errors-in-component-javascript-and-templates),
  not every JavaScript warning.
- Embedded JavaScript and CSS use bundled Prettier 3.9.6 unless Prettier for VS
  Code is installed and selected for that language. Other editor formatters do
  not replace that fallback.
- Each embedded provider pass is bounded to 30 seconds. VS Code does not expose
  cancellation for the underlying public formatter command, so Citry discards
  any result that arrives after that bound.
- `<script>` and `<style>` bodies containing Citry interpolation remain
  unchanged until a context-safe placeholder adapter is available.
- A TextMate grammar cannot prove that a class with a `template`, `js`, or
  `css` assignment inherits from `Component`, so unrelated assignments with
  those exact names may receive Citry highlighting.
