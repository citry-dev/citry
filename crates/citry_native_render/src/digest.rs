//! The ids Citry derives for the rows of one call run (the components one
//! `c-for` places), hashed in Rust.
//!
//! Python names each row of a repeated component call (a `c-for` over a
//! component) with two SHA-256 digests over compact JSON lists
//! (`_digest` in `packages/py/citry/citry/_vue/direct_capture.py`):
//!
//! - the placement key hashes `[call site, route, ["explicit", key]]`;
//! - the child occurrence id hashes `[parent occurrence id, placement key]`.
//!
//! Only the last item changes between the rows of a run, so the text before
//! it (which holds the whole authored template source) is hashed once and
//! the hash state is copied for each row, as Python's `_DigestPrefix` does.
//! Python writes that leading text; Rust adds each row's last item.

use sha2::{Digest, Sha256};

use crate::json::write_plain_json_str;

/// A SHA-256 state that has already consumed the JSON text of a list's
/// leading items, without the closing `]`.
#[derive(Clone)]
pub struct DigestPrefix {
    state: Sha256,
}

const HEX: &[u8; 16] = b"0123456789abcdef";

fn hex(state: Sha256) -> String {
    let digest = state.finalize();
    let mut out = String::with_capacity(64);
    for byte in digest {
        out.push(char::from(HEX[usize::from(byte >> 4)]));
        out.push(char::from(HEX[usize::from(byte & 0x0f)]));
    }
    out
}

impl DigestPrefix {
    /// Start from the JSON text of the leading items, `[item1,...,itemN`.
    pub fn new(prefix_json: &str) -> Self {
        let mut state = Sha256::new();
        state.update(prefix_json.as_bytes());
        DigestPrefix { state }
    }

    /// The hex digest of the list with `["explicit", key]` as its last item:
    /// a row's placement digest.
    pub fn explicit_key(&self, key: &str) -> String {
        let mut suffix = String::with_capacity(key.len() + 16);
        suffix.push_str(",[\"explicit\",");
        write_plain_json_str(&mut suffix, key);
        suffix.push_str("]]");
        let mut state = self.state.clone();
        state.update(suffix.as_bytes());
        hex(state)
    }

    /// The hex digest of the list with the string `value` as its last item:
    /// a row's child occurrence digest.
    pub fn string(&self, value: &str) -> String {
        let mut suffix = String::with_capacity(value.len() + 4);
        suffix.push(',');
        write_plain_json_str(&mut suffix, value);
        suffix.push(']');
        let mut state = self.state.clone();
        state.update(suffix.as_bytes());
        hex(state)
    }
}
