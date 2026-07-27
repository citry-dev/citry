/// The inner payload and byte offsets of a template-attribute fragment.
///
/// Fragment delimiters are attribute-level grouping syntax, not part of the
/// nested template itself. Whitespace outside the delimiters is discarded;
/// whitespace inside them is preserved.
#[derive(Debug, PartialEq, Eq)]
pub(crate) struct TemplateFragment<'a> {
    pub(crate) inner: &'a str,
    pub(crate) inner_start: usize,
    pub(crate) inner_end: usize,
}

/// Return the unwrapped payload of `<>...</>` when `content` is a fragment.
pub(crate) fn template_fragment(content: &str) -> Option<TemplateFragment<'_>> {
    let leading_whitespace = content.len() - content.trim_start().len();
    let trimmed = content.trim();
    let inner = trimmed.strip_prefix("<>")?.strip_suffix("</>")?;
    let inner_start = leading_whitespace + 2;
    let inner_end = inner_start + inner.len();

    Some(TemplateFragment {
        inner,
        inner_start,
        inner_end,
    })
}

#[cfg(test)]
mod tests {
    use super::{template_fragment, TemplateFragment};

    #[test]
    fn unwraps_only_outer_whitespace_and_fragment_delimiters() {
        assert_eq!(
            template_fragment("  <> hello </>  "),
            Some(TemplateFragment {
                inner: " hello ",
                inner_start: 4,
                inner_end: 11,
            })
        );
        assert_eq!(
            template_fragment("<></>"),
            Some(TemplateFragment {
                inner: "",
                inner_start: 2,
                inner_end: 2,
            })
        );
        assert_eq!(template_fragment("<span>hello</span>"), None);
        assert_eq!(template_fragment("   "), None);
    }
}
