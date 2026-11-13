//! The size limits every HTML parse in this crate applies before html5ever
//! builds a tree.
//!
//! Four kinds of input made html5ever's work grow with the square of their
//! size, or grow the tree far past the size of the input:
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
//! - The tree builder keeps a stack of the elements that are open, and
//!   looks down it for many tags (to find a `<p>` to close, or the element
//!   an end tag closes). Each tag therefore costs as much as the nesting
//!   above it, and a page that nests tens of thousands of elements deep
//!   costs the square of its length: 40,000 `<div>` tags (200 KB) took
//!   over 20 seconds to read in a debug build.
//! - When formatting elements (`<a>`, `<b>`, `<i>` and the like) are closed
//!   out of order, the tree builder keeps them on a list. Each time text or
//!   a tag needs a place to go, it opens a new copy of every element still
//!   on the list. An end tag such as `</div>` closes the copies without
//!   taking them off the list, so a short input such as `<div>x</div>`
//!   opens every copy again, and the tree grows by one element, with a copy
//!   of its attributes, for each. With 450 elements waiting on the list,
//!   130 KB of input made 1.1 GB of tree in a debug build.
//!
//! So a parse stops building the tree once one tag has more than
//! [`MAX_ATTRIBUTES_PER_TAG`] attributes, once the page has more than
//! [`MAX_DOCUMENT_TAGS`] start tags of one of `html`, `head` and `body`, once
//! the tree builder holds more than [`MAX_OPEN_ELEMENTS`] elements, or once
//! it has reopened more than [`MAX_REOPENED_FORMATTING_ELEMENTS`] formatting
//! elements and attributes, and the caller refuses the page. Real pages stay
//! far below all four limits, except that one template may nest up to 512
//! tags, which a page cannot hold (see [`MAX_OPEN_ELEMENTS`]).
//!
//! The tag counts come from html5gum while the tree builder tells it which
//! state to read the next part in, in the same parse that builds the tree,
//! with the same context element. So text inside `<script>`, `<title>` or a
//! comment is not counted as a tag, exactly as the browser would not read it
//! as one, and a tag the tree builder reads is always counted. html5gum reads
//! attributes in a loop (see `tokenizer`), so counting costs no more than the
//! parse. The two tree limits are checked after each token the tree builder
//! has processed, by asking the tree builder what it holds
//! ([`HtmlLimits::after_token`]). That takes time in proportion to the
//! elements it holds: a typical page costs about 2% more to read in a
//! release build. A page whose open elements and open formatting elements
//! together come to more than about 512 (256 open `<b>` elements, or 400
//! `<div>` and 60 `<b>`) costs each token ten to seventeen times what the
//! tree builder spends on it.

use std::cell::{Cell, RefCell};
use std::collections::HashSet;
use std::error::Error;
use std::fmt;
use std::hash::{BuildHasherDefault, Hasher};
use std::rc::Rc;

use html5ever::tree_builder::Tracer;
use markup5ever_rcdom::Handle;

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

/// The most elements the tree builder may hold at once: those in its stack
/// of open elements, plus the formatting elements on its list that it
/// would reopen, each counted once. It also keeps a pointer to the `<head>`,
/// to a `<form>` and, when it reads a fragment, to the context element, and
/// those count too. A page scan therefore holds `<html>`, `<body>` and the
/// `<head>` besides the page's own elements, and fits 509 nested ones.
///
/// The number matches `MAX_TAG_NESTING` in the template parser, which
/// caps how deep one template nests its tags. Chrome's HTML parser also
/// stops nesting at about 512 elements. A real page nests a few dozen
/// levels, and the Vue server renderer already leaves everything nested
/// deeper than 400 elements to the browser (`MAX_ELEMENT_DEPTH`). The root
/// `<html>` and `<body>` count too, so a page whose one template nests 512
/// elements is over the limit.
///
/// Without a limit, the tree builder looks down the whole stack for most
/// tags: `<div>` written 40,000 times (200 KB) took 23 seconds to read in
/// a debug build, and the time grows with the square of the count.
///
/// The count is of open elements, not start tags, so a page may write
/// as many `<li>` or `<p>` tags as it likes while their end tags are left
/// out: the tree builder closes each one when the next arrives.
pub const MAX_OPEN_ELEMENTS: usize = 512;

/// The most formatting elements (`a`, `b`, `big`, `code`, `em`, `font`, `i`,
/// `nobr`, `s`, `small`, `strike`, `strong`, `tt` and `u`) the tree builder
/// may reopen or copy while
/// reading one page, counting each element as one and each of its
/// attributes as one more, because a copy repeats the attributes.
///
/// A formatting element that is closed out of order stays on the tree
/// builder's list, and the next text or tag opens a new copy of it (the
/// HTML standard calls this "reconstructing the active formatting
/// elements"). In `<p><b>one</p><p>two</p>`, the second paragraph gets its
/// own `<b>` around "two". Each copy is a new element in the tree, and a
/// copy of every element waiting on the list is made again after each
/// `<div>x</div>`, so the tree grows with the input times the length of
/// the list: with 450 elements waiting, 130 KB of input made about 1.1 GB
/// of tree in a debug build. Each attribute counts because a copy repeats
/// it: 20 waiting elements with 1,024 attributes each make about 1 GB of
/// tree from 250 KB of input.
///
/// A real page reopens a few elements for each tag it misnests. The
/// number is far above that: a page that leaves a `<b>` open in every one
/// of its paragraphs (`<p><b>one</p>`, 13 bytes, 3 copies each once the
/// list is full) reaches it only after about 1 MB, and one that also
/// leaves an `<i>` open (6 copies each) after about 670 KB. Stopping at
/// the number costs up to about 60 MB and 0.2 seconds in a debug build,
/// whether the elements have attributes or not.
pub const MAX_REOPENED_FORMATTING_ELEMENTS: usize = 250_000;

/// How much work the output check may spend reading one page every way
/// browsers can read it, for each byte of the page, on top of
/// [`CHECK_WORK_FLOOR`].
///
/// The check reads some pages more than once (one reading for each way a
/// browser can build the page, see `for_each_reading` in
/// `output_policy.rs`), up to 42 times for a page that holds every kind of
/// markup that calls for another reading. After each token it counts what
/// html5ever holds, and html5ever's own work for the token grows with that
/// count too. The work is that count, added up over every token of every
/// reading, nested documents included: one unit for each handle html5ever
/// reports. html5ever reports a handle (a reference to one node: the
/// document or an element) each time it holds that node. An open formatting
/// element is held in the stack of open elements and on the list of
/// formatting elements, so it counts twice.
///
/// Measured on 1 MB pages in a release build: an ordinary page holds a
/// few dozen elements at a time, needs one or two readings, and spends 1
/// to 3 units for each byte. A page that nests 60 `<div>` elements deep
/// and holds a `<select>`, a `<noscript>` and a `<table>` inside a `<p>`
/// spends about 140. One reading of the costliest page, which holds about
/// 500 elements open across all of it, spends about 250. With a `<table>`
/// inside a `<p>` it needs two readings and spends about 490, which
/// passes. The same page with the markup that
/// calls for all 42 readings would spend about 42 times what one reading
/// does. Each unit costs 4 to 5 nanoseconds there, so the slowest page
/// measured is refused after about 2.6 seconds per megabyte.
pub const MAX_CHECK_WORK_PER_BYTE: usize = 512;

/// The work the output check may spend on any page, however short (see
/// [`MAX_CHECK_WORK_PER_BYTE`]), so a short page can take every reading it
/// needs. At the slowest rate measured it takes about 0.09 seconds in a
/// release build.
pub const CHECK_WORK_FLOOR: usize = 16 * 1024 * 1024;

/// Why a parse stopped reading a page.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum HtmlTooLarge {
    /// One tag has more than [`MAX_ATTRIBUTES_PER_TAG`] attributes.
    Attributes,
    /// The page has more than [`MAX_DOCUMENT_TAGS`] start tags with this
    /// name (`html`, `head` or `body`).
    DocumentTags(&'static str),
    /// The tree builder holds more than [`MAX_OPEN_ELEMENTS`] elements.
    OpenElements,
    /// The tree builder has reopened or copied formatting elements, with
    /// their attributes, more than [`MAX_REOPENED_FORMATTING_ELEMENTS`]
    /// times.
    ReopenedFormatting,
    /// Reading the page every way browsers can read it would take more
    /// work than [`MAX_CHECK_WORK_PER_BYTE`] for each byte plus
    /// [`CHECK_WORK_FLOOR`] allows. Only the output check counts this.
    CheckWork,
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
            // The Python wrappers choose a hint for each limit by the start of
            // its message (`citry/_vue/opaque_html.py`), so each message
            // starts with words no other message starts with.
            Self::OpenElements => write!(
                f,
                "HTML keeps more than {MAX_OPEN_ELEMENTS} elements open at once; Citry reads at \
                 most {MAX_OPEN_ELEMENTS}"
            ),
            Self::ReopenedFormatting => write!(
                f,
                "HTML leaves formatting tags such as <b> and <i> open or misnested so often that \
                 the parser would copy more than {MAX_REOPENED_FORMATTING_ELEMENTS} elements and \
                 attributes; Citry reads at most {MAX_REOPENED_FORMATTING_ELEMENTS}"
            ),
            Self::CheckWork => write!(
                f,
                "HTML would take too long to check, because it keeps many elements open across \
                 much of the page and also holds markup that browsers read in several ways, so \
                 Citry reads it several times; close elements sooner or nest them less deeply"
            ),
        }
    }
}

impl Error for HtmlTooLarge {}

/// Whether `name` is one of the formatting elements the tree builder keeps
/// on its list to reopen: `a`, `b`, `big`, `code`, `em`, `font`, `i`,
/// `nobr`, `s`, `small`, `strike`, `strong`, `tt` and `u`.
pub(crate) fn is_formatting_element(name: &[u8]) -> bool {
    matches!(
        name,
        b"a" | b"b"
            | b"big"
            | b"code"
            | b"em"
            | b"font"
            | b"i"
            | b"nobr"
            | b"s"
            | b"small"
            | b"strike"
            | b"strong"
            | b"tt"
            | b"u"
    )
}

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
    // What the formatting start tags handed to the tree builder account
    // for: one for each tag and one for each attribute on it. The tree
    // builder makes at most this much for them, so what it makes beyond it
    // is the copies it opened by itself (see `after_token`).
    formatting_fed: Cell<usize>,
    // The values of `formatting_fed` and of what the tree builder had made
    // when `after_token` last ran, and the copies counted so far. Each
    // token is compared with only the tags handed over with it.
    fed_seen: Cell<usize>,
    made_seen: Cell<usize>,
    reopened: Cell<usize>,
    // Whether the start tag being read is a formatting element, so its
    // attributes add to `formatting_fed`.
    in_formatting_tag: Cell<bool>,
    // The addresses of the elements `after_token` has counted so far,
    // kept between calls so counting does not allocate each time.
    seen: RefCell<HashSet<usize, BuildHasherDefault<AddressHasher>>>,
    exceeded: Cell<Option<HtmlTooLarge>>,
    // The work the output check may still spend on its readings of one
    // page, shared by all of them (see `MAX_CHECK_WORK_PER_BYTE`), or
    // `None` for every other parse.
    work_left: Option<Rc<Cell<usize>>>,
}

impl HtmlLimits {
    /// Limits that also spend from `work_left` (see
    /// [`MAX_CHECK_WORK_PER_BYTE`]).
    pub(crate) fn spending(work_left: Option<Rc<Cell<usize>>>) -> Self {
        Self {
            work_left,
            ..Self::default()
        }
    }

    /// The work the output check may spend on a page of `length` bytes.
    pub(crate) fn check_work_for(length: usize) -> Rc<Cell<usize>> {
        Rc::new(Cell::new(
            CHECK_WORK_FLOOR.saturating_add(length.saturating_mul(MAX_CHECK_WORK_PER_BYTE)),
        ))
    }

    /// Record a start tag named `name`, which html5gum gives in lower case.
    pub(crate) fn start_tag(&self, name: &[u8]) {
        // The attribute count belongs to one tag, so it starts again here.
        self.attributes.set(0);
        let formatting = is_formatting_element(name);
        self.in_formatting_tag.set(formatting);
        if formatting {
            self.formatting_fed.set(self.formatting_fed.get() + 1);
        }
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
        if self.in_formatting_tag.get() {
            self.formatting_fed.set(self.formatting_fed.get() + 1);
        }
        self.attributes.set(self.attributes.get() + 1);
        if self.attributes.get() > MAX_ATTRIBUTES_PER_TAG {
            self.exceed(HtmlTooLarge::Attributes);
        }
    }

    /// Check what the tree builder holds after it has processed one token.
    ///
    /// `formatting_made` is how much formatting the tree builder has made in
    /// this run: one for each formatting element it created, in any
    /// namespace, and one for each attribute that element carries. The tree
    /// sink counts it as the tree builder creates the elements. A formatting
    /// start tag makes one element for itself and no other formatting
    /// element is made unless the tree builder is reopening or copying one,
    /// so what the token made beyond what the start tag handed over with it
    /// accounts for (`formatting_fed`) is reopening. An attribute counts
    /// because each reopened element copies its attributes.
    ///
    /// A start tag can account for more than the tree builder makes of it:
    /// an ignored tag (inside `<select>`, for one) makes nothing, and the
    /// scan drops an attribute written twice. Each token is therefore
    /// compared with only its own tag, so that tag's surplus cannot hide
    /// the reopening a later token causes.
    ///
    /// `trace` lists what the tree builder holds by calling its
    /// `trace_handles` with the tracer it is given. That reports the
    /// document, then every element in the tree builder's stack of open
    /// elements, then every element on its list of formatting elements, then
    /// the `<head>`, `<form>` and context elements it points at. An open
    /// formatting element is in the stack and on the list, so counting the
    /// reports counts that element twice. The count is therefore taken in
    /// two steps: counting the reports settles the common case in one pass,
    /// and only a tree builder that reports more than [`MAX_OPEN_ELEMENTS`]
    /// handles is asked again, to count each element once by its address.
    ///
    /// Returns how many handles the tree builder reported, or `None` when
    /// this token took the run over the limit on reopened formatting
    /// elements (before the handles were counted) or over the output
    /// check's work budget (after).
    pub(crate) fn after_token(
        &self,
        formatting_made: usize,
        trace: impl Fn(&dyn Tracer<Handle = Handle>),
    ) -> Option<usize> {
        let made = formatting_made - self.made_seen.replace(formatting_made);
        let fed = self.formatting_fed.get() - self.fed_seen.replace(self.formatting_fed.get());
        self.reopened
            .set(self.reopened.get() + made.saturating_sub(fed));
        if self.reopened.get() > MAX_REOPENED_FORMATTING_ELEMENTS {
            self.exceed(HtmlTooLarge::ReopenedFormatting);
            return None;
        }
        let count = CountHandles::default();
        trace(&count);
        let reported = count.0.get();
        // The count is what this token cost, so the output check spends it.
        if let Some(work_left) = &self.work_left {
            match work_left.get().checked_sub(reported) {
                Some(left) => work_left.set(left),
                None => {
                    work_left.set(0);
                    self.exceed(HtmlTooLarge::CheckWork);
                    return None;
                }
            }
        }
        // The first handle is the document, which is no element.
        if reported.saturating_sub(1) <= MAX_OPEN_ELEMENTS {
            return Some(reported);
        }
        self.seen.borrow_mut().clear();
        trace(&CollectAddresses {
            seen: &self.seen,
            first: Cell::new(true),
        });
        if self.seen.borrow().len() > MAX_OPEN_ELEMENTS {
            self.exceed(HtmlTooLarge::OpenElements);
        }
        Some(reported)
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

/// A [`Tracer`] that counts the handles the tree builder reports.
#[derive(Default)]
pub(crate) struct CountHandles(pub(crate) Cell<usize>);

impl Tracer for CountHandles {
    type Handle = Handle;

    fn trace_handle(&self, _node: &Handle) {
        self.0.set(self.0.get() + 1);
    }
}

/// A [`Tracer`] that keeps the address of each reported element once, after
/// the document that comes first.
struct CollectAddresses<'a> {
    seen: &'a RefCell<HashSet<usize, BuildHasherDefault<AddressHasher>>>,
    first: Cell<bool>,
}

impl Tracer for CollectAddresses<'_> {
    type Handle = Handle;

    fn trace_handle(&self, node: &Handle) {
        if self.first.replace(false) {
            return;
        }
        self.seen.borrow_mut().insert(Rc::as_ptr(node) as usize);
    }
}

/// A hasher for the addresses of nodes. The standard hasher is slower per
/// address than a multiplication, and the input does not choose addresses,
/// so a cheap multiplication spreads them well enough. Nodes sit at
/// multiples of 16 bytes, so the low four bits are zero and are dropped
/// first.
#[derive(Default)]
struct AddressHasher(u64);

impl Hasher for AddressHasher {
    fn finish(&self) -> u64 {
        self.0
    }

    fn write(&mut self, bytes: &[u8]) {
        for byte in bytes {
            self.0 = (self.0 ^ u64::from(*byte)).wrapping_mul(0x0100_0000_01b3);
        }
    }

    fn write_usize(&mut self, address: usize) {
        let mixed = (address as u64 >> 4).wrapping_mul(0x9e37_79b9_7f4a_7c15);
        self.0 = mixed ^ (mixed >> 32);
    }
}

#[cfg(test)]
mod tests {
    use super::{
        is_formatting_element, AddressHasher, HtmlLimits, HtmlTooLarge, MAX_ATTRIBUTES_PER_TAG,
        MAX_DOCUMENT_TAGS, MAX_OPEN_ELEMENTS, MAX_REOPENED_FORMATTING_ELEMENTS,
    };
    use html5ever::tree_builder::Tracer;
    use markup5ever_rcdom::{Handle, Node, NodeData};
    use std::hash::Hasher;

    /// Distinct handles, standing in for the tree builder's elements.
    fn elements(count: usize) -> Vec<Handle> {
        (0..count).map(|_| Node::new(NodeData::Document)).collect()
    }

    /// What the tree builder reports for a document, the stack of open
    /// elements `open` and the list of formatting elements `listed`.
    fn report(
        document: &Handle,
        open: &[Handle],
        listed: &[Handle],
    ) -> impl Fn(&dyn Tracer<Handle = Handle>) {
        let handles: Vec<Handle> = std::iter::once(document)
            .chain(open)
            .chain(listed)
            .cloned()
            .collect();
        move |tracer| {
            handles
                .iter()
                .for_each(|handle| tracer.trace_handle(handle))
        }
    }

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
    fn open_elements_count_up_to_the_limit_and_the_document_is_not_one() {
        let document = elements(1).remove(0);
        let all = elements(MAX_OPEN_ELEMENTS + 1);
        let limits = HtmlLimits::default();
        limits.after_token(0, report(&document, &all[..MAX_OPEN_ELEMENTS], &[]));
        assert_eq!(limits.result(), Ok(()));
        limits.after_token(0, report(&document, &all, &[]));
        assert_eq!(limits.result(), Err(HtmlTooLarge::OpenElements));
    }

    #[test]
    fn an_element_open_and_on_the_formatting_list_counts_once() {
        let document = elements(1).remove(0);
        let all = elements(MAX_OPEN_ELEMENTS);
        let limits = HtmlLimits::default();
        // Every open element is also on the list: twice the handles, the
        // same elements.
        limits.after_token(0, report(&document, &all, &all));
        assert_eq!(limits.result(), Ok(()));
        // A listed element that is not open is one the tree builder would
        // reopen, so it counts.
        limits.after_token(0, report(&document, &all, &elements(1)));
        assert_eq!(limits.result(), Err(HtmlTooLarge::OpenElements));
    }

    #[test]
    fn reopened_formatting_elements_are_those_beyond_the_start_tags() {
        let document = elements(1).remove(0);
        let nothing = report(&document, &[], &[]);
        let limits = HtmlLimits::default();
        // A formatting start tag makes one element for itself and one for
        // each attribute, which a copy of it would repeat. The `<b>` with
        // two attributes counts 3, `<i>` and `<a>` 1 each. A `<p>` and its
        // attributes are no formatting element, so they count nothing.
        limits.start_tag(b"b");
        limits.attribute();
        limits.attribute();
        limits.start_tag(b"i");
        limits.start_tag(b"a");
        limits.start_tag(b"p");
        for _ in 0..10 {
            limits.attribute();
        }
        limits.after_token(5 + MAX_REOPENED_FORMATTING_ELEMENTS, &nothing);
        assert_eq!(limits.result(), Ok(()));
        limits.after_token(5 + MAX_REOPENED_FORMATTING_ELEMENTS + 1, &nothing);
        assert_eq!(limits.result(), Err(HtmlTooLarge::ReopenedFormatting));
    }

    #[test]
    fn what_one_start_tag_accounts_for_beyond_its_element_does_not_offset_a_later_token() {
        let document = elements(1).remove(0);
        let nothing = report(&document, &[], &[]);
        let limits = HtmlLimits::default();
        // A `<b>` with 1,024 attributes written twice: html5gum reports
        // them all, and the scan drops the repeats, so the tree builder
        // makes a `<b>` with one attribute, 2 of the 1,025 counted.
        limits.start_tag(b"b");
        for _ in 0..1_024 {
            limits.attribute();
        }
        limits.after_token(2, &nothing);
        assert_eq!(limits.result(), Ok(()));
        // A later token that reopens one more than the limit allows is
        // refused, however much the earlier tag accounted for.
        limits.after_token(2 + MAX_REOPENED_FORMATTING_ELEMENTS + 1, &nothing);
        assert_eq!(limits.result(), Err(HtmlTooLarge::ReopenedFormatting));
    }

    #[test]
    fn the_exact_count_starts_again_for_each_token() {
        let document = elements(1).remove(0);
        let limits = HtmlLimits::default();
        // Each report holds 300 open elements that are also on the list:
        // 601 handles, so the exact count runs, and 300 elements. Two
        // reports of different elements are not 600 together.
        for _ in 0..2 {
            let all = elements(300);
            limits.after_token(0, report(&document, &all, &all));
        }
        assert_eq!(limits.result(), Ok(()));
    }

    #[test]
    fn the_first_limit_reached_stays_the_reason_across_kinds() {
        let document = elements(1).remove(0);
        let limits = HtmlLimits::default();
        limits.after_token(
            MAX_REOPENED_FORMATTING_ELEMENTS + 1,
            report(&document, &elements(MAX_OPEN_ELEMENTS + 1), &[]),
        );
        assert_eq!(limits.exceeded(), Some(HtmlTooLarge::ReopenedFormatting));
    }

    #[test]
    fn addresses_spread_over_the_hash_table_although_their_low_bits_are_zero() {
        // A table picks a slot from the low bits of the hash. Addresses of
        // nodes are multiples of 16 at least, so a hash that kept those bits
        // would put them all in a sixteenth of the slots.
        let mut slots = std::collections::HashSet::new();
        for index in 0..1_000_usize {
            let mut hasher = AddressHasher::default();
            hasher.write_usize(0x6000_0000 + index * 48);
            slots.insert(hasher.finish() & 0x3ff);
        }
        assert!(slots.len() > 500, "{} slots", slots.len());
    }

    #[test]
    fn formatting_elements_are_the_fourteen_the_standard_lists() {
        for name in [
            "a", "b", "big", "code", "em", "font", "i", "nobr", "s", "small", "strike", "strong",
            "tt", "u",
        ] {
            assert!(is_formatting_element(name.as_bytes()), "{name}");
        }
        for name in ["p", "div", "span", "bdi", "abbr", "cite", "mark", "B", ""] {
            assert!(!is_formatting_element(name.as_bytes()), "{name}");
        }
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
        assert_eq!(
            HtmlTooLarge::OpenElements.to_string(),
            "HTML keeps more than 512 elements open at once; Citry reads at most 512"
        );
        assert_eq!(
            HtmlTooLarge::ReopenedFormatting.to_string(),
            "HTML leaves formatting tags such as <b> and <i> open or misnested so often that the \
             parser would copy more than 250000 elements and attributes; Citry reads at most \
             250000"
        );
    }
}
