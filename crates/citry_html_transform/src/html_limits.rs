//! The one limit every html5gum tokenizer run in this crate goes through.
//!
//! html5gum (0.8.4) reads a tag's attributes with state functions that call
//! each other, and it never returns to its main loop between two attributes
//! of the form `name="value"`: each such attribute adds about five nested
//! calls (about 170 bytes of stack in a release build, about 6 KiB in a debug
//! build). A single tag with about 20,000 attributes in a row therefore
//! overflows the 8 MiB main-thread stack and aborts the whole process, and
//! about 3,000 do the same on a 512 KiB thread. The calls are inside
//! html5gum, so a stack guard around our own code cannot stop them, and a
//! larger stack only moves the threshold.
//!
//! So every run is refused up front when the input has more than
//! [`MAX_ATTRIBUTE_RUN`] attributes in a row that html5gum would read in
//! that nested way. Only a double-quoted value, followed by white space and
//! another attribute name that is followed by `=` and a double quote, keeps
//! the nesting going. A bare name, a single-quoted or unquoted value, a
//! value followed directly by the next name, a `/`, or a `>` returns to the
//! main loop, and the count starts again. The limit is far above any real
//! element and far below the point where the stack runs out.
//!
//! The reading below follows the same steps as html5gum but only counts: it
//! never builds a tag, so it stays linear in the input and does not need the
//! stack the tokenizer needs.

use std::convert::Infallible;
use std::error::Error;
use std::fmt;

use html5gum::{Emitter, Tokenizer};

/// The most attributes in a row (written `name="value"`, each followed by
/// white space and the next one) that a tokenizer run accepts.
///
/// The nested calls for this many attributes need about 170 KiB of stack in a
/// release build, so they fit even a 512 KiB thread; [`TOKENIZER_STACK`]
/// keeps the run on enough stack when the thread has less. Real elements have
/// a few dozen attributes at most, so no ordinary page reaches the limit.
pub const MAX_ATTRIBUTE_RUN: usize = 1_024;

/// Why a tokenizer run was refused: some tag holds more than
/// [`MAX_ATTRIBUTE_RUN`] attributes in a row.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TooManyAttributes;

impl fmt::Display for TooManyAttributes {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "HTML has a tag with more than {MAX_ATTRIBUTE_RUN} attributes in a row written as \
             name=\"value\", which is more than Citry reads"
        )
    }
}

impl Error for TooManyAttributes {}

/// The stack an html5gum run at the limit may need, per attribute. A debug
/// build keeps every frame at full size and measured about 6 KiB. A release
/// build measured about 170 bytes with Citry's emitter and about 350 with
/// html5gum's own; the figure leaves room for a compiler or a platform that
/// inlines less.
const STACK_PER_ATTRIBUTE: usize = if cfg!(debug_assertions) {
    12 * 1024
} else {
    1024
};

/// The stack a tokenizer run keeps available: the nested calls for a run at
/// the limit, plus room for the tree builder and the callbacks around them.
const TOKENIZER_STACK: usize = MAX_ATTRIBUTE_RUN * STACK_PER_ATTRIBUTE + 256 * 1024;

/// Run html5gum over `input`, sending its events to `emitter`, or refuse
/// when `input` holds more attributes in a row than [`MAX_ATTRIBUTE_RUN`].
///
/// Every tokenizer run in the crate goes through this function, so the limit
/// has one definition and one place that applies it. The run itself moves to
/// a new stack when the thread has less than [`TOKENIZER_STACK`] left, so an
/// input at the limit also fits on a thread with a small stack.
pub(crate) fn run_tokenizer<E: Emitter<Token = Infallible>>(
    input: &str,
    emitter: E,
) -> Result<(), TooManyAttributes> {
    if has_too_many_attributes_in_a_row(input.as_bytes()) {
        return Err(TooManyAttributes);
    }
    crate::stack::with_stack_reserve(TOKENIZER_STACK, || {
        Tokenizer::new_with_emitter(input, emitter)
            .finish()
            .expect("string input is infallible");
    });
    Ok(())
}

/// Whether some run of attributes in `bytes` is longer than
/// [`MAX_ATTRIBUTE_RUN`].
///
/// The count may be higher than what the tokenizer nests, never lower: a
/// double quote inside a comment or a script is counted like one in a tag,
/// and a name that starts with `=` is taken as part of the run. That keeps
/// the check on the safe side without modelling every tokenizer state.
fn has_too_many_attributes_in_a_row(bytes: &[u8]) -> bool {
    // A run of n attributes needs 2n double quotes, so an input with fewer
    // cannot hold one that is too long, and most pages stop here.
    let quotes = bytes.iter().filter(|&&byte| byte == b'"').count();
    if quotes < 2 * (MAX_ATTRIBUTE_RUN + 1) {
        return false;
    }
    longest_attribute_run(bytes, MAX_ATTRIBUTE_RUN + 1) > MAX_ATTRIBUTE_RUN
}

/// The length of the longest run of attributes in `bytes`, or `cap` as soon
/// as a run reaches it.
fn longest_attribute_run(bytes: &[u8], cap: usize) -> usize {
    let mut longest = 0;
    let mut from = 0;
    while let Some(mut quote) = next_opening_quote(bytes, from) {
        let mut run = 0;
        loop {
            run += 1;
            if run >= cap {
                return cap;
            }
            // The value ends at the next double quote. Without one, no
            // later quote opens anything, so the whole input is read.
            let Some(length) = bytes[quote + 1..].iter().position(|&byte| byte == b'"') else {
                return longest.max(run);
            };
            let close = quote + 1 + length;
            // A run that ends is searched for again right after its last
            // value, so the next one is found even when this one stopped
            // early.
            from = close + 1;
            match chained_opening_quote(bytes, close + 1) {
                Some(next) => quote = next,
                None => break,
            }
        }
        longest = longest.max(run);
    }
    longest
}

/// The position of the next double quote that starts an attribute value
/// (`=`, optional white space, `"`) at or after `from`.
fn next_opening_quote(bytes: &[u8], from: usize) -> Option<usize> {
    let mut at = from;
    while let Some(offset) = bytes[at..].iter().position(|&byte| byte == b'=') {
        let mut quote = at + offset + 1;
        while bytes.get(quote).is_some_and(|&byte| is_space(byte)) {
            quote += 1;
        }
        if bytes.get(quote) == Some(&b'"') {
            return Some(quote);
        }
        at += offset + 1;
    }
    None
}

/// When the attribute whose value ended just before `after_close` is
/// followed by another one that html5gum reads inside the same nested call,
/// the position of that attribute's opening quote.
fn chained_opening_quote(bytes: &[u8], after_close: usize) -> Option<usize> {
    // After a closing quote the tokenizer continues in place only on white
    // space, `/` or `>`; anything else is an error that returns to its loop.
    let first = *bytes.get(after_close)?;
    if !(is_space(first) || first == b'/' || first == b'>') {
        return None;
    }
    let mut at = after_close;
    while bytes.get(at).is_some_and(|&byte| is_space(byte)) {
        at += 1;
    }
    // `/` and `>` end the attribute list, or leave it for the self-closing
    // check; neither continues the nesting.
    let name_start = *bytes.get(at)?;
    if name_start == b'/' || name_start == b'>' {
        return None;
    }
    // The first character always belongs to the name (a leading `=` is
    // counted as a name character, which can only make the count larger).
    at += 1;
    while bytes
        .get(at)
        .is_some_and(|&byte| !is_space(byte) && !matches!(byte, b'/' | b'>' | b'='))
    {
        at += 1;
    }
    // A name that ends without `=` returns to the loop.
    if bytes.get(at) != Some(&b'=') {
        return None;
    }
    at += 1;
    while bytes.get(at).is_some_and(|&byte| is_space(byte)) {
        at += 1;
    }
    (bytes.get(at) == Some(&b'"')).then_some(at)
}

/// The characters html5gum skips between attributes, plus a carriage
/// return, which it turns into a line feed before it reads the input.
fn is_space(byte: u8) -> bool {
    matches!(byte, b' ' | b'\t' | b'\n' | b'\x0c' | b'\r')
}

#[cfg(test)]
mod tests {
    use super::{has_too_many_attributes_in_a_row, MAX_ATTRIBUTE_RUN};

    fn tag(count: usize, attribute: impl Fn(usize) -> String) -> Vec<u8> {
        let attributes: String = (0..count).map(attribute).collect();
        format!("<p{attributes}>x</p>").into_bytes()
    }

    #[test]
    fn a_run_at_the_limit_passes_and_one_more_is_refused() {
        let at_limit = tag(MAX_ATTRIBUTE_RUN, |i| format!(" a{i}=\"v\""));
        let over = tag(MAX_ATTRIBUTE_RUN + 1, |i| format!(" a{i}=\"v\""));
        assert!(!has_too_many_attributes_in_a_row(&at_limit));
        assert!(has_too_many_attributes_in_a_row(&over));
    }

    #[test]
    fn white_space_and_empty_values_keep_the_run_going() {
        for shape in [
            |i: usize| format!(" a{i}=\"\""),
            |i: usize| format!("\n\ta{i}=  \"v\"\r\n"),
            |i: usize| format!(" a{i}=\"v>/\""),
            |i: usize| format!(" a{i}=\"<!--\""),
        ] {
            let page = tag(MAX_ATTRIBUTE_RUN + 1, shape);
            assert!(has_too_many_attributes_in_a_row(&page));
        }
    }

    #[test]
    fn anything_that_returns_the_tokenizer_to_its_loop_resets_the_count() {
        // Each shape keeps the tokenizer from nesting, so no run is long even
        // though the page holds twice the limit in attributes.
        let count = MAX_ATTRIBUTE_RUN * 2;
        for shape in [
            // Single quoted, unquoted and bare attributes.
            |i: usize| format!(" a{i}='v'"),
            |i: usize| format!(" a{i}=v"),
            |i: usize| format!(" a{i}"),
            // The next name starts right after the closing quote.
            |i: usize| format!("a{i}=\"v\""),
            // A solidus after the value.
            |i: usize| format!("/a{i}=\"v\""),
            // White space before the `=`.
            |i: usize| format!(" a{i} =\"v\""),
        ] {
            let page = tag(count, shape);
            assert!(!has_too_many_attributes_in_a_row(&page));
        }
    }

    #[test]
    fn a_page_of_many_short_tags_is_not_a_run() {
        let page = "<p a=\"1\" b=\"2\" c=\"3\">x</p>".repeat(5_000);
        assert!(!has_too_many_attributes_in_a_row(page.as_bytes()));
    }

    #[test]
    fn a_greater_than_sign_inside_a_value_does_not_end_the_run() {
        // The `>` is inside a double-quoted value, so the tag goes on.
        let page = tag(MAX_ATTRIBUTE_RUN + 1, |i| format!(" a{i}=\">\""));
        assert!(has_too_many_attributes_in_a_row(&page));
    }

    #[test]
    fn a_run_is_found_after_text_that_holds_quotes() {
        // The quote in the comment pairs with the first quote of the tag, so
        // the count starts one attribute late; the run is still found.
        let mut page = b"<!-- x=\" -->".to_vec();
        page.extend(tag(MAX_ATTRIBUTE_RUN + 2, |i| format!(" a{i}=\"v\"")));
        assert!(has_too_many_attributes_in_a_row(&page));
    }

    #[test]
    fn an_unclosed_value_ends_the_scan() {
        let mut page = tag(2 * MAX_ATTRIBUTE_RUN, |i| format!(" a{i}='v'"));
        page.extend_from_slice(b" b=\"never closed");
        assert!(!has_too_many_attributes_in_a_row(&page));
    }
}
