//! Give the walks over a parsed HTML tree enough stack, whatever thread runs
//! them.
//!
//! Comparing the browser's parse of written HTML with what was expected
//! (`hydration_structure`) and checking a raw HTML block (`static_html`)
//! call themselves once per level of the parsed tree. Python may run them
//! on any thread, and a thread other than the main one can have as little
//! as 512 KiB of stack (macOS) or 128 KiB (musl Linux). So each level runs
//! through `with_enough_stack`: when less than `RED_ZONE` is left, `stacker`
//! continues on a new segment of `NEW_SEGMENT` bytes from the heap. The
//! sizes follow the template parser's own guard
//! (`citry_template_parser/src/stack.rs`).

/// Run the work on a new segment when less stack than this is left.
const RED_ZONE: usize = 100 * 1024;

/// The size of each new stack segment.
const NEW_SEGMENT: usize = 1024 * 1024;

/// Run `work` with at least `RED_ZONE` bytes of stack available.
///
/// The work must not call into Python: CPython 3.14 and later check the stack
/// pointer against the thread's own stack, and a heap segment is outside it.
pub(crate) fn with_enough_stack<T>(work: impl FnOnce() -> T) -> T {
    stacker::maybe_grow(RED_ZONE, NEW_SEGMENT, work)
}
