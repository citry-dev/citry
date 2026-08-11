const locales = [
  "en-US",
  "cs-CZ",
  "ar-EG",
  "ru-RU",
  "pl-PL",
  "ja-JP",
  "az-Latn",
  "az-Arab",
  "hi-IN-u-nu-deva",
  "th-TH-u-ca-buddhist",
];

const pluralInputs = [0, 1, 2, 1.5, 2.5, 5, 11, 21, 101];
const instant = new Date("2026-03-29T12:30:00Z");

function localeResult(locale) {
  const number = new Intl.NumberFormat(locale, {
    maximumFractionDigits: 3,
  });
  const currency = new Intl.NumberFormat(locale, {
    style: "currency",
    currency: "EUR",
  });
  const percent = new Intl.NumberFormat(locale, { style: "percent" });
  const unit = new Intl.NumberFormat(locale, {
    style: "unit",
    unit: "kilometer",
    unitDisplay: "short",
    maximumFractionDigits: 1,
  });
  const date = new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeZone: "Europe/Prague",
  });
  const plurals = new Intl.PluralRules(locale);

  return {
    resolved: {
      calendar: date.resolvedOptions().calendar,
      locale: number.resolvedOptions().locale,
      numbering_system: number.resolvedOptions().numberingSystem,
    },
    decimal: number.format(1234.5),
    currency: currency.format(1234.5),
    percent: percent.format(0.56),
    unit: unit.format(1234.5),
    list: new Intl.ListFormat(locale).format(["A", "B", "C"]),
    relative_day: new Intl.RelativeTimeFormat(locale, {
      numeric: "always",
    }).format(-3, "day"),
    date: date.format(instant),
    plurals: Object.fromEntries(
      pluralInputs.map((value) => [String(value), plurals.select(value)]),
    ),
  };
}

const parseNames = [
  ...Object.getOwnPropertyNames(Intl),
  ...Object.getOwnPropertyNames(Intl.NumberFormat.prototype),
].filter((name) => /parse/i.test(name));

const output = {
  runtime: {
    node: process.version,
    cldr: process.versions.cldr,
    icu: process.versions.icu,
    tzdb: process.versions.tz,
    unicode: process.versions.unicode,
  },
  locales: Object.fromEntries(locales.map((locale) => [locale, localeResult(locale)])),
  exact_decimal: Object.fromEntries(
    ["9007199254740993", "-0", "1.2300"].map((value) => [
      value,
      new Intl.NumberFormat("en-US", { maximumFractionDigits: 4 }).format(value),
    ]),
  ),
  parsing: {
    public_parse_methods: parseNames,
    has_number_parser: parseNames.length > 0,
  },
  locale_extensions: {
    devanagari_numbering: new Intl.NumberFormat("hi-IN-u-nu-deva")
      .resolvedOptions().numberingSystem,
    thai_calendar: new Intl.DateTimeFormat("th-TH-u-ca-buddhist")
      .resolvedOptions().calendar,
  },
};

process.stdout.write(`${JSON.stringify(output)}\n`);
