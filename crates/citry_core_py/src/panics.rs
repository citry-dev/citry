//! Turn a Rust panic into an error Python can handle.
//!
//! Without this, a panic reaches Python as PyO3's `PanicException`, which
//! derives from `BaseException`, so ordinary `except Exception` handling in
//! Citry never sees it and the whole call aborts.

use std::any::Any;
use std::panic::{AssertUnwindSafe, catch_unwind};

/// Run `body`, returning the panic's message as `Err` if it panics.
pub(crate) fn catch_panic<T>(body: impl FnOnce() -> T) -> Result<T, String> {
    catch_unwind(AssertUnwindSafe(body)).map_err(panic_message)
}

fn panic_message(payload: Box<dyn Any + Send>) -> String {
    payload
        .downcast_ref::<&str>()
        .map(|text| (*text).to_owned())
        .or_else(|| payload.downcast_ref::<String>().cloned())
        .unwrap_or_else(|| "unknown panic".to_owned())
}

#[cfg(test)]
mod tests {
    use super::catch_panic;

    #[test]
    fn a_panic_becomes_its_message() {
        assert_eq!(catch_panic(|| 7), Ok(7));
        assert_eq!(
            catch_panic(|| -> u8 { panic!("boom") }),
            Err("boom".to_owned())
        );
        let detail = format!("index {}", 3);
        assert_eq!(
            catch_panic(|| -> u8 { panic!("{detail}") }),
            Err("index 3".to_owned())
        );
    }
}
