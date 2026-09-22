import { FluentBundle, FluentResource, type FluentFunction, type FluentValue } from "@fluent/bundle";
import { createPureI18nHelpers } from "./citry-i18n-core";

const FSI = "\u2068";
const PDI = "\u2069";
const BIDI_CONTROLS = new Set(Array.from("\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"));
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
export type Direction = "ltr" | "rtl";
export type PolicyMode = "clear" | "explicit" | "inherit";

export interface LocaleContext {
  readonly catalog_revision: string;
  readonly direction: Direction;
  readonly fallback_locales: readonly string[];
  readonly formats_revision: string;
  readonly locale: string;
  readonly time_zone: string | null;
  readonly tzdb_revision: string;
}

export interface FieldPolicy {
  readonly mode: PolicyMode;
  readonly value?: string;
}

export interface ProviderDefinition {
  readonly context: LocaleContext;
  readonly id: string;
  readonly parent: string | null;
  readonly policy: {
    readonly direction: FieldPolicy;
    readonly locale: FieldPolicy;
    readonly time_zone: FieldPolicy;
  };
}

export interface BrowserMessageEntry {
  readonly bundle_locale: string;
  readonly contract: Readonly<Record<string, string>>;
  readonly internal_id: string;
}

export interface BrowserArtifact {
  readonly bundles: Readonly<Record<string, string>>;
  readonly catalog_revision: string;
  readonly formats_revision: string;
  readonly messages: Readonly<Record<string, BrowserMessageEntry>>;
  readonly requested_locale: string;
  readonly revision: string;
  readonly runtime: string;
  readonly schema_version: number;
}

export interface RequirementRecord {
  readonly artifacts: Readonly<Record<string, unknown>>;
  readonly bindings: readonly unknown[];
  readonly messages: readonly string[];
  readonly owner: string;
  readonly outputs: readonly string[];
  readonly provider: string;
  readonly rendered_locale: string;
}

export interface BindingTarget {
  readonly kind: "attribute" | "text";
  readonly name?: string;
}

export interface BindingDefinition {
  readonly id: string;
  readonly message: string;
  readonly output?: string;
  readonly provider: string;
  readonly renderedLocale: string;
  readonly target: BindingTarget;
  readonly values: Readonly<Record<string, unknown>>;
  readonly valuesExpression?: string;
}

export interface I18nManifest {
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
export interface ResolvedMessage {
  readonly direction: Direction;
  readonly locale: string;
  readonly text: string;
  readonly usedFallback: boolean;
}

export interface I18nService {
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

export interface FormatOptions {
  readonly format: string;
}

export interface DateFields {
  readonly day: number;
  readonly month: number;
  readonly year: number;
}

export interface TimeFields {
  readonly hour: number;
  readonly millisecond?: number;
  readonly minute: number;
  readonly second?: number;
}

export interface I18nFormatter {
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

export type NumericParseState = "incomplete" | "invalid" | "valid";

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

export interface BrowserPercentParserRecord {
  readonly affix: "omit" | "required";
  readonly numbers: BrowserNumberParserRecord;
  readonly patterns: readonly {
    readonly negative: boolean;
    readonly prefix: string;
    readonly suffix: string;
  }[];
}

export interface BrowserParserArtifact {
  readonly formats_revision: string;
  readonly locale: string;
  readonly number: Readonly<Record<string, BrowserNumberParserRecord>>;
  readonly percent: Readonly<Record<string, BrowserPercentParserRecord>>;
  readonly revision: string;
  readonly schema_version: number;
}

export interface I18nParser {
  number(input: string, options: FormatOptions): NumericParseResult;
  percent(input: string, options: FormatOptions): NumericParseResult;
}

export interface MessageRuntime {
  readonly artifact: BrowserArtifact;
  format(token: string, values: Readonly<Record<string, unknown>>): string;
}

export interface Requirement {
  readonly artifacts: Map<string, MessageRuntime>;
  readonly bindings: readonly BindingDefinition[];
  readonly messages: Set<string>;
  readonly owner: string;
  readonly outputs: Set<string>;
  readonly provider: string;
  readonly renderedLocale: string;
}

export interface ActiveBinding {
  disposed: boolean;
  dispose?(): void;
  refresh(): void;
}

export interface ProviderInternal {
  readonly bindings: Set<ActiveBinding>;
  readonly children: Set<ProviderInternal>;
  definition: ProviderDefinition;
  generation: number;
  parent: ProviderInternal | null;
  readonly plannedContexts: Map<ProviderInternal, LocaleContext>;
  readonly plannedOwners: Map<ProviderInternal, number>;
  service: I18nService | null;
  readonly state: {
    context: LocaleContext;
    status: Readonly<Record<string, unknown>>;
  };
  readonly subscribers: Set<(context: LocaleContext) => void>;
  switchGeneration: number;
}

export interface RuntimeConfiguration {
  catalogRevision: string;
  contexts: Map<string, LocaleContext>;
  formats: Readonly<Record<string, Readonly<Record<string, unknown>>>>;
  formatsRevision: string;
  locales: Set<string>;
  messagesUrl: string | null;
  parsers: Map<string, BrowserParserArtifact>;
}

export interface I18nWireRuntimeState {
  activeFluentFailures: Array<TypeError & { code?: string }> | null;
  configuration: RuntimeConfiguration | null;
}

export function createI18nWireRuntime(
  runtimeState: I18nWireRuntimeState,
  fail: (code: string, message: string) => never,
) {
  const {
    decimalInput,
    formatExactNumber,
    normalizedDecimal,
    numericParseResult,
    parseNumber,
    parsePlainNumber,
    pluralInput,
    prohibitedText,
    shiftExactDecimal,
  } = createPureI18nHelpers(fail);
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

  function immutableContext(
    value: unknown,
    name: string,
    configuration: RuntimeConfiguration | null = runtimeState.configuration,
  ): LocaleContext {
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
    const context = Object.freeze({
      catalog_revision: exactString(item.catalog_revision, `${name}.catalog_revision`),
      direction,
      fallback_locales: Object.freeze(stringList(item.fallback_locales, `${name}.fallback_locales`)),
      formats_revision: exactString(item.formats_revision, `${name}.formats_revision`),
      locale: exactString(item.locale, `${name}.locale`),
      time_zone: timeZone as string | null,
      tzdb_revision: exactString(item.tzdb_revision, `${name}.tzdb_revision`),
    });
    if (configuration !== null) {
      if (!configuration.locales.has(context.locale)) {
        fail("I18N_WIRE_INVALID", `${name}.locale is not selectable.`);
      }
      if (context.catalog_revision !== configuration.catalogRevision) {
        fail("I18N_WIRE_INVALID", `${name}.catalog_revision is stale.`);
      }
      if (context.formats_revision !== configuration.formatsRevision) {
        fail("I18N_WIRE_INVALID", `${name}.formats_revision is stale.`);
      }
    }
    return context;
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

  function providerDefinition(
    value: unknown,
    configuration: RuntimeConfiguration | null = runtimeState.configuration,
  ): ProviderDefinition {
    const item = exactObject(value, "an i18n provider");
    exactKeys(item, ["context", "id", "parent", "policy"], "an i18n provider");
    const parent = item.parent;
    if (parent !== null && (typeof parent !== "string" || parent.length === 0)) {
      fail("I18N_WIRE_INVALID", "an i18n provider parent must be null or a render ID.");
    }
    const policy = exactObject(item.policy, "an i18n provider policy");
    exactKeys(policy, ["direction", "locale", "time_zone"], "an i18n provider policy");
    const directionPolicy = fieldPolicy(policy.direction, "an i18n direction policy", false);
    const localePolicy = fieldPolicy(policy.locale, "an i18n locale policy", false);
    const timeZonePolicy = fieldPolicy(policy.time_zone, "an i18n time-zone policy", true);
    if (directionPolicy.mode === "explicit" && directionPolicy.value !== "ltr" && directionPolicy.value !== "rtl") {
      fail("I18N_WIRE_INVALID", "an explicit i18n direction policy must be ltr or rtl.");
    }
    if (
      configuration !== null &&
      localePolicy.mode === "explicit" &&
      !configuration.locales.has(exactString(localePolicy.value, "an explicit i18n locale policy value"))
    ) {
      fail("I18N_WIRE_INVALID", "an explicit i18n locale policy is not selectable.");
    }
    return Object.freeze({
      context: immutableContext(item.context, "an i18n provider context", configuration),
      id: exactString(item.id, "an i18n provider id"),
      parent: parent as string | null,
      policy: Object.freeze({
        direction: directionPolicy,
        locale: localePolicy,
        time_zone: timeZonePolicy,
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

  function formatOptions(value: unknown, name: string): FormatOptions {
    const item = exactObject(value, `${name} options`);
    exactKeys(item, ["format"], `${name} options`);
    return Object.freeze({ format: exactString(item.format, `${name} format`) });
  }

  function profile(kind: string, name: string): Record<string, unknown> {
    const category = runtimeState.configuration?.formats[kind];
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
      kind === "number" || kind === "unit"
        ? fractionDigits
        : kind === "percent"
          ? Math.max(0, fractionDigits - 2)
          : null;
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

  function dateOptions(fields: unknown, length: unknown): Intl.DateTimeFormatOptions {
    const widths = dateTimeOptions(length);
    const weekday: Intl.DateTimeFormatOptions["weekday"] =
      length === "short" ? "narrow" : length === "medium" ? "short" : "long";
    switch (fields) {
      case "year":
        return { year: widths.year };
      case "month":
        return { month: widths.month };
      case "day":
        return { day: widths.day };
      case "weekday":
        return { weekday };
      case "year_month":
        return { month: widths.month, year: widths.year };
      case "month_day":
        return { day: widths.day, month: widths.month };
      case "day_weekday":
        return { day: widths.day, weekday };
      case "month_day_weekday":
        return { day: widths.day, month: widths.month, weekday };
      case "year_month_day":
        return widths;
      case "year_month_day_weekday":
        return { ...widths, weekday };
      default:
        return fail("I18N_FORMAT_INVALID", "a date profile has invalid fields.");
    }
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
        exactKeys(spec, ["fields", "input", "length"], `date format ${options.format}`);
        return new Intl.DateTimeFormat(locale(), { ...dateOptions(spec.fields, spec.length), timeZone: "UTC" }).format(
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
    exactKeys(
      item,
      ["formats_revision", "locale", "number", "percent", "revision", "schema_version"],
      "parser artifact",
    );
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

  function createParser(internal: Omit<ProviderInternal, "service">): I18nParser {
    function artifact(): BrowserParserArtifact {
      const result = runtimeState.configuration?.parsers.get(internal.state.context.locale);
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

  function sameExactDecimal(left: string, right: string): boolean {
    return DECIMAL_PATTERN.test(right) && normalizedDecimal(left) === normalizedDecimal(right);
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

  function browserArtifact(
    value: unknown,
    locale: string,
    configuration: RuntimeConfiguration | null = runtimeState.configuration,
  ): BrowserArtifact {
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

  function createMessageRuntime(
    value: unknown,
    locale: string,
    configuration: RuntimeConfiguration | null = runtimeState.configuration,
  ): MessageRuntime {
    const artifact = browserArtifact(value, locale, configuration);
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
        const previousFailures = runtimeState.activeFluentFailures;
        runtimeState.activeFluentFailures = callbackFailures;
        let output: string;
        try {
          output = bundle.formatPattern(message.value, exactArguments(entry.contract, values), errors);
        } finally {
          runtimeState.activeFluentFailures = previousFailures;
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

  function requirementRecord(
    value: unknown,
    configuration: RuntimeConfiguration | null = runtimeState.configuration,
  ): Requirement {
    const item = exactObject(value, "an i18n requirement");
    exactKeys(
      item,
      ["artifacts", "bindings", "messages", "outputs", "owner", "provider", "rendered_locale"],
      "an i18n requirement",
    );
    const provider = exactString(item.provider, "an i18n requirement provider");
    const owner = exactString(item.owner, "an i18n requirement owner");
    const renderedLocale = exactString(item.rendered_locale, "an i18n requirement rendered_locale");
    if (configuration !== null && !configuration.locales.has(renderedLocale)) {
      fail("I18N_WIRE_INVALID", "an i18n requirement rendered_locale is not selectable.");
    }
    const outputs = new Set(stringList(item.outputs, "i18n requirement outputs"));
    const messages = new Set(stringList(item.messages, "i18n requirement messages"));
    const artifacts = new Map<string, MessageRuntime>();
    for (const [locale, artifact] of Object.entries(exactObject(item.artifacts, "i18n requirement artifacts"))) {
      artifacts.set(locale, createMessageRuntime(artifact, locale, configuration));
    }
    if (!Array.isArray(item.bindings)) fail("I18N_WIRE_INVALID", "i18n requirement bindings must be a list.");
    const bindings = Object.freeze(
      item.bindings.map((binding) => bindingDefinition(binding, provider, renderedLocale)),
    );
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
      const checked = immutableContext(context, `context ${locale}`, null);
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
    const formats = exactObject(item.formats, "i18n formats");
    const formatKinds = ["currency", "date", "datetime", "list", "number", "percent", "relative_time", "time", "unit"];
    const unknownFormatKinds = Object.keys(formats).filter((kind) => !formatKinds.includes(kind));
    if (unknownFormatKinds.length) fail("I18N_WIRE_INVALID", "i18n formats has unknown categories.");
    const profileFields: Readonly<Record<string, readonly string[]>> = {
      currency: [],
      date: ["fields", "input", "length"],
      datetime: ["input", "length", "time_zone_name"],
      list: ["kind", "length"],
      number: ["input"],
      percent: ["input"],
      relative_time: ["unit"],
      time: ["input", "length"],
      unit: ["width"],
    };
    const oneOf = (value: unknown, allowed: readonly unknown[], name: string) => {
      if (!allowed.includes(value)) fail("I18N_WIRE_INVALID", `${name} is invalid.`);
    };
    const checkedInput = (value: unknown, name: string, year: boolean) => {
      if (value === null) return;
      const input = exactObject(value, name);
      exactKeys(input, year ? ["mode", "two_digit_year_start"] : ["mode"], name);
      oneOf(input.mode, ["strict_text", "segments"], `${name}.mode`);
      if (
        year &&
        input.two_digit_year_start !== null &&
        (typeof input.two_digit_year_start !== "number" ||
          !Number.isInteger(input.two_digit_year_start) ||
          input.two_digit_year_start < 1 ||
          input.two_digit_year_start > 9900)
      )
        fail("I18N_WIRE_INVALID", `${name}.two_digit_year_start is invalid.`);
    };
    for (const kind of formatKinds) {
      const rawCategory = formats[kind];
      if (rawCategory === undefined) continue;
      const category = exactObject(rawCategory, `i18n formats.${kind}`);
      for (const [name, rawProfile] of Object.entries(category)) {
        if (!/^[A-Za-z0-9_-]+$/.test(name))
          fail("I18N_WIRE_INVALID", `i18n formats.${kind} has an invalid profile name.`);
        const checkedProfile = exactObject(rawProfile, `i18n formats.${kind}.${name}`);
        exactKeys(checkedProfile, profileFields[kind], `i18n formats.${kind}.${name}`);
        const profileName = `i18n formats.${kind}.${name}`;
        if (kind === "number") {
          const input = exactObject(checkedProfile.input, `${profileName}.input`);
          exactKeys(input, ["notation"], `${profileName}.input`);
          oneOf(input.notation, ["decimal", "decimal_or_scientific"], `${profileName}.input.notation`);
        } else if (kind === "percent") {
          const input = exactObject(checkedProfile.input, `${profileName}.input`);
          exactKeys(input, ["affix"], `${profileName}.input`);
          oneOf(input.affix, ["required", "omit"], `${profileName}.input.affix`);
        } else if (kind === "date") {
          oneOf(
            checkedProfile.fields,
            [
              "year",
              "month",
              "day",
              "weekday",
              "year_month",
              "month_day",
              "day_weekday",
              "month_day_weekday",
              "year_month_day",
              "year_month_day_weekday",
            ],
            `${profileName}.fields`,
          );
          oneOf(checkedProfile.length, ["short", "medium", "long"], `${profileName}.length`);
          checkedInput(checkedProfile.input, `${profileName}.input`, true);
          if (checkedProfile.input !== null && checkedProfile.fields !== "year_month_day")
            fail("I18N_WIRE_INVALID", `${profileName}.input requires year_month_day fields.`);
        } else if (kind === "time") {
          oneOf(checkedProfile.length, ["short", "medium", "long"], `${profileName}.length`);
          checkedInput(checkedProfile.input, `${profileName}.input`, false);
        } else if (kind === "datetime") {
          oneOf(checkedProfile.length, ["short", "medium", "long"], `${profileName}.length`);
          oneOf(checkedProfile.time_zone_name, ["none", "short", "long"], `${profileName}.time_zone_name`);
          checkedInput(checkedProfile.input, `${profileName}.input`, true);
        } else if (kind === "relative_time") {
          oneOf(checkedProfile.unit, ["day"], `${profileName}.unit`);
        } else if (kind === "list") {
          oneOf(checkedProfile.kind, ["and", "or"], `${profileName}.kind`);
          oneOf(checkedProfile.length, ["wide", "short", "narrow"], `${profileName}.length`);
        } else if (kind === "unit") {
          oneOf(checkedProfile.width, ["long", "short", "narrow"], `${profileName}.width`);
        }
      }
    }
    const next: RuntimeConfiguration = {
      catalogRevision: exactString(item.catalog_revision, "i18n catalog_revision"),
      contexts,
      formats: formats as RuntimeConfiguration["formats"],
      formatsRevision: exactString(item.formats_revision, "i18n formats_revision"),
      locales: new Set(locales),
      messagesUrl,
      parsers,
    };
    if (
      runtimeState.configuration !== null &&
      (runtimeState.configuration.catalogRevision !== next.catalogRevision ||
        runtimeState.configuration.formatsRevision !== next.formatsRevision ||
        JSON.stringify(Array.from(runtimeState.configuration.locales)) !== JSON.stringify(locales) ||
        runtimeState.configuration.messagesUrl !== next.messagesUrl ||
        JSON.stringify(runtimeState.configuration.formats) !== JSON.stringify(next.formats) ||
        JSON.stringify(Array.from(runtimeState.configuration.parsers)) !== JSON.stringify(Array.from(next.parsers)))
    ) {
      fail("I18N_WIRE_INVALID", "an i18n fragment uses a different project runtimeState.configuration.");
    }
    return [item as unknown as I18nManifest, next] as const;
  }

  return Object.freeze({
    exactObject,
    exactString,
    stringList,
    immutableContext,
    native,
    providerDefinition,
    createFormatter,
    parserArtifact,
    createParser,
    browserArtifact,
    createMessageRuntime,
    bindingDefinition,
    requirementRecord,
    configureManifest,
  });
}
