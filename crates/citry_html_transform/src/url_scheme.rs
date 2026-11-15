//! Read the scheme of a URL the way the browser's URL parser reads it.
//!
//! The server-side checks that decide what a URL may do read its scheme
//! here: the output checks (`javascript:` and `data:` URLs in a finished
//! page), Events `Redirect`, the no-JavaScript redirect resolver, and Citry
//! UI's link and image checks. One reader means one answer: a check cannot
//! read `java\tscript:` as harmless while another reads it as `javascript`.
//!
//! The rules are the first steps of the WHATWG URL parser
//! (<https://url.spec.whatwg.org/#concept-basic-url-parser>):
//!
//! 1. Leading U+0000 to U+0020 (C0 controls and space) are skipped.
//! 2. Tab, line feed and carriage return are skipped wherever they appear.
//! 3. In the "scheme start state" the first character must be an ASCII
//!    letter.
//! 4. In the "scheme state" ASCII letters, digits, `+`, `-` and `.` follow
//!    up to a `:`. Any other character, or no `:`, means the URL has no
//!    scheme, so the browser reads it as relative.
//! 5. The scheme is lowercased, ASCII letters only.
//!
//! Nothing here decodes character references or percent escapes. The HTML
//! tokenizer decodes attribute text before the URL parser sees it, so a
//! caller holding attribute text or a `Markup` value decodes it first.
//! The parser also strips trailing C0 controls and spaces, but a trailing
//! strip can never remove the scheme's colon, so reading the scheme never
//! needs the end of the string. [`UrlScheme::after_colon`] trims it only
//! when a caller asks for the rest.

/// The scheme of a URL as the browser's URL parser reads it, returned by
/// [`url_scheme`].
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct UrlScheme<'a> {
    /// The URL with leading C0 controls and spaces removed.
    text: &'a str,
    /// Byte index of the colon that ends the scheme in `text`.
    colon: usize,
}

impl<'a> UrlScheme<'a> {
    /// Whether the scheme is `name`, which must be a lowercase ASCII
    /// scheme such as `"javascript"`. Tab, line feed and carriage return
    /// inside the scheme are ignored, and ASCII letters match in any case.
    pub fn is(&self, name: &str) -> bool {
        // `scheme_matches` stops at the first difference, so a long scheme
        // costs no more than `name` does.
        scheme_matches(significant_chars(&self.text[..self.colon]), name)
            .is_some_and(|mut rest| rest.next().is_none())
    }

    /// The scheme in lowercase, with tab, line feed and carriage return
    /// removed, as the browser reports it (without the colon).
    pub fn to_lowercase(&self) -> String {
        significant_chars(&self.text[..self.colon])
            .map(|c| c.to_ascii_lowercase())
            .collect()
    }

    /// The text after the scheme's colon, with trailing C0 controls and
    /// spaces trimmed as the URL parser trims them. It may still hold tab,
    /// line feed and carriage return, which the parser removes later.
    pub fn after_colon(&self) -> &'a str {
        // The trim happens only here, so a caller that needs only the
        // scheme never walks the rest of a long URL.
        self.text[self.colon + 1..].trim_end_matches(is_c0_control_or_space)
    }
}

/// Read the scheme of `url`, or return `None` when the browser reads it as
/// a relative URL (such as `/orders`, `?page=2`, `//example.com/x`, or
/// `java script:x`).
pub fn url_scheme(url: &str) -> Option<UrlScheme<'_>> {
    let text = url.trim_start_matches(is_c0_control_or_space);
    let mut chars = text.char_indices().filter(|&(_, c)| !is_tab_or_newline(c));
    // Scheme start state: anything but an ASCII letter makes it relative.
    if !chars.next().is_some_and(|(_, c)| c.is_ascii_alphabetic()) {
        return None;
    }
    // Scheme state: scheme characters run up to the colon; any other
    // character, or the end of the text, means there is no scheme.
    for (index, c) in chars {
        if c == ':' {
            return Some(UrlScheme { text, colon: index });
        }
        if !is_scheme_char(c) {
            return None;
        }
    }
    None
}

/// Whether `url` has the scheme `name`, which must be a lowercase ASCII
/// scheme such as `"javascript"` or `"data"`.
///
/// This gives the same answer as calling [`url_scheme`] and then
/// [`UrlScheme::is`], but stops after reading `name` and the character
/// after it (not counting tab, line feed and carriage return), so the
/// output checks, which ask this of every URL attribute in a page, do not
/// read a long scheme to its end.
pub fn url_scheme_is(url: &str, name: &str) -> bool {
    debug_assert!(
        is_lowercase_scheme(name),
        "{name:?} is not a lowercase scheme"
    );
    let text = url.trim_start_matches(is_c0_control_or_space);
    // `name` starts with a letter and holds only scheme characters, so
    // matching it accepts the same characters the scheme rules in the module
    // docs accept; only the colon
    // right after it is left to check.
    scheme_matches(significant_chars(text), name).is_some_and(|mut rest| rest.next() == Some(':'))
}

/// The characters of `text` that the URL parser keeps: all but tab, line
/// feed and carriage return, which it removes anywhere in the URL.
fn significant_chars(text: &str) -> impl Iterator<Item = char> + '_ {
    text.chars().filter(|&c| !is_tab_or_newline(c))
}

/// Match the start of `chars` against `name` with ASCII letters compared in
/// any case, and return the characters after it, or `None` at the first
/// difference.
fn scheme_matches<I: Iterator<Item = char>>(mut chars: I, name: &str) -> Option<I> {
    for expected in name.chars() {
        // Only ASCII letters fold, so `ſ` (U+017F) or the Kelvin sign never
        // match `s` or `k`, just as the browser reads them.
        if chars.next()?.to_ascii_lowercase() != expected {
            return None;
        }
    }
    Some(chars)
}

fn is_c0_control_or_space(c: char) -> bool {
    c <= '\u{20}'
}

fn is_tab_or_newline(c: char) -> bool {
    matches!(c, '\t' | '\n' | '\r')
}

fn is_scheme_char(c: char) -> bool {
    c.is_ascii_alphanumeric() || matches!(c, '+' | '-' | '.')
}

fn is_lowercase_scheme(name: &str) -> bool {
    let mut chars = name.chars();
    chars.next().is_some_and(|c| c.is_ascii_lowercase())
        && chars
            .all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || matches!(c, '+' | '-' | '.'))
}

#[cfg(test)]
mod tests {
    use super::*;

    /// A second reading of the same rules, written plainly with an owned
    /// string, so the tests compare two independent implementations.
    fn reference_scheme(url: &str) -> Option<(String, String)> {
        let trimmed: String = url
            .chars()
            .skip_while(|c| (*c as u32) <= 0x20)
            .filter(|c| !['\t', '\n', '\r'].contains(c))
            .collect();
        let (scheme, rest) = trimmed.split_once(':')?;
        let first = scheme.chars().next()?;
        if !first.is_ascii_alphabetic() {
            return None;
        }
        let allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-.";
        if !scheme.chars().all(|c| allowed.contains(c)) {
            return None;
        }
        let rest = rest.trim_end_matches(|c: char| (c as u32) <= 0x20);
        Some((scheme.to_ascii_lowercase(), rest.to_owned()))
    }

    /// What the Python binding returns: the scheme and the text after the
    /// colon with tab, line feed and carriage return removed.
    fn read(url: &str) -> Option<(String, String)> {
        url_scheme(url).map(|scheme| {
            let rest = scheme.after_colon().replace(['\t', '\n', '\r'], "");
            (scheme.to_lowercase(), rest)
        })
    }

    /// One row of the shared table in
    /// `tests/fixtures/url_schemes.json`, which the Python and JavaScript
    /// tests read too.
    struct Row {
        url: String,
        scheme: Option<String>,
        rest: Option<String>,
    }

    fn table() -> Vec<Row> {
        let text = include_str!("../tests/fixtures/url_schemes.json");
        // Each row sits on its own line. Rows marked `python_only` hold a
        // lone surrogate, which a Rust string cannot hold (and serde_json
        // refuses), so those lines are skipped before parsing.
        let rows: Vec<Row> = text
            .lines()
            .map(str::trim)
            .filter(|line| line.starts_with("{\"url\"") && !line.contains("\"python_only\""))
            .map(|line| {
                let value: serde_json::Value =
                    serde_json::from_str(line.trim_end_matches(',')).expect(line);
                let field = |key: &str| value[key].as_str().map(str::to_owned);
                Row {
                    url: field("url").expect(line),
                    scheme: field("scheme"),
                    rest: field("rest"),
                }
            })
            .collect();
        // A row written over several lines would be skipped silently, so
        // every row the file holds must be one parsed here or one skipped
        // as `python_only`.
        let skipped = text.matches("\"python_only\"").count();
        assert_eq!(rows.len() + skipped, text.matches("\"url\":").count());
        // A table that stopped parsing must fail, not pass with no rows.
        assert!(rows.len() > 50, "only {} rows parsed", rows.len());
        rows
    }

    #[test]
    fn the_shared_table_reads_as_written() {
        for row in table() {
            let expected = row
                .scheme
                .clone()
                .map(|scheme| (scheme, row.rest.clone().unwrap()));
            assert_eq!(read(&row.url), expected, "{:?}", row.url);
            assert_eq!(reference_scheme(&row.url), expected, "{:?}", row.url);
        }
    }

    #[test]
    fn scheme_checks_agree_with_the_full_reading() {
        let names = ["javascript", "data", "http", "https", "a", "a+b-c.d", "x1"];
        for row in table() {
            for name in names {
                let full = url_scheme(&row.url).is_some_and(|scheme| scheme.is(name));
                assert_eq!(url_scheme_is(&row.url, name), full, "{:?} {name}", row.url);
                assert_eq!(
                    full,
                    row.scheme.as_deref() == Some(name),
                    "{:?} {name}",
                    row.url
                );
            }
        }
    }

    #[test]
    fn generated_urls_read_like_the_reference() {
        // The alphabet holds the characters a careless reader gets wrong:
        // non-ASCII letters that Unicode case folding turns into ASCII,
        // controls the parser strips only at the ends, and scheme
        // punctuation.
        let alphabet: Vec<char> = "jJsSaAvVcCrRiIpPtTdDkK0123456789:+-./?#% \t\n\r\
            \u{0}\u{1}\u{b}\u{c}\u{1f}\u{7f}\u{a0}\u{17f}\u{131}\u{130}\u{212a}\u{feff}\u{200b}"
            .chars()
            .collect();
        // A small random number generator with a fixed seed, so a failure
        // names the same URL on every run and no random-number crate is
        // needed.
        let mut state: u64 = 0x9e37_79b9_7f4a_7c15;
        let mut next = |limit: usize| {
            state ^= state << 13;
            state ^= state >> 7;
            state ^= state << 17;
            (state % limit as u64) as usize
        };
        let mut with_scheme = 0;
        for _ in 0..20_000 {
            let length = next(14);
            let mut url: String = (0..length)
                .map(|_| alphabet[next(alphabet.len())])
                .collect();
            // Start a third of the strings with a scheme-like prefix, so most
            // runs reach the scheme branch. Two prefixes have no colon, so
            // the random tail decides whether a scheme exists.
            if next(3) == 0 {
                let prefixes = ["javascript:", "data:", "JaVa\tScRipt", " h\nttps:", "a"];
                url.insert_str(0, prefixes[next(prefixes.len())]);
            }
            let read_back = read(&url);
            assert_eq!(read_back, reference_scheme(&url), "{url:?}");
            with_scheme += usize::from(read_back.is_some());
            for name in ["javascript", "data", "https"] {
                let full = url_scheme(&url).is_some_and(|scheme| scheme.is(name));
                assert_eq!(url_scheme_is(&url, name), full, "{url:?} {name}");
            }
        }
        // A generator that stopped producing schemes would test only one
        // branch.
        assert!(with_scheme > 3_000, "only {with_scheme} URLs had a scheme");
    }

    #[test]
    fn a_long_scheme_or_padding_is_read_in_linear_time() {
        // A quadratic reading would take minutes on these; a linear one
        // takes a few milliseconds each. The bound is loose so a slow
        // machine does not fail it.
        let long = format!("{}:x", "a".repeat(1_000_000));
        let padded = format!("{}javascript:x", " ".repeat(1_000_000));
        let tabs = format!("java{}script:x", "\t".repeat(1_000_000));
        let started = std::time::Instant::now();
        assert_eq!(
            url_scheme(&long).map(|s| s.to_lowercase().len()),
            Some(1_000_000)
        );
        assert!(!url_scheme_is(&long, "javascript"));
        assert!(url_scheme_is(&padded, "javascript"));
        assert!(url_scheme_is(&tabs, "javascript"));
        assert!(
            started.elapsed().as_secs() < 2,
            "took {:?}",
            started.elapsed()
        );
    }
}
