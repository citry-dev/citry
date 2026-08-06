use std::collections::HashMap;

use citry_template_parser::{Comment, HtmlEndTag, HtmlStartTag, Template, Token};

use crate::error::FormatError;
use crate::source::{Span, direct_template_comments, element_span, is_html_space_text};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub(crate) enum CommentKind {
    Template,
    Html,
    Python,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum CommentPlacement {
    Unassigned,
    HtmlText,
    ProviderOwned,
    BodyLeading,
    BodyTrailing,
    BodyDangling,
    TagLeading,
    TagTrailing,
    TagDangling,
    EndTag,
    Attribute,
}

#[derive(Clone, Debug)]
struct AssociatedComment {
    kind: CommentKind,
    content: String,
    placement: CommentPlacement,
    container: Option<Span>,
    anchor: Option<Span>,
}

/// Canonical comment inventory plus formatter-owned attachment decisions.
#[derive(Clone)]
pub(crate) struct CommentMap {
    entries: HashMap<(usize, usize, CommentKind), AssociatedComment>,
}

impl CommentMap {
    pub(crate) fn new(source: &str, comments: &[Comment]) -> Result<Self, FormatError> {
        let mut entries = HashMap::new();
        for comment in comments {
            validate_token(source, &comment.token, "comment")?;
            let kind = comment_kind(&comment.token.content);
            let placement = match kind {
                CommentKind::Html => CommentPlacement::HtmlText,
                CommentKind::Python => CommentPlacement::ProviderOwned,
                CommentKind::Template => CommentPlacement::Unassigned,
            };
            entries
                .entry((comment.token.start_index, comment.token.end_index, kind))
                .or_insert_with(|| AssociatedComment {
                    kind,
                    content: comment.token.content.clone(),
                    placement,
                    container: None,
                    anchor: None,
                });
        }
        Ok(Self { entries })
    }

    pub(crate) fn associate_body(
        &mut self,
        source: &str,
        template: &Template,
        document_comments: &[Comment],
        body_span: Span,
        base: usize,
    ) -> Result<(), FormatError> {
        let anchors = template
            .elements
            .iter()
            .filter_map(|element| {
                let span = element_span(element);
                let content = source.get(base + span.start..base + span.end)?;
                (!is_html_space_text(content)).then_some(span)
            })
            .collect::<Vec<_>>();

        for comment in direct_template_comments(template, document_comments, body_span) {
            let span = Span::from_token(&comment.token);
            let preceding = anchors
                .iter()
                .copied()
                .take_while(|item| item.end <= span.start)
                .last();
            let following = anchors.iter().copied().find(|item| item.start >= span.end);
            let (placement, anchor) = if preceding.is_some_and(|item| {
                source[base + item.end..base + span.start]
                    .chars()
                    .all(|character| character != '\n' && character != '\r')
            }) {
                (CommentPlacement::BodyTrailing, preceding)
            } else if following
                .is_some_and(|item| is_html_space_text(&source[base + span.end..base + item.start]))
            {
                (CommentPlacement::BodyLeading, following)
            } else {
                (CommentPlacement::BodyDangling, None)
            };
            self.assign(
                comment,
                base,
                placement,
                body_span.offset(base),
                anchor.map(|item| item.offset(base)),
            )?;
        }
        Ok(())
    }

    pub(crate) fn associate_start_tag(
        &mut self,
        source: &str,
        tag: &HtmlStartTag,
        base: usize,
    ) -> Result<(), FormatError> {
        let attrs = tag
            .attrs
            .iter()
            .map(|attr| Span::from_token(&attr.token))
            .collect::<Vec<_>>();
        for comment in &tag.comments {
            let span = Span::from_token(&comment.token);
            let preceding = attrs
                .iter()
                .copied()
                .take_while(|item| item.end <= span.start)
                .last();
            let following = attrs.iter().copied().find(|item| item.start >= span.end);
            let (placement, anchor) = if preceding.is_some_and(|item| {
                source[base + item.end..base + span.start]
                    .chars()
                    .all(|character| character != '\n' && character != '\r')
            }) {
                (CommentPlacement::TagTrailing, preceding)
            } else if following
                .is_some_and(|item| is_html_space_text(&source[base + span.end..base + item.start]))
            {
                (CommentPlacement::TagLeading, following)
            } else {
                (CommentPlacement::TagDangling, None)
            };
            self.assign(
                comment,
                base,
                placement,
                Span::from_token(&tag.token).offset(base),
                anchor.map(|item| item.offset(base)),
            )?;
        }
        for attr in &tag.attrs {
            for comment in &attr.comments {
                if comment_kind(&comment.token.content) == CommentKind::Template {
                    let attr_span = Span::from_token(&attr.token).offset(base);
                    self.assign_if_unassigned(
                        comment,
                        base,
                        CommentPlacement::Attribute,
                        attr_span,
                        Some(attr_span),
                    )?;
                }
            }
        }
        Ok(())
    }

    pub(crate) fn associate_end_tag(
        &mut self,
        tag: &HtmlEndTag,
        base: usize,
    ) -> Result<(), FormatError> {
        let container = Span::from_token(&tag.token).offset(base);
        let anchor = Span::from_token(&tag.name).offset(base);
        for comment in &tag.comments {
            self.assign(
                comment,
                base,
                CommentPlacement::EndTag,
                container,
                Some(anchor),
            )?;
        }
        Ok(())
    }

    pub(crate) fn markup_fingerprint(&self) -> Vec<(CommentKind, String)> {
        let mut result = self
            .entries
            .values()
            .filter(|entry| entry.kind != CommentKind::Python)
            .map(|entry| (entry.kind, entry.content.clone()))
            .collect::<Vec<_>>();
        result.sort();
        result
    }

    pub(crate) fn validate_complete(&self) -> Result<(), FormatError> {
        let unassigned = self
            .entries
            .values()
            .filter(|entry| entry.placement == CommentPlacement::Unassigned)
            .count();
        if unassigned == 0 {
            Ok(())
        } else {
            Err(FormatError::invariant(format!(
                "formatter could not associate {unassigned} template comment(s)"
            )))
        }
    }

    fn assign(
        &mut self,
        comment: &Comment,
        base: usize,
        placement: CommentPlacement,
        container: Span,
        anchor: Option<Span>,
    ) -> Result<(), FormatError> {
        let kind = comment_kind(&comment.token.content);
        let key = (
            base + comment.token.start_index,
            base + comment.token.end_index,
            kind,
        );
        let Some(entry) = self.entries.get_mut(&key) else {
            return Err(FormatError::invariant(
                "formatter comment association did not match the parser inventory",
            ));
        };
        entry.placement = placement;
        entry.container = Some(container);
        entry.anchor = anchor;
        Ok(())
    }

    fn assign_if_unassigned(
        &mut self,
        comment: &Comment,
        base: usize,
        placement: CommentPlacement,
        container: Span,
        anchor: Option<Span>,
    ) -> Result<(), FormatError> {
        let kind = comment_kind(&comment.token.content);
        let key = (
            base + comment.token.start_index,
            base + comment.token.end_index,
            kind,
        );
        let Some(entry) = self.entries.get_mut(&key) else {
            return Err(FormatError::invariant(
                "formatter attribute comment did not match the parser inventory",
            ));
        };
        if entry.placement == CommentPlacement::Unassigned {
            entry.placement = placement;
            entry.container = Some(container);
            entry.anchor = anchor;
        }
        Ok(())
    }
}

fn validate_token(source: &str, token: &Token, label: &str) -> Result<(), FormatError> {
    let range = token.start_index..token.end_index;
    if source.get(range.clone()) == Some(token.content.as_str()) {
        Ok(())
    } else {
        Err(FormatError::invalid_span(
            format!("{label} span does not match its source content"),
            range,
        ))
    }
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

#[cfg(test)]
mod tests {
    use citry_template_parser::{Node, TemplateElement, parse_template};

    use super::{CommentMap, CommentPlacement};
    use crate::source::{Span, element_span};

    #[test]
    fn body_attachments_retain_container_and_anchor_identity() {
        let source = "<main>{# lead #}<div></div>{# trail #}</main>";
        let template = parse_template(source, None, None).unwrap();
        let TemplateElement::Node(Node::WithBody {
            start_tag,
            end_tag,
            body,
            ..
        }) = &template.elements[0]
        else {
            panic!("expected bodied root node");
        };
        let body_span = Span {
            start: start_tag.token.end_index,
            end: end_tag.token.start_index,
        };
        let anchor = element_span(&body.elements[0]);
        let mut comments = CommentMap::new(source, &template.comments).unwrap();

        comments
            .associate_body(source, body, &template.comments, body_span, 0)
            .unwrap();

        let leading = comments
            .entries
            .values()
            .find(|entry| entry.content == "{# lead #}")
            .unwrap();
        assert_eq!(leading.placement, CommentPlacement::BodyLeading);
        assert_eq!(leading.container, Some(body_span));
        assert_eq!(leading.anchor, Some(anchor));

        let trailing = comments
            .entries
            .values()
            .find(|entry| entry.content == "{# trail #}")
            .unwrap();
        assert_eq!(trailing.placement, CommentPlacement::BodyTrailing);
        assert_eq!(trailing.container, Some(body_span));
        assert_eq!(trailing.anchor, Some(anchor));
    }
}
