//! Check that the browser's HTML parser keeps a written token stream nested
//! exactly as written, reusing parse results across requests.
//!
//! [`browser_fragment_matches_nodes`] parses a whole page with html5ever and
//! compares the tree with the nodes the writer meant to create. Most of that
//! work repeats on every request: the parser's decision to keep a tag where it
//! was written, or to close, move or drop it, depends on which elements are
//! open around it, not on the text or attribute values between the tags.
//!
//! This module asks html5ever once per (open elements, token) pair and keeps
//! the answer for the thread. A page passes when every token of its stream
//! got the answer "kept in place". Why the stored answers stay valid for any
//! later page:
//!
//! - While every earlier token was kept in place (each start tag became a
//!   child of the current element, each end tag closed the current element,
//!   each text and comment became a child of the current element), everything
//!   the tree builder uses to handle the next token is decided by the list of
//!   open element names alone: the insertion mode (`in body`, `in table`,
//!   `in select`, raw text after `<textarea>`), the open `<form>`, and the
//!   list of active formatting elements, which then holds only open elements.
//!   The frameset flag, the one piece of state that also depends on earlier
//!   text, only matters for tags this check never accepts (`frameset`,
//!   `body`). So a short document holding just those open tags reaches the
//!   same state, and html5ever's answer for it is its answer for the page.
//! - Text and attribute values cannot change the answer because the caller
//!   escapes them: text has `&`, `<` and `>` written as character references,
//!   attribute values have `&` and `"` written as references, and neither
//!   holds a carriage return or NUL (the caller rejects both). The parser then
//!   decodes each back to the written value. The caller also sends a page to
//!   the full parse when a value holds a control character or a Unicode
//!   noncharacter, which the full parse's tokenizer reports as an error. What
//!   still matters is whether a text is whitespace only (table parts keep only
//!   whitespace in place) and whether it starts with a newline (the parser
//!   drops a newline right after `<pre>`, `<textarea>` or `<listing>`); both
//!   are part of the token.
//! - The one attribute value the tree builder reads for an element the
//!   caller can write is `type="hidden"` on `input`, which decides whether
//!   the input stays inside a table; it is part of the token too.
//! - Attribute names are not compared here. The caller checks them per
//!   request (only lowercase names the tokenizer takes as they are, no
//!   repeats), because a repeated or malformed name changes what the
//!   browser stores.
//!
//! Anything outside this model makes [`tokens_nest_in_browser`] return
//! `false`, and the caller then runs the full page parse, whose answer is
//! final. So this check can only skip work when it is sure; it never admits
//! a page the full parse would reject.

use std::cell::RefCell;
use std::collections::HashMap;

use crate::hydration_structure::{browser_fragment_matches_nodes, ExpectedNodeEvent};

/// One piece of written markup, without the values the parser keeps as they
/// are.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum NestingToken<'a> {
    /// A start tag. `hidden_input` is set for `<input type="hidden">`, whose
    /// place in a table depends on that value.
    Open { tag: &'a str, hidden_input: bool },
    /// The end of the most recent unclosed `Open`; a void element also gets
    /// one, with no end tag written.
    Close,
    /// A non-empty text, escaped as described in the module docs.
    Text {
        whitespace: bool,
        starts_with_newline: bool,
    },
    /// One of Vue's anchor comments (`[`, `]`, `v-if`, or empty).
    Comment(&'a str),
}

/// Elements the parser never gives children, written without an end tag.
const VOID_TAGS: [&str; 14] = [
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source",
    "track", "wbr",
];

/// Tags this check leaves to the full parse: the tokenizer reads their
/// contents as raw text, they belong to the document or another namespace,
/// or the tree builder handles them with state the open elements do not
/// determine (`template` contents, the frameset flag).
const FULL_PARSE_TAGS: [&str; 17] = [
    "script",
    "style",
    "xmp",
    "iframe",
    "noembed",
    "noframes",
    "noscript",
    "plaintext",
    "template",
    "svg",
    "math",
    "html",
    "head",
    "body",
    "frameset",
    "frame",
    "image",
];

const ANCHOR_COMMENTS: [&str; 4] = ["[", "]", "v-if", ""];

/// The parser drops a newline that directly follows these start tags.
const LEADING_NEWLINE_TAGS: [&str; 3] = ["pre", "textarea", "listing"];

/// A stored answer for a start tag in one state.
#[derive(Clone, Copy, Debug)]
enum OpenAnswer {
    /// Kept in place and left open: the state of the open elements after it.
    Nested(u32),
    /// A void element kept in place.
    KeptVoid,
    /// The parser closes, moves or drops it, or the parse failed.
    Moved,
}

/// One list of open elements, stored as its innermost tag and its parent.
struct State {
    parent: u32,
    tag: Box<str>,
    opens: HashMap<Box<str>, OpenAnswer>,
    /// Answers for whitespace-only text (index 0) and other text (index 1).
    text: [Option<bool>; 2],
    /// Answers for each anchor comment, in `ANCHOR_COMMENTS` order.
    comments: [Option<bool>; 4],
}

impl State {
    fn new(parent: u32, tag: &str) -> Self {
        State {
            parent,
            tag: tag.into(),
            opens: HashMap::new(),
            text: [None; 2],
            comments: [None; 4],
        }
    }
}

/// States by id; id 0 is the host `div` with nothing open inside it.
struct Answers {
    states: Vec<State>,
}

/// A thread that renders very varied pages would keep adding states; past
/// this many, the answers are dropped and learned again. Each thread learns
/// its own answers, so a new worker thread pays for a few small parses on
/// its first pages.
const MAX_STATES: usize = 65_536;

/// The key an `<input type="hidden">` is stored under. Tags are checked to be
/// lowercase letters and digits, so no written tag can use this key.
const HIDDEN_INPUT_KEY: &str = "input type=hidden";

thread_local! {
    // Rendering runs without the Python lock, so threads may render at once;
    // each keeps its own answers instead of sharing a lock.
    static ANSWERS: RefCell<Answers> = RefCell::new(Answers {
        states: vec![State::new(0, "")],
    });
}

impl Answers {
    /// The open tags of `state`, outermost first.
    fn open_tags(&self, mut state: u32) -> Vec<&str> {
        let mut tags = Vec::new();
        while state != 0 {
            let node = &self.states[state as usize];
            tags.push(&*node.tag);
            state = node.parent;
        }
        tags.reverse();
        tags
    }

    /// Parse the open tags of `state` around `inner` and check that the
    /// browser builds exactly those elements with `inner_events` inside.
    fn parse_inside(&self, state: u32, inner: &str, inner_events: Vec<ExpectedNodeEvent>) -> bool {
        let tags = self.open_tags(state);
        let mut html = String::new();
        let mut events = Vec::with_capacity(tags.len() * 2 + inner_events.len());
        for tag in &tags {
            html.push('<');
            html.push_str(tag);
            html.push('>');
            events.push(ExpectedNodeEvent::Open {
                tag: (*tag).to_owned(),
                attributes: Vec::new(),
            });
        }
        html.push_str(inner);
        events.extend(inner_events);
        for tag in tags.iter().rev() {
            html.push_str("</");
            html.push_str(tag);
            html.push('>');
            events.push(ExpectedNodeEvent::Close {
                tag: (*tag).to_owned(),
            });
        }
        browser_fragment_matches_nodes(&html, "div", &events)
    }

    fn open(&mut self, state: u32, tag: &str, hidden_input: bool) -> OpenAnswer {
        let key = if hidden_input { HIDDEN_INPUT_KEY } else { tag };
        if let Some(answer) = self.states[state as usize].opens.get(key) {
            return *answer;
        }
        let void = VOID_TAGS.contains(&tag);
        let attributes = if hidden_input {
            vec![("type".to_owned(), Some("hidden".to_owned()))]
        } else {
            Vec::new()
        };
        let mut inner = format!("<{tag}");
        if hidden_input {
            inner.push_str(" type=\"hidden\"");
        }
        inner.push('>');
        if !void {
            inner.push_str("</");
            inner.push_str(tag);
            inner.push('>');
        }
        let events = vec![
            ExpectedNodeEvent::Open {
                tag: tag.to_owned(),
                attributes,
            },
            ExpectedNodeEvent::Close {
                tag: tag.to_owned(),
            },
        ];
        // The probe writes the end tag right after the start tag. In the page
        // the end tag comes after the element's children, and those children
        // were each kept in place, so the parser is back in this same state
        // when it reads it. An element the parser closes at once (`keygen`,
        // a `form` inside a table) passes here, but then every child's own
        // probe fails, because the child is not placed inside it.
        let answer = if !self.parse_inside(state, &inner, events) {
            OpenAnswer::Moved
        } else if void {
            OpenAnswer::KeptVoid
        } else {
            let id = u32::try_from(self.states.len()).expect("state count is capped");
            self.states.push(State::new(state, tag));
            OpenAnswer::Nested(id)
        };
        self.states[state as usize].opens.insert(key.into(), answer);
        answer
    }

    fn text(&mut self, state: u32, whitespace: bool) -> bool {
        let index = usize::from(!whitespace);
        if let Some(answer) = self.states[state as usize].text[index] {
            return answer;
        }
        // A space and a letter stand for every whitespace-only and every
        // other escaped text: the tree builder only tells those two apart.
        let answer = self.parse_inside(state, if whitespace { " " } else { "x" }, Vec::new());
        self.states[state as usize].text[index] = Some(answer);
        answer
    }

    fn comment(&mut self, state: u32, index: usize) -> bool {
        if let Some(answer) = self.states[state as usize].comments[index] {
            return answer;
        }
        let data = ANCHOR_COMMENTS[index];
        let answer = self.parse_inside(
            state,
            &format!("<!--{data}-->"),
            vec![ExpectedNodeEvent::Comment {
                data: data.to_owned(),
            }],
        );
        self.states[state as usize].comments[index] = Some(answer);
        answer
    }
}

fn is_checked_tag(tag: &str) -> bool {
    tag.as_bytes().first().is_some_and(u8::is_ascii_lowercase)
        && tag
            .bytes()
            .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit())
        && !FULL_PARSE_TAGS.contains(&tag)
}

/// Whether the browser's parser, in the host's `div` context, keeps every
/// token of `tokens` where it was written, so the tree it builds is exactly
/// the nesting of the tokens.
///
/// `false` means "not shown here", not "rejected": the caller then runs the
/// full parse ([`browser_fragment_matches_nodes`]), which decides. The
/// caller is responsible for the escaping and attribute rules listed in the
/// module docs.
pub fn tokens_nest_in_browser(tokens: &[NestingToken<'_>]) -> bool {
    ANSWERS.with(|answers| {
        let mut answers = answers.borrow_mut();
        if answers.states.len() > MAX_STATES {
            answers.states.truncate(1);
            answers.states[0] = State::new(0, "");
        }
        walk(&mut answers, tokens)
    })
}

fn walk(answers: &mut Answers, tokens: &[NestingToken<'_>]) -> bool {
    if tokens.is_empty() {
        return false;
    }
    let mut open: Vec<u32> = vec![0];
    // A void element's `Close` must follow its `Open` directly.
    let mut void_open = false;
    // Whether the previous token opened a tag that drops a following newline.
    let mut drops_newline = false;
    for token in tokens {
        let state = *open.last().expect("the host state stays open");
        if void_open && *token != NestingToken::Close {
            return false;
        }
        let after_newline_tag = std::mem::take(&mut drops_newline);
        match *token {
            NestingToken::Open { tag, hidden_input } => {
                if !is_checked_tag(tag) || (hidden_input && tag != "input") {
                    return false;
                }
                match answers.open(state, tag, hidden_input) {
                    OpenAnswer::Nested(next) => {
                        open.push(next);
                        drops_newline = LEADING_NEWLINE_TAGS.contains(&tag);
                    }
                    OpenAnswer::KeptVoid => void_open = true,
                    OpenAnswer::Moved => return false,
                }
            }
            NestingToken::Close => {
                if void_open {
                    void_open = false;
                } else if open.len() > 1 {
                    open.pop();
                } else {
                    return false;
                }
            }
            NestingToken::Text {
                whitespace,
                starts_with_newline,
            } => {
                // The stored answer comes from a probe text without a leading
                // newline, so a text the parser would shorten is not covered.
                if (after_newline_tag && starts_with_newline) || !answers.text(state, whitespace) {
                    return false;
                }
            }
            NestingToken::Comment(data) => {
                let Some(index) = ANCHOR_COMMENTS.iter().position(|known| *known == data) else {
                    return false;
                };
                if !answers.comment(state, index) {
                    return false;
                }
            }
        }
    }
    open.len() == 1 && !void_open
}

#[cfg(test)]
mod tests {
    use super::{tokens_nest_in_browser, NestingToken};
    use crate::hydration_structure::{browser_fragment_matches_nodes, ExpectedNodeEvent};

    const VOID: [&str; 3] = ["br", "input", "img"];

    fn open(tag: &str) -> NestingToken<'_> {
        NestingToken::Open {
            tag,
            hidden_input: false,
        }
    }

    #[test]
    fn nested_elements_text_and_comments_pass() {
        let tokens = [
            open("main"),
            NestingToken::Comment("["),
            open("p"),
            NestingToken::Text {
                whitespace: false,
                starts_with_newline: false,
            },
            NestingToken::Close,
            open("br"),
            NestingToken::Close,
            NestingToken::Comment("]"),
            NestingToken::Close,
        ];
        assert!(tokens_nest_in_browser(&tokens));
    }

    #[test]
    fn parser_repairs_and_unbalanced_streams_fail() {
        // A block element inside `<p>` closes the paragraph.
        assert!(!tokens_nest_in_browser(&[
            open("p"),
            open("div"),
            NestingToken::Close,
            NestingToken::Close,
        ]));
        // A row directly inside a table gets an implied `tbody`.
        assert!(!tokens_nest_in_browser(&[
            open("table"),
            open("tr"),
            NestingToken::Close,
            NestingToken::Close,
        ]));
        // Letters inside a table are moved out of it; whitespace stays.
        let table_text = |whitespace| {
            [
                open("table"),
                NestingToken::Text {
                    whitespace,
                    starts_with_newline: false,
                },
                NestingToken::Close,
            ]
        };
        assert!(!tokens_nest_in_browser(&table_text(false)));
        assert!(tokens_nest_in_browser(&table_text(true)));
        // An element inside `<textarea>` is read as text.
        assert!(!tokens_nest_in_browser(&[
            open("textarea"),
            open("b"),
            NestingToken::Close,
            NestingToken::Close,
        ]));
        // A comment inside `<textarea>` is text as well.
        assert!(!tokens_nest_in_browser(&[
            open("textarea"),
            NestingToken::Comment("["),
            NestingToken::Close,
        ]));
        // Text directly in the host is never expected.
        assert!(!tokens_nest_in_browser(&[NestingToken::Text {
            whitespace: true,
            starts_with_newline: false,
        }]));
        assert!(!tokens_nest_in_browser(&[open("div")]));
        assert!(!tokens_nest_in_browser(&[NestingToken::Close]));
        assert!(!tokens_nest_in_browser(&[]));
        // Other comments and raw-text tags are left to the full parse.
        assert!(!tokens_nest_in_browser(&[NestingToken::Comment("x")]));
        assert!(!tokens_nest_in_browser(&[
            open("script"),
            NestingToken::Close
        ]));
        // A void element's close must follow it directly.
        assert!(!tokens_nest_in_browser(&[
            open("br"),
            NestingToken::Comment("["),
            NestingToken::Close,
        ]));
    }

    #[test]
    fn hidden_inputs_are_answered_separately() {
        let in_table = |hidden_input| {
            [
                open("table"),
                NestingToken::Open {
                    tag: "input",
                    hidden_input,
                },
                NestingToken::Close,
                NestingToken::Close,
            ]
        };
        // The parser keeps a hidden input in the table and moves any other.
        assert!(tokens_nest_in_browser(&in_table(true)));
        assert!(!tokens_nest_in_browser(&in_table(false)));
    }

    /// A small deterministic generator (xorshift), so the test needs no
    /// extra dependency and fails the same way on every run.
    struct Rng(u64);

    impl Rng {
        fn next(&mut self, below: usize) -> usize {
            self.0 ^= self.0 << 13;
            self.0 ^= self.0 >> 7;
            self.0 ^= self.0 << 17;
            usize::try_from(self.0 % below as u64).expect("small bound")
        }
    }

    const TAGS: [&str; 39] = [
        "div", "p", "span", "a", "b", "b", "i", "table", "tbody", "thead", "tr", "td", "th",
        "caption", "colgroup", "col", "ul", "ol", "li", "dl", "dt", "dd", "select", "option",
        "optgroup", "textarea", "pre", "listing", "title", "form", "button", "h1", "h2", "nobr",
        "br", "input", "img", "keygen", "bgsound",
    ];

    /// Write a random tree as HTML with its token stream and expected nodes.
    fn tree<'a>(
        rng: &mut Rng,
        depth: usize,
        html: &mut String,
        tokens: &mut Vec<NestingToken<'a>>,
        events: &mut Vec<ExpectedNodeEvent>,
    ) {
        for _ in 0..rng.next(4) {
            match rng.next(8) {
                0 => {
                    // Texts with and without a leading newline, which the
                    // parser drops right after `pre`, `textarea` and
                    // `listing`.
                    let (text, whitespace) = [
                        (" \n", true),
                        ("\n ", true),
                        ("a &amp; b", false),
                        ("\nx", false),
                    ][rng.next(4)];
                    html.push_str(text);
                    tokens.push(NestingToken::Text {
                        whitespace,
                        starts_with_newline: text.starts_with('\n'),
                    });
                }
                1 => {
                    let data = ["[", "]", "v-if", ""][rng.next(4)];
                    html.push_str(&format!("<!--{data}-->"));
                    tokens.push(NestingToken::Comment(data));
                    events.push(ExpectedNodeEvent::Comment {
                        data: data.to_owned(),
                    });
                }
                _ => {
                    let tag = TAGS[rng.next(TAGS.len())];
                    let hidden_input = tag == "input" && rng.next(2) == 0;
                    let mut attributes = Vec::new();
                    html.push('<');
                    html.push_str(tag);
                    if hidden_input {
                        html.push_str(" type=\"hidden\"");
                        attributes.push(("type".to_owned(), Some("hidden".to_owned())));
                    } else if rng.next(3) == 0 {
                        // Attribute values differ between otherwise equal
                        // elements (the parser compares them when it limits
                        // repeated formatting elements) but not in the token.
                        let value = format!("c{}", rng.next(3));
                        html.push_str(&format!(" class=\"{value}\""));
                        attributes.push(("class".to_owned(), Some(value)));
                    }
                    html.push('>');
                    tokens.push(NestingToken::Open { tag, hidden_input });
                    events.push(ExpectedNodeEvent::Open {
                        tag: tag.to_owned(),
                        attributes,
                    });
                    if !VOID.contains(&tag) {
                        if depth < 6 {
                            tree(rng, depth + 1, html, tokens, events);
                        }
                        html.push_str("</");
                        html.push_str(tag);
                        html.push('>');
                    }
                    tokens.push(NestingToken::Close);
                    events.push(ExpectedNodeEvent::Close {
                        tag: tag.to_owned(),
                    });
                }
            }
        }
    }

    /// The stored answers must never admit a page the full parse rejects.
    /// For the tags and texts generated here they should also admit every
    /// page the full parse accepts.
    #[test]
    fn stored_answers_agree_with_the_full_parse_on_random_trees() {
        let mut rng = Rng(0x9e37_79b9_7f4a_7c15);
        let (mut admitted, mut rejected) = (0, 0);
        for _ in 0..80_000 {
            let mut html = String::new();
            let mut tokens = Vec::new();
            let mut events = Vec::new();
            tree(&mut rng, 0, &mut html, &mut tokens, &mut events);
            let full = browser_fragment_matches_nodes(&html, "div", &events);
            let nested = tokens_nest_in_browser(&tokens);
            assert!(
                !nested || full,
                "admitted a page the full parse rejects: {html}"
            );
            assert!(
                nested || !full,
                "missed a page the full parse accepts: {html}"
            );
            if full {
                admitted += 1;
            } else {
                rejected += 1;
            }
        }
        // Both outcomes must be well represented for the comparison to mean
        // anything.
        assert!(
            admitted > 2_000 && rejected > 2_000,
            "{admitted} / {rejected}"
        );
    }
}
