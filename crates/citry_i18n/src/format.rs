//! Checked ICU4X formatter profiles shared by messages and direct Python calls.

#![allow(clippy::result_large_err)]

use std::cell::RefCell;
use std::collections::BTreeMap;
use std::fmt;

use fixed_decimal::{SignedRoundingMode, UnsignedRoundingMode};
use icu::calendar::types::Month;
use icu::calendar::{AnyCalendarKind, AsCalendar, Date, Iso};
use icu::datetime::fieldsets::enums::{DateAndTimeFieldSet, DateFieldSet, TimeFieldSet};
use icu::datetime::input::{DateTime, Time, ZonedDateTime};
use icu::datetime::{DateTimeFormatter, fieldsets, parts as datetime_parts};
use icu::decimal::DecimalFormatter;
use icu::decimal::DecimalFormatterPreferences;
use icu::decimal::input::Decimal;
use icu::decimal::provider::{
    Baked as DecimalBaked, DecimalDigitsV1, DecimalSymbols, DecimalSymbolsV1,
};
use icu::experimental::dimension::currency::CurrencyCode;
use icu::experimental::dimension::currency::formatter::CurrencyFormatter;
use icu::experimental::dimension::percent::formatter::PercentFormatter;
use icu::experimental::dimension::percent::options::{
    Display as PercentDisplay, PercentFormatterOptions,
};
use icu::experimental::dimension::provider::currency::fractions::{
    Baked as ExperimentalBaked, CurrencyFractionsV1,
};
use icu::experimental::dimension::units::formatter::UnitsFormatter;
use icu::experimental::dimension::units::options::{UnitsFormatterOptions, Width as UnitsWidth};
use icu::experimental::relativetime::{RelativeTimeFormatter, RelativeTimeFormatterOptions};
use icu::list::ListFormatter;
use icu::list::options::{ListFormatterOptions, ListLength};
use icu::locale::Locale;
use icu::time::zone::{TimeZone, UtcOffset, ZoneNameTimestamp};
use icu_provider::prelude::{DataProvider, DataRequest};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use tinystr::TinyAsciiStr;
use writeable::{Part, PartsWrite, Writeable};

use crate::compiler::Failure;

#[derive(Debug, Clone, Copy, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
enum NumberParseState {
    Valid,
    Incomplete,
    Invalid,
}

#[derive(Debug, Clone, Serialize)]
struct NumberParseResult {
    state: NumberParseState,
    value: Option<String>,
    error: Option<&'static str>,
}

impl NumberParseResult {
    fn valid(value: String) -> Self {
        Self {
            state: NumberParseState::Valid,
            value: Some(value),
            error: None,
        }
    }

    fn incomplete(error: &'static str) -> Self {
        Self {
            state: NumberParseState::Incomplete,
            value: None,
            error: Some(error),
        }
    }

    fn invalid(error: &'static str) -> Self {
        Self {
            state: NumberParseState::Invalid,
            value: None,
            error: Some(error),
        }
    }
}

#[derive(Debug, Clone, Serialize)]
struct DateValue {
    year: i32,
    month: u8,
    day: u8,
}

#[derive(Debug, Clone, Copy, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
enum TemporalParseState {
    Valid,
    Incomplete,
    Invalid,
    Ambiguous,
}

#[derive(Debug, Clone, Serialize)]
struct DateParseResult {
    state: TemporalParseState,
    value: Option<DateValue>,
    error: Option<&'static str>,
}

impl DateParseResult {
    fn valid(value: DateValue) -> Self {
        Self {
            state: TemporalParseState::Valid,
            value: Some(value),
            error: None,
        }
    }

    fn incomplete(error: &'static str) -> Self {
        Self {
            state: TemporalParseState::Incomplete,
            value: None,
            error: Some(error),
        }
    }

    fn invalid(error: &'static str) -> Self {
        Self {
            state: TemporalParseState::Invalid,
            value: None,
            error: Some(error),
        }
    }

    fn ambiguous(error: &'static str) -> Self {
        Self {
            state: TemporalParseState::Ambiguous,
            value: None,
            error: Some(error),
        }
    }
}

#[derive(Debug, Clone, Serialize)]
struct TimeValue {
    hour: u8,
    minute: u8,
    second: u8,
    nanosecond: u32,
}

#[derive(Debug, Clone, Serialize)]
struct TimeParseResult {
    state: TemporalParseState,
    value: Option<TimeValue>,
    error: Option<&'static str>,
}

impl TimeParseResult {
    fn valid(value: TimeValue) -> Self {
        Self {
            state: TemporalParseState::Valid,
            value: Some(value),
            error: None,
        }
    }

    fn incomplete(error: &'static str) -> Self {
        Self {
            state: TemporalParseState::Incomplete,
            value: None,
            error: Some(error),
        }
    }

    fn invalid(error: &'static str) -> Self {
        Self {
            state: TemporalParseState::Invalid,
            value: None,
            error: Some(error),
        }
    }
}

#[derive(Debug, Clone, Serialize)]
struct LocalDateTimeValue {
    year: i32,
    month: u8,
    day: u8,
    hour: u8,
    minute: u8,
    second: u8,
    nanosecond: u32,
}

#[derive(Debug, Clone, Serialize)]
struct LocalDateTimeParseResult {
    state: TemporalParseState,
    value: Option<LocalDateTimeValue>,
    error: Option<&'static str>,
}

impl LocalDateTimeParseResult {
    fn valid(value: LocalDateTimeValue) -> Self {
        Self {
            state: TemporalParseState::Valid,
            value: Some(value),
            error: None,
        }
    }

    fn incomplete(error: &'static str) -> Self {
        Self {
            state: TemporalParseState::Incomplete,
            value: None,
            error: Some(error),
        }
    }

    fn invalid(error: &'static str) -> Self {
        Self {
            state: TemporalParseState::Invalid,
            value: None,
            error: Some(error),
        }
    }

    fn ambiguous(error: &'static str) -> Self {
        Self {
            state: TemporalParseState::Ambiguous,
            value: None,
            error: Some(error),
        }
    }
}

#[derive(Default)]
struct CapturingDecimalProvider {
    digits: RefCell<Option<[char; 10]>>,
    symbols: RefCell<Option<DecimalSymbols<'static>>>,
}

impl DataProvider<DecimalSymbolsV1> for CapturingDecimalProvider {
    fn load(
        &self,
        request: DataRequest,
    ) -> Result<icu_provider::DataResponse<DecimalSymbolsV1>, icu_provider::DataError> {
        let response = DataProvider::<DecimalSymbolsV1>::load(&DecimalBaked, request)?;
        self.symbols.replace(Some(
            response
                .payload
                .get_static()
                .ok_or_else(|| {
                    icu_provider::DataError::custom("baked decimal symbols were not static")
                })?
                .clone(),
        ));
        Ok(response)
    }
}

impl DataProvider<DecimalDigitsV1> for CapturingDecimalProvider {
    fn load(
        &self,
        request: DataRequest,
    ) -> Result<icu_provider::DataResponse<DecimalDigitsV1>, icu_provider::DataError> {
        let response = DataProvider::<DecimalDigitsV1>::load(&DecimalBaked, request)?;
        self.digits
            .replace(Some(*response.payload.get_static().ok_or_else(|| {
                icu_provider::DataError::custom("baked decimal digits were not static")
            })?));
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
    numbering_system: String,
}

#[derive(Serialize)]
struct BrowserNumberParserRecord {
    decimal: String,
    digits: [char; 10],
    grouping: String,
    minus_prefix: String,
    minus_suffix: String,
    notation: NumberInputNotation,
    plus_prefix: String,
    plus_suffix: String,
    primary_group: usize,
    secondary_group: usize,
}

impl BrowserNumberParserRecord {
    fn from_spec(spec: &DecimalParseSpec, notation: NumberInputNotation) -> Self {
        Self {
            decimal: spec.decimal.clone(),
            digits: spec.digits,
            grouping: spec.grouping.clone(),
            minus_prefix: spec.minus_prefix.clone(),
            minus_suffix: spec.minus_suffix.clone(),
            notation,
            plus_prefix: spec.plus_prefix.clone(),
            plus_suffix: spec.plus_suffix.clone(),
            primary_group: spec.primary_group,
            secondary_group: spec.secondary_group,
        }
    }
}

impl DecimalParseSpec {
    fn parse_with_notation(&self, input: &str, notation: NumberInputNotation) -> NumberParseResult {
        if notation == NumberInputNotation::Decimal {
            return self.parse(input);
        }
        let mut separators = input.match_indices(['e', 'E']);
        let Some((separator, _)) = separators.next() else {
            return self.parse(input);
        };
        if separators.next().is_some() {
            return NumberParseResult::invalid("multiple_exponents");
        }
        let significand = self.parse(&input[..separator]);
        if significand.state != NumberParseState::Valid {
            return significand;
        }
        let exponent_input = &input[separator + 1..];
        if exponent_input.is_empty() {
            return NumberParseResult::incomplete("missing_exponent_digits");
        }
        let (negative, digits) = if let Some(value) = exponent_input.strip_prefix('-') {
            (true, value)
        } else if let Some(value) = exponent_input.strip_prefix('+') {
            (false, value)
        } else {
            (false, exponent_input)
        };
        if digits.is_empty() {
            return NumberParseResult::incomplete("missing_exponent_digits");
        }
        let mut exponent = String::new();
        for character in digits.chars() {
            let Some(digit) = self.ascii_digit(character) else {
                return NumberParseResult::invalid("foreign_or_invalid_exponent_digit");
            };
            exponent.push(digit);
        }
        let Ok(exponent) = exponent.parse::<i16>() else {
            return NumberParseResult::invalid("exponent_out_of_range");
        };
        let exponent = if negative {
            exponent.checked_neg()
        } else {
            Some(exponent)
        };
        let Some(exponent) = exponent else {
            return NumberParseResult::invalid("exponent_out_of_range");
        };
        let Some(raw) = significand.value else {
            return NumberParseResult::invalid("number_out_of_range");
        };
        let Ok(mut value) = raw.parse::<Decimal>() else {
            return NumberParseResult::invalid("number_out_of_range");
        };
        let was_zero = value.is_zero();
        value.multiply_pow10(exponent);
        if !was_zero && value.is_zero() {
            return NumberParseResult::invalid("number_out_of_range");
        }
        NumberParseResult::valid(value.write_to_string().into_owned())
    }

    fn parse(&self, input: &str) -> NumberParseResult {
        if input.is_empty() {
            return NumberParseResult::incomplete("empty");
        }
        if input.trim() != input {
            return NumberParseResult::invalid("whitespace");
        }
        let (negative, unsigned) = if let Some(value) =
            self.strip_sign(input, &self.minus_prefix, &self.minus_suffix)
        {
            (true, value)
        } else if let Some(value) = self.strip_sign(input, &self.plus_prefix, &self.plus_suffix) {
            (false, value)
        } else if let Some(value) = input.strip_prefix('-') {
            (true, value)
        } else if let Some(value) = input.strip_prefix('+') {
            (false, value)
        } else {
            (false, input)
        };
        if unsigned.is_empty() {
            return NumberParseResult::incomplete("sign_without_digits");
        }

        let mut decimal_parts = unsigned.split(&self.decimal);
        let integer = decimal_parts.next().unwrap_or_default();
        let fraction = decimal_parts.next();
        if decimal_parts.next().is_some() {
            return NumberParseResult::invalid("multiple_decimal_separators");
        }
        if integer.is_empty() {
            return NumberParseResult::incomplete("missing_integer_digits");
        }
        if fraction == Some("") {
            return NumberParseResult::incomplete("missing_fraction_digits");
        }

        let groups = integer.split(&self.grouping).collect::<Vec<_>>();
        if groups.iter().any(|group| group.is_empty()) {
            return if groups.last() == Some(&"") {
                NumberParseResult::incomplete("unfinished_group")
            } else {
                NumberParseResult::invalid("empty_group")
            };
        }
        if groups.len() > 1 {
            if self.primary_group == 0 || self.secondary_group == 0 {
                return NumberParseResult::invalid("grouping_not_allowed");
            }
            let final_count = groups.last().map_or(0, |group| group.chars().count());
            if final_count < self.primary_group {
                return NumberParseResult::incomplete("unfinished_group");
            }
            if final_count > self.primary_group {
                return NumberParseResult::invalid("wrong_primary_group");
            }
            if groups.len() > 2
                && groups[1..groups.len() - 1]
                    .iter()
                    .any(|group| group.chars().count() != self.secondary_group)
            {
                return NumberParseResult::invalid("wrong_secondary_group");
            }
            let leading = groups[0].chars().count();
            if leading == 0 || leading > self.secondary_group {
                return NumberParseResult::invalid("wrong_leading_group");
            }
        }

        let mut ascii = String::new();
        if negative {
            ascii.push('-');
        }
        for character in groups.into_iter().flat_map(str::chars) {
            let Some(digit) = self.ascii_digit(character) else {
                return NumberParseResult::invalid("foreign_or_invalid_digit");
            };
            ascii.push(digit);
        }
        if let Some(fraction) = fraction {
            if fraction.contains(&self.grouping) {
                return NumberParseResult::invalid("grouping_in_fraction");
            }
            ascii.push('.');
            for character in fraction.chars() {
                let Some(digit) = self.ascii_digit(character) else {
                    return NumberParseResult::invalid("foreign_or_invalid_digit");
                };
                ascii.push(digit);
            }
        }
        if ascii.parse::<Decimal>().is_err() {
            return NumberParseResult::invalid("number_out_of_range");
        }
        NumberParseResult::valid(ascii)
    }

    fn strip_sign<'a>(&self, input: &'a str, prefix: &str, suffix: &str) -> Option<&'a str> {
        if prefix.is_empty() && suffix.is_empty() {
            return None;
        }
        input.strip_prefix(prefix)?.strip_suffix(suffix)
    }

    fn ascii_digit(&self, value: char) -> Option<char> {
        self.digits
            .iter()
            .position(|candidate| *candidate == value)
            .and_then(|index| char::from_digit(index as u32, 10))
    }
}

const DATE_IGNORED_DIRECTION_MARKS: [char; 3] = ['\u{061c}', '\u{200e}', '\u{200f}'];
const DATE_REJECTED_BIDI_CONTROLS: [char; 9] = [
    '\u{202a}', '\u{202b}', '\u{202c}', '\u{202d}', '\u{202e}', '\u{2066}', '\u{2067}', '\u{2068}',
    '\u{2069}',
];

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
enum TemporalField {
    Year,
    Month,
    Day,
    Hour,
    Minute,
    Second,
    DayPeriod,
}

#[derive(Debug)]
struct TemporalInputLayout {
    fields: Vec<TemporalField>,
    literals: Vec<String>,
    month_is_numeric: bool,
    month_names: Vec<(String, Vec<u8>)>,
    day_periods: Vec<(String, bool)>,
}

impl TemporalInputLayout {
    fn from_formatted(
        value: &impl Writeable,
        numbers: &DecimalParseSpec,
        profile: &str,
    ) -> Result<Self, Failure> {
        let mut writer = PartCollector::default();
        value.write_to_parts(&mut writer).map_err(|_| {
            Failure::new(
                "I18N_TEMPORAL_INPUT_DATA",
                "could not inspect temporal parts",
            )
        })?;

        let mut fields = Vec::new();
        for (start, end, part) in writer.parts {
            if part == datetime_parts::ERA {
                // Calendars admitted below have one fixed era in Python's
                // supported positive date range. Keep its localized text as a
                // required literal instead of pretending it is editable.
                continue;
            }
            let field = if part == datetime_parts::YEAR {
                Some(TemporalField::Year)
            } else if part == datetime_parts::MONTH {
                Some(TemporalField::Month)
            } else if part == datetime_parts::DAY {
                Some(TemporalField::Day)
            } else if part == datetime_parts::HOUR {
                Some(TemporalField::Hour)
            } else if part == datetime_parts::MINUTE {
                Some(TemporalField::Minute)
            } else if part == datetime_parts::SECOND {
                Some(TemporalField::Second)
            } else if part == datetime_parts::DAY_PERIOD {
                Some(TemporalField::DayPeriod)
            } else {
                None
            };
            if let Some(field) = field {
                fields.push((start, end, field));
            } else if part.category == "datetime" {
                return Err(Failure::new(
                    "I18N_TEMPORAL_INPUT_UNSUPPORTED",
                    format!(
                        "temporal profile {profile:?} needs the unsupported field {:?}",
                        part.value
                    ),
                ));
            }
        }
        fields.sort_unstable_by_key(|(start, end, _)| (*start, *end));
        if fields.is_empty() {
            return Err(Failure::new(
                "I18N_TEMPORAL_INPUT_UNSUPPORTED",
                format!("temporal profile {profile:?} resolved no editable fields"),
            ));
        }

        let mut cursor = 0;
        let mut ordered_fields = Vec::with_capacity(3);
        let mut literals = Vec::with_capacity(4);
        let mut month_is_numeric = true;
        for (start, end, field) in fields {
            if start < cursor || end <= start || end > writer.text.len() {
                return Err(Failure::new(
                    "I18N_TEMPORAL_INPUT_DATA",
                    format!("temporal profile {profile:?} returned overlapping or invalid parts"),
                ));
            }
            literals.push(strip_date_direction_marks(&writer.text[cursor..start]));
            if field == TemporalField::Month {
                month_is_numeric = writer.text[start..end]
                    .chars()
                    .all(|character| numbers.ascii_digit(character).is_some());
            }
            ordered_fields.push(field);
            cursor = end;
        }
        literals.push(strip_date_direction_marks(&writer.text[cursor..]));
        if literals[1..literals.len() - 1].iter().any(String::is_empty) {
            return Err(Failure::new(
                "I18N_TEMPORAL_INPUT_UNSUPPORTED",
                format!("temporal profile {profile:?} has no visible separator between fields"),
            ));
        }
        Ok(Self {
            fields: ordered_fields,
            literals,
            month_is_numeric,
            month_names: Vec::new(),
            day_periods: Vec::new(),
        })
    }

    fn require_fields(&self, required: &[TemporalField], profile: &str) -> Result<(), Failure> {
        if required.iter().all(|field| self.fields.contains(field)) {
            return Ok(());
        }
        Err(Failure::new(
            "I18N_TEMPORAL_INPUT_UNSUPPORTED",
            format!("temporal profile {profile:?} did not resolve the required fields"),
        ))
    }

    fn parse_text(
        &self,
        input: &str,
        numbers: &DecimalParseSpec,
    ) -> Result<BTreeMap<TemporalField, String>, InputFailure> {
        let normalized = normalize_date_edit(input)?;
        let mut remaining = normalized.as_str();
        consume_date_literal(&mut remaining, &self.literals[0])?;

        let mut result = BTreeMap::new();
        for (index, field) in self.fields.iter().enumerate() {
            let value = match field {
                TemporalField::Month if !self.month_is_numeric => {
                    self.take_named_month(remaining)?
                }
                TemporalField::DayPeriod => self.take_day_period(remaining)?,
                _ => {
                    let maximum = if *field == TemporalField::Year { 5 } else { 2 };
                    take_date_digits(remaining, numbers, maximum)?
                }
            };
            let (value, rest) = value;
            remaining = rest;
            result.insert(*field, value);
            consume_date_literal(&mut remaining, &self.literals[index + 1])?;
        }
        if !remaining.is_empty() {
            return Err(InputFailure::Invalid("trailing_temporal_input"));
        }
        Ok(result)
    }

    fn take_named_month<'a>(&self, input: &'a str) -> Result<(String, &'a str), InputFailure> {
        let mut matches = self
            .month_names
            .iter()
            .filter(|(name, _)| input.starts_with(name))
            .collect::<Vec<_>>();
        matches.sort_unstable_by_key(|(name, _)| std::cmp::Reverse(name.len()));
        let Some((name, months)) = matches.first() else {
            return if input.is_empty() {
                Err(InputFailure::Incomplete("missing_month_name"))
            } else {
                Err(InputFailure::Invalid("unknown_month_name"))
            };
        };
        if months.len() != 1 {
            return Err(InputFailure::Ambiguous("ambiguous_month_name"));
        }
        Ok((months[0].to_string(), &input[name.len()..]))
    }

    fn take_day_period<'a>(&self, input: &'a str) -> Result<(String, &'a str), InputFailure> {
        let mut matches = self
            .day_periods
            .iter()
            .filter(|(name, _)| input.starts_with(name))
            .collect::<Vec<_>>();
        matches.sort_unstable_by_key(|(name, _)| std::cmp::Reverse(name.len()));
        let Some((name, is_pm)) = matches.first() else {
            return if input.is_empty() {
                Err(InputFailure::Incomplete("missing_day_period"))
            } else {
                Err(InputFailure::Invalid("unknown_day_period"))
            };
        };
        Ok((
            (if *is_pm { "pm" } else { "am" }).to_owned(),
            &input[name.len()..],
        ))
    }
}

#[derive(Debug, Clone, Copy)]
enum InputFailure {
    Incomplete(&'static str),
    Invalid(&'static str),
    Ambiguous(&'static str),
}

#[derive(Default)]
struct PartCollector {
    text: String,
    parts: Vec<(usize, usize, Part)>,
}

impl fmt::Write for PartCollector {
    fn write_str(&mut self, value: &str) -> fmt::Result {
        self.text.push_str(value);
        Ok(())
    }

    fn write_char(&mut self, value: char) -> fmt::Result {
        self.text.push(value);
        Ok(())
    }
}

impl PartsWrite for PartCollector {
    type SubPartsWrite = Self;

    fn with_part(
        &mut self,
        part: Part,
        mut write: impl FnMut(&mut Self::SubPartsWrite) -> fmt::Result,
    ) -> fmt::Result {
        let start = self.text.len();
        write(self)?;
        let end = self.text.len();
        if start < end {
            self.parts.push((start, end, part));
        }
        Ok(())
    }
}

fn strip_date_direction_marks(value: &str) -> String {
    value
        .chars()
        .filter(|character| !DATE_IGNORED_DIRECTION_MARKS.contains(character))
        .collect()
}

fn normalize_date_edit(value: &str) -> Result<String, InputFailure> {
    if value
        .chars()
        .any(|character| DATE_REJECTED_BIDI_CONTROLS.contains(&character))
    {
        return Err(InputFailure::Invalid("bidi_control"));
    }
    Ok(strip_date_direction_marks(value))
}

fn consume_date_literal(remaining: &mut &str, literal: &str) -> Result<(), InputFailure> {
    if let Some(rest) = remaining.strip_prefix(literal) {
        *remaining = rest;
        return Ok(());
    }
    if literal.starts_with(*remaining) {
        return Err(InputFailure::Incomplete("unfinished_date_separator"));
    }
    Err(InputFailure::Invalid("wrong_date_separator"))
}

fn take_date_digits<'a>(
    input: &'a str,
    numbers: &DecimalParseSpec,
    maximum: usize,
) -> Result<(String, &'a str), InputFailure> {
    let mut ascii = String::new();
    let mut end = 0;
    for (index, character) in input.char_indices() {
        let Some(digit) = numbers.ascii_digit(character) else {
            break;
        };
        if ascii.len() == maximum {
            return Err(InputFailure::Invalid("date_field_too_long"));
        }
        ascii.push(digit);
        end = index + character.len_utf8();
    }
    if ascii.is_empty() {
        return if input.is_empty() {
            Err(InputFailure::Incomplete("missing_date_field"))
        } else {
            Err(InputFailure::Invalid("foreign_or_invalid_digit"))
        };
    }
    Ok((ascii, &input[end..]))
}

fn localized_integer(
    input: &str,
    numbers: &DecimalParseSpec,
    maximum: usize,
) -> Result<String, InputFailure> {
    let input = normalize_date_edit(input)?;
    let (value, rest) = take_date_digits(&input, numbers, maximum)?;
    if rest.is_empty() {
        Ok(value)
    } else {
        Err(InputFailure::Invalid("foreign_or_invalid_digit"))
    }
}

fn date_input_formatter(
    locale: Locale,
    length: DateLength,
    profile: &str,
) -> Result<DateTimeFormatter<DateFieldSet>, Failure> {
    let formatter = match length {
        DateLength::Short => DateTimeFormatter::try_new(locale.into(), fieldsets::YMD::short())
            .map(|value| value.cast_into_fset::<DateFieldSet>()),
        DateLength::Medium => DateTimeFormatter::try_new(locale.into(), fieldsets::YMD::medium())
            .map(|value| value.cast_into_fset::<DateFieldSet>()),
        DateLength::Long => DateTimeFormatter::try_new(locale.into(), fieldsets::YMD::long())
            .map(|value| value.cast_into_fset::<DateFieldSet>()),
    };
    formatter.map_err(|error| format_error("date parser", profile, error))
}

fn time_input_formatter(
    locale: Locale,
    length: TimeLength,
    profile: &str,
) -> Result<DateTimeFormatter<TimeFieldSet>, Failure> {
    let formatter = match length {
        TimeLength::Short => DateTimeFormatter::try_new(locale.into(), fieldsets::T::short())
            .map(|value| value.cast_into_fset::<TimeFieldSet>()),
        TimeLength::Medium => DateTimeFormatter::try_new(locale.into(), fieldsets::T::medium())
            .map(|value| value.cast_into_fset::<TimeFieldSet>()),
        TimeLength::Long => DateTimeFormatter::try_new(locale.into(), fieldsets::T::long())
            .map(|value| value.cast_into_fset::<TimeFieldSet>()),
    };
    formatter.map_err(|error| format_error("time parser", profile, error))
}

fn datetime_input_formatter(
    locale: Locale,
    length: DateLength,
    profile: &str,
) -> Result<DateTimeFormatter<DateAndTimeFieldSet>, Failure> {
    let formatter = match length {
        DateLength::Short => DateTimeFormatter::try_new(locale.into(), fieldsets::YMDT::short())
            .map(|value| value.cast_into_fset::<DateAndTimeFieldSet>()),
        DateLength::Medium => DateTimeFormatter::try_new(locale.into(), fieldsets::YMDT::medium())
            .map(|value| value.cast_into_fset::<DateAndTimeFieldSet>()),
        DateLength::Long => DateTimeFormatter::try_new(locale.into(), fieldsets::YMDT::long())
            .map(|value| value.cast_into_fset::<DateAndTimeFieldSet>()),
    };
    formatter.map_err(|error| format_error("datetime parser", profile, error))
}

fn temporal_part(value: &impl Writeable, part: Part) -> Result<Option<String>, Failure> {
    let mut writer = PartCollector::default();
    value.write_to_parts(&mut writer).map_err(|_| {
        Failure::new(
            "I18N_TEMPORAL_INPUT_DATA",
            "could not inspect temporal parts",
        )
    })?;
    Ok(writer
        .parts
        .into_iter()
        .find(|(_, _, candidate)| *candidate == part)
        .map(|(start, end, _)| strip_date_direction_marks(&writer.text[start..end])))
}

fn ensure_supported_date_input_calendar(
    calendar: AnyCalendarKind,
    profile: &str,
) -> Result<(), Failure> {
    if matches!(
        calendar,
        AnyCalendarKind::Buddhist
            | AnyCalendarKind::Coptic
            | AnyCalendarKind::Ethiopian
            | AnyCalendarKind::EthiopianAmeteAlem
            | AnyCalendarKind::Gregorian
            | AnyCalendarKind::HijriTabularTypeIIFriday
            | AnyCalendarKind::HijriTabularTypeIIThursday
            | AnyCalendarKind::HijriUmmAlQura
            | AnyCalendarKind::Indian
            | AnyCalendarKind::Iso
            | AnyCalendarKind::Persian
    ) {
        return Ok(());
    }
    Err(Failure::new(
        "I18N_DATE_INPUT_CALENDAR",
        format!(
            "date profile {profile:?} needs explicit era or leap-month fields for calendar {calendar:?}"
        ),
    ))
}

fn month_names_for_date(
    formatter: &DateTimeFormatter<DateFieldSet>,
) -> Result<Vec<(String, Vec<u8>)>, Failure> {
    let mut names: BTreeMap<String, Vec<u8>> = BTreeMap::new();
    for iso_month in 1..=12 {
        for iso_day in 1..=31 {
            let Ok(date) = Date::try_new_iso(2024, iso_month, iso_day) else {
                continue;
            };
            let local = date.to_calendar(formatter.calendar());
            let Some(name) = temporal_part(&formatter.format(&date), datetime_parts::MONTH)? else {
                continue;
            };
            let months = names.entry(name).or_default();
            if !months.contains(&local.month().ordinal) {
                months.push(local.month().ordinal);
            }
        }
    }
    Ok(names.into_iter().collect())
}

fn month_names_for_datetime(
    formatter: &DateTimeFormatter<DateAndTimeFieldSet>,
) -> Result<Vec<(String, Vec<u8>)>, Failure> {
    let mut names: BTreeMap<String, Vec<u8>> = BTreeMap::new();
    let time = Time::try_new(13, 47, 59, 0)
        .map_err(|error| Failure::new("I18N_DATETIME_INPUT_DATA", error.to_string()))?;
    for iso_month in 1..=12 {
        for iso_day in 1..=31 {
            let Ok(date) = Date::try_new_iso(2024, iso_month, iso_day) else {
                continue;
            };
            let local = date.to_calendar(formatter.calendar());
            let value = DateTime { date, time };
            let Some(name) = temporal_part(&formatter.format(&value), datetime_parts::MONTH)?
            else {
                continue;
            };
            let months = names.entry(name).or_default();
            if !months.contains(&local.month().ordinal) {
                months.push(local.month().ordinal);
            }
        }
    }
    Ok(names.into_iter().collect())
}

fn day_periods_for_time(
    formatter: &DateTimeFormatter<TimeFieldSet>,
) -> Result<Vec<(String, bool)>, Failure> {
    let mut result = Vec::new();
    for (hour, is_pm) in [(1, false), (13, true)] {
        let value = Time::try_new(hour, 5, 9, 0)
            .map_err(|error| Failure::new("I18N_TIME_INPUT_DATA", error.to_string()))?;
        if let Some(name) = temporal_part(&formatter.format(&value), datetime_parts::DAY_PERIOD)?
            && !result.iter().any(|item: &(String, bool)| item.0 == name)
        {
            result.push((name, is_pm));
        }
    }
    Ok(result)
}

fn day_periods_for_datetime(
    formatter: &DateTimeFormatter<DateAndTimeFieldSet>,
) -> Result<Vec<(String, bool)>, Failure> {
    let date = Date::try_new_iso(2026, 8, 10)
        .map_err(|error| Failure::new("I18N_DATETIME_INPUT_DATA", error.to_string()))?;
    let mut result = Vec::new();
    for (hour, is_pm) in [(1, false), (13, true)] {
        let time = Time::try_new(hour, 5, 9, 0)
            .map_err(|error| Failure::new("I18N_DATETIME_INPUT_DATA", error.to_string()))?;
        let value = DateTime { date, time };
        if let Some(name) = temporal_part(&formatter.format(&value), datetime_parts::DAY_PERIOD)?
            && !result.iter().any(|item: &(String, bool)| item.0 == name)
        {
            result.push((name, is_pm));
        }
    }
    Ok(result)
}

fn date_failure(failure: InputFailure) -> DateParseResult {
    match failure {
        InputFailure::Incomplete(error) => DateParseResult::incomplete(error),
        InputFailure::Invalid(error) => DateParseResult::invalid(error),
        InputFailure::Ambiguous(error) => DateParseResult::ambiguous(error),
    }
}

fn time_failure(failure: InputFailure) -> TimeParseResult {
    match failure {
        InputFailure::Incomplete(error) => TimeParseResult::incomplete(error),
        InputFailure::Invalid(error) | InputFailure::Ambiguous(error) => {
            TimeParseResult::invalid(error)
        }
    }
}

fn datetime_failure(failure: InputFailure) -> LocalDateTimeParseResult {
    match failure {
        InputFailure::Incomplete(error) => LocalDateTimeParseResult::incomplete(error),
        InputFailure::Invalid(error) => LocalDateTimeParseResult::invalid(error),
        InputFailure::Ambiguous(error) => LocalDateTimeParseResult::ambiguous(error),
    }
}

fn temporal_token(
    tokens: &BTreeMap<TemporalField, String>,
    field: TemporalField,
) -> Result<&str, InputFailure> {
    tokens
        .get(&field)
        .map(String::as_str)
        .ok_or(InputFailure::Incomplete("missing_temporal_field"))
}

fn parse_calendar_year(
    value: &str,
    two_digit_year_start: Option<i32>,
) -> Result<i32, InputFailure> {
    if value.len() == 2 {
        let Some(start) = two_digit_year_start else {
            return Err(InputFailure::Incomplete("year_requires_four_digits"));
        };
        let year = value
            .parse::<i32>()
            .map_err(|_| InputFailure::Invalid("date_field_out_of_range"))?;
        return Ok(start + (year - start.rem_euclid(100)).rem_euclid(100));
    }
    if value.len() < 4 {
        return Err(InputFailure::Incomplete("year_requires_four_digits"));
    }
    value
        .parse::<i32>()
        .map_err(|_| InputFailure::Invalid("date_field_out_of_range"))
}

fn parse_date_tokens<A: AsCalendar>(
    tokens: &BTreeMap<TemporalField, String>,
    two_digit_year_start: Option<i32>,
    calendar: A,
) -> DateParseResult {
    let result = (|| {
        let year = parse_calendar_year(
            temporal_token(tokens, TemporalField::Year)?,
            two_digit_year_start,
        )?;
        let month = temporal_token(tokens, TemporalField::Month)?
            .parse::<u8>()
            .map_err(|_| InputFailure::Invalid("date_field_out_of_range"))?;
        let day = temporal_token(tokens, TemporalField::Day)?
            .parse::<u8>()
            .map_err(|_| InputFailure::Invalid("date_field_out_of_range"))?;
        Ok((year, month, day))
    })();
    match result {
        Ok((year, month, day)) => canonical_date_result(calendar, year, month, day),
        Err(failure) => date_failure(failure),
    }
}

fn parse_time_tokens(tokens: &BTreeMap<TemporalField, String>) -> TimeParseResult {
    let result = (|| {
        let mut hour = temporal_token(tokens, TemporalField::Hour)?
            .parse::<u8>()
            .map_err(|_| InputFailure::Invalid("time_field_out_of_range"))?;
        let minute = temporal_token(tokens, TemporalField::Minute)?
            .parse::<u8>()
            .map_err(|_| InputFailure::Invalid("time_field_out_of_range"))?;
        let second = tokens.get(&TemporalField::Second).map_or(Ok(0), |value| {
            value
                .parse::<u8>()
                .map_err(|_| InputFailure::Invalid("time_field_out_of_range"))
        })?;
        if let Some(period) = tokens.get(&TemporalField::DayPeriod) {
            if !(1..=12).contains(&hour) {
                return Err(InputFailure::Invalid("hour_out_of_range"));
            }
            hour %= 12;
            if period == "pm" {
                hour += 12;
            }
        }
        if hour > 23 || minute > 59 || second > 59 {
            return Err(InputFailure::Invalid("time_field_out_of_range"));
        }
        Ok(TimeValue {
            hour,
            minute,
            second,
            nanosecond: 0,
        })
    })();
    match result {
        Ok(value) => TimeParseResult::valid(value),
        Err(failure) => time_failure(failure),
    }
}

fn local_datetime_result(date: DateParseResult, time: TimeParseResult) -> LocalDateTimeParseResult {
    if date.state != TemporalParseState::Valid {
        return LocalDateTimeParseResult {
            state: date.state,
            value: None,
            error: date.error,
        };
    }
    if time.state != TemporalParseState::Valid {
        return LocalDateTimeParseResult {
            state: time.state,
            value: None,
            error: time.error,
        };
    }
    let Some(date) = date.value else {
        return LocalDateTimeParseResult::invalid("invalid_date");
    };
    let Some(time) = time.value else {
        return LocalDateTimeParseResult::invalid("invalid_time");
    };
    LocalDateTimeParseResult::valid(LocalDateTimeValue {
        year: date.year,
        month: date.month,
        day: date.day,
        hour: time.hour,
        minute: time.minute,
        second: time.second,
        nanosecond: time.nanosecond,
    })
}

fn date_segment_tokens(
    layout: &TemporalInputLayout,
    numbers: &DecimalParseSpec,
    year: &str,
    month: &str,
    day: &str,
) -> Result<BTreeMap<TemporalField, String>, InputFailure> {
    let mut tokens = BTreeMap::new();
    tokens.insert(TemporalField::Year, localized_integer(year, numbers, 5)?);
    let month = match localized_integer(month, numbers, 2) {
        Ok(value) => value,
        Err(_) if !layout.month_is_numeric => {
            let month = normalize_date_edit(month)?;
            let (value, rest) = layout.take_named_month(&month)?;
            if !rest.is_empty() {
                return Err(InputFailure::Invalid("trailing_month_input"));
            }
            value
        }
        Err(failure) => return Err(failure),
    };
    tokens.insert(TemporalField::Month, month);
    tokens.insert(TemporalField::Day, localized_integer(day, numbers, 2)?);
    Ok(tokens)
}

fn time_segment_tokens(
    layout: &TemporalInputLayout,
    numbers: &DecimalParseSpec,
    hour: &str,
    minute: &str,
    second: Option<&str>,
    day_period: Option<&str>,
) -> Result<BTreeMap<TemporalField, String>, InputFailure> {
    let mut tokens = BTreeMap::new();
    tokens.insert(TemporalField::Hour, localized_integer(hour, numbers, 2)?);
    tokens.insert(
        TemporalField::Minute,
        localized_integer(minute, numbers, 2)?,
    );
    if layout.fields.contains(&TemporalField::Second) {
        let Some(second) = second else {
            return Err(InputFailure::Incomplete("missing_second"));
        };
        tokens.insert(
            TemporalField::Second,
            localized_integer(second, numbers, 2)?,
        );
    } else if second.is_some_and(|value| !value.is_empty()) {
        return Err(InputFailure::Invalid("unexpected_second"));
    }
    if layout.fields.contains(&TemporalField::DayPeriod) {
        let Some(day_period) = day_period else {
            return Err(InputFailure::Incomplete("missing_day_period"));
        };
        let day_period = normalize_date_edit(day_period)?;
        let (value, rest) = layout.take_day_period(&day_period)?;
        if !rest.is_empty() {
            return Err(InputFailure::Invalid("trailing_day_period_input"));
        }
        tokens.insert(TemporalField::DayPeriod, value);
    } else if day_period.is_some_and(|value| !value.is_empty()) {
        return Err(InputFailure::Invalid("unexpected_day_period"));
    }
    Ok(tokens)
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct FormatRegistrySpec {
    #[serde(default)]
    number: BTreeMap<String, NumberProfile>,
    #[serde(default)]
    percent: BTreeMap<String, PercentProfile>,
    #[serde(default)]
    currency: BTreeMap<String, EmptyProfile>,
    #[serde(default)]
    date: BTreeMap<String, DateProfile>,
    #[serde(default)]
    time: BTreeMap<String, TimeProfile>,
    #[serde(default)]
    datetime: BTreeMap<String, DateTimeProfile>,
    #[serde(default)]
    relative_time: BTreeMap<String, RelativeTimeProfile>,
    #[serde(default)]
    list: BTreeMap<String, ListProfile>,
    #[serde(default)]
    unit: BTreeMap<String, UnitProfile>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct EmptyProfile {}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct NumberProfile {
    #[serde(default)]
    input: NumberInputProfile,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct NumberInputProfile {
    #[serde(default)]
    notation: NumberInputNotation,
}

#[derive(Debug, Clone, Copy, Default, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
enum NumberInputNotation {
    #[default]
    Decimal,
    DecimalOrScientific,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct PercentProfile {
    input: PercentInputProfile,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct PercentInputProfile {
    affix: PercentAffix,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
enum PercentAffix {
    Required,
    Omit,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct DateProfile {
    #[serde(default)]
    fields: DateFields,
    length: DateLength,
    #[serde(default)]
    input: Option<DateInputProfile>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct DateInputProfile {
    mode: DateInputMode,
    #[serde(default)]
    two_digit_year_start: Option<i32>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
enum DateInputMode {
    StrictText,
    Segments,
}

#[derive(Debug, Clone, Copy, Default, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
enum DateFields {
    Year,
    Month,
    Day,
    Weekday,
    YearMonth,
    MonthDay,
    DayWeekday,
    MonthDayWeekday,
    #[default]
    YearMonthDay,
    YearMonthDayWeekday,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
enum DateLength {
    Short,
    Medium,
    Long,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct TimeProfile {
    length: TimeLength,
    #[serde(default)]
    input: Option<TimeInputProfile>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct TimeInputProfile {
    mode: DateInputMode,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
enum TimeLength {
    Short,
    Medium,
    Long,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct DateTimeProfile {
    length: DateLength,
    time_zone_name: TimeZoneName,
    #[serde(default)]
    input: Option<DateTimeInputProfile>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct DateTimeInputProfile {
    mode: DateInputMode,
    #[serde(default)]
    two_digit_year_start: Option<i32>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
enum TimeZoneName {
    None,
    Short,
    Long,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct RelativeTimeProfile {
    unit: RelativeTimeUnit,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
enum RelativeTimeUnit {
    Day,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct ListProfile {
    kind: ListKind,
    length: ListWidth,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
enum ListKind {
    And,
    Or,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
enum ListWidth {
    Wide,
    Short,
    Narrow,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct UnitProfile {
    width: UnitWidth,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
enum UnitWidth {
    Long,
    Short,
    Narrow,
}

#[derive(Debug, Clone)]
pub(crate) struct FormatRegistry {
    spec: FormatRegistrySpec,
    revision: String,
}

impl FormatRegistry {
    pub(crate) fn new(spec: FormatRegistrySpec) -> Result<Self, Failure> {
        validate_names("number", spec.number.keys())?;
        validate_names("percent", spec.percent.keys())?;
        validate_names("currency", spec.currency.keys())?;
        validate_names("date", spec.date.keys())?;
        validate_names("time", spec.time.keys())?;
        validate_names("datetime", spec.datetime.keys())?;
        validate_names("relative_time", spec.relative_time.keys())?;
        validate_names("list", spec.list.keys())?;
        validate_names("unit", spec.unit.keys())?;
        for (name, profile) in &spec.date {
            validate_two_digit_year_start(
                "date",
                name,
                profile
                    .input
                    .as_ref()
                    .and_then(|input| input.two_digit_year_start),
            )?;
        }
        for (name, profile) in &spec.datetime {
            validate_two_digit_year_start(
                "datetime",
                name,
                profile
                    .input
                    .as_ref()
                    .and_then(|input| input.two_digit_year_start),
            )?;
        }
        let encoded = serde_json::to_vec(&spec)
            .map_err(|error| Failure::new("I18N_FORMAT_PROFILE_JSON", error.to_string()))?;
        let revision = format!("{:x}", Sha256::digest(encoded));
        Ok(Self { spec, revision })
    }

    pub(crate) fn revision(&self) -> &str {
        &self.revision
    }

    pub(crate) fn browser_parser_artifact_json(&self, locale: &str) -> Result<String, Failure> {
        let parsed_locale = parse_locale(locale)?;
        let mut number = BTreeMap::new();
        for (name, profile) in &self.spec.number {
            let spec = decimal_parse_spec(parsed_locale.clone(), name)?;
            number.insert(
                name.clone(),
                BrowserNumberParserRecord::from_spec(&spec, profile.input.notation),
            );
        }
        let mut percent = BTreeMap::new();
        for (name, profile) in &self.spec.percent {
            let spec = percent_parse_spec(parsed_locale.clone(), name)?;
            percent.insert(
                name.clone(),
                BrowserPercentParserRecord {
                    affix: profile.input.affix,
                    numbers: BrowserNumberParserRecord::from_spec(
                        &spec.numbers,
                        NumberInputNotation::Decimal,
                    ),
                    patterns: spec
                        .patterns
                        .into_iter()
                        .map(|pattern| BrowserPercentAffixPattern {
                            negative: pattern.negative,
                            prefix: pattern.prefix,
                            suffix: pattern.suffix,
                        })
                        .collect(),
                },
            );
        }
        let revision_payload =
            serde_json::to_string(&(1_u32, locale, &self.revision, &number, &percent))
                .map_err(|error| Failure::new("I18N_BROWSER_PARSER_JSON", error.to_string()))?;
        let artifact = BrowserParserArtifact {
            formats_revision: self.revision.clone(),
            locale: locale.to_owned(),
            number,
            percent,
            revision: format!("{:x}", Sha256::digest(revision_payload.as_bytes())),
            schema_version: 1,
        };
        serde_json::to_string(&artifact)
            .map_err(|error| Failure::new("I18N_BROWSER_PARSER_JSON", error.to_string()))
    }

    pub(crate) fn validate_message_operation(
        &self,
        kind: &str,
        profile: Option<&str>,
    ) -> Result<(), Failure> {
        match kind {
            "number" => {
                let profile = profile.ok_or_else(|| {
                    Failure::new(
                        "I18N_FORMAT_PROFILE",
                        "number operation omitted its profile",
                    )
                })?;
                require_profile(&self.spec.number, "number", profile)?;
            }
            "datetime" => {
                return Err(Failure::new(
                    "I18N_FORMAT_UNRATIFIED",
                    "DATETIME in Fluent messages is not available until time-zone conversion and browser parity are checked",
                ));
            }
            _ => {}
        }
        Ok(())
    }

    pub(crate) fn number(
        &self,
        locale: &str,
        profile: &str,
        value: &str,
    ) -> Result<String, Failure> {
        require_profile(&self.spec.number, "number", profile)?;
        let locale = parse_locale(locale)?;
        let value = parse_decimal(value)?;
        let formatter = DecimalFormatter::try_new(locale.into(), Default::default())
            .map_err(|error| format_error("number", profile, error))?;
        Ok(formatter.format(&value).write_to_string().into_owned())
    }

    pub(crate) fn parse_number_json(
        &self,
        locale: &str,
        profile: &str,
        input: &str,
    ) -> Result<String, Failure> {
        let profile_spec = require_profile(&self.spec.number, "number", profile)?;
        let locale = parse_locale(locale)?;
        let parser = decimal_parse_spec(locale, profile)?;
        let result = parser.parse_with_notation(input, profile_spec.input.notation);
        serde_json::to_string(&result)
            .map_err(|error| Failure::new("I18N_NUMBER_PARSE_JSON", error.to_string()))
    }

    pub(crate) fn percent(
        &self,
        locale: &str,
        profile: &str,
        value: &str,
    ) -> Result<String, Failure> {
        require_profile(&self.spec.percent, "percent", profile)?;
        let locale = parse_locale(locale)?;
        let numbers = decimal_parse_spec(locale.clone(), profile)?;
        let mut value = parse_decimal(value)?;
        let was_zero = value.is_zero();
        value.multiply_pow10(2);
        if !was_zero && value.is_zero() {
            return Err(Failure::new(
                "I18N_PERCENT_VALUE",
                "percent ratio is too large to multiply by 100",
            ));
        }
        value.trim_start();
        let formatter = PercentFormatter::try_new(locale.into(), Default::default())
            .map_err(|error| format_error("percent", profile, error))?;
        let rendered = formatter.format(&value).write_to_string().into_owned();
        Ok(localize_percent_sign(rendered, &numbers.numbering_system))
    }

    pub(crate) fn parse_percent_json(
        &self,
        locale: &str,
        profile: &str,
        input: &str,
    ) -> Result<String, Failure> {
        let profile_spec = require_profile(&self.spec.percent, "percent", profile)?;
        let locale = parse_locale(locale)?;
        let parser = percent_parse_spec(locale, profile)?;
        let result = match profile_spec.input.affix {
            PercentAffix::Required => parser.parse_required(input),
            PercentAffix::Omit => scale_percent_parse_result(parser.numbers.parse(input), false),
        };
        serde_json::to_string(&result)
            .map_err(|error| Failure::new("I18N_PERCENT_PARSE_JSON", error.to_string()))
    }

    pub(crate) fn currency(
        &self,
        locale: &str,
        profile: &str,
        value: &str,
        currency: &str,
    ) -> Result<String, Failure> {
        require_profile(&self.spec.currency, "currency", profile)?;
        if currency.len() != 3 || !currency.bytes().all(|byte| byte.is_ascii_uppercase()) {
            return Err(Failure::new(
                "I18N_CURRENCY_CODE",
                format!(
                    "currency code must be exactly three uppercase ASCII letters; got {currency:?}"
                ),
            ));
        }
        let code = currency.parse::<TinyAsciiStr<3>>().map_err(|error| {
            Failure::new(
                "I18N_CURRENCY_CODE",
                format!("invalid currency code {currency:?}: {error}"),
            )
        })?;
        let locale = parse_locale(locale)?;
        let mut value = parse_decimal(value)?;
        let fraction_payload = <ExperimentalBaked as DataProvider<CurrencyFractionsV1>>::load(
            &ExperimentalBaked,
            DataRequest::default(),
        )
        .map_err(|error| format_error("currency", profile, error))?
        .payload;
        let fraction_data = fraction_payload.get();
        let fraction = fraction_data
            .fractions
            .get_copied(&code.to_unvalidated())
            .unwrap_or(fraction_data.default);
        if fraction.rounding != 0 {
            return Err(Failure::new(
                "I18N_CURRENCY_ROUNDING_UNRATIFIED",
                format!(
                    "currency {currency:?} requires rounding increment {}, which is not checked yet",
                    fraction.rounding
                ),
            ));
        }
        let position = -i16::from(fraction.digits);
        value.round_with_mode(
            position,
            SignedRoundingMode::Unsigned(UnsignedRoundingMode::HalfExpand),
        );
        value.pad_end(position);
        let formatter = CurrencyFormatter::try_new(locale.into(), Default::default())
            .map_err(|error| format_error("currency", profile, error))?;
        Ok(formatter
            .format_fixed_decimal(&value, &CurrencyCode(code))
            .write_to_string()
            .into_owned())
    }

    pub(crate) fn date(
        &self,
        locale: &str,
        profile: &str,
        year: i32,
        month: u8,
        day: u8,
    ) -> Result<String, Failure> {
        let spec = require_profile(&self.spec.date, "date", profile)?;
        let locale = parse_locale(locale)?;
        let value = Date::try_new_iso(year, month, day)
            .map_err(|error| Failure::new("I18N_DATE_VALUE", error.to_string()))?;
        macro_rules! format_fields {
            ($fields:ident) => {{
                match spec.length {
                    DateLength::Short => DateTimeFormatter::try_new(
                        locale.clone().into(),
                        fieldsets::$fields::short(),
                    )
                    .map_err(|error| format_error("date", profile, error))?
                    .format(&value)
                    .write_to_string()
                    .into_owned(),
                    DateLength::Medium => DateTimeFormatter::try_new(
                        locale.clone().into(),
                        fieldsets::$fields::medium(),
                    )
                    .map_err(|error| format_error("date", profile, error))?
                    .format(&value)
                    .write_to_string()
                    .into_owned(),
                    DateLength::Long => DateTimeFormatter::try_new(
                        locale.clone().into(),
                        fieldsets::$fields::long(),
                    )
                    .map_err(|error| format_error("date", profile, error))?
                    .format(&value)
                    .write_to_string()
                    .into_owned(),
                }
            }};
        }
        let result = match spec.fields {
            DateFields::Year => format_fields!(Y),
            DateFields::Month => format_fields!(M),
            DateFields::Day => format_fields!(D),
            DateFields::Weekday => format_fields!(E),
            DateFields::YearMonth => format_fields!(YM),
            DateFields::MonthDay => format_fields!(MD),
            DateFields::DayWeekday => format_fields!(DE),
            DateFields::MonthDayWeekday => format_fields!(MDE),
            DateFields::YearMonthDay => format_fields!(YMD),
            DateFields::YearMonthDayWeekday => format_fields!(YMDE),
        };
        Ok(result)
    }

    pub(crate) fn parse_date_json(
        &self,
        locale: &str,
        profile: &str,
        input: &str,
    ) -> Result<String, Failure> {
        let (date_profile, input_profile) =
            require_date_input(&self.spec.date, profile, DateInputMode::StrictText)?;
        let locale = parse_locale(locale)?;
        let numbers = decimal_parse_spec(locale.clone(), profile)?;
        let formatter = date_input_formatter(locale, date_profile.length, profile)?;
        ensure_supported_date_input_calendar(formatter.calendar().kind(), profile)?;
        let sample = Date::try_new_iso(1987, 11, 23)
            .map_err(|error| Failure::new("I18N_DATE_INPUT_DATA", error.to_string()))?;
        let mut layout =
            TemporalInputLayout::from_formatted(&formatter.format(&sample), &numbers, profile)?;
        layout.require_fields(
            &[
                TemporalField::Year,
                TemporalField::Month,
                TemporalField::Day,
            ],
            profile,
        )?;
        if !layout.month_is_numeric {
            layout.month_names = month_names_for_date(&formatter)?;
        }
        let result = match layout.parse_text(input, &numbers) {
            Ok(tokens) => parse_date_tokens(
                &tokens,
                input_profile.two_digit_year_start,
                formatter.calendar(),
            ),
            Err(failure) => date_failure(failure),
        };
        serde_json::to_string(&result)
            .map_err(|error| Failure::new("I18N_DATE_PARSE_JSON", error.to_string()))
    }

    #[allow(clippy::too_many_arguments)]
    pub(crate) fn parse_date_segments_json(
        &self,
        locale: &str,
        profile: &str,
        year: &str,
        month: &str,
        day: &str,
    ) -> Result<String, Failure> {
        let (date_profile, input_profile) =
            require_date_input(&self.spec.date, profile, DateInputMode::Segments)?;
        let locale = parse_locale(locale)?;
        let numbers = decimal_parse_spec(locale.clone(), profile)?;
        let formatter = date_input_formatter(locale, date_profile.length, profile)?;
        ensure_supported_date_input_calendar(formatter.calendar().kind(), profile)?;
        let sample = Date::try_new_iso(1987, 11, 23)
            .map_err(|error| Failure::new("I18N_DATE_INPUT_DATA", error.to_string()))?;
        let mut layout =
            TemporalInputLayout::from_formatted(&formatter.format(&sample), &numbers, profile)?;
        layout.require_fields(
            &[
                TemporalField::Year,
                TemporalField::Month,
                TemporalField::Day,
            ],
            profile,
        )?;
        if !layout.month_is_numeric {
            layout.month_names = month_names_for_date(&formatter)?;
        }
        let result = match date_segment_tokens(&layout, &numbers, year, month, day) {
            Ok(tokens) => parse_date_tokens(
                &tokens,
                input_profile.two_digit_year_start,
                formatter.calendar(),
            ),
            Err(failure) => date_failure(failure),
        };
        serde_json::to_string(&result)
            .map_err(|error| Failure::new("I18N_DATE_PARSE_JSON", error.to_string()))
    }

    pub(crate) fn time(
        &self,
        locale: &str,
        profile: &str,
        hour: u8,
        minute: u8,
        second: u8,
        nanosecond: u32,
    ) -> Result<String, Failure> {
        let spec = require_profile(&self.spec.time, "time", profile)?;
        let locale = parse_locale(locale)?;
        let value = Time::try_new(hour, minute, second, nanosecond)
            .map_err(|error| Failure::new("I18N_TIME_VALUE", error.to_string()))?;
        let result = match spec.length {
            TimeLength::Short => DateTimeFormatter::try_new(locale.into(), fieldsets::T::short())
                .map_err(|error| format_error("time", profile, error))?
                .format(&value)
                .write_to_string()
                .into_owned(),
            TimeLength::Medium => DateTimeFormatter::try_new(locale.into(), fieldsets::T::medium())
                .map_err(|error| format_error("time", profile, error))?
                .format(&value)
                .write_to_string()
                .into_owned(),
            TimeLength::Long => DateTimeFormatter::try_new(locale.into(), fieldsets::T::long())
                .map_err(|error| format_error("time", profile, error))?
                .format(&value)
                .write_to_string()
                .into_owned(),
        };
        Ok(result)
    }

    pub(crate) fn parse_time_json(
        &self,
        locale: &str,
        profile: &str,
        input: &str,
    ) -> Result<String, Failure> {
        let (time_profile, _) =
            require_time_input(&self.spec.time, profile, DateInputMode::StrictText)?;
        let locale = parse_locale(locale)?;
        let numbers = decimal_parse_spec(locale.clone(), profile)?;
        let formatter = time_input_formatter(locale, time_profile.length, profile)?;
        let sample = Time::try_new(13, 47, 59, 0)
            .map_err(|error| Failure::new("I18N_TIME_INPUT_DATA", error.to_string()))?;
        let mut layout =
            TemporalInputLayout::from_formatted(&formatter.format(&sample), &numbers, profile)?;
        if !layout.fields.contains(&TemporalField::Hour)
            || !layout.fields.contains(&TemporalField::Minute)
        {
            return Err(Failure::new(
                "I18N_TIME_INPUT_UNSUPPORTED",
                format!("time profile {profile:?} did not resolve hour and minute fields"),
            ));
        }
        if layout.fields.contains(&TemporalField::DayPeriod) {
            layout.day_periods = day_periods_for_time(&formatter)?;
        }
        let result = match layout.parse_text(input, &numbers) {
            Ok(tokens) => parse_time_tokens(&tokens),
            Err(failure) => time_failure(failure),
        };
        serde_json::to_string(&result)
            .map_err(|error| Failure::new("I18N_TIME_PARSE_JSON", error.to_string()))
    }

    #[allow(clippy::too_many_arguments)]
    pub(crate) fn parse_time_segments_json(
        &self,
        locale: &str,
        profile: &str,
        hour: &str,
        minute: &str,
        second: Option<&str>,
        day_period: Option<&str>,
    ) -> Result<String, Failure> {
        let (time_profile, _) =
            require_time_input(&self.spec.time, profile, DateInputMode::Segments)?;
        let locale = parse_locale(locale)?;
        let numbers = decimal_parse_spec(locale.clone(), profile)?;
        let formatter = time_input_formatter(locale, time_profile.length, profile)?;
        let sample = Time::try_new(13, 47, 59, 0)
            .map_err(|error| Failure::new("I18N_TIME_INPUT_DATA", error.to_string()))?;
        let mut layout =
            TemporalInputLayout::from_formatted(&formatter.format(&sample), &numbers, profile)?;
        if layout.fields.contains(&TemporalField::DayPeriod) {
            layout.day_periods = day_periods_for_time(&formatter)?;
        }
        let result = match time_segment_tokens(&layout, &numbers, hour, minute, second, day_period)
        {
            Ok(tokens) => parse_time_tokens(&tokens),
            Err(failure) => time_failure(failure),
        };
        serde_json::to_string(&result)
            .map_err(|error| Failure::new("I18N_TIME_PARSE_JSON", error.to_string()))
    }

    #[allow(clippy::too_many_arguments)]
    pub(crate) fn datetime(
        &self,
        locale: &str,
        profile: &str,
        year: i32,
        month: u8,
        day: u8,
        hour: u8,
        minute: u8,
        second: u8,
        nanosecond: u32,
        time_zone: &str,
        offset_seconds: i32,
        epoch_seconds: i64,
    ) -> Result<String, Failure> {
        let spec = require_profile(&self.spec.datetime, "datetime", profile)?;
        let locale = parse_locale(locale)?;
        let date = Date::try_new_iso(year, month, day)
            .map_err(|error| Failure::new("I18N_DATETIME_VALUE", error.to_string()))?;
        let time = Time::try_new(hour, minute, second, nanosecond)
            .map_err(|error| Failure::new("I18N_DATETIME_VALUE", error.to_string()))?;
        if matches!(spec.time_zone_name, TimeZoneName::None) {
            let value = DateTime { date, time };
            let result = match spec.length {
                DateLength::Short => {
                    DateTimeFormatter::try_new(locale.into(), fieldsets::YMDT::short())
                        .map_err(|error| format_error("datetime", profile, error))?
                        .format(&value)
                        .write_to_string()
                        .into_owned()
                }
                DateLength::Medium => {
                    DateTimeFormatter::try_new(locale.into(), fieldsets::YMDT::medium())
                        .map_err(|error| format_error("datetime", profile, error))?
                        .format(&value)
                        .write_to_string()
                        .into_owned()
                }
                DateLength::Long => {
                    DateTimeFormatter::try_new(locale.into(), fieldsets::YMDT::long())
                        .map_err(|error| format_error("datetime", profile, error))?
                        .format(&value)
                        .write_to_string()
                        .into_owned()
                }
            };
            return Ok(result);
        }

        let zone = TimeZone::from_iana_id(time_zone);
        if zone.is_unknown() {
            return Err(Failure::new(
                "I18N_TIME_ZONE_DATA",
                format!("ICU4X does not recognize IANA time-zone ID {time_zone:?}"),
            ));
        }
        let offset = UtcOffset::try_from_seconds(offset_seconds).map_err(|error| {
            Failure::new(
                "I18N_TIME_ZONE_OFFSET",
                format!("invalid UTC offset: {error}"),
            )
        })?;
        let value = ZonedDateTime {
            date,
            time,
            zone: zone
                .with_offset(Some(offset))
                .with_zone_name_timestamp(ZoneNameTimestamp::from_epoch_seconds(epoch_seconds)),
        };
        let result = match (spec.length, spec.time_zone_name) {
            (DateLength::Short, TimeZoneName::Short) => DateTimeFormatter::try_new(
                locale.into(),
                fieldsets::YMDT::short().with_zone(fieldsets::zone::SpecificShort),
            )
            .map_err(|error| format_error("datetime", profile, error))?
            .format(&value)
            .write_to_string()
            .into_owned(),
            (DateLength::Medium, TimeZoneName::Short) => DateTimeFormatter::try_new(
                locale.into(),
                fieldsets::YMDT::medium().with_zone(fieldsets::zone::SpecificShort),
            )
            .map_err(|error| format_error("datetime", profile, error))?
            .format(&value)
            .write_to_string()
            .into_owned(),
            (DateLength::Long, TimeZoneName::Short) => DateTimeFormatter::try_new(
                locale.into(),
                fieldsets::YMDT::long().with_zone(fieldsets::zone::SpecificShort),
            )
            .map_err(|error| format_error("datetime", profile, error))?
            .format(&value)
            .write_to_string()
            .into_owned(),
            (DateLength::Short, TimeZoneName::Long) => DateTimeFormatter::try_new(
                locale.into(),
                fieldsets::YMDT::short().with_zone(fieldsets::zone::SpecificLong),
            )
            .map_err(|error| format_error("datetime", profile, error))?
            .format(&value)
            .write_to_string()
            .into_owned(),
            (DateLength::Medium, TimeZoneName::Long) => DateTimeFormatter::try_new(
                locale.into(),
                fieldsets::YMDT::medium().with_zone(fieldsets::zone::SpecificLong),
            )
            .map_err(|error| format_error("datetime", profile, error))?
            .format(&value)
            .write_to_string()
            .into_owned(),
            (DateLength::Long, TimeZoneName::Long) => DateTimeFormatter::try_new(
                locale.into(),
                fieldsets::YMDT::long().with_zone(fieldsets::zone::SpecificLong),
            )
            .map_err(|error| format_error("datetime", profile, error))?
            .format(&value)
            .write_to_string()
            .into_owned(),
            (_, TimeZoneName::None) => unreachable!("handled before creating the zoned value"),
        };
        Ok(result)
    }

    pub(crate) fn parse_datetime_json(
        &self,
        locale: &str,
        profile: &str,
        input: &str,
    ) -> Result<String, Failure> {
        let (datetime_profile, input_profile) =
            require_datetime_input(&self.spec.datetime, profile, DateInputMode::StrictText)?;
        let locale = parse_locale(locale)?;
        let numbers = decimal_parse_spec(locale.clone(), profile)?;
        let formatter = datetime_input_formatter(locale, datetime_profile.length, profile)?;
        ensure_supported_date_input_calendar(formatter.calendar().kind(), profile)?;
        let date = Date::try_new_iso(1987, 11, 23)
            .map_err(|error| Failure::new("I18N_DATETIME_INPUT_DATA", error.to_string()))?;
        let time = Time::try_new(13, 47, 59, 0)
            .map_err(|error| Failure::new("I18N_DATETIME_INPUT_DATA", error.to_string()))?;
        let sample = DateTime { date, time };
        let mut layout =
            TemporalInputLayout::from_formatted(&formatter.format(&sample), &numbers, profile)?;
        layout.require_fields(
            &[
                TemporalField::Year,
                TemporalField::Month,
                TemporalField::Day,
                TemporalField::Hour,
                TemporalField::Minute,
            ],
            profile,
        )?;
        if !layout.month_is_numeric {
            layout.month_names = month_names_for_datetime(&formatter)?;
        }
        if layout.fields.contains(&TemporalField::DayPeriod) {
            layout.day_periods = day_periods_for_datetime(&formatter)?;
        }
        let result = match layout.parse_text(input, &numbers) {
            Ok(tokens) => local_datetime_result(
                parse_date_tokens(
                    &tokens,
                    input_profile.two_digit_year_start,
                    formatter.calendar(),
                ),
                parse_time_tokens(&tokens),
            ),
            Err(failure) => datetime_failure(failure),
        };
        serde_json::to_string(&result)
            .map_err(|error| Failure::new("I18N_DATETIME_PARSE_JSON", error.to_string()))
    }

    #[allow(clippy::too_many_arguments)]
    pub(crate) fn parse_datetime_segments_json(
        &self,
        locale: &str,
        profile: &str,
        year: &str,
        month: &str,
        day: &str,
        hour: &str,
        minute: &str,
        second: Option<&str>,
        day_period: Option<&str>,
    ) -> Result<String, Failure> {
        let (datetime_profile, input_profile) =
            require_datetime_input(&self.spec.datetime, profile, DateInputMode::Segments)?;
        let locale = parse_locale(locale)?;
        let numbers = decimal_parse_spec(locale.clone(), profile)?;
        let formatter = datetime_input_formatter(locale, datetime_profile.length, profile)?;
        ensure_supported_date_input_calendar(formatter.calendar().kind(), profile)?;
        let sample_date = Date::try_new_iso(1987, 11, 23)
            .map_err(|error| Failure::new("I18N_DATETIME_INPUT_DATA", error.to_string()))?;
        let sample_time = Time::try_new(13, 47, 59, 0)
            .map_err(|error| Failure::new("I18N_DATETIME_INPUT_DATA", error.to_string()))?;
        let sample = DateTime {
            date: sample_date,
            time: sample_time,
        };
        let mut layout =
            TemporalInputLayout::from_formatted(&formatter.format(&sample), &numbers, profile)?;
        if !layout.month_is_numeric {
            layout.month_names = month_names_for_datetime(&formatter)?;
        }
        if layout.fields.contains(&TemporalField::DayPeriod) {
            layout.day_periods = day_periods_for_datetime(&formatter)?;
        }
        let result = match (
            date_segment_tokens(&layout, &numbers, year, month, day),
            time_segment_tokens(&layout, &numbers, hour, minute, second, day_period),
        ) {
            (Ok(date_tokens), Ok(time_tokens)) => {
                let mut tokens = date_tokens;
                tokens.extend(time_tokens);
                local_datetime_result(
                    parse_date_tokens(
                        &tokens,
                        input_profile.two_digit_year_start,
                        formatter.calendar(),
                    ),
                    parse_time_tokens(&tokens),
                )
            }
            (Err(failure), _) | (_, Err(failure)) => datetime_failure(failure),
        };
        serde_json::to_string(&result)
            .map_err(|error| Failure::new("I18N_DATETIME_PARSE_JSON", error.to_string()))
    }

    pub(crate) fn relative_time(
        &self,
        locale: &str,
        profile: &str,
        value: &str,
        unit: &str,
    ) -> Result<String, Failure> {
        let spec = require_profile(&self.spec.relative_time, "relative_time", profile)?;
        if !matches!((spec.unit, unit), (RelativeTimeUnit::Day, "day")) {
            return Err(Failure::new(
                "I18N_RELATIVE_TIME_UNIT",
                format!("relative-time profile {profile:?} requires unit 'day'; got {unit:?}"),
            ));
        }
        let locale = parse_locale(locale)?;
        let value = parse_decimal(value)?;
        let formatter = RelativeTimeFormatter::try_new_long_day(
            locale.into(),
            RelativeTimeFormatterOptions::default(),
        )
        .map_err(|error| format_error("relative_time", profile, error))?;
        Ok(formatter.format(value).write_to_string().into_owned())
    }

    pub(crate) fn list(
        &self,
        locale: &str,
        profile: &str,
        values: &[String],
    ) -> Result<String, Failure> {
        let spec = require_profile(&self.spec.list, "list", profile)?;
        let locale = parse_locale(locale)?;
        let length = match spec.length {
            ListWidth::Wide => ListLength::Wide,
            ListWidth::Short => ListLength::Short,
            ListWidth::Narrow => ListLength::Narrow,
        };
        let options = ListFormatterOptions::default().with_length(length);
        let formatter = match spec.kind {
            ListKind::And => ListFormatter::try_new_and(locale.into(), options),
            ListKind::Or => ListFormatter::try_new_or(locale.into(), options),
        }
        .map_err(|error| format_error("list", profile, error))?;
        Ok(formatter
            .format(values.iter())
            .write_to_string()
            .into_owned())
    }

    pub(crate) fn unit(
        &self,
        locale: &str,
        profile: &str,
        value: &str,
        unit: &str,
    ) -> Result<String, Failure> {
        let spec = require_profile(&self.spec.unit, "unit", profile)?;
        if unit.is_empty()
            || !unit
                .bytes()
                .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit() || byte == b'-')
        {
            return Err(Failure::new(
                "I18N_UNIT_ID",
                format!("unit ID {unit:?} must use lowercase ASCII letters, digits, and '-'"),
            ));
        }
        let width = match spec.width {
            UnitWidth::Long => UnitsWidth::Long,
            UnitWidth::Short => UnitsWidth::Short,
            UnitWidth::Narrow => UnitsWidth::Narrow,
        };
        let locale = parse_locale(locale)?;
        let value = parse_decimal(value)?;
        let formatter =
            UnitsFormatter::try_new(locale.into(), unit, UnitsFormatterOptions::from(width))
                .map_err(|error| format_error("unit", profile, error))?;
        Ok(formatter
            .format_fixed_decimal(&value)
            .write_to_string()
            .into_owned())
    }
}

fn validate_two_digit_year_start(
    kind: &str,
    profile: &str,
    start: Option<i32>,
) -> Result<(), Failure> {
    if start.is_some_and(|value| !(1..=9_900).contains(&value)) {
        return Err(Failure::new(
            "I18N_FORMAT_PROFILE",
            format!(
                "{kind} format profile {profile:?} has two_digit_year_start outside 1 through 9900"
            ),
        ));
    }
    Ok(())
}

fn validate_names<'a>(kind: &str, names: impl Iterator<Item = &'a String>) -> Result<(), Failure> {
    for name in names {
        if name.is_empty()
            || !name
                .bytes()
                .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_'))
        {
            return Err(Failure::new(
                "I18N_FORMAT_PROFILE_NAME",
                format!(
                    "{kind} format profile name {name:?} must use only ASCII letters, digits, '-' and '_'"
                ),
            ));
        }
    }
    Ok(())
}

fn require_profile<'a, T>(
    profiles: &'a BTreeMap<String, T>,
    kind: &str,
    profile: &str,
) -> Result<&'a T, Failure> {
    profiles.get(profile).ok_or_else(|| {
        Failure::new(
            "I18N_FORMAT_PROFILE_UNKNOWN",
            format!("unknown {kind} format profile {profile:?}"),
        )
    })
}

fn parse_locale(value: &str) -> Result<Locale, Failure> {
    value.parse().map_err(|error| {
        Failure::new(
            "I18N_FORMAT_LOCALE",
            format!("invalid format locale {value:?}: {error}"),
        )
    })
}

fn parse_decimal(value: &str) -> Result<Decimal, Failure> {
    value.parse().map_err(|error| {
        Failure::new(
            "I18N_FORMAT_NUMBER_VALUE",
            format!("invalid exact decimal {value:?}: {error}"),
        )
    })
}

fn decimal_parse_spec(locale: Locale, profile: &str) -> Result<DecimalParseSpec, Failure> {
    let provider = CapturingDecimalProvider::default();
    DecimalFormatter::try_new_unstable(
        &provider,
        DecimalFormatterPreferences::from(locale),
        Default::default(),
    )
    .map_err(|error| format_error("number parser", profile, error))?;
    let symbols = provider.symbols.into_inner().ok_or_else(|| {
        Failure::new(
            "I18N_NUMBER_PARSE_DATA",
            format!("number profile {profile:?} did not load decimal symbols"),
        )
    })?;
    let digits = provider.digits.into_inner().ok_or_else(|| {
        Failure::new(
            "I18N_NUMBER_PARSE_DATA",
            format!("number profile {profile:?} did not load decimal digits"),
        )
    })?;
    let secondary_group = if symbols.grouping_sizes.secondary == 0 {
        symbols.grouping_sizes.primary
    } else {
        symbols.grouping_sizes.secondary
    };
    Ok(DecimalParseSpec {
        decimal: symbols.decimal_separator().to_owned(),
        digits,
        grouping: symbols.grouping_separator().to_owned(),
        minus_prefix: symbols.minus_sign_prefix().to_owned(),
        minus_suffix: symbols.minus_sign_suffix().to_owned(),
        plus_prefix: symbols.plus_sign_prefix().to_owned(),
        plus_suffix: symbols.plus_sign_suffix().to_owned(),
        primary_group: symbols.grouping_sizes.primary.into(),
        secondary_group: secondary_group.into(),
        numbering_system: symbols.numsys().to_owned(),
    })
}

#[derive(Debug)]
struct PercentAffixPattern {
    prefix: String,
    suffix: String,
    negative: bool,
}

#[derive(Debug)]
struct PercentParseSpec {
    numbers: DecimalParseSpec,
    patterns: [PercentAffixPattern; 3],
}

#[derive(Serialize)]
struct BrowserPercentAffixPattern {
    negative: bool,
    prefix: String,
    suffix: String,
}

#[derive(Serialize)]
struct BrowserPercentParserRecord {
    affix: PercentAffix,
    numbers: BrowserNumberParserRecord,
    patterns: Vec<BrowserPercentAffixPattern>,
}

#[derive(Serialize)]
struct BrowserParserArtifact {
    formats_revision: String,
    locale: String,
    number: BTreeMap<String, BrowserNumberParserRecord>,
    percent: BTreeMap<String, BrowserPercentParserRecord>,
    revision: String,
    schema_version: u32,
}

impl PercentParseSpec {
    fn parse_required(&self, input: &str) -> NumberParseResult {
        let normalized = match normalize_percent_edit(input) {
            Ok(value) => value,
            Err(result) => return result,
        };
        for pattern in &self.patterns {
            let Some(inner) = normalized
                .strip_prefix(&pattern.prefix)
                .and_then(|value| value.strip_suffix(&pattern.suffix))
            else {
                continue;
            };
            return scale_percent_parse_result(self.numbers.parse(inner), pattern.negative);
        }
        if !normalized.contains('%') && !normalized.contains('\u{066a}') {
            NumberParseResult::incomplete("missing_percent_affix")
        } else {
            NumberParseResult::invalid("wrong_percent_affix")
        }
    }
}

fn percent_parse_spec(locale: Locale, profile: &str) -> Result<PercentParseSpec, Failure> {
    let numbers = decimal_parse_spec(locale.clone(), profile)?;
    let decimal_formatter = DecimalFormatter::try_new(locale.clone().into(), Default::default())
        .map_err(|error| format_error("percent parser", profile, error))?;
    let absolute = parse_decimal("1234567.89")?;
    let localized_number = decimal_formatter
        .format(&absolute)
        .write_to_string()
        .into_owned();

    let ordinary = PercentFormatter::try_new(locale.clone().into(), Default::default())
        .map_err(|error| format_error("percent parser", profile, error))?;
    let explicit = PercentFormatter::try_new(
        locale.into(),
        PercentFormatterOptions::from(PercentDisplay::ExplicitSign),
    )
    .map_err(|error| format_error("percent parser", profile, error))?;
    let negative = parse_decimal("-1234567.89")?;
    let unsigned_output = localize_percent_sign(
        ordinary.format(&absolute).write_to_string().into_owned(),
        &numbers.numbering_system,
    );
    let negative_output = localize_percent_sign(
        ordinary.format(&negative).write_to_string().into_owned(),
        &numbers.numbering_system,
    );
    let positive_output = localize_percent_sign(
        explicit.format(&absolute).write_to_string().into_owned(),
        &numbers.numbering_system,
    );
    Ok(PercentParseSpec {
        patterns: [
            percent_affix_pattern(&negative_output, &localized_number, true, profile)?,
            percent_affix_pattern(&positive_output, &localized_number, false, profile)?,
            percent_affix_pattern(&unsigned_output, &localized_number, false, profile)?,
        ],
        numbers,
    })
}

fn percent_affix_pattern(
    output: &str,
    number: &str,
    negative: bool,
    profile: &str,
) -> Result<PercentAffixPattern, Failure> {
    let Some(start) = output.find(number) else {
        return Err(Failure::new(
            "I18N_PERCENT_PARSE_DATA",
            format!("percent profile {profile:?} did not preserve its localized number"),
        ));
    };
    let end = start + number.len();
    Ok(PercentAffixPattern {
        prefix: strip_date_direction_marks(&output[..start]),
        suffix: strip_date_direction_marks(&output[end..]),
        negative,
    })
}

fn normalize_percent_edit(value: &str) -> Result<String, NumberParseResult> {
    if value
        .chars()
        .any(|character| DATE_REJECTED_BIDI_CONTROLS.contains(&character))
    {
        return Err(NumberParseResult::invalid("bidi_control"));
    }
    Ok(strip_date_direction_marks(value))
}

fn scale_percent_parse_result(
    mut result: NumberParseResult,
    force_negative: bool,
) -> NumberParseResult {
    let Some(raw) = result.value.take() else {
        return result;
    };
    let signed = if force_negative && !raw.starts_with('-') {
        format!("-{raw}")
    } else {
        raw
    };
    let Ok(mut value) = signed.parse::<Decimal>() else {
        return NumberParseResult::invalid("number_out_of_range");
    };
    let was_zero = value.is_zero();
    value.multiply_pow10(-2);
    if !was_zero && value.is_zero() {
        return NumberParseResult::invalid("number_out_of_range");
    }
    NumberParseResult::valid(value.write_to_string().into_owned())
}

fn localize_percent_sign(value: String, numbering_system: &str) -> String {
    if matches!(numbering_system, "arab" | "arabext") {
        value.replace('%', "\u{066a}")
    } else {
        value
    }
}

fn require_date_input<'a>(
    profiles: &'a BTreeMap<String, DateProfile>,
    profile: &str,
    expected: DateInputMode,
) -> Result<(&'a DateProfile, &'a DateInputProfile), Failure> {
    let date = require_profile(profiles, "date", profile)?;
    if date.fields != DateFields::YearMonthDay {
        return Err(Failure::new(
            "I18N_DATE_INPUT_FIELDS",
            format!("date format profile {profile:?} must use year_month_day fields for input"),
        ));
    }
    let Some(input) = &date.input else {
        return Err(Failure::new(
            "I18N_DATE_INPUT_MODE",
            format!("date format profile {profile:?} does not declare an input mode"),
        ));
    };
    if input.mode != expected {
        let expected = match expected {
            DateInputMode::StrictText => "strict_text",
            DateInputMode::Segments => "segments",
        };
        return Err(Failure::new(
            "I18N_DATE_INPUT_MODE",
            format!("date format profile {profile:?} does not declare {expected} input"),
        ));
    }
    Ok((date, input))
}

fn require_time_input<'a>(
    profiles: &'a BTreeMap<String, TimeProfile>,
    profile: &str,
    expected: DateInputMode,
) -> Result<(&'a TimeProfile, &'a TimeInputProfile), Failure> {
    let time = require_profile(profiles, "time", profile)?;
    let Some(input) = &time.input else {
        return Err(Failure::new(
            "I18N_TIME_INPUT_MODE",
            format!("time format profile {profile:?} does not declare an input mode"),
        ));
    };
    require_input_mode("time", profile, input.mode, expected)?;
    Ok((time, input))
}

fn require_datetime_input<'a>(
    profiles: &'a BTreeMap<String, DateTimeProfile>,
    profile: &str,
    expected: DateInputMode,
) -> Result<(&'a DateTimeProfile, &'a DateTimeInputProfile), Failure> {
    let datetime = require_profile(profiles, "datetime", profile)?;
    let Some(input) = &datetime.input else {
        return Err(Failure::new(
            "I18N_DATETIME_INPUT_MODE",
            format!("datetime format profile {profile:?} does not declare an input mode"),
        ));
    };
    require_input_mode("datetime", profile, input.mode, expected)?;
    Ok((datetime, input))
}

fn require_input_mode(
    kind: &str,
    profile: &str,
    actual: DateInputMode,
    expected: DateInputMode,
) -> Result<(), Failure> {
    if actual == expected {
        return Ok(());
    }
    let expected = match expected {
        DateInputMode::StrictText => "strict_text",
        DateInputMode::Segments => "segments",
    };
    Err(Failure::new(
        "I18N_TEMPORAL_INPUT_MODE",
        format!("{kind} format profile {profile:?} does not declare {expected} input"),
    ))
}

fn canonical_date_result<A: AsCalendar>(
    calendar: A,
    year: i32,
    month: u8,
    day: u8,
) -> DateParseResult {
    let Ok(value) = Date::try_new(year.into(), Month::new(month), day, calendar) else {
        return DateParseResult::invalid("invalid_date");
    };
    let iso = value.to_calendar(Iso);
    let year = iso.year().extended_year();
    if !(1..=9999).contains(&year) {
        return DateParseResult::invalid("date_out_of_range");
    }
    DateParseResult::valid(DateValue {
        year,
        month: iso.month().ordinal,
        day: iso.day_of_month().0,
    })
}

fn format_error(kind: &str, profile: &str, error: impl std::fmt::Display) -> Failure {
    Failure::new(
        "I18N_FORMAT_DATA",
        format!("could not construct {kind} profile {profile:?}: {error}"),
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    fn registry() -> FormatRegistry {
        FormatRegistry::new(FormatRegistrySpec {
            number: BTreeMap::from([
                ("measurement".to_owned(), NumberProfile::default()),
                (
                    "scientific-edit".to_owned(),
                    NumberProfile {
                        input: NumberInputProfile {
                            notation: NumberInputNotation::DecimalOrScientific,
                        },
                    },
                ),
            ]),
            percent: BTreeMap::from([
                (
                    "completion".to_owned(),
                    PercentProfile {
                        input: PercentInputProfile {
                            affix: PercentAffix::Required,
                        },
                    },
                ),
                (
                    "completion-field".to_owned(),
                    PercentProfile {
                        input: PercentInputProfile {
                            affix: PercentAffix::Omit,
                        },
                    },
                ),
            ]),
            currency: BTreeMap::from([("money".to_owned(), EmptyProfile {})]),
            date: BTreeMap::from([
                (
                    "date-text".to_owned(),
                    DateProfile {
                        fields: DateFields::YearMonthDay,
                        length: DateLength::Short,
                        input: Some(DateInputProfile {
                            mode: DateInputMode::StrictText,
                            two_digit_year_start: None,
                        }),
                    },
                ),
                (
                    "date-text-long".to_owned(),
                    DateProfile {
                        fields: DateFields::YearMonthDay,
                        length: DateLength::Long,
                        input: Some(DateInputProfile {
                            mode: DateInputMode::StrictText,
                            two_digit_year_start: None,
                        }),
                    },
                ),
                (
                    "date-window".to_owned(),
                    DateProfile {
                        fields: DateFields::YearMonthDay,
                        length: DateLength::Short,
                        input: Some(DateInputProfile {
                            mode: DateInputMode::StrictText,
                            two_digit_year_start: Some(1950),
                        }),
                    },
                ),
                (
                    "date-segments".to_owned(),
                    DateProfile {
                        fields: DateFields::YearMonthDay,
                        length: DateLength::Long,
                        input: Some(DateInputProfile {
                            mode: DateInputMode::Segments,
                            two_digit_year_start: None,
                        }),
                    },
                ),
            ]),
            time: BTreeMap::from([
                (
                    "clock".to_owned(),
                    TimeProfile {
                        length: TimeLength::Medium,
                        input: None,
                    },
                ),
                (
                    "time-text".to_owned(),
                    TimeProfile {
                        length: TimeLength::Medium,
                        input: Some(TimeInputProfile {
                            mode: DateInputMode::StrictText,
                        }),
                    },
                ),
                (
                    "time-segments".to_owned(),
                    TimeProfile {
                        length: TimeLength::Medium,
                        input: Some(TimeInputProfile {
                            mode: DateInputMode::Segments,
                        }),
                    },
                ),
            ]),
            datetime: BTreeMap::from([
                (
                    "event".to_owned(),
                    DateTimeProfile {
                        length: DateLength::Medium,
                        time_zone_name: TimeZoneName::None,
                        input: None,
                    },
                ),
                (
                    "event-zone".to_owned(),
                    DateTimeProfile {
                        length: DateLength::Medium,
                        time_zone_name: TimeZoneName::Long,
                        input: None,
                    },
                ),
                (
                    "datetime-text".to_owned(),
                    DateTimeProfile {
                        length: DateLength::Medium,
                        time_zone_name: TimeZoneName::None,
                        input: Some(DateTimeInputProfile {
                            mode: DateInputMode::StrictText,
                            two_digit_year_start: None,
                        }),
                    },
                ),
                (
                    "datetime-segments".to_owned(),
                    DateTimeProfile {
                        length: DateLength::Medium,
                        time_zone_name: TimeZoneName::None,
                        input: Some(DateTimeInputProfile {
                            mode: DateInputMode::Segments,
                            two_digit_year_start: None,
                        }),
                    },
                ),
            ]),
            unit: BTreeMap::from([(
                "measurement".to_owned(),
                UnitProfile {
                    width: UnitWidth::Long,
                },
            )]),
            ..FormatRegistrySpec::default()
        })
        .expect("checked registry")
    }

    fn parsed(value: &str) -> serde_json::Value {
        serde_json::from_str(value).expect("parse result JSON")
    }

    #[test]
    fn browser_parser_artifact_contains_checked_locale_syntax() {
        let artifact = parsed(
            &registry()
                .browser_parser_artifact_json("cs-CZ")
                .expect("browser parser artifact"),
        );

        assert_eq!(artifact["schema_version"], 1);
        assert_eq!(artifact["locale"], "cs-CZ");
        assert_eq!(artifact["number"]["measurement"]["decimal"], ",");
        assert_eq!(artifact["number"]["measurement"]["grouping"], "\u{a0}");
        assert_eq!(
            artifact["number"]["scientific-edit"]["notation"],
            "decimal_or_scientific"
        );
        assert_eq!(artifact["percent"]["completion"]["affix"], "required");
        assert_eq!(artifact["percent"]["completion-field"]["affix"], "omit");
        assert!(
            artifact["revision"]
                .as_str()
                .is_some_and(|value| !value.is_empty())
        );
    }

    #[test]
    fn localized_number_parser_returns_valid_incomplete_and_invalid_states() {
        let formats = registry();
        assert_eq!(
            parsed(
                &formats
                    .parse_number_json("en-US", "measurement", "1,234.5")
                    .unwrap()
            ),
            serde_json::json!({"state": "valid", "value": "1234.5", "error": null})
        );
        assert_eq!(
            parsed(
                &formats
                    .parse_number_json("en-US", "measurement", "1,")
                    .unwrap()
            ),
            serde_json::json!({"state": "incomplete", "value": null, "error": "unfinished_group"})
        );
        assert_eq!(
            parsed(
                &formats
                    .parse_number_json("en-US", "measurement", "1,2345")
                    .unwrap()
            ),
            serde_json::json!({"state": "invalid", "value": null, "error": "wrong_primary_group"})
        );
    }

    #[test]
    fn localized_number_parser_uses_the_profiles_resolved_digits_and_signs() {
        let formats = registry();
        assert_eq!(
            parsed(
                &formats
                    .parse_number_json("ar-EG", "measurement", "٩٬٠٠٧٫٢٥")
                    .unwrap()
            ),
            serde_json::json!({"state": "valid", "value": "9007.25", "error": null})
        );
        let negative = formats.number("ar-EG", "measurement", "-1234.5").unwrap();
        assert_eq!(
            parsed(
                &formats
                    .parse_number_json("ar-EG", "measurement", &negative)
                    .unwrap()
            ),
            serde_json::json!({"state": "valid", "value": "-1234.5", "error": null})
        );
        assert_eq!(
            parsed(
                &formats
                    .parse_number_json("ar-EG", "measurement", "٩٬00٧٫٢٥")
                    .unwrap()
            )["state"],
            "invalid"
        );
    }

    #[test]
    fn localized_number_parser_accepts_explicit_scientific_notation() {
        let formats = registry();
        assert_eq!(
            parsed(
                &formats
                    .parse_number_json("en-US", "scientific-edit", "1.25e3")
                    .unwrap()
            ),
            serde_json::json!({"state": "valid", "value": "1250", "error": null})
        );
        assert_eq!(
            parsed(
                &formats
                    .parse_number_json("ar-EG", "scientific-edit", "١٫٢٥e٣")
                    .unwrap()
            ),
            serde_json::json!({"state": "valid", "value": "1250", "error": null})
        );
        assert_eq!(
            parsed(
                &formats
                    .parse_number_json("en-US", "scientific-edit", "1e+")
                    .unwrap()
            )["state"],
            "incomplete"
        );
        assert_eq!(
            parsed(
                &formats
                    .parse_number_json("en-US", "measurement", "1e3")
                    .unwrap()
            )["state"],
            "invalid"
        );
    }

    #[test]
    fn percent_uses_ratio_values_and_round_trips_required_or_omitted_affixes() {
        let formats = registry();
        assert_eq!(
            formats.percent("en-US", "completion", "0.125").unwrap(),
            "12.5%"
        );
        assert_eq!(
            formats.percent("tr", "completion", "0.125").unwrap(),
            "%12,5"
        );
        assert_eq!(
            parsed(
                &formats
                    .parse_percent_json("en-US", "completion", "12.5%")
                    .unwrap()
            ),
            serde_json::json!({"state": "valid", "value": "0.125", "error": null})
        );
        assert_eq!(
            parsed(
                &formats
                    .parse_percent_json("en-US", "completion", "12.5")
                    .unwrap()
            ),
            serde_json::json!({
                "state": "incomplete",
                "value": null,
                "error": "missing_percent_affix"
            })
        );
        assert_eq!(
            parsed(
                &formats
                    .parse_percent_json("en-US", "completion-field", "12.5")
                    .unwrap()
            ),
            serde_json::json!({"state": "valid", "value": "0.125", "error": null})
        );
    }

    #[test]
    fn percent_parser_accepts_the_formatter_owned_arabic_affix_and_sign() {
        let formats = registry();
        let rendered = formats.percent("ar-EG", "completion", "-0.125").unwrap();
        assert!(rendered.contains('٪'));
        assert_eq!(
            parsed(
                &formats
                    .parse_percent_json("ar-EG", "completion", &rendered)
                    .unwrap()
            ),
            serde_json::json!({"state": "valid", "value": "-0.125", "error": null})
        );
    }

    #[test]
    fn percent_parser_rejects_wrong_affixes_and_bidi_controls() {
        let formats = registry();
        assert_eq!(
            parsed(
                &formats
                    .parse_percent_json("tr", "completion", "12,5%")
                    .unwrap()
            ),
            serde_json::json!({
                "state": "invalid",
                "value": null,
                "error": "wrong_percent_affix"
            })
        );
        assert_eq!(
            parsed(
                &formats
                    .parse_percent_json("en-US", "completion", "12.5\u{202e}%")
                    .unwrap()
            ),
            serde_json::json!({"state": "invalid", "value": null, "error": "bidi_control"})
        );
    }

    #[test]
    fn strict_date_parser_uses_locale_order_digits_and_selected_calendar() {
        let formats = registry();
        for (locale, input) in [
            ("en-US", "8/10/2026"),
            ("cs-CZ", "10. 08. 2026"),
            ("ar-EG", "١٠/٨/٢٠٢٦"),
            ("hi-IN-u-nu-deva", "१०/८/२०२६"),
            ("th-TH-u-ca-buddhist", "10/8/2569"),
        ] {
            assert_eq!(
                parsed(&formats.parse_date_json(locale, "date-text", input).unwrap()),
                serde_json::json!({
                    "state": "valid",
                    "value": {"year": 2026, "month": 8, "day": 10},
                    "error": null
                }),
                "locale {locale}"
            );
        }
    }

    #[test]
    fn date_parser_preserves_partial_edits_and_rejects_impossible_dates() {
        let formats = registry();
        assert_eq!(
            parsed(
                &formats
                    .parse_date_json("en-US", "date-text", "8/10/20")
                    .unwrap()
            )["state"],
            "incomplete"
        );
        assert_eq!(
            parsed(
                &formats
                    .parse_date_json("en-US", "date-text", "2/29/2025")
                    .unwrap()
            ),
            serde_json::json!({"state": "invalid", "value": null, "error": "invalid_date"})
        );
        assert_eq!(
            parsed(
                &formats
                    .parse_date_json("en-US", "date-text", "8.10.2026")
                    .unwrap()
            ),
            serde_json::json!({
                "state": "invalid",
                "value": null,
                "error": "wrong_date_separator"
            })
        );
        assert_eq!(
            parsed(
                &formats
                    .parse_date_json("en-US", "date-text", "8/10/2026\u{2067}")
                    .unwrap()
            ),
            serde_json::json!({"state": "invalid", "value": null, "error": "bidi_control"})
        );
    }

    #[test]
    fn date_parser_rejects_unratified_calendar_input() {
        let formats = registry();
        for locale in [
            "ja-JP-u-ca-japanese",
            "zh-TW-u-ca-roc",
            "zh-CN-u-ca-chinese",
            "ko-KR-u-ca-dangi",
            "he-IL-u-ca-hebrew",
        ] {
            let error = formats
                .parse_date_segments_json(locale, "date-segments", "8", "8", "10")
                .unwrap_err();
            assert_eq!(error.code(), "I18N_DATE_INPUT_CALENDAR", "{locale}");
        }
    }

    #[test]
    fn segmented_date_parser_uses_named_fields_and_locale_digits() {
        let formats = registry();
        assert_eq!(
            parsed(
                &formats
                    .parse_date_segments_json(
                        "th-TH-u-ca-buddhist",
                        "date-segments",
                        "2569",
                        "8",
                        "10",
                    )
                    .unwrap()
            ),
            serde_json::json!({
                "state": "valid",
                "value": {"year": 2026, "month": 8, "day": 10},
                "error": null
            })
        );
    }

    #[test]
    fn date_parser_handles_month_names_two_digit_windows_and_persian_dates() {
        let formats = registry();
        let rendered = formats
            .date("cs-CZ", "date-text-long", 2026, 8, 10)
            .unwrap();
        assert_eq!(
            parsed(
                &formats
                    .parse_date_json("cs-CZ", "date-text-long", &rendered)
                    .unwrap()
            )["value"],
            serde_json::json!({"year": 2026, "month": 8, "day": 10})
        );
        assert_eq!(
            parsed(
                &formats
                    .parse_date_json("en-US", "date-window", "8/10/49")
                    .unwrap()
            )["value"],
            serde_json::json!({"year": 2049, "month": 8, "day": 10})
        );
        assert_eq!(
            parsed(
                &formats
                    .parse_date_segments_json(
                        "fa-IR-u-ca-persian",
                        "date-segments",
                        "۱۴۰۵",
                        "۵",
                        "۱۹",
                    )
                    .unwrap()
            )["value"],
            serde_json::json!({"year": 2026, "month": 8, "day": 10})
        );
    }

    #[test]
    fn date_parser_round_trips_supported_unambiguous_calendars() {
        let formats = registry();
        for locale in [
            "th-TH-u-ca-buddhist",
            "cop-EG-u-ca-coptic",
            "am-ET-u-ca-ethiopic",
            "am-ET-u-ca-ethioaa",
            "ar-SA-u-ca-islamic-civil",
            "ar-SA-u-ca-islamic-tbla",
            "ar-SA-u-ca-islamic-umalqura",
            "hi-IN-u-ca-indian",
            "en-US-u-ca-iso8601",
            "fa-IR-u-ca-persian",
        ] {
            let rendered = formats.date(locale, "date-text-long", 2026, 8, 10).unwrap();
            assert_eq!(
                parsed(
                    &formats
                        .parse_date_json(locale, "date-text-long", &rendered)
                        .unwrap_or_else(|error| panic!("locale {locale}: {error}"))
                )["value"],
                serde_json::json!({"year": 2026, "month": 8, "day": 10}),
                "locale {locale} rendered {rendered:?}"
            );
        }
    }

    #[test]
    fn time_and_datetime_parsers_preserve_local_fields() {
        let formats = registry();
        let rendered = formats.time("en-US", "time-text", 14, 5, 9, 0).unwrap();
        assert_eq!(
            parsed(
                &formats
                    .parse_time_json("en-US", "time-text", &rendered)
                    .unwrap()
            )["value"],
            serde_json::json!({"hour": 14, "minute": 5, "second": 9, "nanosecond": 0})
        );
        assert_eq!(
            parsed(
                &formats
                    .parse_time_segments_json(
                        "en-US",
                        "time-segments",
                        "2",
                        "05",
                        Some("09"),
                        Some("PM"),
                    )
                    .unwrap()
            )["value"],
            serde_json::json!({"hour": 14, "minute": 5, "second": 9, "nanosecond": 0})
        );
        assert_eq!(
            parsed(
                &formats
                    .parse_datetime_segments_json(
                        "en-US",
                        "datetime-segments",
                        "2026",
                        "10",
                        "25",
                        "2",
                        "30",
                        Some("00"),
                        Some("AM"),
                    )
                    .unwrap()
            )["value"],
            serde_json::json!({
                "year": 2026,
                "month": 10,
                "day": 25,
                "hour": 2,
                "minute": 30,
                "second": 0,
                "nanosecond": 0
            })
        );
    }

    #[test]
    fn unit_formatter_keeps_exact_values_and_explicit_units() {
        let formats = registry();
        assert_eq!(
            formats
                .unit("en-US", "measurement", "1.5", "meter")
                .unwrap(),
            "1.5 meters"
        );
        assert_eq!(
            formats
                .unit("ar-EG", "measurement", "9007199254740993.25", "meter",)
                .unwrap(),
            "٩٬٠٠٧٬١٩٩٬٢٥٤٬٧٤٠٬٩٩٣٫٢٥ متر"
        );
    }

    #[test]
    fn currency_uses_data_driven_fraction_digits_and_half_expand_rounding() {
        let formats = registry();
        assert_eq!(
            formats.currency("en-US", "money", "12.5", "EUR").unwrap(),
            "€12.50"
        );
        assert_eq!(
            formats.currency("en-US", "money", "12", "USD").unwrap(),
            "$12.00"
        );
        assert_eq!(
            formats.currency("ja-JP", "money", "12.50", "JPY").unwrap(),
            "￥13"
        );
    }

    #[test]
    fn temporal_profiles_keep_wall_time_separate_from_resolved_zone_facts() {
        let formats = registry();
        assert_eq!(
            formats.time("en-US", "clock", 14, 5, 9, 0).unwrap(),
            "2:05:09\u{202f}PM"
        );
        assert_eq!(
            formats
                .datetime(
                    "en-US",
                    "event",
                    2026,
                    1,
                    15,
                    13,
                    0,
                    0,
                    0,
                    "Europe/Prague",
                    3_600,
                    1_768_478_400,
                )
                .unwrap(),
            "Jan 15, 2026, 1:00:00\u{202f}PM"
        );
        assert!(
            formats
                .datetime(
                    "en-US",
                    "event-zone",
                    2026,
                    1,
                    15,
                    13,
                    0,
                    0,
                    0,
                    "Europe/Prague",
                    3_600,
                    1_768_478_400,
                )
                .unwrap()
                .contains("Central European Standard Time")
        );
    }

    #[test]
    fn format_registry_rejects_two_digit_year_windows_outside_python_date_range() {
        let error = FormatRegistry::new(FormatRegistrySpec {
            date: BTreeMap::from([(
                "broken".to_owned(),
                DateProfile {
                    fields: DateFields::YearMonthDay,
                    length: DateLength::Short,
                    input: Some(DateInputProfile {
                        mode: DateInputMode::StrictText,
                        two_digit_year_start: Some(9_901),
                    }),
                },
            )]),
            ..FormatRegistrySpec::default()
        })
        .unwrap_err();
        assert_eq!(error.code(), "I18N_FORMAT_PROFILE");
        assert!(error.to_string().contains("1 through 9900"));
    }
}
