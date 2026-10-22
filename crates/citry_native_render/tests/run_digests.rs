//! Fixture test: call-run row ids from [`DigestPrefix`], against ids observed
//! from Python's `_DigestPrefix` (`digest_cases` in `scripts/native_render_fixtures.py`).

use citry_native_render::DigestPrefix;
use serde_json::Value as Json;

#[test]
fn run_ids_match_python() {
    let fixture: Json =
        serde_json::from_str(include_str!("fixtures/run_digests.json")).expect("fixture parses");
    let cases = fixture["cases"].as_array().expect("cases");
    assert!(cases.len() >= 16, "the fixture lost cases");
    for case in cases {
        let text = |name: &str| case[name].as_str().expect("fixture strings");
        let placement = DigestPrefix::new(text("placement_prefix"));
        let child = DigestPrefix::new(text("child_prefix"));
        let placement_key = format!(
            "citryPlacement{}",
            &placement.explicit_key(text("key"))[..24]
        );
        assert_eq!(
            placement_key,
            text("placement_key"),
            "key {:?}",
            text("key")
        );
        let child_id = format!("citryOccurrence{}", &child.string(&placement_key)[..24]);
        assert_eq!(child_id, text("child_id"), "key {:?}", text("key"));
    }
}
