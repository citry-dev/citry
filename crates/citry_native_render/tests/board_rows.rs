//! Fixture tests: a template's plan, evaluated over rows whose expected JSON
//! was observed from Citry's Python evaluator. `scripts/native_render_fixtures.py`
//! writes the fixtures: the row template of the benchmark's project-board
//! page with board-shaped and edge rows, and a template covering the shapes the board does not use.

use citry_native_render::{
    Attrs, Const, ExprSpec, Kinds, OpSpec, Plan, PlanSpec, ReadNode, ReadNodeSpec, SpreadLayout,
    Value,
};
use serde_json::Value as Json;

fn array(value: &Json) -> &Vec<Json> {
    value.as_array().expect("fixture arrays")
}

fn text(value: &Json) -> String {
    value.as_str().expect("fixture strings").to_owned()
}

fn expr(value: &Json) -> ExprSpec {
    let parts = array(value);
    match parts[0].as_str().unwrap() {
        "c" => ExprSpec::Const(match &parts[1] {
            Json::Null => Const::None,
            Json::Bool(flag) => Const::Bool(*flag),
            Json::String(literal) => Const::Str(literal.clone()),
            other => panic!("unexpected literal {other}"),
        }),
        "p" => ExprSpec::Path {
            root: text(&parts[1]),
            keys: array(&parts[2]).iter().map(text).collect(),
        },
        "i" => ExprSpec::If {
            test: Box::new(expr(&parts[1])),
            body: Box::new(expr(&parts[2])),
            otherwise: Box::new(expr(&parts[3])),
        },
        other => panic!("unexpected expression {other}"),
    }
}

fn ops(value: &Json) -> Vec<OpSpec> {
    array(value)
        .iter()
        .map(|op| {
            let parts = array(op);
            let key = text(&parts[1]);
            match parts[0].as_str().unwrap() {
                "text" => OpSpec::Text {
                    key,
                    expr: expr(&parts[2]),
                },
                "open" => OpSpec::Open {
                    key,
                    attributes: array(&parts[2])
                        .iter()
                        .map(|pair| (text(&array(pair)[0]), expr(&array(pair)[1])))
                        .collect(),
                },
                "spread" => OpSpec::Spread {
                    key,
                    expr: expr(&parts[2]),
                },
                "if" => OpSpec::If {
                    key,
                    branches: array(&parts[2])
                        .iter()
                        .map(|branch| {
                            let pair = array(branch);
                            let condition = (!pair[0].is_null()).then(|| expr(&pair[0]));
                            (condition, ops(&pair[1]))
                        })
                        .collect(),
                },
                "for" => OpSpec::For {
                    key,
                    target: text(&parts[2]),
                    iterable: expr(&parts[3]),
                    body: ops(&parts[4]),
                    empty: ops(&parts[5]),
                },
                other => panic!("unexpected operation {other}"),
            }
        })
        .collect()
}

fn read_node(value: &Json) -> ReadNodeSpec {
    let parts = array(value);
    let names: Vec<String> = array(&parts[0]).iter().map(text).collect();
    ReadNodeSpec {
        kinds: Kinds::from_names(names.iter().map(String::as_str)).unwrap(),
        children: array(&parts[1])
            .iter()
            .map(|pair| (text(&array(pair)[0]), read_node(&array(pair)[1])))
            .collect(),
        items: (!parts[2].is_null()).then(|| Box::new(read_node(&parts[2]))),
    }
}

/// Copy a typed fixture value along the read set, as the PyO3 reader does
/// (the fixture rows all pass the checks, so only the copy is modelled).
fn copy(value: &Json, node: &ReadNode) -> Value {
    if node.kinds == Kinds::default() && node.children.is_empty() && node.items.is_none() {
        return Value::Unread;
    }
    let (tag, inner) = value.as_object().unwrap().iter().next().unwrap();
    match tag.as_str() {
        "none" => Value::None,
        "bool" => Value::Bool(inner.as_bool().unwrap()),
        "int" => {
            let digits = inner.as_str().unwrap();
            digits
                .parse::<i64>()
                .map(Value::Int)
                .unwrap_or_else(|_| Value::BigInt(digits.to_owned()))
        }
        "float" => {
            let repr = array(inner)[0].as_str().unwrap();
            Value::Float {
                value: repr.parse().unwrap(),
                text: repr.to_owned(),
            }
        }
        "str" => Value::Str(text(inner)),
        "dict" => {
            let entries = array(inner);
            let lookup = |key: &str| {
                entries
                    .iter()
                    .find(|pair| array(pair)[0].as_str() == Some(key))
                    .map(|pair| &array(pair)[1])
                    .expect("read key present")
            };
            let attrs = (node.kinds.safe_attrs || node.kinds.safe_attrs_or_none).then(|| {
                let scalar = ReadNode {
                    name: String::new(),
                    kinds: Kinds {
                        scalar: true,
                        ..Kinds::default()
                    },
                    children: Vec::new(),
                    items: None,
                };
                Attrs {
                    names: entries.iter().map(|pair| text(&array(pair)[0])).collect(),
                    values: entries
                        .iter()
                        .map(|pair| copy(&array(pair)[1], &scalar))
                        .collect(),
                }
            });
            Value::Dict {
                len: entries.len(),
                children: node
                    .children
                    .iter()
                    .map(|child| copy(lookup(&child.name), child))
                    .collect(),
                attrs,
            }
        }
        "list" => {
            let entries = array(inner);
            Value::List {
                len: entries.len(),
                items: match &node.items {
                    Some(items) => entries.iter().map(|entry| copy(entry, items)).collect(),
                    None => Vec::new(),
                },
            }
        }
        other => panic!("unexpected value tag {other}"),
    }
}

fn check_fixture(source: &str, minimum_rows: usize) {
    let fixture: Json = serde_json::from_str(source).expect("fixture parses");
    let plan_json = &fixture["plan"];
    let spec = PlanSpec {
        ops: ops(&plan_json["ops"]),
        roots: array(&plan_json["roots"])
            .iter()
            .map(|pair| (text(&array(pair)[0]), read_node(&array(pair)[1])))
            .collect(),
        loop_targets: array(&plan_json["loop_targets"]).iter().map(text).collect(),
        js_safe_integer: plan_json["js_safe_integer"]
            .as_i64()
            .expect("the fixture names the JavaScript int limit"),
    };
    let plan = Plan::new(&spec).expect("the board template has a plan");
    let rows = array(&fixture["rows"]);
    assert!(rows.len() >= minimum_rows, "the fixture lost rows");
    for row in rows {
        let name = row["name"].as_str().unwrap();
        let (_tag, entries) = row["variables"].as_object().unwrap().iter().next().unwrap();
        let values: Vec<Value> = plan
            .roots()
            .iter()
            .map(|root| {
                let value = array(entries)
                    .iter()
                    .find(|pair| array(pair)[0].as_str() == Some(root.name.as_str()))
                    .map(|pair| &array(pair)[1])
                    .expect("root present");
                copy(value, root)
            })
            .collect();
        let layouts: Vec<SpreadLayout> = array(&row["spreads"])
            .iter()
            .enumerate()
            .map(|(index, entries)| {
                let names = match plan.spread_value(&values, index) {
                    Some(Value::Dict {
                        attrs: Some(attrs), ..
                    }) => attrs.names.clone(),
                    _ => Vec::new(),
                };
                SpreadLayout::new(
                    &names,
                    array(entries).iter().map(|entry| {
                        let parts = array(entry);
                        (
                            text(&parts[0]),
                            parts[1].as_bool().unwrap(),
                            parts[2].as_str().map(str::to_owned),
                        )
                    }),
                )
                .expect("layout")
            })
            .collect();
        let layout_refs: Vec<&SpreadLayout> = layouts.iter().collect();
        let written = plan
            .write_row(&values, &layout_refs)
            .expect("row evaluates");
        assert_eq!(written, row["expected"].as_str().unwrap(), "{name}");
    }
}

#[test]
fn board_rows_match_the_python_evaluator() {
    check_fixture(include_str!("fixtures/board_rows.json"), 63);
}

#[test]
fn synthetic_shapes_match_the_python_evaluator() {
    check_fixture(include_str!("fixtures/shapes.json"), 86);
}
