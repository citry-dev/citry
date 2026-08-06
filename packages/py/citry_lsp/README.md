# Citry language server

`citry-lsp` provides parser diagnostics, component-aware completion and hover,
lexical template navigation, precise component navigation, document symbols,
and formatting for Citry templates. Component completion offers both
registered tag spellings and a valid class-name spelling such as `c-CButton`,
with the typed prefix deciding which form ranks first.

Even without an app, completion offers Citry's structural tags and
host-specific directive snippets. Parser-proven `c-for` and `c-fill` bindings
complete and hover inside their lexical scope, including shorthand loops,
destructured or aliased slot data, fallback names, and nested template values.
Structural start-tag completion adds the primary syntax and places the cursor
in its value, for example `<c-for each="">` and `<c-if cond="">`; closing tags
remain bare names. These schema-free features do not claim that any user
component exists.

Install it in the same Python environment as the Citry project for registry
knowledge. The first release requires Citry 0.3.2 or newer in the 0.3 series:

```console
python -m pip install citry-lsp
citry-lsp
```

The editor supplies an optional `module:attribute` app spec during LSP
initialization. With no app configured, the server runs in reported
`syntax-only` mode. It still validates definite inline component templates and
documents explicitly assigned the `citry-html` language, but it does not infer
unknown components or component contracts.

Registry mode also describes the data exposed by typed slots. Completion
inside a direct fill binding such as `data="{ row, ... }"` offers the remaining
fields, while slot and component hover show the complete known field set.
Inside a proven component template, expression completion also offers the
declared `TemplateData` roots from an empty expression through partial typing.
This applies to interpolations and Python-valued attributes. Hover and
go-to-definition on an exact free root link back to its annotated Python field.
If a physical template is inherited or shared, the server exposes only
identical field contracts present on every registered consumer. A common
contract may still complete and hover when its consumers authored separate
declarations, but go-to-definition is withheld in that case. Ambiguous
ownership or schemas produce no guess. Catalog v1 does not carry a recursive
type graph, so `user` can link to `TemplateData.user` while members such as
`user.name` remain ordinary Python-expression text and do not receive root
completion.

The server does not diagnose unknown expression roots from `TemplateData`.
Engine-level and per-render template globals, arbitrary `template_data()`
extras, and extensions may all add names outside that schema, so the available
namespace is not closed.

Component definitions use the catalog's loaded Python file and qualified class
name to select an unambiguous class definition. Component input attributes and
static fill slot names use per-field authoring provenance to select an exact
annotated field. A generated, local, duplicate, unreadable, invalid, or
otherwise ambiguous field produces no definition target. Open Python files are
joined against synchronized editor text; closed files are joined against the
current on-disk AST. Catalog v1 does not fingerprint an authored source
generation, so a different valid on-disk class with the same qualified name
and field remains a structural match. Component-tag navigation keeps its
existing safe file fallback.

The server imports configured project code in a bounded worker subprocess.
Project output, `SystemExit`, hangs, and crashes cannot corrupt the LSP stdio
transport. Each workspace folder needs its own server process so its Python
interpreter and app selection remain independent.

The console command also accepts pygls transport options such as `--tcp` for
development. With no transport flag it uses stdio, which is the production
editor integration mode.

## Formatting

Protocol v1 dynamically registers standard document formatting only for the
`citry-html` language beneath that server's workspace root. This keeps
independent servers correctly routed in a multi-root editor, including a
workspace opened through a symlink. Python keeps its selected Python formatter
and uses the versioned `citry/formatTemplates` request for either every definite
inline template or the template containing one cursor position. Both routes
format the current synchronized text, reject stale document versions, and
return no edit when formatting is refused.

Custom document-scope requests also accept an `html` document when the loaded
registry proves that its URI is a resolved `template_file`. Unrelated HTML
remains ineligible, and standard formatting is still registered only for
`citry-html`.

Clients that need to own formatter routing can set the protocol v1
`standardFormatting` initialization option to `false` and use the custom
request. The option defaults to `true`; diagnostics and other language features
are unchanged when it is disabled.

The formatter applies the shared structural Citry/HTML policy, the built-in
Python expression and `c-for` provider, and Citry's `c-fill data` layout. The
active Python provider identity is included in additive project status; the
protocol remains version 1.

Clients may additionally advertise this protocol-v1 initialization option:

```json
{
  "embeddedFormatting": {
    "version": 1,
    "languages": ["javascript", "css"],
    "providerSelection": "vscode-first-result"
  }
}
```

The `citry/formatComponentAssets` request uses the same document or position
scope as `citry/formatTemplates`, but includes proven direct `js` and `css`
literals. During that request, the server sends immutable virtual documents
through `citry/formatEmbedded`. It accepts results only when the document
version, plan, region identities, cardinality, delimiter constraints, and final
Citry or Python parse all remain valid. A stale or malformed response produces
no edit.

`vscode-first-result` names the public editor selection mechanism. It does not
identify the formatter extension that supplied a result. Project status and
format responses therefore leave provider identity and version unset unless a
future client can prove them. Clients without this capability still receive
Citry structure and Python-expression formatting; JavaScript and CSS remain
unchanged and are returned as explicit notices.

For an isolated syntax-only process that cannot import the project registry:

```console
uvx --from citry-lsp citry-lsp
```
