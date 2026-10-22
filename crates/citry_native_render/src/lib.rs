//! The pure-Rust half of Citry's native render path; the design is in
//! `docs/design/native_render.md`.
//!
//! Citry renders a `simple='vue'` row without a Python component: a generated
//! Python function checks that every value the template reads is plain data
//! (the "read set" check), then evaluates the template's expressions into a
//! dict of prepared data that the browser's Vue instance reads. This crate
//! does the same work in Rust for one row:
//!
//! 1. [`Plan::new`] turns a description of the template's operations and of
//!    the paths it reads ([`PlanSpec`]) into a plan. Python builds that
//!    description from the same structures its own generated evaluator is
//!    built from, so no template rule is written here a second time.
//! 2. The caller (the PyO3 layer in `crates/citry_core_py/src/native_render/`)
//!    copies every value the template reads into a [`Value`] tree, checking
//!    each value's type as it goes. A failed check means the caller declines
//!    the row and Python evaluates it.
//! 3. [`Plan::write_row`] evaluates the operations over that tree and writes
//!    the prepared data as JSON, byte for byte what Python's
//!    `script_json({"calls": {}, **data}, sort_keys=True)` writes.
//!
//! [`DigestPrefix`] hashes the ids Citry gives each row of a repeated
//! component call (a `c-for` over a component); see `digest.rs`.
//!
//! The crate has no Python dependency, so the evaluation, the JSON writer and
//! the digests are tested with fixtures observed from Python
//! (`scripts/native_render_fixtures.py` writes them).

mod digest;
mod eval;
mod json;
mod plan;
mod value;

pub use digest::DigestPrefix;
pub use eval::EvalError;
pub use json::{write_json_str, write_plain_json_str};
pub use plan::{
    Const, ExprSpec, Kinds, OpSpec, Plan, PlanError, PlanSpec, ReadNode, ReadNodeSpec,
    SpreadLayout, SpreadLayoutError,
};
pub use value::{Attrs, Value};
