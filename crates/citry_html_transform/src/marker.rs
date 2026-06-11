//! Root-marking scan over serialized component frames.
//!
//! [`mark_html`] walks the HTML once, splices the given attributes onto
//! root-level (depth 0) tags, and splits the result around child placeholder
//! elements so the caller can join in each child's finished HTML without a
//! second scan. Bytes it does not touch are copied through verbatim: no
//! re-serialization, no normalization, no entity handling. It cannot fail;
//! markup it does not understand is treated as text.
//!
//! [`transform_html`](crate::transform_html) stays the right tool when every
//! element of the input must be rewritten (its `all_attributes` mode); this
//! scanner only touches root-level tags.

use crate::transformer::is_void_element;

/// Elements whose content is raw text in HTML5: markup-like text inside them
/// is not markup, so the scanner skips to their matching closing tag instead
/// of interpreting their content.
const RAW_TEXT_ELEMENTS: [&str; 4] = ["script", "style", "textarea", "title"];

/// One placeholder element found by [`mark_html`].
pub struct MarkedPlaceholder {
    /// The value of the placeholder attribute (the child's render id).
    pub id: String,
    /// The placeholder element's text, including any spliced attributes.
    /// Callers that do not recognize `id` emit this verbatim.
    pub html: String,
    /// The attributes spliced into this placeholder (a subset of
    /// `root_attributes`; non-empty only when the placeholder sat at depth 0).
    pub added_attributes: Vec<String>,
}

/// The result of [`mark_html`].
///
/// The marked frame is `segments[0] + placeholders[0].html + segments[1] +
/// ... + segments[n]`; there is always exactly one more segment than
/// placeholders.
pub struct MarkedHtml {
    pub segments: Vec<String>,
    pub placeholders: Vec<MarkedPlaceholder>,
}

/// Splice `root_attributes` (as `attr=""`) onto every root-level (depth 0)
/// tag of `html`, and split the output around placeholder elements.
///
/// A placeholder is a `<template>` element (any ASCII case) that carries
/// `placeholder_attr` and whose body is only whitespace, e.g.
/// `<template c-render-id="cAb3d9"></template>`.
///
/// Root-level void and self-closing tags are marked too. Depth tracking
/// understands comments, doctype, CDATA, processing instructions, raw-text
/// elements (`<script>` etc.), and quoted attribute values containing `>`.
pub fn mark_html(html: &str, root_attributes: &[String], placeholder_attr: &str) -> MarkedHtml {
    let bytes = html.as_bytes();
    let len = bytes.len();
    let splice: String = root_attributes
        .iter()
        .map(|attr| format!(" {attr}=\"\""))
        .collect();

    let mut segments: Vec<String> = Vec::new();
    let mut placeholders: Vec<MarkedPlaceholder> = Vec::new();
    let mut seg = String::with_capacity(len + splice.len());
    let mut depth: i32 = 0;
    let mut pos = 0;

    while pos < len {
        // Copy text verbatim up to the next '<'.
        let Some(lt) = find_byte(bytes, pos, b'<') else {
            seg.push_str(&html[pos..]);
            break;
        };
        seg.push_str(&html[pos..lt]);
        pos = lt;

        if starts_with_at(bytes, pos, b"<!--") {
            // Comment: copy through `-->` (or to EOF when unterminated).
            let end = find_seq(bytes, pos + 4, b"-->").map_or(len, |i| i + 3);
            seg.push_str(&html[pos..end]);
            pos = end;
        } else if starts_with_at(bytes, pos, b"<![CDATA[") {
            let end = find_seq(bytes, pos + 9, b"]]>").map_or(len, |i| i + 3);
            seg.push_str(&html[pos..end]);
            pos = end;
        } else if starts_with_at(bytes, pos, b"<!") || starts_with_at(bytes, pos, b"<?") {
            // Doctype or processing instruction: copy through the next '>'.
            let end = find_byte(bytes, pos, b'>').map_or(len, |i| i + 1);
            seg.push_str(&html[pos..end]);
            pos = end;
        } else if starts_with_at(bytes, pos, b"</") {
            // End tag.
            let name_start = pos + 2;
            let mut i = name_start;
            while i < len && !is_ws(bytes[i]) && bytes[i] != b'>' {
                i += 1;
            }
            let name_end = i;
            let end = find_byte(bytes, pos, b'>').map_or(len, |i| i + 1);
            if !is_void_element(&bytes[name_start..name_end]) {
                depth -= 1;
            }
            seg.push_str(&html[pos..end]);
            pos = end;
        } else if pos + 1 < len && bytes[pos + 1].is_ascii_alphabetic() {
            // Start tag.
            let tag = lex_start_tag(bytes, pos, placeholder_attr);
            let name = &bytes[tag.name_start..tag.name_end];
            let at_root = depth == 0;
            let added: &str = if at_root { &splice } else { "" };

            // A placeholder: a `<template placeholder_attr=...>` whose body is
            // only whitespace up to its own `</template>`.
            let placeholder_end = if !tag.self_closing && name.eq_ignore_ascii_case(b"template") {
                tag.placeholder_value
                    .and_then(|_| placeholder_close_end(bytes, tag.end))
            } else {
                None
            };

            if let Some(ph_end) = placeholder_end {
                let (val_start, val_end) = tag.placeholder_value.expect("checked above");
                let mut ph_html = String::with_capacity(ph_end - pos + added.len());
                ph_html.push_str(&html[pos..tag.insert_pos]);
                ph_html.push_str(added);
                ph_html.push_str(&html[tag.insert_pos..ph_end]);
                placeholders.push(MarkedPlaceholder {
                    id: html[val_start..val_end].to_string(),
                    html: ph_html,
                    added_attributes: if at_root {
                        root_attributes.to_vec()
                    } else {
                        Vec::new()
                    },
                });
                segments.push(std::mem::take(&mut seg));
                pos = ph_end;
                // The whole element was consumed, so depth is unchanged.
                continue;
            }

            seg.push_str(&html[pos..tag.insert_pos]);
            seg.push_str(added);
            seg.push_str(&html[tag.insert_pos..tag.end]);
            pos = tag.end;

            if !tag.self_closing && !is_void_element(name) {
                if let Some(content_end) = raw_text_content_end(bytes, pos, name) {
                    // Raw-text element: its content is not markup. Copy it and
                    // the closing tag through; depth is unchanged.
                    seg.push_str(&html[pos..content_end]);
                    pos = content_end;
                } else {
                    depth += 1;
                }
            }
        } else {
            // A bare '<' that opens no construct: plain text.
            seg.push('<');
            pos += 1;
        }
    }

    segments.push(seg);
    MarkedHtml {
        segments,
        placeholders,
    }
}

/// A lexed start tag. All positions are byte offsets into the scanned input,
/// and all sit on ASCII bytes, so they are valid `str` slice boundaries.
struct StartTag {
    name_start: usize,
    name_end: usize,
    /// Where spliced attributes go: right after the last attribute (or the
    /// tag name), before any trailing whitespace and the `>` / `/>`.
    insert_pos: usize,
    /// One past the closing `>`.
    end: usize,
    self_closing: bool,
    /// Span of the placeholder attribute's value, when the tag carries it.
    placeholder_value: Option<(usize, usize)>,
}

/// Lex one start tag beginning at `start` (which holds `<`). Quoted attribute
/// values may contain `>`. Never fails; at EOF the tag just ends there.
fn lex_start_tag(bytes: &[u8], start: usize, placeholder_attr: &str) -> StartTag {
    let len = bytes.len();
    let name_start = start + 1;
    let mut i = name_start;
    while i < len && !is_ws(bytes[i]) && bytes[i] != b'/' && bytes[i] != b'>' {
        i += 1;
    }
    let name_end = i;
    let mut insert_pos = i;
    let mut placeholder_value: Option<(usize, usize)> = None;

    macro_rules! tag {
        ($end:expr, $self_closing:expr) => {
            StartTag {
                name_start,
                name_end,
                insert_pos,
                end: $end,
                self_closing: $self_closing,
                placeholder_value,
            }
        };
    }

    loop {
        while i < len && is_ws(bytes[i]) {
            i += 1;
        }
        if i >= len {
            return tag!(len, false);
        }
        match bytes[i] {
            b'>' => return tag!(i + 1, false),
            b'/' if i + 1 < len && bytes[i + 1] == b'>' => return tag!(i + 2, true),
            b'/' => i += 1, // stray slash inside the tag, skip it
            _ => {
                // Attribute name.
                let attr_start = i;
                while i < len
                    && !is_ws(bytes[i])
                    && bytes[i] != b'='
                    && bytes[i] != b'>'
                    && bytes[i] != b'/'
                {
                    i += 1;
                }
                let attr_end = i;
                let mut j = i;
                while j < len && is_ws(bytes[j]) {
                    j += 1;
                }
                let value = if j < len && bytes[j] == b'=' {
                    j += 1;
                    while j < len && is_ws(bytes[j]) {
                        j += 1;
                    }
                    if j < len && (bytes[j] == b'"' || bytes[j] == b'\'') {
                        let quote = bytes[j];
                        j += 1;
                        let val_start = j;
                        while j < len && bytes[j] != quote {
                            j += 1;
                        }
                        let val_end = j;
                        if j < len {
                            j += 1; // the closing quote
                        }
                        i = j;
                        Some((val_start, val_end))
                    } else {
                        // Unquoted value (may contain '/', per HTML5).
                        let val_start = j;
                        while j < len && !is_ws(bytes[j]) && bytes[j] != b'>' {
                            j += 1;
                        }
                        i = j;
                        Some((val_start, j))
                    }
                } else {
                    // Boolean attribute; do not consume the lookahead whitespace.
                    Some((attr_end, attr_end))
                };
                if bytes[attr_start..attr_end].eq_ignore_ascii_case(placeholder_attr.as_bytes()) {
                    placeholder_value = value;
                }
                insert_pos = i;
            }
        }
    }
}

/// When the bytes at `from` are only whitespace followed by a `</template>`
/// end tag, return one past that end tag's `>`; otherwise `None`.
fn placeholder_close_end(bytes: &[u8], from: usize) -> Option<usize> {
    let len = bytes.len();
    let mut i = from;
    while i < len && is_ws(bytes[i]) {
        i += 1;
    }
    if !starts_with_at(bytes, i, b"</") {
        return None;
    }
    let name_end = i + 2 + "template".len();
    if name_end > len || !bytes[i + 2..name_end].eq_ignore_ascii_case(b"template") {
        return None;
    }
    let mut j = name_end;
    while j < len && is_ws(bytes[j]) {
        j += 1;
    }
    if j < len && bytes[j] == b'>' {
        Some(j + 1)
    } else {
        None
    }
}

/// For a raw-text element named `name`, return one past the `>` of its
/// matching closing tag (searching from `from`, the end of the start tag), or
/// the input length when the closing tag is missing. Returns `None` when
/// `name` is not a raw-text element.
fn raw_text_content_end(bytes: &[u8], from: usize, name: &[u8]) -> Option<usize> {
    RAW_TEXT_ELEMENTS
        .iter()
        .find(|raw| raw.as_bytes().eq_ignore_ascii_case(name))?;
    let len = bytes.len();
    let mut i = from;
    while i + 2 + name.len() <= len {
        if bytes[i] == b'<'
            && bytes[i + 1] == b'/'
            && bytes[i + 2..i + 2 + name.len()].eq_ignore_ascii_case(name)
        {
            // HTML5: the name must be followed by whitespace, '/', or '>'.
            let after = i + 2 + name.len();
            if after >= len || is_ws(bytes[after]) || bytes[after] == b'/' || bytes[after] == b'>' {
                return Some(find_byte(bytes, after, b'>').map_or(len, |k| k + 1));
            }
        }
        i += 1;
    }
    Some(len)
}

fn is_ws(b: u8) -> bool {
    matches!(b, b' ' | b'\t' | b'\n' | b'\r' | b'\x0C')
}

fn find_byte(bytes: &[u8], from: usize, needle: u8) -> Option<usize> {
    bytes[from..]
        .iter()
        .position(|&b| b == needle)
        .map(|i| from + i)
}

fn starts_with_at(bytes: &[u8], at: usize, prefix: &[u8]) -> bool {
    bytes.len() >= at + prefix.len() && &bytes[at..at + prefix.len()] == prefix
}

fn find_seq(bytes: &[u8], from: usize, needle: &[u8]) -> Option<usize> {
    if from >= bytes.len() {
        return None;
    }
    bytes[from..]
        .windows(needle.len())
        .position(|w| w == needle)
        .map(|i| from + i)
}
