# Citry language server

`citry-lsp` brings Citry template diagnostics, completion, hover, navigation,
symbols, references, and formatting to editors that support the Language Server
Protocol.

It understands templates written inside Python, standalone `citry-html`
documents, and template files owned by registered components. It can work
without loading an app, while a project-aware installation also understands
your registered components and their Python declarations.

## Install in your project

Install the server in the same Python environment as the Citry project:

```console
python -m pip install citry-lsp
```

The 0.1.x server supports Citry 0.4.x and Python 3.10 through 3.14. It installs
the compatible Citry runtime, pygls, and the supported `ty` analyzer
automatically.

Your editor should launch this command over stdio:

```console
citry-lsp
```

For an isolated syntax-only process, use:

```console
uvx --from citry-lsp citry-lsp
```

The isolated form cannot import the project app, so it deliberately omits
registry-backed component knowledge.

## Choose how much project knowledge to load

Without a project target, the server reports `syntax-only` mode. Parser
diagnostics, Citry structural completion, lexical `c-for` and `c-fill`
bindings, Citry event/State binding keys and modifiers, Alpine directive
completion and hover, first-party hover help, and structural formatting remain
available.
The server does not guess which user components exist.

For component-aware features, the editor supplies a `module:attribute` target
through its `citry.app` setting:

```json
{
  "citry.app": "my_project.web:app"
}
```

The target may be a configured `Citry` instance or a `ComponentLibrary`:

```json
{
  "citry.app": "citry_ui:__citry_library__"
}
```

The server imports that target in a bounded worker process. Import errors,
invalid targets, crashes, and timeouts produce one visible status message and
fall back to syntax-only behavior without corrupting the editor connection.

Clients may also provide an optional `envFile` initialization option. Relative
paths resolve from the workspace:

```json
{
  "protocolVersion": 1,
  "app": "my_project.web:app",
  "envFile": ".env"
}
```

File values override the environment inherited by the server and apply only
to the isolated app-discovery worker. The stdio server and its type analyzer
remain unchanged. Each registry reload rereads the file; missing or malformed
configured files produce a syntax-only status instead of importing the app
with an unintended environment. Citry's environment adapter reports the
selected path but never serializes or logs its parsed values.

Registry mode adds:

- component, input, slot, and typed slot-data completion and hover;
- navigation to component classes, schema fields, inferred data keys, and
  template bindings;
- `TemplateData`, `JsData`, and `CssData` checks across Python, templates,
  Alpine expressions, JavaScript, and CSS;
- Events handler and `$c-props` checks;
- Fluent message, key, argument, formatter, and translation navigation;
- project lint settings and component-aware diagnostics.

Each workspace folder should run its own server process so it can use that
folder's Python interpreter and registry target.

## Type-aware template expressions

The server uses the `ty` executable installed in the selected project
environment. Proven template roots receive Python member and call completion,
hover, definitions, signature help, narrowing, and source-mapped diagnostics.

If `ty` is missing, has the wrong version, exits, or times out, the server shows
one degradation notice and keeps parser diagnostics and Citry-owned root
features active.

## Formatting

Protocol v1 formats `citry-html` documents and parser-proven templates inside
Python through Citry's shared structural formatter. Registry-proven ordinary
HTML template files can be formatted through the explicit Citry request without
registering Citry as the formatter for every HTML document.

Clients may also negotiate `citry/formatComponentAssets` and
`citry/formatEmbedded` for one atomic template, JavaScript, and CSS formatting
operation. Stale or malformed client responses produce no edit.

## Compatibility

The server advertises language-server version 0.1.3, Citry 0.4.x, component
catalog v1, and client protocol v1. It refuses incompatible client protocols or
Citry series instead of returning results based on a contract it does not
understand.

The console command accepts pygls development transports:

```console
citry-lsp --tcp --host 127.0.0.1 --port 2087
```

Use stdio for normal editor integration.

For editor setup and troubleshooting, see the
[Citry IDE guide](https://citry.dev/ide/vscode/). Report problems through the
[Citry issue tracker](https://github.com/citry-dev/citry/issues).
