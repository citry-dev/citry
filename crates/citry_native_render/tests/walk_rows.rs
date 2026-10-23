//! Fixture test: the loop walk of level C2 (`walk.rs`) against Python's own
//! sandboxed evaluator (`walk_cases` in `scripts/native_render_fixtures.py`).
//!
//! Each case is a loop over JSON data. Where the walk reads the rows, every
//! input value and key must equal what Python evaluated; where Python
//! raised, the walk must decline; and the decline reason must be the one
//! the case expects.

use citry_native_render::{
    Decline, PathSpec, RowKey, Shape, Step, StepKey, Tree, WalkPlan, WalkPlanError, WalkSpec,
};
use serde_json::Value as Json;

/// A JSON value seen as the walk sees a Python value: an object is an exact
/// dict, an array an exact list, and `{"$const": ...}` a `Const` marker.
#[derive(Clone, Debug)]
struct Node<'a>(&'a Json);

impl Tree for Node<'_> {
    type Error = ();

    fn shape(&self) -> Shape {
        match self.0 {
            Json::Object(map) if map.contains_key("$const") => Shape::Marker,
            Json::Object(_) => Shape::Dict,
            Json::Array(_) => Shape::Seq,
            Json::String(_) => Shape::Str,
            Json::Number(number) => number.as_i64().map_or(Shape::Other, Shape::Int),
            _ => Shape::Other,
        }
    }

    fn get(&self, step: &Step) -> Result<Option<Self>, ()> {
        // JSON object keys are strings, as a Python dict with str keys: an
        // int key finds nothing.
        Ok(match (&step.key, self.0) {
            (StepKey::Str(key), Json::Object(map)) => map.get(key).map(Node),
            _ => None,
        })
    }

    fn item(&self, index: usize) -> Option<Self> {
        self.0
            .as_array()
            .and_then(|items| items.get(index))
            .map(Node)
    }

    fn len_hint(&self) -> usize {
        self.0.as_array().map_or(0, Vec::len)
    }
}

fn path(value: &Json) -> PathSpec {
    PathSpec {
        name: value["name"].as_str().expect("name").to_owned(),
        steps: value["steps"]
            .as_array()
            .expect("steps")
            .iter()
            .map(|step| match (step.get("str"), step.get("int")) {
                (Some(text), _) => StepKey::Str(text.as_str().expect("str step").to_owned()),
                (_, Some(number)) => StepKey::Int(number.as_i64().expect("int step")),
                _ => panic!("unknown step {step}"),
            })
            .collect(),
    }
}

fn spec(value: &Json) -> WalkSpec {
    WalkSpec {
        target: value["target"].as_str().expect("target").to_owned(),
        iterable: path(&value["iterable"]),
        kwargs: value["kwargs"]
            .as_array()
            .expect("kwargs")
            .iter()
            .map(path)
            .collect(),
        key: path(&value["key"]),
    }
}

#[test]
fn walk_matches_python() {
    let fixture: Json =
        serde_json::from_str(include_str!("fixtures/walk_rows.json")).expect("fixture parses");
    let cases = fixture["cases"].as_array().expect("cases");
    // A fixture that lost its cases would pass every assertion below.
    assert!(cases.len() >= 20, "the fixture lost cases");
    let mut read_rows = 0;
    for case in cases {
        let name = case["name"].as_str().expect("name");
        let plan = WalkPlan::new(&spec(&case["spec"])).expect("plan");
        let result = plan
            .read_rows(&Node(&case["scope"]))
            .expect("no read error");
        let expected_decline = case["decline"].as_str();
        let python = &case["python"];
        match result {
            Ok(rows) => {
                assert_eq!(
                    expected_decline, None,
                    "{name}: Rust read rows it should decline"
                );
                let python_rows = python.as_array().expect("Python read the rows too");
                assert_eq!(rows.len, python_rows.len(), "{name}: row count");
                assert_eq!(rows.kwargs.len(), rows.len * plan.kwargs_len(), "{name}");
                for (index, python_row) in python_rows.iter().enumerate() {
                    let values = &rows.kwargs[index * plan.kwargs_len()..][..plan.kwargs_len()];
                    let python_values = python_row["kwargs"].as_array().expect("kwargs");
                    for (value, python_value) in values.iter().zip(python_values) {
                        assert_eq!(value.0, python_value, "{name}: row {index} input");
                    }
                    let key = match &rows.keys[index] {
                        RowKey::Str(text) => text.0.as_str().expect("str key").to_owned(),
                        RowKey::Int(number) => number.to_string(),
                    };
                    assert_eq!(
                        key,
                        python_row["key"].as_str().expect("key"),
                        "{name}: row {index} key"
                    );
                }
                read_rows += rows.len;
            }
            Err(decline) => {
                assert_eq!(
                    Some(decline.as_str()),
                    expected_decline,
                    "{name}: decline reason"
                );
            }
        }
        if python.is_string() {
            assert!(
                expected_decline.is_some(),
                "{name}: Python raised, so Rust must decline"
            );
        }
    }
    assert!(read_rows >= 20, "too few rows read: {read_rows}");
}

fn plain(name: &str, steps: &[&str]) -> PathSpec {
    PathSpec {
        name: name.to_owned(),
        steps: steps
            .iter()
            .map(|step| StepKey::Str((*step).to_owned()))
            .collect(),
    }
}

#[test]
fn plan_refuses_paths_the_lowering_never_passes() {
    let base = WalkSpec {
        target: "row".to_owned(),
        iterable: plain("rows", &[]),
        kwargs: vec![plain("row", &[])],
        key: plain("row", &["id"]),
    };
    assert!(WalkPlan::new(&base).is_ok());
    let mut iterable_target = base.clone();
    iterable_target.iterable = plain("row", &[]);
    assert_eq!(
        WalkPlan::new(&iterable_target).unwrap_err(),
        WalkPlanError::IterableReadsTarget
    );
    let mut private_name = base.clone();
    private_name.kwargs = vec![plain("_secret", &[])];
    assert_eq!(
        WalkPlan::new(&private_name).unwrap_err(),
        WalkPlanError::PrivateName("_secret".to_owned())
    );
    let mut private_key = base.clone();
    private_key.key = plain("row", &["_id"]);
    assert_eq!(
        WalkPlan::new(&private_key).unwrap_err(),
        WalkPlanError::PrivateName("_id".to_owned())
    );
    let mut negative = base.clone();
    negative.iterable.steps = vec![StepKey::Int(-1)];
    assert_eq!(
        WalkPlan::new(&negative).unwrap_err(),
        WalkPlanError::NegativeIndex(-1)
    );
}

#[test]
fn steps_number_scope_names_first() {
    let spec = WalkSpec {
        target: "row".to_owned(),
        iterable: plain("phase", &["outputs"]),
        kwargs: vec![
            plain("row", &[]),
            plain("page", &["title"]),
            plain("phase", &[]),
        ],
        key: plain("row", &["id"]),
    };
    let plan = WalkPlan::new(&spec).expect("plan");
    let keys: Vec<&StepKey> = plan.steps().iter().map(|step| &step.key).collect();
    let text = |value: &str| StepKey::Str(value.to_owned());
    assert_eq!(
        keys,
        [
            &text("phase"),
            &text("page"),
            &text("outputs"),
            &text("title"),
            &text("id")
        ]
    );
    for (index, step) in plan.steps().iter().enumerate() {
        assert_eq!(step.id, index);
    }
}

#[test]
fn marker_items_decline() {
    let scope: Json =
        serde_json::from_str(r#"{"rows": [{"id": "a"}, {"$const": {"id": "b"}}]}"#).expect("json");
    let plan = WalkPlan::new(&WalkSpec {
        target: "row".to_owned(),
        iterable: plain("rows", &[]),
        kwargs: vec![plain("row", &[])],
        key: plain("row", &["id"]),
    })
    .expect("plan");
    assert!(matches!(
        plan.read_rows(&Node(&scope)).expect("no read error"),
        Err(Decline::Marker)
    ));
}
