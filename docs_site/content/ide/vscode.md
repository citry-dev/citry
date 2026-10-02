---
title: VS Code
description: Get errors as you type, completion, go to definition, type checking, and formatting for Citry components in VS Code and its forks.
---

# VS Code

The Citry extension makes VS Code understand your components. Inside the
`template`, `js`, `css`, and `messages` strings of a Python component, and in
standalone template files, you get:

- errors as you type, such as a misspelled component tag or a variable your
  template data never provides;
- completion for component names, inputs, template variables, and browser
  data;
- hover with types, and go to definition from a template back to the Python
  field it came from;
- TypeScript type checks in component JavaScript and Vue expressions;
- formatting for the template, JavaScript, and CSS strings;
- coloring for each of those languages.

Citry completes components and their inputs without leaving the Python file:

<c-image src="https://raw.githubusercontent.com/citry-dev/citry/main/packages/editors/vscode/images/autocomplete.gif" alt="Citry component autocomplete inside an inline Python template" width="960" />

Hover explains template values, and references and navigation connect them to
their Python definitions:

<c-image src="https://raw.githubusercontent.com/citry-dev/citry/main/packages/editors/vscode/images/refs_hints.gif" alt="Citry hover hints and references connecting a template to Python" width="960" />

## Set up the extension

1. Install **Citry** from the
   [Visual Studio Marketplace](https://marketplace.visualstudio.com/items?itemName=citry-dev.citry)
   or [Open VSX](https://open-vsx.org/extension/citry-dev/citry). Cursor,
   Windsurf, VSCodium, and other desktop forks use the Open VSX release. Each
   release's VSIX file is also on
   [GitHub Releases](https://github.com/citry-dev/citry/releases).
2. Install the Citry language server in your project's Python environment:

    ```console
    python -m pip install citry-lsp
    ```

    The language server is the program that does the checking. It must run in
    the environment that can import your application.

3. Tell Citry where your application is, with the `citry.app` setting
   described [below](#connect-your-app).

The status bar then shows whether Citry is working:

| Status bar | Meaning |
| --- | --- |
| **Citry** with a check mark | Citry loaded your application. Everything works. |
| **Citry: syntax only** | Citry checks template syntax, but does not know your components. See [troubleshooting](#syntax-only). |
| **Citry unavailable** | The language server did not start. See [troubleshooting](#citry-unavailable). |

Click it, or run **Citry: Show Language Server Status**, to see the Python
interpreter, application, and Citry version in use.

The extension needs desktop VS Code 1.101 or newer, or a compatible fork. It
also works in remote workspaces, but not in VS Code for the Web.

## Connect your app

Set `citry.app` in your workspace settings to the `module:attribute` path of
your [`Citry`][citry.Citry] instance:

```json
{
  "citry.app": "myproject.app:citry_app"
}
```

Citry imports that instance to learn which components you registered. With
it, Citry can complete your components, check their inputs and slots, and
take you to their definitions. Without it, Citry only checks template syntax
and explains built-in tags such as `<c-if>`.

To work on a component library without a host application, point `citry.app`
at the library's [`ComponentLibrary`][citry.ComponentLibrary] instead:

```json
{
  "citry.app": "citry_ui:__citry_library__"
}
```

Citry then knows the built-in components and that library only. If the
library needs an extension that the host application installs, point
`citry.app` at a `Citry` instance that installs it.

### Load an env file

If importing your application needs environment variables, point
`citry.envFile` to a dotenv file:

```json
{
  "citry.app": "myproject.app:citry_app",
  "citry.envFile": "${workspaceFolder}/.env"
}
```

For Django, include the settings the import needs. Citry imports the module
directly and does not run `manage.py`:

```ini
DJANGO_SETTINGS_MODULE=myproject.settings
DJANGO_SECRET_KEY=editor-development-secret
```

Citry uses these variables only while it imports your application. They do
not change your terminal, tests, or application server. Saving, creating, or
deleting the file reloads your components. If the file is missing or invalid,
Citry checks syntax only, and **Citry: Show Language Server Status** says
why.

### Pick the interpreter

The extension uses the interpreter you selected in Microsoft's Python
extension. When that extension is not installed, or you want a different
interpreter, set `citry.python`:

```json
{
  "citry.python": "/path/to/project/.venv/bin/python"
}
```

`${workspaceFolder}` works in this path.

## Settings

| Setting | What it does | Default |
| --- | --- | --- |
| `citry.app` | Your `Citry` instance or `ComponentLibrary`, as `module:attribute` | Empty: syntax checks only |
| `citry.envFile` | A dotenv file to load before importing `citry.app`. Relative paths start at the workspace folder | Empty |
| `citry.python` | The Python executable that runs `citry-lsp` | Empty: the Python extension's interpreter |
| `citry.typeCheck` | Report [TypeScript errors](#typescript-errors-in-component-javascript-and-templates) in component JavaScript and templates | `true` |
| `citry.trace.server` | Log messages between VS Code and the language server: `off`, `messages`, or `verbose` | `off` |
| `citry.trace.performance` | Write timings for completion, hover, and go to definition to the **Citry Performance** output channel | `false` |

Which template mistakes are errors or warnings is not an editor setting. Your
application sets it, and `citry check` uses the same rules. See
[Template linting](/ide/template-linting/).

## Troubleshooting

### "Citry unavailable" { #citry-unavailable }

The language server could not start. Run **Citry: Show Language Server
Status** for the reason, then check:

- `citry-lsp` is installed in the interpreter Citry uses. A notification
  names that interpreter and the command to install it.
- `citry.python`, if set, points to a Python executable.
- Your `citry-lsp` version works with your extension version. Upgrade both if
  the status names a version problem.

### "Syntax only" { #syntax-only }

Citry is running but has not loaded your application, so it does not know
your components. Either:

- `citry.app` is not set. Set it as shown
  [above](#connect-your-app).
- Importing `citry.app` failed. **Citry: Show Language Server Status** shows
  the error. A common cause is a missing environment variable; see
  [`citry.envFile`](#load-an-env-file).

### Template file ignored

The extension does not claim `.html` files, because Citry accepts any file
name in `template_file`. Associate your template files with the Citry
Template language:

```json
{
  "files.associations": {
    "templates/components/**/*.html": "citry-html"
  }
}
```

### Stale results

Citry reads open Python files as you type, so most edits update at once. When
a component or its template is chosen by code, for example by a factory or
an imported constant, save the file and run **Citry: Restart Language
Server**.

### `{` adds an f-string

Pylance can add an `f` prefix when you type `{` in a Python string. Its
`python.analysis.autoFormatStrings` setting is off by default. If you turned
it on, turn it off for the workspace:

```json
{
  "python.analysis.autoFormatStrings": false
}
```

The setting applies to every Python file in the window; Pylance has no
per-string exception.

### Report a bug

Include the Citry extension version, the `citry-lsp` version, the VS Code
version, your operating system, and the output of **Citry: Show Language
Server Status**. For a log of what the editor and server exchanged, set
`citry.trace.server` to `messages` or `verbose`. Remove secrets and private
paths before posting.

## Template variables { #complete-template-roots }

In a component's template, Citry completes and documents the variables the
template can use: fields of your `TemplateData` class, keys that
`template_data()` returns, `Kwargs` fields, `template_globals`, and names you
declared for [linting](/ide/template-linting/). This works in `{{ ... }}`
and in `c-*` attributes.

- **Hover** shows the variable's type.
- **Go to Definition** opens the field or the returned dict key.
- **Go to Declaration** opens where the name is written: the field, the dict
  key, or the `c-for` or `c-fill` that introduces it.
- **Go to Type Definition** opens the Python class of the value.
- **Find All References** lists the uses of the variable in that template.

Once Citry knows a variable's type, you also get completion of its members,
signature help for calls, and type errors, inside expressions, loops, and
nested templates. A `c-if` narrows an optional type, as in Python.

These updates follow your edits in open Python files without saving.

## Look up Citry syntax

Hover a Citry tag, such as `<c-slot>`, or a Citry attribute, such as
`c-bind`, `#c-key`, or `required`, to see a short explanation and a link to
its full guide. This works without `citry.app`. A `c-*` attribute that sets
an HTML attribute, such as `c-class`, shows the HTML help for that
attribute.

HTML help also works inside a nested template, the markup you write in an
attribute value between `<>` and `</>`. Use single quotes for attributes
inside a double-quoted value:

```citry-html
<c-card c-body="<><input type='email' autocomplete='email' /></>" />
```

For `<c-element>`, a literal tag such as `is="form"` gets the attribute help
for `<form>`. With a dynamic `c-is` or `c-bind`, only global HTML attributes
are offered, because the final tag is not known.

## Check component inputs

A `c-*` value on a component tag is a Python keyword argument, so Citry checks
it against the child's `Kwargs` annotation. A wrong value shows a
`citry.python.invalid-assignment` error that names both types:

```citry-html
{# TaskCard declares `task: Task` #}
<c-TaskCard c-task="1" />
```

A static attribute on a component tag passes its text as a string, so it is
checked the same way:

```citry-html
{# TaskCard declares `size: Literal["sm", "md", "lg"]` #}
<c-TaskCard size="xl" />
```

On HTML elements, `c-class` and `c-style` are checked too. They take a
string, a dict, a list or tuple of those, or `None`, so `c-class="1"` is an
error.

The check follows the annotation, not runtime validation. A Pydantic `Kwargs`
field that converts `"1"` to `1` at runtime still reports a string passed to
an `int`.

## Vue and component JS { #complete-vue-expressions-and-component-javascript }

In a component's template, Vue expressions know the data the component sends
to the browser:

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

`JsData` names complete in Vue directives and bindings. Hover shows their
JavaScript type, and **Go to Definition**, **Go to Declaration**, and **Find
All References** connect them to the Python field or `js_data()` key. Fields
of the component's `State` work the same way through `$state`.

Hovering `$component`, a callback value, or a helper such as `$sendEvent`,
`$loading`, or `$error` shows what it does and links to its
[browser API reference](/reference/browser-apis/). Inside `sendEvent`,
`$sendEvent`, `$loading`, and `$error`, Citry completes your server event
handler names. A literal handler name, and the name in an `@c-*` binding,
must match a handler on the component, and go to definition opens that
Python method. Names computed at runtime, and names in `onEvent()` and
`$onEvent()`, are not checked.

VS Code's own JavaScript, HTML, and CSS help keeps working alongside Citry.

### Types of `js_data()`

Citry works out the JavaScript type of each `js_data()` value from your
Python code:

```citry
class TaskCard(Component):
    class Kwargs:
        task: Task  # a dataclass with `lane: str`

    def js_data(self, kwargs, slots):
        return {"laneKey": kwargs.task.lane}
```

Here `this.laneKey` is a `string`. Citry follows attributes through
dataclasses, NamedTuples, Pydantic models, and annotated classes.

- A `Literal["sm", "md"]` field, or a type alias of it, stays `"sm" | "md"`.
  An `Enum` member's `.value` is the union of its values.
- A constant you write in `js_data()`, such as `False`, keeps only its kind,
  `boolean`, because browser code may change it later.
- A NamedTuple becomes an array, and a TypedDict an object.
- A value read through an optional, such as `reviewer: Owner | None`, is
  `any`.

For other values, such as a method call or a list comprehension, the editor
asks ty, the Python type checker Citry runs:

```citry
class TaskList(Component):
    def labels(self) -> list[str]:
        return ["todo", "done"]

    def js_data(self, kwargs, slots):
        return {
            "labels": self.labels(),
            "upper": [label.upper() for label in self.labels()],
        }
```

Both `this.labels` and `this.upper` are `string[]`. These types can take a
moment to appear after you open or save a file. A value that ty types as a
class or as `Any`, or cannot type, stays `any`.

Returning a whole class instance, such as `kwargs.task`, is a
[`citry.js-data.unsupported-type`](/ide/diagnostics/#citry.js-data.unsupported-type)
warning, because the value may not survive the trip to the browser as JSON.

### Members of `this`

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

Hovering `this.count`, or `count` in the template, shows `number`, and **Go
to Definition** from either opens the `count` key in `data()`. From
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
handlers, lifecycle hooks such as `mounted()`, and `provide()`. The
`component` value in `onServerRender` or `init` gets it too. Citry's
helpers, such as `$sendEvent`, `$loading`, and `$state`, and Vue's `$el`,
`$refs`, and `$emit` are included.

Reading a member the component does not define is an error; see
[`citry.component-js.unknown-member`](/ide/diagnostics/#citry.component-js.unknown-member).

### `$el`, `$state`, `$emit`

`$el` takes its type from the first node of the component's template:

| Template root | Type of `$el` |
| --- | --- |
| One element, such as `<button>` | That element's type, such as `HTMLButtonElement`. `<svg>` is `SVGSVGElement` |
| `v-if` and `v-else`, or `c-if` and `c-else` | Each branch's type joined with `\|`, plus `Comment` when there is no else branch |
| A child component tag, such as `<c-Lane>` | The child's own `$el` type |
| Text only | `Text` |
| Several nodes, `v-for`, `c-for`, a slot, or a template the editor cannot read | `Node` |

With several root nodes, Vue sets `$el` to an empty marker node, not to the
first element, so use `$refs` or the `els` value in `onServerRender`
instead. `$el` is `null` until the component
mounts, for example in `data()` or `created()`, although its type does not
say so, as in Vue's own types.

`$state` is Citry's [Events State](/reference/browser-apis/#state) for the
component, not Vue's `data()`. Its fields come from the component's `State`
class. Every public field can be assigned, unless `State` sets `_model`; then
only the fields it lists can be.

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

- The array form, such as `emits: ['drop-task']`, allows only the listed
  names, with any values.
- In the object form, the validator's parameters type the values. A `null`
  validator accepts any values.
- Without `emits`, `$emit` accepts any name, as in Vue.

Completion inside `this.$emit('')` offers the declared names. In a parent
template, a listener on the child's tag gets the same types:
`@drop-task="move($event)"` on `<c-Lane>` types `$event` as the payload.
The parameters of an inline function, such as
`@drop-task="(payload) => move(payload)"`, get the same type, and so does
`$event` in an `@c-drop-task` binding on that tag.

On an HTML element, `$event` is the DOM event, such as `KeyboardEvent` for
`@keydown`. A name the DOM does not define, such as `@board:notice`, is a
`CustomEvent`, so `$event.detail` works.

### Emitted event names

When `emits` is an array of strings or an object with plain keys, Citry
checks event names in the editor and in `citry check`:

- Emitting a name that `emits` does not list is an error:
  [`citry.browser.undeclared-emit`](/ide/diagnostics/#citry.browser.undeclared-emit).
- Listening on a child component for a name the child does not declare is a
  warning:
  [`citry.browser.undeclared-component-event`](/ide/diagnostics/#citry.browser.undeclared-component-event).

A prop named `on<Event>`, such as `onPing` for `ping`, also declares the
event, as in Vue.

### Child component props

When a child component declares `props` in `$component({ props })`, Citry
checks the props you pass on its tag. It reports an unknown prop, a missing
required prop, and a value whose type the prop does not accept. Hover and go
to definition on a prop open its declaration. With a `v-bind` spread on the
tag, Citry does not report missing props. A component chosen at runtime is
not checked.

## TypeScript errors { #typescript-errors-in-component-javascript-and-templates }

The editor reports TypeScript's errors in component JavaScript and in Vue
expressions, on the line you wrote, whether the code is in a `.js` file, a
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

Each commented line, and `startDrag('first')` in the template, shows an error
with a code such as `citry.typescript.ts2322`, where the number is
TypeScript's own.

| Mistake | Example | TypeScript codes |
| --- | --- | --- |
| A value of the wrong type | `this.clearDropTarget = true` | 2322, 2345, 2769, and related |
| A member that does not exist | `this.$el.fooBar` | 2339, 2551, 2353, 2561 |
| The wrong number of arguments | `this.startDrag(1, 2)` | 2554, 2555, 2556, 2575 |
| A syntax error in JavaScript inside a Python string | `const = 1` | 1000 to 1999 |
| A bound HTML attribute value of the wrong type | `:style="1"` | 2345 |

A bound attribute on an HTML element is checked against Vue's types for that
attribute, so `:style="1"` is an error while `:style="{ color: 'red' }"`
passes.

VS Code's built-in TypeScript runs the check, so you do not need Node.js, but
the built-in **TypeScript and JavaScript Language Features** extension must be
enabled. If it does not answer, the **Citry** output channel says so once.
These errors can appear a moment after Citry's own.

To turn them off, set `citry.typeCheck` to `false`. To run the same check in a
terminal or CI, use
[`citry check --types`](/cli/#check-types-with-typescript-and-ty).

### `aria-*`, `id`, `title`

Vue types `aria-*` attributes. `aria-expanded` takes a boolean or
`'true'`/`'false'`, so `:aria-expanded="String(open)"` is an error, because
`String()` returns any string. Bind the boolean itself:
`:aria-expanded="open"`.

Vue types `id` and `title` as strings, so `:id="task.id"` is an error when
the id is a number. Bind `:id="String(task.id)"`.

### Errors left out

- **Mistakes Citry already reports.** An unknown name inside `$component`, an
  unknown member such as `this.startDargg()`, or an undeclared event name
  shows only Citry's own diagnostic. An unknown name in a template follows
  [`citry.vue.unknown-variable`](/ide/diagnostics/#citry.vue.unknown-variable)
  and your lint settings.
- **Values Citry cannot type.** An injection, a server event's result, or a
  `JsData` field that cannot be sent as JSON is `any`, so reading it is never
  an error.
- **Strict-mode errors.** TypeScript's strict mode is off, so a `data()`
  value that starts as `null` can take any value later, and an implicit
  `any` is not reported.
- **Queries by CSS selector.** `this.$el.querySelector('#name')` returns
  `any`, because the selector does not say which element it finds. A query
  by tag name, such as `querySelector('input')`, keeps the tag's type.
- **Unknown `window` members.** A member such as `window.htmx` is `any`,
  because a page script may add it.
- **Template event targets.** A template cannot cast, so `$event.target` and
  `$event.currentTarget` are `any`.
- **Minified files**, such as `runtime.min.js`, are not checked.

## Format Citry code

Two commands in the command palette format a Python component's strings:

- **Citry: Format Document** formats every `template`, `js`, and `css`
  string in the current Python file.
- **Citry: Format at Cursor** formats only the string under the cursor.

Formatting lays out the template's HTML structure and formats the JavaScript
and CSS, while keeping the Python triple-quoted strings readable:

<c-image src="https://raw.githubusercontent.com/citry-dev/citry/main/packages/editors/vscode/images/formatting.gif" alt="Citry formatting an inline template, JavaScript, and CSS inside a Python component" width="960" />

Your Python formatter keeps formatting the rest of the file. To run Citry's
formatter whenever you save a Python file, add it as a save action:

```json
{
  "[python]": {
    "editor.codeActionsOnSave": {
      "source.format.citry": "explicit"
    }
  }
}
```

A standalone Citry template is formatted as a whole. The two Citry commands
also format an `.html` file that your application uses as a
`template_file`. Make Citry its default
formatter to use VS Code's **Format Document** and format on save:

```json
{
  "[citry-html]": {
    "editor.defaultFormatter": "citry-dev.citry",
    "editor.formatOnSave": true
  }
}
```

For JavaScript and CSS, Citry uses
[Prettier for VS Code](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)
when it is installed and selected for that language, so your Prettier
configuration applies. Otherwise it uses its own copy of Prettier 3.9.6 with
two-space indentation.

The template formatting matches `citry format` on the command line. The
JavaScript and CSS output matches only when both use the same formatter,
version, and options; `citry format` uses Biome. See
[Command line](/cli/#format-component-files).

### What stays unchanged

- `messages` strings and `.ftl` files. Citry colors Fluent but does not
  format it.
- A `<script>` or `<style>` that contains Citry interpolation, such as
  `{{ title }}`.
- Code where moving text would change its meaning, such as multiline
  strings and comments whose whitespace matters, a hashbang, `@charset`, or
  a byte order mark.
- Anything outside a `template`, `js`, or `css` string, such as a
  `template_file` path or a `template_data()` method. The command refuses
  and makes no edits. Open the file itself to format it, or use
  `citry format`.

## CSS variables

Citry connects a `var(--name)` in a component's CSS to the Python data that
sets it:

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

Inside `var(--...)`, completion offers the `CssData` names. Hover shows where
the value comes from, **Go to Definition** opens the Python field, and **Find
All References** lists the uses in that stylesheet. Keys that `css_data()`
returns work too, so `{"row-color": value}` is available as `--row-color`.
This works in `css` strings and in `css_file` files.

Citry does not report an unknown `var(--name)`. The value may come from a
parent element, a theme, or another stylesheet.

## i18n messages

When your application uses [i18n](/i18n/), Citry connects message IDs across
Python, templates, Fluent files, Vue expressions, and component JavaScript.
This needs `citry.app`.

- **Message IDs** complete and navigate in `tr()`, `self.i18n.tr()`,
  `<c-trans message="...">`, `$c-tr`, `Component.I18n.client_messages`,
  `$i18n.tr()`, and `i18n.bind()`. Go to definition opens the message, even
  when it lives in another component or a catalog package.
- **Hover** on a message shows its text, its parameters with their types
  and descriptions, and where it is defined.
- **Arguments**, such as `count` in `tr("account-unread", count=value)`, show
  their `@param` type on hover, and go to definition opens the `@param` line.
- **Formatter and parser profiles** complete in calls such as
  `fmt.number(..., format="...")` and `$i18n.format.currency(...)`.

The editor reports an unknown message ID or profile, a missing, extra, or
mistyped argument, a misspelled `fmt` method, and invalid Fluent, using the
same checks as `citry check`. It also reports a malformed `$c-tr` name, such
as `$c-tr:` or `$c-tr:notice[]`. A message ID or argument computed at runtime
is not checked. Fluent coloring works without `citry.app`.

## Less common cases

### Shared templates

When several components use the same template file, Citry offers only what
is true for all of them. A name that one of them does not define gets no
completion or type, though **Go to Definition** still lists each component's
declaration. A CSS file shared by several components completes only the
`var(--name)` names that all of them supply.

### Templates set by code

Citry follows edits to `template` and `template_file` live when the value is
a string or a `pathlib.Path(...)`. When the template is chosen by an imported
constant, a factory, a decorator, or a metaclass, Citry uses the components
it loaded at startup, and withholds go to definition for variables until you
save and restart the language server.

### Union-typed `c-*` values

If ty reports `str | int` for a row's `size` that only ever holds a string,
the row is probably a dict nested inside the dict `template_data()` returns.
ty types each top-level key on its own, but merges the values of a nested
dict into one union:

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

Give the row its own type. A `TypedDict` keeps the value a plain dict, so the
template does not change:

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

A value from a function typed `-> str` is `str`, not one of the input's
choices. Annotate the function with the `Literal` type it really returns, or
use `typing.cast()` after code that has checked the value.

### Unchecked `c-*` values

An attribute without a value, such as `<c-TaskCard compact>`, passes `True`
and is not checked. Neither is an unquoted value, or a value with a
backslash or a line break. A missing or unknown input is reported by the
template's input checks instead.

### Bound attribute values

A keyword the HTML Standard lists for an attribute, such as the empty value
in `:translate="''"`, is accepted, as the
[attribute-value check](/ide/template-linting/#find-invalid-html-attribute-values)
accepts it. Vue types some attributes, such as `dir`, as any string, so a
bound `:dir="'sideways'"` is not reported, though the same static value is.
Vue's types are case-sensitive, so a bound `'LAZY'` is an error where a
static `"LAZY"` passes. A bound value that both Vue's types and the
attribute-value rule reject, such as `:draggable="'treu'"`, is reported once,
by the attribute-value rule. Attributes Vue does not declare, such as `data-id`,
attributes on custom elements, and bindings with a modifier such as `.prop`
are not checked.

### Undeclared child events

A listener for an event the child does not declare gets the DOM event of
that name as `$event`, because Vue then passes the listener to the child's
root element. When the child lists its events as an array, or Citry cannot
read its `emits`, `$event` is `any`.

### Typing inside `data()`

`this` inside `data()` has props, injections, `js_data()` keys, and Citry's
helpers, but not the `data()` result or the methods. A Vue Options section
with the wrong shape, such as a `computed` entry that is a number, can stop
computed values and methods from being typed until you fix it.

### Hover shows nothing

Citry shows nothing rather than a guess when the source does not parse, when
it cannot tell which component uses a template, or when it cannot follow a
value that `template_data()` returns.

### `$i18n` scope

`$i18n` gets completion and checks only inside a `<c-i18n>` that is enabled
for the browser. A server-only `<c-i18n>` nested inside it turns them off for
its contents.

### When ty is unavailable

The language server installs ty, the Python type checker it uses, in the same
environment. If ty cannot start or stops answering, Citry says so once and
keeps its own checks, completion, hover, and navigation for template
variables. Member types and Python type errors are missing until ty works
again.

### Other editors

Other editors that use `citry-lsp` run the TypeScript check with the `tsc`
from your project's `node_modules` or from `PATH`.

### Limits

- Coloring of deeply nested or unfinished expressions is best effort.
- Citry reports only the first syntax error in a template.
- Citry analyzes template expressions. Pylance, Pyright, or another Python
  extension still checks the rest of your Python code.
- Embedded CSS gets coloring, completion, hover, and formatting, but no
  CSS warnings, because VS Code does not share them with extensions.
- Embedded JavaScript reports the TypeScript errors listed
  [above](#typescript-errors-in-component-javascript-and-templates), not
  every JavaScript warning.
- Citry gives each JavaScript or CSS formatter 30 seconds. A result that
  arrives later is discarded.
- Coloring cannot tell whether a class with a `template`, `js`, or `css`
  assignment is a `Component`, so an unrelated class with those exact
  attribute names may get Citry coloring.
- Calls in templates, such as `tr(...)` or `fmt.currency(...)`, are colored
  as function calls even before Citry knows their types.
