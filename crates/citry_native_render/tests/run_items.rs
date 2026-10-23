//! Fixture test: call-run row ids, repeat checks and manifest items from
//! `run.rs`, against what Python's `_DigestPrefix` and `_script_json` give
//! (`run_cases` in `scripts/native_render_fixtures.py`).

use citry_native_render::{OccurrenceItem, RunIds, first_repeat, write_occurrence_item};
use serde_json::Value as Json;

fn strings(value: &Json) -> Vec<&str> {
    value
        .as_array()
        .expect("fixture list")
        .iter()
        .map(|item| item.as_str().expect("fixture string"))
        .collect()
}

#[test]
fn run_rows_match_python() {
    let fixture: Json =
        serde_json::from_str(include_str!("fixtures/run_items.json")).expect("fixture parses");
    let cases = fixture["cases"].as_array().expect("cases");
    // A fixture that lost its cases would pass every assertion below.
    assert!(cases.len() >= 3, "the fixture lost cases");
    let mut rows = 0;
    for case in cases {
        let text = |name: &str| case[name].as_str().expect("fixture strings");
        let ids = RunIds::new(text("placement_prefix"), text("child_prefix"));
        let keys = strings(&case["keys"]);
        let render_ids = strings(&case["render_ids"]);
        let prepared = strings(&case["prepared_json"]);
        let expected_items = strings(&case["expected_items"]);
        let expected_ids = case["expected_ids"].as_array().expect("ids");
        assert_eq!(
            first_repeat(keys.iter().copied()),
            case["first_repeat"].as_u64().map(|index| index as usize),
            "first repeated key"
        );
        for (index, key) in keys.iter().enumerate() {
            let (placement_key, child_id) = ids.member_ids(key);
            let pair = strings(&expected_ids[index]);
            assert_eq!(placement_key, pair[0], "placement key for {key:?}");
            assert_eq!(child_id, pair[1], "child id for {key:?}");
            let mut out = String::new();
            write_occurrence_item(
                &mut out,
                &OccurrenceItem {
                    definition_id: text("definition_id"),
                    id: &child_id,
                    parent_id: Some(text("parent_id")),
                    placement_key: Some(&placement_key),
                    prepared_json: prepared[index],
                    render_id: render_ids[index],
                    type_key: text("type_key"),
                },
            );
            assert_eq!(out, expected_items[index], "item for {key:?}");
            rows += 1;
        }
    }
    assert!(rows >= 19, "the fixture lost rows");
}

#[test]
fn null_parent_and_placement_are_written_as_null() {
    // Run rows always have both; the writer still matches json.dumps for None.
    let mut out = String::new();
    write_occurrence_item(
        &mut out,
        &OccurrenceItem {
            definition_id: "d",
            id: "i",
            parent_id: None,
            placement_key: None,
            prepared_json: "{\"calls\":{}}",
            render_id: "r",
            type_key: "t",
        },
    );
    assert_eq!(
        out,
        "{\"definitionId\":\"d\",\"id\":\"i\",\"parentId\":null,\"placementKey\":null,\
         \"preparedData\":{\"calls\":{}},\"renderId\":\"r\",\"serverData\":{},\"typeKey\":\"t\"}"
    );
}

#[test]
fn first_repeat_finds_the_first_repeat() {
    assert_eq!(first_repeat(["a", "b", "c"]), None);
    assert_eq!(first_repeat(["a", "b", "a", "b"]), Some(2));
    assert_eq!(first_repeat(Vec::<&str>::new()), None);
}
