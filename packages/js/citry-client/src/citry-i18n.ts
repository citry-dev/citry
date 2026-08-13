/**
 * Citry's opt-in browser i18n runtime.
 *
 * Ordinary server-rendered `tr()` output is intentionally unbound. Explicit
 * `$i18n` expressions, checked `$c-tr` markers, and `i18n.bind()` registrations
 * react to provider locale changes.
 */

import { FluentBundle, FluentResource, type FluentFunction, type FluentValue } from "@fluent/bundle";

const SERVICE_KEY = "citry_i18n";
const MANIFEST_SELECTOR = 'script[type="application/json"][data-citry-i18n]';
const FSI = "\u2068";
const PDI = "\u2069";
const BIDI_CONTROLS = new Set(Array.from("\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"));
const PARAGRAPH_BOUNDARIES = new Set(Array.from("\r\n\u001c\u001d\u001e\u0085\u2029"));
const DECIMAL_PATTERN = /^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$/;
const INTEGER_PATTERN = /^-?(?:0|[1-9][0-9]*)$/;
const PARAMETER_TYPES = new Set(["Decimal", "Slot", "datetime", "int", "scalar", "str"]);
const BINDING_ATTRIBUTE_TARGETS = new Set([
  "alt",
  "aria-description",
  "aria-label",
  "aria-placeholder",
  "aria-roledescription",
  "aria-valuetext",
  "placeholder",
  "title",
]);

type Direction = "ltr" | "rtl";
type PolicyMode = "clear" | "explicit" | "inherit";

interface LocaleContext {
  readonly catalog_revision: string;
  readonly direction: Direction;
  readonly fallback_locales: readonly string[];
  readonly formats_revision: string;
  readonly locale: string;
  readonly time_zone: string | null;
  readonly tzdb_revision: string;
}

interface FieldPolicy {
  readonly mode: PolicyMode;
  readonly value?: string;
}

interface ProviderDefinition {
  readonly context: LocaleContext;
  readonly id: string;
  readonly parent: string | null;
  readonly policy: {
    readonly direction: FieldPolicy;
    readonly locale: FieldPolicy;
    readonly time_zone: FieldPolicy;
  };
}

interface BrowserMessageEntry {
  readonly bundle_locale: string;
  readonly contract: Readonly<Record<string, string>>;
  readonly internal_id: string;
}

interface BrowserArtifact {
  readonly bundles: Readonly<Record<string, string>>;
  readonly catalog_revision: string;
  readonly formats_revision: string;
  readonly messages: Readonly<Record<string, BrowserMessageEntry>>;
  readonly requested_locale: string;
  readonly revision: string;
  readonly runtime: string;
  readonly schema_version: number;
}

interface RequirementRecord {
  readonly artifacts: Readonly<Record<string, unknown>>;
  readonly bindings: readonly unknown[];
  readonly messages: readonly string[];
  readonly owner: string;
  readonly outputs: readonly string[];
  readonly provider: string;
  readonly rendered_locale: string;
}

interface BindingTarget {
  readonly kind: "attribute" | "text";
  readonly name?: string;
}

interface BindingDefinition {
  readonly id: string;
  readonly message: string;
  readonly output?: string;
  readonly provider: string;
  readonly renderedLocale: string;
  readonly target: BindingTarget;
  readonly values: Readonly<Record<string, unknown>>;
  readonly valuesExpression?: string;
}

interface I18nManifest {
  readonly catalog_revision: string;
  readonly contexts: Readonly<Record<string, LocaleContext>>;
  readonly formats: Readonly<Record<string, Readonly<Record<string, unknown>>>>;
  readonly formats_revision: string;
  readonly locales: readonly string[];
  readonly messages_url: string | null;
  readonly parsers: Readonly<Record<string, BrowserParserArtifact>>;
  readonly providers: readonly ProviderDefinition[];
  readonly requirements: readonly RequirementRecord[];
  readonly runtime: string;
  readonly schema_version: number;
}

interface AlpineRuntime {
  directive(name: string, callback: (element: Element) => void): { before(other: string): void };
  effect(callback: () => void): object;
  evaluate(element: Element, expression: string): unknown;
  onElRemoved(element: Element, callback: () => void): void;
  reactive<T extends object>(value: T): T;
  release(effectReference: object): void;
}

interface ComponentContext {
  i18n?: I18nService | null;
  inject(key: string, defaultValue?: unknown): unknown;
}

interface ResolvedMessage {
  readonly direction: Direction;
  readonly locale: string;
  readonly text: string;
  readonly usedFallback: boolean;
}

interface CitryBrowser {
  alpine: {
    _magic(name: string, provider: (element: Element) => unknown): () => void;
    _register(options: {
      init?: (element: Element) => void;
      mutations?: (mutations: MutationRecord[]) => void;
    }): () => void;
    beforeStart(callback: (alpine: AlpineRuntime) => void): void;
  };
  i18n?: Readonly<{
    provider(element: Element, parent: I18nService | null): I18nService;
  }>;
  manager: {
    decorateContext(callback: (context: ComponentContext) => void): () => void;
    registerFrameworkManifest(
      name: string,
      handler: {
        commit(token: unknown, element: Element): void;
        match(element: Element): boolean;
        prepare(
          element: Element,
          options: {
            readonly acceptedOwners?: ReadonlySet<string> | null;
            readonly candidateRoot?: ParentNode | null;
          } | null,
        ): Promise<unknown> | unknown;
        rollback(token: unknown, element: Element, error: unknown): void;
      },
    ): () => void;
  };
}

interface I18nService {
  readonly context: LocaleContext;
  readonly format: I18nFormatter;
  readonly parse: I18nParser;
  readonly status: Readonly<Record<string, unknown>>;
  ensureMessages(messages: string | readonly string[]): Promise<void>;
  bind(options: {
    readonly message: string;
    readonly onChange: (text: string, resolved: ResolvedMessage) => void;
    readonly output?: string;
    readonly values?: () => Readonly<Record<string, unknown>>;
  }): Readonly<{ dispose(): void; refresh(): void }>;
  resolve(
    message: string,
    values?: Readonly<Record<string, unknown>>,
    options?: { readonly attr?: string },
  ): Readonly<ResolvedMessage>;
  subscribe(callback: (context: LocaleContext) => void): () => void;
  switchLocale(locale: string): Promise<Readonly<{ context?: LocaleContext; status: "committed" | "stale" }>>;
  tr(message: string, values?: Readonly<Record<string, unknown>>, options?: { readonly attr?: string }): string;
}

interface FormatOptions {
  readonly format: string;
}

interface DateFields {
  readonly day: number;
  readonly month: number;
  readonly year: number;
}

interface TimeFields {
  readonly hour: number;
  readonly millisecond?: number;
  readonly minute: number;
  readonly second?: number;
}

interface I18nFormatter {
  currency(value: unknown, currency: string, options: FormatOptions): string;
  date(value: DateFields, options: FormatOptions): string;
  datetime(value: Date, options: FormatOptions): string;
  list(values: readonly string[], options: FormatOptions): string;
  number(value: unknown, options: FormatOptions): string;
  percent(value: unknown, options: FormatOptions): string;
  relativeTime(value: unknown, options: FormatOptions & { readonly unit: string }): string;
  time(value: TimeFields, options: FormatOptions): string;
  unit(value: unknown, unit: string, options: FormatOptions): string;
}

type NumericParseState = "incomplete" | "invalid" | "valid";

interface NumericParseResult {
  readonly error: string | null;
  readonly input: string;
  readonly state: NumericParseState;
  readonly valid: boolean;
  readonly value: string | null;
}

interface BrowserNumberParserRecord {
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

interface BrowserPercentParserRecord {
  readonly affix: "omit" | "required";
  readonly numbers: BrowserNumberParserRecord;
  readonly patterns: readonly {
    readonly negative: boolean;
    readonly prefix: string;
    readonly suffix: string;
  }[];
}

interface BrowserParserArtifact {
  readonly formats_revision: string;
  readonly locale: string;
  readonly number: Readonly<Record<string, BrowserNumberParserRecord>>;
  readonly percent: Readonly<Record<string, BrowserPercentParserRecord>>;
  readonly revision: string;
  readonly schema_version: number;
}

interface I18nParser {
  number(input: string, options: FormatOptions): NumericParseResult;
  percent(input: string, options: FormatOptions): NumericParseResult;
}

interface MessageRuntime {
  readonly artifact: BrowserArtifact;
  format(token: string, values: Readonly<Record<string, unknown>>): string;
}

interface Requirement {
  readonly artifacts: Map<string, MessageRuntime>;
  readonly bindings: readonly BindingDefinition[];
  readonly messages: Set<string>;
  readonly owner: string;
  readonly outputs: Set<string>;
  readonly provider: string;
  readonly renderedLocale: string;
}

interface ActiveBinding {
  disposed: boolean;
  refresh(): void;
}

interface ProviderInternal {
  readonly bindings: Set<ActiveBinding>;
  readonly children: Set<ProviderInternal>;
  readonly definition: ProviderDefinition;
  generation: number;
  parent: ProviderInternal | null;
  readonly plannedContexts: Map<ProviderInternal, LocaleContext>;
  readonly plannedOwners: Map<ProviderInternal, number>;
  readonly service: I18nService;
  readonly state: {
    context: LocaleContext;
    status: Readonly<Record<string, unknown>>;
  };
  readonly subscribers: Set<(context: LocaleContext) => void>;
  switchGeneration: number;
  readonly wrapper: HTMLElement;
}

interface RuntimeConfiguration {
  catalogRevision: string;
  contexts: Map<string, LocaleContext>;
  formats: Readonly<Record<string, Readonly<Record<string, unknown>>>>;
  formatsRevision: string;
  locales: Set<string>;
  messagesUrl: string | null;
  parsers: Map<string, BrowserParserArtifact>;
}

const globalValue = globalThis as unknown as { Citry?: CitryBrowser };
const citry = globalValue.Citry;
if (!citry?.alpine || !citry.manager) {
  throw new Error("[Citry] i18n runtime needs the Citry dependency manager before it loads.");
}

let alpine: AlpineRuntime | null = null;
let configuration: RuntimeConfiguration | null = null;
let activeFluentFailures: Array<TypeError & { code?: string }> | null = null;
const definitions = new Map<string, ProviderDefinition>();
const requirementsByProvider = new Map<string, Set<Requirement>>();
const bindingDefinitions = new Map<string, BindingDefinition>();
const bindingReferenceCounts = new Map<string, number>();
const manifestRequirements = new WeakMap<Element, Requirement[]>();
const manifestDefinitions = new WeakMap<Element, ProviderDefinition[]>();
const processedManifests = new WeakSet<Element>();
const activeManifests = new WeakSet<Element>();
const mountedProviders = new Map<string, ProviderInternal>();
const internals = new WeakMap<I18nService, ProviderInternal>();

function fail(code: string, message: string): never {
  const error = new TypeError(`[Citry] i18n: ${message}`) as TypeError & { code?: string };
  error.code = code;
  activeFluentFailures?.push(error);
  throw error;
}

function exactObject(value: unknown, name: string): Record<string, unknown> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    fail("I18N_WIRE_INVALID", `${name} must be an object.`);
  }
  return value as Record<string, unknown>;
}

function exactKeys(value: Record<string, unknown>, expected: readonly string[], name: string): void {
  const actual = Object.keys(value).sort();
  const sortedExpected = [...expected].sort();
  if (actual.length !== sortedExpected.length || actual.some((key, index) => key !== sortedExpected[index])) {
    fail("I18N_WIRE_INVALID", `${name} has unknown or missing fields.`);
  }
}

function exactString(value: unknown, name: string): string {
  if (typeof value !== "string" || value.length === 0) {
    fail("I18N_WIRE_INVALID", `${name} must be a non-empty string.`);
  }
  return value;
}

function stringList(value: unknown, name: string): string[] {
  if (!Array.isArray(value) || value.some((item) => typeof item !== "string" || item.length === 0)) {
    fail("I18N_WIRE_INVALID", `${name} must be a list of non-empty strings.`);
  }
  if (new Set(value).size !== value.length) fail("I18N_WIRE_INVALID", `${name} contains duplicates.`);
  return value as string[];
}

function immutableContext(value: unknown, name: string): LocaleContext {
  const item = exactObject(value, name);
  exactKeys(
    item,
    ["catalog_revision", "direction", "fallback_locales", "formats_revision", "locale", "time_zone", "tzdb_revision"],
    name,
  );
  const direction = item.direction;
  if (direction !== "ltr" && direction !== "rtl") fail("I18N_WIRE_INVALID", `${name}.direction is invalid.`);
  const timeZone = item.time_zone;
  if (timeZone !== null && (typeof timeZone !== "string" || timeZone.length === 0)) {
    fail("I18N_WIRE_INVALID", `${name}.time_zone must be null or a non-empty string.`);
  }
  return Object.freeze({
    catalog_revision: exactString(item.catalog_revision, `${name}.catalog_revision`),
    direction,
    fallback_locales: Object.freeze(stringList(item.fallback_locales, `${name}.fallback_locales`)),
    formats_revision: exactString(item.formats_revision, `${name}.formats_revision`),
    locale: exactString(item.locale, `${name}.locale`),
    time_zone: timeZone as string | null,
    tzdb_revision: exactString(item.tzdb_revision, `${name}.tzdb_revision`),
  });
}

function fieldPolicy(value: unknown, name: string, allowClear: boolean): FieldPolicy {
  const item = exactObject(value, name);
  const mode = item.mode;
  if (mode !== "inherit" && mode !== "explicit" && (!allowClear || mode !== "clear")) {
    fail("I18N_WIRE_INVALID", `${name}.mode is invalid.`);
  }
  exactKeys(item, mode === "explicit" ? ["mode", "value"] : ["mode"], name);
  return Object.freeze(
    mode === "explicit" ? { mode, value: exactString(item.value, `${name}.value`) } : { mode },
  ) as FieldPolicy;
}

function providerDefinition(value: unknown): ProviderDefinition {
  const item = exactObject(value, "an i18n provider");
  exactKeys(item, ["context", "id", "parent", "policy"], "an i18n provider");
  const parent = item.parent;
  if (parent !== null && (typeof parent !== "string" || parent.length === 0)) {
    fail("I18N_WIRE_INVALID", "an i18n provider parent must be null or a render ID.");
  }
  const policy = exactObject(item.policy, "an i18n provider policy");
  exactKeys(policy, ["direction", "locale", "time_zone"], "an i18n provider policy");
  return Object.freeze({
    context: immutableContext(item.context, "an i18n provider context"),
    id: exactString(item.id, "an i18n provider id"),
    parent: parent as string | null,
    policy: Object.freeze({
      direction: fieldPolicy(policy.direction, "an i18n direction policy", false),
      locale: fieldPolicy(policy.locale, "an i18n locale policy", false),
      time_zone: fieldPolicy(policy.time_zone, "an i18n time-zone policy", true),
    }),
  });
}

function native(value: unknown): unknown {
  if (value !== null && typeof value === "object" && "valueOf" in value) {
    const method = (value as { valueOf(): unknown }).valueOf;
    if (typeof method === "function") return method.call(value);
  }
  return value;
}

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

function argumentValue(name: string, typeName: string, value: unknown): string {
  let result: string;
  if (typeName === "str") {
    if (typeof value !== "string") fail("I18N_ARGUMENT_INVALID", `$${name} must be a string.`);
    result = value;
  } else if (typeName === "int" || typeName === "Decimal") {
    result = decimalInput(value, typeName);
  } else if (typeName === "scalar") {
    result = typeof value === "string" ? value : decimalInput(value, "Decimal");
  } else if (typeName === "datetime") {
    if (!(value instanceof Date) || !Number.isFinite(value.valueOf())) {
      fail("I18N_ARGUMENT_INVALID", `$${name} must be a valid Date.`);
    }
    result = value.toISOString();
  } else if (typeName === "Slot") {
    fail("I18N_ARGUMENT_INVALID", `$${name} is a Slot and must be rendered through <c-trans>.`);
  } else {
    fail("I18N_ARGUMENT_INVALID", `$${name} has unsupported type ${typeName}.`);
  }
  if (prohibitedText(result)) fail("I18N_ARGUMENT_INVALID", `$${name} contains a prohibited bidi boundary.`);
  return result;
}

function exactArguments(
  contract: Readonly<Record<string, string>>,
  rawValues: Readonly<Record<string, unknown>>,
): Record<string, string> {
  const expected = Object.keys(contract).sort();
  const actual = Object.keys(rawValues).sort();
  if (expected.length !== actual.length || expected.some((name, index) => name !== actual[index])) {
    fail("I18N_ARGUMENT_INVALID", `message arguments must be exactly: ${expected.join(", ") || "(none)"}.`);
  }
  return Object.fromEntries(expected.map((name) => [name, argumentValue(name, contract[name], rawValues[name])]));
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

function formatOptions(value: unknown, name: string): FormatOptions {
  const item = exactObject(value, `${name} options`);
  exactKeys(item, ["format"], `${name} options`);
  return Object.freeze({ format: exactString(item.format, `${name} format`) });
}

function profile(kind: string, name: string): Record<string, unknown> {
  const category = configuration?.formats[kind];
  const value = category?.[name];
  if (value === undefined) fail("I18N_FORMAT_INVALID", `unknown ${kind} format ${name}.`);
  return exactObject(value, `${kind} format ${name}`);
}

function exactNumberFormatter(locale: string, options: Intl.NumberFormatOptions): Intl.NumberFormat {
  return new Intl.NumberFormat(locale, options);
}

function formatIntlNumber(locale: string, value: unknown, options: Intl.NumberFormatOptions, kind: string): string {
  const decimal = decimalInput(value, "Decimal");
  const fractionDigits = decimal.includes(".") ? decimal.length - decimal.indexOf(".") - 1 : 0;
  if (fractionDigits > 20) {
    fail("I18N_FORMAT_UNSUPPORTED", `browser ${kind} formatting supports at most 20 exact fraction digits.`);
  }
  const displayedFractionDigits =
    kind === "number" || kind === "unit" ? fractionDigits : kind === "percent" ? Math.max(0, fractionDigits - 2) : null;
  const formatter = exactNumberFormatter(locale, {
    ...options,
    ...(displayedFractionDigits === null
      ? {}
      : {
          maximumFractionDigits: displayedFractionDigits,
          minimumFractionDigits: displayedFractionDigits,
        }),
  }) as Intl.NumberFormat & { format(value: string): string };
  return formatter.format(decimal);
}

function integerField(value: unknown, name: string, minimum: number, maximum: number): number {
  if (typeof value !== "number" || !Number.isInteger(value) || value < minimum || value > maximum) {
    fail("I18N_FORMAT_INVALID", `${name} must be an integer from ${minimum} through ${maximum}.`);
  }
  return value;
}

function dateValue(value: unknown): Date {
  const item = exactObject(value, "date fields");
  exactKeys(item, ["day", "month", "year"], "date fields");
  const year = integerField(item.year, "date year", 1, 9999);
  const month = integerField(item.month, "date month", 1, 12);
  const day = integerField(item.day, "date day", 1, 31);
  const result = new Date(0);
  result.setUTCHours(12, 0, 0, 0);
  result.setUTCFullYear(year, month - 1, day);
  if (result.getUTCFullYear() !== year || result.getUTCMonth() !== month - 1 || result.getUTCDate() !== day) {
    fail("I18N_FORMAT_INVALID", "date fields do not form a real ISO calendar date.");
  }
  return result;
}

function timeValue(value: unknown): Date {
  const item = exactObject(value, "time fields");
  const keys = Object.keys(item).sort();
  if (
    keys.some((key) => !["hour", "millisecond", "minute", "second"].includes(key)) ||
    !keys.includes("hour") ||
    !keys.includes("minute")
  ) {
    fail("I18N_FORMAT_INVALID", "time fields need hour and minute and may add second and millisecond.");
  }
  const hour = integerField(item.hour, "time hour", 0, 23);
  const minute = integerField(item.minute, "time minute", 0, 59);
  const second = integerField(item.second ?? 0, "time second", 0, 59);
  const millisecond = integerField(item.millisecond ?? 0, "time millisecond", 0, 999);
  return new Date(Date.UTC(1970, 0, 1, hour, minute, second, millisecond));
}

function dateTimeOptions(length: unknown): Intl.DateTimeFormatOptions {
  if (length !== "short" && length !== "medium" && length !== "long") {
    fail("I18N_FORMAT_INVALID", "a temporal profile has an invalid length.");
  }
  if (length === "short") return { day: "numeric", month: "numeric", year: "2-digit" };
  if (length === "medium") return { day: "numeric", month: "short", year: "numeric" };
  return { day: "numeric", month: "long", year: "numeric" };
}

function wallTimeOptions(length: unknown): Intl.DateTimeFormatOptions {
  if (length !== "short" && length !== "medium" && length !== "long") {
    fail("I18N_FORMAT_INVALID", "a temporal profile has an invalid length.");
  }
  return { hour: "numeric", minute: "2-digit", second: "2-digit" };
}

function createFormatter(internal: Omit<ProviderInternal, "service">): I18nFormatter {
  function locale(): string {
    return internal.state.context.locale;
  }

  return Object.freeze({
    currency(value: unknown, currency: string, rawOptions: FormatOptions): string {
      const options = formatOptions(rawOptions, "currency");
      const spec = profile("currency", options.format);
      exactKeys(spec, [], `currency format ${options.format}`);
      if (!/^[A-Z]{3}$/.test(currency)) {
        fail("I18N_FORMAT_INVALID", "currency must be exactly three uppercase ASCII letters.");
      }
      return formatIntlNumber(locale(), value, { currency, style: "currency" }, "currency");
    },
    date(value: DateFields, rawOptions: FormatOptions): string {
      const options = formatOptions(rawOptions, "date");
      const spec = profile("date", options.format);
      return new Intl.DateTimeFormat(locale(), { ...dateTimeOptions(spec.length), timeZone: "UTC" }).format(
        dateValue(value),
      );
    },
    datetime(value: Date, rawOptions: FormatOptions): string {
      const options = formatOptions(rawOptions, "datetime");
      const spec = profile("datetime", options.format);
      if (!(value instanceof Date) || !Number.isFinite(value.valueOf())) {
        fail("I18N_FORMAT_INVALID", "datetime needs a valid JavaScript Date instant.");
      }
      const timeZone = internal.state.context.time_zone;
      if (timeZone === null) fail("I18N_FORMAT_INVALID", "datetime needs time_zone in the active i18n context.");
      const timeZoneName = spec.time_zone_name;
      if (timeZoneName !== "none" && timeZoneName !== "short" && timeZoneName !== "long") {
        fail("I18N_FORMAT_INVALID", "a datetime profile has an invalid time_zone_name.");
      }
      return new Intl.DateTimeFormat(locale(), {
        ...dateTimeOptions(spec.length),
        ...wallTimeOptions(spec.length),
        timeZone,
        ...(timeZoneName === "none" ? {} : { timeZoneName }),
      }).format(value);
    },
    list(values: readonly string[], rawOptions: FormatOptions): string {
      const options = formatOptions(rawOptions, "list");
      const spec = profile("list", options.format);
      if (!Array.isArray(values) || values.some((value) => typeof value !== "string")) {
        fail("I18N_FORMAT_INVALID", "list formatting needs an array of strings.");
      }
      if (values.some((value) => value.length === 0 || prohibitedText(value))) {
        fail("I18N_FORMAT_INVALID", "list items must be non-empty and contain no bidi or paragraph controls.");
      }
      const type = spec.kind === "and" ? "conjunction" : spec.kind === "or" ? "disjunction" : null;
      const style = spec.length === "wide" ? "long" : spec.length;
      if (type === null || (style !== "long" && style !== "short" && style !== "narrow")) {
        fail("I18N_FORMAT_INVALID", "a list profile is invalid.");
      }
      return new Intl.ListFormat(locale(), { style, type }).format(values.map((value) => `${FSI}${value}${PDI}`));
    },
    number(value: unknown, rawOptions: FormatOptions): string {
      const options = formatOptions(rawOptions, "number");
      profile("number", options.format);
      return formatIntlNumber(locale(), value, {}, "number");
    },
    percent(value: unknown, rawOptions: FormatOptions): string {
      const options = formatOptions(rawOptions, "percent");
      profile("percent", options.format);
      return formatIntlNumber(locale(), value, { style: "percent" }, "percent");
    },
    relativeTime(value: unknown, rawOptions: FormatOptions & { readonly unit: string }): string {
      const item = exactObject(rawOptions, "relative time options");
      exactKeys(item, ["format", "unit"], "relative time options");
      const format = exactString(item.format, "relative time format");
      const unit = exactString(item.unit, "relative time unit");
      const spec = profile("relative_time", format);
      if (unit !== "day" || spec.unit !== "day") {
        fail("I18N_FORMAT_INVALID", "relative time currently supports only unit day.");
      }
      const decimal = decimalInput(value, "Decimal");
      const numeric = pluralInput(decimal);
      return new Intl.RelativeTimeFormat(locale(), { numeric: "always", style: "long" }).format(numeric, "day");
    },
    time(value: TimeFields, rawOptions: FormatOptions): string {
      const options = formatOptions(rawOptions, "time");
      const spec = profile("time", options.format);
      return new Intl.DateTimeFormat(locale(), { ...wallTimeOptions(spec.length), timeZone: "UTC" }).format(
        timeValue(value),
      );
    },
    unit(value: unknown, unit: string, rawOptions: FormatOptions): string {
      const options = formatOptions(rawOptions, "unit");
      const spec = profile("unit", options.format);
      if (typeof unit !== "string" || unit.length === 0) fail("I18N_FORMAT_INVALID", "unit must be a string.");
      const unitDisplay = spec.width;
      if (unitDisplay !== "long" && unitDisplay !== "short" && unitDisplay !== "narrow") {
        fail("I18N_FORMAT_INVALID", "a unit profile has an invalid width.");
      }
      const decimal = decimalInput(value, "Decimal");
      const numeric = Number(decimal);
      if (!Number.isFinite(numeric) || normalizedDecimal(String(numeric)) !== normalizedDecimal(decimal)) {
        fail(
          "I18N_FORMAT_UNSUPPORTED",
          "browser unit formatting cannot preserve this exact value for plural selection.",
        );
      }
      return formatIntlNumber(locale(), decimal, { style: "unit", unit, unitDisplay }, "unit");
    },
  });
}

function numberParserRecord(value: unknown, name: string): BrowserNumberParserRecord {
  const item = exactObject(value, name);
  exactKeys(
    item,
    [
      "decimal",
      "digits",
      "grouping",
      "minus_prefix",
      "minus_suffix",
      "notation",
      "plus_prefix",
      "plus_suffix",
      "primary_group",
      "secondary_group",
    ],
    name,
  );
  const digits = item.digits;
  if (
    !Array.isArray(digits) ||
    digits.length !== 10 ||
    digits.some((digit) => typeof digit !== "string" || Array.from(digit).length !== 1) ||
    new Set(digits).size !== 10
  ) {
    fail("I18N_WIRE_INVALID", `${name}.digits must contain ten distinct Unicode characters.`);
  }
  const notation = item.notation;
  if (notation !== "decimal" && notation !== "decimal_or_scientific") {
    fail("I18N_WIRE_INVALID", `${name}.notation is invalid.`);
  }
  const primaryGroup = item.primary_group;
  const secondaryGroup = item.secondary_group;
  if (
    typeof primaryGroup !== "number" ||
    !Number.isInteger(primaryGroup) ||
    primaryGroup < 0 ||
    primaryGroup > 32 ||
    typeof secondaryGroup !== "number" ||
    !Number.isInteger(secondaryGroup) ||
    secondaryGroup < 0 ||
    secondaryGroup > 32
  ) {
    fail("I18N_WIRE_INVALID", `${name} has invalid grouping sizes.`);
  }
  const decimal = exactString(item.decimal, `${name}.decimal`);
  const grouping = exactString(item.grouping, `${name}.grouping`);
  if (decimal === grouping) fail("I18N_WIRE_INVALID", `${name} reuses one decimal and grouping separator.`);
  for (const field of ["minus_prefix", "minus_suffix", "plus_prefix", "plus_suffix"] as const) {
    if (typeof item[field] !== "string") fail("I18N_WIRE_INVALID", `${name}.${field} must be a string.`);
  }
  return Object.freeze({
    decimal,
    digits: Object.freeze([...(digits as string[])]),
    grouping,
    minus_prefix: item.minus_prefix as string,
    minus_suffix: item.minus_suffix as string,
    notation,
    plus_prefix: item.plus_prefix as string,
    plus_suffix: item.plus_suffix as string,
    primary_group: primaryGroup,
    secondary_group: secondaryGroup,
  });
}

function parserArtifact(value: unknown, locale: string, formatsRevision: string): BrowserParserArtifact {
  const item = exactObject(value, `browser parser artifact ${locale}`);
  exactKeys(item, ["formats_revision", "locale", "number", "percent", "revision", "schema_version"], "parser artifact");
  if (
    item.schema_version !== 1 ||
    item.locale !== locale ||
    item.formats_revision !== formatsRevision ||
    typeof item.revision !== "string" ||
    item.revision.length === 0
  ) {
    fail("I18N_WIRE_INVALID", `browser parser artifact ${locale} has incompatible identity.`);
  }
  const number = Object.fromEntries(
    Object.entries(exactObject(item.number, `browser parser artifact ${locale}.number`)).map(([profile, record]) => [
      profile,
      numberParserRecord(record, `number parser ${profile}`),
    ]),
  );
  const percent = Object.fromEntries(
    Object.entries(exactObject(item.percent, `browser parser artifact ${locale}.percent`)).map(([profile, value]) => {
      const record = exactObject(value, `percent parser ${profile}`);
      exactKeys(record, ["affix", "numbers", "patterns"], `percent parser ${profile}`);
      if (record.affix !== "required" && record.affix !== "omit") {
        fail("I18N_WIRE_INVALID", `percent parser ${profile}.affix is invalid.`);
      }
      if (!Array.isArray(record.patterns) || record.patterns.length !== 3) {
        fail("I18N_WIRE_INVALID", `percent parser ${profile}.patterns must contain three records.`);
      }
      const patterns = record.patterns.map((rawPattern, index) => {
        const pattern = exactObject(rawPattern, `percent parser ${profile}.patterns[${index}]`);
        exactKeys(pattern, ["negative", "prefix", "suffix"], `percent parser ${profile}.patterns[${index}]`);
        if (
          typeof pattern.negative !== "boolean" ||
          typeof pattern.prefix !== "string" ||
          typeof pattern.suffix !== "string"
        ) {
          fail("I18N_WIRE_INVALID", `percent parser ${profile}.patterns[${index}] is invalid.`);
        }
        return Object.freeze({
          negative: pattern.negative,
          prefix: pattern.prefix,
          suffix: pattern.suffix,
        });
      });
      return [
        profile,
        Object.freeze({
          affix: record.affix,
          numbers: numberParserRecord(record.numbers, `percent parser ${profile}.numbers`),
          patterns: Object.freeze(patterns),
        }),
      ];
    }),
  );
  return Object.freeze({
    formats_revision: formatsRevision,
    locale,
    number: Object.freeze(number),
    percent: Object.freeze(percent),
    revision: item.revision as string,
    schema_version: 1,
  });
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
    point === 0 ? `0.${digits}` : point === digits.length ? digits : `${digits.slice(0, point)}.${digits.slice(point)}`;
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

function createParser(internal: Omit<ProviderInternal, "service">): I18nParser {
  function artifact(): BrowserParserArtifact {
    const result = configuration?.parsers.get(internal.state.context.locale);
    if (result === undefined) fail("I18N_PARSE_UNAVAILABLE", "the current locale has no browser parser artifact.");
    return result;
  }

  return Object.freeze({
    number(input: string, rawOptions: FormatOptions): NumericParseResult {
      if (typeof input !== "string") fail("I18N_PARSE_INVALID", "number input must be a string.");
      const options = formatOptions(rawOptions, "number parser");
      const record = artifact().number[options.format];
      if (record === undefined) fail("I18N_PARSE_INVALID", `unknown number parser ${options.format}.`);
      return parseNumber(input, record);
    },
    percent(input: string, rawOptions: FormatOptions): NumericParseResult {
      if (typeof input !== "string") fail("I18N_PARSE_INVALID", "percent input must be a string.");
      const options = formatOptions(rawOptions, "percent parser");
      const record = artifact().percent[options.format];
      if (record === undefined) fail("I18N_PARSE_INVALID", `unknown percent parser ${options.format}.`);
      if (record.affix === "omit") {
        const parsed = parsePlainNumber(input, record.numbers);
        if (!parsed.valid) return parsed;
        const value = shiftExactDecimal(parsed.value!, -2);
        return value === null
          ? numericParseResult(input, "invalid", "number_out_of_range")
          : numericParseResult(input, "valid", null, value);
      }
      if (
        Array.from(input).some(
          (character) => BIDI_CONTROLS.has(character) && !["\u061c", "\u200e", "\u200f"].includes(character),
        )
      ) {
        return numericParseResult(input, "invalid", "bidi_control");
      }
      const normalized = input.replace(/[\u061c\u200e\u200f]/g, "");
      for (const pattern of record.patterns) {
        if (!normalized.startsWith(pattern.prefix) || !normalized.endsWith(pattern.suffix)) continue;
        const inner = normalized.slice(pattern.prefix.length, normalized.length - pattern.suffix.length);
        const parsed = parsePlainNumber(inner, record.numbers);
        if (!parsed.valid) return Object.freeze({ ...parsed, input });
        const signed = pattern.negative && !parsed.value!.startsWith("-") ? `-${parsed.value}` : parsed.value!;
        const value = shiftExactDecimal(signed, -2);
        return value === null
          ? numericParseResult(input, "invalid", "number_out_of_range")
          : numericParseResult(input, "valid", null, value);
      }
      return normalized.includes("%") || normalized.includes("٪")
        ? numericParseResult(input, "invalid", "wrong_percent_affix")
        : numericParseResult(input, "incomplete", "missing_percent_affix");
    },
  });
}

function normalizedDecimal(value: string): string {
  const negative = value.startsWith("-");
  const unsigned = negative ? value.slice(1) : value;
  const [integer, fraction = ""] = unsigned.split(".");
  const normalizedFraction = fraction.replace(/0+$/, "");
  const magnitude = normalizedFraction.length === 0 ? integer : `${integer}.${normalizedFraction}`;
  return /^0(?:\.0*)?$/.test(magnitude) ? "0" : `${negative ? "-" : ""}${magnitude}`;
}

function sameExactDecimal(left: string, right: string): boolean {
  return DECIMAL_PATTERN.test(right) && normalizedDecimal(left) === normalizedDecimal(right);
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

function fluentFunctions(locale: string, formats: RuntimeConfiguration["formats"]): Record<string, FluentFunction> {
  return {
    CITRY_PLURAL(positional: FluentValue[], named: Record<string, FluentValue>): string {
      const value = String(native(positional[0]));
      if (!DECIMAL_PATTERN.test(value)) fail("I18N_PLURAL_INVALID", "CITRY_PLURAL received a non-decimal value.");
      const mode = named.mode === undefined ? "cardinal" : String(native(named.mode));
      if (mode !== "cardinal" && mode !== "ordinal") fail("I18N_PLURAL_INVALID", "plural mode is invalid.");
      if (Object.keys(named).some((name) => name !== "exact" && name !== "mode")) {
        fail("I18N_PLURAL_INVALID", "CITRY_PLURAL received an unknown option.");
      }
      if (named.exact !== undefined) {
        const exact = String(native(named.exact))
          .split(",")
          .find((candidate) => sameExactDecimal(value, candidate));
        if (exact !== undefined) return `exact-${exact}`;
      }
      return new Intl.PluralRules(locale, { type: mode }).select(pluralInput(value));
    },
    CITRY_TEXT(positional: FluentValue[], named: Record<string, FluentValue>): string {
      if (Object.keys(named).length !== 0) fail("I18N_TEXT_INVALID", "CITRY_TEXT does not accept options.");
      const value = String(native(positional[0]));
      if (prohibitedText(value)) fail("I18N_TEXT_INVALID", "CITRY_TEXT received a prohibited bidi boundary.");
      return `${FSI}${value}${PDI}`;
    },
    NUMBER(positional: FluentValue[], named: Record<string, FluentValue>): string {
      const profile = String(native(named.profile));
      if (Object.keys(named).length !== 1 || formats.number?.[profile] === undefined) {
        fail("I18N_NUMBER_INVALID", `NUMBER received unknown profile ${profile}.`);
      }
      const value = String(native(positional[0]));
      if (!DECIMAL_PATTERN.test(value)) fail("I18N_NUMBER_INVALID", "NUMBER received a non-decimal value.");
      return `${FSI}${formatExactNumber(locale, value)}${PDI}`;
    },
    SLOT(): never {
      return fail("I18N_SLOT_INVALID", "plain browser translation cannot format a Slot.");
    },
  };
}

function browserArtifact(value: unknown, locale: string): BrowserArtifact {
  const item = exactObject(value, "a browser catalog artifact");
  exactKeys(
    item,
    [
      "bundles",
      "catalog_revision",
      "formats_revision",
      "messages",
      "requested_locale",
      "revision",
      "runtime",
      "schema_version",
    ],
    "a browser catalog artifact",
  );
  if (item.schema_version !== 1 || item.runtime !== "@fluent/bundle@0.19.1" || item.requested_locale !== locale) {
    fail("I18N_ARTIFACT_INVALID", "the browser artifact version or requested locale does not match.");
  }
  if (
    configuration === null ||
    item.catalog_revision !== configuration.catalogRevision ||
    item.formats_revision !== configuration.formatsRevision
  ) {
    fail("I18N_ARTIFACT_INVALID", "the browser artifact catalog or formatter revision is stale.");
  }
  exactString(item.revision, "a browser artifact revision");
  return item as unknown as BrowserArtifact;
}

function createMessageRuntime(value: unknown, locale: string): MessageRuntime {
  const artifact = browserArtifact(value, locale);
  const messages = exactObject(artifact.messages, "browser artifact messages");
  const bundles = exactObject(artifact.bundles, "browser artifact bundles");
  const compiled = new Map<string, FluentBundle>();
  for (const [bundleLocale, source] of Object.entries(bundles)) {
    if (typeof source !== "string") fail("I18N_ARTIFACT_INVALID", "a browser bundle must contain FTL text.");
    const bundle = new FluentBundle(bundleLocale, {
      functions: fluentFunctions(bundleLocale, configuration!.formats),
      useIsolating: false,
    });
    const errors = bundle.addResource(new FluentResource(source), { allowOverrides: false });
    if (errors.length !== 0) fail("I18N_ARTIFACT_INVALID", "a browser bundle failed to parse.");
    compiled.set(bundleLocale, bundle);
  }
  for (const [token, rawEntry] of Object.entries(messages)) {
    const item = exactObject(rawEntry, `browser message ${token}`);
    exactKeys(item, ["bundle_locale", "contract", "internal_id"], `browser message ${token}`);
    const contract = exactObject(item.contract, `browser message ${token} contract`);
    for (const [name, typeName] of Object.entries(contract)) {
      if (!name || typeof typeName !== "string" || !PARAMETER_TYPES.has(typeName)) {
        fail("I18N_ARTIFACT_INVALID", `browser message ${token} has an invalid parameter contract.`);
      }
    }
    const entry = item as unknown as BrowserMessageEntry;
    exactString(entry.bundle_locale, `browser message ${token} bundle_locale`);
    exactString(entry.internal_id, `browser message ${token} internal_id`);
    const bundle = compiled.get(entry.bundle_locale);
    if (bundle?.getMessage(entry.internal_id)?.value == null) {
      fail("I18N_ARTIFACT_INVALID", `browser message ${token} has no compiled pattern.`);
    }
  }
  return Object.freeze({
    artifact,
    format(token: string, values: Readonly<Record<string, unknown>>): string {
      const entry = artifact.messages[token];
      if (entry === undefined) fail("I18N_MESSAGE_MISSING", `browser message ${token} is not loaded.`);
      const bundle = compiled.get(entry.bundle_locale);
      const message = bundle?.getMessage(entry.internal_id);
      if (bundle === undefined || message?.value == null) {
        fail("I18N_ARTIFACT_INVALID", `browser message ${token} is unavailable.`);
      }
      const errors: Error[] = [];
      const callbackFailures: Array<TypeError & { code?: string }> = [];
      const previousFailures = activeFluentFailures;
      activeFluentFailures = callbackFailures;
      let output: string;
      try {
        output = bundle.formatPattern(message.value, exactArguments(entry.contract, values), errors);
      } finally {
        activeFluentFailures = previousFailures;
      }
      if (callbackFailures.length !== 0) throw callbackFailures[0];
      if (errors.length !== 0) fail("I18N_MESSAGE_INVALID", `browser message ${token} failed to format.`);
      return output;
    },
  });
}

function taggedBindingValue(value: unknown, name: string): unknown {
  const item = exactObject(value, name);
  exactKeys(item, ["type", "value"], name);
  const typeName = exactString(item.type, `${name}.type`);
  const text =
    typeof item.value === "string" ? item.value : fail("I18N_WIRE_INVALID", `${name}.value must be a string.`);
  if (typeName === "str") return text;
  if (typeName === "int") {
    if (!INTEGER_PATTERN.test(text)) fail("I18N_WIRE_INVALID", `${name} is not a canonical integer.`);
    const number = Number(text);
    return Number.isSafeInteger(number) ? number : text;
  }
  if (typeName === "decimal") {
    if (!DECIMAL_PATTERN.test(text)) fail("I18N_WIRE_INVALID", `${name} is not a canonical decimal.`);
    return text;
  }
  if (typeName === "datetime") {
    const date = new Date(text);
    if (!Number.isFinite(date.valueOf())) {
      fail("I18N_WIRE_INVALID", `${name} is not a canonical datetime instant.`);
    }
    return date;
  }
  fail("I18N_WIRE_INVALID", `${name}.type is unsupported.`);
}

function bindingDefinition(value: unknown, provider: string, renderedLocale: string): BindingDefinition {
  const item = exactObject(value, "an i18n binding");
  const expected = ["id", "message", "target", "values"];
  if (Object.prototype.hasOwnProperty.call(item, "output")) expected.push("output");
  if (Object.prototype.hasOwnProperty.call(item, "values_expression")) expected.push("values_expression");
  exactKeys(item, expected, "an i18n binding");
  const targetItem = exactObject(item.target, "an i18n binding target");
  const kind = targetItem.kind;
  let target: BindingTarget;
  if (kind === "text") {
    exactKeys(targetItem, ["kind"], "an i18n text target");
    target = Object.freeze({ kind });
  } else if (kind === "attribute") {
    exactKeys(targetItem, ["kind", "name"], "an i18n attribute target");
    const name = exactString(targetItem.name, "an i18n attribute target name");
    if (!BINDING_ATTRIBUTE_TARGETS.has(name)) fail("I18N_WIRE_INVALID", `binding target ${name} is not allowed.`);
    target = Object.freeze({ kind, name });
  } else {
    fail("I18N_WIRE_INVALID", "an i18n binding target kind is invalid.");
  }
  const rawValues = exactObject(item.values, "i18n binding values");
  const values = Object.freeze(
    Object.fromEntries(
      Object.entries(rawValues).map(([name, tagged]) => [
        name,
        taggedBindingValue(tagged, `i18n binding value ${name}`),
      ]),
    ),
  );
  const output = item.output;
  if (output !== undefined && (typeof output !== "string" || output.length === 0)) {
    fail("I18N_WIRE_INVALID", "an i18n binding output must be a non-empty string.");
  }
  const valuesExpression = item.values_expression;
  if (valuesExpression !== undefined && (typeof valuesExpression !== "string" || valuesExpression.length === 0)) {
    fail("I18N_WIRE_INVALID", "an i18n binding values_expression must be a non-empty string.");
  }
  return Object.freeze({
    id: exactString(item.id, "an i18n binding id"),
    message: exactString(item.message, "an i18n binding message"),
    ...(output === undefined ? {} : { output }),
    provider,
    renderedLocale,
    target,
    values,
    ...(valuesExpression === undefined ? {} : { valuesExpression }),
  });
}

function requirementRecord(value: unknown): Requirement {
  const item = exactObject(value, "an i18n requirement");
  exactKeys(
    item,
    ["artifacts", "bindings", "messages", "outputs", "owner", "provider", "rendered_locale"],
    "an i18n requirement",
  );
  const provider = exactString(item.provider, "an i18n requirement provider");
  const owner = exactString(item.owner, "an i18n requirement owner");
  const renderedLocale = exactString(item.rendered_locale, "an i18n requirement rendered_locale");
  const outputs = new Set(stringList(item.outputs, "i18n requirement outputs"));
  const messages = new Set(stringList(item.messages, "i18n requirement messages"));
  const artifacts = new Map<string, MessageRuntime>();
  for (const [locale, artifact] of Object.entries(exactObject(item.artifacts, "i18n requirement artifacts"))) {
    artifacts.set(locale, createMessageRuntime(artifact, locale));
  }
  if (!Array.isArray(item.bindings)) fail("I18N_WIRE_INVALID", "i18n requirement bindings must be a list.");
  const bindings = Object.freeze(item.bindings.map((binding) => bindingDefinition(binding, provider, renderedLocale)));
  return { artifacts, bindings, messages, outputs, owner, provider, renderedLocale };
}

function configureManifest(value: unknown): readonly [I18nManifest, RuntimeConfiguration] {
  const item = exactObject(value, "an i18n manifest");
  exactKeys(
    item,
    [
      "catalog_revision",
      "contexts",
      "formats",
      "formats_revision",
      "locales",
      "messages_url",
      "parsers",
      "providers",
      "requirements",
      "runtime",
      "schema_version",
    ],
    "an i18n manifest",
  );
  if (item.schema_version !== 1 || item.runtime !== "@fluent/bundle@0.19.1") {
    fail("I18N_WIRE_INVALID", "the i18n manifest version is unsupported.");
  }
  const locales = stringList(item.locales, "i18n manifest locales");
  const contexts = new Map<string, LocaleContext>();
  for (const [locale, context] of Object.entries(exactObject(item.contexts, "i18n manifest contexts"))) {
    if (!locales.includes(locale)) fail("I18N_WIRE_INVALID", `context locale ${locale} is not selectable.`);
    const checked = immutableContext(context, `context ${locale}`);
    if (checked.locale !== locale) fail("I18N_WIRE_INVALID", `context ${locale} names another locale.`);
    contexts.set(locale, checked);
  }
  if (contexts.size !== locales.length) fail("I18N_WIRE_INVALID", "the i18n context table is incomplete.");
  const messagesUrl = item.messages_url;
  if (messagesUrl !== null && (typeof messagesUrl !== "string" || messagesUrl.length === 0)) {
    fail("I18N_WIRE_INVALID", "the i18n messages URL must be null or a non-empty string.");
  }
  const parsers = new Map<string, BrowserParserArtifact>();
  for (const [locale, artifact] of Object.entries(exactObject(item.parsers, "i18n parser artifacts"))) {
    if (!locales.includes(locale)) fail("I18N_WIRE_INVALID", `parser locale ${locale} is not selectable.`);
    parsers.set(locale, parserArtifact(artifact, locale, exactString(item.formats_revision, "formats_revision")));
  }
  if (parsers.size !== locales.length) fail("I18N_WIRE_INVALID", "the i18n parser artifact table is incomplete.");
  const next: RuntimeConfiguration = {
    catalogRevision: exactString(item.catalog_revision, "i18n catalog_revision"),
    contexts,
    formats: exactObject(item.formats, "i18n formats") as RuntimeConfiguration["formats"],
    formatsRevision: exactString(item.formats_revision, "i18n formats_revision"),
    locales: new Set(locales),
    messagesUrl,
    parsers,
  };
  if (
    configuration !== null &&
    (configuration.catalogRevision !== next.catalogRevision ||
      configuration.formatsRevision !== next.formatsRevision ||
      JSON.stringify(Array.from(configuration.locales)) !== JSON.stringify(locales) ||
      configuration.messagesUrl !== next.messagesUrl ||
      JSON.stringify(configuration.formats) !== JSON.stringify(next.formats) ||
      JSON.stringify(Array.from(configuration.parsers)) !== JSON.stringify(Array.from(next.parsers)))
  ) {
    fail("I18N_WIRE_INVALID", "an i18n fragment uses a different project configuration.");
  }
  return [item as unknown as I18nManifest, next] as const;
}

function addRequirement(requirement: Requirement): void {
  const target = requirementsByProvider.get(requirement.provider) ?? new Set<Requirement>();
  target.add(requirement);
  requirementsByProvider.set(requirement.provider, target);
  for (const binding of requirement.bindings) {
    const existing = bindingDefinitions.get(binding.id);
    if (existing !== undefined && JSON.stringify(existing) !== JSON.stringify(binding)) {
      fail("I18N_WIRE_INVALID", `binding ${binding.id} has conflicting definitions.`);
    }
    bindingDefinitions.set(binding.id, binding);
    bindingReferenceCounts.set(binding.id, (bindingReferenceCounts.get(binding.id) ?? 0) + 1);
  }
  invalidateProviderTree(requirement.provider);
}

function removeRequirement(requirement: Requirement): void {
  const target = requirementsByProvider.get(requirement.provider);
  if (target === undefined) return;
  target.delete(requirement);
  if (target.size === 0) requirementsByProvider.delete(requirement.provider);
  for (const binding of requirement.bindings) {
    const remaining = (bindingReferenceCounts.get(binding.id) ?? 0) - 1;
    if (remaining <= 0) {
      bindingReferenceCounts.delete(binding.id);
      bindingDefinitions.delete(binding.id);
    } else {
      bindingReferenceCounts.set(binding.id, remaining);
    }
  }
  invalidateProviderTree(requirement.provider);
}

function processManifest(element: Element, acceptedOwners: ReadonlySet<string> | null = null): void {
  if (processedManifests.has(element)) {
    if (!activeManifests.has(element)) {
      (manifestRequirements.get(element) ?? []).forEach(addRequirement);
      activeManifests.add(element);
    }
    return;
  }
  let manifest: I18nManifest;
  let nextConfiguration: RuntimeConfiguration;
  [manifest, nextConfiguration] = configureManifest(JSON.parse(element.textContent ?? ""));
  if (!Array.isArray(manifest.providers) || !Array.isArray(manifest.requirements)) {
    fail("I18N_WIRE_INVALID", "an i18n manifest needs provider and requirement lists.");
  }
  const previousConfiguration = configuration;
  if (configuration === null) configuration = nextConfiguration;
  let nextDefinitions: ProviderDefinition[];
  let requirements: Requirement[];
  try {
    nextDefinitions = manifest.providers
      .map(providerDefinition)
      .filter((definition) => acceptedOwners === null || acceptedOwners.has(definition.id));
    requirements = manifest.requirements
      .map(requirementRecord)
      .filter((requirement) => acceptedOwners === null || acceptedOwners.has(requirement.owner));
  } catch (error) {
    configuration = previousConfiguration;
    throw error;
  }
  try {
    const definitionIds = new Set<string>();
    for (const definition of nextDefinitions) {
      if (definitions.has(definition.id) || definitionIds.has(definition.id)) {
        fail("I18N_WIRE_INVALID", `provider ${definition.id} is duplicated.`);
      }
      if (definition.context.catalog_revision !== nextConfiguration.catalogRevision) {
        fail("I18N_WIRE_INVALID", `provider ${definition.id} has a stale catalog revision.`);
      }
      definitionIds.add(definition.id);
    }
    const stagedBindings = new Map<string, BindingDefinition>();
    for (const requirement of requirements) {
      const localIds = new Set<string>();
      for (const binding of requirement.bindings) {
        if (localIds.has(binding.id)) fail("I18N_WIRE_INVALID", `binding ${binding.id} is duplicated.`);
        localIds.add(binding.id);
        const existing = bindingDefinitions.get(binding.id) ?? stagedBindings.get(binding.id);
        if (existing !== undefined && JSON.stringify(existing) !== JSON.stringify(binding)) {
          fail("I18N_WIRE_INVALID", `binding ${binding.id} has conflicting definitions.`);
        }
        stagedBindings.set(binding.id, binding);
      }
    }
  } catch (error) {
    configuration = previousConfiguration;
    throw error;
  }
  nextDefinitions.forEach((definition) => {
    definitions.set(definition.id, definition);
  });
  requirements.forEach(addRequirement);
  manifestRequirements.set(element, requirements);
  manifestDefinitions.set(element, nextDefinitions);
  processedManifests.add(element);
  activeManifests.add(element);
}

interface PreparedFrameworkManifest {
  readonly adjustedProviders: readonly ProviderDefinition[];
  readonly definitions: readonly ProviderDefinition[];
  readonly element: Element;
  readonly requirements: readonly Requirement[];
  readonly writes: readonly PreparedBindingWrite[];
}

interface PreparedBindingWrite {
  readonly binding: BindingDefinition;
  readonly text: string;
}

function bindingMarkersWithin(root: ParentNode): HTMLElement[] {
  const markers = Array.from(root.querySelectorAll<HTMLElement>("[data-citry-i18n-binding]"));
  for (const template of root.querySelectorAll<HTMLTemplateElement>("template")) {
    markers.push(...bindingMarkersWithin(template.content));
  }
  return markers;
}

function markerOwnsBinding(marker: HTMLElement, bindingId: string): boolean {
  return (marker.getAttribute("data-citry-i18n-binding") ?? "").trim().split(/\s+/).includes(bindingId);
}

function applyPreparedBindingWrite(destination: HTMLElement, write: PreparedBindingWrite): void {
  if (write.binding.target.kind === "text") destination.textContent = write.text;
  else destination.setAttribute(write.binding.target.name!, write.text);
}

function providerContextForPreparation(providerId: string): LocaleContext | null {
  return mountedProviders.get(providerId)?.state.context ?? definitions.get(providerId)?.context ?? null;
}

function adjustPreparedProviders(definitionList: readonly ProviderDefinition[]): ProviderDefinition[] {
  const pending = new Map(definitionList.map((definition) => [definition.id, definition]));
  const adjusted: ProviderDefinition[] = [];
  let progress = true;
  while (pending.size !== 0 && progress) {
    progress = false;
    for (const [id, definition] of pending) {
      if (definition.parent === null) {
        adjusted.push(definition);
        pending.delete(id);
        progress = true;
        continue;
      }
      if (pending.has(definition.parent)) continue;
      const parentContext = providerContextForPreparation(definition.parent);
      if (parentContext === null) continue;
      const context = childContext(parentContext, definition);
      const replacement = sameContext(context, definition.context)
        ? definition
        : Object.freeze({ ...definition, context });
      definitions.set(id, replacement);
      adjusted.push(replacement);
      pending.delete(id);
      progress = true;
    }
  }
  for (const definition of pending.values()) adjusted.push(definition);
  return adjusted;
}

async function prepareRequirementForCurrentLocale(requirement: Requirement): Promise<void> {
  for (let attempt = 0; attempt < 16; attempt += 1) {
    const context = providerContextForPreparation(requirement.provider);
    if (context === null) return;
    await fetchArtifact(requirement, context.locale);
    if (providerContextForPreparation(requirement.provider)?.locale === context.locale) return;
  }
  fail("I18N_BINDING_INVALID", `provider ${requirement.provider} kept changing while its fragment prepared.`);
}

function rollbackPreparedFrameworkManifest(prepared: PreparedFrameworkManifest): void {
  if (activeManifests.has(prepared.element)) {
    prepared.requirements.forEach(removeRequirement);
    activeManifests.delete(prepared.element);
  }
  for (const definition of prepared.definitions) {
    if (!mountedProviders.has(definition.id)) definitions.delete(definition.id);
  }
}

async function prepareFrameworkManifest(
  element: Element,
  acceptedOwners: ReadonlySet<string> | null,
  candidateRoot: ParentNode | null,
): Promise<PreparedFrameworkManifest> {
  processManifest(element, acceptedOwners);
  const requirements = manifestRequirements.get(element) ?? [];
  const definitionList = manifestDefinitions.get(element) ?? [];
  const partial = {
    adjustedProviders: adjustPreparedProviders(definitionList),
    definitions: definitionList,
    element,
    requirements,
  };
  try {
    await Promise.all(requirements.map(prepareRequirementForCurrentLocale));
    const writes: PreparedBindingWrite[] = [];
    const markers = candidateRoot === null ? [] : bindingMarkersWithin(candidateRoot);
    for (const requirement of requirements) {
      const context = providerContextForPreparation(requirement.provider);
      if (context === null) continue;
      const runtime = requirement.artifacts.get(context.locale);
      for (const binding of requirement.bindings) {
        if (candidateRoot !== null && !markers.some((marker) => markerOwnsBinding(marker, binding.id))) {
          fail("I18N_BINDING_INVALID", `binding ${binding.id} has no destination in its fragment candidate.`);
        }
        if (context.locale === requirement.renderedLocale) continue;
        if (runtime === undefined) {
          fail("I18N_BINDING_INVALID", `provider ${requirement.provider} did not prepare locale ${context.locale}.`);
        }
        const token = binding.output === undefined ? binding.message : `${binding.message}.${binding.output}`;
        writes.push(Object.freeze({ binding, text: runtime.format(token, binding.values) }));
      }
    }
    for (const write of writes) {
      for (const destination of markers.filter((marker) => markerOwnsBinding(marker, write.binding.id))) {
        applyPreparedBindingWrite(destination, write);
      }
    }
    return Object.freeze({ ...partial, writes });
  } catch (error) {
    rollbackPreparedFrameworkManifest({ ...partial, writes: [] });
    throw error;
  }
}

function commitPreparedFrameworkManifest(prepared: PreparedFrameworkManifest): void {
  const elements = Array.from(document.querySelectorAll<HTMLElement>("[data-cid]"));
  for (const definition of prepared.adjustedProviders) {
    const wrapper = elements.find((element) =>
      (element.getAttribute("data-cid") ?? "").trim().split(/\s+/).includes(definition.id),
    );
    if (wrapper === undefined) continue;
    wrapper.lang = definition.context.locale;
    wrapper.dir = definition.context.direction;
  }
  const markers = bindingMarkersWithin(document);
  for (const write of prepared.writes) {
    const destinations = markers.filter((element) => markerOwnsBinding(element, write.binding.id));
    if (destinations.length === 0) {
      fail("I18N_BINDING_INVALID", `binding ${write.binding.id} has no inserted destination.`);
    }
    for (const destination of destinations) {
      applyPreparedBindingWrite(destination, write);
    }
  }
}

function manifestsWithin(node: Node): Element[] {
  if (!(node instanceof Element)) return [];
  const result = node.matches(MANIFEST_SELECTOR) ? [node] : [];
  return [...result, ...Array.from(node.querySelectorAll(MANIFEST_SELECTOR))];
}

function processExistingManifests(): void {
  document.querySelectorAll(MANIFEST_SELECTOR).forEach((element) => {
    processManifest(element);
  });
}

function retireDisconnectedProviders(): void {
  for (const [id, internal] of mountedProviders) {
    if (internal.wrapper.isConnected) continue;
    treeRoot(internal).generation += 1;
    if (internal.parent !== null) internal.parent.children.delete(internal);
    mountedProviders.delete(id);
  }
}

function treeRoot(internal: ProviderInternal): ProviderInternal {
  let current = internal;
  while (current.parent !== null) current = current.parent;
  return current;
}

function invalidateProviderTree(providerId: string): void {
  const internal = mountedProviders.get(providerId);
  if (internal !== undefined) treeRoot(internal).generation += 1;
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

function handleMutations(mutations: MutationRecord[]): void {
  for (const mutation of mutations) {
    mutation.addedNodes.forEach((node) => {
      manifestsWithin(node).forEach((element) => {
        processManifest(element);
      });
    });
    mutation.removedNodes.forEach((node) => {
      for (const element of manifestsWithin(node)) {
        if (element.isConnected || !activeManifests.has(element)) continue;
        const requirements = manifestRequirements.get(element) ?? [];
        requirements.forEach(removeRequirement);
        activeManifests.delete(element);
      }
    });
  }
  retireDisconnectedProviders();
}

function contextForLocale(locale: string): LocaleContext {
  const context = configuration?.contexts.get(locale);
  if (context === undefined) fail("I18N_LOCALE_INVALID", `locale ${locale} is not selectable.`);
  return context;
}

function childContext(parent: LocaleContext, definition: ProviderDefinition): LocaleContext {
  const locale = definition.policy.locale.mode === "explicit" ? definition.policy.locale.value! : parent.locale;
  const localeContext = contextForLocale(locale);
  const direction =
    definition.policy.direction.mode === "explicit"
      ? (definition.policy.direction.value as Direction)
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

function rootSwitchContext(internal: ProviderInternal, locale: string): LocaleContext {
  const localeContext = contextForLocale(locale);
  return Object.freeze({
    ...localeContext,
    direction:
      internal.definition.policy.direction.mode === "explicit"
        ? (internal.definition.policy.direction.value as Direction)
        : localeContext.direction,
    time_zone: internal.state.context.time_zone,
    tzdb_revision: internal.state.context.tzdb_revision,
  });
}

function providerRequirements(internal: ProviderInternal): Requirement[] {
  return Array.from(requirementsByProvider.get(internal.definition.id) ?? []);
}

async function fetchArtifact(requirement: Requirement, locale: string): Promise<MessageRuntime> {
  const loaded = requirement.artifacts.get(locale);
  if (loaded !== undefined) return loaded;
  const url = configuration?.messagesUrl;
  if (url === null || url === undefined) {
    fail("I18N_MESSAGES_UNAVAILABLE", `static output has no ${locale} artifact for this message set.`);
  }
  const response = await fetch(url, {
    body: JSON.stringify({
      catalog_revision: configuration!.catalogRevision,
      locale,
      messages: Array.from(requirement.messages),
      outputs: Array.from(requirement.outputs),
      schema_version: 1,
    }),
    headers: { "Content-Type": "application/json" },
    method: "POST",
  });
  if (!response.ok) fail("I18N_MESSAGES_UNAVAILABLE", `the ${locale} message request failed with ${response.status}.`);
  const runtime = createMessageRuntime(await response.json(), locale);
  requirement.artifacts.set(locale, runtime);
  return runtime;
}

function plannedTree(root: ProviderInternal): Array<[ProviderInternal, LocaleContext]> {
  const planned: Array<[ProviderInternal, LocaleContext]> = [];
  function visit(internal: ProviderInternal, inherited: LocaleContext | null): void {
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

async function stageTree(
  planned: ReadonlyArray<readonly [ProviderInternal, LocaleContext]>,
): Promise<Array<[ProviderInternal, LocaleContext]>> {
  await Promise.all(
    planned.flatMap(([internal, context]) =>
      providerRequirements(internal).map((requirement) => fetchArtifact(requirement, context.locale)),
    ),
  );
  return planned.map(([internal, context]) => [internal, context]);
}

function planProviderSubtree(internal: ProviderInternal, context: LocaleContext, owner: number): void {
  const coordinator = treeRoot(internal);
  function visit(target: ProviderInternal, next: LocaleContext): void {
    coordinator.plannedContexts.set(target, next);
    coordinator.plannedOwners.set(target, owner);
    Array.from(target.children).forEach((child) => {
      visit(child, childContext(next, child.definition));
    });
  }
  visit(internal, context);
}

function restoreFailedPlan(
  coordinator: ProviderInternal,
  owner: number,
  initiator: ProviderInternal,
  error: unknown,
): void {
  for (const [target, targetOwner] of coordinator.plannedOwners) {
    if (targetOwner !== owner) continue;
    coordinator.plannedOwners.delete(target);
    coordinator.plannedContexts.delete(target);
    target.state.status = Object.freeze({ phase: "ready" });
  }
  const code = error instanceof Error ? ((error as Error & { code?: string }).code ?? error.message) : String(error);
  if (initiator.wrapper.isConnected) initiator.state.status = Object.freeze({ error: code, phase: "error" });
}

function formatLoaded(
  internal: ProviderInternal,
  message: string,
  values: Readonly<Record<string, unknown>>,
  attr: string | undefined,
): { entry: BrowserMessageEntry; text: string } {
  if (typeof message !== "string" || message.length === 0) fail("I18N_MESSAGE_INVALID", "message must be a string.");
  if (attr !== undefined && (typeof attr !== "string" || attr.length === 0)) {
    fail("I18N_MESSAGE_INVALID", "attr must be a non-empty string when provided.");
  }
  const token = attr === undefined ? message : `${message}.${attr}`;
  for (const requirement of providerRequirements(internal)) {
    const runtime = requirement.artifacts.get(internal.state.context.locale);
    const entry = runtime?.artifact.messages[token];
    if (runtime !== undefined && entry !== undefined) return { entry, text: runtime.format(token, values) };
  }
  fail(
    "I18N_MESSAGE_MISSING",
    `message ${token} is not loaded; declare a literal client use or await i18n.ensureMessages(${JSON.stringify(message)}).`,
  );
}

function bindingValues(value: unknown, name: string): Readonly<Record<string, unknown>> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    fail("I18N_BINDING_INVALID", `${name} must return an object of named values.`);
  }
  return value as Readonly<Record<string, unknown>>;
}

function bindingFingerprint(values: Readonly<Record<string, unknown>>): string {
  const normalized: Array<readonly [string, string, string]> = [];
  for (const [name, value] of Object.entries(values).sort(([left], [right]) => left.localeCompare(right))) {
    if (value instanceof Date) {
      normalized.push([name, "datetime", value.toISOString()]);
      continue;
    }
    const nativeValue = native(value);
    if (typeof nativeValue === "bigint") normalized.push([name, "int", nativeValue.toString()]);
    else if (typeof nativeValue === "number") {
      normalized.push([name, "number", decimalInput(nativeValue, "Decimal")]);
    } else if (typeof nativeValue === "string") normalized.push([name, "string", nativeValue]);
    else fail("I18N_BINDING_INVALID", `binding value ${name} has unsupported type ${typeof nativeValue}.`);
  }
  return JSON.stringify(normalized);
}

function reportBindingError(id: string, error: unknown): void {
  console.error(`[Citry] i18n binding ${id} failed:`, error);
}

function resolvedLoaded(
  internal: ProviderInternal,
  message: string,
  values: Readonly<Record<string, unknown>>,
  output: string | undefined,
): Readonly<ResolvedMessage> {
  const resolved = formatLoaded(internal, message, values, output);
  const locale = resolved.entry.bundle_locale;
  const selected = configuration?.contexts.get(locale);
  return Object.freeze({
    direction: selected?.direction ?? internal.state.context.direction,
    locale,
    text: resolved.text,
    usedFallback: locale !== internal.state.context.locale,
  });
}

function activateDeclarativeBinding(element: Element, definition: BindingDefinition): ActiveBinding {
  if (alpine === null) fail("I18N_BINDING_INVALID", `binding ${definition.id} initialized before Alpine.`);
  const service = alpine.evaluate(element, `$inject('${SERVICE_KEY}', null)`);
  const internal = service !== null && typeof service === "object" ? internals.get(service as I18nService) : undefined;
  if (internal === undefined || internal.definition.id !== definition.provider) {
    fail("I18N_BINDING_INVALID", `binding ${definition.id} is outside its logical i18n provider.`);
  }
  let values = definition.values;
  let effectReference: object | null = null;
  const active: ActiveBinding = {
    disposed: false,
    refresh() {
      if (active.disposed) return;
      const resolved = resolvedLoaded(internal, definition.message, values, definition.output);
      if (definition.target.kind === "text") element.textContent = resolved.text;
      else element.setAttribute(definition.target.name!, resolved.text);
    },
  };
  internal.bindings.add(active);
  if (definition.valuesExpression !== undefined) {
    let initial = true;
    effectReference = alpine.effect(() => {
      if (active.disposed) return;
      try {
        const evaluated = bindingValues(
          alpine!.evaluate(element, definition.valuesExpression!),
          `binding ${definition.id} values expression`,
        );
        const preserve =
          initial &&
          internal.state.context.locale === definition.renderedLocale &&
          bindingFingerprint(evaluated) === bindingFingerprint(definition.values);
        values = evaluated;
        initial = false;
        if (!preserve) active.refresh();
      } catch (error) {
        initial = false;
        reportBindingError(definition.id, error);
      }
    });
  } else if (internal.state.context.locale !== definition.renderedLocale) {
    active.refresh();
  }
  alpine.onElRemoved(element, () => {
    if (active.disposed) return;
    active.disposed = true;
    internal.bindings.delete(active);
    if (effectReference !== null) alpine!.release(effectReference);
  });
  return active;
}

function activateMarker(element: Element): void {
  element.removeAttribute("x-citry-tr");
  const ids = (element.getAttribute("data-citry-i18n-binding") ?? "").trim().split(/\s+/).filter(Boolean);
  if (ids.length === 0 || new Set(ids).size !== ids.length) {
    fail("I18N_BINDING_INVALID", "an i18n binding marker is empty or contains duplicate IDs.");
  }
  const destinations = new Set<string>();
  for (const id of ids) {
    const definition = bindingDefinitions.get(id);
    if (definition === undefined) fail("I18N_BINDING_INVALID", `binding marker ${id} has no checked record.`);
    const destination = definition.target.kind === "text" ? "text" : `attribute:${definition.target.name}`;
    if (destinations.has(destination)) fail("I18N_BINDING_INVALID", `binding marker ${id} duplicates ${destination}.`);
    destinations.add(destination);
    activateDeclarativeBinding(element, definition);
  }
}

function createService(internal: Omit<ProviderInternal, "service">): I18nService {
  const formatter = createFormatter(internal);
  const parser = createParser(internal);
  const service: I18nService = {
    get context(): LocaleContext {
      return internal.state.context;
    },
    get format(): I18nFormatter {
      return formatter;
    },
    get parse(): I18nParser {
      return parser;
    },
    get status(): Readonly<Record<string, unknown>> {
      return internal.state.status;
    },
    bind(options) {
      if (options === null || typeof options !== "object") {
        fail("I18N_BINDING_INVALID", "bind() needs an options object.");
      }
      const message = exactString(options.message, "bind() message");
      const output = options.output;
      if (output !== undefined && (typeof output !== "string" || output.length === 0)) {
        fail("I18N_BINDING_INVALID", "bind() output must be a non-empty string.");
      }
      if (typeof options.onChange !== "function") fail("I18N_BINDING_INVALID", "bind() needs onChange.");
      if (options.values !== undefined && typeof options.values !== "function") {
        fail("I18N_BINDING_INVALID", "bind() values must be a function.");
      }
      let values: Readonly<Record<string, unknown>> = {};
      let effectReference: object | null = null;
      const id = `imperative:${internal.definition.id}`;
      const active: ActiveBinding = {
        disposed: false,
        refresh() {
          if (active.disposed) return;
          try {
            if (options.values !== undefined) values = bindingValues(options.values(), "bind() values");
            const resolved = resolvedLoaded(internal as ProviderInternal, message, values, output);
            options.onChange(resolved.text, resolved);
          } catch (error) {
            reportBindingError(id, error);
          }
        },
      };
      internal.bindings.add(active);
      if (options.values !== undefined) effectReference = alpine!.effect(active.refresh);
      else active.refresh();
      return Object.freeze({
        dispose() {
          if (active.disposed) return;
          active.disposed = true;
          internal.bindings.delete(active);
          if (effectReference !== null) alpine!.release(effectReference);
        },
        refresh: active.refresh,
      });
    },
    async ensureMessages(input: string | readonly string[]): Promise<void> {
      const messages = typeof input === "string" ? [input] : [...input];
      stringList(messages, "ensureMessages messages");
      const requirement: Requirement = {
        artifacts: new Map(),
        bindings: [],
        messages: new Set(messages),
        owner: internal.definition.id,
        outputs: new Set(),
        provider: internal.definition.id,
        renderedLocale: internal.state.context.locale,
      };
      await fetchArtifact(requirement, internal.state.context.locale);
      addRequirement(requirement);
    },
    resolve(message, values = {}, options = {}) {
      return resolvedLoaded(internal as ProviderInternal, message, values, options.attr);
    },
    subscribe(callback: (context: LocaleContext) => void): () => void {
      if (typeof callback !== "function") fail("I18N_SUBSCRIBER_INVALID", "subscribe needs a callback.");
      internal.subscribers.add(callback);
      try {
        callback(internal.state.context);
      } catch (error) {
        reportBindingError("subscriber", error);
      }
      return () => internal.subscribers.delete(callback);
    },
    async switchLocale(locale: string) {
      if (typeof locale !== "string" || !configuration?.locales.has(locale)) {
        fail("I18N_LOCALE_INVALID", `locale ${String(locale)} is not selectable.`);
      }
      const initiator = internal as ProviderInternal;
      const coordinator = treeRoot(initiator);
      coordinator.switchGeneration += 1;
      const request = coordinator.switchGeneration;
      planProviderSubtree(initiator, rootSwitchContext(initiator, locale), request);
      for (const target of coordinator.plannedOwners.keys()) coordinator.plannedOwners.set(target, request);
      coordinator.generation += 1;
      for (const [target, targetOwner] of coordinator.plannedOwners) {
        if (targetOwner === request) {
          target.state.status = Object.freeze({
            phase: "loading",
            target: coordinator.plannedContexts.get(target)!.locale,
          });
        }
      }
      for (let attempt = 0; attempt < 32; attempt += 1) {
        const generation = coordinator.generation;
        const snapshot = plannedTree(coordinator);
        let staged: Array<[ProviderInternal, LocaleContext]>;
        try {
          staged = await stageTree(snapshot);
        } catch (error) {
          if (request !== coordinator.switchGeneration) {
            return Object.freeze({ status: "stale" as const });
          }
          if (!initiator.wrapper.isConnected) {
            restoreFailedPlan(coordinator, request, initiator, error);
            return Object.freeze({ status: "stale" as const });
          }
          if (generation !== coordinator.generation) continue;
          restoreFailedPlan(coordinator, request, initiator, error);
          throw error;
        }
        if (request !== coordinator.switchGeneration) {
          return Object.freeze({ status: "stale" as const });
        }
        if (!initiator.wrapper.isConnected) {
          restoreFailedPlan(coordinator, request, initiator, new Error("the switching provider was removed"));
          return Object.freeze({ status: "stale" as const });
        }
        if (generation !== coordinator.generation) continue;
        const changed: Array<[ProviderInternal, LocaleContext]> = [];
        for (const [target, context] of staged) {
          target.wrapper.lang = context.locale;
          target.wrapper.dir = context.direction;
          if (!sameContext(target.state.context, context)) changed.push([target, context]);
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
              reportBindingError("provider-commit", error);
            }
          });
          target.subscribers.forEach((callback) => {
            try {
              callback(context);
            } catch (error) {
              reportBindingError("subscriber", error);
            }
          });
        }
        return Object.freeze({ context: initiator.state.context, status: "committed" as const });
      }
      const error = new Error("the provider tree kept changing while its locale switch staged");
      restoreFailedPlan(coordinator, request, initiator, error);
      throw error;
    },
    tr(message, values = {}, options = {}) {
      return formatLoaded(internal as ProviderInternal, message, values, options.attr).text;
    },
  };
  return Object.freeze(service);
}

function provider(element: Element, parentService: I18nService | null): I18nService {
  if (!(element instanceof HTMLElement) || !element.isConnected) {
    fail("I18N_PROVIDER_INVALID", "a client provider needs one live wrapper element.");
  }
  const ids = (element.getAttribute("data-cid") ?? "").trim().split(/\s+/).filter(Boolean);
  const candidates = ids.filter((id) => definitions.has(id) && !mountedProviders.has(id));
  if (candidates.length !== 1) fail("I18N_PROVIDER_INVALID", "the wrapper does not identify one unused provider.");
  const definition = definitions.get(candidates[0])!;
  const parent =
    parentService === null
      ? null
      : (internals.get(parentService) ??
        fail("I18N_PROVIDER_INVALID", "the inherited service is not owned by this i18n runtime."));
  if ((parent?.definition.id ?? null) !== definition.parent) {
    fail("I18N_PROVIDER_INVALID", "the provider's server and browser parents differ.");
  }
  if (alpine === null) fail("I18N_PROVIDER_INVALID", "the provider initialized before Alpine was ready.");
  const resolved = parent === null ? definition.context : childContext(parent.state.context, definition);
  if (
    resolved.locale !== definition.context.locale ||
    resolved.direction !== definition.context.direction ||
    resolved.time_zone !== definition.context.time_zone
  ) {
    fail("I18N_PROVIDER_INVALID", "the provider's server and browser contexts differ.");
  }
  const internal = {
    bindings: new Set<ActiveBinding>(),
    children: new Set<ProviderInternal>(),
    definition,
    generation: 0,
    parent: parent ?? null,
    plannedContexts: new Map<ProviderInternal, LocaleContext>(),
    plannedOwners: new Map<ProviderInternal, number>(),
    state: alpine.reactive({
      context: resolved,
      status: Object.freeze({ phase: "ready" }),
    }),
    subscribers: new Set<(context: LocaleContext) => void>(),
    switchGeneration: 0,
    wrapper: element,
  };
  const service = createService(internal);
  const complete = Object.assign(internal, { service }) as ProviderInternal;
  internals.set(service, complete);
  mountedProviders.set(definition.id, complete);
  parent?.children.add(complete);
  treeRoot(complete).generation += 1;
  return service;
}

citry.i18n = Object.freeze({ provider });
citry.manager.registerFrameworkManifest("i18n", {
  commit(token) {
    commitPreparedFrameworkManifest(token as PreparedFrameworkManifest);
  },
  match(element) {
    return element.matches(MANIFEST_SELECTOR);
  },
  prepare(element, options) {
    return prepareFrameworkManifest(element, options?.acceptedOwners ?? null, options?.candidateRoot ?? null);
  },
  rollback(token) {
    rollbackPreparedFrameworkManifest(token as PreparedFrameworkManifest);
  },
});
citry.manager.decorateContext((context) => {
  context.i18n = context.inject(SERVICE_KEY, null) as I18nService | null;
});
citry.alpine.beforeStart((runtime) => {
  alpine = runtime;
  processExistingManifests();
  runtime.directive("citry-tr", activateMarker);
  citry.alpine._magic("i18n", (element) => runtime.evaluate(element, `$inject('${SERVICE_KEY}')`));
});
citry.alpine._register({
  init(element) {
    if (element.hasAttribute("data-citry-i18n-binding")) element.setAttribute("x-citry-tr", "");
  },
  mutations: handleMutations,
});
