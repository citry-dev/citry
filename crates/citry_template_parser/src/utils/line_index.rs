//! Find the line and column of a byte offset without scanning from the start.
//!
//! Every token the parser creates records its line and column. Pest's
//! `pest::Position::line_col` walks every character from the start of the
//! source, so asking it once per token would make parse time grow with the
//! square of the template's length. This index is built once from the whole
//! template string the caller passed, shared with the parses of nested
//! template attribute values, and answers each lookup with a binary search.
//!
//! The answers match `pest::Position::line_col` exactly. Lines are 1-based
//! and end after each `\n` (so `\r\n` ends a line, and a lone `\r` is an
//! ordinary character). Columns are 1-based and count characters (Rust
//! `char`s, one per Unicode code point).

/// How far apart, in bytes, the character-count checkpoints sit. On a line
/// with non-ASCII text, a lookup makes two character counts, and each covers
/// at most this many bytes plus one character.
const CHECKPOINT_SPACING: usize = 256;

/// Line starts and character counts for one source string.
#[derive(Debug)]
pub(crate) struct LineIndex {
    /// Byte offset where each line starts. The first line starts at 0.
    line_starts: Vec<usize>,
    /// Whether each line holds only ASCII. On such a line a column is just
    /// the byte distance from the line start.
    line_is_ascii: Vec<bool>,
    /// `(byte offset, characters before it)` at a character boundary about
    /// every `CHECKPOINT_SPACING` bytes, so counting characters never has to
    /// start from the beginning of a long line.
    checkpoints: Vec<(usize, usize)>,
}

impl LineIndex {
    /// Index `source`, reading it once.
    pub(crate) fn new(source: &str) -> Self {
        Self::with_checkpoint_spacing(source, CHECKPOINT_SPACING)
    }

    /// Index `source` with checkpoints `spacing` bytes apart. Tests use small
    /// spacings so that short strings cross many checkpoints.
    fn with_checkpoint_spacing(source: &str, spacing: usize) -> Self {
        let mut line_starts = vec![0];
        let mut line_is_ascii = vec![true];
        let mut checkpoints = vec![(0, 0)];
        let mut next_checkpoint = spacing;
        for (characters_before, (offset, character)) in source.char_indices().enumerate() {
            if offset >= next_checkpoint {
                checkpoints.push((offset, characters_before));
                next_checkpoint = offset + spacing;
            }
            if !character.is_ascii() {
                *line_is_ascii.last_mut().unwrap() = false;
            }
            // The newline belongs to the line it ends, as in Pest.
            if character == '\n' {
                line_starts.push(offset + 1);
                line_is_ascii.push(true);
            }
        }
        LineIndex {
            line_starts,
            line_is_ascii,
            checkpoints,
        }
    }

    /// The 1-based line and column of `offset` in `source`.
    ///
    /// `source` must be the string the index was built from, and `offset`
    /// must be a character boundary in it (the parser checks this before it
    /// asks).
    pub(crate) fn line_col(&self, source: &str, offset: usize) -> (usize, usize) {
        // The last line that starts at or before the offset holds it.
        let line = self.line_starts.partition_point(|&start| start <= offset) - 1;
        let line_start = self.line_starts[line];
        let column = if self.line_is_ascii[line] {
            offset - line_start
        } else {
            self.characters_before(source, offset) - self.characters_before(source, line_start)
        };
        (line + 1, column + 1)
    }

    /// How many characters come before byte `offset`.
    fn characters_before(&self, source: &str, offset: usize) -> usize {
        let checkpoint = self
            .checkpoints
            .partition_point(|&(start, _)| start <= offset)
            - 1;
        let (start, characters) = self.checkpoints[checkpoint];
        characters + source[start..offset].chars().count()
    }
}

#[cfg(test)]
mod tests {
    use super::LineIndex;

    /// A small random-number generator, so the test needs no extra crate and
    /// every run checks the same strings.
    struct XorShift(u64);

    impl XorShift {
        fn next(&mut self) -> u64 {
            self.0 ^= self.0 << 13;
            self.0 ^= self.0 >> 7;
            self.0 ^= self.0 << 17;
            self.0
        }
    }

    /// Every offset of every string must get the same answer as Pest, with
    /// the real checkpoint spacing and with spacings small enough that every
    /// string crosses several checkpoints.
    fn assert_matches_pest(source: &str) {
        for spacing in [1, 2, 3, 7, super::CHECKPOINT_SPACING] {
            let index = LineIndex::with_checkpoint_spacing(source, spacing);
            for offset in (0..=source.len()).filter(|&offset| source.is_char_boundary(offset)) {
                let expected = pest::Position::new(source, offset).unwrap().line_col();
                assert_eq!(
                    index.line_col(source, offset),
                    expected,
                    "offset {offset}, spacing {spacing}, in {source:?}"
                );
            }
        }
    }

    #[test]
    fn matches_pest_at_every_offset_of_random_strings() {
        // Line breaks of every kind, ASCII, and characters of two, three and
        // four bytes, so lines mix ASCII and non-ASCII text. U+2028 and U+0085
        // end a line in some editors, but Pest treats them as ordinary
        // characters, and so must the index.
        let pieces = [
            "a", "b", " ", "<", "\n", "\r\n", "\r", "é", "€", "😀", "\n\n", "\r\r\n", "\u{2028}",
            "\u{85}",
        ];
        let mut random = XorShift(0x2545_f491_4f6c_dd1d);
        for _ in 0..300 {
            let length = (random.next() % 80) as usize;
            let source: String = (0..length)
                .map(|_| pieces[(random.next() % pieces.len() as u64) as usize])
                .collect();
            assert_matches_pest(&source);
        }
    }

    #[test]
    fn matches_pest_across_checkpoints_on_long_lines() {
        // Long lines put several checkpoints inside one line, and the
        // multibyte characters move them off the 256-byte marks.
        assert_matches_pest(&"x".repeat(1_000));
        assert_matches_pest(&"é".repeat(700));
        assert_matches_pest(&format!(
            "{}\n{}\r\n{}",
            "a€".repeat(300),
            "😀b".repeat(200),
            "c".repeat(600)
        ));
    }

    #[test]
    fn matches_pest_on_edge_cases() {
        for source in ["", "\n", "\r", "\r\n", "\n\r", "é", "a\rb\nc", "\r\n\r\n"] {
            assert_matches_pest(source);
        }
    }
}
