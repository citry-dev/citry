use crate::PREFERRED_WIDTH;
use crate::error::FormatError;
use crate::newline::detect_newline;
use crate::source::{SourceModel, Span, StartTagModel, TagItemModel};
use crate::suppression::ProtectedRange;

const PREFERRED_ITEM_WIDTH: usize = PREFERRED_WIDTH / 2;

#[derive(Clone, Debug)]
pub(crate) struct Edit {
    pub(crate) span: Span,
    pub(crate) replacement: String,
}

pub(crate) struct EditPlan {
    edits: Vec<Edit>,
}

impl EditPlan {
    pub(crate) fn build(source: &str, model: &SourceModel) -> Result<Self, FormatError> {
        let newline = detect_newline(source);
        let mut edits = Vec::new();
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
        edits.sort_by_key(|edit| (edit.span.start, edit.span.end));
        validate_edits(source, &edits, &model.protected)?;
        Ok(Self { edits })
    }

    pub(crate) fn apply(&self, source: &str) -> Result<String, FormatError> {
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
}

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
    let multiline = item_sources
        .iter()
        .any(|item| item.contains('\n') || item.contains('\r'))
        || (item_sources.len() > 1
            && item_sources
                .iter()
                .any(|item| item.chars().count() > PREFERRED_ITEM_WIDTH))
        || !fits_one_line(source, tag, &item_sources, layout_column)?;

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

fn canonical_item(
    source: &str,
    item: &TagItemModel,
    protected: &[ProtectedRange],
) -> Result<String, FormatError> {
    match item {
        TagItemModel::Comment(span) => source_slice(source, *span).map(str::to_string),
        TagItemModel::Attr(attr) => {
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

fn validate_edits(
    source: &str,
    edits: &[Edit],
    protected: &[ProtectedRange],
) -> Result<(), FormatError> {
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
