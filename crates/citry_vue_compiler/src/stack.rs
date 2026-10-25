//! Give the Vue compiler and the server renderer enough stack, whatever
//! thread runs them.
//!
//! Compiling a template, reading the render function it produces, writing
//! its HTML, evaluating its expressions and freeing what was read all call
//! themselves once per nesting level. Python may run them on any thread. A
//! thread gets the platform's default stack unless Python sets one: 128 KiB
//! on musl Linux, also for Python's own threads, and 512 KiB on macOS for a
//! thread started outside Python; and `threading.stack_size()` can make any
//! Python thread as small. So without a guard a deep template overflows it
//! and aborts the process.
//!
//! Each recursion entry in the reader, the writers, `eval`, `fully_supported`
//! and the class and style normalizers runs its work through
//! `with_enough_stack`. When less than `RED_ZONE` is left, `stacker`
//! runs the work on a new segment of `NEW_SEGMENT` bytes taken from the
//! heap, and later levels keep using that segment until it too runs low.
//! On a thread with room to spare, nothing is allocated and the check is
//! cheap. The sizes follow the template parser's own guard
//! (`citry_template_parser/src/stack.rs`).
//!
//! Some recursion happens inside code Citry does not own: Vue's compiler
//! (Vize), the JavaScript parser that reads the render code, `serde_json`
//! reading and freeing deep data, and the drop of a read program's tree.
//! The other functions here give that whole piece of work enough stack up
//! front.
//!
//! On wasm32 (Pyodide), `stacker` cannot tell how much stack is left, so the
//! outermost guarded call takes a block from the heap and nested calls reuse
//! it. A render takes one `NEW_SEGMENT` block (and one `LARGE_STACK` block
//! more when its data is deeper than 128 levels), freeing a program takes
//! one `FREE_RED_ZONE` block, and a compile and a read take one `LARGE_STACK`
//! block each.

/// Run the work on a new segment when less stack than this is left: enough
/// for the largest frames between two guarded calls in a debug build, with
/// a wide margin.
const RED_ZONE: usize = 100 * 1024;

/// The size of each new stack segment for the reader and the writers.
const NEW_SEGMENT: usize = 1024 * 1024;

/// The stack a render needs to read its data with serde_json's default
/// limit of 128 nested levels. A debug build used about 175 KiB to render a
/// page whose data nests 120 levels (measured on macOS arm64).
const DATA_RED_ZONE: usize = 256 * 1024;

/// The stack freeing a read program needs: its tree is at most
/// `MAX_READ_DEPTH` levels deep, and freeing one level takes a few small
/// frames.
const FREE_RED_ZONE: usize = 1024 * 1024;

/// The stack for work in `with_large_stack`. A debug build needed about
/// 9.3 MiB to compile 512 nested `<div v-for>` elements (measured on macOS
/// arm64), the depth the nesting limits planned in #272 allow, so this
/// leaves a margin of about 70%. A release build needs less.
const LARGE_STACK: usize = 16 * 1024 * 1024;

/// Run `work` with at least `RED_ZONE` bytes of stack available.
///
/// The work must not call into Python: CPython 3.14 and later check the stack
/// pointer against the thread's own stack, and a heap segment is outside it.
/// The same rule applies to every function here.
pub(crate) fn with_enough_stack<T>(work: impl FnOnce() -> T) -> T {
    stacker::maybe_grow(RED_ZONE, NEW_SEGMENT, work)
}

/// Run `work`, which reads JSON with serde_json's default nesting limit,
/// with at least `DATA_RED_ZONE` bytes of stack available.
pub(crate) fn with_stack_for_data<T>(work: impl FnOnce() -> T) -> T {
    stacker::maybe_grow(DATA_RED_ZONE, NEW_SEGMENT, work)
}

/// Run `work`, which frees a read program's tree, with at least
/// `FREE_RED_ZONE` bytes of stack available.
pub(crate) fn with_stack_for_freeing<T>(work: impl FnOnce() -> T) -> T {
    stacker::maybe_grow(FREE_RED_ZONE, FREE_RED_ZONE, work)
}

/// Run `work` with `LARGE_STACK` bytes of stack available, for recursion
/// that Citry cannot guard level by level.
pub(crate) fn with_large_stack<T>(work: impl FnOnce() -> T) -> T {
    stacker::maybe_grow(LARGE_STACK, LARGE_STACK, work)
}
