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

Set `citry.app` to your `module:attribute` Citry instance for registry-backed
validation, component completion, and catalog documentation:

```json
{
  "citry.app": "myproject.app:engine"
}
```

With no app setting, the status bar explicitly reports `syntax only`. This
mode still checks definite inline template regions and files explicitly using
the `Citry Template` language, completes Citry's structural tags and directive
snippets, and understands parser-proven local names from `c-for` and `c-fill`.
Registry mode also recognizes resolved `template_file` assets from the selected
app without claiming unrelated HTML files. Syntax-only mode does not infer
unknown components or component inputs and slots. In a registry-owned
component template, declared `TemplateData` roots receive completion, hover,
and exact Python field navigation when ownership is unambiguous. Shared or
inherited templates expose only the fields common to every effective consumer;
member inference and unknown-root diagnostics remain deliberately conservative.
The extension normally uses the Python extension's selected interpreter. Set
`citry.python` when an editor fork cannot provide that API or when an
environment needs an explicit executable.

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
name in the source. Citry control directives and `c-*` component tags are not
rewritten. Nested templates stored inside attribute values and `<c-element>`
target attributes are deliberately deferred until their target and source maps
can be proven.

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
The server provides schema-free structural/directive completion; lexical
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
