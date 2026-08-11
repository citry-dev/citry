<!-- Absolute URL so the logo also renders on the Marketplace listing, which
     serves this README from outside the repository and cannot resolve a
     repo-relative path. -->
<img src="https://raw.githubusercontent.com/citry-dev/citry/main/docs/assets/citry-wordmark.png" alt="Citry" width="170">

# Citry for Visual Studio Code

This extension highlights Citry components where they are normally written:
inside the `template`, `js`, and `css` multiline string attributes of a Python
component. It also provides a `Citry Template` language mode for standalone
templates and formats those authored sections without replacing the selected
Python formatter.

The extension understands Citry component tags, dynamic attributes, template
expressions and comments, raw blocks, browser props, Events bindings, and
Alpine expressions. Its declarative highlighting continues to work in
vscode.dev. Desktop and remote extension hosts can additionally start the
`citry-lsp` process for diagnostics and editor intelligence.

## Language server setup

Install `citry-lsp` in the Python environment selected for each workspace
folder:

```console
python -m pip install citry-lsp
```

Set `citry.app` to a `module:attribute` path for either your configured `Citry`
instance or a reusable `ComponentLibrary`. Both provide registry-backed
validation, component completion, and catalog documentation:

```json
{
  "citry.app": "myproject.app:engine"
}
```

For example, a project using the standalone Citry UI catalog can select it
directly:

```json
{
  "citry.app": "citry_ui:__citry_library__"
}
```

A library target contains Citry's built-ins and that library only. It does not
include host-application components, configuration, or host-provided
extensions. Select a configured `Citry` instance when the library needs those
application facilities.

With no app setting, the status bar explicitly reports `syntax only`. This
mode still checks definite inline template regions and files explicitly using
the `Citry Template` language, completes Citry's structural tags and directive
snippets, shows first-party hover documentation for Citry tags and directives,
and understands parser-proven local names from `c-for` and `c-fill`.
Registry mode also recognizes resolved `template_file` assets from the selected
app without claiming unrelated HTML files. Syntax-only mode does not infer
unknown components or component inputs and slots. In a registry-owned
component template, declared `TemplateData` roots receive completion, hover,
and exact Python field navigation when ownership is unambiguous. Without a
declared `TemplateData`, direct dict keys inferred conservatively from
`template_data()` receive the same root assistance and follow unsaved Python
edits; the inherited `return kwargs` implementation reuses effective `Kwargs`
fields. Shared or inherited templates expose only roots proven for every
effective consumer. Proven roots also receive Python member and call
completion, type hover, user-member navigation, signature help, and mapped
diagnostics. `c-if` narrowing, `c-for` scope, nested templates, inferred
return paths, and unsaved Python edits participate. Unknown-root diagnostics
remain reserved for Citry's shared lint policy.
Unsaved template-ownership checks cover direct string and `pathlib.Path(...)`
declarations. Components that select templates through imported constants,
factories, decorators, metaclasses, or other dynamic code temporarily withhold
registry-backed variable navigation while a Python buffer is open; restart
the language server after saving to refresh that registry state.
Variable hover is rendered as a Python-highlighted declaration, such as
`(variable) method: str | None`, with its Citry source and description below.
The displayed type follows template narrowing and works for declared,
source-inferred, loop, and fill variables.
Go to References lists uses of the same proven root or exact loop/fill binding
inside that physical template. Go to Declaration targets its authored field,
dict key, or lexical introduction. Go to Type Definition targets the actual
Python class or standard-library type when every component consumer and return
path produces a safe mapped answer. Unused fill bindings target their current
neutral `Any` contract.
In direct Python component templates and Citry Template documents, root
completion does not require padding around an expression. It opens when an
identifier starts directly after `{{`, an attribute quote, or an operator, as
well as after whitespace. The extension keeps that retrigger local to Citry
expression and structural-value hosts; ordinary Python typing and text inside
expression strings or comments do not wake Citry completion.
The extension normally uses the Python extension's selected interpreter. Set
`citry.python` when an editor fork cannot provide that API or when an
environment needs an explicit executable.

Registry-owned component CSS also joins `var(--...)` references to Python CSS
data. This works in direct `css` literals and resolved `css_file` documents:

```citry
class Chart(Component):
    class CssData:
        chart_height: str

    css = """
    .chart {
        height: var(--chart_height);
    }
    """
```

Typing `var(--` completes exact `CssData` names. Hover shows the Python
producer, Definition and Declaration open its annotated field, and References
list the uses in that physical stylesheet. Direct string keys inferred from
`css_data()` work too, including a key such as `"row-color"` becoming
`--row-color`. A stylesheet shared by several components exposes only names
provided by every proven owner.

Citry does not flag other custom properties as unknown: the cascade, host page,
themes, ancestors, scripts, and external stylesheets can all provide them.
VS Code's CSS service continues to supply ordinary CSS completion, validation,
and local custom-property navigation alongside Citry's producer information.

## Complete browser data and events

In a registry-owned template, Alpine attributes such as `x-text`, `@click`,
and `:class` complete top-level values declared by `JsData` or inferred from
direct `js_data()` keys. VS Code's JavaScript service supplies ordinary member
completion and hover using Citry's JSON-derived types, while Citry links each
root to its exact Python field or returned dict key.

Component `js` and `js_file` assets receive the same data shape through the
complete `$component` callback context. This includes typed `data`, initial
`scope`, read-only `props`, Events `state`, effects, dependency helpers, and
event functions. Direct synchronous writes to `scope` become typed Alpine
names. A static `$component({ props, init })` declaration types its prop shape.
Public Events `State` fields type `$state` in Alpine and `$state` plus callback
`state` in component JavaScript.

Unknown Alpine roots are errors by default through the shared Citry lint
policy. A free name inside `$component` is also an error by default, so using
`scope` without destructuring it is reported at the authored reference.
Application and component lint settings can change either rule's severity or
declare real host-provided browser globals. Alpine `x-for` declarations receive
iterable-derived types and exact binding navigation.

Hovering `$component`, a callback context binding, or a Citry Alpine magic
shows its signature, a concise explanation, and a link to the Citry browser
API reference. Literal `sendEvent()`/`$sendEvent()` calls, declarative `@c-*`
handlers, and handler names passed to `$loading()` or `$error()` are checked
against effective Python event handlers and navigate to the matching method.
Those literal positions also complete handler names, including from an empty
string. Dynamic event names remain unchecked. `onEvent()` and `$onEvent()`
listen for open browser event names, so Citry does not restrict them.

Direct `$c-props` objects on statically resolved child components validate
unknown keys, required props, and proven value types against the child's
static `$component({props})` declaration. Hover and navigation on a key open
that JavaScript declaration. Dynamic component targets and `c-$c-props`
values remain unproven. Unsupported strict-JSON `JsData` fields receive a
warning and use `unknown` for JavaScript tooling.

## Keep template strings from becoming f-strings

Pylance can add an `f` prefix when `{` is typed in a Python string. Its
`python.analysis.autoFormatStrings` setting is off by default. If it is enabled
in your profile or workspace, keep Citry template literals unchanged with:

```json
{
  "python.analysis.autoFormatStrings": false
}
```

This setting applies to every Python file in the VS Code window. Pylance does
not provide a per-literal exception. Citry leaves typed and automated edits
alone, so a deliberate f-string is never silently reverted.

## Embedded HTML, CSS, and JavaScript

The extension reuses VS Code's built-in web-language providers inside exact
`template`, `js`, and `css` triple-string assignments. Standard HTML tags and
attributes, CSS properties, and JavaScript APIs therefore receive completion,
hover, and go-to-definition behavior without `citry.app` and without a
separate web extension. The `Citry Template` language receives the same HTML
requests, and its HTML results are combined with Citry component results when
the language server is available.

On a direct ordinary HTML start tag, dynamic native attributes keep the same
hover documentation as their static spelling. For example, hovering `c-class`
on `<form c-class="classes">` forwards to the installed HTML provider's
`class` documentation and MDN link, then highlights the complete `c-class`
name in the source. Citry control directives and component-input boundaries are
not rewritten.

Parser-proven nested templates receive the same HTML completion, hover, and
go-to-definition behavior even though the outer HTML provider would otherwise
see quoted text. Quote the inner HTML attributes with the opposite quote from
the nested-template host, for example:

```html
<c-card c-body="<><input type='email' autocomplete='email' /></>" />
```

`<c-element>` also follows its selected HTML element. A literal target such as
`<c-element is="form">` receives form-specific attributes, while a dynamic
`c-is` or `c-bind` receives only generic global-attribute assistance. Dynamic
native spellings such as `c-action` retain the underlying `action`
documentation. Invalid syntax, non-linear Python-literal mappings, unavailable
providers, and stale documents produce no forwarded result.

Provider forwarding has a bounded wait, so a stalled HTML or JavaScript
extension cannot leave Citry hover showing `Loading...` indefinitely. To
measure a slow request, enable `citry.trace.performance`, reproduce it, and
open the **Citry Performance** output channel. Each JSON line separates the
projection, virtual-document, delegated-provider, and total elapsed times.

Intelligence forwarding preserves source coordinates by replacing text outside the
selected embedded language with spaces while retaining line breaks. A missing
or failing built-in provider contributes no result and leaves Citry features
unchanged. VS Code does not expose diagnostics as a request. JavaScript and
CSS formatting uses a separate validated virtual-document round trip described
below, without registering Citry as a Python document formatter.

## Formatting

The command palette provides two formatting commands:

- **Citry: Format Document**
- **Citry: Format at Cursor**

**Citry: Format Document** formats every definite direct `template`, `js`, and
`css` literal in the current Python file, including eligible JavaScript and CSS
inside templates. **Citry: Format at Cursor** formats only the direct literal
whose body contains the cursor. A cursor on a `template_file`, `js_file`, or
`css_file` path, a method such as `template_data`, or unrelated Python code is
outside a format region and produces an explicit refusal without edits. The
commands never follow a declaration into another file; open that target and
use its document formatter, or use `citry format` for statically resolved file
assets.

A standalone Citry Template document is one authored template, so either
command formats the whole document, including eligible `<script>` and
`<style>` bodies. The explicit commands also work on an ordinary HTML-mode
file when the configured Citry registry proves that it is a resolved
`template_file`; unrelated HTML is refused. Associate a template file with
`citry-html` to get the standard formatter and format-on-save behavior below.
In Python, both commands preserve the project's selected Python formatter and
edit only definite Citry literals.

Standalone Citry Template documents use VS Code's standard formatter and
native format-on-save setting:

```json
{
  "[citry-html]": {
    "editor.defaultFormatter": "citry-dev.citry",
    "editor.formatOnSave": true
  }
}
```

Python formatting runs as an independent source action on save:

```json
{
  "[python]": {
    "editor.codeActionsOnSave": {
      "source.format.citry": "explicit"
    }
  }
}
```

Formatting uses the same structural Citry/HTML and validated Python-expression
implementation as the CLI and Python API. For expression-free `script` and
`style` bodies and direct `js` and `css` literals, the extension invokes VS
Code's public `vscode.executeFormatDocumentProvider` command on a standalone
document whose URI, language, selector, and configuration scope remain stable
while its immutable content snapshot is refreshed between passes. It validates
the returned UTF-16 edits, protected ranges, Citry delimiters, source version,
and a second idempotence pass before the language server composes one atomic
Python edit. Each provider pass is bounded
to 30 seconds; a late result is discarded and cannot edit the source file.

VS Code's public command supplies the first applicable formatter result but
does not reveal the provider identity or guarantee that it is the configured
default formatter. Citry reports this mechanism as `vscode-first-result` with
provider identity unknown. Missing or failing JavaScript and CSS formatters
leave their regions unchanged and are reported in the Citry Formatter output
channel.

The built-in CSS formatter accepts Citry's virtual documents. VS Code's
built-in JavaScript/TypeScript formatter currently does not, so JavaScript
formatting requires an installed formatter that accepts non-file virtual
documents. Prettier is the recommended compatible option. This limitation
affects formatting only; JavaScript highlighting, completion, hover, and
definitions use a separate embedded-language route. The CLI does not use
Prettier and continues to require its explicitly configured native Biome
adapter.

Install the recommended JavaScript formatter with:

```console
code --install-extension esbenp.prettier-vscode
```

Interpolated JavaScript and CSS bodies also remain unchanged until a
context-safe placeholder adapter is available. The same conservative rule
keeps bodies with whitespace-sensitive multiline language tokens or
position-sensitive hashbang, `@charset`, and BOM bytes unchanged until a
language-aware source map can preserve them exactly.

Each workspace folder keeps its own language-server process and project
configuration. When workspace folders are nested, document synchronization and
formatting are routed through the folder VS Code selects for that document.

## Standalone templates

Citry accepts any filename for `template_file`, so the extension does not claim
ordinary `.html` files. Select `Citry Template` from VS Code's language picker,
or add an association that fits your project:

```json
{
  "files.associations": {
    "templates/components/**/*.html": "citry-html"
  }
}
```

An invalid pattern or unknown language id is handled by VS Code's normal
settings validation. Files that do not match an association remain in their
existing language mode.

## Current scope

TextMate coloring of deeply nested or unfinished expressions remains best
effort. Parser diagnostics are precise and fail after the first syntax error.
The server provides schema-free structural/directive completion and linked
first-party syntax hover; lexical
loop/fill completion, hover, and navigation; registry component, input, and
slot completion; catalog hover; typed slot-data completion and hover; precise
component-class navigation with safe file fallback; exact component-input and
static fill-slot navigation when authoring provenance is unambiguous; and
document symbols. It
deliberately leaves Python analysis to Pylance or Pyright. The VS Code client,
not the Citry server, delegates embedded HTML, CSS, and JavaScript requests to
the providers already installed in VS Code.

The Python injection keys on the exact `template`, `js`, and `css` assignment
names. A TextMate grammar cannot prove that the surrounding class inherits
from `Component`, so an unrelated multiline assignment with one of those names
receives the same highlighting. Other assignment names remain ordinary Python
strings.

## Development

From the Citry repository root:

```console
pnpm install
pnpm --dir packages/editors/vscode run check
pnpm --dir packages/editors/vscode run package
```

The package command writes `dist/citry.vsix`. Install it locally with:

```console
code --install-extension packages/editors/vscode/dist/citry.vsix --force
```

The grammar adapter consumes the shared behavior cases in
`packages/editors/syntax-fixtures/`. The Pygments and future browser-editor
adapters consume the same cases with their own native token vocabulary.

### What `engines.vscode` decides

`package.json` takes no comments, so the reasoning lives here. `engines.vscode`
declares the oldest VS Code this extension supports, and three other values
follow from it. They move together, in one change, and never on their own:

| Value | Today | Why |
|---|---|---|
| `engines.vscode` | `^1.101.0` | the decision |
| `@types/vscode` | `1.101.0` | matches the floor exactly |
| esbuild `--target` | `node22` | VS Code 1.101 embeds Node 22.15.1 |
| `@types/node` | `22.x` | describes that same embedded Node |

Each one breaks differently if set on its own. A newer **`@types/vscode`** lets
code compile against editor APIs that are absent at run time on the oldest
supported version, so the extension fails only for the users still on it. A
newer **esbuild target** lets esbuild emit syntax the embedded Node cannot run,
and skip the downleveling that would have made it safe. A newer **`@types/node`**
describes APIs that embedded Node does not provide.

The embedded Node comes from the editor, not from Node's own release schedule,
so a Node version reaching end of life is not by itself a reason to raise the
target. Look up what a given VS Code release embeds at
[ewanharris/vscode-versions](https://github.com/ewanharris/vscode-versions), and
pick the floor from the oldest editor you intend to support.

Dependabot proposes the two type packages regularly;
`.github/dependabot.yml` ignores them so the decision is made here rather than
re-argued weekly.

For an M3 smoke test, use a workspace whose selected Python interpreter has
the local `citry` and `citry-lsp` builds installed. Open a component with a
direct `js` or `css` triple-string, or an expression-free `<script>` or
`<style>` body in its template, then run **Citry: Format Document**. The Citry
Formatter output channel shows each region's status and the `vscode-first-result`
mechanism. The built-in CSS provider covers CSS. Install Prettier, or another
JavaScript formatter that supports non-file virtual documents, to exercise the
JavaScript path; the built-in JavaScript/TypeScript formatter does not accept
Citry's custom URI. This manual check confirms which providers installed in
the Extension Host accept that URI.

## License

MIT
