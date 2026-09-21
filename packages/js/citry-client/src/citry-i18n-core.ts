/** Framework-neutral exact-number and locale parser primitives shared by Citry browser adapters. */
const BIDI_CONTROLS = new Set(Array.from("\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"));
const PARAGRAPH_BOUNDARIES = new Set(Array.from("\r\n\u001c\u001d\u001e\u0085\u2029"));
const DECIMAL_PATTERN = /^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$/;
const INTEGER_PATTERN = /^-?(?:0|[1-9][0-9]*)$/;
type NumericParseState = "incomplete" | "invalid" | "valid";
export interface NumericParseResult {
  readonly error: string | null;
  readonly input: string;
  readonly state: NumericParseState;
  readonly valid: boolean;
  readonly value: string | null;
}
export interface BrowserNumberParserRecord {
  readonly decimal: string;
  readonly digits: readonly string[];
  readonly grouping: string;
  readonly minus_prefix: string;
  readonly minus_suffix: string;
  readonly notation: "decimal" | "decimal_or_scientific";
  readonly plus_prefix: string;
  readonly plus_suffix: string;
  readonly primary_group: number;
  readonly secondary_group: number;
}
type Failure = (code: string, message: string) => never;

export function createI18nRuntimeState<
  Configuration,
  ProviderDefinition,
  Requirement,
  BindingDefinition,
  ProviderInternal,
  Service extends object,
>(adapter: {
  commitContext(provider: ProviderInternal, context: unknown): void;
  effect(callback: () => void): () => void;
  isAlive(provider: ProviderInternal): boolean;
  onScopeDispose?(callback: () => void): void;
}) {
  return {
    adapter,
    configuration: null as Configuration | null,
    activeFluentFailures: null as Array<TypeError & { code?: string }> | null,
    definitions: new Map<string, ProviderDefinition>(),
    requirementsByProvider: new Map<string, Set<Requirement>>(),
    bindingDefinitions: new Map<string, BindingDefinition>(),
    bindingReferenceCounts: new Map<string, number>(),
    mountedProviders: new Map<string, ProviderInternal>(),
    internals: new WeakMap<Service, ProviderInternal>(),
  };
}

export interface I18nServiceCoreOperations<Context, Formatter, Parser, Resolved> {
  context(): Context;
  format(): Formatter;
  parse(): Parser;
  status(): Readonly<Record<string, unknown>>;
  bind(options: {
    readonly message: string;
    readonly onChange: (text: string, resolved: Resolved) => void;
    readonly output?: string;
    readonly values?: () => Readonly<Record<string, unknown>>;
  }): Readonly<{ dispose(): void; refresh(): void }>;
  ensureMessages(messages: string | readonly string[]): Promise<void>;
  resolve(message: string, values?: Readonly<Record<string, unknown>>, options?: { readonly attr?: string }): Resolved;
  subscribe(callback: (context: Context) => void): () => void;
  switchLocale(locale: string): Promise<Readonly<{ context?: Context; status: "committed" | "stale" }>>;
  tr(message: string, values?: Readonly<Record<string, unknown>>, options?: { readonly attr?: string }): string;
}

export function createI18nServiceCore<Context, Formatter, Parser, Resolved>(
  operations: I18nServiceCoreOperations<Context, Formatter, Parser, Resolved>,
) {
  return Object.freeze({
    get context() {
      return operations.context();
    },
    get format() {
      return operations.format();
    },
    get parse() {
      return operations.parse();
    },
    get status() {
      return operations.status();
    },
    bind: operations.bind,
    ensureMessages: operations.ensureMessages,
    resolve: operations.resolve,
    subscribe: operations.subscribe,
    switchLocale: operations.switchLocale,
    tr: operations.tr,
  });
}

export interface CoreMessageRuntime {
  readonly artifact: { readonly messages: Readonly<Record<string, { readonly bundle_locale: string }>> };
  format(token: string, values: Readonly<Record<string, unknown>>): string;
}
export interface CoreRequirement extends TreeRequirement {
  readonly artifacts: Map<string, CoreMessageRuntime>;
  readonly bindings: readonly unknown[];
  readonly owner: string;
  readonly provider: string;
  readonly renderedLocale: string;
}
export interface CoreActiveBinding {
  disposed: boolean;
  refresh(): void;
  dispose?(): void;
}
export interface CoreResolvedMessage {
  readonly direction: "ltr" | "rtl";
  readonly locale: string;
  readonly text: string;
  readonly usedFallback: boolean;
}
export interface CoreProviderNode extends ProviderTreeNode {
  readonly bindings: Set<CoreActiveBinding>;
  readonly children: Set<CoreProviderNode>;
  definition: TreeDefinition;
  generation: number;
  parent: CoreProviderNode | null;
  readonly plannedContexts: Map<CoreProviderNode, TreeContext>;
  readonly plannedOwners: Map<CoreProviderNode, number>;
  readonly state: { context: TreeContext; status: Readonly<Record<string, unknown>> };
  readonly subscribers: Set<(context: TreeContext) => void>;
  switchGeneration: number;
}
export interface CoreRuntimeState {
  readonly adapter: {
    commitContext(provider: CoreProviderNode, context: TreeContext): void;
    effect(callback: () => void): () => void;
    isAlive(provider: CoreProviderNode): boolean;
    onScopeDispose?(callback: () => void): void;
  };
  configuration: { contexts: Map<string, TreeContext>; locales: Set<string> } | null;
}
export interface CoreProviderTreeOperations {
  fetchArtifact(requirement: CoreRequirement, locale: string): Promise<CoreMessageRuntime>;
  planProviderSubtree(internal: CoreProviderNode, context: TreeContext, owner: number): void;
  plannedTree(root: CoreProviderNode): Array<[CoreProviderNode, TreeContext]>;
  providerRequirements(internal: CoreProviderNode): CoreRequirement[];
  restoreFailedPlan(coordinator: CoreProviderNode, owner: number, initiator: CoreProviderNode, error: unknown): void;
  rootSwitchContext(internal: CoreProviderNode, locale: string): TreeContext;
  stageTree(
    planned: ReadonlyArray<readonly [CoreProviderNode, TreeContext]>,
  ): Promise<Array<[CoreProviderNode, TreeContext]>>;
}

export function createPerAppI18nService<Formatter, Parser>(
  state: CoreRuntimeState,
  tree: CoreProviderTreeOperations,
  internal: CoreProviderNode,
  dependencies: {
    addRequirement(requirement: CoreRequirement): void;
    bindingValues(value: unknown, name: string): Readonly<Record<string, unknown>>;
    createFormatter(internal: CoreProviderNode): Formatter;
    createParser(internal: CoreProviderNode): Parser;
    exactString(value: unknown, name: string): string;
    fail: Failure;
    reportBindingError(id: string, error: unknown): void;
    sameContext(left: TreeContext, right: TreeContext): boolean;
    stringList(values: unknown[], name: string): void;
    treeRoot(internal: CoreProviderNode): CoreProviderNode;
  },
) {
  const { fail } = dependencies;
  function formatLoaded(
    message: string,
    values: Readonly<Record<string, unknown>>,
    attr: string | undefined,
  ): { entry: { readonly bundle_locale: string }; text: string } {
    if (typeof message !== "string" || message.length === 0) fail("I18N_MESSAGE_INVALID", "message must be a string.");
    if (attr !== undefined && (typeof attr !== "string" || attr.length === 0)) {
      fail("I18N_MESSAGE_INVALID", "attr must be a non-empty string when provided.");
    }
    const token = attr === undefined ? message : `${message}.${attr}`;
    for (const requirement of tree.providerRequirements(internal)) {
      const runtime = requirement.artifacts.get(internal.state.context.locale);
      const entry = runtime?.artifact.messages[token];
      if (runtime !== undefined && entry !== undefined) return { entry, text: runtime.format(token, values) };
    }
    fail(
      "I18N_MESSAGE_MISSING",
      `message ${token} is not loaded; declare a literal client use or await i18n.ensureMessages(${JSON.stringify(message)}).`,
    );
    throw new Error("unreachable");
  }
  function resolvedLoaded(message: string, values: Readonly<Record<string, unknown>>, output: string | undefined) {
    const resolved = formatLoaded(message, values, output);
    const locale = resolved.entry.bundle_locale;
    const selected = state.configuration?.contexts.get(locale);
    return Object.freeze({
      direction: selected?.direction ?? internal.state.context.direction,
      locale,
      text: resolved.text,
      usedFallback: locale !== internal.state.context.locale,
    });
  }
  const formatter = dependencies.createFormatter(internal);
  const parser = dependencies.createParser(internal);
  return createI18nServiceCore({
    context: () => internal.state.context,
    format: () => formatter,
    parse: () => parser,
    status: () => internal.state.status,
    bind(options: {
      readonly message: string;
      readonly onChange: (text: string, resolved: CoreResolvedMessage) => void;
      readonly output?: string;
      readonly values?: () => Readonly<Record<string, unknown>>;
    }) {
      if (options === null || typeof options !== "object")
        fail("I18N_BINDING_INVALID", "bind() needs an options object.");
      const message = dependencies.exactString(options.message, "bind() message");
      const output = options.output;
      if (output !== undefined && (typeof output !== "string" || output.length === 0)) {
        fail("I18N_BINDING_INVALID", "bind() output must be a non-empty string.");
      }
      if (typeof options.onChange !== "function") fail("I18N_BINDING_INVALID", "bind() needs onChange.");
      if (options.values !== undefined && typeof options.values !== "function") {
        fail("I18N_BINDING_INVALID", "bind() values must be a function.");
      }
      let values: Readonly<Record<string, unknown>> = {};
      let stopEffect: (() => void) | null = null;
      const id = `imperative:${internal.definition.id}`;
      const active: CoreActiveBinding = {
        disposed: false,
        refresh() {
          if (active.disposed) return;
          try {
            if (options.values !== undefined) values = dependencies.bindingValues(options.values(), "bind() values");
            const resolved = resolvedLoaded(message, values, output);
            options.onChange(resolved.text, resolved);
          } catch (error) {
            dependencies.reportBindingError(id, error);
          }
        },
      };
      internal.bindings.add(active);
      if (options.values !== undefined) stopEffect = state.adapter.effect(active.refresh);
      else active.refresh();
      const dispose = () => {
        if (active.disposed) return;
        active.disposed = true;
        internal.bindings.delete(active);
        stopEffect?.();
      };
      active.dispose = dispose;
      state.adapter.onScopeDispose?.(dispose);
      return Object.freeze({
        dispose,
        refresh: active.refresh,
      });
    },
    async ensureMessages(input: string | readonly string[]) {
      const messages = typeof input === "string" ? [input] : [...input];
      dependencies.stringList(messages, "ensureMessages messages");
      const requirement: CoreRequirement = {
        artifacts: new Map<string, CoreMessageRuntime>(),
        bindings: [],
        messages: new Set(messages),
        owner: internal.definition.id,
        outputs: new Set<string>(),
        provider: internal.definition.id,
        renderedLocale: internal.state.context.locale,
      };
      await tree.fetchArtifact(requirement, internal.state.context.locale);
      dependencies.addRequirement(requirement);
    },
    resolve(message: string, values = {}, options = {}) {
      return resolvedLoaded(message, values, options.attr);
    },
    subscribe(callback: (context: TreeContext) => void) {
      if (typeof callback !== "function") fail("I18N_SUBSCRIBER_INVALID", "subscribe needs a callback.");
      internal.subscribers.add(callback);
      try {
        callback(internal.state.context);
      } catch (error) {
        dependencies.reportBindingError("subscriber", error);
      }
      return () => internal.subscribers.delete(callback);
    },
    async switchLocale(locale: string) {
      if (typeof locale !== "string" || !state.configuration?.locales.has(locale)) {
        fail("I18N_LOCALE_INVALID", `locale ${String(locale)} is not selectable.`);
      }
      const initiator = internal;
      const coordinator = dependencies.treeRoot(initiator);
      coordinator.switchGeneration += 1;
      const request = coordinator.switchGeneration;
      tree.planProviderSubtree(initiator, tree.rootSwitchContext(initiator, locale), request);
      for (const target of coordinator.plannedOwners.keys()) coordinator.plannedOwners.set(target, request);
      coordinator.generation += 1;
      for (const [target, owner] of coordinator.plannedOwners)
        if (owner === request) {
          target.state.status = Object.freeze({
            phase: "loading",
            target: coordinator.plannedContexts.get(target)!.locale,
          });
        }
      for (let attempt = 0; attempt < 32; attempt += 1) {
        const generation = coordinator.generation;
        const snapshot = tree.plannedTree(coordinator);
        let staged: Array<[CoreProviderNode, TreeContext]>;
        try {
          staged = await tree.stageTree(snapshot);
        } catch (error) {
          if (request !== coordinator.switchGeneration) return Object.freeze({ status: "stale" as const });
          if (!state.adapter.isAlive(initiator)) {
            tree.restoreFailedPlan(coordinator, request, initiator, error);
            return Object.freeze({ status: "stale" as const });
          }
          if (generation !== coordinator.generation) continue;
          tree.restoreFailedPlan(coordinator, request, initiator, error);
          throw error;
        }
        if (request !== coordinator.switchGeneration) return Object.freeze({ status: "stale" as const });
        if (!state.adapter.isAlive(initiator)) {
          tree.restoreFailedPlan(coordinator, request, initiator, new Error("the switching provider was removed"));
          return Object.freeze({ status: "stale" as const });
        }
        if (generation !== coordinator.generation) continue;
        const changed: Array<[CoreProviderNode, TreeContext]> = [];
        for (const [target, context] of staged) {
          state.adapter.commitContext(target, context);
          if (!dependencies.sameContext(target.state.context, context)) changed.push([target, context]);
          target.state.context = context;
          target.state.status = Object.freeze({ phase: "ready" });
        }
        coordinator.plannedContexts.clear();
        coordinator.plannedOwners.clear();
        for (const [target, context] of changed) {
          target.bindings.forEach((binding) => {
            try {
              binding.refresh();
            } catch (error) {
              dependencies.reportBindingError("provider-commit", error);
            }
          });
          target.subscribers.forEach((callback) => {
            try {
              callback(context);
            } catch (error) {
              dependencies.reportBindingError("subscriber", error);
            }
          });
        }
        return Object.freeze({ context: initiator.state.context, status: "committed" as const });
      }
      const error = new Error("the provider tree kept changing while its locale switch staged");
      tree.restoreFailedPlan(coordinator, request, initiator, error);
      throw error;
    },
    tr(message: string, values = {}, options = {}) {
      return formatLoaded(message, values, options.attr).text;
    },
  });
}

export interface TreeContext {
  readonly catalog_revision: string;
  readonly direction: "ltr" | "rtl";
  readonly fallback_locales: readonly string[];
  readonly formats_revision: string;
  readonly locale: string;
  readonly time_zone: string | null;
  readonly tzdb_revision: string;
}
export interface TreeDefinition {
  readonly id: string;
  readonly context: TreeContext;
  readonly policy: {
    readonly direction: { readonly mode: string; readonly value?: string };
    readonly locale: { readonly mode: string; readonly value?: string };
    readonly time_zone: { readonly mode: string; readonly value?: string };
  };
}
export interface TreeRequirement<Runtime = unknown> {
  readonly artifacts: Map<string, Runtime>;
  readonly messages: Set<string>;
  readonly outputs: Set<string>;
}
export interface ProviderTreeShape<Node> {
  readonly children: Set<Node>;
  readonly definition: TreeDefinition;
  readonly plannedContexts: Map<Node, TreeContext>;
  readonly plannedOwners: Map<Node, number>;
  readonly state: { context: TreeContext; status: Readonly<Record<string, unknown>> };
}
export interface ProviderTreeNode extends ProviderTreeShape<ProviderTreeNode> {}

export function createProviderTreeCore<
  Node extends ProviderTreeShape<Node>,
  Requirement extends TreeRequirement<Runtime>,
  Runtime,
>(
  state: {
    readonly adapter: { isAlive(provider: Node): boolean };
    readonly requirementsByProvider: Map<string, Set<Requirement>>;
    configuration: {
      catalogRevision: string;
      contexts: Map<string, TreeContext>;
      messagesUrl: string | null;
    } | null;
  },
  fail: Failure,
  treeRoot: (provider: Node) => Node,
  transport: {
    createMessageRuntime(value: unknown, locale: string): Runtime;
    fetch(input: string, init: RequestInit): Promise<Response>;
  },
) {
  function contextForLocale(locale: string): TreeContext {
    const context = state.configuration?.contexts.get(locale);
    if (context === undefined) fail("I18N_LOCALE_INVALID", `locale ${locale} is not selectable.`);
    return context;
  }
  function childContext(parent: TreeContext, definition: TreeDefinition): TreeContext {
    const locale = definition.policy.locale.mode === "explicit" ? definition.policy.locale.value! : parent.locale;
    const localeContext = contextForLocale(locale);
    const direction =
      definition.policy.direction.mode === "explicit"
        ? (definition.policy.direction.value as "ltr" | "rtl")
        : definition.policy.locale.mode === "explicit"
          ? localeContext.direction
          : parent.direction;
    const timeZone =
      definition.policy.time_zone.mode === "explicit"
        ? definition.policy.time_zone.value!
        : definition.policy.time_zone.mode === "clear"
          ? null
          : parent.time_zone;
    return Object.freeze({
      ...localeContext,
      direction,
      time_zone: timeZone,
      tzdb_revision: timeZone === null ? "none" : definition.context.tzdb_revision,
    });
  }
  function rootSwitchContext(internal: Node, locale: string): TreeContext {
    const localeContext = contextForLocale(locale);
    return Object.freeze({
      ...localeContext,
      direction:
        internal.definition.policy.direction.mode === "explicit"
          ? (internal.definition.policy.direction.value as "ltr" | "rtl")
          : localeContext.direction,
      time_zone: internal.state.context.time_zone,
      tzdb_revision: internal.state.context.tzdb_revision,
    });
  }
  function providerRequirements(internal: Node): Requirement[] {
    return Array.from(state.requirementsByProvider.get(internal.definition.id) ?? []);
  }
  function plannedTree(root: Node): Array<[Node, TreeContext]> {
    const planned: Array<[Node, TreeContext]> = [];
    function visit(internal: Node, inherited: TreeContext | null): void {
      const context =
        root.plannedContexts.get(internal) ??
        (inherited === null ? internal.state.context : childContext(inherited, internal.definition));
      planned.push([internal, context]);
      Array.from(internal.children).forEach((child) => {
        visit(child, context);
      });
    }
    visit(root, null);
    return planned;
  }
  function planProviderSubtree(internal: Node, context: TreeContext, owner: number): void {
    const coordinator = treeRoot(internal);
    function visit(target: Node, next: TreeContext): void {
      coordinator.plannedContexts.set(target, next);
      coordinator.plannedOwners.set(target, owner);
      Array.from(target.children).forEach((child) => {
        visit(child, childContext(next, child.definition));
      });
    }
    visit(internal, context);
  }
  function restoreFailedPlan(coordinator: Node, owner: number, initiator: Node, error: unknown): void {
    for (const [target, targetOwner] of coordinator.plannedOwners) {
      if (targetOwner !== owner) continue;
      coordinator.plannedOwners.delete(target);
      coordinator.plannedContexts.delete(target);
      target.state.status = Object.freeze({ phase: "ready" });
    }
    const code = error instanceof Error ? ((error as Error & { code?: string }).code ?? error.message) : String(error);
    if (state.adapter.isAlive(initiator)) initiator.state.status = Object.freeze({ error: code, phase: "error" });
  }
  async function fetchArtifact(requirement: Requirement, locale: string): Promise<Runtime> {
    const loaded = requirement.artifacts.get(locale);
    if (loaded !== undefined) return loaded;
    const url = state.configuration?.messagesUrl;
    if (url === null || url === undefined) {
      fail("I18N_MESSAGES_UNAVAILABLE", `static output has no ${locale} artifact for this message set.`);
    }
    const response = await transport.fetch(url, {
      body: JSON.stringify({
        catalog_revision: state.configuration!.catalogRevision,
        locale,
        messages: Array.from(requirement.messages),
        outputs: Array.from(requirement.outputs),
        schema_version: 1,
      }),
      headers: { "Content-Type": "application/json" },
      method: "POST",
    });
    if (!response.ok)
      fail("I18N_MESSAGES_UNAVAILABLE", `the ${locale} message request failed with ${response.status}.`);
    const runtime = transport.createMessageRuntime(await response.json(), locale);
    requirement.artifacts.set(locale, runtime);
    return runtime;
  }
  async function stageTree(planned: ReadonlyArray<readonly [Node, TreeContext]>): Promise<Array<[Node, TreeContext]>> {
    await Promise.all(
      planned.flatMap(([internal, context]) =>
        providerRequirements(internal).map((requirement) => fetchArtifact(requirement, context.locale)),
      ),
    );
    return planned.map(([internal, context]) => [internal, context]);
  }
  return Object.freeze({
    contextForLocale,
    childContext,
    rootSwitchContext,
    providerRequirements,
    plannedTree,
    planProviderSubtree,
    restoreFailedPlan,
    fetchArtifact,
    stageTree,
  });
}
export function createPureI18nHelpers(fail: Failure) {
  function prohibitedText(value: string): boolean {
    return Array.from(value).some((character) => BIDI_CONTROLS.has(character) || PARAGRAPH_BOUNDARIES.has(character));
  }

  function decimalInput(value: unknown, typeName: string): string {
    if (typeof value === "bigint") return value.toString();
    if (typeof value === "number") {
      if (Number.isInteger(value) && !Number.isSafeInteger(value)) {
        fail("I18N_ARGUMENT_INVALID", `a ${typeName} integer must be safe, a bigint, or a canonical decimal string.`);
      }
      if (!Number.isFinite(value)) fail("I18N_ARGUMENT_INVALID", "numeric message arguments must be finite.");
      const text = Object.is(value, -0) ? "-0" : String(value);
      if (typeName === "int" && !INTEGER_PATTERN.test(text)) {
        fail("I18N_ARGUMENT_INVALID", "an int argument must not contain a fraction.");
      }
      return text;
    }
    if (typeof value !== "string") fail("I18N_ARGUMENT_INVALID", `a ${typeName} argument needs a numeric value.`);
    const pattern = typeName === "int" ? INTEGER_PATTERN : DECIMAL_PATTERN;
    if (!pattern.test(value)) fail("I18N_ARGUMENT_INVALID", `a ${typeName} argument is not canonical.`);
    return value;
  }

  function formatExactNumber(locale: string, value: string): string {
    const fractionDigits = value.includes(".") ? value.length - value.indexOf(".") - 1 : 0;
    if (fractionDigits > 20) {
      fail("I18N_NUMBER_UNSUPPORTED", "browser NUMBER() supports at most 20 exact fraction digits.");
    }
    const formatter = new Intl.NumberFormat(locale, {
      maximumFractionDigits: fractionDigits,
      minimumFractionDigits: fractionDigits,
      useGrouping: true,
    }) as Intl.NumberFormat & { format(value: string): string };
    return formatter.format(value);
  }

  function numericParseResult(
    input: string,
    state: NumericParseState,
    error: string | null,
    value: string | null = null,
  ): NumericParseResult {
    return Object.freeze({ error, input, state, valid: state === "valid", value });
  }

  function codePointLength(value: string): number {
    return Array.from(value).length;
  }

  function stripSign(input: string, prefix: string, suffix: string): string | null {
    if (prefix.length === 0 && suffix.length === 0) return null;
    if (!input.startsWith(prefix) || !input.endsWith(suffix)) return null;
    return input.slice(prefix.length, input.length - suffix.length);
  }

  function parsePlainNumber(input: string, record: BrowserNumberParserRecord): NumericParseResult {
    if (input.length === 0) return numericParseResult(input, "incomplete", "empty");
    if (input.trim() !== input) return numericParseResult(input, "invalid", "whitespace");
    let negative = false;
    let unsigned = stripSign(input, record.minus_prefix, record.minus_suffix);
    if (unsigned !== null) {
      negative = true;
    } else {
      unsigned = stripSign(input, record.plus_prefix, record.plus_suffix);
      if (unsigned === null && input.startsWith("-")) {
        negative = true;
        unsigned = input.slice(1);
      } else if (unsigned === null && input.startsWith("+")) {
        unsigned = input.slice(1);
      } else if (unsigned === null) {
        unsigned = input;
      }
    }
    if (unsigned.length === 0) return numericParseResult(input, "incomplete", "sign_without_digits");

    const firstDecimal = unsigned.indexOf(record.decimal);
    if (firstDecimal >= 0 && unsigned.indexOf(record.decimal, firstDecimal + record.decimal.length) >= 0) {
      return numericParseResult(input, "invalid", "multiple_decimal_separators");
    }
    const integer = firstDecimal < 0 ? unsigned : unsigned.slice(0, firstDecimal);
    const fraction = firstDecimal < 0 ? null : unsigned.slice(firstDecimal + record.decimal.length);
    if (integer.length === 0) return numericParseResult(input, "incomplete", "missing_integer_digits");
    if (fraction === "") return numericParseResult(input, "incomplete", "missing_fraction_digits");

    const groups = integer.split(record.grouping);
    if (groups.some((group) => group.length === 0)) {
      return groups[groups.length - 1] === ""
        ? numericParseResult(input, "incomplete", "unfinished_group")
        : numericParseResult(input, "invalid", "empty_group");
    }
    if (groups.length > 1) {
      if (record.primary_group === 0 || record.secondary_group === 0) {
        return numericParseResult(input, "invalid", "grouping_not_allowed");
      }
      const finalCount = codePointLength(groups[groups.length - 1]);
      if (finalCount < record.primary_group) return numericParseResult(input, "incomplete", "unfinished_group");
      if (finalCount > record.primary_group) return numericParseResult(input, "invalid", "wrong_primary_group");
      if (groups.slice(1, -1).some((group) => codePointLength(group) !== record.secondary_group)) {
        return numericParseResult(input, "invalid", "wrong_secondary_group");
      }
      const leading = codePointLength(groups[0]);
      if (leading === 0 || leading > record.secondary_group) {
        return numericParseResult(input, "invalid", "wrong_leading_group");
      }
    }

    const digitMap = new Map(record.digits.map((digit, index) => [digit, String(index)]));
    let canonical = negative ? "-" : "";
    for (const character of Array.from(groups.join(""))) {
      const digit = digitMap.get(character);
      if (digit === undefined) return numericParseResult(input, "invalid", "foreign_or_invalid_digit");
      canonical += digit;
    }
    if (fraction !== null) {
      if (fraction.includes(record.grouping)) return numericParseResult(input, "invalid", "grouping_in_fraction");
      canonical += ".";
      for (const character of Array.from(fraction)) {
        const digit = digitMap.get(character);
        if (digit === undefined) return numericParseResult(input, "invalid", "foreign_or_invalid_digit");
        canonical += digit;
      }
    }
    if (canonical.length > 32_768) return numericParseResult(input, "invalid", "number_out_of_range");
    return numericParseResult(input, "valid", null, canonical);
  }

  function shiftExactDecimal(value: string, power: number): string | null {
    const negative = value.startsWith("-");
    const unsigned = negative ? value.slice(1) : value;
    const [integer, fraction = ""] = unsigned.split(".");
    let digits = `${integer}${fraction}`;
    let point = integer.length + power;
    if (point <= 0) {
      digits = `${"0".repeat(-point)}${digits}`;
      point = 0;
    } else if (point >= digits.length) {
      digits = `${digits}${"0".repeat(point - digits.length)}`;
      point = digits.length;
    }
    if (digits.length > 32_768) return null;
    const rendered =
      point === 0
        ? `0.${digits}`
        : point === digits.length
          ? digits
          : `${digits.slice(0, point)}.${digits.slice(point)}`;
    const [rawInteger, rawFraction] = rendered.split(".");
    const normalizedInteger = rawInteger.replace(/^0+(?=\d)/, "");
    const normalized = rawFraction === undefined ? normalizedInteger : `${normalizedInteger}.${rawFraction}`;
    return negative && /[1-9]/.test(digits) ? `-${normalized}` : normalized;
  }

  function parseNumber(input: string, record: BrowserNumberParserRecord): NumericParseResult {
    if (record.notation === "decimal") return parsePlainNumber(input, record);
    const separators = Array.from(input.matchAll(/[eE]/g));
    if (separators.length === 0) return parsePlainNumber(input, record);
    if (separators.length > 1) return numericParseResult(input, "invalid", "multiple_exponents");
    const separator = separators[0].index!;
    const significand = parsePlainNumber(input.slice(0, separator), record);
    if (!significand.valid) return Object.freeze({ ...significand, input });
    let exponentInput = input.slice(separator + 1);
    if (exponentInput.length === 0) return numericParseResult(input, "incomplete", "missing_exponent_digits");
    let negative = false;
    if (exponentInput.startsWith("-")) {
      negative = true;
      exponentInput = exponentInput.slice(1);
    } else if (exponentInput.startsWith("+")) {
      exponentInput = exponentInput.slice(1);
    }
    if (exponentInput.length === 0) return numericParseResult(input, "incomplete", "missing_exponent_digits");
    const digitMap = new Map(record.digits.map((digit, index) => [digit, String(index)]));
    let ascii = "";
    for (const character of Array.from(exponentInput)) {
      const digit = digitMap.get(character);
      if (digit === undefined) {
        return numericParseResult(input, "invalid", "foreign_or_invalid_exponent_digit");
      }
      ascii += digit;
    }
    if (ascii.length > 5) return numericParseResult(input, "invalid", "exponent_out_of_range");
    const absolute = Number(ascii);
    const exponent = negative ? -absolute : absolute;
    if (!Number.isInteger(exponent) || exponent < -32_768 || exponent > 32_767) {
      return numericParseResult(input, "invalid", "exponent_out_of_range");
    }
    const shifted = shiftExactDecimal(significand.value!, exponent);
    return shifted === null
      ? numericParseResult(input, "invalid", "number_out_of_range")
      : numericParseResult(input, "valid", null, shifted);
  }

  function normalizedDecimal(value: string): string {
    const negative = value.startsWith("-");
    const unsigned = negative ? value.slice(1) : value;
    const [integer, fraction = ""] = unsigned.split(".");
    const normalizedFraction = fraction.replace(/0+$/, "");
    const magnitude = normalizedFraction.length === 0 ? integer : `${integer}.${normalizedFraction}`;
    return /^0(?:\.0*)?$/.test(magnitude) ? "0" : `${negative ? "-" : ""}${magnitude}`;
  }

  function pluralInput(value: string): number {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) {
      fail("I18N_PLURAL_UNSUPPORTED", "browser plural selection cannot preserve this exact decimal.");
    }
    if (INTEGER_PATTERN.test(value)) {
      if (!Number.isSafeInteger(numeric)) {
        fail("I18N_PLURAL_UNSUPPORTED", "browser plural selection requires a safe integer.");
      }
      return numeric;
    }
    if (value.endsWith("0") || String(numeric) !== value) {
      fail("I18N_PLURAL_UNSUPPORTED", "browser Intl.PluralRules cannot preserve this decimal's exact visible digits.");
    }
    return numeric;
  }

  return Object.freeze({
    prohibitedText,
    decimalInput,
    formatExactNumber,
    numericParseResult,
    parsePlainNumber,
    shiftExactDecimal,
    parseNumber,
    normalizedDecimal,
    pluralInput,
  });
}
