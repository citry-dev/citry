//! The size limits every HTML parse in this crate applies before html5ever
//! builds a tree.
//!
//! Two kinds of input made html5ever's work grow with the square of their
//! size:
//!
//! - html5ever's own tokenizer compares each attribute name of a tag with
//!   every earlier one: in a release build one tag with 10,000 attributes
//!   took about 100 ms, and a debug build is many times slower. So every
//!   parse here reads with html5gum, which drops a repeated name with a set
//!   (`output_scanner`). The limit remains because no real element has
//!   thousands of attributes.
//! - The tree builder copies the attributes of every repeated `<html>` or
//!   `<body>` start tag onto the first one, and RcDom rebuilds a set of the
//!   first one's attributes each time. 10,000 `<body>` tags that each add
//!   64 new attributes (5.6 MB) took about two minutes in a release build.
//!
//! So a parse stops building the tree once one tag has more than
//! [`MAX_ATTRIBUTES_PER_TAG`] attributes, or once the page has more than
//! [`MAX_DOCUMENT_TAGS`] start tags of one of `html`, `head` and `body`, and
//! the caller refuses the page. Real pages stay far below both limits.
//!
//! The counts come from html5gum while the tree builder tells it which state
//! to read the next part in, in the same parse that builds the tree, with the
//! same context element. So text inside `<script>`, `<title>` or a comment is
//! not counted as a tag, exactly as the browser would not read it as one, and
//! a tag the tree builder reads is always counted. html5gum reads attributes
//! in a loop (see `tokenizer`), so counting costs no more than the parse.

use std::cell::Cell;
use std::error::Error;
use std::fmt;

/// The most attributes one tag may have. Real elements have a few dozen
/// at most. The limit also bounds what each repeated `<html>` or `<body>`
/// tag can copy (see [`MAX_DOCUMENT_TAGS`]).
pub const MAX_ATTRIBUTES_PER_TAG: usize = 1_024;

/// The most start tags a page may hold of each of `html`, `head` and `body`.
/// `<head>` costs nothing when repeated, but is counted too, so one rule
/// covers all three document tags.
///
/// A page has one of each. Some pages repeat them: HTML pasted from
/// another page, or a layout that writes a whole document into a part of a
/// page. Each repeated `<html>` or `<body>` copies up to
/// [`MAX_ATTRIBUTES_PER_TAG`] attributes onto the first one, and the copy
/// reads every attribute the first one has gathered, so the work grows with
/// the square of this number. At 16, the worst page makes about 140,000
/// attribute copies for `<body>` and as many for `<html>`, a few
/// milliseconds at most.
pub const MAX_DOCUMENT_TAGS: usize = 16;

/// Why a parse stopped reading a page.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum HtmlTooLarge {
    /// One tag has more than [`MAX_ATTRIBUTES_PER_TAG`] attributes.
    Attributes,
    /// The page has more than [`MAX_DOCUMENT_TAGS`] start tags with this
    /// name (`html`, `head` or `body`).
    DocumentTags(&'static str),
}

impl fmt::Display for HtmlTooLarge {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Attributes => write!(
                f,
                "HTML has a tag with more than {MAX_ATTRIBUTES_PER_TAG} attributes; Citry reads at \
                 most {MAX_ATTRIBUTES_PER_TAG} on one tag"
            ),
            Self::DocumentTags(name) => write!(
                f,
                "HTML has more than {MAX_DOCUMENT_TAGS} <{name}> start tags; Citry reads at most \
                 {MAX_DOCUMENT_TAGS} of each"
            ),
        }
    }
}

impl Error for HtmlTooLarge {}

/// Counts what one tokenizer run has read so far, against the limits.
///
/// The scan callback reports each start tag and attribute here, and stops
/// handing tokens to the tree builder as soon as [`HtmlLimits::exceeded`]
/// returns something. The counters are cells so the callback and the code
/// that started the run can share one value.
#[derive(Default)]
pub(crate) struct HtmlLimits {
    attributes: Cell<usize>,
    html: Cell<usize>,
    head: Cell<usize>,
    body: Cell<usize>,
    exceeded: Cell<Option<HtmlTooLarge>>,
}

impl HtmlLimits {
    /// Record a start tag named `name`, which html5gum gives in lower case.
    pub(crate) fn start_tag(&self, name: &[u8]) {
        // The attribute count belongs to one tag, so it starts again here.
        self.attributes.set(0);
        let (counter, name) = match name {
            b"html" => (&self.html, "html"),
            b"head" => (&self.head, "head"),
            b"body" => (&self.body, "body"),
            _ => return,
        };
        counter.set(counter.get() + 1);
        if counter.get() > MAX_DOCUMENT_TAGS {
            self.exceed(HtmlTooLarge::DocumentTags(name));
        }
    }

    /// Record one more attribute on the current start tag. The scan drops
    /// an end tag's attributes before the tree builder sees them, as the
    /// browser does, so only a start tag's attributes are counted.
    pub(crate) fn attribute(&self) {
        self.attributes.set(self.attributes.get() + 1);
        if self.attributes.get() > MAX_ATTRIBUTES_PER_TAG {
            self.exceed(HtmlTooLarge::Attributes);
        }
    }

    /// The first limit the run went over, if any.
    pub(crate) fn exceeded(&self) -> Option<HtmlTooLarge> {
        self.exceeded.get()
    }

    /// The result of the whole run: `Ok` when it stayed within every limit.
    pub(crate) fn result(&self) -> Result<(), HtmlTooLarge> {
        self.exceeded().map_or(Ok(()), Err)
    }

    fn exceed(&self, reason: HtmlTooLarge) {
        // The first limit reached is the one the message names; the scan
        // stops building the tree there, so later counts mean nothing.
        if self.exceeded.get().is_none() {
            self.exceeded.set(Some(reason));
        }
    }
}

#[cfg(test)]
mod tests {
    use super::{HtmlLimits, HtmlTooLarge, MAX_ATTRIBUTES_PER_TAG, MAX_DOCUMENT_TAGS};

    #[test]
    fn attributes_count_per_tag() {
        let limits = HtmlLimits::default();
        for _ in 0..3 {
            limits.start_tag(b"p");
            for _ in 0..MAX_ATTRIBUTES_PER_TAG {
                limits.attribute();
            }
        }
        assert_eq!(limits.result(), Ok(()));
        limits.attribute();
        assert_eq!(limits.result(), Err(HtmlTooLarge::Attributes));
    }

    #[test]
    fn each_document_tag_name_counts_on_its_own() {
        let limits = HtmlLimits::default();
        for name in [&b"html"[..], b"head", b"body"] {
            for _ in 0..MAX_DOCUMENT_TAGS {
                limits.start_tag(name);
            }
        }
        assert_eq!(limits.result(), Ok(()));
        limits.start_tag(b"head");
        assert_eq!(limits.result(), Err(HtmlTooLarge::DocumentTags("head")));
        // The first limit reached stays the reason.
        limits.start_tag(b"body");
        assert_eq!(limits.exceeded(), Some(HtmlTooLarge::DocumentTags("head")));
    }

    #[test]
    fn messages_name_the_limit() {
        assert_eq!(
            HtmlTooLarge::Attributes.to_string(),
            "HTML has a tag with more than 1024 attributes; Citry reads at most 1024 on one tag"
        );
        assert_eq!(
            HtmlTooLarge::DocumentTags("body").to_string(),
            "HTML has more than 16 <body> start tags; Citry reads at most 16 of each"
        );
    }
}
