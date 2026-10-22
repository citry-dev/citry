//! The JSON text Python's `json.dumps(ensure_ascii=True)` writes, with or
//! without `script_json`'s extra escape for `<`.

use std::fmt::Write as _;

/// Write `text` as a JSON string the way `json.dumps(ensure_ascii=True)`
/// does, with `<` also written as `\u003c`, as `script_json` does, so
/// the JSON is safe inside a `<script>` element.
///
/// `json.dumps` escapes every character outside printable ASCII (space to
/// `~`), so DEL and every non-ASCII character are escaped too, with
/// lowercase hex digits, and two `\u` escapes (a UTF-16 surrogate pair)
/// for characters above U+FFFF.
pub fn write_json_str(out: &mut String, text: &str) {
    write_json_string(out, text, true);
}

/// Write `text` as a JSON string exactly as `json.dumps(ensure_ascii=True)`
/// does, leaving `<` as is. Citry's ids hash this plain JSON text.
pub fn write_plain_json_str(out: &mut String, text: &str) {
    write_json_string(out, text, false);
}

fn write_json_string(out: &mut String, text: &str, escape_lt: bool) {
    out.push('"');
    let bytes = text.as_bytes();
    let mut start = 0;
    let mut index = 0;
    while index < bytes.len() {
        let byte = bytes[index];
        // Printable ASCII other than `"`, `\` and (for script JSON) `<` is
        // copied in runs, which covers almost all real text.
        if (0x20..=0x7e).contains(&byte)
            && byte != b'"'
            && byte != b'\\'
            && (byte != b'<' || !escape_lt)
        {
            index += 1;
            continue;
        }
        out.push_str(&text[start..index]);
        if byte < 0x80 {
            match byte {
                b'"' => out.push_str("\\\""),
                b'\\' => out.push_str("\\\\"),
                b'\n' => out.push_str("\\n"),
                b'\r' => out.push_str("\\r"),
                b'\t' => out.push_str("\\t"),
                0x08 => out.push_str("\\b"),
                0x0c => out.push_str("\\f"),
                // '<', DEL and the other control characters.
                _ => write!(out, "\\u{byte:04x}").expect("writing to a String cannot fail"),
            }
            index += 1;
        } else {
            let character = text[index..]
                .chars()
                .next()
                .expect("index is on a char boundary");
            let mut units = [0u16; 2];
            for unit in character.encode_utf16(&mut units) {
                write!(out, "\\u{unit:04x}").expect("writing to a String cannot fail");
            }
            index += character.len_utf8();
        }
        start = index;
    }
    out.push_str(&text[start..]);
    out.push('"');
}
