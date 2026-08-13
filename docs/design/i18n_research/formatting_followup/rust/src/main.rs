use fixed_decimal::Decimal;
use icu::experimental::dimension::percent::formatter::PercentFormatter;
use icu::experimental::dimension::units::formatter::UnitsFormatter;
use icu::experimental::dimension::units::options::{UnitsFormatterOptions, Width};
use icu::locale::locale;
use icu::plurals::{PluralOperands, PluralRules};
use writeable::Writeable;

fn escaped(value: &str) -> String {
    value.chars().flat_map(char::escape_unicode).collect()
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let locale = locale!("ar-EG");
    let plurals = PluralRules::try_new_cardinal(locale.clone().into())?;
    let units = UnitsFormatter::try_new(
        locale.clone().into(),
        "meter",
        UnitsFormatterOptions::from(Width::Long),
    )?;

    for raw in ["11", "11.25", "12345.67", "9007199254740993.25"] {
        let value: Decimal = raw.parse()?;
        let operands = PluralOperands::from(&value);
        let category = plurals.category_for(operands);
        let formatted = units
            .format_fixed_decimal(&value)
            .write_to_string()
            .into_owned();

        println!(
            "unit raw={raw} operands={operands:?} category={category:?} output={} escaped={}",
            formatted,
            escaped(&formatted),
        );
    }

    let percent = PercentFormatter::try_new(locale.into(), Default::default())?;
    for raw in ["0.125", "12.5"] {
        let value: Decimal = raw.parse()?;
        let formatted = percent.format(&value).write_to_string().into_owned();
        println!(
            "percent raw={raw} output={} escaped={}",
            formatted,
            escaped(&formatted),
        );
    }

    Ok(())
}
