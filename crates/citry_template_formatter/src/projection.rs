//! Capability-aware projections used to verify formatter invariants.
//!
//! A projection is the template with everything the formatter is allowed to
//! change deliberately thrown away. Two templates with equal projections differ
//! only in ways that do not reach the reader, so comparing the projection before
//! and after formatting answers the question that matters: did re-laying this
//! out change what it means?
//!
//! What gets discarded depends on the capability in play, which is why the
//! projection is built to order rather than once. Under `OpeningTags` only
//! spacing inside a start tag is ignored; `StructuralLayout` additionally
//! ignores gaps the whitespace rules proved insignificant; `PythonExpressions`
//! additionally compares expressions as syntax trees rather than text.
//!
//! The comparison is only ever as good as what it keeps. Anything dropped here
//! is, by construction, something the formatter may silently change.

use std::collections::HashSet;

use citry_template_parser::{
    Comment, Expr, HtmlAttr, HtmlAttrKind, HtmlEndTag, HtmlStartTag, Node, ParseOptions, Template,
    TemplateElement, Token, parse_template, parse_template_with_options,
};
use ruff_python_ast::{
    comparable::ComparableExpr,
    token::{TokenKind, Tokens},
};
use ruff_python_parser::parse_expression;
use ruff_python_trivia::CommentRanges;
use thiserror::Error;

use crate::PREFERRED_WIDTH;
use crate::html::{
    ContainerKind, EdgeKind, GapContext, WhitespaceClass, classify_gap, container_kind_for_tag,
};
use crate::layout::{ItemEdges, analyze_elements};

/// How much the projection is willing to ignore.
///
/// Each level subsumes the one before it, so the check tightens as the formatter
/// is given less freedom. `StructuralLayout` is only reachable from tests today,
/// since the live formatter always runs with expression formatting on.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum ProjectionCapability {
    OpeningTags,
    #[cfg_attr(not(test), allow(dead_code))]
    StructuralLayout,
    PythonExpressions,
}

#[derive(Debug, Error)]
pub(crate) enum ContractError {
    #[error("Citry parse failed while building the formatter contract projection: {0}")]
    Parse(String),
    #[error("invalid {label} span {start}..{end} for a {source_len}-byte source")]
    InvalidSpan {
        label: &'static str,
        start: usize,
        end: usize,
        source_len: usize,
    },
    #[error("{label} span {start}..{end} does not match its token content")]
    TokenMismatch {
        label: &'static str,
        start: usize,
        end: usize,
    },
    #[error("body items overlap or are out of order at byte {at}")]
    OverlappingItems { at: usize },
    #[error("unclaimed non-whitespace source in body gap {start}..{end}")]
    NonWhitespaceGap { start: usize, end: usize },
    #[error("formatter contract projection changed\nbefore: {before}\nafter: {after}")]
    Mismatch { before: String, after: String },
    #[error("Python projection failed for {kind}: {message}")]
    Python { kind: &'static str, message: String },
}

#[derive(Clone, Debug, PartialEq, Eq)]
struct DocumentProjection {
    body: BodyProjection,
    comments: Vec<CommentProjection>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
struct BodyProjection {
    items: Vec<BodyItemProjection>,
    gaps: Vec<GapProjection>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
enum BodyItemProjection {
    Node(NodeProjection),
    Expr(String),
    Text(String),
    TemplateComment(String),
}

#[derive(Clone, Debug, PartialEq, Eq)]
struct NodeProjection {
    start_tag: StartTagProjection,
    end_tag: Option<EndTagProjection>,
    body: Option<BodyProjection>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
struct StartTagProjection {
    name: String,
    attrs: Vec<AttrProjection>,
    item_order: Vec<TagItemProjection>,
    is_self_closing: bool,
    foreign_source: Option<String>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
struct EndTagProjection {
    name: String,
    source: String,
    comments: Vec<String>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
struct AttrProjection {
    key: String,
    kind: AttrKindProjection,
    quote_char: Option<char>,
    value: AttrValueProjection,
}

#[derive(Clone, Debug, PartialEq, Eq)]
enum AttrValueProjection {
    None,
    Exact(String),
    Template {
        prefix: String,
        document: Box<DocumentProjection>,
        suffix: String,
    },
    Python {
        syntax: String,
        comments: Vec<String>,
    },
    FillData {
        whole: Option<String>,
        fields: Vec<(String, String)>,
        rest: Option<String>,
    },
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum AttrKindProjection {
    Static,
    Expression,
    Template,
    Meta,
}

#[derive(Clone, Debug, PartialEq, Eq)]
enum TagItemProjection {
    Attr(String),
    Comment(String),
}

#[derive(Clone, Debug, PartialEq, Eq)]
enum GapProjection {
    Exact(String),
    Structural,
}

#[derive(Clone, Debug, PartialEq, Eq, Hash, PartialOrd, Ord)]
struct CommentProjection {
    kind: CommentKind,
    content: String,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, PartialOrd, Ord)]
enum CommentKind {
    Template,
    Html,
    Python,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct Span {
    start: usize,
    end: usize,
}

struct SourceItem {
    span: Span,
    projection: BodyItemProjection,
    edges: Option<ItemEdges>,
}

struct ProjectedBody {
    projection: BodyProjection,
}

/// Confirm that formatting did not change what the template means.
///
/// Both sides are projected independently from text, so this never trusts the
/// formatter's own model of what it did. On a mismatch the two projections are
/// rendered into the error, because the useful question when this fires is which
/// field differs.
#[cfg(test)]
pub(crate) fn verify_contract_projection(
    before: &str,
    after: &str,
    mode: ProjectionCapability,
) -> Result<(), ContractError> {
    verify_contract_projection_with_options(
        before,
        &ParseOptions::default(),
        after,
        &ParseOptions::default(),
        mode,
    )
}

pub(crate) fn verify_contract_projection_with_options(
    before: &str,
    before_options: &ParseOptions,
    after: &str,
    after_options: &ParseOptions,
    mode: ProjectionCapability,
) -> Result<(), ContractError> {
    let before = project_document_with_options(before, before_options, mode)?;
    let after = project_document_with_options(after, after_options, mode)?;
    if before == after {
        Ok(())
    } else {
        Err(ContractError::Mismatch {
            before: format!("{before:#?}"),
            after: format!("{after:#?}"),
        })
    }
}

fn project_document(
    source: &str,
    mode: ProjectionCapability,
) -> Result<DocumentProjection, ContractError> {
    project_document_with_options(source, &ParseOptions::default(), mode)
}

fn project_document_with_options(
    source: &str,
    options: &ParseOptions,
    mode: ProjectionCapability,
) -> Result<DocumentProjection, ContractError> {
    let template = if options == &ParseOptions::default() {
        parse_template(source, None, None)
    } else {
        parse_template_with_options(source, None, None, options)
    }
    .map_err(|error| ContractError::Parse(error.to_string()))?;
    project_parsed_document(source, &template, mode)
}

fn project_parsed_document(
    source: &str,
    template: &Template,
    mode: ProjectionCapability,
) -> Result<DocumentProjection, ContractError> {
    let body = project_body(
        source,
        template,
        Span {
            start: 0,
            end: source.len(),
        },
        ContainerKind::Root,
        None,
        mode,
        &template.comments,
    )?;
    Ok(DocumentProjection {
        body: body.projection,
        comments: project_comments(source, &template.comments, mode)?,
    })
}

fn project_body(
    source: &str,
    template: &Template,
    body_span: Span,
    container: ContainerKind,
    parent_tag_name: Option<&str>,
    mode: ProjectionCapability,
    document_comments: &[Comment],
) -> Result<ProjectedBody, ContractError> {
    source_slice(source, body_span, "body")?;

    let element_spans = template
        .elements
        .iter()
        .map(element_span)
        .collect::<Vec<_>>();
    let mut items = Vec::new();
    let element_layouts = analyze_elements(template, parent_tag_name);

    for (index, element) in template.elements.iter().enumerate() {
        let layout = element_layouts[index];
        match element {
            TemplateElement::Node(node) => {
                let projection = project_node(source, node, mode, document_comments)?;
                items.push(SourceItem {
                    span: element_span(element),
                    projection: BodyItemProjection::Node(projection),
                    edges: layout.edges,
                });
            }
            TemplateElement::Expr(expr) => {
                validate_token(source, &expr.token, "expression")?;
                validate_token(source, &expr.value, "expression value")?;
                let value = project_expression(expr, mode)?;
                items.push(SourceItem {
                    span: span(&expr.token),
                    projection: BodyItemProjection::Expr(value),
                    edges: layout.edges,
                });
            }
            TemplateElement::Text(text) => {
                validate_token(source, &text.token, "text")?;
                // Whitespace-only text is dropped from the projection because
                // it is exactly what the formatter rewrites. Non-whitespace text
                // is kept verbatim, so a single changed character fails the
                // comparison.
                if is_html_space_text(&text.token.content) {
                    continue;
                }
                items.push(SourceItem {
                    span: span(&text.token),
                    projection: BodyItemProjection::Text(text.token.content.clone()),
                    edges: layout.edges,
                });
            }
            TemplateElement::Foreign(part) => {
                validate_token(source, &part.token, "foreign source")?;
                items.push(SourceItem {
                    span: span(&part.token),
                    projection: BodyItemProjection::Text(part.token.content.clone()),
                    edges: layout.edges,
                });
            }
        }
    }

    // The parser reports every comment on the document, so a body has to pick
    // out the ones that are directly its own: inside this body, not inside one
    // of its elements (that element projects its own), and not already taken.
    let mut seen_direct_comments = HashSet::new();
    for comment in document_comments {
        if comment_kind(&comment.token.content) != CommentKind::Template {
            continue;
        }
        let comment_span = span(&comment.token);
        if !contains(body_span, comment_span)
            || element_spans
                .iter()
                .any(|element_span| contains(*element_span, comment_span))
            || !seen_direct_comments.insert((
                comment_span.start,
                comment_span.end,
                comment.token.content.clone(),
            ))
        {
            continue;
        }
        validate_token(source, &comment.token, "template comment")?;
        items.push(SourceItem {
            span: comment_span,
            projection: BodyItemProjection::TemplateComment(comment.token.content.clone()),
            edges: None,
        });
    }

    items.sort_by_key(|item| (item.span.start, item.span.end));
    validate_item_order(body_span, &items)?;
    let gaps = project_gaps(source, body_span, container, mode, &items)?;
    Ok(ProjectedBody {
        projection: BodyProjection {
            items: items.into_iter().map(|item| item.projection).collect(),
            gaps,
        },
    })
}

fn project_node(
    source: &str,
    node: &Node,
    mode: ProjectionCapability,
    document_comments: &[Comment],
) -> Result<NodeProjection, ContractError> {
    let tag_name = node.tag_name();
    match node {
        Node::SelfClosing { start_tag, .. } => {
            let start_tag = project_start_tag(source, start_tag, mode)?;
            Ok(NodeProjection {
                start_tag,
                end_tag: None,
                body: None,
            })
        }
        Node::WithBody {
            start_tag,
            end_tag,
            body,
            ..
        } => {
            let start_projection = project_start_tag(source, start_tag, mode)?;
            let end_projection = project_end_tag(source, end_tag)?;
            let body = project_body(
                source,
                body,
                Span {
                    start: start_tag.token.end_index,
                    end: end_tag.token.start_index,
                },
                container_kind_for_tag(tag_name),
                Some(tag_name),
                mode,
                document_comments,
            )?;
            Ok(NodeProjection {
                start_tag: start_projection,
                end_tag: Some(end_projection),
                body: Some(body.projection),
            })
        }
    }
}

fn project_start_tag(
    source: &str,
    tag: &HtmlStartTag,
    mode: ProjectionCapability,
) -> Result<StartTagProjection, ContractError> {
    validate_token(source, &tag.token, "start tag")?;
    validate_token(source, &tag.name, "start tag name")?;
    let attrs = tag
        .attrs
        .iter()
        .map(|attr| project_attr(source, &tag.name.content, attr, mode))
        .collect::<Result<Vec<_>, _>>()?;

    let mut ordered = tag
        .attrs
        .iter()
        .map(|attr| {
            (
                attr.token.start_index,
                TagItemProjection::Attr(attr.key.content.clone()),
            )
        })
        .collect::<Vec<_>>();
    for comment in &tag.comments {
        validate_token(source, &comment.token, "start tag comment")?;
        if tag
            .attrs
            .iter()
            .any(|attr| contains(span(&attr.token), span(&comment.token)))
        {
            continue;
        }
        ordered.push((
            comment.token.start_index,
            TagItemProjection::Comment(comment.token.content.clone()),
        ));
    }
    ordered.sort_by_key(|(start, _)| *start);

    Ok(StartTagProjection {
        name: tag.name.content.clone(),
        attrs,
        item_order: ordered.into_iter().map(|(_, item)| item).collect(),
        is_self_closing: tag.is_self_closing,
        foreign_source: (!tag.foreign_parts.is_empty()).then(|| tag.token.content.clone()),
    })
}

fn project_end_tag(source: &str, tag: &HtmlEndTag) -> Result<EndTagProjection, ContractError> {
    validate_token(source, &tag.token, "end tag")?;
    validate_token(source, &tag.name, "end tag name")?;
    let mut comments = tag.comments.iter().collect::<Vec<_>>();
    comments.sort_by_key(|comment| comment.token.start_index);
    for comment in &comments {
        validate_token(source, &comment.token, "end tag comment")?;
    }
    Ok(EndTagProjection {
        name: tag.name.content.clone(),
        source: tag.token.content.clone(),
        comments: comments
            .into_iter()
            .map(|comment| comment.token.content.clone())
            .collect(),
    })
}

fn project_attr(
    source: &str,
    tag_name: &str,
    attr: &HtmlAttr,
    mode: ProjectionCapability,
) -> Result<AttrProjection, ContractError> {
    validate_token(source, &attr.token, "attribute")?;
    validate_token(source, &attr.key, "attribute key")?;
    if let Some(value) = &attr.value {
        validate_token(source, value, "attribute value")?;
    }
    if let Some(inner_value) = &attr.inner_value {
        validate_token(source, inner_value, "attribute inner value")?;
    }

    let kind = match attr.kind {
        HtmlAttrKind::Static => AttrKindProjection::Static,
        HtmlAttrKind::Expression => AttrKindProjection::Expression,
        HtmlAttrKind::Template => AttrKindProjection::Template,
        HtmlAttrKind::Meta => AttrKindProjection::Meta,
    };
    let key = attr.key.content.to_ascii_lowercase();
    let tag_name = tag_name.to_ascii_lowercase();
    let value = match (&attr.kind, &attr.inner_value) {
        (_, None) => AttrValueProjection::None,
        (_, Some(inner_value)) if !attr.foreign_parts.is_empty() => {
            AttrValueProjection::Exact(inner_value.content.clone())
        }
        (_, Some(inner_value))
            if mode == ProjectionCapability::PythonExpressions
                && (key == "c-for" || (tag_name == "c-for" && key == "each")) =>
        {
            project_python(
                &format!("(None for {}\n)", inner_value.content),
                "c-for clause",
            )?
        }
        (_, Some(_))
            if mode == ProjectionCapability::PythonExpressions
                && tag_name == "c-fill"
                && key == "data"
                && attr.fill_data_pattern.is_some() =>
        {
            let pattern = attr.fill_data_pattern.as_ref().expect("guarded above");
            AttrValueProjection::FillData {
                whole: pattern.whole.as_ref().map(|token| token.content.clone()),
                fields: pattern
                    .fields
                    .iter()
                    .map(|field| (field.source.content.clone(), field.target.content.clone()))
                    .collect(),
                rest: pattern.rest.as_ref().map(|token| token.content.clone()),
            }
        }
        (_, Some(inner_value))
            if mode == ProjectionCapability::PythonExpressions
                && (attr.kind == HtmlAttrKind::Expression || key == "#c-key") =>
        {
            project_python(&inner_value.content, "attribute expression")?
        }
        (HtmlAttrKind::Template, Some(inner_value))
            if mode == ProjectionCapability::OpeningTags =>
        {
            AttrValueProjection::Exact(inner_value.content.clone())
        }
        (HtmlAttrKind::Template, Some(inner_value)) => {
            let (prefix, nested_source, suffix) = split_template_framing(&inner_value.content);
            AttrValueProjection::Template {
                prefix,
                document: Box::new(project_document(nested_source, mode)?),
                suffix,
            }
        }
        (_, Some(inner_value)) => AttrValueProjection::Exact(inner_value.content.clone()),
    };

    Ok(AttrProjection {
        key: attr.key.content.clone(),
        kind,
        quote_char: attr.quote_char,
        value,
    })
}

/// How much of an expression the comparison keeps.
///
/// Each level gives up a little more text in exchange for allowing the formatter
/// a little more freedom, ending at the syntax tree, which lets Ruff re-wrap the
/// expression however it likes while still catching a change in meaning.
fn project_expression(expr: &Expr, mode: ProjectionCapability) -> Result<String, ContractError> {
    match mode {
        // Expressions are untouched at this level, so compare them byte for byte.
        ProjectionCapability::OpeningTags => Ok(expr.token.content.clone()),
        // Only the padding inside `{{ }}` is negotiable here, and only for a
        // short single-line expression with no comments, where trimming cannot
        // lose anything. Anything else stays exact.
        ProjectionCapability::StructuralLayout
            if expr.comments.is_empty()
                && !expr.value.content.contains('\n')
                && !expr.value.content.contains('\r')
                && expr.value.content.trim().chars().count() + "{{  }}".chars().count()
                    <= PREFERRED_WIDTH =>
        {
            Ok(expr.value.content.trim().to_string())
        }
        ProjectionCapability::StructuralLayout => Ok(expr.token.content.clone()),
        ProjectionCapability::PythonExpressions => {
            let projection = project_python(&expr.value.content, "template expression")?;
            Ok(format!("{projection:?}"))
        }
    }
}

/// Reduce Python to its syntax tree plus its comments.
///
/// Comments are carried separately because they are not part of the tree, so
/// comparing trees alone would let a provider drop one unnoticed.
fn project_python(source: &str, kind: &'static str) -> Result<AttrValueProjection, ContractError> {
    let parsed = parse_expression(source).map_err(|error| ContractError::Python {
        kind,
        message: error.to_string(),
    })?;
    Ok(AttrValueProjection::Python {
        syntax: format!("{:?}", ComparableExpr::from(parsed.syntax().body.as_ref())),
        comments: python_comments(source, parsed.tokens()),
    })
}

/// Fingerprint each Python comment by what it says and what it sits next to.
///
/// Position alone would change whenever the expression is re-wrapped, and text
/// alone would not notice a comment moving to a different line of a multi-line
/// expression. Anchoring to the neighbouring tokens, plus whether it shares
/// their line, survives re-wrapping while still catching a move.
fn python_comments(source: &str, tokens: &Tokens) -> Vec<String> {
    CommentRanges::from(tokens)
        .iter()
        .filter_map(|range| {
            let index = tokens.iter().position(|token| {
                token.kind() == TokenKind::Comment && token.as_tuple().1 == *range
            })?;
            let previous = tokens[..index]
                .iter()
                .rev()
                .find(|token| is_python_anchor_token(token.kind()));
            let next = tokens[index + 1..]
                .iter()
                .find(|token| is_python_anchor_token(token.kind()));
            let comment = &source[range.start().to_usize()..range.end().to_usize()];
            let same_line = previous.is_some_and(|token| {
                let token_range = token.as_tuple().1;
                !source[token_range.end().to_usize()..range.start().to_usize()]
                    .contains(['\n', '\r'])
            });
            Some(format!(
                "{}|{:?}|{same_line}|{:?}",
                comment.strip_prefix('#').unwrap_or(comment).trim(),
                previous.map(|token| python_token_fingerprint(source, token)),
                next.map(|token| python_token_fingerprint(source, token)),
            ))
        })
        .collect()
}

fn is_python_anchor_token(kind: TokenKind) -> bool {
    !matches!(
        kind,
        TokenKind::Comment
            | TokenKind::Newline
            | TokenKind::NonLogicalNewline
            | TokenKind::Indent
            | TokenKind::Dedent
            | TokenKind::EndOfFile
    )
}

fn python_token_fingerprint(source: &str, token: &ruff_python_ast::token::Token) -> String {
    let (kind, range) = token.as_tuple();
    format!(
        "{kind:?}:{}",
        &source[range.start().to_usize()..range.end().to_usize()]
    )
}

fn project_comments(
    source: &str,
    comments: &[Comment],
    mode: ProjectionCapability,
) -> Result<Vec<CommentProjection>, ContractError> {
    let mut seen = HashSet::new();
    let mut projected = Vec::new();
    for comment in comments {
        validate_token(source, &comment.token, "comment")?;
        validate_token(source, &comment.value, "comment value")?;
        let kind = comment_kind(&comment.token.content);
        if seen.insert((
            kind,
            comment.token.start_index,
            comment.token.end_index,
            comment.token.content.clone(),
        )) {
            projected.push(CommentProjection {
                kind,
                content: if kind == CommentKind::Python
                    && mode == ProjectionCapability::PythonExpressions
                {
                    normalize_python_comment(&comment.token.content)
                } else {
                    comment.token.content.clone()
                },
            });
        }
    }
    projected.sort();
    Ok(projected)
}

fn normalize_python_comment(comment: &str) -> String {
    comment
        .strip_prefix('#')
        .unwrap_or(comment)
        .trim()
        .to_string()
}

/// Project the whitespace between items, keeping only what the reader can see.
///
/// This is the heart of the comparison. A gap the whitespace rules call
/// structural collapses to one marker, so any amount of indentation compares
/// equal; a gap that renders is kept byte for byte, so touching it fails.
fn project_gaps(
    source: &str,
    body_span: Span,
    container: ContainerKind,
    _mode: ProjectionCapability,
    items: &[SourceItem],
) -> Result<Vec<GapProjection>, ContractError> {
    let mut gaps = Vec::with_capacity(items.len() + 1);
    // One item with a sensitive edge makes the whole body's spacing meaningful,
    // so every gap in it is compared exactly. Judging each gap alone would let
    // whitespace next to an inline neighbour be treated as free.
    let preserve_mixed_body = items.iter().any(|item| {
        item.edges.is_some_and(|edges| {
            edges.first == EdgeKind::Sensitive || edges.last == EdgeKind::Sensitive
        })
    });
    let mut cursor = body_span.start;
    for index in 0..=items.len() {
        let end = items
            .get(index)
            .map_or(body_span.end, |item| item.span.start);
        let gap_span = Span { start: cursor, end };
        let gap = source_slice(source, gap_span, "body gap")?;
        // Anything other than whitespace between two items means the items did
        // not account for all the source, so the projection would be comparing
        // an incomplete picture and quietly ignoring the remainder.
        if !is_html_space_text(gap) {
            return Err(ContractError::NonWhitespaceGap {
                start: gap_span.start,
                end: gap_span.end,
            });
        }

        // Look past items that render nothing to find the edges that actually
        // face each other across this gap.
        let left = items[..index]
            .iter()
            .rev()
            .find_map(|item| item.edges.map(|edges| edges.last));
        let right = items[index..]
            .iter()
            .find_map(|item| item.edges.map(|edges| edges.first));
        let class = classify_gap(GapContext {
            container,
            left,
            right,
            authored_whitespace: !gap.is_empty(),
            protected: false,
        });
        // Both capabilities use the same semantic whitespace equivalence.
        // The active formatter also verifies its exact deterministic
        // structural edit plan independently of this projection.
        gaps.push(match class {
            WhitespaceClass::Structural if preserve_mixed_body => {
                GapProjection::Exact(gap.to_string())
            }
            WhitespaceClass::Structural => GapProjection::Structural,
            WhitespaceClass::Verbatim | WhitespaceClass::Sensitive => {
                GapProjection::Exact(gap.to_string())
            }
        });

        if let Some(item) = items.get(index) {
            cursor = item.span.end;
        }
    }
    Ok(gaps)
}

fn validate_item_order(body_span: Span, items: &[SourceItem]) -> Result<(), ContractError> {
    let mut cursor = body_span.start;
    for item in items {
        if item.span.start < cursor || item.span.end > body_span.end {
            return Err(ContractError::OverlappingItems {
                at: item.span.start,
            });
        }
        cursor = item.span.end;
    }
    Ok(())
}

fn validate_token(source: &str, token: &Token, label: &'static str) -> Result<(), ContractError> {
    let token_span = span(token);
    let actual = source_slice(source, token_span, label)?;
    if actual == token.content {
        Ok(())
    } else {
        Err(ContractError::TokenMismatch {
            label,
            start: token_span.start,
            end: token_span.end,
        })
    }
}

fn source_slice<'a>(
    source: &'a str,
    source_span: Span,
    label: &'static str,
) -> Result<&'a str, ContractError> {
    source
        .get(source_span.start..source_span.end)
        .ok_or(ContractError::InvalidSpan {
            label,
            start: source_span.start,
            end: source_span.end,
            source_len: source.len(),
        })
}

fn element_span(element: &TemplateElement) -> Span {
    match element {
        TemplateElement::Node(Node::SelfClosing { start_tag, .. }) => span(&start_tag.token),
        TemplateElement::Node(Node::WithBody {
            start_tag, end_tag, ..
        }) => Span {
            start: start_tag.token.start_index,
            end: end_tag.token.end_index,
        },
        TemplateElement::Expr(expr) => span(&expr.token),
        TemplateElement::Text(text) => span(&text.token),
        TemplateElement::Foreign(part) => span(&part.token),
    }
}

fn span(token: &Token) -> Span {
    Span {
        start: token.start_index,
        end: token.end_index,
    }
}

fn contains(outer: Span, inner: Span) -> bool {
    outer.start <= inner.start && inner.end <= outer.end
}

/// Return whether every character is an HTML space character.
///
/// Rust's Unicode whitespace predicate is intentionally too broad here: NBSP
/// and other Unicode separators render as text in HTML and must stay projected
/// as sensitive body items.
fn is_html_space_text(content: &str) -> bool {
    content.chars().all(|character| {
        matches!(
            character,
            '\u{0009}' | '\u{000a}' | '\u{000c}' | '\u{000d}' | ' '
        )
    })
}

fn comment_kind(content: &str) -> CommentKind {
    if content.starts_with("{#") {
        CommentKind::Template
    } else if content.starts_with("<!--") {
        CommentKind::Html
    } else {
        CommentKind::Python
    }
}

fn split_template_framing(content: &str) -> (String, &str, String) {
    let without_leading = content.trim_start_matches(is_html_ascii_whitespace);
    let leading = content.len() - without_leading.len();
    let trimmed = without_leading.trim_end_matches(is_html_ascii_whitespace);
    let trailing = without_leading.len() - trimmed.len();
    let trimmed_end = content.len() - trailing;
    let trimmed = &content[leading..trimmed_end];
    if let Some(inner_with_close) = trimmed.strip_prefix("<>")
        && let Some(inner) = inner_with_close.strip_suffix("</>")
    {
        let inner_start = leading + 2;
        let inner_end = inner_start + inner.len();
        return (
            content[..inner_start].to_string(),
            &content[inner_start..inner_end],
            content[inner_end..].to_string(),
        );
    }
    (String::new(), content, String::new())
}

const fn is_html_ascii_whitespace(character: char) -> bool {
    matches!(character, '\t' | '\n' | '\u{000C}' | '\r' | ' ')
}

#[cfg(test)]
mod tests {
    use super::{ContractError, ProjectionCapability, verify_contract_projection};

    #[test]
    fn opening_tags_allow_tag_internal_and_adjacent_structural_layout() {
        assert!(
            verify_contract_projection(
                r#"<c-Card  class = "x"  disabled ></c-Card>"#,
                r#"<c-Card class="x" disabled></c-Card>"#,
                ProjectionCapability::OpeningTags,
            )
            .is_ok()
        );
        assert!(
            verify_contract_projection(
                "<div><section></section></div>",
                "<div>\n<section></section>\n</div>",
                ProjectionCapability::OpeningTags,
            )
            .is_ok()
        );
        assert!(matches!(
            verify_contract_projection(
                "{{ name }}",
                "{{name }}",
                ProjectionCapability::OpeningTags
            ),
            Err(ContractError::Mismatch { .. })
        ));
        assert!(matches!(
            verify_contract_projection(
                "<div></div   >",
                "<div></div>",
                ProjectionCapability::OpeningTags,
            ),
            Err(ContractError::Mismatch { .. })
        ));
    }

    #[test]
    fn structural_layout_allows_structural_but_not_sensitive_whitespace_changes() {
        assert!(
            verify_contract_projection(
                "<main><section></section><footer></footer></main>",
                "<main>\n  <section></section>\n  <footer></footer>\n</main>",
                ProjectionCapability::StructuralLayout,
            )
            .is_ok()
        );
        assert!(matches!(
            verify_contract_projection(
                "<span>A</span><span>B</span>",
                "<span>A</span> <span>B</span>",
                ProjectionCapability::StructuralLayout,
            ),
            Err(ContractError::Mismatch { .. })
        ));
    }

    #[test]
    fn structural_layout_normalizes_only_short_comment_free_expression_trivia() {
        assert!(
            verify_contract_projection(
                "{{name}}",
                "{{ name }}",
                ProjectionCapability::StructuralLayout
            )
            .is_ok()
        );
        assert!(matches!(
            verify_contract_projection(
                "{{ name }}",
                "{{ other }}",
                ProjectionCapability::StructuralLayout
            ),
            Err(ContractError::Mismatch { .. })
        ));
        assert!(matches!(
            verify_contract_projection(
                "{{ name  # person }}",
                "{{ name # person }}",
                ProjectionCapability::StructuralLayout,
            ),
            Err(ContractError::Mismatch { .. })
        ));
        let long_value = "x".repeat(95);
        let authored = format!("{{{{  {long_value}  }}}}");
        let normalized = format!("{{{{ {long_value} }}}}");
        assert!(matches!(
            verify_contract_projection(
                &authored,
                &normalized,
                ProjectionCapability::StructuralLayout,
            ),
            Err(ContractError::Mismatch { .. })
        ));
    }

    #[test]
    fn projection_keeps_tag_spelling_attribute_order_and_quotes() {
        for changed in [
            r#"<c-card a='1' b="2"></c-card>"#,
            r#"<c-Card b="2" a='1'></c-Card>"#,
            r#"<c-Card a="1" b="2"></c-Card>"#,
        ] {
            assert!(matches!(
                verify_contract_projection(
                    r#"<c-Card a='1' b="2"></c-Card>"#,
                    changed,
                    ProjectionCapability::StructuralLayout,
                ),
                Err(ContractError::Mismatch { .. })
            ));
        }
    }

    #[test]
    fn nested_template_values_use_the_same_projection_contract() {
        assert!(matches!(
            verify_contract_projection(
                r#"<c-Card c-body="<main><section></section></main>" />"#,
                "<c-Card c-body=\"<main>\n  <section></section>\n</main>\" />",
                ProjectionCapability::OpeningTags,
            ),
            Err(ContractError::Mismatch { .. })
        ));
        assert!(
            verify_contract_projection(
                r#"<c-Card c-body="<main><section></section></main>" />"#,
                "<c-Card c-body=\"<main>\n  <section></section>\n</main>\" />",
                ProjectionCapability::StructuralLayout,
            )
            .is_ok()
        );
        assert!(
            verify_contract_projection(
                r#"<c-Card c-body="  <><main><section></section></main></>  " />"#,
                "<c-Card c-body=\"  <><main>\n  <section></section>\n</main></>  \" />",
                ProjectionCapability::StructuralLayout,
            )
            .is_ok()
        );
    }

    #[test]
    fn exhaustive_block_control_branches_are_structural() {
        assert!(
            verify_contract_projection(
                r#"<main><c-if cond="ok"><section></section></c-if><c-else><footer></footer></c-else></main>"#,
                "<main>\n  <c-if cond=\"ok\">\n    <section></section>\n  </c-if>\n  <c-else>\n    <footer></footer>\n  </c-else>\n</main>",
                ProjectionCapability::StructuralLayout,
            )
            .is_ok()
        );
    }

    #[test]
    fn optional_or_disagreeing_control_edges_stay_sensitive() {
        assert!(matches!(
            verify_contract_projection(
                r#"<main><c-if cond="ok"><section></section></c-if></main>"#,
                "<main>\n<c-if cond=\"ok\"><section></section></c-if>\n</main>",
                ProjectionCapability::StructuralLayout,
            ),
            Err(ContractError::Mismatch { .. })
        ));
        assert!(matches!(
            verify_contract_projection(
                r#"<main><c-if cond="ok"><section></section></c-if><c-else><span>x</span></c-else></main>"#,
                "<main>\n<c-if cond=\"ok\"><section></section></c-if><c-else><span>x</span></c-else>\n</main>",
                ProjectionCapability::StructuralLayout,
            ),
            Err(ContractError::Mismatch { .. })
        ));
    }

    #[test]
    fn shorthand_control_flow_uses_the_underlying_edge_but_remains_optional() {
        assert!(matches!(
            verify_contract_projection(
                r#"<main><section c-if="ok"></section></main>"#,
                "<main>\n<section c-if=\"ok\"></section>\n</main>",
                ProjectionCapability::StructuralLayout,
            ),
            Err(ContractError::Mismatch { .. })
        ));
        assert!(
            verify_contract_projection(
                r#"<main><section c-if="ok"></section><footer c-else></footer></main>"#,
                "<main>\n  <section c-if=\"ok\"></section>\n  <footer c-else></footer>\n</main>",
                ProjectionCapability::StructuralLayout,
            )
            .is_ok()
        );
        assert!(matches!(
            verify_contract_projection(
                r#"<main><section c-if="ok" c-for="item in items"></section><footer c-else></footer></main>"#,
                "<main>\n<section c-if=\"ok\" c-for=\"item in items\"></section><footer c-else></footer>\n</main>",
                ProjectionCapability::StructuralLayout,
            ),
            Err(ContractError::Mismatch { .. })
        ));
    }

    #[test]
    fn contextual_and_empty_structures_do_not_gain_whitespace() {
        assert!(matches!(
            verify_contract_projection(
                "<main><option>A</option><div>B</div></main>",
                "<main><option>A</option>\n<div>B</div></main>",
                ProjectionCapability::StructuralLayout,
            ),
            Err(ContractError::Mismatch { .. })
        ));
        assert!(matches!(
            verify_contract_projection(
                "<div></div>",
                "<div>\n</div>",
                ProjectionCapability::StructuralLayout,
            ),
            Err(ContractError::Mismatch { .. })
        ));
        assert!(matches!(
            verify_contract_projection(
                "<div>{# note #}</div>",
                "<div>\n{# note #}\n</div>",
                ProjectionCapability::StructuralLayout,
            ),
            Err(ContractError::Mismatch { .. })
        ));
        assert!(matches!(
            verify_contract_projection(
                "<div><!-- note --></div>",
                "<div>\n<!-- note -->\n</div>",
                ProjectionCapability::StructuralLayout,
            ),
            Err(ContractError::Mismatch { .. })
        ));
        assert!(matches!(
            verify_contract_projection(
                "<main>\u{00a0}<section></section></main>",
                "<main>\n<section></section>\n</main>",
                ProjectionCapability::StructuralLayout,
            ),
            Err(ContractError::Mismatch { .. })
        ));
        assert!(matches!(
            verify_contract_projection(
                "<main>text<section></section></main>",
                "<main>text<section></section>\n</main>",
                ProjectionCapability::StructuralLayout,
            ),
            Err(ContractError::Mismatch { .. })
        ));
    }
}
