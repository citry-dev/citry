import {
  createI18nRuntimeState,
  createPerAppI18nService,
  createProviderTreeCore,
  type CoreProviderNode,
} from "./citry-i18n-core";
import {
  createI18nWireRuntime,
  type BindingDefinition,
  type I18nService,
  type LocaleContext,
  type MessageRuntime,
  type ProviderDefinition,
  type ProviderInternal,
  type Requirement,
  type RuntimeConfiguration,
} from "./citry-i18n-runtime";
import type { ComponentOptions, ComponentPublicInstance, ComputedRef, SetupContext, ShallowRef } from "vue";

declare const __CITRY_I18N_BUILD_ID__: string;
interface Occurrence {
  readonly id: string;
  readonly parentId: string | null;
}
interface PreparedSnapshot {
  readonly occurrences: readonly Occurrence[];
  readonly rootId?: string;
  readonly baseRevision?: number;
  readonly replacedRootIds?: readonly string[];
}
interface PluginHost {
  readonly vue: typeof import("vue");
  occurrence(id: string): Occurrence | null;
  occurrenceId(component: ComponentPublicInstance): string | null;
}
interface StableRegistry {
  registerBrowserPlugin(
    name: string,
    version: number,
    factory: (host: PluginHost) => BrowserPlugin,
    contextNames: readonly string[],
  ): void;
}
interface BrowserPlugin {
  install(): void;
  decorateTypeOptions(typeKey: string, options: ComponentOptions): ComponentOptions;
  translateRevision(payload: unknown, resolveOccurrenceId: (id: string) => string): unknown;
  prepareRevision(payload: unknown, snapshot: PreparedSnapshot): PreparedStage;
  prepareRevisionBatch(
    entries: readonly { readonly payload: unknown; readonly rootId: string }[],
    snapshot: PreparedSnapshot,
  ): PreparedStage;
  activateRevision(stage: PreparedStage): void;
  commitRevision(stage: PreparedStage): void;
  abortRevision(stage: PreparedStage): void;
  rollbackRevision(stage: PreparedStage): void;
  dispose(): void;
}
type ProviderReference = string | null | { readonly serverProviderId: string };
interface PreparedProvider extends Omit<ProviderDefinition, "parent"> {
  readonly parent: ProviderReference;
  readonly serverProviderId: string;
}
interface PreparedRequirement extends Record<string, unknown> {
  readonly owner: string;
  readonly provider: ProviderReference;
}
interface PreparedPayload extends Record<string, unknown> {
  readonly barriers: readonly string[];
  readonly providers: readonly PreparedProvider[];
  readonly requirements: readonly PreparedRequirement[];
}
interface PreparedPartial {
  readonly payload: PreparedPayload;
  readonly providers: Map<string, PreparedProvider>;
  readonly barriers: Set<string>;
}
interface PreparedView {
  readonly providers: Map<string, PreparedProvider & { parent: string | null }>;
  readonly barriers: Set<string>;
}
interface ActivationState extends PreparedView {
  readonly configuration: RuntimeConfiguration | null;
  readonly definitions: Map<string, ProviderDefinition>;
  readonly requirements: Map<string, Requirement[]>;
}
interface PreparedStage extends ActivationState {
  readonly previous: {
    readonly configuration: RuntimeConfiguration | null;
    readonly definitions: Map<string, ProviderDefinition>;
    readonly requirements: Map<string, Requirement[]>;
    readonly bindingValues: Map<string, Readonly<Record<string, unknown>>>;
    readonly mounted: Map<
      string,
      {
        readonly definition: ProviderDefinition;
        readonly parentId: string | null;
        readonly context: LocaleContext;
        readonly status: Readonly<Record<string, unknown>>;
      }
    >;
    readonly view: PreparedView;
  };
}
interface PluginGlobal extends Window {
  CitryStable: StableRegistry;
}

(function (global: PluginGlobal) {
  const REGISTRATION = Symbol.for("Citry.i18n.vue-plugin.registered");
  const BUILD_ID = __CITRY_I18N_BUILD_ID__;
  const registeredBuild = Reflect.get(global, REGISTRATION) as unknown;
  if (registeredBuild !== undefined) {
    if (registeredBuild === BUILD_ID) return;
    throw new Error("a different Citry Vue i18n plugin build is already registered");
  }
  const SERVICE = Symbol("Citry.i18n.service");

  function plain(value: unknown, name: string): Record<string, unknown> {
    if (!value || Object.getPrototypeOf(value) !== Object.prototype)
      throw new TypeError("[Citry] i18n: " + name + " must be a plain object.");
    return value as Record<string, unknown>;
  }

  function preparePayload(payloadValue: unknown, snapshot: PreparedSnapshot): PreparedPartial {
    const payloadRecord = plain(payloadValue, "payload");
    const dormantKeys = ["barriers", "providers", "requirements"];
    const configuredKeys = [
      ...dormantKeys,
      "catalog_revision",
      "contexts",
      "formats",
      "formats_revision",
      "locales",
      "messages_url",
      "parsers",
      "runtime",
    ];
    const actualKeys = Object.keys(payloadRecord).sort();
    const expectedKeys = Object.prototype.hasOwnProperty.call(payloadRecord, "catalog_revision")
      ? configuredKeys.sort()
      : dormantKeys.sort();
    if (actualKeys.length !== expectedKeys.length || actualKeys.some((key, index) => key !== expectedKeys[index]))
      throw new TypeError("[Citry] i18n: payload has unknown or missing fields.");
    if (
      !Array.isArray(payloadRecord.providers) ||
      !Array.isArray(payloadRecord.requirements) ||
      !Array.isArray(payloadRecord.barriers)
    )
      throw new TypeError("[Citry] i18n: payload providers, barriers, and requirements must be arrays.");
    const payload = payloadRecord as unknown as PreparedPayload;
    const occurrenceIds = new Set(snapshot.occurrences.map((item) => item.id));
    const providers = new Map<string, PreparedProvider>();
    const serverProviderIds = new Set();
    for (const source of payload.providers) {
      const itemRecord = plain(source, "provider");
      const item = itemRecord as unknown as PreparedProvider;
      if (typeof item.id !== "string" || !occurrenceIds.has(item.id) || providers.has(item.id))
        throw new TypeError("[Citry] i18n: provider occurrence is missing or duplicated.");
      if (
        typeof item.serverProviderId !== "string" ||
        item.serverProviderId.length === 0 ||
        serverProviderIds.has(item.serverProviderId)
      )
        throw new TypeError("[Citry] i18n: provider server identity is invalid.");
      serverProviderIds.add(item.serverProviderId);
      if (
        item.parent !== null &&
        typeof item.parent !== "string" &&
        (!item.parent ||
          Object.keys(item.parent).join(",") !== "serverProviderId" ||
          typeof item.parent.serverProviderId !== "string" ||
          !item.parent.serverProviderId)
      )
        throw new TypeError("[Citry] i18n: provider parent reference is invalid.");
      providers.set(item.id, structuredClone(item));
    }
    const barriers = new Set<string>(payload.barriers);
    if (
      barriers.size !== payload.barriers.length ||
      [...barriers].some((id) => typeof id !== "string" || !occurrenceIds.has(id) || providers.has(id))
    )
      throw new TypeError("[Citry] i18n: barrier occurrence is invalid or conflicts with a provider.");
    return Object.freeze({ payload: structuredClone(payload), providers, barriers });
  }

  global.CitryStable.registerBrowserPlugin(
    "i18n",
    1,
    (host) => {
      const V = host.vue;
      const viewState = V.shallowRef<PreparedView>(
        Object.freeze({
          providers: new Map<string, PreparedProvider & { parent: string | null }>(),
          barriers: new Set<string>(),
        }),
      );
      const cells = new Map<string, ComputedRef<I18nService | null>>();
      const parentCells = new Map<string, ShallowRef<ComputedRef<I18nService | null> | null>>();
      let activeRequirements = new Map<string, Requirement[]>();
      const bindingValues = new Map<string, Readonly<Record<string, unknown>>>();
      let disposed = false;

      function fail(code: string, message: string): never {
        const error = new TypeError(`[Citry] i18n: ${message}`) as TypeError & { code?: string };
        error.code = code;
        runtimeState.activeFluentFailures?.push(error);
        throw error;
      }
      const runtimeState = createI18nRuntimeState<
        RuntimeConfiguration,
        ProviderDefinition,
        Requirement,
        BindingDefinition,
        ProviderInternal,
        I18nService
      >({
        commitContext() {},
        effect(callback) {
          return V.watchEffect(callback);
        },
        onScopeDispose(callback: () => void) {
          if (V.getCurrentScope()) V.onScopeDispose(callback);
        },
        isAlive(provider) {
          return !disposed && host.occurrence(provider.definition.id) !== null;
        },
      });
      const wire = createI18nWireRuntime(runtimeState, fail);
      function treeRoot(internal: ProviderInternal): ProviderInternal {
        let current = internal;
        while (current.parent !== null) current = current.parent;
        return current;
      }
      const tree = createProviderTreeCore<ProviderInternal, Requirement, MessageRuntime>(runtimeState, fail, treeRoot, {
        createMessageRuntime: wire.createMessageRuntime,
        fetch: globalThis.fetch.bind(globalThis),
      });
      function artifactsAgree(left: MessageRuntime, right: MessageRuntime): boolean {
        for (const [message, entry] of Object.entries(left.artifact.messages)) {
          const other = right.artifact.messages[message];
          if (other !== undefined && JSON.stringify(entry) !== JSON.stringify(other)) return false;
        }
        return true;
      }
      function addRequirement(requirement: Requirement): void {
        const target = runtimeState.requirementsByProvider.get(requirement.provider) ?? new Set();
        for (const existing of target) {
          const bindingIds = new Set(existing.bindings.map((binding) => binding.id));
          if (requirement.bindings.some((binding) => bindingIds.has(binding.id)))
            fail("I18N_WIRE_INVALID", "i18n requirements contain a duplicate binding ID.");
          for (const [locale, artifact] of requirement.artifacts) {
            const prior = existing.artifacts.get(locale);
            if (prior !== undefined && !artifactsAgree(prior, artifact))
              fail("I18N_WIRE_INVALID", `i18n requirements conflict for the ${locale} artifact.`);
          }
        }
        target.add(requirement);
        runtimeState.requirementsByProvider.set(requirement.provider, target);
      }
      function validateRequirements(requirementsByOwner: ReadonlyMap<string, readonly Requirement[]>): void {
        const byProvider = new Map<string, Requirement[]>();
        for (const requirements of requirementsByOwner.values()) {
          for (const requirement of requirements) {
            const existing = byProvider.get(requirement.provider) ?? [];
            for (const prior of existing) {
              const bindingIds = new Set(prior.bindings.map((binding) => binding.id));
              if (requirement.bindings.some((binding) => bindingIds.has(binding.id)))
                fail("I18N_WIRE_INVALID", "i18n requirements contain a duplicate binding ID.");
              for (const [locale, artifact] of requirement.artifacts) {
                const priorArtifact = prior.artifacts.get(locale);
                if (priorArtifact !== undefined && !artifactsAgree(priorArtifact, artifact))
                  fail("I18N_WIRE_INVALID", `i18n requirements conflict for the ${locale} artifact.`);
              }
            }
            existing.push(requirement);
            byProvider.set(requirement.provider, existing);
          }
        }
      }
      function sameContext(left: LocaleContext, right: LocaleContext): boolean {
        return (
          left.catalog_revision === right.catalog_revision &&
          left.direction === right.direction &&
          left.formats_revision === right.formats_revision &&
          left.locale === right.locale &&
          left.time_zone === right.time_zone &&
          left.tzdb_revision === right.tzdb_revision &&
          JSON.stringify(left.fallback_locales) === JSON.stringify(right.fallback_locales)
        );
      }
      function internalFor(id: string): ProviderInternal | null {
        if (disposed) return null;
        const existing = runtimeState.mountedProviders.get(id);
        if (existing) return existing;
        const definition = runtimeState.definitions.get(id);
        if (!definition || runtimeState.configuration === null) return null;
        const parent: ProviderInternal | null = definition.parent === null ? null : internalFor(definition.parent);
        const internal: ProviderInternal = {
          bindings: new Set(),
          children: new Set(),
          definition,
          generation: 0,
          parent,
          plannedContexts: new Map(),
          plannedOwners: new Map(),
          state: V.reactive({
            context: parent === null ? definition.context : tree.childContext(parent.state.context, definition),
            status: Object.freeze({ phase: "ready" }),
          }),
          subscribers: new Set(),
          switchGeneration: 0,
          service: null,
        };
        const serviceState = {
          adapter: {
            commitContext() {},
            effect: runtimeState.adapter.effect,
            isAlive: (provider: CoreProviderNode) => !disposed && host.occurrence(provider.definition.id) !== null,
            onScopeDispose: runtimeState.adapter.onScopeDispose,
          },
          get configuration() {
            return runtimeState.configuration;
          },
        };
        const service = createPerAppI18nService(serviceState, tree, internal, {
          addRequirement,
          bindingValues(value, name) {
            if (!value || typeof value !== "object" || Array.isArray(value))
              fail("I18N_BINDING_INVALID", `${name} must return an object.`);
            return value as Readonly<Record<string, unknown>>;
          },
          createFormatter: wire.createFormatter,
          createParser: wire.createParser,
          exactString: wire.exactString,
          fail,
          reportBindingError(id, error) {
            console.error(`[Citry] i18n binding ${id} failed:`, error);
          },
          sameContext,
          stringList: wire.stringList,
          treeRoot,
        });
        internal.service = service;
        runtimeState.internals.set(service, internal);
        runtimeState.mountedProviders.set(id, internal);
        parent?.children.add(internal);
        return internal;
      }
      function serviceFor(id: string): I18nService | null {
        return internalFor(id)?.service ?? null;
      }

      function cellFor(
        id: string,
        parentCell: ComputedRef<I18nService | null> | null,
      ): ComputedRef<I18nService | null> {
        let parent = parentCells.get(id);
        if (!parent) {
          parent = V.shallowRef(parentCell);
          parentCells.set(id, parent);
        } else {
          parent.value = parentCell;
        }
        let cell = cells.get(id);
        if (cell) return cell;
        cell = V.computed(() => {
          const provider = viewState.value.providers.get(id);
          if (provider) return serviceFor(id);
          if (viewState.value.barriers.has(id)) return null;
          return V.unref(parent.value) ?? null;
        });
        cells.set(id, cell);
        return cell;
      }

      function occurrenceFrom(snapshot: PreparedSnapshot, id: string): Occurrence | null {
        return snapshot.occurrences.find((item) => item.id === id) ?? host.occurrence(id);
      }

      function isWithin(snapshot: PreparedSnapshot, id: string, rootId: string): boolean {
        const seen = new Set();
        let current = occurrenceFrom(snapshot, id);
        while (current) {
          if (current.id === rootId) return true;
          if (seen.has(current.id)) throw new Error("[Citry] i18n: occurrence ancestry contains a cycle.");
          seen.add(current.id);
          current = current.parentId === null ? null : occurrenceFrom(snapshot, current.parentId);
        }
        return false;
      }

      function prepareRevision(payload: unknown, snapshot: PreparedSnapshot): PreparedStage {
        if (disposed) throw new Error("[Citry] i18n: disposed plugin cannot prepare a revision.");
        const partial = preparePayload(payload, snapshot);
        let configuration = runtimeState.configuration;
        const revision = Object.prototype.hasOwnProperty.call(snapshot, "baseRevision");
        const rootIds = snapshot.replacedRootIds ?? (typeof snapshot.rootId === "string" ? [snapshot.rootId] : []);
        if (revision && rootIds.length === 0) throw new TypeError("i18n revision snapshot has no rootId");
        const withinReplaced = (id: string): boolean => rootIds.some((rootId) => isWithin(snapshot, id, rootId));
        const retainedProviders = revision
          ? new Map<string, PreparedProvider & { parent: string | null }>(viewState.value.providers)
          : new Map<string, PreparedProvider & { parent: string | null }>();
        if (revision) for (const id of retainedProviders.keys()) if (withinReplaced(id)) retainedProviders.delete(id);
        const retainedByServer = new Map<string, string>();
        for (const [id, provider] of retainedProviders) {
          if (retainedByServer.has(provider.serverProviderId))
            throw new Error("[Citry] i18n: retained server provider identity is ambiguous.");
          retainedByServer.set(provider.serverProviderId, id);
        }
        for (const provider of partial.providers.values()) {
          if (retainedByServer.has(provider.serverProviderId))
            throw new Error("[Citry] i18n: incoming provider reuses a retained server provider identity.");
        }
        const resolveProviderReference = (reference: ProviderReference, owner: string): string | null => {
          if (reference === null || typeof reference === "string") return reference;
          plain(reference, "server provider reference");
          if (Object.keys(reference).join(",") !== "serverProviderId" || typeof reference.serverProviderId !== "string")
            throw new Error("[Citry] i18n: invalid retained server provider reference.");
          const resolved = retainedByServer.get(reference.serverProviderId);
          if (!resolved || withinReplaced(resolved) || !isWithin(snapshot, owner, resolved))
            throw new Error("[Citry] i18n: retained server provider reference is stale or not an ancestor.");
          let current = occurrenceFrom(snapshot, owner)?.parentId ?? null;
          while (current !== null && current !== resolved) {
            if (partial.barriers.has(current) || partial.providers.has(current) || retainedProviders.has(current))
              throw new Error(
                "[Citry] i18n: retained server provider reference skips an effective provider or barrier.",
              );
            current = occurrenceFrom(snapshot, current)?.parentId ?? null;
          }
          if (current !== resolved)
            throw new Error("[Citry] i18n: retained server provider is outside the owner ancestry.");
          return resolved;
        };
        const normalizedPayload: Record<string, unknown> & {
          providers: Array<Omit<ProviderDefinition, "parent"> & { parent: string | null }>;
          requirements: Array<Record<string, unknown> & { owner: string; provider: string | null }>;
          barriers?: readonly string[];
        } = { ...structuredClone(partial.payload), providers: [], requirements: [] };
        normalizedPayload.providers = partial.payload.providers.map((provider) => {
          const { serverProviderId: _serverProviderId, ...wireProvider } = provider;
          return { ...wireProvider, parent: resolveProviderReference(provider.parent, provider.id) };
        });
        normalizedPayload.requirements = partial.payload.requirements.map((requirement) => ({
          ...requirement,
          provider: resolveProviderReference(requirement.provider, requirement.owner),
        }));
        const definitions = revision
          ? new Map<string, ProviderDefinition>(runtimeState.definitions)
          : new Map<string, ProviderDefinition>();
        const requirements = revision
          ? new Map<string, Requirement[]>(activeRequirements)
          : new Map<string, Requirement[]>();
        if (revision) {
          for (const id of definitions.keys()) if (withinReplaced(id)) definitions.delete(id);
          for (const owner of requirements.keys()) if (withinReplaced(owner)) requirements.delete(owner);
        }
        if (Object.prototype.hasOwnProperty.call(partial.payload, "catalog_revision")) {
          const projected = { ...normalizedPayload, schema_version: 1 };
          delete projected.barriers;
          const [manifest, checkedConfiguration] = wire.configureManifest(projected);
          configuration = checkedConfiguration;
          for (const value of manifest.providers) {
            const checked = wire.providerDefinition(value, checkedConfiguration);
            definitions.set(checked.id, checked);
          }
          for (const value of manifest.requirements) {
            const checked = wire.requirementRecord(value, checkedConfiguration);
            const owned = requirements.get(checked.owner) ?? [];
            requirements.set(checked.owner, [...owned, checked]);
          }
        }
        const providers = retainedProviders;
        const barriers = revision ? new Set<string>(viewState.value.barriers) : new Set<string>();
        if (revision) {
          for (const id of providers.keys()) if (withinReplaced(id)) providers.delete(id);
          for (const id of barriers) if (withinReplaced(id)) barriers.delete(id);
        }
        for (const [id, provider] of partial.providers) {
          providers.set(id, { ...provider, parent: resolveProviderReference(provider.parent, provider.id) });
        }
        for (const id of partial.barriers) barriers.add(id);
        for (const [id, provider] of providers) {
          if (provider.parent === null || providers.has(provider.parent)) continue;
          let parentId = occurrenceFrom(snapshot, id)?.parentId ?? null;
          while (parentId !== null && !providers.has(parentId)) {
            if (barriers.has(parentId)) {
              parentId = null;
              break;
            }
            parentId = occurrenceFrom(snapshot, parentId)?.parentId ?? null;
          }
          providers.set(id, { ...provider, parent: parentId });
          const definition = definitions.get(id);
          if (definition) definitions.set(id, { ...definition, parent: parentId });
        }
        for (const provider of providers.values()) {
          if (provider.parent === null) continue;
          if (!occurrenceFrom(snapshot, provider.parent) || !isWithin(snapshot, provider.id, provider.parent))
            throw new Error("[Citry] i18n: provider parent is missing, stale, or not an ancestor.");
        }
        validateRequirements(requirements);
        return Object.freeze({
          payload: partial.payload,
          providers,
          barriers,
          configuration,
          definitions,
          requirements,
          previous: Object.freeze({
            configuration: runtimeState.configuration,
            definitions: new Map(runtimeState.definitions),
            requirements: new Map(activeRequirements),
            bindingValues: new Map(bindingValues),
            mounted: new Map(
              [...runtimeState.mountedProviders].map(([id, internal]) => [
                id,
                {
                  definition: internal.definition,
                  parentId: internal.parent?.definition.id ?? null,
                  context: internal.state.context,
                  status: internal.state.status,
                },
              ]),
            ),
            view: viewState.value,
          }),
        });
      }

      function prepareRevisionBatch(
        entries: readonly { readonly payload: unknown; readonly rootId: string }[],
        snapshot: PreparedSnapshot,
      ): PreparedStage {
        if (entries.length < 2) throw new TypeError("[Citry] i18n: a revision batch requires several targets.");
        const canonical = (value: unknown): string => {
          if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
          if (value && typeof value === "object") {
            const record = value as Record<string, unknown>;
            return `{${Object.keys(record)
              .sort()
              .map((key) => `${JSON.stringify(key)}:${canonical(record[key])}`)
              .join(",")}}`;
          }
          return JSON.stringify(value);
        };
        const payloads = entries.map((entry) => preparePayload(entry.payload, snapshot).payload);
        const merged = structuredClone(payloads[0]) as Record<string, unknown>;
        for (const field of ["providers", "barriers", "requirements"]) merged[field] = [];
        const metadata = new Map<string, string>();
        for (const payload of payloads) {
          for (const [key, value] of Object.entries(payload)) {
            if (key === "providers" || key === "barriers" || key === "requirements") continue;
            const encoded = canonical(value);
            const prior = metadata.get(key);
            if (prior !== undefined && prior !== encoded)
              throw new Error(`[Citry] i18n: revision batch ${key} conflicts across targets.`);
            metadata.set(key, encoded);
            merged[key] = structuredClone(value);
          }
          for (const field of ["providers", "barriers", "requirements"] as const) {
            if (!Array.isArray(payload[field]))
              throw new TypeError(`[Citry] i18n: revision batch ${field} must be an array.`);
            (merged[field] as unknown[]).push(...structuredClone(payload[field]));
          }
        }
        return prepareRevision(merged, {
          ...snapshot,
          replacedRootIds: entries.map((entry) => entry.rootId),
        });
      }

      function activate(stage: ActivationState): void {
        if (disposed) throw new Error("[Citry] i18n: disposed plugin cannot activate a revision.");
        const checked = new Set<string>();
        const checking = new Set<string>();
        const validateDefinition = (id: string): void => {
          if (checked.has(id)) return;
          if (checking.has(id)) throw new Error("[Citry] i18n: provider definition graph contains a cycle.");
          checking.add(id);
          const definition = stage.definitions.get(id);
          if (definition && definition.parent !== null) {
            if (!stage.definitions.has(definition.parent)) {
              throw new Error("[Citry] i18n: provider definition parent is missing.");
            }
            validateDefinition(definition.parent);
          }
          checking.delete(id);
          checked.add(id);
        };
        for (const id of stage.definitions.keys()) validateDefinition(id);
        const prior = new Map(
          [...runtimeState.mountedProviders].map(([id, internal]) => [
            id,
            { definition: internal.definition, parent: internal.parent },
          ]),
        );
        runtimeState.configuration = stage.configuration;
        runtimeState.definitions.clear();
        for (const [id, definition] of stage.definitions) runtimeState.definitions.set(id, definition);
        runtimeState.requirementsByProvider.clear();
        activeRequirements = new Map(stage.requirements);
        for (const requirements of activeRequirements.values())
          for (const requirement of requirements) addRequirement(requirement);
        const activeBindingIds = new Set<string>();
        runtimeState.bindingDefinitions.clear();
        for (const requirements of activeRequirements.values()) {
          for (const requirement of requirements) {
            for (const binding of requirement.bindings) {
              runtimeState.bindingDefinitions.set(binding.id, binding);
              activeBindingIds.add(binding.id);
              if (!bindingValues.has(binding.id)) bindingValues.set(binding.id, binding.values);
            }
          }
        }
        for (const id of bindingValues.keys()) if (!activeBindingIds.has(id)) bindingValues.delete(id);
        const ordered: Array<[string, ProviderInternal]> = [];
        const visiting = new Set<string>();
        const visited = new Set<string>();
        const visit = (id: string): void => {
          if (visited.has(id)) return;
          if (visiting.has(id)) throw new Error("[Citry] i18n: provider definition graph contains a cycle.");
          visiting.add(id);
          const definition = runtimeState.definitions.get(id);
          if (definition && definition.parent !== null && runtimeState.mountedProviders.has(definition.parent)) {
            visit(definition.parent);
          }
          visiting.delete(id);
          visited.add(id);
          const internal = runtimeState.mountedProviders.get(id);
          if (internal) ordered.push([id, internal]);
        };
        for (const id of runtimeState.mountedProviders.keys()) visit(id);
        const contextChanged = new Set<string>();
        for (const [id, internal] of ordered) {
          const definition = runtimeState.definitions.get(id);
          if (definition) {
            const desiredParent = definition.parent === null ? null : internalFor(definition.parent);
            const previous = prior.get(id);
            if (internal.parent !== desiredParent) {
              internal.parent?.children.delete(internal);
              desiredParent?.children.add(internal);
              internal.parent = desiredParent;
            }
            internal.definition = definition;
            const definitionChanged = JSON.stringify(previous?.definition) !== JSON.stringify(definition);
            const parentContextChanged = desiredParent !== null && contextChanged.has(desiredParent.definition.id);
            if (definitionChanged || previous?.parent !== desiredParent || parentContextChanged) {
              internal.state.context =
                desiredParent === null
                  ? definition.context
                  : tree.childContext(desiredParent.state.context, definition);
              contextChanged.add(id);
            }
          }
        }
        viewState.value = Object.freeze({ providers: stage.providers, barriers: stage.barriers });
      }

      function renderBinding(id: unknown, values: (() => unknown) | undefined): string {
        if (disposed) fail("I18N_BINDING_INVALID", "binding helper belongs to a disposed plugin.");
        if (typeof id !== "string") fail("I18N_BINDING_INVALID", "binding helper requires a binding ID.");
        const definition = runtimeState.bindingDefinitions.get(id);
        if (!definition) fail("I18N_BINDING_INVALID", `binding ${id} is not active.`);
        const service = serviceFor(definition.provider);
        if (!service) fail("I18N_BINDING_INVALID", `binding ${id} has no mounted provider.`);
        if (values !== undefined) {
          try {
            const candidate = values();
            const normalized = Object.freeze({ ...plain(candidate, `binding ${id} values`) });
            const translated = service.tr(definition.message, normalized, {
              ...(definition.output === undefined ? {} : { attr: definition.output }),
            });
            bindingValues.set(id, normalized);
            return translated;
          } catch (error) {
            console.error(`[Citry] i18n binding ${id} values failed:`, error);
          }
        }
        return service.tr(definition.message, bindingValues.get(id) ?? definition.values, {
          ...(definition.output === undefined ? {} : { attr: definition.output }),
        });
      }

      function translateRevision(payload: unknown, resolveOccurrenceId: (id: string) => string): unknown {
        const translated = structuredClone(plain(payload, "i18n revision payload")) as PreparedPayload;
        if (
          !Array.isArray(translated.providers) ||
          !Array.isArray(translated.barriers) ||
          !Array.isArray(translated.requirements)
        ) {
          throw new TypeError("[Citry] i18n: revision payload has invalid occurrence reference containers.");
        }
        return {
          ...translated,
          providers: translated.providers.map((provider) => ({
            ...provider,
            id: resolveOccurrenceId(provider.id),
            parent: typeof provider.parent === "string" ? resolveOccurrenceId(provider.parent) : provider.parent,
          })),
          barriers: translated.barriers.map(resolveOccurrenceId),
          requirements: translated.requirements.map((requirement) => ({
            ...requirement,
            owner: resolveOccurrenceId(requirement.owner),
            provider:
              typeof requirement.provider === "string"
                ? resolveOccurrenceId(requirement.provider)
                : requirement.provider,
          })),
        };
      }

      const plugin = {
        install() {},
        translateRevision,
        decorateTypeOptions(_typeKey: string, options: ComponentOptions): ComponentOptions {
          const propNames = Array.isArray(options.props) ? options.props : Object.keys(options.props || {});
          const injectNames = Array.isArray(options.inject) ? options.inject : Object.keys(options.inject || {});
          if (
            propNames.includes("$i18n") ||
            propNames.includes("$citryI18nBinding") ||
            injectNames.includes("$i18n") ||
            injectNames.includes("$citryI18nBinding") ||
            Object.prototype.hasOwnProperty.call(options.methods || {}, "$i18n") ||
            Object.prototype.hasOwnProperty.call(options.computed || {}, "$i18n") ||
            Object.prototype.hasOwnProperty.call(options.methods || {}, "$citryI18nBinding") ||
            Object.prototype.hasOwnProperty.call(options.computed || {}, "$citryI18nBinding")
          )
            throw new Error("[Citry] i18n: $i18n collides with an existing Vue option.");
          const originalSetup = options.setup;
          const originalCreated = options.created;
          const originalBeforeUnmount = options.beforeUnmount;
          return {
            ...options,
            setup(props: Readonly<Record<string, unknown>>, setupContext: SetupContext) {
              const parentCell = V.inject(SERVICE, null);
              const id = typeof props.citryId === "string" ? props.citryId : null;
              const cell = id === null ? null : cellFor(id, parentCell);
              if (cell !== null) V.provide(SERVICE, cell);
              const original = originalSetup ? originalSetup(props, setupContext) : {};
              if (
                original &&
                typeof original === "object" &&
                (Object.prototype.hasOwnProperty.call(original, "$i18n") ||
                  Object.prototype.hasOwnProperty.call(original, "$citryI18nBinding"))
              )
                throw new Error("[Citry] i18n: template context collides with an existing setup binding.");
              return original;
            },
            created() {
              const id = typeof this.citryId === "string" ? this.citryId : host.occurrenceId(this);
              if (id !== null) {
                if ("$i18n" in this || "$citryI18nBinding" in this)
                  throw new Error("[Citry] i18n: template context collides with an existing public instance property.");
                Object.defineProperty(this, "$i18n", {
                  configurable: true,
                  get() {
                    return cells.get(id)?.value ?? null;
                  },
                });
                Object.defineProperty(this, "$citryI18nBinding", {
                  configurable: true,
                  value: renderBinding,
                });
              }
              if (originalCreated) originalCreated.call(this);
            },
            beforeUnmount() {
              try {
                if (originalBeforeUnmount) originalBeforeUnmount.call(this);
              } finally {
                const id = typeof this.citryId === "string" ? this.citryId : host.occurrenceId(this);
                if (id !== null && !host.occurrence(id)) {
                  cells.delete(id);
                  parentCells.delete(id);
                }
              }
            },
          };
        },
        prepareRevision,
        prepareRevisionBatch,
        activateRevision(stage: PreparedStage) {
          activate(stage);
        },
        commitRevision(stage: PreparedStage) {
          for (const [id, internal] of runtimeState.mountedProviders) {
            if (stage.providers.has(id)) continue;
            internal.bindings.forEach((binding) => {
              binding.dispose?.();
            });
            internal.bindings.clear();
            internal.subscribers.clear();
            internal.parent?.children.delete(internal);
            runtimeState.mountedProviders.delete(id);
          }
        },
        abortRevision() {},
        rollbackRevision(stage: PreparedStage) {
          bindingValues.clear();
          for (const [id, values] of stage.previous.bindingValues) bindingValues.set(id, values);
          activate({
            configuration: stage.previous.configuration,
            definitions: stage.previous.definitions,
            requirements: stage.previous.requirements,
            providers: stage.previous.view.providers,
            barriers: stage.previous.view.barriers,
          });
          for (const internal of runtimeState.mountedProviders.values()) internal.children.clear();
          for (const [id, saved] of stage.previous.mounted) {
            const internal = runtimeState.mountedProviders.get(id);
            if (!internal) continue;
            internal.definition = saved.definition;
            internal.parent =
              saved.parentId === null ? null : (runtimeState.mountedProviders.get(saved.parentId) ?? null);
            internal.parent?.children.add(internal);
            internal.state.context = saved.context;
            internal.state.status = saved.status;
          }
        },
        dispose() {
          if (disposed) return;
          disposed = true;
          let firstError: unknown = null;
          for (const internal of runtimeState.mountedProviders.values()) {
            for (const binding of internal.bindings) {
              try {
                binding.dispose?.();
              } catch (error) {
                firstError ??= error;
              }
            }
            internal.bindings.clear();
            internal.subscribers.clear();
            internal.children.clear();
            internal.parent = null;
          }
          runtimeState.mountedProviders.clear();
          runtimeState.requirementsByProvider.clear();
          runtimeState.bindingDefinitions.clear();
          runtimeState.definitions.clear();
          runtimeState.configuration = null;
          activeRequirements.clear();
          bindingValues.clear();
          cells.clear();
          parentCells.clear();
          viewState.value = Object.freeze({
            providers: new Map<string, PreparedProvider & { parent: string | null }>(),
            barriers: new Set<string>(),
          });
          if (firstError !== null) throw firstError;
        },
      };
      return plugin;
    },
    ["$citryI18nBinding", "$i18n"],
  );
  Object.defineProperty(global, REGISTRATION, { value: BUILD_ID, configurable: false, writable: false });
})(window as unknown as PluginGlobal);
