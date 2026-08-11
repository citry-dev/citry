//! Checked ICU4X formatter profiles shared by messages and direct Python calls.

#![allow(clippy::result_large_err)]

use std::cell::RefCell;
use std::collections::BTreeMap;

use fixed_decimal::{SignedRoundingMode, UnsignedRoundingMode};
use icu::datetime::input::{Date, DateTime, Time, ZonedDateTime};
use icu::datetime::{DateTimeFormatter, fieldsets};
use icu::decimal::DecimalFormatter;
use icu::decimal::DecimalFormatterPreferences;
use icu::decimal::input::Decimal;
use icu::decimal::provider::{
    Baked as DecimalBaked, DecimalDigitsV1, DecimalSymbols, DecimalSymbolsV1,
};
use icu::experimental::dimension::currency::CurrencyCode;
use icu::experimental::dimension::currency::formatter::CurrencyFormatter;
use icu::experimental::dimension::provider::currency::fractions::{
    Baked as ExperimentalBaked, CurrencyFractionsV1,
};
use icu::experimental::relativetime::{RelativeTimeFormatter, RelativeTimeFormatterOptions};
use icu::list::ListFormatter;
use icu::list::options::{ListFormatterOptions, ListLength};
use icu::locale::Locale;
use icu::time::zone::{TimeZone, UtcOffset, ZoneNameTimestamp};
use icu_provider::prelude::{DataProvider, DataRequest};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use tinystr::TinyAsciiStr;
use writeable::Writeable;

use crate::compiler::Failure;

#[derive(Debug, Clone, Serialize)]
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
}

impl DecimalParseSpec {
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

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct FormatRegistrySpec {
    #[serde(default)]
    number: BTreeMap<String, EmptyProfile>,
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
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct EmptyProfile {}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct DateProfile {
    length: DateLength,
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

#[derive(Debug, Clone)]
pub(crate) struct FormatRegistry {
    spec: FormatRegistrySpec,
    revision: String,
}

impl FormatRegistry {
    pub(crate) fn new(spec: FormatRegistrySpec) -> Result<Self, Failure> {
        validate_names("number", spec.number.keys())?;
        validate_names("currency", spec.currency.keys())?;
        validate_names("date", spec.date.keys())?;
        validate_names("time", spec.time.keys())?;
        validate_names("datetime", spec.datetime.keys())?;
        validate_names("relative_time", spec.relative_time.keys())?;
        validate_names("list", spec.list.keys())?;
        let encoded = serde_json::to_vec(&spec)
            .map_err(|error| Failure::new("I18N_FORMAT_PROFILE_JSON", error.to_string()))?;
        let revision = format!("{:x}", Sha256::digest(encoded));
        Ok(Self { spec, revision })
    }

    pub(crate) fn revision(&self) -> &str {
        &self.revision
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
        require_profile(&self.spec.number, "number", profile)?;
        let locale = parse_locale(locale)?;
        let parser = decimal_parse_spec(locale, profile)?;
        serde_json::to_string(&parser.parse(input))
            .map_err(|error| Failure::new("I18N_NUMBER_PARSE_JSON", error.to_string()))
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
        let result = match spec.length {
            DateLength::Short => {
                DateTimeFormatter::try_new(locale.clone().into(), fieldsets::YMD::short())
                    .map_err(|error| format_error("date", profile, error))?
                    .format(&value)
                    .write_to_string()
                    .into_owned()
            }
            DateLength::Medium => {
                DateTimeFormatter::try_new(locale.clone().into(), fieldsets::YMD::medium())
                    .map_err(|error| format_error("date", profile, error))?
                    .format(&value)
                    .write_to_string()
                    .into_owned()
            }
            DateLength::Long => DateTimeFormatter::try_new(locale.into(), fieldsets::YMD::long())
                .map_err(|error| format_error("date", profile, error))?
                .format(&value)
                .write_to_string()
                .into_owned(),
        };
        Ok(result)
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
            number: BTreeMap::from([("measurement".to_owned(), EmptyProfile {})]),
            currency: BTreeMap::from([("money".to_owned(), EmptyProfile {})]),
            time: BTreeMap::from([(
                "clock".to_owned(),
                TimeProfile {
                    length: TimeLength::Medium,
                },
            )]),
            datetime: BTreeMap::from([
                (
                    "event".to_owned(),
                    DateTimeProfile {
                        length: DateLength::Medium,
                        time_zone_name: TimeZoneName::None,
                    },
                ),
                (
                    "event-zone".to_owned(),
                    DateTimeProfile {
                        length: DateLength::Medium,
                        time_zone_name: TimeZoneName::Long,
                    },
                ),
            ]),
            ..FormatRegistrySpec::default()
        })
        .expect("checked registry")
    }

    fn parsed(value: &str) -> serde_json::Value {
        serde_json::from_str(value).expect("parse result JSON")
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
}
