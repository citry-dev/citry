//! Turns the source model into byte edits and applies them.
//!
//! Formatting is expressed as replacements of specific spans in the original
//! text, never as a re-render of the parsed tree. That is what lets the crate
//! promise your bytes back: anything no edit covers is copied through
//! untouched, so text, verbatim bodies, and quote characters survive by
//! construction rather than by remembering to reproduce them.

use citry_template_parser::{ForeignSpan, ParseOptions};

use crate::PREFERRED_WIDTH;
use crate::error::FormatError;
use crate::newline::detect_newline;
use crate::source::{SourceModel, Span, StartTagModel, TagItemModel};
use crate::suppression::ProtectedRange;

/// An attribute longer than half the line is treated as wide enough to earn a
/// line of its own, rather than waiting for the whole tag to overflow.
const PREFERRED_ITEM_WIDTH: usize = PREFERRED_WIDTH / 2;

/// One span of the original source and the text that replaces it.
#[derive(Clone, Debug)]
pub(crate) struct Edit {
    pub(crate) span: Span,
    pub(crate) replacement: String,
}

/// The complete set of edits for one pass, sorted and checked for overlap.
pub(crate) struct EditPlan {
    edits: Vec<Edit>,
}

impl EditPlan {
    /// Collect every edit this pass wants to make.
    ///
    /// The three groups are independent: a body gap, an expression, and a start
    /// tag never cover the same bytes, which is why they can be gathered in any
    /// order and sorted afterwards.
    pub(crate) fn build(source: &str, model: &SourceModel) -> Result<Self, FormatError> {
        let newline = detect_newline(source);
        let mut edits = Vec::new();
        // Only gaps the model already proved safe to move reach this loop, so
        // rewriting one to a line break plus indent cannot change rendering.
        for gap in &model.body_gaps {
            push_edit(
                source,
                &model.protected,
                &mut edits,
                gap.span,
                &format!("{newline}{}", " ".repeat(gap.indent)),
            )?;
        }
        for expression in &model.expressions {
            push_edit(
                source,
                &model.protected,
                &mut edits,
                expression.span,
                &expression.canonical,
            )?;
        }
        for tag in &model.tags {
            plan_start_tag(source, tag, newline, &model.protected, &mut edits)?;
        }
        // `apply` walks the source once with a forward cursor, so the edits have
        // to be in source order. Validation then rejects overlaps, which would
        // otherwise silently drop or duplicate bytes during that walk.
        edits.sort_by_key(|edit| (edit.span.start, edit.span.end));
        validate_edits(source, &edits, &model.protected)?;
        Ok(Self { edits })
    }

    /// Splice the edits into `source`, copying everything they do not cover.
    pub(crate) fn apply(&self, source: &str) -> Result<String, FormatError> {
        // Size the buffer for the growth the edits add, so a tag that gains
        // several line breaks does not force repeated reallocation.
        let extra: usize = self
            .edits
            .iter()
            .map(|edit| {
                edit.replacement
                    .len()
                    .saturating_sub(edit.span.end - edit.span.start)
            })
            .sum();
        let mut output = String::with_capacity(source.len() + extra);
        let mut cursor = 0;
        for edit in &self.edits {
            // `get` rather than slicing: a span landing mid-character means the
            // model built a bad offset, and that should surface as an error
            // rather than a panic in an editor's format-on-save.
            let unchanged = source.get(cursor..edit.span.start).ok_or_else(|| {
                FormatError::invalid_span(
                    "formatter edit does not fall on UTF-8 source boundaries",
                    edit.span.start..edit.span.end,
                )
            })?;
            output.push_str(unchanged);
            output.push_str(&edit.replacement);
            cursor = edit.span.end;
        }
        output.push_str(source.get(cursor..).ok_or_else(|| {
            FormatError::invalid_span(
                "formatter edit cursor does not fall on a UTF-8 source boundary",
                cursor..cursor,
            )
        })?);
        Ok(output)
    }

    #[cfg(test)]
    pub(crate) fn from_test_edits(edits: Vec<Edit>) -> Self {
        Self { edits }
    }

    pub(crate) fn validate_for_source(
        &self,
        source: &str,
        protected: &[ProtectedRange],
    ) -> Result<(), FormatError> {
        validate_edits(source, &self.edits, protected)
    }

    /// Move foreign claims by the same byte deltas as this edit plan.
    ///
    /// Validation has already proved that no edit intersects a claim, so only
    /// edits ending before a claim can affect its coordinates.
    pub(crate) fn rebase_options(
        &self,
        options: &ParseOptions,
    ) -> Result<ParseOptions, FormatError> {
        let foreign_spans = options
            .foreign_spans
            .iter()
            .map(|span| {
                let delta = self
                    .edits
                    .iter()
                    .take_while(|edit| edit.span.end <= span.start_byte)
                    .map(|edit| {
                        edit.replacement.len() as i128 - (edit.span.end - edit.span.start) as i128
                    })
                    .sum::<i128>();
                let start_byte =
                    usize::try_from(span.start_byte as i128 + delta).map_err(|_| {
                        FormatError::invariant("formatter edit moved a foreign span out of bounds")
                    })?;
                let end_byte = usize::try_from(span.end_byte as i128 + delta).map_err(|_| {
                    FormatError::invariant("formatter edit moved a foreign span out of bounds")
                })?;
                Ok(ForeignSpan::from_parts(
                    start_byte,
                    end_byte,
                    span.provider.clone(),
                    span.ordinal,
                    span.may_control_body,
                ))
            })
            .collect::<Result<Vec<_>, FormatError>>()?;
        Ok(ParseOptions::with_foreign_spans(foreign_spans))
    }
}

/// Lay out one start tag, either on a single line or one item per line.
///
/// Returns whether the tag went multiline, which the caller uses to decide the
/// layout of what follows.
fn plan_start_tag(
    source: &str,
    tag: &StartTagModel,
    newline: &str,
    protected: &[ProtectedRange],
    edits: &mut Vec<Edit>,
) -> Result<bool, FormatError> {
    let item_sources = tag
        .items
        .iter()
        .map(|item| canonical_item(source, item, protected))
        .collect::<Result<Vec<_>, _>>()?;
    let layout_column = tag.layout_column;
    // Three separate reasons to break a tag across lines: an item that already
    // spans lines (an author's line break inside a value is kept, so the tag
    // has to open up around it), an item wide enough to deserve its own line,
    // or the whole tag not fitting.
    let multiline = item_sources
        .iter()
        .any(|item| item.contains('\n') || item.contains('\r'))
        || (item_sources.len() > 1
            && item_sources
                .iter()
                .any(|item| item.chars().count() > PREFERRED_ITEM_WIDTH))
        || !fits_one_line(source, tag, &item_sources, layout_column)?;

    // Collapse any padding the author left around `=` in `class = "x"`. This is
    // separate from the spacing between items below, because the two sides of
    // an `=` belong to one attribute and never wrap apart from each other.
    for item in &tag.items {
        if let TagItemModel::Attr(attr) = item
            && let Some(value) = attr.value
        {
            push_edit(
                source,
                protected,
                edits,
                Span {
                    start: attr.key.end,
                    end: value.start,
                },
                "=",
            )?;
        }
    }

    // A tag with no attributes has nothing to lay out, so close up whatever sits
    // between the name and the delimiter and report that it stayed on one line.
    if tag.items.is_empty() {
        push_edit(
            source,
            protected,
            edits,
            Span {
                start: tag.name.end,
                end: tag.delimiter.start,
            },
            "",
        )?;
        return Ok(false);
    }

    // Every gap inside the tag becomes one of two strings: `continuation`
    // between items, and `closing` before the delimiter. On one line that is a
    // single space and nothing; broken up, the items indent two past the tag
    // and the delimiter returns to the tag's own column.
    let continuation = if multiline {
        format!("{newline}{}", " ".repeat(layout_column + 2))
    } else {
        " ".to_string()
    };
    let closing = if multiline {
        format!("{newline}{}", " ".repeat(layout_column))
    } else {
        String::new()
    };

    // Name to first item, then between each neighbouring pair, then last item
    // to delimiter. Together these cover every byte between the items, so no
    // original spacing inside the tag survives by accident.
    push_edit(
        source,
        protected,
        edits,
        Span {
            start: tag.name.end,
            end: tag.items[0].span().start,
        },
        &continuation,
    )?;
    for pair in tag.items.windows(2) {
        push_edit(
            source,
            protected,
            edits,
            Span {
                start: pair[0].span().end,
                end: pair[1].span().start,
            },
            &continuation,
        )?;
    }
    push_edit(
        source,
        protected,
        edits,
        Span {
            start: tag.items.last().expect("non-empty items").span().end,
            end: tag.delimiter.start,
        },
        &closing,
    )?;
    Ok(multiline)
}

/// The text an item will occupy once formatted, used to measure the tag.
///
/// Width has to be judged on what the item will become, not what it is now, or
/// a tag padded with spaces would be measured as too wide and broken up for no
/// reason.
fn canonical_item(
    source: &str,
    item: &TagItemModel,
    protected: &[ProtectedRange],
) -> Result<String, FormatError> {
    match item {
        TagItemModel::Comment(span) => source_slice(source, *span).map(str::to_string),
        TagItemModel::Attr(attr) => {
            // Only predict the tightened `key=value` when the `=` is actually
            // editable. Inside a protected range it keeps its original spacing,
            // so measuring the tightened form would understate its width.
            if let Some(value) = attr.value
                && !span_intersects_protected(
                    Span {
                        start: attr.key.end,
                        end: value.start,
                    },
                    protected,
                )
            {
                let mut result = source_slice(source, attr.key)?.to_string();
                result.push('=');
                result.push_str(source_slice(source, value)?);
                Ok(result)
            } else {
                source_slice(source, attr.span).map(str::to_string)
            }
        }
    }
}

/// Whether the whole tag still fits within the preferred width.
///
/// Measured in characters rather than bytes, so a tag full of non-ASCII text is
/// judged by how wide it looks rather than how many bytes it takes.
fn fits_one_line(
    source: &str,
    tag: &StartTagModel,
    item_sources: &[String],
    line_prefix_width: usize,
) -> Result<bool, FormatError> {
    let tag_head = source_slice(
        source,
        Span {
            start: tag.span.start,
            end: tag.name.end,
        },
    )?;
    let delimiter = source_slice(source, tag.delimiter)?;
    // An empty element's end tag sits on the same line, so `<div></div>` has to
    // be measured whole. Ignoring it would keep a tag on one line that then
    // overflows once the end tag lands beside it.
    let adjacent_end_tag = tag
        .adjacent_end_tag
        .map(|span| source_slice(source, span))
        .transpose()?
        .unwrap_or_default();
    let item_width = item_sources
        .iter()
        .map(|item| item.chars().count())
        .sum::<usize>();
    let spaces = usize::from(!item_sources.is_empty()) * item_sources.len();
    let width = line_prefix_width
        + tag_head.chars().count()
        + item_width
        + spaces
        + delimiter.chars().count()
        + adjacent_end_tag.chars().count();
    Ok(width <= PREFERRED_WIDTH)
}

/// Record an edit, unless it would change nothing or reach protected bytes.
///
/// Dropping no-op edits here is what lets the pass loop use "the text stopped
/// changing" as its fixed point: a settled template produces an empty plan.
fn push_edit(
    source: &str,
    protected: &[ProtectedRange],
    edits: &mut Vec<Edit>,
    span: Span,
    replacement: &str,
) -> Result<(), FormatError> {
    let current = source_slice(source, span)?;
    if current == replacement || span_intersects_protected(span, protected) {
        return Ok(());
    }
    edits.push(Edit {
        span,
        replacement: replacement.to_string(),
    });
    Ok(())
}

/// Reject a plan that would corrupt the source rather than reformat it.
///
/// `push_edit` already skips protected spans, so a violation reaching here means
/// a span was built wrong. Checking again at the boundary keeps that from
/// reaching the file.
fn validate_edits(
    source: &str,
    edits: &[Edit],
    protected: &[ProtectedRange],
) -> Result<(), FormatError> {
    // Edits arrive sorted, so a start behind the cursor is an overlap.
    let mut cursor = 0;
    for edit in edits {
        source_slice(source, edit.span)?;
        if edit.span.start < cursor {
            return Err(FormatError::invariant(
                "formatter produced overlapping source edits",
            ));
        }
        if span_intersects_protected(edit.span, protected) {
            return Err(FormatError::invariant(
                "formatter edit intersects a protected suppression range",
            ));
        }
        cursor = edit.span.end;
    }
    Ok(())
}

fn span_intersects_protected(span: Span, protected: &[ProtectedRange]) -> bool {
    protected.iter().any(|range| {
        // An empty span is an insertion point, not an overlap, so it needs the
        // range's own rule about whether text may be inserted there. Plain
        // overlap arithmetic would call it disjoint and let the insertion
        // through into protected text.
        if span.start == span.end {
            range.blocks_insertion(span.start)
        } else {
            span.start < range.span.end && range.span.start < span.end
        }
    })
}

fn source_slice(source: &str, span: Span) -> Result<&str, FormatError> {
    source.get(span.start..span.end).ok_or_else(|| {
        FormatError::invalid_span(
            "formatter source span is not on UTF-8 boundaries",
            span.start..span.end,
        )
    })
}

#[cfg(test)]
mod tests {
    use super::{Edit, EditPlan};
    use crate::source::Span;
    use crate::suppression::ProtectedRange;

    #[test]
    fn protected_ranges_reject_intersecting_edits() {
        let source = "<div  class = \"x\"></div>";
        let plan = EditPlan::from_test_edits(vec![Edit {
            span: Span { start: 5, end: 18 },
            replacement: " class=\"x\"".to_string(),
        }]);

        assert!(
            plan.validate_for_source(
                source,
                &[ProtectedRange {
                    span: Span { start: 6, end: 17 },
                    allow_insertion_at_end: false,
                }],
            )
            .is_err()
        );
    }
}
