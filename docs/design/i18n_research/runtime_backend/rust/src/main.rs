use std::fs;
use std::path::Path;
use std::sync::Arc;

use fluent_bundle::concurrent::FluentBundle;
use fluent_bundle::{FluentArgs, FluentResource, FluentValue};
use serde_json::{Map, Value, json};
use unic_langid::LanguageIdentifier;

type Bundle = FluentBundle<Arc<FluentResource>>;
const FSI: &str = "\u{2068}";
const LRI: &str = "\u{2066}";
const RLI: &str = "\u{2067}";
const PDI: &str = "\u{2069}";
const HOSTILE_NAME: &str = "אבג <Ada&Co>";
const BIDI_CONTROLS: [char; 12] = [
    '\u{061c}', '\u{200e}', '\u{200f}', '\u{202a}', '\u{202b}', '\u{202c}', '\u{202d}', '\u{202e}',
    '\u{2066}', '\u{2067}', '\u{2068}', '\u{2069}',
];
const BIDI_PARAGRAPH_BOUNDARIES: [char; 7] = [
    '\n', '\r', '\u{001c}', '\u{001d}', '\u{001e}', '\u{0085}', '\u{2029}',
];

fn assert_send_sync<T: Send + Sync>() {}

fn value_text(value: &FluentValue<'_>) -> Option<String> {
    match value {
        FluentValue::String(value) => Some(value.to_string()),
        FluentValue::Number(value) => Some(if value.value.fract() == 0.0 {
            format!("{:.0}", value.value)
        } else {
            value.value.to_string()
        }),
        _ => None,
    }
}

fn named_text(named: &FluentArgs<'_>, name: &str) -> Option<String> {
    named.get(name).and_then(value_text)
}

fn register_functions(bundle: &mut Bundle, locale: &str) {
    bundle
        .add_function("NUMBER", |positional, named| {
            let Some(value) = positional.first().and_then(value_text) else {
                return FluentValue::Error;
            };
            let Some(profile) = named_text(named, "profile") else {
                return FluentValue::Error;
            };
            let suffix = named_text(named, "currency")
                .map(|currency| format!(",currency={currency}"))
                .unwrap_or_default();
            format!("{FSI}NUM[value={value},profile={profile}{suffix}]{PDI}").into()
        })
        .expect("NUMBER registration failed");
    bundle
        .add_function("DATETIME", |positional, named| {
            let Some(value) = positional.first().and_then(value_text) else {
                return FluentValue::Error;
            };
            let Some(profile) = named_text(named, "profile") else {
                return FluentValue::Error;
            };
            format!("{FSI}DATE[value={value},profile={profile}]{PDI}").into()
        })
        .expect("DATETIME registration failed");
    bundle
        .add_function("SLOT", |positional, named| {
            if named.iter().next().is_some() {
                return FluentValue::Error;
            }
            match positional.first().and_then(value_text) {
                Some(value) if value.starts_with("__CITRY_SLOT_") => value.into(),
                _ => FluentValue::Error,
            }
        })
        .expect("SLOT registration failed");
    bundle
        .add_function("CITRY_TEXT", |positional, named| {
            if named.iter().next().is_some() {
                return FluentValue::Error;
            }
            match positional.first().and_then(value_text) {
                Some(value)
                    if !value.chars().any(|char| BIDI_CONTROLS.contains(&char))
                        && !value
                            .chars()
                            .any(|char| BIDI_PARAGRAPH_BOUNDARIES.contains(&char)) =>
                {
                    format!("{FSI}{value}{PDI}").into()
                }
                _ => FluentValue::Error,
            }
        })
        .expect("CITRY_TEXT registration failed");
    let is_czech = locale == "cs-CZ";
    bundle
        .add_function("CITRY_PLURAL", move |positional, named| {
            if named
                .iter()
                .any(|(name, _)| !matches!(name, "exact" | "mode"))
            {
                return FluentValue::Error;
            }
            let Some(value) = positional.first().and_then(value_text) else {
                return FluentValue::Error;
            };
            let Ok(value) = value.parse::<f64>() else {
                return FluentValue::Error;
            };
            let mode = named_text(named, "mode").unwrap_or_else(|| "cardinal".to_owned());
            if mode == "ordinal" {
                if !is_czech && value.fract() == 0.0 {
                    let value = value as i64;
                    if !matches!(value % 100, 11..=13) {
                        return match value % 10 {
                            1 => "one".into(),
                            2 => "two".into(),
                            3 => "few".into(),
                            _ => "other".into(),
                        };
                    }
                }
                return "other".into();
            }
            if mode != "cardinal" {
                return FluentValue::Error;
            }
            if let Some(matched) = named_text(named, "exact").and_then(|values| {
                values
                    .split(',')
                    .find(|candidate| candidate.parse::<f64>().is_ok_and(|item| item == value))
                    .map(str::to_owned)
            }) {
                return format!("exact-{matched}").into();
            }
            if is_czech {
                if value.fract() != 0.0 {
                    "many".into()
                } else if value == 1.0 {
                    "one".into()
                } else if (2.0..=4.0).contains(&value) {
                    "few".into()
                } else {
                    "other".into()
                }
            } else if value == 1.0 {
                "one".into()
            } else {
                "other".into()
            }
        })
        .expect("CITRY_PLURAL registration failed");
}

fn marker_for(seed: &str, locale: &str) -> String {
    format!(
        "__CITRY_SLOT_{}_{}_terms_link__",
        seed,
        locale.replace('-', "_")
    )
}

fn validate_catalog_source(source: &str) -> Result<(), String> {
    if source.chars().any(|char| BIDI_CONTROLS.contains(&char)) {
        return Err("authored catalog contains a prohibited bidi-control character".to_owned());
    }
    Ok(())
}

fn validate_decoded_catalog_text(value: &str) -> Result<(), String> {
    if value.chars().any(|char| BIDI_CONTROLS.contains(&char)) {
        return Err("decoded catalog contains a prohibited bidi-control character".to_owned());
    }
    Ok(())
}

fn isolate_known_direction_paragraphs(value: &str, direction: &str) -> String {
    let initiator = if direction == "ltr" { LRI } else { RLI };
    let chars: Vec<char> = value.chars().collect();
    let mut output = String::new();
    let mut start = 0;
    let mut index = 0;
    while index < chars.len() {
        if !BIDI_PARAGRAPH_BOUNDARIES.contains(&chars[index]) {
            index += 1;
            continue;
        }
        output.push_str(initiator);
        output.extend(&chars[start..index]);
        output.push_str(PDI);
        let mut end = index + 1;
        if chars[index] == '\r' && chars.get(end) == Some(&'\n') {
            end += 1;
        }
        output.extend(&chars[index..end]);
        start = end;
        index = end;
    }
    output.push_str(initiator);
    output.extend(&chars[start..]);
    output.push_str(PDI);
    output
}

fn try_bundle_for(locale_name: &str, source: String) -> Result<Bundle, String> {
    validate_catalog_source(&source)?;
    let locale: LanguageIdentifier = locale_name
        .parse()
        .map_err(|error| format!("invalid locale fixture: {error}"))?;
    let resource = FluentResource::try_new(source)
        .map_err(|(_, errors)| format!("Fluent parse errors: {errors:?}"))?;
    let mut bundle = Bundle::new_concurrent(vec![locale]);
    bundle.set_use_isolating(false);
    register_functions(&mut bundle, locale_name);
    bundle
        .add_resource(Arc::new(resource))
        .map_err(|errors| format!("resource registration failed: {errors:?}"))?;
    Ok(bundle)
}

fn bundle_for(locale_name: &str, source: String) -> Bundle {
    try_bundle_for(locale_name, source).expect("fixture bundle construction failed")
}

fn validate_runtime_contract(
    message_id: &str,
    args: &FluentArgs<'_>,
    marker: Option<&str>,
) -> Result<(), String> {
    for (_, value) in args.iter() {
        if value_text(value)
            .is_some_and(|value| value.chars().any(|char| BIDI_CONTROLS.contains(&char)))
        {
            return Err(format!(
                "{message_id} contains a prohibited bidi-control scalar"
            ));
        }
        if value_text(value).is_some_and(|value| {
            value
                .chars()
                .any(|char| BIDI_PARAGRAPH_BOUNDARIES.contains(&char))
        }) {
            return Err(format!(
                "{message_id} contains a prohibited bidi-paragraph scalar"
            ));
        }
    }
    if matches!(
        message_id,
        "inbox-count" | "acceptance" | "invalid-plural-input" | "ordinal-position"
    ) {
        let field = match message_id {
            "invalid-plural-input" => "value",
            "ordinal-position" => "position",
            _ => "count",
        };
        let valid = matches!(
            args.get(field),
            Some(FluentValue::Number(value))
                if value.value.is_finite() && value.value.abs() <= 9_007_199_254_740_991.0
        );
        if !valid {
            return Err(format!(
                "{message_id} ${field} must be a finite safe number before resolution"
            ));
        }
    }
    if message_id == "acceptance"
        && value_text(args.get("terms_link").unwrap_or(&FluentValue::None)).as_deref() != marker
    {
        return Err("acceptance $terms_link must be the current opaque Slot marker".to_owned());
    }
    if message_id == "slot-function-scalar"
        && value_text(args.get("value").unwrap_or(&FluentValue::None)).as_deref() != marker
    {
        return Err("slot-function-scalar $value must be a Slot before resolution".to_owned());
    }
    Ok(())
}

fn format_value(
    bundle: &Bundle,
    message_id: &str,
    args: &FluentArgs<'_>,
    attribute: Option<&str>,
    marker: Option<&str>,
    validate: bool,
) -> Result<String, String> {
    if validate {
        validate_runtime_contract(message_id, args, marker)?;
    }
    let message = bundle
        .get_message(message_id)
        .ok_or_else(|| format!("missing message {message_id}"))?;
    let pattern = match attribute {
        Some(attribute) => message
            .get_attribute(attribute)
            .ok_or_else(|| format!("missing attribute {message_id}.{attribute}"))?
            .value(),
        None => message
            .value()
            .ok_or_else(|| format!("missing message value {message_id}"))?,
    };
    let mut errors = vec![];
    let value = bundle.format_pattern(pattern, Some(args), &mut errors);
    if errors.is_empty() {
        Ok(value.into_owned())
    } else {
        Err(format!("{errors:?}"))
    }
}

fn args(marker: &str, count: f64) -> FluentArgs<'_> {
    let mut args = FluentArgs::new();
    args.set("account_name", HOSTILE_NAME);
    args.set("amount", 1234.5_f64);
    args.set("count", count);
    args.set("due_ms", 1_782_864_000_000_i64);
    args.set("position", 2_i64);
    args.set("terms_link", marker);
    args
}

fn args_with_position(marker: &str, position: i64) -> FluentArgs<'_> {
    let mut values = args(marker, 2.0);
    values.set("position", position);
    values
}

fn ensure_no_collision(source: &str, scalar_values: &[&str], marker: &str) -> Result<(), String> {
    if source.contains(marker) {
        return Err("slot marker collides with a catalog resource".to_owned());
    }
    if scalar_values.iter().any(|value| value.contains(marker)) {
        return Err("slot marker collides with a scalar input".to_owned());
    }
    Ok(())
}

fn split_slot(value: &str, marker: &str) -> Result<Value, String> {
    let count = value.matches(marker).count();
    if count == 0 {
        return Err("expected at least one slot marker, received 0".to_owned());
    }
    let isolated_marker = format!("{FSI}{marker}{PDI}");
    if value.contains(&isolated_marker) {
        return Err("slot marker was unexpectedly wrapped as scalar text".to_owned());
    }
    let mut output = Vec::with_capacity(count * 2 + 1);
    for (index, part) in value.split(marker).enumerate() {
        output.push(json!({"kind": "text", "value": part}));
        if index < count {
            output.push(json!({"kind": "slot", "name": "terms_link", "occurrence": index}));
        }
    }
    Ok(Value::Array(output))
}

fn config_strings(config: &Value, key: &str) -> Vec<String> {
    config[key]
        .as_array()
        .unwrap_or_else(|| panic!("{key} must be an array"))
        .iter()
        .map(|value| {
            value
                .as_str()
                .unwrap_or_else(|| panic!("{key} entries must be strings"))
                .to_owned()
        })
        .collect()
}

fn hostile_catalog_sources(control_hex: &[String], forms: &[String]) -> Vec<String> {
    let mut sources = vec![];
    for hex_value in control_hex {
        let codepoint = u32::from_str_radix(hex_value, 16).expect("invalid hostile code point");
        for form in forms {
            let encoded = match form.as_str() {
                "literal" => char::from_u32(codepoint)
                    .expect("hostile code point is not a scalar")
                    .to_string(),
                "u4" => format!("{{ \"\\u{hex_value}\" }}"),
                "U6" => format!("{{ \"\\U{codepoint:06X}\" }}"),
                _ => panic!("unknown hostile catalog escape form {form}"),
            };
            sources.push(format!("hostile = {encoded}"));
        }
    }
    sources
}

fn main() {
    assert_send_sync::<Bundle>();

    let mut argv = std::env::args().skip(1);
    let fixtures = argv.next().expect("fixtures path argument missing");
    let marker_seed = argv.next().expect("slot marker seed argument missing");
    let fixtures = Path::new(&fixtures);
    let generated_layers = fs::read_to_string(fixtures.join("layered-generated.ftl"))
        .expect("generated layer fixture read failed");
    let hostile_config: Value = serde_json::from_str(
        &fs::read_to_string(fixtures.join("hostile-bidi-control.json"))
            .expect("hostile catalog fixture read failed"),
    )
    .expect("hostile catalog fixture JSON failed");
    let bidi_control_hex = config_strings(&hostile_config, "bidi_control_hex");
    let paragraph_boundary_hex = config_strings(&hostile_config, "paragraph_boundary_hex");
    let fluent_escape_forms = config_strings(&hostile_config, "fluent_escape_forms");
    let mut cases = Map::new();
    let mut markers = vec![];
    let mut resolution_markers_distinct = true;
    let mut sources = Map::new();

    for locale in ["en-US", "cs-CZ"] {
        let marker = marker_for(&marker_seed, locale);
        markers.push(marker.clone());
        let source = format!(
            "{}\n{}",
            fs::read_to_string(fixtures.join(format!("{locale}.ftl")))
                .expect("fixture read failed"),
            generated_layers,
        );
        sources.insert(locale.to_owned(), Value::String(source.clone()));
        ensure_no_collision(&source, &[HOSTILE_NAME], &marker).unwrap();
        let bundle = bundle_for(locale, source);
        let normal = args(&marker, 2.0);
        let rich = split_slot(
            &format_value(&bundle, "acceptance", &normal, None, Some(&marker), true).unwrap(),
            &marker,
        )
        .unwrap();
        let second_marker = marker_for(&format!("{marker_seed}_resolution_2"), locale);
        resolution_markers_distinct &= second_marker != marker;
        ensure_no_collision(
            sources[locale].as_str().expect("source is text"),
            &[HOSTILE_NAME],
            &second_marker,
        )
        .unwrap();
        let second_args = args(&second_marker, 2.0);
        let second_rich = split_slot(
            &format_value(
                &bundle,
                "acceptance",
                &second_args,
                None,
                Some(&second_marker),
                true,
            )
            .unwrap(),
            &second_marker,
        )
        .unwrap();
        assert_eq!(
            rich, second_rich,
            "normalized rich output changed across fresh markers"
        );
        let result = json!({
            "summary": format_value(&bundle, "account-summary", &normal, None, Some(&marker), true).unwrap(),
            "attribute": format_value(&bundle, "account-actions", &normal, Some("aria-label"), Some(&marker), true).unwrap(),
            "plural_0": format_value(&bundle, "inbox-count", &args(&marker, 0.0), None, Some(&marker), true).unwrap(),
            "plural_negative_zero": format_value(&bundle, "inbox-count", &args(&marker, -0.0), None, Some(&marker), true).unwrap(),
            "plural_1": format_value(&bundle, "inbox-count", &args(&marker, 1.0), None, Some(&marker), true).unwrap(),
            "plural_2": format_value(&bundle, "inbox-count", &normal, None, Some(&marker), true).unwrap(),
            "plural_1_5": format_value(&bundle, "inbox-count", &args(&marker, 1.5), None, Some(&marker), true).unwrap(),
            "plural_2_5": format_value(&bundle, "inbox-count", &args(&marker, 2.5), None, Some(&marker), true).unwrap(),
            "plural_5": format_value(&bundle, "inbox-count", &args(&marker, 5.0), None, Some(&marker), true).unwrap(),
            "ordinal_1": format_value(&bundle, "ordinal-position", &args_with_position(&marker, 1), None, Some(&marker), true).unwrap(),
            "ordinal_2": format_value(&bundle, "ordinal-position", &normal, None, Some(&marker), true).unwrap(),
            "ordinal_3": format_value(&bundle, "ordinal-position", &args_with_position(&marker, 3), None, Some(&marker), true).unwrap(),
            "ordinal_4": format_value(&bundle, "ordinal-position", &args_with_position(&marker, 4), None, Some(&marker), true).unwrap(),
            "ordinal_11": format_value(&bundle, "ordinal-position", &args_with_position(&marker, 11), None, Some(&marker), true).unwrap(),
            "ordinal_21": format_value(&bundle, "ordinal-position", &args_with_position(&marker, 21), None, Some(&marker), true).unwrap(),
            "balance": format_value(&bundle, "balance", &normal, None, Some(&marker), true).unwrap(),
            "due_date": format_value(&bundle, "due-date", &normal, None, Some(&marker), true).unwrap(),
            "layered_reference": format_value(&bundle, "citry-lib-wrapper", &normal, None, Some(&marker), true).unwrap(),
            "multiline_fallback_isolated": isolate_known_direction_paragraphs(
                &format_value(&bundle, "multiline-fallback", &normal, None, Some(&marker), true).unwrap(),
                "ltr",
            ),
            "rich": rich,
        });
        cases.insert(locale.to_owned(), result);
    }

    let marker = &markers[0];
    let invalid = bundle_for(
        "en-US",
        fs::read_to_string(fixtures.join("invalid.ftl")).expect("invalid fixture read failed"),
    );
    let mut rejections = Map::new();
    for (message_id, value) in [
        ("unknown-variable", None),
        ("unknown-function", Some("1")),
        ("slot-function-scalar", Some("ordinary scalar")),
        ("invalid-plural-input", Some("not a number")),
    ] {
        let mut invalid_args = FluentArgs::new();
        if let Some(value) = value {
            invalid_args.set("value", value);
        }
        let error = format_value(
            &invalid,
            message_id,
            &invalid_args,
            None,
            Some(marker),
            true,
        )
        .expect_err("strict wrapper unexpectedly accepted an invalid message");
        rejections.insert(message_id.to_owned(), Value::String(error));
    }
    for (rejection_name, value) in [
        ("invalid-plural-nan", f64::NAN),
        ("invalid-plural-infinity", f64::INFINITY),
    ] {
        let mut invalid_args = FluentArgs::new();
        invalid_args.set("value", value);
        let error = format_value(
            &invalid,
            "invalid-plural-input",
            &invalid_args,
            None,
            Some(marker),
            true,
        )
        .expect_err("strict wrapper unexpectedly accepted a non-finite plural input");
        rejections.insert(rejection_name.to_owned(), Value::String(error));
    }
    for (name, value) in [
        ("slot_marker_omitted", "marker omitted".to_owned()),
        ("slot_marker_wrapped", format!("{FSI}{marker}{PDI}")),
    ] {
        rejections.insert(
            name.to_owned(),
            Value::String(split_slot(&value, marker).unwrap_err()),
        );
    }
    let en_source = sources["en-US"].as_str().expect("source is text");
    rejections.insert(
        "slot_catalog_collision".to_owned(),
        Value::String(
            ensure_no_collision(&format!("{en_source}{marker}"), &[], marker).unwrap_err(),
        ),
    );
    rejections.insert(
        "slot_scalar_collision".to_owned(),
        Value::String(ensure_no_collision(en_source, &[marker], marker).unwrap_err()),
    );
    let dangerous_bidi = format!("prefix{PDI}\u{202e}override\u{202c}");
    let en_bundle = bundle_for("en-US", en_source.to_owned());
    let mut bad_plain = FluentArgs::new();
    bad_plain.set("account_name", dangerous_bidi.as_str());
    rejections.insert(
        "bidi-control-plain".to_owned(),
        Value::String(
            format_value(
                &en_bundle,
                "account-summary",
                &bad_plain,
                None,
                Some(marker),
                true,
            )
            .unwrap_err(),
        ),
    );
    let mut bad_rich = args(marker, 2.0);
    bad_rich.set("account_name", dangerous_bidi.as_str());
    rejections.insert(
        "bidi-control-rich".to_owned(),
        Value::String(
            format_value(
                &en_bundle,
                "acceptance",
                &bad_rich,
                None,
                Some(marker),
                true,
            )
            .unwrap_err(),
        ),
    );
    for (sink, message_id) in [("plain", "account-summary"), ("rich", "acceptance")] {
        let mut count = 0;
        for hex_value in &paragraph_boundary_hex {
            let boundary = char::from_u32(
                u32::from_str_radix(hex_value, 16).expect("invalid paragraph boundary"),
            )
            .expect("paragraph boundary is not a scalar");
            let bad_value = format!("before{boundary}אבג");
            let mut bad_args = if sink == "plain" {
                FluentArgs::new()
            } else {
                args(marker, 2.0)
            };
            bad_args.set("account_name", bad_value.as_str());
            if format_value(&en_bundle, message_id, &bad_args, None, Some(marker), true).is_err() {
                count += 1;
            }
        }
        if count != paragraph_boundary_hex.len() {
            panic!(
                "{sink} rejected {count} bidi paragraph boundaries, expected {}",
                paragraph_boundary_hex.len()
            );
        }
        rejections.insert(
            format!("paragraph-boundary-{sink}"),
            Value::String(format!(
                "rejected all {count} Unicode bidi paragraph boundaries"
            )),
        );
    }

    let mut catalog_rejections = 0;
    for source in hostile_catalog_sources(&bidi_control_hex, &fluent_escape_forms) {
        let result = try_bundle_for("en-US", source).and_then(|bundle| {
            let decoded = format_value(&bundle, "hostile", &FluentArgs::new(), None, None, false)?;
            validate_decoded_catalog_text(&decoded)
        });
        if result.is_err() {
            catalog_rejections += 1;
        }
    }
    let expected_catalog_rejections = bidi_control_hex.len() * fluent_escape_forms.len();
    assert_eq!(
        catalog_rejections, expected_catalog_rejections,
        "not every literal/escaped catalog bidi control was rejected"
    );
    rejections.insert(
        "bidi-control-catalog".to_owned(),
        Value::String(format!(
            "rejected all {catalog_rejections} literal and escaped bidi-control cases"
        )),
    );

    let mut paragraph_isolation_cases: Vec<String> = paragraph_boundary_hex
        .iter()
        .map(|hex_value| {
            char::from_u32(u32::from_str_radix(hex_value, 16).expect("invalid paragraph boundary"))
                .expect("paragraph boundary is not a scalar")
                .to_string()
        })
        .collect();
    paragraph_isolation_cases.push("\r\n".to_owned());
    for boundary in &paragraph_isolation_cases {
        let actual = isolate_known_direction_paragraphs(&format!("left{boundary}אבג"), "ltr");
        let expected = format!("{LRI}left{PDI}{boundary}{LRI}אבג{PDI}");
        assert_eq!(actual, expected, "paragraph isolation failed");
    }

    let mut slot_selector_args = FluentArgs::new();
    slot_selector_args.set("terms_link", marker.as_str());
    let unsafe_runtime_behaviors = json!({
        "slot_as_selector": format_value(
            &invalid,
            "slot-as-selector",
            &slot_selector_args,
            None,
            Some(marker),
            false,
        ).unwrap(),
    });

    println!(
        "{}",
        json!({
            "candidate": "rust",
            "cases": cases,
            "marker_properties": {
                "distinct_per_locale": markers[0] != markers[1],
                "distinct_per_resolution": resolution_markers_distinct,
            },
            "bidi_properties": {
                "catalog_cases_rejected": catalog_rejections,
                "catalog_escape_forms": fluent_escape_forms,
                "paragraph_boundaries_rejected_per_scalar_sink": paragraph_boundary_hex.len(),
                "whole_message_paragraph_cases_isolated": paragraph_isolation_cases.len(),
            },
            "rejections": rejections,
            "unsafe_runtime_behaviors": unsafe_runtime_behaviors,
        })
    );
}
