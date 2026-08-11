use std::collections::BTreeMap;
use std::fs;
use std::sync::Arc;

use fluent_bundle::concurrent::FluentBundle;
use fluent_bundle::{FluentArgs, FluentResource, FluentValue};
use serde_json::{Map, Value, json};
use unic_langid::LanguageIdentifier;

type Bundle = FluentBundle<Arc<FluentResource>>;
const FSI: &str = "\u{2068}";
const PDI: &str = "\u{2069}";

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
        .add_function("CITRY_TEXT", |positional, named| {
            if named.iter().next().is_some() {
                return FluentValue::Error;
            }
            positional
                .first()
                .and_then(value_text)
                .map(|value| format!("{FSI}{value}{PDI}").into())
                .unwrap_or(FluentValue::Error)
        })
        .expect("CITRY_TEXT registration failed");
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
        .add_function("NUMBER", |positional, named| {
            let Some(value) = positional.first().and_then(value_text) else {
                return FluentValue::Error;
            };
            let Some(profile) = named_text(named, "profile") else {
                return FluentValue::Error;
            };
            format!("{FSI}NUM[value={value},profile={profile}]{PDI}").into()
        })
        .expect("NUMBER registration failed");

    let locale = locale.to_owned();
    bundle
        .add_function("CITRY_PLURAL", move |positional, named| {
            let Some(value) = positional.first().and_then(value_text) else {
                return FluentValue::Error;
            };
            let Ok(value) = value.parse::<f64>() else {
                return FluentValue::Error;
            };
            let mode = named_text(named, "mode").unwrap_or_else(|| "cardinal".to_owned());
            if mode == "ordinal" {
                if locale == "en-US" && value.fract() == 0.0 {
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
            if locale == "cs-CZ" {
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

fn json_args(value: &Value) -> FluentArgs<'static> {
    let mut args = FluentArgs::new();
    for (name, value) in value.as_object().expect("case args must be an object") {
        match value {
            Value::String(value) => args.set(name.clone(), value.clone()),
            Value::Number(value) => args.set(
                name.clone(),
                value.as_f64().expect("numeric argument must fit binary64"),
            ),
            _ => panic!("unsupported argument value for {name}"),
        }
    }
    args
}

fn main() {
    let payload_path = std::env::args().nth(1).expect("payload path is required");
    let payload: Value =
        serde_json::from_str(&fs::read_to_string(payload_path).expect("payload read failed"))
            .expect("payload JSON failed");

    let mut bundles = BTreeMap::new();
    for (locale, source) in payload["artifacts"]
        .as_object()
        .expect("artifacts must be an object")
    {
        let language: LanguageIdentifier = locale.parse().expect("locale failed");
        let mut bundle = FluentBundle::new_concurrent(vec![language]);
        bundle.set_use_isolating(false);
        register_functions(&mut bundle, locale);
        let resource = Arc::new(
            FluentResource::try_new(source.as_str().expect("artifact must be text").to_owned())
                .expect("artifact parse failed"),
        );
        bundle.add_resource(resource).expect("artifact add failed");
        bundles.insert(locale.clone(), bundle);
    }

    let mut results = Map::new();
    for case in payload["cases"].as_array().expect("cases must be an array") {
        let locale = case["bundle_locale"]
            .as_str()
            .expect("bundle locale missing");
        let message_id = case["internal_id"].as_str().expect("internal ID missing");
        let bundle = bundles.get(locale).expect("bundle missing");
        let message = bundle.get_message(message_id).expect("message missing");
        let pattern = message.value().expect("message value missing");
        let args = json_args(&case["args"]);
        let mut errors = vec![];
        let value = bundle.format_pattern(pattern, Some(&args), &mut errors);
        if !errors.is_empty() {
            panic!("format errors: {errors:?}");
        }
        results.insert(
            case["name"].as_str().expect("case name missing").to_owned(),
            json!({"bundle_locale": locale, "value": value}),
        );
    }

    println!("{}", json!({"candidate": "rust", "results": results}));
}
