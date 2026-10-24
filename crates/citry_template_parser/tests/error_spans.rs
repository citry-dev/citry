//! A parse error over many lines is built quickly, and reads exactly as pest
//! would build it.
//!
//! Pest's own `Error::new_from_span` takes time that grows with the number of
//! lines in the span times the length of the input, so `ParseError::from_span`
//! builds long spans from a copy of their first and last lines. These tests
//! check that the result is identical, field for field, and that a long span
//! is fast.

use std::time::{Duration, Instant};

use citry_template_parser::error::ParseError;
use citry_template_parser::parser::parse_template;

/// The text and debug form that users and tests see for an error.
fn rendered(error: &ParseError) -> (String, String) {
    (error.to_string(), format!("{error:?}"))
}

/// A small, fixed random number generator, so a failure always reproduces.
struct XorShift(u64);

impl XorShift {
    fn below(&mut self, bound: usize) -> usize {
        self.0 ^= self.0 << 13;
        self.0 ^= self.0 >> 7;
        self.0 ^= self.0 << 17;
        (self.0 % bound as u64) as usize
    }
}

#[test]
fn every_span_reads_as_pest_builds_it() {
    // `\n`, `\r` alone and before `\n` (pest treats the two differently),
    // tabs and spaces, and multi-byte characters, so byte offsets and columns
    // differ.
    let alphabet = ['a', ' ', '\t', '\n', '\n', '\r', 'é', '😀'];
    let mut random = XorShift(0x9E37_79B9_7F4A_7C15);
    let mut long_spans = 0;
    for _ in 0..400 {
        let length = random.below(16);
        let input: String = (0..length)
            .map(|_| alphabet[random.below(alphabet.len())])
            .collect();
        let boundaries: Vec<usize> = input
            .char_indices()
            .map(|(index, _)| index)
            .chain([input.len()])
            .collect();
        for &start in &boundaries {
            for &end in boundaries.iter().filter(|&&end| end >= start) {
                let span = pest::Span::new(&input, start, end).unwrap();
                let expected = ParseError::Syntax(pest::error::Error::new_from_span(
                    pest::error::ErrorVariant::CustomError {
                        message: "m".to_string(),
                    },
                    span,
                ));
                let actual = ParseError::from_span(span, "m".to_string());
                assert_eq!(
                    rendered(&actual),
                    rendered(&expected),
                    "input {input:?}, span {start}..{end}"
                );
                if span.lines().count() >= 3 {
                    long_spans += 1;
                }
            }
        }
    }
    // Spans over three or more lines take the copied-lines path, so the
    // comparison must have covered many of them.
    assert!(
        long_spans > 1_000,
        "only {long_spans} spans covered three or more lines"
    );
}

#[test]
fn an_error_over_twenty_thousand_lines_is_fast() {
    // About 0.2 s in a debug build on an M-series Mac, and 134 s before the
    // copied-lines path. 10 s leaves room for slow CI runners while still
    // catching the old cost many times over.
    // Built directly: a span over every line of a long input.
    let input = "item,\n".repeat(20_000);
    let started = Instant::now();
    let span = pest::Span::new(&input, 2, input.len() - 1).unwrap();
    let error = ParseError::from_span(span, "m".to_string());
    assert!(error.to_string().contains("item,"));
    assert!(
        started.elapsed() < Duration::from_secs(10),
        "took {:?}",
        started.elapsed()
    );

    // Through the parser: an invalid expression on 20,000 lines, whose error
    // covers the whole expression.
    let source = format!("<p>{{{{ [\n{}1 1] }}}}</p>", "1,\n".repeat(20_000));
    let started = Instant::now();
    let error = parse_template(&source, None, None).unwrap_err();
    assert!(
        error.to_string().contains("Failed to parse expression"),
        "{error}"
    );
    assert!(
        started.elapsed() < Duration::from_secs(10),
        "took {:?}",
        started.elapsed()
    );
}
