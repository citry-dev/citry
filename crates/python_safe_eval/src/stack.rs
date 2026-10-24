//! Make sure python_safe_eval's own passes over one expression have enough
//! stack, whatever thread runs them.
//!
//! The passes over an expression's tree (the keyword check, the sandbox
//! transformer, and code generation) call themselves once per tree level.
//! `nesting::MAX_NESTING` bounds the depth, but at that depth the passes still
//! need more stack than a small thread has: a debug build used about 9 KB per
//! level (measured on macOS arm64, where a 256 KiB thread handled only about
//! 28 levels), and a release build about 1.2 KB.
//!
//! So each public entry point runs its work through `with_enough_stack`. When
//! less than `RED_ZONE` is left, `stacker` runs the work on a new stack
//! segment taken from the heap. On a large thread, such as the usual 8 MB
//! main thread on Linux and macOS, nothing is allocated and the check is
//! cheap.
//!
//! On wasm32 (Pyodide), `stacker` cannot tell how much stack is left, so every
//! outermost call takes a new segment from the heap and frees it afterwards.
//! It can move the part of the stack that lives in WebAssembly memory, but
//! not the engine's own call stack. A native release build used about 1.2 KB
//! per level; if WebAssembly frames cost about the same, the limit needs
//! about 240 KB. Engines usually give WebAssembly about
//! 1 MB of call stack, but Pyodide's exact figure is not confirmed here. The
//! release smoke script (`scripts/smoke_citry_core.py`), which runs inside
//! Pyodide when citry-core is qualified for release, checks the largest
//! accepted expressions there.

/// The stack one expression can need: 200 levels at about 9 KB each is about
/// 1.8 MB in a debug build, rounded up for a margin.
const RED_ZONE: usize = 2 * 1024 * 1024;

/// The size of a new segment, twice the red zone, so one segment holds the
/// passes over a whole expression.
const SEGMENT: usize = 4 * 1024 * 1024;

/// Run `work` with at least `RED_ZONE` bytes of stack available.
///
/// The work must not call into Python: CPython 3.14 and later check the stack
/// pointer against the thread's own stack, and a heap segment is outside it.
pub(crate) fn with_enough_stack<T>(work: impl FnOnce() -> T) -> T {
    stacker::maybe_grow(RED_ZONE, SEGMENT, work)
}
