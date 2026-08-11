const exact = "9007199254740993.25";
const instant = new Date("2026-08-10T00:00:00Z");

const outputs = {
  arabic_currency: new Intl.NumberFormat("ar-EG", {
    style: "currency",
    currency: "EUR",
  }).format(exact),
  arabic_exact_decimal: new Intl.NumberFormat("ar-EG").format(exact),
  arabic_percent_fraction: new Intl.NumberFormat("ar-EG", {
    style: "percent",
    maximumFractionDigits: 1,
  }).format(0.125),
  arabic_unit: new Intl.NumberFormat("ar-EG", {
    style: "unit",
    unit: "meter",
    unitDisplay: "long",
  }).format(exact),
  buddhist_date: new Intl.DateTimeFormat("th-TH-u-ca-buddhist", {
    year: "numeric",
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  }).format(instant),
  czech_fraction_plural: new Intl.PluralRules("cs-CZ").select(1.5),
  czech_relative_day: new Intl.RelativeTimeFormat("cs-CZ", {
    numeric: "always",
  }).format(-3, "day"),
  devanagari_exact_decimal: new Intl.NumberFormat("hi-IN-u-nu-deva").format(exact),
  spanish_list: new Intl.ListFormat("es", {
    style: "long",
    type: "conjunction",
  }).format(["España", "Suiza", "Italia"]),
};

process.stdout.write(`${JSON.stringify({
  icu: process.versions.icu,
  node: process.version,
  outputs,
}, null, 2)}\n`);
