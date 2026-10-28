//! Give the recursive passes over a template tree enough stack, whatever
//! thread runs them.
//!
//! The compiler calls itself once per nesting level. A debug build used
//! about 18 KB of stack per compiler level, so a template a few hundred
//! levels deep overflowed a small thread and crashed the process. The
//! parser also parses a template written in an attribute value by calling
//! itself, and `Template`'s `Debug` prints each level by calling itself.
//! The parser's passes over the finished tree, and `Template`'s clone,
//! comparison and drop, keep their own list of what is left to visit
//! instead, so they need no guard.
//!
//! Each recursion entry runs its work through `with_enough_stack`. When less
//! than `RED_ZONE` is left, `stacker` runs the work on a new segment of
//! `NEW_SEGMENT` bytes taken from the heap, and later levels keep using that
//! segment until it too runs low. On a thread with room to spare, nothing is
//! allocated and the check is cheap. The sizes follow Ruff's parser, which
//! ships inside citry_core and guards its own recursion the same way.
//!
//! On wasm32 (Pyodide), `stacker` cannot tell how much stack is left, so
//! every guarded call not already running on a new segment takes a 1 MiB
//! block from the heap and frees it afterwards. When Python calls the
//! parser, the Python bindings' own guard takes one block for the whole
//! call, and the guards inside reuse it. When Rust code calls the parser
//! with no guard around it, each outermost template written in an
//! attribute value, and each embedded expression parsed outside one, takes
//! one block.

/// Run the work on a new segment when less stack than this is left: enough
/// for the largest frames between two guarded calls, about 18 KB per
/// compiler level in a debug build, with a wide margin.
const RED_ZONE: usize = 100 * 1024;

/// The red zone for parsing one embedded expression, which covers the
/// measured 100 KiB of its error path with a margin.
const EXPRESSION_RED_ZONE: usize = 256 * 1024;

/// The size of each new stack segment.
const NEW_SEGMENT: usize = 1024 * 1024;

/// Run `work` with at least `RED_ZONE` bytes of stack available.
///
/// The Python bindings (`citry_core_py`) also run the Rust work of each
/// entry point Python calls that does deep work through it. CPython lets a call
/// into an extension through with only about 20 KiB of stack left, and the
/// large frames of a debug build can use more than that before the first
/// guard inside the work, so the guard comes first.
///
/// The work must not call into Python: CPython 3.14 and later check the stack
/// pointer against the thread's own stack, and a heap segment is outside it.
pub fn with_enough_stack<T>(work: impl FnOnce() -> T) -> T {
    stacker::maybe_grow(RED_ZONE, NEW_SEGMENT, work)
}

/// Run `work` like [`with_enough_stack`], but only where `stacker` can
/// measure the stack.
///
/// The Python bindings use this for entry points that run on every render,
/// such as the output HTML checks, message lookups and browser expression
/// analysis. On wasm32, `stacker` cannot measure the stack, so a guard there
/// would take a 1 MiB block from the heap on every call; there the work runs
/// on the current stack, unchecked.
pub fn with_enough_stack_where_measurable<T>(work: impl FnOnce() -> T) -> T {
    #[cfg(target_arch = "wasm32")]
    {
        work()
    }
    #[cfg(not(target_arch = "wasm32"))]
    {
        with_enough_stack(work)
    }
}

/// Run the work of parsing one embedded expression with enough stack.
///
/// Reporting an invalid expression needs far more stack than parsing a valid
/// one: a debug build needed about 148 KiB for `{{ x + }}` and 48 KiB for
/// `{{ x }}` (measured on macOS arm64), more than a 128 KiB thread has. So
/// this call keeps a larger red zone than the general guard's `RED_ZONE`.
pub(crate) fn with_stack_for_expression<T>(work: impl FnOnce() -> T) -> T {
    stacker::maybe_grow(EXPRESSION_RED_ZONE, NEW_SEGMENT, work)
}
