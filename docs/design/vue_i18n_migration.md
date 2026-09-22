# Vue i18n integration

Citry's i18n extension already records each selected component's provider,
message, formatter, parser, and binding requirements during Python rendering.
The Vue renderer must carry those records with the prepared view and make them
available through Vue's component lifecycle. It must do this for the initial
page and every Events revision without rendering the Python tree again.

This document proposes a generic browser-render extension contract. I18n is
the first consumer, but the contract does not name or import i18n in the Vue
renderer.

## Prior art

The proposal follows these existing paths:

- `citry._vue.events.DirectVueEventsProducer._prepare_from_render_result`
  assembles the selected render once, keeps `Assembly.render_to_occurrence`,
  and produces both initial manifests and revision envelopes.
- `citry._vue.protocol.prepared_manifest` and `revision_envelope` validate the
  prepared view before it reaches the browser.
- `citry.extension.OnSerializeContext` exposes joined document HTML. It runs
  after preparation and does not run for Events subtree responses.
- `citry.ext.dependencies.emission.OnDependenciesContext` lets extensions
  change document or fragment script and style lists. It has the selected
  render, but it does not expose the assembly's stable occurrence mapping.
- `I18nExtension.on_render_context_merge` collects `I18nRenderRecord` values
  in the root `CitryContext`. `emit_i18n_dependencies` currently converts the
  selected records into one initial-page manifest and adds the browser bundle.
- `CitryStable.startPrepared` loads definition and component assets before it
  creates the Vue app. `applyEnvelope` validates and stages a revision before
  it publishes the reactive occurrence snapshot and runs server callbacks.
- `DirectVueEventsProducer` already emits component scripts and styles for
  types introduced by a revision. The current serialization policy treats
  i18n as a special case when deciding whether those assets may arrive late.

The smallest reusable server hook belongs in
`_prepare_from_render_result`, immediately after assembly. At that point the
renderer has the final selected render, stable occurrence IDs, and revision
identity for both entry paths. Neither existing serialization hook has all
three.

## Server preparation hook

Add a core extension hook named `prepare_browser_render`. Core calls each
implementation once, in extension installation order, after assembly and
before it builds the wire manifest.

The context shell is frozen, while `context`, `selected_render`, and `view` are
borrowed read-only values. Core detaches `render_to_occurrence`. The required
final validation checks the render, extension registry, component registry and
every captured plugin descriptor again after all hooks return. Independent
review found that registry and earlier-descriptor revalidation still needs
implementation; checking each extension immediately after its own hook does
not detect a later hook mutating it.

```python
@dataclass(frozen=True, slots=True)
class OnBrowserRenderPrepareContext:
    citry: Citry
    context: CitryContext
    selected_render: CitryRender
    view: PreparedView
    render_to_occurrence: Mapping[str, str]
    app_id: str
    revision: int
    base_revision: int | None
```

`render_to_occurrence` maps selected server render IDs to the stable IDs in
`view.occurrences`. Core supplies a detached, read-only mapping. An extension
must use this mapping to translate its render-time records. It must not derive
ownership from serialized HTML or DOM markers.

The hook returns `BrowserRenderContribution | None`:

```python
@dataclass(frozen=True, slots=True)
class BrowserRenderContribution:
    schema_version: int
    payload: dict[str, object]
    scripts: tuple[Script, ...] = ()
    styles: tuple[Style, ...] = ()
```

Core keys each contribution by the installed extension's public name. The
extension does not write its own name into the record. `payload` must be exact
strict JSON. Core detaches it through a JSON round trip with non-finite numbers
rejected, then verifies after preparation and again after serialization hooks
that the extension registry, captured descriptors, and component registry did
not change. Script and style values use the existing public dependency types.
Prepared delivery rejects response nonces and delayed or non-classic scripts,
preserves validated external metadata, and hashes only engine-owned bytes.

Plugin identity, supported schema versions, and the late-component-asset policy
are fixed initial-app capabilities. They are not repeated in revision
contributions. Configured i18n installs a dormant plugin for prepared apps even
when the initial render has no provider records. This lets a later
Events revision activate its first provider without installing a Vue mixin
after the app has mounted.

The initial manifest and revision envelope gain one optional member:

```json
{
  "extensions": {
    "i18n": {
      "schemaVersion": 1,
      "payload": {}
    }
  }
}
```

Extension names are sorted when encoded. Missing `extensions` means no browser
extension data. Core rejects an invalid name, extra wrapper fields, invalid
generic asset descriptor, or non-object payload before loading assets. After a
verified initial asset registers its factory, the factory validates its name,
schema version, and capabilities before app creation. A revision entry must
match that fixed installed identity and supported schema. Initial and revision
validators apply the same structural rules.

Assets are separate from payload data because they have different lifetimes.
Core publishes JavaScript and CSS under distinct content-addressed identities
and response types. Each app claims only stylesheet elements carrying its exact
app and manifest-URL markers; an authored same-URL stylesheet is never adopted.
Initial plugin and contribution scripts finish in declared order before
bootstrap, and newly required immutable assets load in order during revision
preparation. A plugin required by a revision must already have been installed
on that app. A revision cannot introduce a new plugin after mount. Loaded
revision assets may remain cached after a rejected transaction, but their code
does not receive committed metadata.

Component styles name their component type and the selected occurrence IDs
that require them. A committed update replaces references for its selected
subtree, preserving references from siblings and other apps. Retire a sheet
only after Vue has flushed the update and no committed or staged user remains.
An unsuccessful loader must not remove a sheet adopted by another transaction.

Extension contribution assets have a different owner: the installed extension
in one app. A hook receives only the selected render, so its style list cannot
describe every stylesheet still needed elsewhere in the app. Newly contributed
styles accumulate for that app's lifetime and are released when it is disposed.
The wire distinguishes component ownership from extension ownership explicitly;
extensions do not manufacture component IDs to retain a stylesheet. Each app
keeps its own element ownership and disposal accounting even when browser HTTP
caching shares the URL bytes. Contribution scripts load once per app through
the checked asset policy. Preflight precedes fetching executable assets;
rollback cannot undo arbitrary side effects from executing JavaScript.

## I18n payload

The i18n producer reuses the current checked manifest data, with render IDs
translated through `render_to_occurrence`. A revision contribution describes
the target subtree replacement. The client merges it into the committed full
app metadata and preserves records outside the target subtree. Its payload
contains:

- the catalog and format revisions, format profiles, configured locales,
  locale contexts, parser artifacts, and message endpoint;
- provider records keyed by stable occurrence ID;
- binding and browser API requirements keyed by stable occurrence ID;
- parent provider references expressed as selected stable occurrence IDs,
  checked references to retained providers, or the existing ambient sentinel.

Provider records contain only the fields already validated by
`I18nRenderRecord`: locale, time zone, direction policies, parent, barrier,
messages, outputs, and bindings. Rich translated content remains typed Vue
children and slots. The payload does not carry trusted HTML.

Several selected render IDs may map to one transparent Vue occurrence. The
producer merges compatible requirements and rejects conflicting provider or
barrier roles. An explicit parent provider outside a revision target is encoded
as a retained-ancestor reference. The client resolves it against the committed
full-app provider graph and rejects a missing, stale, or nonancestor reference.
The producer also rejects mismatched catalog and format revisions. A static
render or JavaScript omission does not invoke the browser plugin; server
translation continues to produce ordinary escaped output.

## Vue plugin lifecycle

Each browser asset registers one plugin factory under its extension name.
Before `createApp`, `startPrepared` validates the registry entry, creates the
plugin for this app, and calls `vueApp.use(plugin, host)`. The host exposes
read-only app identity, the committed revision, stable occurrence lookup, and
the extension's validated initial payload. It does not expose mutable
coordinator maps.

The i18n plugin installs three Vue-native pieces before mount:

1. A private Symbol identifies a stable reactive forwarding cell. Every Citry
   occurrence provides one cell for its whole lifetime. The cell points to its
   owned provider, barrier, or inherited parent service. A revision changes the
   cell's contents without replacing the provided object, so retained
   descendants whose native injection resolved once still follow provider and
   barrier changes. An app-level cell handles ambient browser calls.
2. The generic plugin type decorator wraps each registered type's `setup()`.
   Its native Symbol `inject()` receives the nearest ancestor cell, and its
   native Symbol `provide()` returns the occurrence's stable cell. It calls the
   component's authored setup in the same active Vue setup scope. This models
   nested providers through the Vue component tree, including teleported DOM,
   without walking the DOM.
3. The plugin registers the translation directive and exposes `$i18n` through
   `app.config.globalProperties`. Both resolve the calling occurrence through
   the host and read reactive plugin state.

The real Vue proof showed that a plugin mixin's `setup()` does not merge into
these generated component Options. Core therefore calls the generic
`decorateTypeOptions(typeKey, options)` plugin callback before it registers
each type. The callback returns Vue Options and remains available to every
browser plugin. The core wrapper's collision checks still apply to authored
user options; private service transport uses Symbols and does not add a
`js_data`, prop, method, or setup binding. Direct access to Vue component
internals is not part of the contract.

Locale changes update the provider's reactive service. Descendants that inherit
that service and directive bindings then update through Vue effects. Explicit
child providers keep their own policy. Removing a provider or changing a
barrier retargets stable forwarding cells during the same revision activation.

## Revision transaction

The coordinator extends its existing prepared-render transaction with generic
plugin stages. The order is:

1. Validate the envelope, stable occurrence graph, extension wrapper shapes,
   plugin presence, schema versions, and asset descriptors.
2. Load immutable definition, component, and plugin assets. Loading does not
   publish extension data.
3. Call `plugin.prepareRevision(payload, snapshot)` for every installed plugin
   in installation order. It returns an opaque staged value and must not mutate
   committed reactive state.
4. After every plugin prepares successfully, call
   `plugin.activateRevision(stage)`. Activation makes staged metadata visible
   to the Vue render that consumes the incoming occurrence snapshot.
5. In one synchronous publication block, activate every plugin's complete
   state reference, publish the core snapshot, and write every retained
   occurrence's `record.live`. No await, fetch, callback, or other external
   side effect may occur within this block. Vue then batches its normal render
   work until `nextTick`. A user-created `flush: 'sync'` watcher observes
   ordinary intermediate writes; the contract does not promise atomicity
   across occurrences.
6. Call `plugin.commitRevision(stage)` in installation order, publish the core
   revision, then run `onServerRender` callbacks.
7. If preparation fails, call `plugin.abortRevision(stage)` for earlier stages
   in reverse order and leave the committed app unchanged. If activation or
   rendering fails, call `plugin.rollbackRevision(stage)` in reverse order.
   Abort and rollback are idempotent, nonthrowing, and release stage-owned
   resources. Once core publishes the incoming snapshot, a later failure marks
   the app terminal and disposes it; the coordinator does not promise to restore
   the prior DOM. Asset caches remain populated.

Plugins receive detached occurrence metadata and may keep reactive state keyed
by stable occurrence ID. They must remove records absent from the incoming
complete snapshot at commit. A retained ID updates its service in place where
its provider role is compatible. A changed provider role may replace that
service during activation so Vue descendants observe the incoming relationship.
Plugin stages are single-use and tied to app ID, base revision, and incoming
revision. Reuse, concurrent activation, a stale base, or commit in a different
order fails before mutation.

Initial mount uses the same validation and plugin preparation rules with no
base revision. It activates initial stages before `vueApp.mount`, commits them
after the mounted occurrence set passes validation, and rolls them back if
mount fails.

## Rejected alternatives

Using `on_serialize` would limit metadata to full documents and would run after
the prepared view is built. Events revisions do not call it. Using only
`on_dependencies` would couple metadata to tag placement and omit the stable
render-to-occurrence mapping. Both choices would require a second tree scan or
special handling for revisions.

Installing the i18n plugin when the first provider appears in a later revision
would add mixins after existing instances were created. Those instances could
not participate consistently in native injection. Configured plugins therefore
install before the initial mount.

Finding provider ownership from DOM ancestry would fail for fragments,
teleports, and components with multiple roots. Stable prepared occurrence
relationships are the source of provider ancestry.

Adding i18n fields directly to the prepared occurrence or Events protocol
would couple two extensions. The optional `extensions` object gives every
installed extension the same versioned contract.

## Qualification and falsifiers

### Retained providers outside a replacement

A child Events render contains only the selected subtree's render-to-occurrence
mapping. An inherited provider outside that subtree still has its original
server render ID in Python's provided context. Treating that string as a stable
Vue occurrence ID is incorrect; the two identifiers are different.

The independently reviewed correction retains both identifiers in accepted
provider metadata. Each provider carries its stable occurrence `id` and exact
`serverProviderId` from the server's provider record. A selected provider is
referenced by stable ID. An external reference is explicit:

```json
{"serverProviderId": "the-original-server-provider-id"}
```

The browser resolves that reference against previously accepted provider
metadata for the same app and base revision. The provider must be retained
strictly outside the replacement target and be the nearest effective provider
in the combined incoming/retained ancestry. A sibling, descendant, selected
provider encoded as external, missing provider, stale ID, intervening provider
or barrier is an error. This checks the reference against accepted app state;
it does not mint server credentials or keep a server-side app registry.

Apply the same normalization to provider parents and requirement providers
before passing them to the shared i18n wire validator. Provider server IDs must
be unique, and an incoming provider cannot claim a retained provider's server
ID. Replace the ID index with the staged provider records at activation and
restore it on prepublication failure. Detect cycles before following parents.
The current host provider has one server ID; reject ambiguity rather than
silently choosing a mapping.

Qualify an actual child-subtree revision under an unchanged outer provider,
alongside rejection tests for the invalid references above. The implementation
must preserve the retained service object and outside-subtree requirements.

### Revision lifecycle review evidence

The runtime now validates the complete definition, relationship, extension and
asset input before publication. Plugin stages participate in the same ordered
prepare, activate, commit, rollback and disposal boundary as core state.
Focused browser cases cover the following transaction properties:

- JSON definition metadata validates the revision, source
  generation, component relationships, replacement actions, installed plugin
  schemas and all asset descriptors before executing any definition scripts.
  Definition descriptors already contain the required call and replacement
  metadata. After loading, compare the executable definition's metadata with
  the checked declaration before registering it.
- Created plugins and prepared stages are tracked separately. A plugin whose
  preparation fails still needs disposal. Roll back attempted activations in
  reverse order; abort prepared stages whose activation was never attempted.
  Both operations must precede plugin disposal.
- Plugin stages activate before existing user callback scopes are disposed or
  writing the next core state. Activation failure is recoverable while those
  existing resources remain intact. Once core publication starts, a later
  failure is terminal and tears down the app after stage cleanup.
- Type decoration, bridge creation, mounting and initial commit share the
  same initial lifecycle boundary. Recheck the exact server-event source
  generation at commit. Give plugins detached, frozen payload and snapshot
  inputs so an accidental mutation cannot alter another plugin's inputs or
  the checked core transaction.
- Contribution scripts and styles materialize for both initial pages and
  revision responses. Validate the complete descriptor set before execution,
  and keep the prior committed revision usable when preparation fails.

Browser plugin installation and stage processing use canonical extension-name
order. Plugins must not depend on another plugin's installation position.
Server contribution hooks still run in extension installation order.

Failure tests include a definition URL that records execution when given an
invalid revision (it is neither requested nor executed), two plugins
where the second activation throws, failed initial type decoration, terminal
failure after publication, and revision-only contribution JavaScript and CSS.
Assert exact cleanup order and resource counts, not just rejected promises.

### Translation context in supplied slots

The full `CitryStable.startPrepared` browser test found a difference between
component injection and inline slot expressions. Its Page creates an
I18nProvider, which forwards Page's fill through I18nClientHost. The provider
and host both have an `en-US` service, while Page has no service. Vue compiles
the fill's `$i18n` as `Page._ctx.$i18n`, so the inline output sees no locale.
The standalone provider test did not cover this path.

Vue documents that supplied slot expressions retain their author's scope.
[Scoped slot props](https://vuejs.org/guide/components/slots.html#scoped-slots)
let the receiver pass selected values into that scope. The proposed correction
uses that native mechanism for explicitly declared browser-extension context
names. Other component variables keep their normal lexical scope. Independent
review accepted direct slot props as the smallest mechanism to test.

Prior art: `direct_capture.py` generates all native slot outlets and fill
definitions from `DirectSlotRender`; `browser_render.py` owns fixed plugin
descriptors; `events.py` assembles the view before collecting render-specific
contributions. The native Vize compiler already handles scoped-slot parameters.
A local compile check with the pinned compiler produced no diagnostics for:

```html
<Receiver>
  <template v-slot:default="{ $i18n }">
    <slot name="forward" :$i18n="$i18n"></slot>
    <output v-text="$i18n.context.locale + label"></output>
  </template>
</Receiver>
```

The compiled function reads the slot parameter `$i18n` and the parent variable
`_ctx.label` separately. Its forwarding call passes `$i18n` onward as a native
slot prop. No expression-string evaluator or DOM provider search is needed.
This compile check establishes syntax support, not end-to-end correctness.

A subsequent local Chrome proof used three native-compiled definitions with
the exact generated dynamic slot-name syntax. Page supplied an output through
Provider and Host. Its text progressed from `caller:en-US` to `parent:cs-CZ`
after separately changing Page's label and Host's service, then to
`parent:none` after setting that service to null. This proves native forwarding,
caller-variable isolation, reactive replacement, and null handling for that
minimal tree. The full Citry startup and revision tests remain required.

After integrating descriptor capture and generated slot props, the previously
failing `test_i18n_plugin_mounts_through_start_prepared` passed in the pinned
Chrome through Citry's actual Python render and startup path. Page-authored
content sees the locale through I18nProvider and I18nClientHost. This qualifies
that initial forwarding case; the full service and revision matrix are still
in progress.

The implementation proposal is to validate a plugin's fixed template context
names before assembly, retain that exact descriptor for contribution
preparation, and generate the corresponding slot props and destructured fill
parameters. Names must be exact, valid non-reserved public `$` identifiers, unique
across installed plugins, and collision-checked against component declarations.
An ordinary outlet reads the receiving instance's context; a forwarding outlet
inside a supplied fill passes its received context onward. Null is a deliberate
barrier value and must not fall back to an outer service. Applications without
declared context names keep their current slot output.

Before accepting this correction, also compile the exact generated dynamic
slot-name form, `v-slot:['citrySlotExample']="{ $i18n }"`. Test nested providers, barriers, named and
fallback slots, two forwarding levels, components created within fills,
teleports, provider changes on retained instances, and duplicate apps through
the actual prepared-render entrypoint. Ordinary caller variables must remain
lexical in each case. A missing or incompatible plugin capability must fail
before definitions execute. Core must not contain an i18n-specific name branch.

Native injection alone was rejected for inline fills because the mounted test
demonstrates the lexical mismatch. A global render-context stack or rewriting
individual `$i18n` expressions would introduce custom scope machinery; neither
is needed if the scoped-slot tests pass.

The design is not complete until focused tests prove all of these cases:

- initial nested providers, barriers, inherited policies, and ambient context;
- locale switching updates text, attributes, component `$i18n` calls,
  formatters, parsers, and direction without remounting retained IDs; rich
  translated fills update through an Events rerender;
- a revision adds, removes, moves, and reintroduces provider and consumer
  occurrences while retained component state survives, including provider
  removal and barrier changes below retained ancestors;
- the first i18n provider appears after an initial payload with no records;
- a teleported consumer follows component ancestry rather than DOM ancestry;
- a rejected or stale revision leaves the prior locale services and bindings
  active, calls rollback once, and does not run server callbacks;
- newly introduced component JavaScript and CSS load before its first mount,
  subject to the generic late-asset policy;
- duplicate apps keep separate locales, stages, assets, and cleanup;
- unmount removes plugin watchers and directive effects exactly once;
- JavaScript omission emits escaped static translations and no plugin payload;
- malformed extension names, wrapper fields, versions, payloads, occurrence
  references, and asset descriptors fail before app mutation;
- source text containing `<`, `&`, or Vue interpolation syntax stays literal,
  while rich translations remain typed children and slots.

Any failure that requires an i18n import or name check in `_vue`, a DOM scan to
recover provider relationships, a second Python render, or publication of
extension state before envelope validation falsifies the generic contract.
