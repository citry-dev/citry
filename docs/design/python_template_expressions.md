# Type-aware Python template expressions

Status: implemented on 2026-08-08.

This design gives Citry templates ordinary Python type intelligence without
turning Citry into a second Python type checker. Citry describes where template
expressions came from and how template scopes behave. A real Python analyzer
then resolves types, members, calls, aliases, unions, and narrowing.

## Prior art

The implementation starts from these existing contracts:

- `citry.analysis` discovers inline Python templates and maps parser UTF-8
  offsets back to authored UTF-16 editor positions.
- `citry._template_data_source` proves returned mapping keys and retains their
  key and value-expression ranges without executing `template_data()`.
- `citry_lsp.project.SourceAnalysisIndex` copies a statically validated class
  resolution chain from the isolated app worker.
- `citry_lsp.engine` already joins roots across every proven consumer of a
  physical template and models lexical `c-for` and `c-fill` bindings.
- `python_safe_eval` remains authoritative for the executable expression
  language and its sandbox restrictions.
- Vendored Ruff 0.16.2 provides Ruff's parser to Citry's Rust crates. That
  parser does not infer Python types. Ruff's type inference belongs to `ty`.

The catalog's `type_display` values are presentation text. They deliberately do
not resolve aliases, forward references, imports, or local scopes, so this
implementation never parses them back into a type system.

## Analyzer boundary

Citry runs the published `ty==0.0.71` language server as one child process per
Citry workspace. It communicates through the documented Language Server
Protocol surface and converts the returned completion, hover, definition,
signature, and diagnostic records into Citry-owned results.

The executable must come from the selected interpreter's scripts directory and
its installed package version must match the exact supported version. Citry
does not select an arbitrary executable from `PATH`. The `citry` package owns
the exact optional `analysis-ty` dependency, and `citry-lsp` requests that
extra so editor installations always include it. Ordinary Citry runtime
installations and `citry_core` wheels do not carry the analyzer.

Citry also passes the running interpreter's `sys.prefix` as ty's explicit
`environment.python` setting. Module resolution therefore follows the same
interpreter selected for citry-lsp even when it lives outside the workspace and
`VIRTUAL_ENV` is absent.

The child owns Ruff's incremental database. Ruff database objects, internal
type enums, rendered `reveal_type` output, and unpublished Rust crate APIs do
not cross the process boundary. The standard LSP records are the structured
adapter. Citry additionally validates that every returned edit or range belongs
to an authored expression before exposing it.

If the child is unavailable, crashes, times out, or returns an invalid response,
Citry keeps parser diagnostics, root completion, hover, and navigation. It
reports the analyzer degradation once rather than returning stale semantic
answers.

## Shadow Python document

The portable builder emits a Python document plus explicit copied ranges. The
document recreates only the facts needed to analyze template expressions:

1. Proven template roots are bound from their authored schema fields or from
   the exact returned value expressions in `template_data()`.
2. Template expressions are copied byte-for-byte into Python expression
   statements.
3. `c-if`, `c-elif`, and `c-else` become Python branch structure so narrowing
   remains inside the correct branch.
4. `c-for` clauses become comprehensions and loops so each iterable, target,
   filter, and later clause sees the same bindings as Citry.
5. Nested templates inherit their outer template environment.
6. `c-fill` variables are declared at their lexical scope. They remain unknown
   until portable slot-data types prove more.

Each copied range records the authored template byte range and generated Python
string range. The LSP adapter converts that range to UTF-16 only at the protocol
boundary. Generated imports, wrappers, helper names, and root setup have no
authored mapping. Diagnostics on those ranges are dropped.

### Declared schemas

A declared `TemplateData` schema is authoritative. The shadow document refers
to the real authored class and field through Python source, so aliases and
forward references resolve in their original module. `Kwargs` fields use the
same path for the inherited default `return kwargs` behavior.

The runtime catalog preserves that source path across Python's two annotation
models. Component construction snapshots each effective field's authored owner
while it builds the schema, including every distinct owner in a C3-composed
`TemplateData` or `Kwargs`. Python 3.14 deferred annotations use the
`ForwardRef` annotation format, so one unavailable annotation name does not
erase the field or its owner. The isolated app worker copies only the resulting
field metadata. The long-lived LSP never calls the project's deferred
annotation function. If runtime construction cannot obtain one complete
annotation snapshot, project discovery fails normally rather than publishing a
partially typed schema; if source provenance is unavailable, the corresponding
typed shadow is withheld.

### Inferred returned dictionaries

When no `TemplateData` is declared, the builder copies the current source module
and adds a renamed analysis-only copy of the exact `template_data()` method.
Every statically retained return binds the proven roots from that return value,
then evaluates the template expressions in the same method scope. Returns after
an unconditional suite terminator are removed. A return affected by a non-empty
`finally` suite conservatively disables this analysis because that suite can
replace or mutate the value before the caller observes it.
This lets `ty`
infer `kwargs.method`, local aliases, helper return types, branches, and unions
even when the method's public return annotation is only `dict[str, Any]`.

A physical template with several consumers produces one shadow query per
consumer. Member completion keeps only candidates valid for every proven
consumer. Hover reports all distinct proven types, and navigation returns all
distinct authored definitions. No result silently chooses the first consumer.

## Synchronized source

The Citry LSP forwards open Python documents to the child and opens shadow
documents as unsaved virtual files beside the source module they copy. Because
`ty` does not assign package identity to a `didOpen`-only sibling, the portable
builder also mirrors direct module imports and rewrites method-local relative
imports to their absolute spelling from proven module provenance. Relative star
imports are declined conservatively. No shadow file is written into the project.

The pinned `ty` server currently resolves imports from a virtual shadow against
disk even when the imported module also has an open `didChange` generation.
Citry therefore uses synchronized text for the copied schema or
`template_data()` owner, but withholds semantic results while any other open
Python file differs from disk. This is deliberately broader than an import
dependency scan and prevents stale imported types from reaching the editor.

Each virtual sibling keeps a stable URI for one component definition while its
LSP document version advances whenever the current module, template query, or
consumer context changes. Citry builds every request from the current project
generation and synchronized sources; it does not cache a semantic answer
outside the analyzer. The server rejects any answer when the template, a
synchronized Python document, or the project changes while a request is in
flight. A changed or conflicting source generation therefore invalidates the
input, and an invalid current template never falls back to
semantic data from the last valid parse.

## Editor behavior

The semantic provider applies inside:

- `{{ ... }}`;
- every Python-valued `c-*` attribute;
- `#c-key` and `c-$c-props`;
- structural `cond`, `each`, `c-is`, `c-name`, and `c-required` values;
- recursively nested templates.

Root-name completion and unknown-root diagnostics remain Citry-owned because
Citry knows the template namespace and application lint policy. `ty` supplies
member and call completion, hover, definition, type definition, signature help,
and diagnostics for proven roots and lexical values.

Hover for a proven root or lexical value combines both owners' information.
Citry identifies the exact variable and its provenance, while `ty` supplies
the current type after template control-flow narrowing. The editor receives a
Python-highlighted declaration such as `(variable) method: str`, followed by
the `TemplateData`, `template_data()`, `Kwargs`, loop, or fill explanation.
Shared templates retain every distinct consumer type in one displayed union;
one missing consumer or return-path answer discards the semantic type rather
than selecting a partial result. The adapter accepts only the pinned
analyzer's exact one-line Python hover block. Unexpected analyzer markup,
unavailable analysis, or an unmappable range falls back to declared catalog
type text and Citry provenance. Lexical values without a catalog still retain
the same declaration-shaped hover without a guessed type. Fill variables
currently resolve to `Any` until portable slot-data metadata carries their
Python types. Their `data` declarations retain the same provenance without a
guessed hover type, while Type Definition probes that neutral `Any` contract
directly even when a binding has no authored use.

References remain Citry-owned. They enumerate only parser-proven root uses or
uses of one exact `c-for` or `c-fill` binding inside the same physical template.
Declaration and Definition share the exact authored variable origin. Type
Definition instead asks `ty` for the underlying Python class or typeshed type
and accepts an answer only when every consumer and inferred return copy maps
safely. A synchronized edit that changes or removes a component's
`template_file` declaration removes that stale consumer before any of these
operations is offered.
The source freshness proof is intentionally narrower than Citry's runtime
asset API: it accepts direct string literals and direct `pathlib.Path(...)`
declarations. Imported constants, factories, decorators, metaclasses, and
other dynamic selection have no finite proven dependency set, so once any
Python buffer is synchronized the server withholds registry-backed variable
results for that consumer until project discovery runs again.

For a direct proven root member completion, Citry adds an analysis-only
`root is not None` control. This exposes the useful non-`None` member surface
for `Optional` roots before an author has written the guard. It is a completion
aid only: hover and diagnostics analyze the authored union, and downstream
expressions use only real `c-if` or Python narrowing. Incomplete trailing-dot
and call requests retain a separately repaired query for walrus and lambda
safety checks, including structural `cond` and `each` hosts.

Completion filters members that Citry cannot execute: private names, dunder
names, `str.format`, `str.format_map`, type-object `mro`, generator and coroutine
frame/code fields, and every member on receiver-proven code, frame, and
traceback objects. Receiver-sensitive filters require `ty` type evidence plus
exact pinned-typeshed definition ownership, so same-named user classes remain
available.
Parser and sandbox diagnostics remain authoritative for disallowed syntax and
unsafe access, so analyzer findings do not duplicate them.

Assignment expressions use Citry's shared render context, which differs from
ordinary Python in lambda scopes and in loop-clause framing. Semantic results
are therefore withheld after a prior walrus, for a lambda-local walrus, and for
a walrus in the current loop host. Citry's parser result remains authoritative.

## Batch boundary

The shadow builder lives in `citry.analysis`, outside the editor server, and its
tests use disk source as well as synchronized source. That makes the type model
batch-first and reusable by `citry check`.

The first editor delivery does not make the production `citry` package depend
on the 22 MB analyzer executable. Step 17, which already owns shared lint policy
and `citry check` findings, will choose and document the CLI provider mode. It
must consume this exact shadow representation rather than build another one.

## Alternatives rejected

### Link Ruff's internal `ty` crates into `citry_core`

The unpublished `ty_project` and `ty_ide` crates expose database-bound APIs and
`ty_python_semantic` labels itself internal. A clean local check of that route
used hundreds of megabytes of build output, and a completion-only release proof
was about 25 MB before it entered the Python wheel. It would enlarge every
Citry runtime installation, add a new PyO3 surface, and make Citry follow
internal Salsa ownership changes. The supported child LSP provides the same
incremental features with a smaller maintenance contract.

### Ask the editor's installed Python extension

VS Code can forward selected provider calls, but that path cannot obtain another
extension's diagnostics and does not serve PyCharm or batch checking. It also
makes results depend on whichever Python extension happens to be installed.

### Implement a small Citry type system

Parsing catalog display strings or special-casing built-in containers would
work only for demonstrations. It would fail on aliases, overloads, generics,
protocols, forward references, user classes, and narrowing, while creating a
second set of Python semantics for Citry to maintain.

## Falsifiers

Revisit the child-process decision if any of these becomes true:

1. the pinned `ty` wheel cannot cover every platform supported by
   `citry-lsp`;
2. a clean workspace consistently exceeds 200 ms for ordinary member
   completion after startup;
3. virtual sibling documents cannot preserve real project and relative-import
   resolution;
4. the public LSP surface cannot return a required structured operation without
   parsing display text;
5. maintaining the pinned child across two consecutive Ruff updates costs more
   than a Citry-owned compiled adapter would.

## Verification

Acceptance covers declared and inferred roots, `Optional` and union behavior,
truthiness and `is None` narrowing, member and call completion, overload
signatures, exact definition locations, every Python-expression host, explicit
and shorthand loops, nested templates, shared consumers, synchronized source,
invalid current buffers, comments, UTF-16 positions, implicit string
concatenation boundaries, analyzer crashes, and sandbox-only restrictions.
