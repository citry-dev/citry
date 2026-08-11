use fluent_syntax::{
    ast::{
        self, CallArguments, Entry, Expression, InlineExpression, Pattern, PatternElement,
        VariantKey,
    },
    parser::{self, Slice},
    serializer,
};
use serde::Serialize;
use std::{collections::BTreeMap, env, fs, ops::Range, path::PathBuf, sync::Arc};

#[derive(Clone)]
struct SpannedSlice {
    source: Arc<String>,
    range: Range<usize>,
}

impl SpannedSlice {
    fn root(source: &str) -> Self {
        Self {
            source: Arc::new(source.to_owned()),
            range: 0..source.len(),
        }
    }

    fn range(&self) -> Range<usize> {
        self.range.clone()
    }
}

impl AsRef<str> for SpannedSlice {
    fn as_ref(&self) -> &str {
        &self.source[self.range.clone()]
    }
}

impl std::fmt::Debug for SpannedSlice {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("SpannedSlice")
            .field("text", &self.as_ref())
            .field("range", &self.range())
            .finish()
    }
}

// fluent-syntax compares S values when it detects duplicate named arguments.
// Position must therefore be metadata, not part of semantic equality.
impl PartialEq for SpannedSlice {
    fn eq(&self, other: &Self) -> bool {
        self.as_ref() == other.as_ref()
    }
}

impl Eq for SpannedSlice {}

impl Slice<'_> for SpannedSlice {
    fn slice(&self, range: Range<usize>) -> Self {
        let start = self.range.start + range.start;
        let end = self.range.start + range.end;
        Self {
            source: Arc::clone(&self.source),
            range: start..end,
        }
    }

    fn trim(&mut self) {
        let trimmed = self.as_ref().trim_end_matches([' ', '\r', '\n']);
        self.range.end = self.range.start + trimmed.len();
    }
}

#[derive(Debug, Serialize)]
struct SpanRecord {
    kind: String,
    path: String,
    start: usize,
    end: usize,
    text: String,
}

#[derive(Debug, Serialize)]
struct SampleSpan {
    start: usize,
    end: usize,
    text: String,
}

#[derive(Debug, Serialize)]
struct ProbeEvidence {
    schema_version: u8,
    result: &'static str,
    fluent_syntax: &'static str,
    gates: BTreeMap<&'static str, bool>,
    counts: BTreeMap<String, usize>,
    samples: BTreeMap<String, SampleSpan>,
    limitations: Vec<&'static str>,
}

struct SpanIndex<'source> {
    source: &'source str,
    records: Vec<SpanRecord>,
}

impl<'source> SpanIndex<'source> {
    fn new(source: &'source str) -> Self {
        Self {
            source,
            records: Vec::new(),
        }
    }

    fn record(&mut self, kind: &str, path: &str, span: Range<usize>) -> Result<(), String> {
        ensure(
            span.start <= span.end && span.end <= self.source.len(),
            format!("invalid range {span:?} for {kind} at {path}"),
        )?;
        ensure(
            self.source.is_char_boundary(span.start) && self.source.is_char_boundary(span.end),
            format!("range {span:?} splits UTF-8 for {kind} at {path}"),
        )?;
        self.records.push(SpanRecord {
            kind: kind.to_owned(),
            path: path.to_owned(),
            start: span.start,
            end: span.end,
            text: self.source[span].to_owned(),
        });
        Ok(())
    }

    fn record_identifier(
        &mut self,
        path: &str,
        identifier: &ast::Identifier<SpannedSlice>,
    ) -> Result<Range<usize>, String> {
        let span = identifier.name.range();
        self.record("identifier", path, span.clone())?;
        Ok(span)
    }

    fn visit_resource(&mut self, resource: &ast::Resource<SpannedSlice>) -> Result<(), String> {
        self.record("resource", "resource", 0..self.source.len())?;
        for (index, entry) in resource.body.iter().enumerate() {
            self.visit_entry(entry, &format!("entry[{index}]"))?;
        }
        Ok(())
    }

    fn visit_entry(&mut self, entry: &Entry<SpannedSlice>, path: &str) -> Result<(), String> {
        match entry {
            Entry::Message(message) => {
                if let Some(comment) = &message.comment {
                    self.visit_comment(comment, &format!("{path}.comment"))?;
                }
                let id = self.record_identifier(&format!("{path}.id"), &message.id)?;
                let mut end = id.end;
                if let Some(value) = &message.value {
                    end = self.visit_pattern(value, &format!("{path}.value"))?.end;
                }
                for (index, attribute) in message.attributes.iter().enumerate() {
                    end = self
                        .visit_attribute(attribute, &format!("{path}.attribute[{index}]"))?
                        .end;
                }
                self.record("message", path, id.start..end)?;
            }
            Entry::Term(term) => {
                if let Some(comment) = &term.comment {
                    self.visit_comment(comment, &format!("{path}.comment"))?;
                }
                let id = self.record_identifier(&format!("{path}.id"), &term.id)?;
                let start = self.expand_ascii_left(id.start, b'-')?;
                let mut end = self
                    .visit_pattern(&term.value, &format!("{path}.value"))?
                    .end;
                for (index, attribute) in term.attributes.iter().enumerate() {
                    end = self
                        .visit_attribute(attribute, &format!("{path}.attribute[{index}]"))?
                        .end;
                }
                self.record("term", path, start..end)?;
            }
            Entry::Comment(comment)
            | Entry::GroupComment(comment)
            | Entry::ResourceComment(comment) => self.visit_comment(comment, path)?,
            Entry::Junk { content } => {
                self.record("junk", path, content.range())?;
            }
        }
        Ok(())
    }

    fn visit_comment(
        &mut self,
        comment: &ast::Comment<SpannedSlice>,
        path: &str,
    ) -> Result<(), String> {
        for (index, line) in comment.content.iter().enumerate() {
            let line_path = format!("{path}.line[{index}]");
            let span = line.range();
            self.record("comment-line", &line_path, span.clone())?;
            if let Some(relative) = line.as_ref().find("@param") {
                self.record(
                    "param-annotation",
                    &line_path,
                    span.start + relative..span.end,
                )?;
            }
        }
        Ok(())
    }

    fn visit_attribute(
        &mut self,
        attribute: &ast::Attribute<SpannedSlice>,
        path: &str,
    ) -> Result<Range<usize>, String> {
        let id = self.record_identifier(&format!("{path}.id"), &attribute.id)?;
        let start = self.expand_ascii_left(id.start, b'.')?;
        let value = self.visit_pattern(&attribute.value, &format!("{path}.value"))?;
        let span = start..value.end;
        self.record("attribute", path, span.clone())?;
        Ok(span)
    }

    fn visit_pattern(
        &mut self,
        pattern: &Pattern<SpannedSlice>,
        path: &str,
    ) -> Result<Range<usize>, String> {
        let mut element_spans = Vec::with_capacity(pattern.elements.len());
        for (index, element) in pattern.elements.iter().enumerate() {
            let element_path = format!("{path}.element[{index}]");
            let span = match element {
                PatternElement::TextElement { value } => {
                    let span = value.range();
                    self.record("text", &element_path, span.clone())?;
                    span
                }
                PatternElement::Placeable { expression } => {
                    let inner =
                        self.visit_expression(expression, &format!("{element_path}.expression"))?;
                    let span = self.expand_braces(inner)?;
                    self.record("placeable", &element_path, span.clone())?;
                    span
                }
            };
            element_spans.push(span);
        }
        let first = element_spans
            .first()
            .ok_or_else(|| format!("empty pattern at {path}"))?;
        let last = element_spans
            .last()
            .ok_or_else(|| format!("empty pattern at {path}"))?;
        let span = first.start..last.end;
        self.record("pattern", path, span.clone())?;
        Ok(span)
    }

    fn visit_expression(
        &mut self,
        expression: &Expression<SpannedSlice>,
        path: &str,
    ) -> Result<Range<usize>, String> {
        match expression {
            Expression::Inline(inline) => self.visit_inline(inline, path),
            Expression::Select { selector, variants } => {
                let selector_span = self.visit_inline(selector, &format!("{path}.selector"))?;
                let mut end = selector_span.end;
                for (index, variant) in variants.iter().enumerate() {
                    let key_path = format!("{path}.variant[{index}].key");
                    let key = match &variant.key {
                        VariantKey::Identifier { name }
                        | VariantKey::NumberLiteral { value: name } => {
                            let span = name.range();
                            self.record("variant-key", &key_path, span.clone())?;
                            span
                        }
                    };
                    let mut start = self.expand_ascii_left(key.start, b'[')?;
                    if let Some(previous) = self.previous_non_whitespace(start)
                        && self.source.as_bytes()[previous] == b'*'
                    {
                        start = previous;
                    }
                    let value = self
                        .visit_pattern(&variant.value, &format!("{path}.variant[{index}].value"))?;
                    let variant_span = start..value.end;
                    self.record(
                        "variant",
                        &format!("{path}.variant[{index}]"),
                        variant_span.clone(),
                    )?;
                    end = variant_span.end;
                }
                let span = selector_span.start..end;
                self.record("select-expression", path, span.clone())?;
                Ok(span)
            }
        }
    }

    fn visit_inline(
        &mut self,
        expression: &InlineExpression<SpannedSlice>,
        path: &str,
    ) -> Result<Range<usize>, String> {
        let (kind, span) = match expression {
            InlineExpression::StringLiteral { value } => {
                let inner = value.range();
                let start = self.expand_ascii_left(inner.start, b'"')?;
                let end = self.expand_ascii_right(inner.end, b'"')?;
                ("string-literal", start..end)
            }
            InlineExpression::NumberLiteral { value } => ("number-literal", value.range()),
            InlineExpression::VariableReference { id } => {
                let id_span = self.record_identifier(&format!("{path}.id"), id)?;
                let start = self.expand_ascii_left(id_span.start, b'$')?;
                ("variable-reference", start..id_span.end)
            }
            InlineExpression::MessageReference { id, attribute } => {
                let id_span = self.record_identifier(&format!("{path}.id"), id)?;
                let end = if let Some(attribute) = attribute {
                    self.record_identifier(&format!("{path}.attribute"), attribute)?
                        .end
                } else {
                    id_span.end
                };
                ("message-reference", id_span.start..end)
            }
            InlineExpression::TermReference {
                id,
                attribute,
                arguments,
            } => {
                let id_span = self.record_identifier(&format!("{path}.id"), id)?;
                let start = self.expand_ascii_left(id_span.start, b'-')?;
                let mut end = if let Some(attribute) = attribute {
                    self.record_identifier(&format!("{path}.attribute"), attribute)?
                        .end
                } else {
                    id_span.end
                };
                if let Some(arguments) = arguments {
                    self.visit_arguments(arguments, &format!("{path}.arguments"))?;
                    end = self.call_end(end)?;
                }
                ("term-reference", start..end)
            }
            InlineExpression::FunctionReference { id, arguments } => {
                let id_span = self.record_identifier(&format!("{path}.id"), id)?;
                self.visit_arguments(arguments, &format!("{path}.arguments"))?;
                let end = self.call_end(id_span.end)?;
                ("function-reference", id_span.start..end)
            }
            InlineExpression::Placeable { expression } => {
                let inner = self.visit_expression(expression, &format!("{path}.expression"))?;
                ("nested-placeable", self.expand_braces(inner)?)
            }
        };
        self.record(kind, path, span.clone())?;
        Ok(span)
    }

    fn visit_arguments(
        &mut self,
        arguments: &CallArguments<SpannedSlice>,
        path: &str,
    ) -> Result<(), String> {
        for (index, positional) in arguments.positional.iter().enumerate() {
            self.visit_inline(positional, &format!("{path}.positional[{index}]"))?;
        }
        for (index, named) in arguments.named.iter().enumerate() {
            let named_path = format!("{path}.named[{index}]");
            let name = self.record_identifier(&format!("{named_path}.name"), &named.name)?;
            let value = self.visit_inline(&named.value, &format!("{named_path}.value"))?;
            let span = name.start..value.end;
            self.record("named-argument", &named_path, span)?;
        }
        Ok(())
    }

    fn expand_braces(&self, inner: Range<usize>) -> Result<Range<usize>, String> {
        let start = self.expand_ascii_left(inner.start, b'{')?;
        let end = self.expand_ascii_right(inner.end, b'}')?;
        Ok(start..end)
    }

    fn expand_ascii_left(&self, start: usize, expected: u8) -> Result<usize, String> {
        let position = self
            .previous_non_whitespace(start)
            .ok_or_else(|| format!("missing {} before byte {start}", char::from(expected)))?;
        ensure(
            self.source.as_bytes()[position] == expected,
            format!(
                "expected {} before byte {start}, found {:?}",
                char::from(expected),
                char::from(self.source.as_bytes()[position])
            ),
        )?;
        Ok(position)
    }

    fn expand_ascii_right(&self, end: usize, expected: u8) -> Result<usize, String> {
        let position = self
            .next_non_whitespace(end)
            .ok_or_else(|| format!("missing {} after byte {end}", char::from(expected)))?;
        ensure(
            self.source.as_bytes()[position] == expected,
            format!(
                "expected {} after byte {end}, found {:?}",
                char::from(expected),
                char::from(self.source.as_bytes()[position])
            ),
        )?;
        Ok(position + 1)
    }

    fn previous_non_whitespace(&self, mut position: usize) -> Option<usize> {
        let bytes = self.source.as_bytes();
        while position > 0 {
            position -= 1;
            if !matches!(bytes[position], b' ' | b'\r' | b'\n' | b'\t') {
                return Some(position);
            }
        }
        None
    }

    fn next_non_whitespace(&self, mut position: usize) -> Option<usize> {
        let bytes = self.source.as_bytes();
        while position < bytes.len() {
            if !matches!(bytes[position], b' ' | b'\r' | b'\n' | b'\t') {
                return Some(position);
            }
            position += 1;
        }
        None
    }

    fn call_end(&self, after_callee: usize) -> Result<usize, String> {
        let open = self
            .next_non_whitespace(after_callee)
            .ok_or_else(|| format!("missing call after byte {after_callee}"))?;
        ensure(
            self.source.as_bytes()[open] == b'(',
            format!("expected call parenthesis at byte {open}"),
        )?;
        self.matching_delimiter(open, b'(', b')')
            .map(|close| close + 1)
    }

    fn matching_delimiter(&self, open: usize, opening: u8, closing: u8) -> Result<usize, String> {
        let bytes = self.source.as_bytes();
        let mut depth = 0usize;
        let mut in_string = false;
        let mut escaped = false;
        for (position, byte) in bytes.iter().copied().enumerate().skip(open) {
            if in_string {
                if escaped {
                    escaped = false;
                } else if byte == b'\\' {
                    escaped = true;
                } else if byte == b'"' {
                    in_string = false;
                }
                continue;
            }
            if byte == b'"' {
                in_string = true;
            } else if byte == opening {
                depth += 1;
            } else if byte == closing {
                depth = depth
                    .checked_sub(1)
                    .ok_or_else(|| format!("unbalanced delimiter at byte {position}"))?;
                if depth == 0 {
                    return Ok(position);
                }
            }
        }
        Err(format!("unterminated delimiter beginning at byte {open}"))
    }
}

fn ensure(condition: bool, message: impl Into<String>) -> Result<(), String> {
    if condition {
        Ok(())
    } else {
        Err(message.into())
    }
}

fn find_record<'record>(
    records: &'record [SpanRecord],
    kind: &str,
    text: &str,
) -> Result<&'record SpanRecord, String> {
    let matches = records
        .iter()
        .filter(|record| record.kind == kind && record.text == text)
        .collect::<Vec<_>>();
    ensure(
        matches.len() == 1,
        format!(
            "expected one {kind} record for {text:?}, got {}; candidates: {:?}",
            matches.len(),
            records
                .iter()
                .filter(|record| record.kind == kind)
                .map(|record| record.text.as_str())
                .collect::<Vec<_>>()
        ),
    )?;
    Ok(matches[0])
}

fn main() -> Result<(), String> {
    let fixture_path = env::args_os()
        .nth(1)
        .map(PathBuf::from)
        .ok_or_else(|| "usage: citry-i18n-span-probe FIXTURE".to_owned())?;
    let source = fs::read_to_string(&fixture_path)
        .map_err(|error| format!("failed to read {}: {error}", fixture_path.display()))?;

    let resource = parser::parse(SpannedSlice::root(&source))
        .map_err(|(_, errors)| format!("valid fixture failed to parse: {errors:?}"))?;
    let plain_resource = parser::parse(source.as_str())
        .map_err(|(_, errors)| format!("plain parser failed: {errors:?}"))?;

    let mut index = SpanIndex::new(&source);
    index.visit_resource(&resource)?;

    let custom_serialized = serializer::serialize(&resource);
    let plain_serialized = serializer::serialize(&plain_resource);
    ensure(
        custom_serialized == plain_serialized,
        "custom Slice changed AST semantics or serialization",
    )?;

    let variable_name_records = index
        .records
        .iter()
        .filter(|record| record.kind == "variable-reference" && record.text == "$name")
        .collect::<Vec<_>>();
    ensure(
        variable_name_records.len() == 3,
        format!(
            "expected three distinct $name references, got {}",
            variable_name_records.len()
        ),
    )?;
    let distinct_name_starts = variable_name_records
        .windows(2)
        .all(|pair| pair[0].start != pair[1].start);
    ensure(distinct_name_starts, "repeated $name spans collapsed")?;

    let slot_records = index
        .records
        .iter()
        .filter(|record| record.kind == "variable-reference" && record.text == "$terms_link")
        .collect::<Vec<_>>();
    ensure(
        slot_records.len() == 2,
        "repeated Slot occurrences were not distinct",
    )?;

    let function = find_record(
        &index.records,
        "function-reference",
        "NUMBER($count, minimumFractionDigits: 2)",
    )?;
    let named_argument = find_record(&index.records, "named-argument", "minimumFractionDigits: 2")?;
    let nested = find_record(&index.records, "nested-placeable", "{ \"nested\\u2069\" }")?;
    let outer_nested = find_record(&index.records, "placeable", "{ { \"nested\\u2069\" } }")?;
    let term_call = find_record(&index.records, "term-reference", "-brand(case: \"short\")")?;
    let message_attribute = find_record(&index.records, "message-reference", "complex.aria-label")?;
    let select = index
        .records
        .iter()
        .find(|record| record.kind == "select-expression")
        .ok_or_else(|| "select-expression record is missing".to_owned())?;
    ensure(
        select.text.starts_with("$count ->")
            && select.text.contains("[0] Nothing")
            && select.text.contains("*[other]"),
        format!("select-expression span is incomplete: {:?}", select.text),
    )?;
    let annotation = find_record(
        &index.records,
        "param-annotation",
        "@param {Slot} $terms_link - Application-owned link.",
    )?;
    let trimmed = find_record(&index.records, "text", "trailing spaces")?;
    ensure(
        source.as_bytes().get(trimmed.end) == Some(&b' '),
        "trimmed text span did not stop before authored trailing spaces",
    )?;
    ensure(
        function.start < named_argument.start && named_argument.end < function.end,
        "named argument is not nested inside the function span",
    )?;
    ensure(
        outer_nested.start < nested.start && nested.end < outer_nested.end,
        "nested placeable ranges are not properly nested",
    )?;

    let unicode_text = index
        .records
        .iter()
        .find(|record| record.kind == "text" && record.text.starts_with("Přivítej"))
        .ok_or_else(|| "Unicode text record is missing".to_owned())?;
    ensure(
        unicode_text.end > source[..unicode_text.end].chars().count(),
        "fixture did not distinguish UTF-8 byte and code-point offsets",
    )?;

    let crlf_source = source.replace('\n', "\r\n");
    let crlf_resource = parser::parse(SpannedSlice::root(&crlf_source))
        .map_err(|(_, errors)| format!("CRLF fixture failed to parse: {errors:?}"))?;
    let mut crlf_index = SpanIndex::new(&crlf_source);
    crlf_index.visit_resource(&crlf_resource)?;
    find_record(
        &crlf_index.records,
        "function-reference",
        "NUMBER($count, minimumFractionDigits: 2)",
    )?;

    let duplicate_source = "broken = { FUNC(foo: \"a\", foo: \"b\") }\n";
    let (invalid_resource, parser_errors) = parser::parse(SpannedSlice::root(duplicate_source))
        .expect_err("duplicate named argument unexpectedly parsed");
    ensure(
        parser_errors.len() == 1,
        "expected one duplicate-argument error",
    )?;
    ensure(
        format!("{:?}", parser_errors[0].kind).contains("DuplicatedNamedArgument"),
        format!("unexpected parser error: {:?}", parser_errors[0]),
    )?;
    let junk = invalid_resource
        .body
        .iter()
        .find_map(|entry| match entry {
            Entry::Junk { content } => Some(content),
            _ => None,
        })
        .ok_or_else(|| "recovered AST did not contain Junk".to_owned())?;
    ensure(
        Some(junk.range()) == parser_errors[0].slice,
        "Junk leaf range did not match ParserError.slice",
    )?;

    let mut counts = BTreeMap::new();
    for record in &index.records {
        *counts.entry(record.kind.clone()).or_insert(0) += 1;
    }

    let samples = [
        ("function", function),
        ("named_argument", named_argument),
        ("nested_placeable", nested),
        ("outer_nested_placeable", outer_nested),
        ("term_call", term_call),
        ("message_attribute", message_attribute),
        ("select_expression", select),
        ("param_annotation", annotation),
        ("trimmed_text", trimmed),
    ]
    .into_iter()
    .map(|(name, record)| {
        (
            name.to_owned(),
            SampleSpan {
                start: record.start,
                end: record.end,
                text: record.text.clone(),
            },
        )
    })
    .collect();

    let gates = BTreeMap::from([
        ("composite_operation_spans", true),
        ("crlf_offsets", true),
        ("custom_slice_preserved_ast_semantics", true),
        ("duplicate_named_argument_semantics", true),
        ("error_and_junk_ranges", true),
        ("nested_placeable_spans", true),
        ("param_comment_spans", true),
        ("repeated_occurrences_distinct", true),
        ("trimmed_text_range", true),
        ("utf8_byte_offsets", true),
    ]);

    let evidence = ProbeEvidence {
        schema_version: 1,
        result: "PASS_BOUNDED",
        fluent_syntax: "0.12.0",
        gates,
        counts,
        samples,
        limitations: vec![
            "the prototype indexes the Fluent constructs used by the current Citry compiler design, not every legal Fluent AST shape",
            "composite spans are reconstructed by a Citry adapter around exact positioned leaves because upstream AST nodes remain spanless",
            "the probe does not benchmark large catalogs or concurrent compilation",
            "the probe does not establish an upstream API design or submit any upstream change",
        ],
    };

    println!(
        "{}",
        serde_json::to_string_pretty(&evidence)
            .map_err(|error| format!("failed to serialize evidence: {error}"))?
    );
    Ok(())
}
