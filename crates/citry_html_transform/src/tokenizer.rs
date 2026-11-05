//! The one place this crate starts an html5gum tokenizer run.
//!
//! html5gum reads a tag's attributes with state functions that call each
//! other. Since 0.9.1 (untitaker/html5gum pull request 158) it returns to
//! its main loop between two attributes, so the stack a run needs does not
//! grow with the input.
//! A stack overflow aborts the whole process, and a guard in this crate
//! cannot stop it, because the calls are inside html5gum. So
//! `tests/attribute_runs.rs` reads a tag with 100,000 attributes on a
//! small stack and fails with a crash if a newer html5gum nests again.

use std::convert::Infallible;

use html5gum::{Emitter, Tokenizer};

use crate::html_limits::{HtmlLimits, HtmlTooLarge};

/// The stack a tokenizer run keeps available. html5gum calls a few state
/// functions in a row within one token, and the emitter runs html5ever's
/// tree builder and this crate's callbacks on top of them. None of that
/// grows with the input; the figure leaves a wide margin for it in both
/// debug and release builds.
const TOKENIZER_STACK: usize = 1024 * 1024 + 256 * 1024;

/// Run html5gum over `input`, sending its events to `emitter`, and return
/// whether the run stayed within the limits the emitter counted in `limits`.
///
/// Every tokenizer run in the crate goes through this function, so a run
/// always starts with [`TOKENIZER_STACK`] available: it moves to a new stack
/// segment when the thread has less left. Taking `limits` here, and returning
/// its result, means no run can forget to check them (see `html_limits`).
pub(crate) fn run_tokenizer<E: Emitter<Token = Infallible>>(
    input: &str,
    emitter: E,
    limits: &HtmlLimits,
) -> Result<(), HtmlTooLarge> {
    crate::stack::with_stack_reserve(TOKENIZER_STACK, || {
        Tokenizer::new_with_emitter(input, emitter)
            .finish()
            .expect("string input is infallible");
    });
    limits.result()
}
