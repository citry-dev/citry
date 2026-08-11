//! Two-pass orchestration for JavaScript and CSS embedded in Citry templates.
//!
//! This crate formats neither language, and deliberately so: the caller already
//! has a JavaScript and CSS formatter, and bundling another would mean a second
//! opinion about the same files. So the work is split. `prepare_embedded_format`
//! reports which regions want formatting and hands over their text;
//! the caller formats them however it likes; `finish_embedded_format` checks
//! what comes back and splices it in.
//!
//! The plan carries an id derived from the formatted source, which is what makes
//! the handoff safe across a process or editor boundary. A result computed
//! against a document that has since changed no longer matches its plan and is
//! rejected, rather than being pasted into text it was never formatted for.

use std::collections::{BTreeSet, HashMap};
use std::fmt::Write as _;
use std::ops::Range;

use citry_template_parser::parse_template;
use sha2::{Digest, Sha256};

use crate::diagnostic_catalog::{
    FORMAT_EMBEDDED_INTERPOLATION_UNSUPPORTED, FORMAT_EMBEDDED_LANGUAGE_UNSUPPORTED,
    FORMAT_EMBEDDED_SUPPRESSED, FORMAT_PROVIDER_UNAVAILABLE,
};
use crate::error::FormatError;
use crate::formatter;
use crate::newline::{detect_newline, normalize_to_lf};
use crate::source::{EmbeddedBodyModel, SourceModel};

/// Language requested from an external embedded formatter.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum EmbeddedLanguage {
    JavaScript,
    Css,
}

impl EmbeddedLanguage {
    /// Return the stable protocol spelling.
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::JavaScript => "javascript",
            Self::Css => "css",
        }
    }
}

/// Syntactic location owned by an embedded formatter request.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum EmbeddedRegionKind {
    ScriptBody,
    StyleBody,
}

impl EmbeddedRegionKind {
    /// Return the stable protocol spelling.
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::ScriptBody => "script-body",
            Self::StyleBody => "style-body",
        }
    }

    const fn forbidden_end_tag(self) -> &'static str {
        match self {
            Self::ScriptBody => "</script",
            Self::StyleBody => "</style",
        }
    }
}

/// One immutable JavaScript or CSS request in an embedded formatting plan.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct EmbeddedFormatRequest {
    id: String,
    language: EmbeddedLanguage,
    kind: EmbeddedRegionKind,
    source: String,
    virtual_source: String,
    byte_range: Range<usize>,
    base_indent: usize,
    newline: String,
}

impl EmbeddedFormatRequest {
    pub fn id(&self) -> &str {
        &self.id
    }

    pub const fn language(&self) -> EmbeddedLanguage {
        self.language
    }

    pub const fn kind(&self) -> EmbeddedRegionKind {
        self.kind
    }

    /// Return the exact source bytes owned by this region.
    pub fn source(&self) -> &str {
        &self.source
    }

    /// Return the standalone provider document for this region.
    pub fn virtual_source(&self) -> &str {
        &self.virtual_source
    }

    /// Return the half-open UTF-8 byte range in the plan's formatted source.
    pub fn byte_range(&self) -> Range<usize> {
        self.byte_range.clone()
    }

    /// Return the absolute content indentation used when composing output.
    pub const fn base_indent(&self) -> usize {
        self.base_indent
    }

    pub fn newline(&self) -> &str {
        &self.newline
    }
}

/// A non-fatal embedded-formatting capability or provider notice.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct EmbeddedFormatNotice {
    code: &'static str,
    message: String,
    region_id: Option<String>,
    language: Option<EmbeddedLanguage>,
}

impl EmbeddedFormatNotice {
    pub const fn code(&self) -> &'static str {
        self.code
    }

    pub fn message(&self) -> &str {
        &self.message
    }

    pub fn region_id(&self) -> Option<&str> {
        self.region_id.as_deref()
    }

    pub const fn language(&self) -> Option<EmbeddedLanguage> {
        self.language
    }
}

/// Opaque source-bound plan prepared before async provider delegation.
#[derive(Clone, Debug)]
pub struct EmbeddedFormatPlan {
    id: String,
    formatted_source: String,
    requests: Vec<EmbeddedFormatRequest>,
    notices: Vec<EmbeddedFormatNotice>,
}

impl EmbeddedFormatPlan {
    pub fn id(&self) -> &str {
        &self.id
    }

    pub fn formatted_source(&self) -> &str {
        &self.formatted_source
    }

    pub fn requests(&self) -> &[EmbeddedFormatRequest] {
        &self.requests
    }

    pub fn notices(&self) -> &[EmbeddedFormatNotice] {
        &self.notices
    }
}

/// One provider response, echoing the plan and region identities.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum EmbeddedFormatResult {
    Formatted {
        plan_id: String,
        region_id: String,
        text: String,
        provider: Option<String>,
    },
    Unchanged {
        plan_id: String,
        region_id: String,
    },
    Unavailable {
        plan_id: String,
        region_id: String,
        message: String,
    },
    Error {
        plan_id: String,
        region_id: String,
        message: String,
    },
}

impl EmbeddedFormatResult {
    pub fn formatted(
        plan_id: impl Into<String>,
        region_id: impl Into<String>,
        text: impl Into<String>,
        provider: Option<impl Into<String>>,
    ) -> Self {
        Self::Formatted {
            plan_id: plan_id.into(),
            region_id: region_id.into(),
            text: text.into(),
            provider: provider.map(Into::into),
        }
    }

    pub fn unchanged(plan_id: impl Into<String>, region_id: impl Into<String>) -> Self {
        Self::Unchanged {
            plan_id: plan_id.into(),
            region_id: region_id.into(),
        }
    }

    pub fn unavailable(
        plan_id: impl Into<String>,
        region_id: impl Into<String>,
        message: impl Into<String>,
    ) -> Self {
        Self::Unavailable {
            plan_id: plan_id.into(),
            region_id: region_id.into(),
            message: message.into(),
        }
    }

    pub fn error(
        plan_id: impl Into<String>,
        region_id: impl Into<String>,
        message: impl Into<String>,
    ) -> Self {
        Self::Error {
            plan_id: plan_id.into(),
            region_id: region_id.into(),
            message: message.into(),
        }
    }

    fn plan_id(&self) -> &str {
        match self {
            Self::Formatted { plan_id, .. }
            | Self::Unchanged { plan_id, .. }
            | Self::Unavailable { plan_id, .. }
            | Self::Error { plan_id, .. } => plan_id,
        }
    }

    fn region_id(&self) -> &str {
        match self {
            Self::Formatted { region_id, .. }
            | Self::Unchanged { region_id, .. }
            | Self::Unavailable { region_id, .. }
            | Self::Error { region_id, .. } => region_id,
        }
    }
}

/// Atomically composed template plus notices and proven provider identities.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct EmbeddedFormatOutcome {
    source: String,
    notices: Vec<EmbeddedFormatNotice>,
    providers: Vec<String>,
}

impl EmbeddedFormatOutcome {
    pub fn source(&self) -> &str {
        &self.source
    }

    pub fn notices(&self) -> &[EmbeddedFormatNotice] {
        &self.notices
    }

    pub fn providers(&self) -> &[String] {
        &self.providers
    }
}

/// Prepare deterministic M2 source and its safe expression-free JS/CSS bodies.
pub fn prepare_embedded_format(source: &str) -> Result<EmbeddedFormatPlan, FormatError> {
    // Structural formatting runs first, so the offsets in the plan refer to the
    // text the caller will splice into. Preparing against the unformatted source
    // would hand back positions that move the moment anything else is applied.
    let formatted_source = formatter::format(source)?;
    let template = parse_template(&formatted_source, None, None)
        .map_err(|error| FormatError::from_parse(&error))?;
    let model = SourceModel::build(&formatted_source, &template)?;
    let id = plan_id(&formatted_source);
    let newline = detect_newline(&formatted_source).to_string();
    let mut requests = Vec::new();
    let mut notices = Vec::new();

    // A region that cannot be handed over produces a notice rather than an
    // error: the rest of the document still formats, and the caller can tell the
    // author which blocks were left alone and why.
    for (index, body) in model.embedded_bodies().iter().enumerate() {
        let region_id = format!("{}-{index}", body.kind.as_str());
        if body_is_protected(body, &model) {
            notices.push(notice(
                FORMAT_EMBEDDED_SUPPRESSED,
                "embedded body is protected by a formatter directive",
                &region_id,
                body.language,
            ));
            continue;
        }
        let Some(language) = body.language else {
            notices.push(notice(
                FORMAT_EMBEDDED_LANGUAGE_UNSUPPORTED,
                "embedded body has an alternate or dynamic language",
                &region_id,
                None,
            ));
            continue;
        };
        let exact = formatted_source
            .get(body.span.start..body.span.end)
            .ok_or_else(|| {
                FormatError::invalid_span(
                    "embedded body is not valid UTF-8 source",
                    body.span.start..body.span.end,
                )
            })?;
        // A body holding `{{ ... }}` or `{# ... #}` is not valid standalone
        // JavaScript or CSS, so a formatter for those languages would either
        // reject it or mangle it. The textual check backs up the parsed flag,
        // since the sequence can appear in places the parse did not mark.
        if body.has_interpolation || exact.contains("{{") || exact.contains("{#") {
            notices.push(notice(
                FORMAT_EMBEDDED_INTERPOLATION_UNSUPPORTED,
                "embedded body contains Citry interpolation or comment syntax without a context-safe placeholder adapter",
                &region_id,
                Some(language),
            ));
            continue;
        }
        if exact.chars().all(is_embedded_layout_whitespace) {
            continue;
        }
        if contains_multiline_literal(exact, language) {
            notices.push(notice(
                FORMAT_EMBEDDED_LANGUAGE_UNSUPPORTED,
                "embedded body contains a multiline whitespace-sensitive token that cannot be reindented safely",
                &region_id,
                Some(language),
            ));
            continue;
        }
        let standalone = standalone_source(exact);
        if starts_with_lexical_sentinel(&standalone, language) {
            notices.push(notice(
                FORMAT_EMBEDDED_LANGUAGE_UNSUPPORTED,
                "embedded body starts with a position-sensitive language sentinel that cannot be reframed safely",
                &region_id,
                Some(language),
            ));
            continue;
        }
        requests.push(EmbeddedFormatRequest {
            id: region_id,
            language,
            kind: body.kind,
            source: exact.to_string(),
            virtual_source: standalone,
            byte_range: body.span.start..body.span.end,
            base_indent: body.tag_column + 2,
            newline: newline.clone(),
        });
    }

    Ok(EmbeddedFormatPlan {
        id,
        formatted_source,
        requests,
        notices,
    })
}

/// Validate and atomically compose all provider results for a prepared plan.
///
/// Atomically because a document with some regions formatted and others not is
/// worse than one left alone: nothing is spliced until every result has been
/// checked. The four checks below are all about identity rather than content,
/// since a result that belongs to the wrong document will still look like
/// perfectly good JavaScript.
pub fn finish_embedded_format(
    plan: &EmbeddedFormatPlan,
    results: &[EmbeddedFormatResult],
) -> Result<EmbeddedFormatOutcome, FormatError> {
    let requests = plan
        .requests
        .iter()
        .map(|request| (request.id.as_str(), request))
        .collect::<HashMap<_, _>>();
    // Requiring an exact count catches a caller that dropped a region as well as
    // one that invented an extra.
    if results.len() != requests.len() {
        return Err(provider_error(format!(
            "embedded result count {} does not match request count {}",
            results.len(),
            requests.len()
        )));
    }

    let mut by_id = HashMap::new();
    for result in results {
        if result.plan_id() != plan.id {
            return Err(provider_error(
                "embedded result belongs to a different plan",
            ));
        }
        if !requests.contains_key(result.region_id()) {
            return Err(provider_error(format!(
                "unknown embedded region ID {:?}",
                result.region_id()
            )));
        }
        if by_id.insert(result.region_id(), result).is_some() {
            return Err(provider_error(format!(
                "duplicate embedded result for {:?}",
                result.region_id()
            )));
        }
    }

    let mut replacements = Vec::new();
    let mut notices = plan.notices.clone();
    let mut providers = BTreeSet::new();
    for request in &plan.requests {
        let result = by_id
            .get(request.id.as_str())
            .copied()
            .ok_or_else(|| provider_error(format!("missing result for {:?}", request.id)))?;
        match result {
            EmbeddedFormatResult::Formatted { text, provider, .. } => {
                if contains_ascii_case_insensitive(text, request.kind.forbidden_end_tag()) {
                    return Err(FormatError::provider(
                        format!(
                            "provider output for {:?} contains forbidden delimiter {}",
                            request.id,
                            request.kind.forbidden_end_tag()
                        ),
                        Some(request.byte_range.clone()),
                    ));
                }
                if let Some(delimiter) = ["{{", "{#"]
                    .into_iter()
                    .find(|delimiter| text.contains(delimiter))
                {
                    return Err(FormatError::provider(
                        format!(
                            "provider output for {:?} contains forbidden Citry delimiter {delimiter}",
                            request.id
                        ),
                        Some(request.byte_range.clone()),
                    ));
                }
                let standalone = standalone_source(text);
                if contains_multiline_literal(text, request.language)
                    || starts_with_lexical_sentinel(&standalone, request.language)
                {
                    return Err(FormatError::provider(
                        format!(
                            "provider output for {:?} contains language bytes that cannot be reframed safely",
                            request.id
                        ),
                        Some(request.byte_range.clone()),
                    ));
                }
                if let Some(provider) = provider {
                    providers.insert(provider.clone());
                }
                replacements.push((
                    request.byte_range.clone(),
                    compose_body(text, request.base_indent, &request.newline),
                ));
            }
            EmbeddedFormatResult::Unchanged { .. } => {}
            EmbeddedFormatResult::Unavailable { message, .. } => notices.push(notice(
                FORMAT_PROVIDER_UNAVAILABLE,
                message,
                &request.id,
                Some(request.language),
            )),
            EmbeddedFormatResult::Error { message, .. } => {
                return Err(FormatError::provider(
                    format!("provider failed for {:?}: {message}", request.id),
                    Some(request.byte_range.clone()),
                ));
            }
        }
    }

    replacements.sort_by_key(|(range, _)| range.start);
    for pair in replacements.windows(2) {
        if pair[0].0.end > pair[1].0.start {
            return Err(provider_error("embedded replacement ranges overlap"));
        }
    }
    let mut candidate = plan.formatted_source.clone();
    for (range, replacement) in replacements.into_iter().rev() {
        candidate.replace_range(range, &replacement);
    }
    let verified = formatter::format(&candidate).map_err(|error| {
        FormatError::provider(
            format!("composed embedded output failed Citry validation: {error}"),
            error.range(),
        )
    })?;
    if verified != candidate {
        return Err(provider_error(
            "composed embedded output changed the stable outer Citry layout",
        ));
    }

    Ok(EmbeddedFormatOutcome {
        source: candidate,
        notices,
        providers: providers.into_iter().collect(),
    })
}

fn plan_id(source: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(b"citry-embedded-format-plan-v1\0");
    hasher.update(source.as_bytes());
    let mut result = String::from("sha256:");
    for byte in hasher.finalize() {
        write!(&mut result, "{byte:02x}").expect("writing to a String cannot fail");
    }
    result
}

fn body_is_protected(body: &EmbeddedBodyModel, model: &SourceModel) -> bool {
    model
        .protected
        .iter()
        .any(|range| body.span.start < range.span.end && range.span.start < body.span.end)
}

fn standalone_source(source: &str) -> String {
    let normalized = normalize_to_lf(source);
    let mut lines = normalized.split('\n').collect::<Vec<_>>();
    while lines
        .first()
        .is_some_and(|line| line_is_layout_whitespace(line))
    {
        lines.remove(0);
    }
    while lines
        .last()
        .is_some_and(|line| line_is_layout_whitespace(line))
    {
        lines.pop();
    }
    let indent = lines
        .iter()
        .filter(|line| !line_is_layout_whitespace(line))
        .map(|line| line.len() - line.trim_start_matches([' ', '\t']).len())
        .min()
        .unwrap_or(0);
    lines
        .iter()
        .map(|line| line.get(indent..).unwrap_or(line))
        .collect::<Vec<_>>()
        .join("\n")
}

fn line_is_layout_whitespace(line: &str) -> bool {
    line.chars().all(is_embedded_layout_whitespace)
}

const fn is_embedded_layout_whitespace(character: char) -> bool {
    matches!(
        character,
        '\u{0009}' | '\u{000a}' | '\u{000c}' | '\u{000d}' | ' '
    )
}

fn contains_multiline_literal(source: &str, language: EmbeddedLanguage) -> bool {
    let characters = source.chars().collect::<Vec<_>>();
    match language {
        EmbeddedLanguage::JavaScript => contains_multiline_javascript_token(&characters),
        EmbeddedLanguage::Css => contains_multiline_css_token(&characters),
    }
}

fn contains_multiline_javascript_token(characters: &[char]) -> bool {
    let mut index = 0;
    let mut regex_allowed = true;
    let mut property_identifier = false;
    while index < characters.len() {
        if characters[index] == '/' && characters.get(index + 1) == Some(&'*') {
            index += 2;
            while index + 1 < characters.len()
                && !(characters[index] == '*' && characters[index + 1] == '/')
            {
                if is_javascript_line_terminator(characters[index]) {
                    return true;
                }
                index += 1;
            }
            index = (index + 2).min(characters.len());
            continue;
        }
        if characters[index] == '/' && characters.get(index + 1) == Some(&'/') {
            index += 2;
            while index < characters.len() && !is_javascript_line_terminator(characters[index]) {
                index += 1;
            }
            continue;
        }
        let delimiter = characters[index];
        if matches!(delimiter, '\'' | '"' | '`') {
            if quoted_token_crosses_line(characters, &mut index, delimiter, true) {
                return true;
            }
            regex_allowed = false;
            property_identifier = false;
            continue;
        }
        if delimiter == '/' && regex_allowed {
            skip_javascript_regex(characters, &mut index);
            regex_allowed = false;
            property_identifier = false;
            continue;
        }
        if delimiter == '/'
            && characters[index + 1..]
                .iter()
                .take_while(|character| !is_javascript_line_terminator(**character))
                .any(|character| matches!(character, '\'' | '"' | '`'))
        {
            return true;
        }
        if delimiter.is_ascii_whitespace() || is_javascript_line_terminator(delimiter) {
            index += 1;
            continue;
        }
        if delimiter.is_ascii_alphabetic() || matches!(delimiter, '_' | '$') {
            let start = index;
            index += 1;
            while index < characters.len()
                && (characters[index].is_ascii_alphanumeric()
                    || matches!(characters[index], '_' | '$'))
            {
                index += 1;
            }
            let word = characters[start..index].iter().collect::<String>();
            regex_allowed = !property_identifier
                && matches!(
                    word.as_str(),
                    "case"
                        | "delete"
                        | "else"
                        | "in"
                        | "instanceof"
                        | "new"
                        | "return"
                        | "throw"
                        | "typeof"
                        | "void"
                );
            property_identifier = false;
            continue;
        }
        if delimiter.is_ascii_digit() {
            index += 1;
            while index < characters.len()
                && (characters[index].is_ascii_alphanumeric()
                    || matches!(characters[index], '.' | '_'))
            {
                index += 1;
            }
            regex_allowed = false;
            property_identifier = false;
            continue;
        }
        if matches!(delimiter, '+' | '-') && characters.get(index + 1) == Some(&delimiter) {
            index += 2;
            property_identifier = false;
            continue;
        }
        regex_allowed = matches!(
            delimiter,
            '(' | '['
                | '{'
                | ','
                | ';'
                | ':'
                | '?'
                | '!'
                | '='
                | '+'
                | '-'
                | '/'
                | '*'
                | '%'
                | '&'
                | '|'
                | '^'
                | '~'
        );
        if matches!(delimiter, ')' | ']' | '}') {
            regex_allowed = false;
        }
        property_identifier = delimiter == '.' || (delimiter == '#' && property_identifier);
        index += 1;
    }
    false
}

fn contains_multiline_css_token(characters: &[char]) -> bool {
    let mut index = 0;
    while index < characters.len() {
        if characters[index] == '/' && characters.get(index + 1) == Some(&'*') {
            index += 2;
            while index + 1 < characters.len()
                && !(characters[index] == '*' && characters[index + 1] == '/')
            {
                if matches!(characters[index], '\r' | '\n') {
                    return true;
                }
                index += 1;
            }
            index = (index + 2).min(characters.len());
            continue;
        }
        let delimiter = characters[index];
        if delimiter == '\\' {
            index += 1;
            if index < characters.len() {
                if matches!(characters[index], '\r' | '\n') {
                    return true;
                }
                index += 1;
            }
            continue;
        }
        if matches!(delimiter, '\'' | '"')
            && quoted_token_crosses_line(characters, &mut index, delimiter, false)
        {
            return true;
        }
        if !matches!(delimiter, '\'' | '"') {
            index += 1;
        }
    }
    false
}

fn quoted_token_crosses_line(
    characters: &[char],
    index: &mut usize,
    delimiter: char,
    javascript: bool,
) -> bool {
    *index += 1;
    while *index < characters.len() {
        let character = characters[*index];
        let is_line = matches!(character, '\r' | '\n')
            || (javascript && matches!(character, '\u{2028}' | '\u{2029}'));
        if is_line {
            return true;
        }
        if character == '\\' {
            *index += 1;
            if *index < characters.len() {
                let escaped = characters[*index];
                if matches!(escaped, '\r' | '\n')
                    || (javascript && matches!(escaped, '\u{2028}' | '\u{2029}'))
                {
                    return true;
                }
                *index += 1;
            }
            continue;
        }
        if delimiter == '`' && character == '$' && characters.get(*index + 1) == Some(&'{') {
            *index += 2;
            if javascript_template_substitution_is_unsafe(characters, index) {
                return true;
            }
            continue;
        }
        *index += 1;
        if character == delimiter {
            break;
        }
    }
    false
}

fn javascript_template_substitution_is_unsafe(characters: &[char], index: &mut usize) -> bool {
    let mut brace_depth = 1;
    let mut regex_allowed = true;
    let mut property_identifier = false;
    while *index < characters.len() {
        let character = characters[*index];
        if is_javascript_line_terminator(character) {
            return true;
        }
        if character == '/' && characters.get(*index + 1) == Some(&'*') {
            *index += 2;
            while *index + 1 < characters.len()
                && !(characters[*index] == '*' && characters[*index + 1] == '/')
            {
                if is_javascript_line_terminator(characters[*index]) {
                    return true;
                }
                *index += 1;
            }
            *index = (*index + 2).min(characters.len());
            continue;
        }
        if character == '/' && characters.get(*index + 1) == Some(&'/') {
            return true;
        }
        if matches!(character, '\'' | '"') {
            if quoted_token_crosses_line(characters, index, character, true) {
                return true;
            }
            regex_allowed = false;
            property_identifier = false;
            continue;
        }
        // Nested templates require recursively tracking their raw segments. M3
        // conservatively preserves the complete body instead.
        if character == '`' {
            return true;
        }
        if character == '/' && regex_allowed {
            skip_javascript_regex(characters, index);
            regex_allowed = false;
            property_identifier = false;
            continue;
        }
        if character == '/'
            && characters[*index + 1..]
                .iter()
                .take_while(|character| !is_javascript_line_terminator(**character))
                .any(|character| matches!(character, '\'' | '"' | '`'))
        {
            return true;
        }
        if character.is_ascii_whitespace() {
            *index += 1;
            continue;
        }
        if character.is_ascii_alphabetic() || matches!(character, '_' | '$') {
            let start = *index;
            *index += 1;
            while *index < characters.len()
                && (characters[*index].is_ascii_alphanumeric()
                    || matches!(characters[*index], '_' | '$'))
            {
                *index += 1;
            }
            let word = characters[start..*index].iter().collect::<String>();
            regex_allowed = !property_identifier
                && matches!(
                    word.as_str(),
                    "case"
                        | "delete"
                        | "else"
                        | "in"
                        | "instanceof"
                        | "new"
                        | "return"
                        | "throw"
                        | "typeof"
                        | "void"
                );
            property_identifier = false;
            continue;
        }
        if character.is_ascii_digit() {
            *index += 1;
            while *index < characters.len()
                && (characters[*index].is_ascii_alphanumeric()
                    || matches!(characters[*index], '.' | '_'))
            {
                *index += 1;
            }
            regex_allowed = false;
            property_identifier = false;
            continue;
        }
        if character == '{' {
            brace_depth += 1;
            regex_allowed = true;
            property_identifier = false;
            *index += 1;
            continue;
        }
        if character == '}' {
            brace_depth -= 1;
            *index += 1;
            if brace_depth == 0 {
                return false;
            }
            regex_allowed = false;
            property_identifier = false;
            continue;
        }
        if matches!(character, '+' | '-') && characters.get(*index + 1) == Some(&character) {
            *index += 2;
            property_identifier = false;
            continue;
        }
        regex_allowed = matches!(
            character,
            '(' | '['
                | ','
                | ';'
                | ':'
                | '?'
                | '!'
                | '='
                | '+'
                | '-'
                | '/'
                | '*'
                | '%'
                | '&'
                | '|'
                | '^'
                | '~'
        );
        if matches!(character, ')' | ']') {
            regex_allowed = false;
        }
        property_identifier = character == '.' || (character == '#' && property_identifier);
        *index += 1;
    }
    true
}

fn skip_javascript_regex(characters: &[char], index: &mut usize) {
    *index += 1;
    let mut character_class = false;
    while *index < characters.len() {
        let character = characters[*index];
        if is_javascript_line_terminator(character) {
            return;
        }
        if character == '\\' {
            *index = (*index + 2).min(characters.len());
            continue;
        }
        if character == '[' {
            character_class = true;
        } else if character == ']' {
            character_class = false;
        } else if character == '/' && !character_class {
            *index += 1;
            while *index < characters.len() && characters[*index].is_ascii_alphabetic() {
                *index += 1;
            }
            return;
        }
        *index += 1;
    }
}

const fn is_javascript_line_terminator(character: char) -> bool {
    matches!(character, '\r' | '\n' | '\u{2028}' | '\u{2029}')
}

fn starts_with_lexical_sentinel(source: &str, language: EmbeddedLanguage) -> bool {
    if source.starts_with('\u{feff}') {
        return true;
    }
    match language {
        EmbeddedLanguage::JavaScript => source.starts_with("#!"),
        EmbeddedLanguage::Css => source
            .get(.."@charset".len())
            .is_some_and(|prefix| prefix.eq_ignore_ascii_case("@charset")),
    }
}

fn compose_body(source: &str, base_indent: usize, newline: &str) -> String {
    let standalone = standalone_source(source);
    if standalone.is_empty() {
        return String::new();
    }
    let content_indent = " ".repeat(base_indent);
    let closing_indent = " ".repeat(base_indent.saturating_sub(2));
    let content = standalone
        .split('\n')
        .map(|line| format!("{content_indent}{line}"))
        .collect::<Vec<_>>()
        .join(newline);
    format!("{newline}{content}{newline}{closing_indent}")
}

fn contains_ascii_case_insensitive(source: &str, needle: &str) -> bool {
    source
        .as_bytes()
        .windows(needle.len())
        .any(|window| window.eq_ignore_ascii_case(needle.as_bytes()))
}

fn notice(
    code: &'static str,
    message: impl Into<String>,
    region_id: &str,
    language: Option<EmbeddedLanguage>,
) -> EmbeddedFormatNotice {
    EmbeddedFormatNotice {
        code,
        message: message.into(),
        region_id: Some(region_id.to_string()),
        language,
    }
}

fn provider_error(message: impl Into<String>) -> FormatError {
    FormatError::provider(message, None)
}
