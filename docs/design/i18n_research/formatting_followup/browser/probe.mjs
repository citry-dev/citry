const exact = "9007199254740993.25";
const locale = "ar-EG";
const plural = new Intl.PluralRules(locale, { maximumFractionDigits: 20 });
const unit = new Intl.NumberFormat(locale, {
  style: "unit",
  unit: "meter",
  unitDisplay: "long",
  maximumFractionDigits: 20,
});
const percent = new Intl.NumberFormat(locale, {
  style: "percent",
  maximumFractionDigits: 3,
});

const output = {
  runtime: process.versions,
  unit: ["11", "11.25", "12345.67", exact].map((raw) => ({
    raw,
    plural: plural.select(raw),
    formatted: unit.format(raw),
    parts: unit.formatToParts(raw),
  })),
  percent: ["0.125", "12.5"].map((raw) => ({
    raw,
    formatted: percent.format(raw),
    parts: percent.formatToParts(raw),
  })),
};

process.stdout.write(`${JSON.stringify(output, null, 2)}\n`);
