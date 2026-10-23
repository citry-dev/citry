//! One call run's rows in serialize: their ids, the repeat checks over
//! them, and their manifest items.
//!
//! A call run is the rows one `c-for` places at one component call site.
//! When Rust read every row of a run, the PyO3 layer
//! (`crates/citry_core_py/src/native_render/runs.rs`) records the whole run
//! with one object instead of one Python record per row. This module holds
//! the parts that need no Python: the ids both levels use, and the repeat
//! checks and items the run object needs:
//!
//! - [`RunIds`] names each row as Python's `_DigestPrefix` does: a placement
//!   key from the call site and the row's `#c-key`, and a child occurrence id
//!   from the parent occurrence and that placement key;
//! - [`first_repeat`] finds the first row whose text repeats an earlier
//!   row's, so a run with a repeated key, render id or child id goes back to
//!   Python, which raises its own error at that row;
//! - [`write_occurrence_item`] writes one row's manifest item as
//!   `script_json(item, sort_keys=True)` writes the dict Python would build.

use std::collections::HashSet;

use crate::digest::DigestPrefix;
use crate::json::write_json_str;

/// The leading text of both ids of a run's rows, hashed once per run.
///
/// Python passes the JSON text it would hash before each row's own item
/// (`_DIGEST_JSON.encode(prefix)[:-1]`): `[[call site...], route` for the
/// placement key and `[parent occurrence id` for the child id.
#[derive(Clone)]
pub struct RunIds {
    placement: DigestPrefix,
    child: DigestPrefix,
}

impl RunIds {
    /// Start from the two leading texts.
    pub fn new(placement_prefix_json: &str, child_prefix_json: &str) -> Self {
        RunIds {
            placement: DigestPrefix::new(placement_prefix_json),
            child: DigestPrefix::new(child_prefix_json),
        }
    }

    /// Return `(placement_key, child_id)` for the row whose `#c-key` is
    /// `key`: `citryPlacement` and `citryOccurrence` followed by the first 24
    /// hex digits of the two digests, as Python builds them.
    pub fn member_ids(&self, key: &str) -> (String, String) {
        let placement_digest = self.placement.explicit_key(key);
        let placement_key = format!("citryPlacement{}", &placement_digest[..24]);
        let child_digest = self.child.string(&placement_key);
        let child_id = format!("citryOccurrence{}", &child_digest[..24]);
        (placement_key, child_id)
    }
}

/// Return the index of the first item equal to an earlier item, or None.
///
/// The caller passes the text of exact Python `str`s, for which Python's
/// equality is equality of the text.
pub fn first_repeat<'a>(items: impl IntoIterator<Item = &'a str>) -> Option<usize> {
    let mut seen = HashSet::new();
    for (index, item) in items.into_iter().enumerate() {
        if !seen.insert(item) {
            return Some(index);
        }
    }
    None
}

/// The fields of one row's manifest item.
///
/// Python builds the item as a dict in `prepared_manifest`
/// (`citry/_vue/protocol.py`) and adds `renderId` in `_prepare_holding_assets`
/// (`citry/_vue/events.py`). A run row never gets an `eventContext`, because
/// no Events instance is a `simple='vue'` row.
pub struct OccurrenceItem<'a> {
    /// The definition id the compiler gave the row's definition, which is
    /// the id the manifest carries.
    pub definition_id: &'a str,
    pub id: &'a str,
    pub parent_id: Option<&'a str>,
    pub placement_key: Option<&'a str>,
    /// The row's prepared data, already written as JSON.
    pub prepared_json: &'a str,
    pub render_id: &'a str,
    pub type_key: &'a str,
}

fn write_optional(out: &mut String, value: Option<&str>) {
    match value {
        Some(text) => write_json_str(out, text),
        None => out.push_str("null"),
    }
}

/// Write one row's manifest item, its keys in sorted order and its server
/// data as `{}`, byte for byte what `script_json(item, sort_keys=True)`
/// writes for the dict Python would build.
pub fn write_occurrence_item(out: &mut String, item: &OccurrenceItem<'_>) {
    // The keys are fixed text in sorted order, as `sort_keys=True` orders
    // them; the fixture test locks this order against Python's output.
    out.push_str("{\"definitionId\":");
    write_json_str(out, item.definition_id);
    out.push_str(",\"id\":");
    write_json_str(out, item.id);
    out.push_str(",\"parentId\":");
    write_optional(out, item.parent_id);
    out.push_str(",\"placementKey\":");
    write_optional(out, item.placement_key);
    out.push_str(",\"preparedData\":");
    out.push_str(item.prepared_json);
    out.push_str(",\"renderId\":");
    write_json_str(out, item.render_id);
    // A Rust-read row has no js_data, so its server data is always empty.
    out.push_str(",\"serverData\":{},\"typeKey\":");
    write_json_str(out, item.type_key);
    out.push('}');
}
