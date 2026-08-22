use std::borrow::Cow;
use std::cell::RefCell;
use std::collections::{BTreeMap, HashMap, HashSet};
use std::rc::Rc;

use pest::error::InputLocation;
use pyo3::prelude::*;

use crate::ast::{Comment, ForeignSourcePart, Token};
use crate::error::ParseError;
use crate::foreign::ForeignSpan;
use crate::grammar::Rule;
use crate::lang::lang::LangImpl;

/// Attribute validation rules for special tags
///
/// Used to define custom attribute validation rules for user-defined tags.
///
/// # Examples
///
/// ```ignore
/// use std::collections::{BTreeMap, HashMap};
/// use citry_template_parser::{TagRules, parse_template};
///
/// let mut rules = HashMap::new();
/// rules.insert("my-tag".to_string(), TagRules {
///     allowed_attrs: Some(vec![vec!["id".to_string(), "c-id".to_string()]]),
///     required_attrs: vec![vec!["id".to_string(), "c-id".to_string()]],
///     allowed_slots: Some(vec!["default".to_string()]),
///     required_slots: vec!["default".to_string()],
///     slot_data_fields: BTreeMap::new(),
/// });
///
/// let template = parse_template("<my-tag id=\"test\"></my-tag>", None, Some(&rules))?;
/// ```
#[pyclass]
#[derive(Debug, Clone)]
pub struct TagRules {
    /// Allowed attributes. List of lists where inner lists mean "one of" (mutually exclusive).
    /// - If `None`, any attributes allowed.
    /// - If `Some(vec![])`, no attributes allowed.
    /// - If `Some([["c-name", "name"]])`, the tag can have either "c-name" OR "name", but not both.
    /// - If `Some([["c-name", "name"], ["data"]])`, the tag can have either "c-name" OR "name", but not both,
    ///   and can have "data" as well.
    #[pyo3(get)]
    pub allowed_attrs: Option<Vec<Vec<String>>>,
    /// Required attributes. List of lists where inner lists mean "one of"
    /// (at least one from each inner list must be present).
    /// - If `[]`, no attributes required.
    /// - If `[["id", "c-id"]]`, at least one of "id" or "c-id" must be present.
    /// - If `[["id", "c-id", "c-bind"], ["data"]]`, at least one of "id" or "c-id" or "c-bind" must be present,
    ///   and "data" can be present as well.
    #[pyo3(get)]
    pub required_attrs: Vec<Vec<String>>,
    /// Allowed slot names (for `<c-fill>` tags).
    /// - If `None`, any slot names allowed.
    /// - If `Some(vec![])`, no slots allowed (component cannot have fills).
    /// - If `Some(vec!["default", "footer"])`, only "default" and "footer" slots are allowed.
    #[pyo3(get)]
    pub allowed_slots: Option<Vec<String>>,
    /// Required slot names.
    /// - If `[]`, no slots required.
    /// - If `vec!["default"]`, the "default" slot must be present (either as explicit `<c-fill name="default">` or as body content).
    /// - If `vec!["default", "footer"]`, both "default" and "footer" slots must be present.
    #[pyo3(get)]
    pub required_slots: Vec<String>,
    /// Statically known slot-data fields, keyed by slot name.
    /// - A missing slot key means its data shape is unknown and is not checked.
    /// - A present key with an empty list means the slot has a known empty shape.
    /// - Explicit fields in a direct `<c-fill data="{ ... }">` binding must
    ///   belong to the effective statically named slot's list.
    #[pyo3(get)]
    pub slot_data_fields: BTreeMap<String, Vec<String>>,
}

#[pymethods]
impl TagRules {
    #[new]
    #[pyo3(signature = (allowed_attrs=None, required_attrs=Vec::new(), allowed_slots=None, required_slots=Vec::new(), slot_data_fields=BTreeMap::new()))]
    fn new(
        allowed_attrs: Option<Vec<Vec<String>>>,
        required_attrs: Vec<Vec<String>>,
        allowed_slots: Option<Vec<String>>,
        required_slots: Vec<String>,
        slot_data_fields: BTreeMap<String, Vec<String>>,
    ) -> Self {
        Self {
            allowed_attrs,
            required_attrs,
            allowed_slots,
            required_slots,
            slot_data_fields,
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "TagRules(allowed_attrs={:?}, required_attrs={:?}, allowed_slots={:?}, required_slots={:?}, slot_data_fields={:?})",
            self.allowed_attrs,
            self.required_attrs,
            self.allowed_slots,
            self.required_slots,
            self.slot_data_fields
        )
    }
}

/// Global context for parsing templates and tags
#[derive(Clone)]
pub struct ParserContext {
    /// Line offset to add to all line numbers (0-based internally, but reported as 1-based)
    pub line_offset: usize,
    /// Column offset to add to column numbers on the first line only
    pub col_offset: usize,
    /// Index offset to add to start_index and end_index
    pub index_offset: usize,
    /// User-defined attribute validation rules (tag_name -> rules)
    pub user_rules: Rc<HashMap<String, TagRules>>,
    /// Language-specific implementation for parsing expressions
    pub lang: Rc<dyn LangImpl>,
    /// Complete source passed to the outermost parser invocation.
    ///
    /// Nested template attributes are parsed from substrings, but diagnostics
    /// must still point into this source rather than displaying the substring
    /// as a separate template.
    root_source: Rc<String>,
    /// Statically known loop/fill bindings declared inside nested-template
    /// attribute values, keyed by the absolute span of the containing attr.
    ///
    /// `HtmlAttr` intentionally keeps its public shape and stores only the
    /// nested template's free variables. This parser-private side table lets
    /// the outer scope validator still see declarations inside that value.
    nested_template_bindings: Rc<RefCell<HashMap<(usize, usize), Vec<Token>>>>,
    /// Validated, non-overlapping foreign claims in root-source byte units.
    foreign_spans: Rc<Vec<ForeignSpan>>,
    /// Claims already attached to exactly one supported semantic locus.
    claimed_foreign: Rc<RefCell<HashSet<(String, usize)>>>,
}

impl ParserContext {
    /// Create a new context with no offsets
    pub fn new(lang: &Rc<dyn LangImpl>, user_rules: &Rc<HashMap<String, TagRules>>) -> Self {
        Self {
            line_offset: 0,
            col_offset: 0,
            index_offset: 0,
            lang: Rc::clone(lang),
            user_rules: Rc::clone(user_rules),
            root_source: Rc::new(String::new()),
            nested_template_bindings: Rc::new(RefCell::new(HashMap::new())),
            foreign_spans: Rc::new(Vec::new()),
            claimed_foreign: Rc::new(RefCell::new(HashSet::new())),
        }
    }

    /// Create the root parsing context for a complete source string.
    pub(crate) fn for_source(
        source: &str,
        lang: &Rc<dyn LangImpl>,
        user_rules: &Rc<HashMap<String, TagRules>>,
    ) -> Self {
        let mut context = Self::new(lang, user_rules);
        context.root_source = Rc::new(source.to_string());
        context
    }

    /// Create a root context carrying validated foreign claims.
    pub(crate) fn for_source_with_foreign(
        root_source: &str,
        source_offset: usize,
        lang: &Rc<dyn LangImpl>,
        user_rules: &Rc<HashMap<String, TagRules>>,
        foreign_spans: Vec<ForeignSpan>,
    ) -> Result<Self, ParseError> {
        let mut context = Self::for_source(root_source, lang, user_rules);
        let position = pest::Position::new(root_source, source_offset).ok_or_else(|| {
            ParseError::Value(format!(
                "Projected template offset {source_offset} is not a UTF-8 boundary"
            ))
        })?;
        let (line, col) = position.line_col();
        context.index_offset = source_offset;
        context.line_offset = line.saturating_sub(1);
        context.col_offset = col.saturating_sub(1);
        context.foreign_spans = Rc::new(foreign_spans);
        Ok(context)
    }

    /// Create a child context with specified offsets
    ///
    /// This is used when creating nested contexts (e.g., for template strings).
    pub fn create_child_context(
        &self,
        line_offset: usize,
        col_offset: usize,
        index_offset: usize,
    ) -> Self {
        Self {
            line_offset,
            col_offset,
            index_offset,
            // User-defined attribute rules are inherited from the parent context via Rc (no cloning).
            user_rules: Rc::clone(&self.user_rules),
            // Language implementation is inherited from the parent context via Rc (no cloning).
            lang: Rc::clone(&self.lang),
            root_source: Rc::clone(&self.root_source),
            nested_template_bindings: Rc::clone(&self.nested_template_bindings),
            foreign_spans: Rc::clone(&self.foreign_spans),
            claimed_foreign: Rc::clone(&self.claimed_foreign),
        }
    }

    /// Return a byte-length-preserving parse copy whose foreign bytes are
    /// grammar-inert whitespace. Newline bytes remain in place. Public tokens
    /// are rebuilt from `root_source`, so mask bytes never escape the parser.
    pub(crate) fn masked_local_source<'source>(
        &self,
        source: &'source str,
    ) -> Result<Cow<'source, str>, ParseError> {
        if self.foreign_spans.is_empty() {
            return Ok(Cow::Borrowed(source));
        }
        let local_start = self.index_offset;
        let local_end = local_start.saturating_add(source.len());
        let mut bytes = source.as_bytes().to_vec();

        let first = self
            .foreign_spans
            .partition_point(|span| span.end_byte <= local_start);
        for span in self.foreign_spans[first..]
            .iter()
            .take_while(|span| span.start_byte < local_end)
        {
            if span.start_byte < local_start || span.end_byte > local_end {
                return Err(ParseError::Value(format!(
                    "Foreign span for provider {:?} crosses a nested template boundary: {}..{} versus {}..{}",
                    span.provider, span.start_byte, span.end_byte, local_start, local_end,
                )));
            }
            let start = span.start_byte - local_start;
            let end = span.end_byte - local_start;
            for byte in &mut bytes[start..end] {
                if !matches!(*byte, b'\n' | b'\r') {
                    *byte = b' ';
                }
            }
        }

        String::from_utf8(bytes).map(Cow::Owned).map_err(|error| {
            ParseError::Value(format!(
                "Internal error while masking foreign spans as UTF-8: {error}"
            ))
        })
    }

    pub(crate) fn has_foreign_intersection(&self, start: usize, end: usize) -> bool {
        let first = self
            .foreign_spans
            .partition_point(|span| span.end_byte <= start);
        self.foreign_spans
            .get(first)
            .is_some_and(|span| span.start_byte < end)
    }

    /// Attach all still-unclaimed foreign ranges wholly contained in a token.
    pub(crate) fn claim_foreign_parts(
        &self,
        start: usize,
        end: usize,
    ) -> Result<Vec<ForeignSourcePart>, ParseError> {
        let mut parts = Vec::new();
        let mut claimed = self.claimed_foreign.borrow_mut();
        let first = self
            .foreign_spans
            .partition_point(|span| span.end_byte <= start);
        for span in self.foreign_spans[first..]
            .iter()
            .take_while(|span| span.start_byte < end)
        {
            if span.start_byte < start || span.end_byte > end {
                return Err(self.error_from_absolute_range(
                    span.start_byte.max(start),
                    span.end_byte.min(end),
                    format!(
                        "FOREIGN_SPAN_UNSUPPORTED_POSITION: provider {:?} span {}..{} crosses a Citry source boundary",
                        span.provider, span.start_byte, span.end_byte,
                    ),
                ));
            }
            let claim_id = (span.provider.clone(), span.ordinal);
            if claimed.insert(claim_id) {
                parts.push(ForeignSourcePart {
                    token: self.token_from_absolute_range(span.start_byte, span.end_byte)?,
                    provider: span.provider.clone(),
                    ordinal: span.ordinal,
                    may_control_body: span.may_control_body,
                });
            }
        }
        Ok(parts)
    }

    /// Return foreign ranges in a source token without changing their claim
    /// ledger. Nested-template attributes keep this projection metadata on the
    /// outer attribute while the child AST remains the semantic owner.
    pub(crate) fn foreign_parts_in_range(
        &self,
        start: usize,
        end: usize,
    ) -> Result<Vec<ForeignSourcePart>, ParseError> {
        let mut parts = Vec::new();
        let first = self
            .foreign_spans
            .partition_point(|span| span.end_byte <= start);
        for span in self.foreign_spans[first..]
            .iter()
            .take_while(|span| span.start_byte < end)
        {
            if span.start_byte < start || span.end_byte > end {
                return Err(self.error_from_absolute_range(
                    span.start_byte.max(start),
                    span.end_byte.min(end),
                    format!(
                        "FOREIGN_SPAN_UNSUPPORTED_POSITION: provider {:?} span {}..{} crosses a Citry source boundary",
                        span.provider, span.start_byte, span.end_byte,
                    ),
                ));
            }
            parts.push(ForeignSourcePart {
                token: self.token_from_absolute_range(span.start_byte, span.end_byte)?,
                provider: span.provider.clone(),
                ordinal: span.ordinal,
                may_control_body: span.may_control_body,
            });
        }
        Ok(parts)
    }

    pub(crate) fn ensure_all_foreign_claimed(&self) -> Result<(), ParseError> {
        let claimed = self.claimed_foreign.borrow();
        if let Some(span) = self
            .foreign_spans
            .iter()
            .find(|span| !claimed.contains(&(span.provider.clone(), span.ordinal)))
        {
            return Err(self.error_from_absolute_range(
                span.start_byte,
                span.end_byte,
                format!(
                    "FOREIGN_SPAN_UNSUPPORTED_POSITION: provider {:?} span {}..{} has no supported Citry source owner",
                    span.provider, span.start_byte, span.end_byte,
                ),
            ));
        }
        Ok(())
    }

    pub(crate) fn token_from_absolute_range(
        &self,
        start: usize,
        end: usize,
    ) -> Result<Token, ParseError> {
        let source = self.root_source.as_str();
        let content = source.get(start..end).ok_or_else(|| {
            ParseError::Value(format!(
                "Invalid UTF-8 token range in root template: {start}..{end}"
            ))
        })?;
        let position = pest::Position::new(source, start).ok_or_else(|| {
            ParseError::Value(format!("Invalid token start in root template: {start}"))
        })?;
        Ok(Token {
            content: content.to_string(),
            start_index: start,
            end_index: end,
            line_col: position.line_col(),
        })
    }

    /// Reject a claim that masking displaced from an authored tag name into a
    /// grammar text token. Structural validation normally sees tag names in
    /// `collect_start_tag_foreign`; this guard covers the case where blanking
    /// the complete name made the whole tag disappear from the masked AST.
    pub(crate) fn validate_foreign_body_locus(
        &self,
        part: &ForeignSourcePart,
    ) -> Result<(), ParseError> {
        let bytes = self.root_source.as_bytes();
        let start = part.token.start_index;
        let Some(open) = bytes[..start].iter().rposition(|byte| *byte == b'<') else {
            return Ok(());
        };
        if bytes[..start]
            .iter()
            .rposition(|byte| *byte == b'>')
            .is_some_and(|close| close > open)
        {
            return Ok(());
        }

        let mut name_start = open + 1;
        if bytes.get(name_start) == Some(&b'/') {
            name_start += 1;
        }
        let Some(first) = bytes.get(name_start) else {
            return Ok(());
        };
        if !first.is_ascii_alphabetic() {
            return Ok(());
        }
        let name_end = bytes[name_start..]
            .iter()
            .position(|byte| byte.is_ascii_whitespace() || matches!(*byte, b'/' | b'>'))
            .map_or(bytes.len(), |offset| name_start + offset);
        if start < name_end && part.token.end_index > name_start {
            return Err(self.error_from_token(
                &part.token,
                format!(
                    "FOREIGN_SPAN_UNSUPPORTED_POSITION: provider {:?} span {}..{} cannot own a tag name",
                    part.provider, part.token.start_index, part.token.end_index,
                ),
            ));
        }
        Ok(())
    }

    /// Record the declarations found inside one nested-template attribute.
    pub(crate) fn record_nested_template_bindings(&self, attr_token: &Token, bindings: Vec<Token>) {
        self.nested_template_bindings
            .borrow_mut()
            .insert((attr_token.start_index, attr_token.end_index), bindings);
    }

    /// Return declarations found inside one nested-template attribute.
    pub(crate) fn nested_template_bindings(&self, attr_token: &Token) -> Vec<Token> {
        self.nested_template_bindings
            .borrow()
            .get(&(attr_token.start_index, attr_token.end_index))
            .cloned()
            .unwrap_or_default()
    }

    /// Build an error from a span in the substring currently being parsed.
    pub(crate) fn error_from_local_span(
        &self,
        span: pest::Span<'_>,
        message: String,
    ) -> ParseError {
        self.error_from_absolute_range(
            self.index_offset.saturating_add(span.start()),
            self.index_offset.saturating_add(span.end()),
            message,
        )
    }

    /// Build an error from a token whose indices are already root-absolute.
    pub(crate) fn error_from_token(&self, token: &Token, message: String) -> ParseError {
        self.error_from_absolute_range(token.start_index, token.end_index, message)
    }

    /// Build an error spanning the complete outer source.
    pub(crate) fn error_from_absolute_source(&self, message: String) -> ParseError {
        self.error_from_absolute_range(0, self.root_source.len(), message)
    }

    /// Rebase a Pest grammar error from the current substring onto the root source.
    pub(crate) fn error_from_pest(
        &self,
        error: pest::error::Error<Rule>,
        prefix: &str,
    ) -> ParseError {
        let message = format!("{}{}", prefix, error.variant.message());
        match error.location {
            InputLocation::Pos(position) => self
                .error_from_absolute_position(self.index_offset.saturating_add(position), message),
            InputLocation::Span((start, end)) => self.error_from_absolute_range(
                self.index_offset.saturating_add(start),
                self.index_offset.saturating_add(end),
                message,
            ),
        }
    }

    fn error_from_absolute_position(&self, position: usize, message: String) -> ParseError {
        let source = self.root_source.as_str();
        if let Some(position) = pest::Position::new(source, position) {
            return ParseError::Syntax(pest::error::Error::new_from_pos(
                pest::error::ErrorVariant::CustomError { message },
                position,
            ));
        }

        ParseError::Value(message)
    }

    fn error_from_absolute_range(&self, start: usize, end: usize, message: String) -> ParseError {
        let source = self.root_source.as_str();
        if let Some(span) = pest::Span::new(source, start, end) {
            return ParseError::from_span(span, message);
        }

        ParseError::Value(message)
    }

    // /////////////////////////////////////////////////////
    // COMMENTS
    // /////////////////////////////////////////////////////

    /// Helper to create a Comment from a COMMENT rule pair
    fn create_comment(&self, pair: &pest::iterators::Pair<Rule>) -> Result<Comment, ParseError> {
        let token = self.create_token(pair);

        // A comment must be at least 4 characters: {# #}
        if token.content.len() < 4 {
            return Err(self.error_from_local_span(
                pair.as_span(),
                format!("Invalid comment: too short ({})", token.content.clone()),
            ));
        }

        // Create value token with offsets to skip {# at start and #} at end
        // The content will be automatically sliced and trimmed
        let value_token = token.clone().crop_cols(2, -2);

        Ok(Comment {
            token,
            value: value_token,
        })
    }

    /// Filter wrapper pairs whose single child might be a COMMENT
    ///
    /// This helper is used for cases like `template_element` which wraps a single child
    /// that could be `html_tag | expression | COMMENT | text`.
    ///
    /// For each parent pair:
    /// 1. Peeks at the single child
    /// 2. If child is a COMMENT, extracts it and adds to context
    /// 3. If child is not a COMMENT, keeps the parent pair
    /// 4. Returns a Vec of parent pairs (excluding those with COMMENT children)
    pub fn extract_comments_from_pairs<'i>(
        &self,
        pairs: impl IntoIterator<Item = pest::iterators::Pair<'i, Rule>>,
    ) -> Result<
        (
            impl Iterator<Item = pest::iterators::Pair<'i, Rule>>,
            Vec<Comment>,
        ),
        ParseError,
    > {
        let mut filtered_pairs = Vec::new();
        let mut comments = Vec::new();

        for pair in pairs {
            let pair_rule = pair.as_rule();

            // Handle spacing and spacing_with_whitespace by recursively extracting comments
            if pair_rule == Rule::spacing || pair_rule == Rule::spacing_with_whitespace {
                // Recursively process spacing to extract nested comments
                self._extract_comments_from_pairs(pair.into_inner(), &mut comments)?
                    .for_each(|_| {});
                // Don't add spacing pairs to filtered_pairs
                continue;
            }

            // template_element may have a COMMENT as its child. In which case we drop the parent pair
            if pair_rule == Rule::template_element {
                // Check if this pair's single child is a COMMENT
                let inner = pair.clone().into_inner().next();
                if let Some(inner_rule) = inner {
                    if inner_rule.as_rule() == Rule::template_comment {
                        // Extract and collect the comment
                        let comment = self.create_comment(&inner_rule)?;
                        comments.push(comment);
                        // Don't add this parent pair to filtered_pairs
                        continue;
                    }
                }
            }

            // Keep the parent pair if child is not a comment
            filtered_pairs.push(pair);
        }

        Ok((filtered_pairs.into_iter(), comments))
    }

    /// Filter pairs, extracting and collecting comments and spacing, returning only meaningful pairs
    ///
    /// This helper processes an iterator of pairs and:
    /// 1. Extracts COMMENT pairs and adds them to the context
    /// 2. Recursively processes spacing pairs to extract nested comments
    /// 3. Returns a Vec of non-comment, non-spacing pairs
    fn _extract_comments_from_pairs<'i>(
        &self,
        pairs: impl IntoIterator<Item = pest::iterators::Pair<'i, Rule>>,
        comments: &mut Vec<Comment>,
    ) -> Result<impl Iterator<Item = pest::iterators::Pair<'i, Rule>>, ParseError> {
        let mut filtered_pairs = Vec::new();

        for pair in pairs {
            match pair.as_rule() {
                Rule::template_comment => {
                    // Collect the comment
                    let comment = self.create_comment(&pair)?;
                    comments.push(comment);
                }
                Rule::spacing => {
                    // Recursively process spacing to extract nested comments
                    self._extract_comments_from_pairs(pair.into_inner(), comments)?
                        .for_each(|_| {});
                    // Note: we don't add spacing pairs to filtered_pairs
                }
                _ => {
                    // Keep all other pairs
                    filtered_pairs.push(pair);
                }
            }
        }

        Ok(filtered_pairs.into_iter())
    }

    // /////////////////////////////////////////////////////
    // TOKENS
    // /////////////////////////////////////////////////////

    /// Apply context offsets (line, column, index) to an existing Token
    ///
    /// This modifies the token's positions to account for the context's offsets.
    /// This is useful when you have a token created in a different context (e.g., from safe_eval)
    /// and need to adjust it to match the current context's position.
    pub fn offset_token(&self, token: Token) -> Token {
        token.offset(self.index_offset, self.line_offset, self.col_offset)
    }

    /// Create a Token from a pest Pair, applying line, column, and index offsets
    pub fn create_token(&self, pair: &pest::iterators::Pair<Rule>) -> Token {
        let span = pair.as_span();
        let start = self.index_offset.saturating_add(span.start());
        let end = self.index_offset.saturating_add(span.end());
        if !self.root_source.is_empty() {
            return self
                .token_from_absolute_range(start, end)
                .expect("Pest pair ranges must remain valid in the original root source");
        }
        self.offset_token(Token::from_pair(pair))
    }
}
