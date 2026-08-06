use std::borrow::Cow;

/// Select the first physical newline sequence in the document.
pub(crate) fn detect_newline(source: &str) -> &'static str {
    let bytes = source.as_bytes();
    let mut index = 0;
    while index < bytes.len() {
        match bytes[index] {
            b'\r' if bytes.get(index + 1) == Some(&b'\n') => return "\r\n",
            b'\r' => return "\r",
            b'\n' => return "\n",
            _ => index += 1,
        }
    }
    "\n"
}

/// Normalize all physical newline spellings for internal line processing.
pub(crate) fn normalize_to_lf(source: &str) -> Cow<'_, str> {
    if !source.contains('\r') {
        return Cow::Borrowed(source);
    }

    let mut normalized = String::with_capacity(source.len());
    let bytes = source.as_bytes();
    let mut cursor = 0;
    let mut segment_start = 0;
    while cursor < bytes.len() {
        if bytes[cursor] != b'\r' {
            cursor += 1;
            continue;
        }
        normalized.push_str(&source[segment_start..cursor]);
        normalized.push('\n');
        cursor += 1;
        if bytes.get(cursor) == Some(&b'\n') {
            cursor += 1;
        }
        segment_start = cursor;
    }
    normalized.push_str(&source[segment_start..]);
    Cow::Owned(normalized)
}

#[cfg(test)]
mod tests {
    use super::{detect_newline, normalize_to_lf};

    #[test]
    fn first_newline_wins_for_mixed_sources() {
        assert_eq!(detect_newline("first\nsecond\r\nthird"), "\n");
        assert_eq!(detect_newline("first\r\nsecond\nthird"), "\r\n");
        assert_eq!(detect_newline("first\rsecond\nthird"), "\r");
        assert_eq!(detect_newline("no newline"), "\n");
    }

    #[test]
    fn internal_line_processing_handles_every_physical_spelling() {
        assert_eq!(normalize_to_lf("a\nb\r\nc\rd"), "a\nb\nc\nd");
    }
}
