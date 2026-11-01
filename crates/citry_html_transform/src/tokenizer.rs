//! The one place this crate starts an html5gum tokenizer run.
//!
//! html5gum is the patched copy in `third_party/rust/html5gum`. Upstream
//! 0.8.4 reads a tag's attributes with state functions that call each other
//! and does not return to its main loop between two attributes written
//! `name="value"`, so each such attribute added a few nested calls. One tag
//! with about 50,000 of them overflowed the 8 MiB main-thread stack in a
//! release build and aborted the process (about 3,000 on a 512 KiB thread,
//! and far fewer in a debug build). The patched copy returns to the main
//! loop after every attribute, so the stack a run needs no longer grows
//! with the input. `tests/attribute_runs.rs` checks that on a small
//! stack; the copy's `README.citry.md` names the changed line.

use std::convert::Infallible;

use html5gum::{Emitter, Tokenizer};

/// The stack a tokenizer run keeps available. html5gum still calls a few
/// state functions in a row within one token, and the emitter runs
/// html5ever's tree builder and this crate's callbacks on top of them. None
/// of that grows with the input; the figure leaves a wide margin for it in
/// both debug and release builds.
const TOKENIZER_STACK: usize = 1024 * 1024 + 256 * 1024;

/// Run html5gum over `input`, sending its events to `emitter`.
///
/// Every tokenizer run in the crate goes through this function, so a run
/// always starts with [`TOKENIZER_STACK`] available: it moves to a new stack
/// segment when the thread has less left.
pub(crate) fn run_tokenizer<E: Emitter<Token = Infallible>>(input: &str, emitter: E) {
    crate::stack::with_stack_reserve(TOKENIZER_STACK, || {
        Tokenizer::new_with_emitter(input, emitter)
            .finish()
            .expect("string input is infallible");
    });
}
