use std::cell::RefCell;
use std::collections::BTreeMap;
use std::hint::black_box;
use std::sync::Arc;
use std::thread;
use std::time::Instant;

use icu::datetime::DateTimeFormatter;
use icu::datetime::fieldsets;
use icu::datetime::input::Date;
use icu::decimal::input::Decimal;
use icu::decimal::provider::{Baked, DecimalDigitsV1, DecimalSymbols, DecimalSymbolsV1};
use icu::decimal::{DecimalFormatter, DecimalFormatterPreferences};
use icu::experimental::dimension::currency::CurrencyCode;
use icu::experimental::dimension::currency::formatter::CurrencyFormatter;
use icu::experimental::dimension::percent::formatter::PercentFormatter;
use icu::experimental::dimension::units::formatter::UnitsFormatter;
use icu::experimental::dimension::units::options::{UnitsFormatterOptions, Width};
use icu::experimental::relativetime::{RelativeTimeFormatter, RelativeTimeFormatterOptions};
use icu::list::ListFormatter;
use icu::list::options::{ListFormatterOptions, ListLength};
use icu::locale::{Locale, locale};
use icu::plurals::PluralRules;
use icu_provider::prelude::*;
use serde::Serialize;
use tinystr::tinystr;
use writeable::Writeable;

#[derive(Serialize)]
struct Evidence {
    capabilities: BTreeMap<&'static str, bool>,
    first_constructor_ns: u128,
    known_gaps: BTreeMap<&'static str, bool>,
    outputs: BTreeMap<&'static str, String>,
    repeated_format_ns_per_operation: u128,
    runtime: BTreeMap<&'static str, &'static str>,
}

#[derive(Default)]
struct CapturingDecimalProvider {
    digits: RefCell<Option<[char; 10]>>,
    symbols: RefCell<Option<DecimalSymbols<'static>>>,
}

impl DataProvider<DecimalSymbolsV1> for CapturingDecimalProvider {
    fn load(&self, request: DataRequest) -> Result<DataResponse<DecimalSymbolsV1>, DataError> {
        let response = DataProvider::<DecimalSymbolsV1>::load(&Baked, request)?;
        self.symbols.replace(Some(
            response
                .payload
                .get_static()
                .ok_or_else(|| DataError::custom("baked decimal symbols were not static"))?
                .clone(),
        ));
        Ok(response)
    }
}

impl DataProvider<DecimalDigitsV1> for CapturingDecimalProvider {
    fn load(&self, request: DataRequest) -> Result<DataResponse<DecimalDigitsV1>, DataError> {
        let response = DataProvider::<DecimalDigitsV1>::load(&Baked, request)?;
        self.digits.replace(Some(
            *response
                .payload
                .get_static()
                .ok_or_else(|| DataError::custom("baked decimal digits were not static"))?,
        ));
        Ok(response)
    }
}

#[derive(Debug)]
struct DecimalParseSpec {
    decimal: String,
    digits: [char; 10],
    grouping: String,
    minus_prefix: String,
    minus_suffix: String,
    plus_prefix: String,
    plus_suffix: String,
    primary_group: usize,
    secondary_group: usize,
}

impl DecimalParseSpec {
    fn parse(&self, input: &str) -> Result<String, &'static str> {
        if input.trim() != input || input.is_empty() {
            return Err("whitespace or empty input");
        }
        let (sign, unsigned) = if let Some(value) = input
            .strip_prefix(&self.minus_prefix)
            .and_then(|value| value.strip_suffix(&self.minus_suffix))
        {
            ("-", value)
        } else if let Some(value) = input
            .strip_prefix(&self.plus_prefix)
            .and_then(|value| value.strip_suffix(&self.plus_suffix))
        {
            ("+", value)
        } else if let Some(value) = input.strip_prefix('-') {
            ("-", value)
        } else if let Some(value) = input.strip_prefix('+') {
            ("+", value)
        } else {
            ("", input)
        };
        let mut decimal_parts = unsigned.split(&self.decimal);
        let integer = decimal_parts.next().ok_or("missing integer")?;
        let fraction = decimal_parts.next();
        if decimal_parts.next().is_some() || integer.is_empty() || fraction == Some("") {
            return Err("invalid decimal separator placement");
        }
        let groups = integer.split(&self.grouping).collect::<Vec<_>>();
        if groups.iter().any(|group| group.is_empty()) {
            return Err("empty digit group");
        }
        if groups.len() > 1 {
            if groups
                .last()
                .is_none_or(|group| group.chars().count() != self.primary_group)
            {
                return Err("wrong primary grouping");
            }
            if groups.len() > 2
                && groups[1..groups.len() - 1]
                    .iter()
                    .any(|group| group.chars().count() != self.secondary_group)
            {
                return Err("wrong secondary grouping");
            }
            let first = groups[0].chars().count();
            if first == 0 || first > self.secondary_group {
                return Err("wrong leading group");
            }
        }
        let mut ascii = String::from(sign);
        for character in groups.into_iter().flat_map(str::chars) {
            ascii.push(self.ascii_digit(character)?);
        }
        if let Some(fraction) = fraction {
            if fraction.contains(&self.grouping) {
                return Err("grouping in fraction");
            }
            ascii.push('.');
            for character in fraction.chars() {
                ascii.push(self.ascii_digit(character)?);
            }
        }
        Ok(ascii)
    }

    fn ascii_digit(&self, value: char) -> Result<char, &'static str> {
        self.digits
            .iter()
            .position(|candidate| *candidate == value)
            .and_then(|index| char::from_digit(index as u32, 10))
            .ok_or("foreign or invalid digit")
    }
}

fn decimal_formatter_and_parser(
    preferences: DecimalFormatterPreferences,
) -> Result<(DecimalFormatter, DecimalParseSpec), Box<dyn std::error::Error>> {
    let provider = CapturingDecimalProvider::default();
    let formatter = DecimalFormatter::try_new_unstable(&provider, preferences, Default::default())?;
    let symbols = provider
        .symbols
        .into_inner()
        .ok_or("formatter did not load symbols")?;
    let digits = provider
        .digits
        .into_inner()
        .ok_or("formatter did not load digits")?;
    let secondary_group = if symbols.grouping_sizes.secondary == 0 {
        symbols.grouping_sizes.primary
    } else {
        symbols.grouping_sizes.secondary
    };
    let parser = DecimalParseSpec {
        decimal: symbols.decimal_separator().to_owned(),
        digits,
        grouping: symbols.grouping_separator().to_owned(),
        minus_prefix: symbols.minus_sign_prefix().to_owned(),
        minus_suffix: symbols.minus_sign_suffix().to_owned(),
        plus_prefix: symbols.plus_sign_prefix().to_owned(),
        plus_suffix: symbols.plus_sign_suffix().to_owned(),
        primary_group: symbols.grouping_sizes.primary.into(),
        secondary_group: secondary_group.into(),
    };
    Ok((formatter, parser))
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    fn require_send_sync<T: Send + Sync>() {}
    require_send_sync::<DecimalFormatter>();
    require_send_sync::<PluralRules>();

    let constructor_started = Instant::now();
    let constructor_probe = DecimalFormatter::try_new(locale!("en-US").into(), Default::default())?;
    black_box(constructor_probe);
    let first_constructor_ns = constructor_started.elapsed().as_nanos();

    let exact: Decimal = "9007199254740993.25".parse()?;
    let (ar, ar_parser) = decimal_formatter_and_parser(locale!("ar-EG").into())?;
    let (deva, deva_parser) =
        decimal_formatter_and_parser("hi-IN-u-nu-deva".parse::<Locale>()?.into())?;
    let ar_number = ar.format(&exact).write_to_string().into_owned();
    let deva_number = deva.format(&exact).write_to_string().into_owned();
    let ar_parsed = ar_parser.parse(&ar_number)?;
    let deva_parsed = deva_parser.parse(&deva_number)?;
    let ar_negative = ar
        .format(&"-1234.5".parse()?)
        .write_to_string()
        .into_owned();
    let ar_negative_parsed = ar_parser.parse(&ar_negative)?;
    let invalid_grouping_rejected = ar_parser.parse("٩٬٠٠٧٬١٩٩٬٢٥٤٬٧٤٠٬٩٩٫٣٢٥").is_err();
    let mixed_digits_rejected = deva_parser.parse("९,००,71,९९,२५,४७,४०,९९३.२५").is_err();

    let currency = CurrencyFormatter::try_new(locale!("ar-EG").into(), Default::default())?;
    let eur = CurrencyCode(tinystr!(3, "EUR"));
    let currency_output = currency
        .format_fixed_decimal(&exact, &eur)
        .write_to_string()
        .into_owned();

    let percent = PercentFormatter::try_new(
        "ar-EG-u-nu-arab".parse::<Locale>()?.into(),
        Default::default(),
    )?;
    let percent_value: Decimal = "12.5".parse()?;
    let percent_output = percent
        .format(&percent_value)
        .write_to_string()
        .into_owned();

    let units = UnitsFormatter::try_new(
        locale!("ar-EG").into(),
        "meter",
        UnitsFormatterOptions::from(Width::Long),
    )?;
    let unit_output = units
        .format_fixed_decimal(&exact)
        .write_to_string()
        .into_owned();

    let relative = RelativeTimeFormatter::try_new_long_day(
        locale!("cs-CZ").into(),
        RelativeTimeFormatterOptions::default(),
    )?;
    let relative_output = relative
        .format(Decimal::from(-3i8))
        .write_to_string()
        .into_owned();

    let list = ListFormatter::try_new_and(
        locale!("es").into(),
        ListFormatterOptions::default().with_length(ListLength::Wide),
    )?;
    let list_output = list
        .format(["España", "Suiza", "Italia"].iter())
        .write_to_string()
        .into_owned();

    let date = Date::try_new_iso(2026, 8, 10)?;
    let date_formatter = DateTimeFormatter::try_new(
        "th-TH-u-ca-buddhist".parse::<Locale>()?.into(),
        fieldsets::YMD::medium(),
    )?;
    let date_output = date_formatter.format(&date).write_to_string().into_owned();

    let cs_plurals = PluralRules::try_new_cardinal(locale!("cs-CZ").into())?;
    let cs_fraction: Decimal = "1.5".parse()?;
    let plural_output = format!("{:?}", cs_plurals.category_for(&cs_fraction));

    let started = Instant::now();
    let iterations = 100_000u128;
    for _ in 0..iterations {
        black_box(ar.format(&exact).write_to_string());
    }
    let repeated_format_ns_per_operation = started.elapsed().as_nanos() / iterations;

    let shared_formatter = Arc::new(ar);
    let workers = (0..16)
        .map(|_| {
            let formatter = Arc::clone(&shared_formatter);
            let value = exact.clone();
            thread::spawn(move || {
                for _ in 0..1_000 {
                    if !formatter.format(&value).write_to_string().contains('٩') {
                        return false;
                    }
                }
                true
            })
        })
        .collect::<Vec<_>>();
    let concurrent_formatting = workers
        .into_iter()
        .all(|worker| worker.join().unwrap_or(false));

    let mut outputs = BTreeMap::new();
    outputs.insert("arabic_currency", currency_output);
    outputs.insert("arabic_exact_decimal", ar_number);
    outputs.insert("arabic_negative", ar_negative);
    outputs.insert("arabic_negative_parsed", ar_negative_parsed);
    outputs.insert("arabic_unit", unit_output);
    outputs.insert("arabic_parsed", ar_parsed);
    outputs.insert("buddhist_date", date_output);
    outputs.insert("czech_fraction_plural", plural_output);
    outputs.insert("czech_relative_day", relative_output);
    outputs.insert("devanagari_exact_decimal", deva_number);
    outputs.insert("devanagari_parsed", deva_parsed);
    outputs.insert("spanish_list", list_output);
    outputs.insert("arabic_percent", percent_output);

    let mut capabilities = BTreeMap::new();
    capabilities.insert(
        "alternate_calendar",
        outputs["buddhist_date"].contains("2569"),
    );
    capabilities.insert("currency", outputs["arabic_currency"].contains("€"));
    capabilities.insert("concurrent_formatting", concurrent_formatting);
    capabilities.insert(
        "exact_decimal",
        outputs["arabic_exact_decimal"].contains('٢'),
    );
    capabilities.insert("list", outputs["spanish_list"].contains(" e "));
    capabilities.insert(
        "non_latin_digits",
        outputs["devanagari_exact_decimal"].contains('९'),
    );
    capabilities.insert(
        "strict_decimal_bad_grouping_rejected",
        invalid_grouping_rejected,
    );
    capabilities.insert(
        "strict_decimal_mixed_digits_rejected",
        mixed_digits_rejected,
    );
    capabilities.insert(
        "strict_decimal_round_trip",
        outputs["arabic_parsed"] == "9007199254740993.25"
            && outputs["arabic_negative_parsed"] == "-1234.5"
            && outputs["devanagari_parsed"] == "9007199254740993.25",
    );
    capabilities.insert(
        "plural_fraction",
        outputs["czech_fraction_plural"] == "Many",
    );
    capabilities.insert("percent_formatting", !outputs["arabic_percent"].is_empty());
    capabilities.insert("relative_time", !outputs["czech_relative_day"].is_empty());
    capabilities.insert("unit", outputs["arabic_unit"].contains("متر"));

    if capabilities.values().any(|value| !value) {
        return Err(format!(
            "one or more capability checks failed: {capabilities:?}; outputs={outputs:?}"
        )
        .into());
    }

    let mut known_gaps = BTreeMap::new();
    known_gaps.insert(
        "direct_percent_uses_percentage_points_instead_of_fraction",
        outputs["arabic_percent"].starts_with("١٢٫٥"),
    );
    known_gaps.insert(
        "direct_percent_symbol_differs_from_browser_intl",
        outputs["arabic_percent"].contains('%') && !outputs["arabic_percent"].contains('٪'),
    );
    if known_gaps.values().any(|value| !value) {
        return Err(format!("an expected direct ICU4X gap changed: {known_gaps:?}").into());
    }

    let mut runtime = BTreeMap::new();
    runtime.insert("icu", "2.2.0");
    runtime.insert("icu_experimental", "0.5.0");
    runtime.insert("profile", "release");

    println!(
        "{}",
        serde_json::to_string_pretty(&Evidence {
            capabilities,
            first_constructor_ns,
            known_gaps,
            outputs,
            repeated_format_ns_per_operation,
            runtime,
        })?
    );
    Ok(())
}
