//! Reject an expression whose syntax tree could nest too deeply, before any
//! code builds or walks that tree.
//!
//! Ruff's parser grows its own stack, but the passes after it do not: the
//! keyword check, the sandbox transformer, code generation, and dropping the
//! tree all call themselves once per tree level. A long chain such as
//! `1+1+...+1`, `not not ... x` or `a.b.b...` nests the tree one level per
//! operator, with no brackets at all, and enough of them overflowed the
//! stack and crashed the process.
//!
//! So `check_nesting` reads the tokens first, which needs no recursion, and
//! computes a depth bound: a number meant never to be smaller than the tree's
//! depth. Each comma-separated part of a bracket costs two levels for every
//! token that can add a tree level (operators, keywords, `.`, `:`, `=`, ...),
//! plus its deepest inner bracket, plus two. Each bracket adds one more.
//!
//! - Counting every such token in the part, wherever it sits, keeps the bound
//!   from being too small where Python nests a later operator above an
//!   earlier bracket, as in `(x) + y`.
//! - The factor of two covers syntax that adds two tree levels, such as a call
//!   `f(x)`, which adds a `Call` node and an `Arguments` node under it.
//! - A bracket right after an operand is a call or subscript (`f()()`,
//!   `a[0][0]`), which wraps everything before it in one more level with no
//!   operator token, so it counts as such a token too.
//! - Commas start a new part, so a long flat list or call stays cheap. A comma
//!   between a `lambda`'s parameters does not, because the lambda's body still
//!   nests under it.
//!
//! The check runs before parsing, so it also guards input that does not
//! parse: Ruff still builds a partial tree for it, and dropping that tree
//! calls itself once per level too.

use ruff_python_ast::token::TokenKind;
use ruff_python_parser::lexer::lex;
use ruff_python_parser::{Mode, ParseError, ParseErrorType};
use ruff_text_size::{TextRange, TextSize};

/// The largest depth bound an expression may have.
///
/// With the stack guard in `stack.rs`, every expression within it is fully
/// processed (parsed, checked, transformed, turned back into code, and
/// dropped) even on a thread with a 256 KiB stack in a debug build.
/// `tests/nesting.rs` checks this, and that the bound is never below the real
/// depth, on random expressions and on a pure chain of each of 26 common
/// constructs that nest the tree. Typical template expressions stay far below
/// it: `a.b(c[d] + 1)`
/// has a bound of 16, and a list comprehension with a condition about 20.
pub const MAX_NESTING: usize = 200;

/// One bracket that is still open while the tokens are read.
#[derive(Default)]
struct OpenBracket {
    /// Tokens in the current comma-separated part that can add a tree level.
    level_tokens: usize,
    /// The largest bound of a bracket already closed inside the current part.
    deepest_inner: usize,
    /// The largest bound of a finished part of this bracket.
    deepest_part: usize,
    /// `lambda` keywords whose `:` has not come yet. Their parameters are
    /// separated by commas that do not end the lambda, so those commas must
    /// not start a new part.
    open_lambdas: usize,
}

impl OpenBracket {
    /// Close the current comma-separated part and start a new one.
    fn finish_part(&mut self) {
        let part = 2 * self.level_tokens + self.deepest_inner + 2;
        self.deepest_part = self.deepest_part.max(part);
        self.level_tokens = 0;
        self.deepest_inner = 0;
    }
}

/// Return a number that is at least the depth of the syntax tree `source`
/// would parse to.
pub fn nesting_bound(source: &str) -> usize {
    // The whole expression is treated as one outer bracket.
    let mut open = vec![OpenBracket::default()];
    let mut lexer = lex(source, Mode::Expression);
    // Whether the last token ended an operand, such as a name or `)`. A
    // bracket right after one is a call or subscript, as in `f()()` or
    // `a[0][0]`, and each of those wraps everything before it in one more
    // tree level, with no operator token to count.
    let mut after_operand = false;
    loop {
        let kind = lexer.next_token();
        let ends_operand = matches!(
            kind,
            TokenKind::Name
                | TokenKind::Int
                | TokenKind::Float
                | TokenKind::Complex
                | TokenKind::String
                | TokenKind::True
                | TokenKind::False
                | TokenKind::None
                | TokenKind::Ellipsis
                | TokenKind::Rpar
                | TokenKind::Rsqb
                | TokenKind::Rbrace
                | TokenKind::FStringEnd
                | TokenKind::TStringEnd
        );
        match kind {
            TokenKind::EndOfFile => break,
            TokenKind::Lpar | TokenKind::Lsqb => {
                if after_operand {
                    open.last_mut().unwrap().level_tokens += 1;
                }
                open.push(OpenBracket::default());
            }
            // An f-string or t-string wraps its `{...}` fields in its own node,
            // so it counts as a bracket. Since Python 3.12 (PEP 701) the lexer
            // emits those fields as ordinary tokens, so they are counted
            // inside it. Neither can follow an operand as a call or subscript,
            // so adjacent fields such as `f'{a}{b}'` stay flat.
            TokenKind::Lbrace | TokenKind::FStringStart | TokenKind::TStringStart => {
                open.push(OpenBracket::default());
            }
            TokenKind::Rpar
            | TokenKind::Rsqb
            | TokenKind::Rbrace
            | TokenKind::FStringEnd
            | TokenKind::TStringEnd => close_bracket(&mut open),
            TokenKind::Comma => {
                let bracket = open.last_mut().unwrap();
                // A comma between lambda parameters stays inside the lambda.
                if bracket.open_lambdas == 0 {
                    bracket.finish_part();
                }
            }
            TokenKind::Lambda => {
                let bracket = open.last_mut().unwrap();
                bracket.level_tokens += 1;
                bracket.open_lambdas += 1;
            }
            TokenKind::Colon => {
                let bracket = open.last_mut().unwrap();
                bracket.level_tokens += 1;
                bracket.open_lambdas = bracket.open_lambdas.saturating_sub(1);
            }
            // Names and literals are leaves, which the `+ 2` of each part
            // already covers; comments and layout tokens add nothing to the
            // tree.
            TokenKind::Name
            | TokenKind::Int
            | TokenKind::Float
            | TokenKind::Complex
            | TokenKind::String
            | TokenKind::FStringMiddle
            | TokenKind::TStringMiddle
            | TokenKind::Comment
            | TokenKind::Newline
            | TokenKind::NonLogicalNewline
            | TokenKind::Indent
            | TokenKind::Dedent => {}
            // Every other token (operators, keywords, `.`, `=`, `*`, and
            // anything unexpected) may add a level.
            _ => open.last_mut().unwrap().level_tokens += 1,
        }
        // Comments and line breaks do not change what the next bracket means.
        if !matches!(
            kind,
            TokenKind::Comment | TokenKind::Newline | TokenKind::NonLogicalNewline
        ) {
            after_operand = ends_operand;
        }
    }
    // Brackets left open in input that does not parse still count.
    while open.len() > 1 {
        close_bracket(&mut open);
    }
    let mut outer = open.pop().unwrap();
    outer.finish_part();
    outer.deepest_part
}

/// Finish the innermost open bracket and add its bound to the part around it.
fn close_bracket(open: &mut Vec<OpenBracket>) {
    // A closing bracket with nothing open does not parse; treat it as an
    // ordinary token so the count only grows.
    if open.len() == 1 {
        open[0].level_tokens += 1;
        return;
    }
    let mut bracket = open.pop().unwrap();
    bracket.finish_part();
    let bound = bracket.deepest_part + 1;
    let enclosing = open.last_mut().unwrap();
    enclosing.deepest_inner = enclosing.deepest_inner.max(bound);
}

/// Reject `source` when its tree could nest deeper than [`MAX_NESTING`].
pub fn check_nesting(source: &str) -> Result<(), ParseError> {
    let bound = nesting_bound(source);
    if bound <= MAX_NESTING {
        return Ok(());
    }
    // CPython also refuses deep bracket nesting ("too many nested
    // parentheses"). This message also names the limit and says what to
    // change.
    Err(ParseError {
        error: ParseErrorType::OtherError(format!(
            "expression is nested too deeply: Citry counts its operators, calls \
             and brackets as {bound} levels, and the limit is {MAX_NESTING}. Split \
             it into smaller expressions, or compute part of it in Python first."
        )),
        location: TextRange::new(TextSize::default(), TextSize::of(source)),
    })
}
