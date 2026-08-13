#![allow(clippy::result_large_err)]

use std::collections::{BTreeMap, BTreeSet};
use std::ops::Range;
use std::sync::{Arc, Mutex};

use fluent_bundle::concurrent::FluentBundle;
use fluent_bundle::{FluentArgs, FluentResource, FluentValue};
use fluent_syntax::ast::{
    self, CallArguments, Entry, Expression, InlineExpression, Pattern, PatternElement, VariantKey,
};
use fluent_syntax::parser::Slice;
use icu::decimal::input::Decimal;
use icu::locale::Locale;
use icu::plurals::{PluralCategory, PluralRules};
use icu_locale::LocaleCanonicalizer;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use unic_langid::LanguageIdentifier;

use crate::format::{FormatRegistry, FormatRegistrySpec};

/// Version of the first production catalog artifact.
pub const SCHEMA_VERSION: u32 = 1;
const FSI: &str = "\u{2068}";
const PDI: &str = "\u{2069}";
const BIDI_CONTROLS: [char; 12] = [
    '\u{061c}', '\u{200e}', '\u{200f}', '\u{202a}', '\u{202b}', '\u{202c}', '\u{202d}', '\u{202e}',
    '\u{2066}', '\u{2067}', '\u{2068}', '\u{2069}',
];
const BIDI_PARAGRAPH_BOUNDARIES: [char; 7] = [
    '\n', '\r', '\u{001c}', '\u{001d}', '\u{001e}', '\u{0085}', '\u{2029}',
];

/// One stable compiler or runtime diagnostic.
#[derive(Debug, Clone, Serialize)]
pub struct Failure {
    code: &'static str,
    message: String,
    path: Option<String>,
    start: Option<usize>,
    end: Option<usize>,
    line: Option<usize>,
    column: Option<usize>,
    message_id: Option<String>,
    related: Vec<DiagnosticRelated>,
}

impl Failure {
    pub(crate) fn new(code: &'static str, message: impl Into<String>) -> Self {
        Self {
            code,
            message: message.into(),
            path: None,
            start: None,
            end: None,
            line: None,
            column: None,
            message_id: None,
            related: vec![],
        }
    }

    fn at(mut self, path: &str, source: &str, start: usize, end: usize) -> Self {
        let (line, column) = line_column(source, start);
        self.path = Some(path.to_owned());
        self.start = Some(start);
        self.end = Some(end);
        self.line = Some(line);
        self.column = Some(column);
        self
    }

    fn for_message(mut self, message_id: &str) -> Self {
        self.message_id = Some(message_id.to_owned());
        self
    }

    fn with_related(mut self, related: DiagnosticRelated) -> Self {
        self.related.push(related);
        self
    }

    /// Stable machine-readable diagnostic code.
    pub fn code(&self) -> &'static str {
        self.code
    }

    /// JSON record used by host bindings without re-parsing display text.
    pub fn diagnostic_json(&self) -> String {
        serde_json::to_string(self).unwrap_or_else(|_| {
            format!(
                r#"{{"code":"I18N_INTERNAL_JSON","message":{:?}}}"#,
                self.message
            )
        })
    }
}

impl std::fmt::Display for Failure {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter.write_str(&self.message)
    }
}

impl std::error::Error for Failure {}

#[derive(Debug, Clone, Serialize)]
struct DiagnosticRelated {
    message: String,
    path: String,
    start: usize,
    end: usize,
    line: usize,
    column: usize,
}

fn validate_fallbacks(fallbacks: &BTreeMap<String, Vec<String>>) -> Result<(), Failure> {
    fn visit(
        locale: &str,
        fallbacks: &BTreeMap<String, Vec<String>>,
        visiting: &mut BTreeSet<String>,
        visited: &mut BTreeSet<String>,
    ) -> Result<(), Failure> {
        if !visiting.insert(locale.to_owned()) {
            return Err(Failure::new(
                "I18N_FALLBACK_CYCLE",
                format!("fallback graph contains a cycle through {locale:?}"),
            ));
        }
        if visited.contains(locale) {
            visiting.remove(locale);
            return Ok(());
        }
        for next in fallbacks.get(locale).into_iter().flatten() {
            visit(next, fallbacks, visiting, visited)?;
        }
        visiting.remove(locale);
        visited.insert(locale.to_owned());
        Ok(())
    }

    let mut visited = BTreeSet::new();
    for locale in fallbacks.keys() {
        visit(locale, fallbacks, &mut BTreeSet::new(), &mut visited)?;
    }
    Ok(())
}

fn validate_locale(value: &str, source: &str) -> Result<(), Failure> {
    let mut locale: Locale = value.parse().map_err(|error| {
        Failure::new(
            "I18N_LOCALE_INVALID",
            format!("{source} contains invalid locale {value:?}: {error}"),
        )
    })?;
    LocaleCanonicalizer::new_extended().canonicalize(&mut locale);
    let canonical = locale.to_string();
    if canonical != value {
        return Err(Failure::new(
            "I18N_LOCALE_NONCANONICAL",
            format!("{source} must use canonical locale {canonical:?}, got {value:?}"),
        ));
    }
    Ok(())
}

fn validate_request_locales(
    request: &CompileRequest,
    linked_catalogs: &[LoadedCatalog],
) -> Result<(), Failure> {
    let mut active = BTreeSet::new();
    let mut known = BTreeSet::new();
    for locale in &request.active_locales {
        validate_locale(locale, "active_locales")?;
        if !active.insert(locale) {
            return Err(Failure::new(
                "I18N_ACTIVE_LOCALE_DUPLICATE",
                format!("active locale {locale:?} is declared more than once"),
            ));
        }
        known.insert(locale);
    }
    for package in &request.packages {
        validate_locale(
            &package.source_locale,
            &format!("package {:?} source_locale", package.name),
        )?;
        known.insert(&package.source_locale);
    }
    for catalog in request
        .catalogs
        .iter()
        .chain(linked_catalogs.iter().map(|catalog| &catalog.spec))
    {
        validate_locale(
            &catalog.locale,
            &format!("catalog {:?} locale", catalog.path),
        )?;
        known.insert(&catalog.locale);
    }
    for (locale, parents) in &request.fallbacks {
        validate_locale(locale, "fallback locale")?;
        if !known.contains(locale) {
            return Err(Failure::new(
                "I18N_FALLBACK_UNKNOWN_LOCALE",
                format!("fallback graph names undeclared locale {locale:?}"),
            ));
        }
        let mut seen = BTreeSet::new();
        for parent in parents {
            validate_locale(parent, &format!("fallbacks[{locale:?}]"))?;
            if !known.contains(parent) {
                return Err(Failure::new(
                    "I18N_FALLBACK_UNKNOWN_LOCALE",
                    format!("fallback graph names undeclared locale {parent:?}"),
                ));
            }
            if !seen.insert(parent) {
                return Err(Failure::new(
                    "I18N_FALLBACK_DUPLICATE",
                    format!("fallback {parent:?} is repeated for {locale:?}"),
                ));
            }
        }
    }
    Ok(())
}

fn diagnostic_layout(source: &str) -> String {
    source
        .chars()
        .map(|character| match character {
            '\r' | '\n' => character,
            _ => match character.len_utf8() {
                1 => ' ',
                2 => 'é',
                3 => '€',
                4 => '𐀀',
                _ => unreachable!("UTF-8 scalars use at most four bytes"),
            },
        })
        .collect()
}

fn link_unit_revision(
    packages: &[PackageSpec],
    catalogs: &[LinkCatalog],
) -> Result<String, Failure> {
    serde_json::to_string(&(env!("CARGO_PKG_VERSION"), packages, catalogs))
        .map(|payload| digest_text(&payload))
        .map_err(|error| Failure::new("I18N_LINK_UNIT_JSON", error.to_string()))
}

fn validate_link_unit(unit: &LinkUnit) -> Result<(), Failure> {
    if unit.schema_version != SCHEMA_VERSION {
        return Err(Failure::new(
            "I18N_LINK_UNIT_SCHEMA",
            format!(
                "expected link-unit schema {SCHEMA_VERSION}, got {}",
                unit.schema_version
            ),
        ));
    }
    if unit.compiler_version != env!("CARGO_PKG_VERSION") {
        return Err(Failure::new(
            "I18N_LINK_UNIT_COMPILER",
            format!(
                "link unit uses compiler {:?}, expected {:?}",
                unit.compiler_version,
                env!("CARGO_PKG_VERSION")
            ),
        ));
    }
    if unit.revision != link_unit_revision(&unit.packages, &unit.catalogs)? {
        return Err(Failure::new(
            "I18N_LINK_UNIT_REVISION",
            "link-unit semantic revision does not match its contents",
        ));
    }
    for catalog in &unit.catalogs {
        if catalog.source_digest != catalog.parsed.digest {
            return Err(Failure::new(
                "I18N_LINK_UNIT_SOURCE_DIGEST",
                format!(
                    "link catalog {:?} has inconsistent source digests",
                    catalog.path
                ),
            ));
        }
        for (message_id, message) in &catalog.parsed.messages {
            if text(&message.id.name) != message_id {
                return Err(Failure::new(
                    "I18N_LINK_UNIT_MESSAGE_ID",
                    format!(
                        "link catalog {:?} has inconsistent message metadata",
                        catalog.path
                    ),
                ));
            }
        }
        for (term_id, term) in &catalog.parsed.terms {
            if text(&term.id.name) != term_id {
                return Err(Failure::new(
                    "I18N_LINK_UNIT_TERM_ID",
                    format!(
                        "link catalog {:?} has inconsistent term metadata",
                        catalog.path
                    ),
                ));
            }
        }
        validate_link_catalog_patterns(catalog)?;
    }
    Ok(())
}

fn validate_link_catalog_patterns(catalog: &LinkCatalog) -> Result<(), Failure> {
    let spec = CatalogSpec {
        path: catalog.path.clone(),
        package: catalog.package.clone(),
        layer: "compiled-link-unit".to_owned(),
        precedence: 0,
        locale: catalog.locale.clone(),
        source: catalog.diagnostic_layout.clone(),
        missing_param_type: catalog.missing_param_type,
        entry_spans: catalog_entry_spans(&catalog.parsed),
    };
    for (message_id, message) in &catalog.parsed.messages {
        if let Some(pattern) = &message.value {
            validate_linked_pattern(pattern, &spec, message_id)?;
        }
        for attribute in &message.attributes {
            validate_linked_pattern(&attribute.value, &spec, message_id)?;
        }
    }
    for (term_id, term) in &catalog.parsed.terms {
        validate_linked_pattern(&term.value, &spec, &format!("-{term_id}"))?;
        for attribute in &term.attributes {
            validate_linked_pattern(&attribute.value, &spec, &format!("-{term_id}"))?;
        }
    }
    Ok(())
}

fn validate_linked_pattern(
    pattern: &Pattern<SpannedSlice>,
    spec: &CatalogSpec,
    message_id: &str,
) -> Result<(), Failure> {
    for element in &pattern.elements {
        match element {
            PatternElement::TextElement { value } if contains_bidi_control(value.as_ref()) => {
                let range = value.range();
                return Err(Failure::new(
                    "I18N_BIDI_CONTROL_CATALOG",
                    "compiled Fluent text contains a prohibited bidi-control character",
                )
                .at(&spec.path, &spec.source, range.start, range.end)
                .for_message(message_id));
            }
            PatternElement::Placeable {
                expression: Expression::Select { variants, .. },
            } => {
                for variant in variants {
                    validate_linked_pattern(&variant.value, spec, message_id)?;
                }
            }
            _ => {}
        }
    }
    validate_decoded_pattern(pattern, spec, message_id)
}

fn expand_link_units(request: &mut CompileRequest) -> Result<Vec<LoadedCatalog>, Failure> {
    let mut loaded = vec![];
    for input in std::mem::take(&mut request.link_units) {
        let unit: LinkUnit = serde_json::from_str(&input.artifact_json).map_err(|error| {
            Failure::new(
                "I18N_LINK_UNIT_JSON",
                format!("invalid compiled link unit: {error}"),
            )
        })?;
        validate_link_unit(&unit)?;
        request.packages.extend(unit.packages);
        loaded.extend(unit.catalogs.into_iter().map(|catalog| {
            let entry_spans = catalog_entry_spans(&catalog.parsed);
            LoadedCatalog {
                spec: CatalogSpec {
                    path: catalog.path,
                    package: catalog.package,
                    layer: input.layer.clone(),
                    precedence: input.precedence,
                    locale: catalog.locale,
                    source: catalog.diagnostic_layout,
                    missing_param_type: catalog.missing_param_type,
                    entry_spans,
                },
                parsed: Arc::new(catalog.parsed),
            }
        }));
    }
    Ok(loaded)
}

fn catalog_entry_spans(parsed: &ParsedCatalog) -> BTreeMap<String, Range<usize>> {
    let mut spans = parsed
        .messages
        .iter()
        .map(|(id, message)| (id.clone(), message.id.name.range()))
        .collect::<BTreeMap<_, _>>();
    spans.extend(
        parsed
            .terms
            .iter()
            .map(|(id, term)| (format!("-{id}"), term.id.name.range())),
    );
    spans
}

fn line_column(source: &str, byte_offset: usize) -> (usize, usize) {
    let prefix = &source[..byte_offset.min(source.len())];
    let line = prefix.bytes().filter(|item| *item == b'\n').count() + 1;
    let column = prefix.rsplit_once('\n').map_or_else(
        || prefix.chars().count() + 1,
        |(_, tail)| tail.chars().count() + 1,
    );
    (line, column)
}

fn digest_text(value: &str) -> String {
    format!("{:x}", Sha256::digest(value.as_bytes()))
}

fn source_unit_identity(spec: &CatalogSpec) -> String {
    format!(
        "v1\0{}\0{}\0{}\0{}\0{}",
        spec.package, spec.layer, spec.precedence, spec.locale, spec.path
    )
}

#[derive(Clone)]
struct SpannedSlice {
    source: Arc<String>,
    range: Range<usize>,
    source_offset: usize,
}

impl SpannedSlice {
    fn root(source: &str) -> Self {
        Self {
            source: Arc::new(source.to_owned()),
            range: 0..source.len(),
            source_offset: 0,
        }
    }

    fn range(&self) -> Range<usize> {
        self.range.clone()
    }
}

impl AsRef<str> for SpannedSlice {
    fn as_ref(&self) -> &str {
        let start = self.range.start - self.source_offset;
        let end = self.range.end - self.source_offset;
        &self.source[start..end]
    }
}

impl std::fmt::Debug for SpannedSlice {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("SpannedSlice")
            .field("text", &self.as_ref())
            .field("range", &self.range)
            .finish()
    }
}

// fluent-syntax compares Slice values while checking duplicate named arguments.
// The source range is metadata and must not change semantic equality.
impl PartialEq for SpannedSlice {
    fn eq(&self, other: &Self) -> bool {
        self.as_ref() == other.as_ref()
    }
}

impl Eq for SpannedSlice {}

impl Slice<'_> for SpannedSlice {
    fn slice(&self, range: Range<usize>) -> Self {
        Self {
            source: Arc::clone(&self.source),
            range: self.range.start + range.start..self.range.start + range.end,
            source_offset: self.source_offset,
        }
    }

    fn trim(&mut self) {
        let trimmed = self.as_ref().trim_end_matches([' ', '\r', '\n']);
        self.range.end = self.range.start + trimmed.len();
    }
}

impl Serialize for SpannedSlice {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        (&self.as_ref(), self.range.start, self.range.end).serialize(serializer)
    }
}

impl<'de> Deserialize<'de> for SpannedSlice {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let (value, start, end): (String, usize, usize) = Deserialize::deserialize(deserializer)?;
        if end < start || end - start != value.len() {
            return Err(serde::de::Error::custom(
                "invalid compiled Fluent source range",
            ));
        }
        Ok(Self {
            source: Arc::new(value),
            range: start..end,
            source_offset: start,
        })
    }
}

fn text(value: &SpannedSlice) -> &str {
    value.as_ref()
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct CompileRequest {
    schema_version: u32,
    active_locales: Vec<String>,
    #[serde(default)]
    fallbacks: BTreeMap<String, Vec<String>>,
    packages: Vec<PackageSpec>,
    catalogs: Vec<CatalogSpec>,
    #[serde(default)]
    link_units: Vec<LinkUnitInput>,
    #[serde(default)]
    formats: FormatRegistrySpec,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct PackageSpec {
    name: String,
    source_locale: String,
    #[serde(default)]
    exports: Vec<String>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct CatalogSpec {
    path: String,
    package: String,
    layer: String,
    precedence: i32,
    locale: String,
    source: String,
    #[serde(default)]
    missing_param_type: MissingParamType,
    #[serde(skip)]
    entry_spans: BTreeMap<String, Range<usize>>,
}

#[derive(Debug, Clone, Copy, Default, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
enum MissingParamType {
    Ignore,
    #[default]
    Warning,
    Error,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct ParsedCatalog {
    digest: String,
    messages: BTreeMap<String, ast::Message<SpannedSlice>>,
    terms: BTreeMap<String, ast::Term<SpannedSlice>>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct LinkUnitInput {
    artifact_json: String,
    layer: String,
    precedence: i32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct LinkUnit {
    schema_version: u32,
    compiler_version: String,
    revision: String,
    packages: Vec<PackageSpec>,
    catalogs: Vec<LinkCatalog>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct LinkCatalog {
    path: String,
    package: String,
    locale: String,
    source_digest: String,
    diagnostic_layout: String,
    missing_param_type: MissingParamType,
    parsed: ParsedCatalog,
}

#[derive(Debug, Clone)]
struct LoadedCatalog {
    spec: CatalogSpec,
    parsed: Arc<ParsedCatalog>,
}

#[derive(Debug, Default)]
struct CompilerState {
    cache: BTreeMap<String, Arc<ParsedCatalog>>,
}

#[derive(Debug, Clone, Eq, PartialEq, Ord, PartialOrd)]
struct OutputKey {
    message_id: String,
    attribute: Option<String>,
}

impl OutputKey {
    fn value(message_id: impl Into<String>) -> Self {
        Self {
            message_id: message_id.into(),
            attribute: None,
        }
    }

    fn token(&self) -> String {
        self.attribute.as_ref().map_or_else(
            || self.message_id.clone(),
            |attribute| format!("{}.{}", self.message_id, attribute),
        )
    }
}

#[derive(Debug, Clone, Eq, PartialEq)]
enum GraphNode {
    Message(OutputKey),
    Term(usize, String),
}

impl GraphNode {
    fn label(&self) -> String {
        match self {
            Self::Message(key) => key.token(),
            Self::Term(_, term) => format!("-{term}"),
        }
    }
}

#[derive(Debug, Clone, Copy)]
struct DefinitionRef {
    catalog: usize,
}

#[derive(Debug, Clone)]
struct ResolutionGraph {
    locale: String,
    messages: BTreeMap<OutputKey, DefinitionRef>,
    terms: BTreeSet<(usize, String)>,
}

type Contract = BTreeMap<String, String>;
type Interface = BTreeMap<String, ParameterMetadata>;

#[derive(Debug, Clone)]
struct ParamDeclaration {
    type_name: String,
    description: Option<String>,
    span: Range<usize>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct ParameterMetadata {
    type_name: String,
    direct: bool,
    declarations: Vec<ParameterDeclarationMetadata>,
}

#[derive(Debug, Clone, Eq, PartialEq, Serialize, Deserialize)]
struct ParameterDeclarationMetadata {
    path: String,
    start: usize,
    end: usize,
    line: usize,
    column: usize,
    description: Option<String>,
    annotated: bool,
}

#[derive(Debug, Serialize, Deserialize)]
struct CompileResult {
    schema_version: u32,
    compiler_version: String,
    revision: String,
    artifacts: BTreeMap<String, String>,
    manifest: BTreeMap<String, BTreeMap<String, ManifestEntry>>,
    source_maps: Vec<SourceMapEntry>,
    stats: CompileStats,
    formats: FormatRegistrySpec,
    formats_revision: String,
    diagnostics: Vec<CompilerDiagnostic>,
}

#[derive(Debug, Serialize, Deserialize)]
struct CompilerDiagnostic {
    code: String,
    severity: String,
    message: String,
    path: String,
    start: usize,
    end: usize,
    line: usize,
    column: usize,
    message_id: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct ManifestEntry {
    owner: String,
    owner_source_locale: String,
    definition_path: String,
    definition_start: usize,
    definition_end: usize,
    definition_line: usize,
    definition_column: usize,
    bundle_locale: String,
    internal_id: String,
    contract: BTreeMap<String, String>,
    interface: Interface,
    selected_layer: String,
    selected_path: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct SourceMapEntry {
    output: String,
    internal_id: String,
    authored_path: String,
    authored_start: usize,
    authored_end: usize,
    authored_line: usize,
    authored_column: usize,
    generated_locale: String,
    generated_start: usize,
    generated_end: usize,
    generated_line: usize,
    generated_column: usize,
    kind: String,
    detail: Option<String>,
}

#[derive(Debug, Serialize)]
struct SourceAnalysis {
    schema_version: u32,
    definitions: Vec<SourceSymbol>,
    references: Vec<SourceSymbol>,
}

#[derive(Debug, Serialize)]
struct SourceSymbol {
    kind: String,
    token: String,
    start: usize,
    end: usize,
}

#[derive(Debug, Serialize, Deserialize)]
struct CompileStats {
    parsed_catalogs: usize,
    reused_catalogs: usize,
    invalidated_catalogs: usize,
    evicted_catalogs: usize,
    linked_outputs: usize,
}

struct Linker {
    packages: BTreeMap<String, PackageSpec>,
    owners: BTreeMap<String, String>,
    fallbacks: BTreeMap<String, Vec<String>>,
    catalogs: Vec<LoadedCatalog>,
}

impl Linker {
    fn new(request: &CompileRequest, catalogs: Vec<LoadedCatalog>) -> Result<Self, Failure> {
        let mut packages = BTreeMap::new();
        let mut owners = BTreeMap::new();
        for package in &request.packages {
            if packages
                .insert(package.name.clone(), package.clone())
                .is_some()
            {
                return Err(Failure::new(
                    "I18N_DUPLICATE_PACKAGE",
                    format!("package {:?} is declared more than once", package.name),
                ));
            }
            let inferred_exports = catalogs
                .iter()
                .filter(|catalog| {
                    catalog.spec.package == package.name
                        && catalog.spec.locale == package.source_locale
                })
                .flat_map(|catalog| catalog.parsed.messages.keys().cloned())
                .collect::<BTreeSet<_>>();
            if package.exports.is_empty() {
                for message_id in inferred_exports {
                    owners
                        .entry(message_id)
                        .or_insert_with(|| package.name.clone());
                }
            } else {
                for message_id in &package.exports {
                    if let Some(previous) = owners.insert(message_id.clone(), package.name.clone())
                    {
                        return Err(Failure::new(
                            "I18N_DUPLICATE_OWNER",
                            format!(
                                "message {message_id:?} is exported by both {previous:?} and {:?}",
                                package.name
                            ),
                        ));
                    }
                }
            }
        }
        for catalog in &catalogs {
            if !packages.contains_key(&catalog.spec.package) {
                return Err(Failure::new(
                    "I18N_UNKNOWN_PACKAGE",
                    format!(
                        "catalog {:?} names unknown package {:?}",
                        catalog.spec.path, catalog.spec.package
                    ),
                ));
            }
        }
        validate_fallbacks(&request.fallbacks)?;
        let linker = Self {
            packages,
            owners,
            fallbacks: request.fallbacks.clone(),
            catalogs,
        };
        linker.validate_same_layer_duplicates()?;
        linker.validate_owner_sources()?;
        linker.validate_annotation_owners()?;
        Ok(linker)
    }

    fn validate_same_layer_duplicates(&self) -> Result<(), Failure> {
        let mut seen = BTreeMap::<(String, i32, String, String), usize>::new();
        for (catalog_index, catalog) in self.catalogs.iter().enumerate() {
            for (message_id, message) in &catalog.parsed.messages {
                let identity = (
                    catalog.spec.locale.clone(),
                    catalog.spec.precedence,
                    catalog.spec.layer.clone(),
                    message_id.clone(),
                );
                if let Some(previous_index) = seen.insert(identity, catalog_index) {
                    let previous = &self.catalogs[previous_index];
                    let previous_message = &previous.parsed.messages[message_id];
                    let current_span = message.id.name.range();
                    let previous_span = previous_message.id.name.range();
                    let (related_line, related_column) =
                        line_column(&previous.spec.source, previous_span.start);
                    return Err(Failure::new(
                        "I18N_DUPLICATE_LAYER_OUTPUT",
                        format!(
                            "message {message_id:?} is defined more than once in locale {:?}, layer {:?}, precedence {}",
                            catalog.spec.locale, catalog.spec.layer, catalog.spec.precedence
                        ),
                    )
                    .at(
                        &catalog.spec.path,
                        &catalog.spec.source,
                        current_span.start,
                        current_span.end,
                    )
                    .for_message(message_id)
                    .with_related(DiagnosticRelated {
                        message: "previous definition is here".to_owned(),
                        path: previous.spec.path.clone(),
                        start: previous_span.start,
                        end: previous_span.end,
                        line: related_line,
                        column: related_column,
                    }));
                }
            }
        }
        Ok(())
    }

    fn validate_annotation_owners(&self) -> Result<(), Failure> {
        for (catalog_index, catalog) in self.catalogs.iter().enumerate() {
            for (message_id, message) in &catalog.parsed.messages {
                let params = parse_params(message, &catalog.spec)?;
                if params.is_empty() {
                    continue;
                }
                let source = self.owner_source_message_definition(message_id)?;
                if source.catalog != catalog_index {
                    let owner = &self.owners[message_id];
                    let owner_source_locale = &self.packages[owner].source_locale;
                    let source_catalog = &self.catalogs[source.catalog];
                    let source_message = &source_catalog.parsed.messages[message_id];
                    let source_params = parse_params(source_message, &source_catalog.spec)?;
                    let repeats_source_contract =
                        catalog.spec.locale == *owner_source_locale && params == source_params;
                    if repeats_source_contract {
                        continue;
                    }
                    let span = message.id.name.range();
                    return Err(Failure::new(
                        "I18N_TRANSLATION_PARAM_DECLARATION",
                        format!(
                            "only the defining owner's source message or an exact source-locale override may declare @param values for {message_id:?}"
                        ),
                    )
                    .at(&catalog.spec.path, &catalog.spec.source, span.start, span.end)
                    .for_message(message_id));
                }
            }
        }
        Ok(())
    }

    fn validate_owner_sources(&self) -> Result<(), Failure> {
        for (message_id, owner) in &self.owners {
            let package = &self.packages[owner];
            if self
                .message_definition_in_package(message_id, owner, &package.source_locale)
                .is_none()
            {
                return Err(Failure::new(
                    "I18N_OWNER_SOURCE_MISSING",
                    format!(
                        "owner {owner:?} does not define exported message {message_id:?} in source locale {:?}",
                        package.source_locale
                    ),
                ));
            }
        }
        Ok(())
    }

    fn public_outputs(&self) -> Vec<OutputKey> {
        let mut result = BTreeSet::new();
        for (message_id, owner) in &self.owners {
            let package = &self.packages[owner];
            for catalog in self.catalogs.iter().filter(|catalog| {
                catalog.spec.package == *owner && catalog.spec.locale == package.source_locale
            }) {
                let Some(message) = catalog.parsed.messages.get(message_id) else {
                    continue;
                };
                if message.value.is_some() {
                    result.insert(OutputKey::value(message_id));
                }
                for attribute in &message.attributes {
                    result.insert(OutputKey {
                        message_id: message_id.clone(),
                        attribute: Some(text(&attribute.id.name).to_owned()),
                    });
                }
            }
        }
        result.into_iter().collect()
    }

    fn message_definition_in_package(
        &self,
        message_id: &str,
        package: &str,
        locale: &str,
    ) -> Option<DefinitionRef> {
        self.catalogs
            .iter()
            .enumerate()
            .filter(|(_, catalog)| catalog.spec.package == package && catalog.spec.locale == locale)
            .filter(|(_, catalog)| catalog.parsed.messages.contains_key(message_id))
            .max_by_key(|(_, catalog)| {
                (
                    catalog.spec.precedence,
                    catalog.spec.layer.as_str(),
                    catalog.spec.path.as_str(),
                )
            })
            .map(|(catalog, _)| DefinitionRef { catalog })
    }

    fn definition_in_package(
        &self,
        key: &OutputKey,
        package: &str,
        locale: &str,
    ) -> Option<DefinitionRef> {
        self.catalogs
            .iter()
            .enumerate()
            .filter(|(_, catalog)| catalog.spec.package == package && catalog.spec.locale == locale)
            .filter(|(_, catalog)| pattern_for(catalog, key).is_some())
            .max_by_key(|(_, catalog)| {
                (
                    catalog.spec.precedence,
                    catalog.spec.layer.as_str(),
                    catalog.spec.path.as_str(),
                )
            })
            .map(|(catalog, _)| DefinitionRef { catalog })
    }

    fn definition(&self, key: &OutputKey, locale: &str) -> Option<DefinitionRef> {
        self.catalogs
            .iter()
            .enumerate()
            .filter(|(_, catalog)| catalog.spec.locale == locale)
            .filter(|(_, catalog)| pattern_for(catalog, key).is_some())
            .max_by_key(|(_, catalog)| {
                (
                    catalog.spec.precedence,
                    catalog.spec.layer.as_str(),
                    catalog.spec.path.as_str(),
                )
            })
            .map(|(catalog, _)| DefinitionRef { catalog })
    }

    fn owner_source_definition(&self, key: &OutputKey) -> Result<DefinitionRef, Failure> {
        let owner = self.owners.get(&key.message_id).ok_or_else(|| {
            Failure::new(
                "I18N_UNKNOWN_PUBLIC_MESSAGE",
                format!("message {:?} has no defining package", key.message_id),
            )
        })?;
        let package = &self.packages[owner];
        self.definition_in_package(key, owner, &package.source_locale)
            .ok_or_else(|| {
                Failure::new(
                    "I18N_OWNER_SOURCE_OUTPUT_MISSING",
                    format!("owner source is missing output {:?}", key.token()),
                )
            })
    }

    fn owner_source_message_definition(&self, message_id: &str) -> Result<DefinitionRef, Failure> {
        let owner = self.owners.get(message_id).ok_or_else(|| {
            Failure::new(
                "I18N_UNKNOWN_PUBLIC_MESSAGE",
                format!("message {message_id:?} has no defining package"),
            )
        })?;
        let package = &self.packages[owner];
        self.message_definition_in_package(message_id, owner, &package.source_locale)
            .ok_or_else(|| {
                Failure::new(
                    "I18N_OWNER_SOURCE_MISSING",
                    format!("owner source is missing message {message_id:?}"),
                )
            })
    }

    fn source_contract(&self, key: &OutputKey) -> Result<Contract, Failure> {
        Ok(self
            .source_interface(key)?
            .into_iter()
            .map(|(name, metadata)| (name, metadata.type_name))
            .collect())
    }

    fn source_interface(&self, key: &OutputKey) -> Result<Interface, Failure> {
        self.source_interface_inner(key, &mut vec![])
    }

    fn source_interface_inner(
        &self,
        key: &OutputKey,
        stack: &mut Vec<GraphNode>,
    ) -> Result<Interface, Failure> {
        let node = GraphNode::Message(key.clone());
        if stack.contains(&node) {
            return Err(Failure::new(
                "I18N_REFERENCE_CYCLE",
                format!("public reference cycle reaches {:?}", key.token()),
            ));
        }
        stack.push(node);
        let definition = self.owner_source_definition(key)?;
        let catalog = &self.catalogs[definition.catalog];
        let pattern = pattern_for(catalog, key).expect("owner source pattern checked");
        let message = &catalog.parsed.messages[&key.message_id];
        let declarations = parse_param_declarations(message, &catalog.spec)?;
        let params = declarations
            .iter()
            .map(|(name, declaration)| (name.clone(), declaration.type_name.clone()))
            .collect();
        validate_message_annotations(message, &params, &catalog.spec)?;
        let mut interface = BTreeMap::new();
        for variable in direct_variables(pattern) {
            let (type_name, declaration) = if let Some(param) = declarations.get(&variable) {
                (
                    param.type_name.clone(),
                    parameter_declaration_metadata(
                        param.span.clone(),
                        &catalog.spec,
                        param.description.clone(),
                        true,
                    ),
                )
            } else if matches!(catalog.spec.missing_param_type, MissingParamType::Error) {
                return Err(semantic_failure(
                    "I18N_PARAM_MISSING",
                    format!(
                        "message {:?} uses ${variable} without an @param declaration",
                        key.message_id
                    ),
                    &catalog.spec,
                    &key.message_id,
                ));
            } else {
                let span = message_variable_span(message, &variable)
                    .unwrap_or_else(|| message.id.name.range());
                (
                    "scalar".to_owned(),
                    parameter_declaration_metadata(span, &catalog.spec, None, false),
                )
            };
            merge_parameter_metadata(
                &mut interface,
                variable,
                ParameterMetadata {
                    type_name,
                    direct: true,
                    declarations: vec![declaration],
                },
                &catalog.spec,
                &key.message_id,
            )?;
        }
        for reference in message_references(pattern) {
            let inherited = self.source_interface_inner(&reference, stack)?;
            for (name, mut metadata) in inherited {
                metadata.direct = false;
                merge_parameter_metadata(
                    &mut interface,
                    name,
                    metadata,
                    &catalog.spec,
                    &key.message_id,
                )?;
            }
        }
        for term in term_references(pattern) {
            let inherited =
                self.source_term_interface(definition.catalog, &term, stack, &key.message_id)?;
            for (name, mut metadata) in inherited {
                metadata.direct = false;
                merge_parameter_metadata(
                    &mut interface,
                    name,
                    metadata,
                    &catalog.spec,
                    &key.message_id,
                )?;
            }
        }
        stack.pop();
        Ok(interface)
    }

    fn source_term_interface(
        &self,
        catalog_index: usize,
        term: &str,
        stack: &mut Vec<GraphNode>,
        root_message_id: &str,
    ) -> Result<Interface, Failure> {
        let node = GraphNode::Term(catalog_index, term.to_owned());
        if stack.contains(&node) {
            return Err(Failure::new(
                "I18N_REFERENCE_CYCLE",
                format!("message/term reference cycle reaches {:?}", node.label()),
            ));
        }
        let catalog = &self.catalogs[catalog_index];
        let term_node = catalog.parsed.terms.get(term).ok_or_else(|| {
            semantic_failure(
                "I18N_OWNER_SOURCE_OUTPUT_MISSING",
                format!("source message references missing private term -{term}"),
                &catalog.spec,
                root_message_id,
            )
        })?;
        if pattern_has_variables(&term_node.value) {
            return Err(semantic_failure(
                "I18N_UNSUPPORTED_TERM_VARIABLE",
                format!(
                    "private term -{term} uses variables; parameterized private terms are not supported yet"
                ),
                &catalog.spec,
                root_message_id,
            ));
        }
        stack.push(node);
        let mut interface = Interface::new();
        for reference in message_references(&term_node.value) {
            let inherited = self.source_interface_inner(&reference, stack)?;
            for (name, mut metadata) in inherited {
                metadata.direct = false;
                merge_parameter_metadata(
                    &mut interface,
                    name,
                    metadata,
                    &catalog.spec,
                    root_message_id,
                )?;
            }
        }
        for nested in term_references(&term_node.value) {
            let inherited =
                self.source_term_interface(catalog_index, &nested, stack, root_message_id)?;
            for (name, mut metadata) in inherited {
                metadata.direct = false;
                merge_parameter_metadata(
                    &mut interface,
                    name,
                    metadata,
                    &catalog.spec,
                    root_message_id,
                )?;
            }
        }
        stack.pop();
        Ok(interface)
    }

    fn resolve(&self, active_locale: &str, key: &OutputKey) -> Result<ResolutionGraph, Failure> {
        let owner = self.owners.get(&key.message_id).ok_or_else(|| {
            Failure::new(
                "I18N_UNKNOWN_PUBLIC_MESSAGE",
                format!("unknown message {:?}", key.message_id),
            )
        })?;
        let source_locale = &self.packages[owner].source_locale;
        let mut candidates = vec![active_locale.to_owned()];
        self.append_fallbacks(active_locale, &mut candidates);
        if source_locale != active_locale && !candidates.contains(source_locale) {
            candidates.push(source_locale.clone());
        }
        let mut last_missing = None;
        for locale in candidates {
            match self.graph_for_locale(&locale, key) {
                Ok(graph) => return Ok(graph),
                Err(error) if error.code == "I18N_CANDIDATE_INCOMPLETE" => {
                    last_missing = Some(error)
                }
                Err(error) => return Err(error),
            }
        }
        Err(last_missing.unwrap_or_else(|| {
            Failure::new(
                "I18N_CANDIDATE_INCOMPLETE",
                format!("no complete graph for {:?}", key.token()),
            )
        }))
    }

    fn append_fallbacks(&self, locale: &str, result: &mut Vec<String>) {
        for fallback in self.fallbacks.get(locale).into_iter().flatten() {
            if !result.contains(fallback) {
                result.push(fallback.clone());
                self.append_fallbacks(fallback, result);
            }
        }
    }

    fn graph_for_locale(&self, locale: &str, key: &OutputKey) -> Result<ResolutionGraph, Failure> {
        let mut graph = ResolutionGraph {
            locale: locale.to_owned(),
            messages: BTreeMap::new(),
            terms: BTreeSet::new(),
        };
        self.add_message(locale, key, &mut graph, &mut vec![])?;
        Ok(graph)
    }

    fn validate_graph_contract(
        &self,
        root: &OutputKey,
        graph: &ResolutionGraph,
        root_contract: &Contract,
    ) -> Result<(), Failure> {
        for (key, definition) in &graph.messages {
            let selected_contract = self.source_contract(key)?;
            let catalog = &self.catalogs[definition.catalog];
            for (name, type_name) in selected_contract {
                match root_contract.get(&name) {
                    Some(root_type) if root_type == &type_name => {}
                    Some(root_type) => {
                        return Err(semantic_failure(
                            "I18N_TRANSLATION_REFERENCE_TYPE_CONFLICT",
                            format!(
                                "translation graph for {:?} needs ${name} as {type_name}, but its source interface declares {root_type}",
                                root.token()
                            ),
                            &catalog.spec,
                            &key.message_id,
                        ));
                    }
                    None => {
                        return Err(semantic_failure(
                            "I18N_TRANSLATION_REFERENCE_ARGUMENT_ADDED",
                            format!(
                                "translation graph for {:?} introduces ${name} through public reference {:?}",
                                root.token(),
                                key.token()
                            ),
                            &catalog.spec,
                            &key.message_id,
                        ));
                    }
                }
            }
        }
        Ok(())
    }

    fn add_message(
        &self,
        locale: &str,
        key: &OutputKey,
        graph: &mut ResolutionGraph,
        stack: &mut Vec<GraphNode>,
    ) -> Result<(), Failure> {
        let node = GraphNode::Message(key.clone());
        if stack.contains(&node) {
            return Err(Failure::new(
                "I18N_REFERENCE_CYCLE",
                format!("public reference cycle reaches {:?}", key.token()),
            ));
        }
        if graph.messages.contains_key(key) {
            return Ok(());
        }
        let definition = self.definition(key, locale).ok_or_else(|| {
            Failure::new(
                "I18N_CANDIDATE_INCOMPLETE",
                format!("locale {locale:?} is missing {:?}", key.token()),
            )
        })?;
        stack.push(node);
        let catalog = &self.catalogs[definition.catalog];
        let pattern = pattern_for(catalog, key).expect("selected definition has pattern");
        let contract = self.source_contract(key)?;
        for variable in direct_variables(pattern) {
            if !contract.contains_key(&variable) {
                let span = pattern_variable_span(pattern, &variable)
                    .unwrap_or_else(|| output_span(catalog, key));
                return Err(Failure::new(
                    "I18N_TRANSLATION_VARIABLE_ADDED",
                    format!(
                        "translation of {:?} introduces undeclared variable ${variable}",
                        key.token()
                    ),
                )
                .at(
                    &catalog.spec.path,
                    &catalog.spec.source,
                    span.start,
                    span.end,
                )
                .for_message(&key.message_id));
            }
        }
        graph.messages.insert(key.clone(), definition);
        for reference in message_references(pattern) {
            self.add_message(locale, &reference, graph, stack)?;
        }
        for term in term_references(pattern) {
            self.add_term(
                locale,
                definition.catalog,
                &term,
                graph,
                stack,
                &key.message_id,
            )?;
        }
        stack.pop();
        Ok(())
    }

    fn add_term(
        &self,
        locale: &str,
        catalog_index: usize,
        term: &str,
        graph: &mut ResolutionGraph,
        stack: &mut Vec<GraphNode>,
        root_message_id: &str,
    ) -> Result<(), Failure> {
        let node = GraphNode::Term(catalog_index, term.to_owned());
        if stack.contains(&node) {
            return Err(Failure::new(
                "I18N_REFERENCE_CYCLE",
                format!("message/term reference cycle reaches {:?}", node.label()),
            ));
        }
        if graph.terms.contains(&(catalog_index, term.to_owned())) {
            return Ok(());
        }
        let catalog = &self.catalogs[catalog_index];
        let term_node = catalog.parsed.terms.get(term).ok_or_else(|| {
            Failure::new(
                "I18N_CANDIDATE_INCOMPLETE",
                format!(
                    "locale {locale:?} layer {:?} is missing private term -{term}",
                    catalog.spec.layer
                ),
            )
        })?;
        if pattern_has_variables(&term_node.value) {
            return Err(semantic_failure(
                "I18N_UNSUPPORTED_TERM_VARIABLE",
                format!(
                    "private term -{term} uses variables; parameterized private terms are not supported yet"
                ),
                &catalog.spec,
                root_message_id,
            ));
        }
        stack.push(node);
        graph.terms.insert((catalog_index, term.to_owned()));
        for reference in message_references(&term_node.value) {
            self.add_message(locale, &reference, graph, stack)?;
        }
        for nested in term_references(&term_node.value) {
            self.add_term(
                locale,
                catalog_index,
                &nested,
                graph,
                stack,
                root_message_id,
            )?;
        }
        stack.pop();
        Ok(())
    }

    fn validate_slots(
        &self,
        root: &OutputKey,
        graph: &ResolutionGraph,
        contract: &Contract,
    ) -> Result<(), Failure> {
        let required: BTreeSet<_> = contract
            .iter()
            .filter(|(_, type_name)| type_name.as_str() == "Slot")
            .map(|(name, _)| name.clone())
            .collect();
        if required.is_empty() {
            return Ok(());
        }
        let minimums = self.slot_minimums(root, graph, contract, &mut vec![])?;
        for slot in required {
            if minimums.get(&slot).copied().unwrap_or(0) == 0 {
                let definition = graph.messages[root];
                let catalog = &self.catalogs[definition.catalog];
                return Err(semantic_failure(
                    "I18N_REQUIRED_SLOT_MISSING",
                    format!(
                        "translation of {:?} omits required Slot ${slot} on a reachable path",
                        root.token()
                    ),
                    &catalog.spec,
                    &root.message_id,
                ));
            }
        }
        Ok(())
    }

    fn slot_minimums(
        &self,
        key: &OutputKey,
        graph: &ResolutionGraph,
        contract: &Contract,
        stack: &mut Vec<OutputKey>,
    ) -> Result<BTreeMap<String, usize>, Failure> {
        if stack.contains(key) {
            return Err(Failure::new(
                "I18N_REFERENCE_CYCLE",
                format!("public reference cycle reaches {:?}", key.token()),
            ));
        }
        stack.push(key.clone());
        let definition = graph.messages[key];
        let catalog = &self.catalogs[definition.catalog];
        let pattern = pattern_for(catalog, key).expect("graph pattern");
        let minimums = self.pattern_slot_minimums(pattern, key, graph, contract, stack, catalog)?;
        stack.pop();
        Ok(minimums)
    }

    fn pattern_slot_minimums(
        &self,
        pattern: &Pattern<SpannedSlice>,
        key: &OutputKey,
        graph: &ResolutionGraph,
        contract: &Contract,
        stack: &mut Vec<OutputKey>,
        catalog: &LoadedCatalog,
    ) -> Result<BTreeMap<String, usize>, Failure> {
        let mut minimums = BTreeMap::new();
        for element in &pattern.elements {
            let PatternElement::Placeable { expression } = element else {
                continue;
            };
            let incoming =
                self.expression_slot_minimums(expression, key, graph, contract, stack, catalog)?;
            for (name, count) in incoming {
                *minimums.entry(name).or_default() += count;
            }
        }
        Ok(minimums)
    }

    fn expression_slot_minimums(
        &self,
        expression: &Expression<SpannedSlice>,
        key: &OutputKey,
        graph: &ResolutionGraph,
        contract: &Contract,
        stack: &mut Vec<OutputKey>,
        catalog: &LoadedCatalog,
    ) -> Result<BTreeMap<String, usize>, Failure> {
        match expression {
            Expression::Inline(InlineExpression::VariableReference { id }) => {
                let name = text(&id.name);
                if contract.get(name).is_some_and(|item| item == "Slot") {
                    Ok(BTreeMap::from([(name.to_owned(), 1)]))
                } else {
                    Ok(BTreeMap::new())
                }
            }
            Expression::Inline(InlineExpression::MessageReference { id, attribute }) => self
                .slot_minimums(
                    &OutputKey {
                        message_id: text(&id.name).to_owned(),
                        attribute: attribute.as_ref().map(|item| text(&item.name).to_owned()),
                    },
                    graph,
                    contract,
                    stack,
                ),
            Expression::Inline(InlineExpression::FunctionReference { arguments, .. }) => {
                for argument in arguments
                    .positional
                    .iter()
                    .chain(arguments.named.iter().map(|item| &item.value))
                {
                    if let InlineExpression::VariableReference { id } = argument
                        && contract
                            .get(text(&id.name))
                            .is_some_and(|type_name| type_name == "Slot")
                    {
                        let span = inline_span(argument, &catalog.spec.source)?;
                        return Err(Failure::new(
                            "I18N_SLOT_FUNCTION",
                            "Slot values cannot be passed to authored Fluent functions",
                        )
                        .at(
                            &catalog.spec.path,
                            &catalog.spec.source,
                            span.start,
                            span.end,
                        )
                        .for_message(&key.message_id));
                    }
                }
                Ok(BTreeMap::new())
            }
            Expression::Inline(InlineExpression::Placeable { expression }) => {
                let nested = self
                    .expression_slot_minimums(expression, key, graph, contract, stack, catalog)?;
                if nested.values().any(|count| *count > 0) {
                    let span = expression_span(expression, &catalog.spec.source)?;
                    return Err(Failure::new(
                        "I18N_SLOT_NESTED",
                        "Slot values must be direct standalone placeables",
                    )
                    .at(
                        &catalog.spec.path,
                        &catalog.spec.source,
                        span.start,
                        span.end,
                    )
                    .for_message(&key.message_id));
                }
                Ok(BTreeMap::new())
            }
            Expression::Select { selector, variants } => {
                if let InlineExpression::VariableReference { id } = selector
                    && contract
                        .get(text(&id.name))
                        .is_some_and(|type_name| type_name == "Slot")
                {
                    let span = inline_span(selector, &catalog.spec.source)?;
                    return Err(Failure::new(
                        "I18N_SLOT_SELECTOR",
                        "Slot values cannot be selectors",
                    )
                    .at(
                        &catalog.spec.path,
                        &catalog.spec.source,
                        span.start,
                        span.end,
                    )
                    .for_message(&key.message_id));
                }
                let mut minimums: Option<BTreeMap<String, usize>> = None;
                for variant in variants {
                    let branch = self.pattern_slot_minimums(
                        &variant.value,
                        key,
                        graph,
                        contract,
                        stack,
                        catalog,
                    )?;
                    minimums = Some(match minimums {
                        None => branch,
                        Some(previous) => minimum_slot_counts(previous, branch),
                    });
                }
                Ok(minimums.unwrap_or_default())
            }
            Expression::Inline(_) => Ok(BTreeMap::new()),
        }
    }
}

fn minimum_slot_counts(
    left: BTreeMap<String, usize>,
    right: BTreeMap<String, usize>,
) -> BTreeMap<String, usize> {
    left.keys()
        .chain(right.keys())
        .cloned()
        .collect::<BTreeSet<_>>()
        .into_iter()
        .map(|name| {
            let count = left
                .get(&name)
                .copied()
                .unwrap_or(0)
                .min(right.get(&name).copied().unwrap_or(0));
            (name, count)
        })
        .collect()
}

fn pattern_for<'a>(
    catalog: &'a LoadedCatalog,
    key: &OutputKey,
) -> Option<&'a Pattern<SpannedSlice>> {
    let message = catalog.parsed.messages.get(&key.message_id)?;
    match &key.attribute {
        None => message.value.as_ref(),
        Some(attribute) => message
            .attributes
            .iter()
            .find(|item| text(&item.id.name) == attribute)
            .map(|item| &item.value),
    }
}

fn output_span(catalog: &LoadedCatalog, key: &OutputKey) -> Range<usize> {
    let message = &catalog.parsed.messages[&key.message_id];
    match &key.attribute {
        None => message.id.name.range(),
        Some(attribute) => message
            .attributes
            .iter()
            .find(|item| text(&item.id.name) == attribute)
            .map_or_else(|| message.id.name.range(), |item| item.id.name.range()),
    }
}

fn parse_params(
    message: &ast::Message<SpannedSlice>,
    spec: &CatalogSpec,
) -> Result<Contract, Failure> {
    Ok(parse_param_declarations(message, spec)?
        .into_iter()
        .map(|(name, declaration)| (name, declaration.type_name))
        .collect())
}

fn parse_param_declarations(
    message: &ast::Message<SpannedSlice>,
    spec: &CatalogSpec,
) -> Result<BTreeMap<String, ParamDeclaration>, Failure> {
    let mut result = BTreeMap::new();
    let Some(comment) = &message.comment else {
        return Ok(result);
    };
    for content in &comment.content {
        let line = content.as_ref().trim();
        if !line.starts_with("@param") {
            continue;
        }
        let rest = line[6..].trim();
        let Some(after_open) = rest.strip_prefix('{') else {
            return Err(param_failure(
                "I18N_PARAM_SYNTAX",
                format!("invalid @param declaration {line:?}"),
                spec,
                message,
                content,
            ));
        };
        let Some((type_name, after_type)) = after_open.split_once('}') else {
            return Err(param_failure(
                "I18N_PARAM_SYNTAX",
                format!("invalid @param declaration {line:?}"),
                spec,
                message,
                content,
            ));
        };
        if !matches!(type_name, "str" | "int" | "Decimal" | "datetime" | "Slot") {
            return Err(param_failure(
                "I18N_PARAM_TYPE_UNSUPPORTED",
                format!("unsupported @param type {type_name:?}"),
                spec,
                message,
                content,
            ));
        }
        let variable_part = after_type.trim();
        let variable_token = variable_part.split_whitespace().next().unwrap_or("");
        let Some(name) = variable_token.strip_prefix('$') else {
            return Err(param_failure(
                "I18N_PARAM_SYNTAX",
                format!("invalid @param declaration {line:?}"),
                spec,
                message,
                content,
            ));
        };
        if name.is_empty()
            || !name
                .chars()
                .all(|item| item == '_' || item.is_ascii_alphanumeric())
        {
            return Err(param_failure(
                "I18N_PARAM_SYNTAX",
                format!("invalid @param variable {variable_token:?}"),
                spec,
                message,
                content,
            ));
        }
        let description_text = variable_part[variable_token.len()..].trim();
        let description = if description_text.is_empty() {
            None
        } else if let Some(value) = description_text.strip_prefix('-') {
            let value = value.trim();
            (!value.is_empty()).then(|| value.to_owned())
        } else {
            return Err(param_failure(
                "I18N_PARAM_SYNTAX",
                format!(
                    "invalid @param description in {line:?}; expected '-' before the description"
                ),
                spec,
                message,
                content,
            ));
        };
        if result
            .insert(
                name.to_owned(),
                ParamDeclaration {
                    type_name: type_name.to_owned(),
                    description,
                    span: content.range(),
                },
            )
            .is_some()
        {
            return Err(param_failure(
                "I18N_PARAM_DUPLICATE",
                format!("duplicate @param for ${name}"),
                spec,
                message,
                content,
            ));
        }
    }
    Ok(result)
}

fn param_failure(
    code: &'static str,
    message_text: String,
    spec: &CatalogSpec,
    message: &ast::Message<SpannedSlice>,
    content: &SpannedSlice,
) -> Failure {
    let span = content.range();
    Failure::new(code, message_text)
        .at(&spec.path, &spec.source, span.start, span.end)
        .for_message(text(&message.id.name))
}

fn parameter_declaration_metadata(
    span: Range<usize>,
    spec: &CatalogSpec,
    description: Option<String>,
    annotated: bool,
) -> ParameterDeclarationMetadata {
    let (line, column) = line_column(&spec.source, span.start);
    ParameterDeclarationMetadata {
        path: spec.path.clone(),
        start: span.start,
        end: span.end,
        line,
        column,
        description,
        annotated,
    }
}

fn merge_parameter_metadata(
    interface: &mut Interface,
    name: String,
    mut metadata: ParameterMetadata,
    spec: &CatalogSpec,
    message_id: &str,
) -> Result<(), Failure> {
    if let Some(previous) = interface.get_mut(&name) {
        if previous.type_name != metadata.type_name {
            return Err(semantic_failure(
                "I18N_TRANSITIVE_TYPE_CONFLICT",
                format!(
                    "${name} is inherited as both {} and {}",
                    previous.type_name, metadata.type_name
                ),
                spec,
                message_id,
            ));
        }
        previous.direct |= metadata.direct;
        previous.declarations.append(&mut metadata.declarations);
        previous.declarations.sort_by(|left, right| {
            (&left.path, left.start, left.end, &left.description).cmp(&(
                &right.path,
                right.start,
                right.end,
                &right.description,
            ))
        });
        previous.declarations.dedup();
    } else {
        interface.insert(name, metadata);
    }
    Ok(())
}

fn validate_message_annotations(
    message: &ast::Message<SpannedSlice>,
    params: &Contract,
    spec: &CatalogSpec,
) -> Result<(), Failure> {
    let mut used = BTreeSet::new();
    if let Some(value) = &message.value {
        used.extend(direct_variables(value));
    }
    for attribute in &message.attributes {
        used.extend(direct_variables(&attribute.value));
    }
    for variable in params.keys() {
        if !used.contains(variable) {
            return Err(semantic_failure(
                "I18N_PARAM_UNUSED",
                format!(
                    "source message {:?} declares unused ${variable}",
                    text(&message.id.name)
                ),
                spec,
                text(&message.id.name),
            ));
        }
    }
    Ok(())
}

fn missing_param_diagnostics(linker: &Linker) -> Result<Vec<CompilerDiagnostic>, Failure> {
    let mut diagnostics = vec![];
    for message_id in linker.owners.keys() {
        let definition = linker.owner_source_message_definition(message_id)?;
        let catalog = &linker.catalogs[definition.catalog];
        if !matches!(catalog.spec.missing_param_type, MissingParamType::Warning) {
            continue;
        }
        let message = &catalog.parsed.messages[message_id];
        let params = parse_params(message, &catalog.spec)?;
        let mut used = BTreeSet::new();
        if let Some(value) = &message.value {
            used.extend(direct_variables(value));
        }
        for attribute in &message.attributes {
            used.extend(direct_variables(&attribute.value));
        }
        for variable in used.difference(&params.keys().cloned().collect()) {
            let span =
                message_variable_span(message, variable).unwrap_or_else(|| message.id.name.range());
            let (line, column) = line_column(&catalog.spec.source, span.start);
            diagnostics.push(CompilerDiagnostic {
                code: "citry.i18n.missing-param-type".to_owned(),
                severity: "warning".to_owned(),
                message: format!(
                    "Message {message_id:?} uses ${variable} without an @param type declaration."
                ),
                path: catalog.spec.path.clone(),
                start: span.start,
                end: span.end,
                line,
                column,
                message_id: message_id.clone(),
            });
        }
    }
    diagnostics.sort_by(|left, right| {
        (&left.path, left.start, &left.message_id).cmp(&(
            &right.path,
            right.start,
            &right.message_id,
        ))
    });
    Ok(diagnostics)
}

fn message_variable_span(
    message: &ast::Message<SpannedSlice>,
    variable: &str,
) -> Option<Range<usize>> {
    let mut result = None;
    let mut inspect = |inline: &InlineExpression<SpannedSlice>| {
        if result.is_none()
            && let InlineExpression::VariableReference { id } = inline
            && text(&id.name) == variable
        {
            result = Some(id.name.range());
        }
    };
    if let Some(value) = &message.value {
        walk_pattern(value, &mut inspect);
    }
    for attribute in &message.attributes {
        walk_pattern(&attribute.value, &mut inspect);
    }
    result
}

fn pattern_variable_span(pattern: &Pattern<SpannedSlice>, variable: &str) -> Option<Range<usize>> {
    let mut result = None;
    walk_pattern(pattern, &mut |inline| {
        if result.is_none()
            && let InlineExpression::VariableReference { id } = inline
            && text(&id.name) == variable
        {
            result = Some(id.name.range());
        }
    });
    result
}

fn direct_variables(pattern: &Pattern<SpannedSlice>) -> BTreeSet<String> {
    direct_variables_with_repetition(pattern)
        .into_iter()
        .collect()
}

fn direct_variables_with_repetition(pattern: &Pattern<SpannedSlice>) -> Vec<String> {
    let mut result = vec![];
    for element in &pattern.elements {
        if let PatternElement::Placeable { expression } = element {
            variables_in_expression(expression, &mut result);
        }
    }
    result
}

fn variables_in_expression(expression: &Expression<SpannedSlice>, result: &mut Vec<String>) {
    match expression {
        Expression::Inline(inline) => variables_in_inline(inline, result),
        Expression::Select { selector, variants } => {
            variables_in_inline(selector, result);
            for variant in variants {
                result.extend(direct_variables_with_repetition(&variant.value));
            }
        }
    }
}

fn variables_in_inline(inline: &InlineExpression<SpannedSlice>, result: &mut Vec<String>) {
    match inline {
        InlineExpression::VariableReference { id } => result.push(text(&id.name).to_owned()),
        InlineExpression::FunctionReference { arguments, .. } => {
            for item in &arguments.positional {
                variables_in_inline(item, result);
            }
            for item in &arguments.named {
                variables_in_inline(&item.value, result);
            }
        }
        InlineExpression::TermReference {
            arguments: Some(arguments),
            ..
        } => {
            for item in &arguments.positional {
                variables_in_inline(item, result);
            }
            for item in &arguments.named {
                variables_in_inline(&item.value, result);
            }
        }
        InlineExpression::Placeable { expression } => variables_in_expression(expression, result),
        _ => {}
    }
}

fn message_references(pattern: &Pattern<SpannedSlice>) -> Vec<OutputKey> {
    let mut result = vec![];
    walk_pattern(pattern, &mut |inline| {
        if let InlineExpression::MessageReference { id, attribute } = inline {
            result.push(OutputKey {
                message_id: text(&id.name).to_owned(),
                attribute: attribute.as_ref().map(|item| text(&item.name).to_owned()),
            });
        }
    });
    result
}

fn term_references(pattern: &Pattern<SpannedSlice>) -> Vec<String> {
    let mut result = vec![];
    walk_pattern(pattern, &mut |inline| {
        if let InlineExpression::TermReference { id, .. } = inline {
            result.push(text(&id.name).to_owned());
        }
    });
    result
}

fn walk_pattern(
    pattern: &Pattern<SpannedSlice>,
    visit: &mut impl FnMut(&InlineExpression<SpannedSlice>),
) {
    for element in &pattern.elements {
        if let PatternElement::Placeable { expression } = element {
            walk_expression(expression, visit);
        }
    }
}

fn walk_expression(
    expression: &Expression<SpannedSlice>,
    visit: &mut impl FnMut(&InlineExpression<SpannedSlice>),
) {
    match expression {
        Expression::Inline(inline) => walk_inline(inline, visit),
        Expression::Select { selector, variants } => {
            walk_inline(selector, visit);
            for variant in variants {
                walk_pattern(&variant.value, visit);
            }
        }
    }
}

fn walk_inline(
    inline: &InlineExpression<SpannedSlice>,
    visit: &mut impl FnMut(&InlineExpression<SpannedSlice>),
) {
    visit(inline);
    match inline {
        InlineExpression::FunctionReference { arguments, .. } => {
            for item in &arguments.positional {
                walk_inline(item, visit);
            }
            for item in &arguments.named {
                walk_inline(&item.value, visit);
            }
        }
        InlineExpression::TermReference {
            arguments: Some(arguments),
            ..
        } => {
            for item in &arguments.positional {
                walk_inline(item, visit);
            }
            for item in &arguments.named {
                walk_inline(&item.value, visit);
            }
        }
        InlineExpression::Placeable { expression } => walk_expression(expression, visit),
        _ => {}
    }
}

fn pattern_has_variables(pattern: &Pattern<SpannedSlice>) -> bool {
    !direct_variables(pattern).is_empty()
}

fn semantic_failure(
    code: &'static str,
    message: String,
    spec: &CatalogSpec,
    message_id: &str,
) -> Failure {
    let span = spec
        .entry_spans
        .get(message_id)
        .cloned()
        .unwrap_or_else(|| {
            let start = entry_offset(&spec.source, message_id, false).unwrap_or(0);
            start..start + message_id.len()
        });
    Failure::new(code, message)
        .at(&spec.path, &spec.source, span.start, span.end)
        .for_message(message_id)
}

fn entry_offset(source: &str, id: &str, term: bool) -> Option<usize> {
    let token = if term {
        format!("-{id}")
    } else {
        id.to_owned()
    };
    let mut offset = 0;
    for line in source.split_inclusive('\n') {
        if let Some(rest) = line.strip_prefix(&token)
            && rest.trim_start_matches([' ', '\t']).starts_with('=')
        {
            return Some(offset + usize::from(term));
        }
        offset += line.len();
    }
    None
}

fn parse_catalog(spec: &CatalogSpec) -> Result<ParsedCatalog, Failure> {
    if contains_bidi_control(&spec.source) {
        let (start, character) = spec
            .source
            .char_indices()
            .find(|(_, character)| BIDI_CONTROLS.contains(character))
            .expect("bidi-control scan reported a match");
        return Err(Failure::new(
            "I18N_BIDI_CONTROL_CATALOG",
            "authored catalog contains a prohibited bidi-control character",
        )
        .at(
            &spec.path,
            &spec.source,
            start,
            start + character.len_utf8(),
        ));
    }
    let resource = match fluent_syntax::parser::parse(SpannedSlice::root(&spec.source)) {
        Ok(resource) => resource,
        Err((_resource, errors)) => {
            let error = errors
                .into_iter()
                .next()
                .expect("parser returned an empty error list");
            return Err(Failure::new("I18N_FTL_SYNTAX", error.to_string()).at(
                &spec.path,
                &spec.source,
                error.pos.start,
                error.pos.end,
            ));
        }
    };
    let mut messages = BTreeMap::<String, ast::Message<SpannedSlice>>::new();
    let mut terms = BTreeMap::<String, ast::Term<SpannedSlice>>::new();
    for entry in resource.body {
        match entry {
            Entry::Message(message) => {
                let id = text(&message.id.name).to_owned();
                if let Some(value) = &message.value {
                    validate_decoded_pattern(value, spec, &id)?;
                }
                for attribute in &message.attributes {
                    validate_decoded_pattern(&attribute.value, spec, &id)?;
                }
                if let Some(previous) = messages.get(&id) {
                    let current_span = message.id.name.range();
                    let previous_span = previous.id.name.range();
                    let (related_line, related_column) =
                        line_column(&spec.source, previous_span.start);
                    return Err(Failure::new(
                        "I18N_DUPLICATE_MESSAGE",
                        format!("message {id:?} is defined twice"),
                    )
                    .at(
                        &spec.path,
                        &spec.source,
                        current_span.start,
                        current_span.end,
                    )
                    .for_message(&id)
                    .with_related(DiagnosticRelated {
                        message: "previous definition is here".to_owned(),
                        path: spec.path.clone(),
                        start: previous_span.start,
                        end: previous_span.end,
                        line: related_line,
                        column: related_column,
                    }));
                }
                messages.insert(id, message);
            }
            Entry::Term(term) => {
                let id = text(&term.id.name).to_owned();
                validate_decoded_pattern(&term.value, spec, &format!("-{id}"))?;
                for attribute in &term.attributes {
                    validate_decoded_pattern(&attribute.value, spec, &format!("-{id}"))?;
                }
                if let Some(previous) = terms.get(&id) {
                    let current_span = term.id.name.range();
                    let previous_span = previous.id.name.range();
                    let (related_line, related_column) =
                        line_column(&spec.source, previous_span.start);
                    return Err(Failure::new(
                        "I18N_DUPLICATE_TERM",
                        format!("term -{id} is defined twice"),
                    )
                    .at(
                        &spec.path,
                        &spec.source,
                        current_span.start,
                        current_span.end,
                    )
                    .for_message(&format!("-{id}"))
                    .with_related(DiagnosticRelated {
                        message: "previous definition is here".to_owned(),
                        path: spec.path.clone(),
                        start: previous_span.start,
                        end: previous_span.end,
                        line: related_line,
                        column: related_column,
                    }));
                }
                terms.insert(id, term);
            }
            Entry::Junk { .. } => {
                return Err(Failure::new(
                    "I18N_FTL_JUNK",
                    format!("catalog {:?} contains an unparsed Junk entry", spec.path),
                ));
            }
            _ => {}
        }
    }
    Ok(ParsedCatalog {
        digest: digest_text(&spec.source),
        messages,
        terms,
    })
}

fn validate_decoded_pattern(
    pattern: &Pattern<SpannedSlice>,
    spec: &CatalogSpec,
    message_id: &str,
) -> Result<(), Failure> {
    let mut unsafe_span = None;
    walk_pattern(pattern, &mut |inline| {
        if unsafe_span.is_none()
            && let InlineExpression::StringLiteral { value } = inline
            && contains_decoded_bidi_control(value.as_ref())
        {
            unsafe_span = inline_span(inline, &spec.source).ok();
        }
    });
    if let Some(span) = unsafe_span {
        return Err(Failure::new(
            "I18N_BIDI_CONTROL_CATALOG",
            "decoded Fluent string contains a prohibited bidi-control character",
        )
        .at(&spec.path, &spec.source, span.start, span.end)
        .for_message(message_id));
    }
    Ok(())
}

fn internal_id(locale: &str, key: &OutputKey, catalog: &LoadedCatalog) -> String {
    let identity = format!(
        "v1\0{locale}\0{}\0{}\0{}\0{}",
        key.token(),
        catalog.spec.package,
        catalog.spec.layer,
        catalog.spec.path
    );
    format!("citry-{}", &digest_text(&identity)[..20])
}

fn term_internal_id(locale: &str, term: &str, catalog: &LoadedCatalog) -> String {
    let identity = format!(
        "v1-term\0{locale}\0{term}\0{}\0{}\0{}",
        catalog.spec.package, catalog.spec.layer, catalog.spec.path
    );
    format!("citry-term-{}", &digest_text(&identity)[..20])
}

#[derive(Debug)]
struct RenderedOperation {
    kind: &'static str,
    detail: Option<String>,
    authored: Range<usize>,
    generated: Range<usize>,
}

#[derive(Debug)]
struct PendingSourceMap {
    output: String,
    internal_id: String,
    authored_path: String,
    authored_source: String,
    generated_locale: String,
    operation: RenderedOperation,
}

#[derive(Debug, Default)]
struct RenderedPattern {
    source: String,
    operations: Vec<RenderedOperation>,
}

impl RenderedPattern {
    fn push_nested(&mut self, nested: RenderedPattern) {
        let offset = self.source.len();
        self.source.push_str(&nested.source);
        self.operations
            .extend(nested.operations.into_iter().map(|mut operation| {
                operation.generated =
                    operation.generated.start + offset..operation.generated.end + offset;
                operation
            }));
    }

    fn push_operation(
        &mut self,
        source: String,
        kind: &'static str,
        detail: Option<String>,
        authored: Range<usize>,
    ) {
        let start = self.source.len();
        self.source.push_str(&source);
        self.operations.push(RenderedOperation {
            kind,
            detail,
            authored,
            generated: start..self.source.len(),
        });
    }
}

fn contains_bidi_control(value: &str) -> bool {
    value
        .chars()
        .any(|character| BIDI_CONTROLS.contains(&character))
}

fn contains_decoded_bidi_control(value: &str) -> bool {
    if contains_bidi_control(value) {
        return true;
    }
    let bytes = value.as_bytes();
    let mut index = 0usize;
    while index < bytes.len() {
        let digits = if bytes.get(index..index + 2) == Some(b"\\u") {
            4
        } else if bytes.get(index..index + 2) == Some(b"\\U") {
            6
        } else {
            index += 1;
            continue;
        };
        let end = index + 2 + digits;
        if let Some(hex) = value.get(index + 2..end)
            && hex.bytes().all(|byte| byte.is_ascii_hexdigit())
            && let Ok(codepoint) = u32::from_str_radix(hex, 16)
            && let Some(character) = char::from_u32(codepoint)
            && BIDI_CONTROLS.contains(&character)
        {
            return true;
        }
        index = end.min(bytes.len());
    }
    false
}

fn contains_paragraph_boundary(value: &str) -> bool {
    value
        .chars()
        .any(|character| BIDI_PARAGRAPH_BOUNDARIES.contains(&character))
}

fn inline_span(
    inline: &InlineExpression<SpannedSlice>,
    source: &str,
) -> Result<Range<usize>, Failure> {
    let span = match inline {
        InlineExpression::StringLiteral { value } => {
            let start = value.range().start.checked_sub(1).ok_or_else(|| {
                Failure::new(
                    "I18N_INTERNAL_SOURCE_MAP",
                    "string literal has no opening quote",
                )
            })?;
            start..value.range().end + 1
        }
        InlineExpression::NumberLiteral { value } => value.range(),
        InlineExpression::VariableReference { id } => {
            let start = id.name.range().start.checked_sub(1).ok_or_else(|| {
                Failure::new("I18N_INTERNAL_SOURCE_MAP", "variable has no dollar sign")
            })?;
            start..id.name.range().end
        }
        InlineExpression::MessageReference { id, attribute } => {
            id.name.range().start
                ..attribute
                    .as_ref()
                    .map_or(id.name.range().end, |item| item.name.range().end)
        }
        InlineExpression::TermReference {
            id,
            attribute,
            arguments,
        } => {
            let start = id.name.range().start.checked_sub(1).ok_or_else(|| {
                Failure::new("I18N_INTERNAL_SOURCE_MAP", "term has no leading hyphen")
            })?;
            let base_end = attribute
                .as_ref()
                .map_or(id.name.range().end, |item| item.name.range().end);
            start
                ..arguments
                    .as_ref()
                    .map_or(Ok(base_end), |_| call_end(source, base_end))?
        }
        InlineExpression::FunctionReference { id, .. } => {
            id.name.range().start..call_end(source, id.name.range().end)?
        }
        InlineExpression::Placeable { expression } => expression_span(expression, source)?,
    };
    if span.start > span.end
        || span.end > source.len()
        || !source.is_char_boundary(span.start)
        || !source.is_char_boundary(span.end)
    {
        return Err(Failure::new(
            "I18N_INTERNAL_SOURCE_MAP",
            format!("invalid operation range {span:?}"),
        ));
    }
    Ok(span)
}

fn expression_span(
    expression: &Expression<SpannedSlice>,
    source: &str,
) -> Result<Range<usize>, Failure> {
    match expression {
        Expression::Inline(inline) => inline_span(inline, source),
        Expression::Select { selector, variants } => {
            let start = inline_span(selector, source)?.start;
            let end = variants
                .last()
                .and_then(|variant| variant.value.elements.last())
                .map(pattern_element_end)
                .ok_or_else(|| {
                    Failure::new("I18N_INTERNAL_SOURCE_MAP", "select has no variants")
                })?;
            Ok(start..end)
        }
    }
}

fn pattern_element_end(element: &PatternElement<SpannedSlice>) -> usize {
    match element {
        PatternElement::TextElement { value } => value.range().end,
        PatternElement::Placeable { expression } => match expression {
            Expression::Inline(inline) => inline_leaf_end(inline),
            Expression::Select { variants, .. } => variants
                .last()
                .and_then(|variant| variant.value.elements.last())
                .map_or(0, pattern_element_end),
        },
    }
}

fn inline_leaf_end(inline: &InlineExpression<SpannedSlice>) -> usize {
    match inline {
        InlineExpression::StringLiteral { value } | InlineExpression::NumberLiteral { value } => {
            value.range().end
        }
        InlineExpression::VariableReference { id }
        | InlineExpression::MessageReference {
            id,
            attribute: None,
        }
        | InlineExpression::TermReference {
            id,
            attribute: None,
            arguments: None,
        }
        | InlineExpression::FunctionReference { id, .. } => id.name.range().end,
        InlineExpression::MessageReference {
            attribute: Some(attribute),
            ..
        }
        | InlineExpression::TermReference {
            attribute: Some(attribute),
            ..
        } => attribute.name.range().end,
        InlineExpression::TermReference {
            id,
            attribute: None,
            arguments: Some(_),
        } => id.name.range().end,
        InlineExpression::Placeable { expression } => match expression.as_ref() {
            Expression::Inline(nested) => inline_leaf_end(nested),
            Expression::Select { variants, .. } => variants
                .last()
                .and_then(|variant| variant.value.elements.last())
                .map_or(0, pattern_element_end),
        },
    }
}

fn call_end(source: &str, after_callee: usize) -> Result<usize, Failure> {
    let bytes = source.as_bytes();
    let mut open = after_callee;
    while bytes.get(open).is_some_and(u8::is_ascii_whitespace) {
        open += 1;
    }
    if bytes.get(open) != Some(&b'(') {
        return Err(Failure::new(
            "I18N_INTERNAL_SOURCE_MAP",
            format!("expected call parenthesis after byte {after_callee}"),
        ));
    }
    let mut depth = 0usize;
    let mut quoted = false;
    let mut escaped = false;
    for (index, byte) in bytes.iter().copied().enumerate().skip(open) {
        if quoted {
            if escaped {
                escaped = false;
            } else if byte == b'\\' {
                escaped = true;
            } else if byte == b'"' {
                quoted = false;
            }
            continue;
        }
        if byte == b'"' {
            quoted = true;
        } else if byte == b'(' {
            depth += 1;
        } else if byte == b')' {
            depth = depth.checked_sub(1).ok_or_else(|| {
                Failure::new("I18N_INTERNAL_SOURCE_MAP", "unbalanced call parenthesis")
            })?;
            if depth == 0 {
                return Ok(index + 1);
            }
        }
    }
    Err(Failure::new(
        "I18N_INTERNAL_SOURCE_MAP",
        format!("unterminated call after byte {after_callee}"),
    ))
}

fn render_pattern(
    pattern: &Pattern<SpannedSlice>,
    key: &OutputKey,
    catalog_index: usize,
    graph: &ResolutionGraph,
    linker: &Linker,
    contract: &Contract,
) -> Result<RenderedPattern, Failure> {
    let mut result = RenderedPattern::default();
    for element in &pattern.elements {
        match element {
            PatternElement::TextElement { value } => {
                if contains_bidi_control(value.as_ref()) {
                    let definition = graph.messages[key];
                    let catalog = &linker.catalogs[definition.catalog];
                    return Err(Failure::new(
                        "I18N_BIDI_CONTROL_CATALOG",
                        "decoded catalog text contains a prohibited bidi-control character",
                    )
                    .at(
                        &catalog.spec.path,
                        &catalog.spec.source,
                        value.range().start,
                        value.range().end,
                    )
                    .for_message(&key.message_id));
                }
                result.source.push_str(value.as_ref());
            }
            PatternElement::Placeable { expression } => {
                result.source.push_str("{ ");
                result.push_nested(render_expression(
                    expression,
                    key,
                    catalog_index,
                    graph,
                    linker,
                    contract,
                )?);
                result.source.push_str(" }");
            }
        }
    }
    Ok(result)
}

fn render_expression(
    expression: &Expression<SpannedSlice>,
    key: &OutputKey,
    catalog_index: usize,
    graph: &ResolutionGraph,
    linker: &Linker,
    contract: &Contract,
) -> Result<RenderedPattern, Failure> {
    match expression {
        Expression::Inline(inline) => {
            render_inline(inline, key, catalog_index, graph, linker, contract)
        }
        Expression::Select { selector, variants } => render_select(
            selector,
            variants,
            key,
            catalog_index,
            graph,
            linker,
            contract,
        ),
    }
}

fn render_inline(
    inline: &InlineExpression<SpannedSlice>,
    key: &OutputKey,
    catalog_index: usize,
    graph: &ResolutionGraph,
    linker: &Linker,
    contract: &Contract,
) -> Result<RenderedPattern, Failure> {
    let catalog = &linker.catalogs[catalog_index];
    let authored = inline_span(inline, &catalog.spec.source)?;
    let mut result = RenderedPattern::default();
    match inline {
        InlineExpression::VariableReference { id } => {
            let name = text(&id.name);
            let type_name = contract.get(name).ok_or_else(|| {
                Failure::new(
                    "I18N_INTERNAL_CONTRACT",
                    format!("no source type for ${name}"),
                )
            })?;
            let (function, kind) = match type_name.as_str() {
                "str" | "scalar" => ("CITRY_TEXT", "scalar"),
                "Slot" => ("SLOT", "slot"),
                _ => {
                    return Err(Failure::new(
                        "I18N_FORMAT_REQUIRED",
                        format!("${name} has type {type_name} and must use NUMBER or DATETIME"),
                    )
                    .at(
                        &catalog.spec.path,
                        &catalog.spec.source,
                        authored.start,
                        authored.end,
                    )
                    .for_message(&key.message_id));
                }
            };
            result.push_operation(
                format!("{function}(${name})"),
                kind,
                Some(name.to_owned()),
                authored,
            );
        }
        InlineExpression::MessageReference { id, attribute } => {
            let reference = OutputKey {
                message_id: text(&id.name).to_owned(),
                attribute: attribute.as_ref().map(|item| text(&item.name).to_owned()),
            };
            let definition = graph.messages.get(&reference).ok_or_else(|| {
                Failure::new(
                    "I18N_INTERNAL_GRAPH",
                    format!(
                        "linked graph omitted public reference {:?}",
                        reference.token()
                    ),
                )
            })?;
            result.push_operation(
                internal_id(
                    &graph.locale,
                    &reference,
                    &linker.catalogs[definition.catalog],
                ),
                "public-reference",
                Some(reference.token()),
                authored,
            );
        }
        InlineExpression::TermReference {
            id,
            attribute: None,
            arguments: None,
        } => {
            let name = text(&id.name);
            result.push_operation(
                term_internal_id(&graph.locale, name, catalog),
                "private-term",
                Some(format!("-{name}")),
                authored,
            );
        }
        InlineExpression::StringLiteral { value } => {
            if contains_decoded_bidi_control(value.as_ref()) {
                return Err(Failure::new(
                    "I18N_BIDI_CONTROL_CATALOG",
                    "decoded Fluent string contains a prohibited bidi-control character",
                )
                .at(
                    &catalog.spec.path,
                    &catalog.spec.source,
                    authored.start,
                    authored.end,
                )
                .for_message(&key.message_id));
            }
            result
                .source
                .push_str(&format!("\"{}\"", value.as_ref().replace('"', "\\\"")));
        }
        InlineExpression::NumberLiteral { value } => result.source.push_str(value.as_ref()),
        InlineExpression::FunctionReference { id, arguments } => {
            render_formatter(
                text(&id.name),
                arguments,
                key,
                contract,
                catalog,
                authored,
                &mut result,
            )?;
        }
        InlineExpression::Placeable { expression } => {
            result.source.push_str("{ ");
            result.push_nested(render_expression(
                expression,
                key,
                catalog_index,
                graph,
                linker,
                contract,
            )?);
            result.source.push_str(" }");
        }
        InlineExpression::TermReference { .. } => {
            return Err(Failure::new(
                "I18N_PHASE0_SUBSET_EXPRESSION",
                "term attributes and term arguments are outside this compiler slice",
            )
            .at(
                &catalog.spec.path,
                &catalog.spec.source,
                authored.start,
                authored.end,
            )
            .for_message(&key.message_id));
        }
    }
    Ok(result)
}

fn render_formatter(
    function: &str,
    arguments: &CallArguments<SpannedSlice>,
    key: &OutputKey,
    contract: &Contract,
    catalog: &LoadedCatalog,
    authored: Range<usize>,
    result: &mut RenderedPattern,
) -> Result<(), Failure> {
    if !matches!(function, "NUMBER" | "DATETIME") {
        return Err(Failure::new(
            "I18N_FUNCTION_UNSUPPORTED",
            format!("authored function {function} is not supported"),
        )
        .at(
            &catalog.spec.path,
            &catalog.spec.source,
            authored.start,
            authored.end,
        )
        .for_message(&key.message_id));
    }
    let [InlineExpression::VariableReference { id }] = arguments.positional.as_slice() else {
        return Err(Failure::new(
            "I18N_FORMAT_OPERAND",
            format!("{function} requires exactly one variable operand"),
        )
        .at(
            &catalog.spec.path,
            &catalog.spec.source,
            authored.start,
            authored.end,
        )
        .for_message(&key.message_id));
    };
    let name = text(&id.name);
    let expected_types: &[&str] = if function == "NUMBER" {
        &["int", "Decimal"]
    } else {
        &["datetime"]
    };
    let type_name = contract.get(name).map(String::as_str);
    if !type_name.is_some_and(|item| expected_types.contains(&item)) {
        return Err(Failure::new(
            "I18N_FORMAT_TYPE",
            format!("{function} cannot format ${name} with type {type_name:?}"),
        )
        .at(
            &catalog.spec.path,
            &catalog.spec.source,
            authored.start,
            authored.end,
        )
        .for_message(&key.message_id));
    }
    if arguments.named.len() != 1 {
        return Err(Failure::new(
            "I18N_FORMAT_PROFILE",
            format!("{function} requires one literal profile and no other options"),
        )
        .at(
            &catalog.spec.path,
            &catalog.spec.source,
            authored.start,
            authored.end,
        )
        .for_message(&key.message_id));
    }
    let profile = &arguments.named[0];
    if text(&profile.name.name) != "profile" {
        return Err(Failure::new(
            "I18N_FORMAT_PROFILE",
            format!("{function} requires a literal profile"),
        )
        .at(
            &catalog.spec.path,
            &catalog.spec.source,
            authored.start,
            authored.end,
        )
        .for_message(&key.message_id));
    }
    let InlineExpression::StringLiteral { value } = &profile.value else {
        return Err(Failure::new(
            "I18N_FORMAT_PROFILE",
            format!("{function} profile must be a string literal"),
        )
        .at(
            &catalog.spec.path,
            &catalog.spec.source,
            authored.start,
            authored.end,
        )
        .for_message(&key.message_id));
    };
    let profile = value.as_ref();
    if profile.is_empty()
        || !profile.chars().all(|character| {
            character == '-' || character == '_' || character.is_ascii_alphanumeric()
        })
    {
        return Err(Failure::new(
            "I18N_FORMAT_PROFILE",
            format!("invalid formatter profile {profile:?}"),
        )
        .at(
            &catalog.spec.path,
            &catalog.spec.source,
            authored.start,
            authored.end,
        )
        .for_message(&key.message_id));
    }
    result.push_operation(
        format!("{function}(${name}, profile: \"{profile}\")"),
        if function == "NUMBER" {
            "number"
        } else {
            "datetime"
        },
        Some(profile.to_owned()),
        authored,
    );
    Ok(())
}

fn render_select(
    selector: &InlineExpression<SpannedSlice>,
    variants: &[ast::Variant<SpannedSlice>],
    key: &OutputKey,
    catalog_index: usize,
    graph: &ResolutionGraph,
    linker: &Linker,
    contract: &Contract,
) -> Result<RenderedPattern, Failure> {
    let catalog = &linker.catalogs[catalog_index];
    let authored = inline_span(selector, &catalog.spec.source)?;
    let mut seen_identifiers = BTreeSet::new();
    for variant in variants {
        if let VariantKey::Identifier { name } = &variant.key
            && !seen_identifiers.insert(name.as_ref())
        {
            let range = name.range();
            return Err(Failure::new(
                "I18N_SELECTOR_VARIANT_DUPLICATE",
                format!(
                    "selector variant {:?} is declared more than once",
                    name.as_ref()
                ),
            )
            .at(
                &catalog.spec.path,
                &catalog.spec.source,
                range.start,
                range.end,
            )
            .for_message(&key.message_id));
        }
    }
    let (variable, mode) = match selector {
        InlineExpression::VariableReference { id } => (text(&id.name), "cardinal"),
        InlineExpression::FunctionReference { id, arguments } if text(&id.name) == "NUMBER" => {
            let [InlineExpression::VariableReference { id }] = arguments.positional.as_slice()
            else {
                return Err(Failure::new(
                    "I18N_ORDINAL_SELECTOR",
                    "ordinal selector requires exactly one variable",
                )
                .at(
                    &catalog.spec.path,
                    &catalog.spec.source,
                    authored.start,
                    authored.end,
                )
                .for_message(&key.message_id));
            };
            let ordinal = arguments.named.len() == 1
                && text(&arguments.named[0].name.name) == "type"
                && matches!(
                    &arguments.named[0].value,
                    InlineExpression::StringLiteral { value } if value.as_ref() == "ordinal"
                );
            if !ordinal {
                return Err(Failure::new(
                    "I18N_SELECTOR_UNSUPPORTED",
                    "NUMBER selector must use the literal option type: \"ordinal\"",
                )
                .at(
                    &catalog.spec.path,
                    &catalog.spec.source,
                    authored.start,
                    authored.end,
                )
                .for_message(&key.message_id));
            }
            (text(&id.name), "ordinal")
        }
        _ => {
            return Err(Failure::new(
                "I18N_SELECTOR_UNSUPPORTED",
                "selector must be a numeric variable or NUMBER($value, type: \"ordinal\")",
            )
            .at(
                &catalog.spec.path,
                &catalog.spec.source,
                authored.start,
                authored.end,
            )
            .for_message(&key.message_id));
        }
    };
    let type_name = contract.get(variable).map(String::as_str);
    if mode == "cardinal" && type_name == Some("str") {
        if variants
            .iter()
            .any(|variant| matches!(variant.key, VariantKey::NumberLiteral { .. }))
        {
            return Err(Failure::new(
                "I18N_STRING_SELECTOR_NUMBER_VARIANT",
                format!("string selector ${variable} cannot use numeric variants"),
            )
            .at(
                &catalog.spec.path,
                &catalog.spec.source,
                authored.start,
                authored.end,
            )
            .for_message(&key.message_id));
        }
        let mut result = RenderedPattern::default();
        result.source.push('$');
        result.source.push_str(variable);
        result.source.push_str(" ->");
        for variant in variants {
            result.source.push_str("\n    ");
            if variant.default {
                result.source.push('*');
            }
            let VariantKey::Identifier { name } = &variant.key else {
                unreachable!("numeric variants were rejected above");
            };
            result.source.push('[');
            result.source.push_str(name.as_ref());
            result.source.push_str("] ");
            result.push_nested(render_pattern(
                &variant.value,
                key,
                catalog_index,
                graph,
                linker,
                contract,
            )?);
        }
        result.source.push('\n');
        return Ok(result);
    }
    if !matches!(type_name, Some("int" | "Decimal")) {
        return Err(Failure::new(
            "I18N_SELECTOR_TYPE",
            format!("selector ${variable} must have type int or Decimal"),
        )
        .at(
            &catalog.spec.path,
            &catalog.spec.source,
            authored.start,
            authored.end,
        )
        .for_message(&key.message_id));
    }
    let mut exact = Vec::<(String, String)>::new();
    let mut seen_exact = BTreeSet::new();
    for variant in variants {
        let VariantKey::NumberLiteral { value } = &variant.key else {
            continue;
        };
        let normalized = normalized_decimal(value.as_ref()).ok_or_else(|| {
            Failure::new(
                "I18N_EXACT_SELECTOR_VALUE",
                format!(
                    "exact selector value {:?} is not canonical numeric input",
                    value.as_ref()
                ),
            )
            .at(
                &catalog.spec.path,
                &catalog.spec.source,
                value.range().start,
                value.range().end,
            )
            .for_message(&key.message_id)
        })?;
        if !seen_exact.insert(normalized.clone()) {
            return Err(Failure::new(
                "I18N_EXACT_SELECTOR_DUPLICATE",
                format!("exact selector value {normalized:?} is declared more than once"),
            )
            .at(
                &catalog.spec.path,
                &catalog.spec.source,
                value.range().start,
                value.range().end,
            )
            .for_message(&key.message_id));
        }
        exact.push((
            normalized.clone(),
            format!("exact-{}", digest_text(&normalized)),
        ));
    }
    for variant in variants {
        if let VariantKey::Identifier { name } = &variant.key
            && !matches!(
                name.as_ref(),
                "zero" | "one" | "two" | "few" | "many" | "other"
            )
        {
            let range = name.range();
            return Err(Failure::new(
                "I18N_SELECTOR_VARIANT",
                format!("unsupported plural category {:?}", name.as_ref()),
            )
            .at(
                &catalog.spec.path,
                &catalog.spec.source,
                range.start,
                range.end,
            )
            .for_message(&key.message_id));
        }
    }
    let mut result = RenderedPattern::default();
    let mut selector_source = format!("CITRY_PLURAL(${variable}");
    if !exact.is_empty() {
        selector_source.push_str(&format!(
            ", exact: \"{}\"",
            exact
                .iter()
                .map(|(value, key)| format!("{value}:{key}"))
                .collect::<Vec<_>>()
                .join(",")
        ));
    }
    if mode == "ordinal" {
        selector_source.push_str(", mode: \"ordinal\"");
    }
    selector_source.push(')');
    result.push_operation(
        selector_source,
        if mode == "ordinal" {
            "ordinal-selector"
        } else {
            "plural-selector"
        },
        (!exact.is_empty()).then(|| {
            exact
                .iter()
                .map(|(value, _)| value.clone())
                .collect::<Vec<_>>()
                .join(",")
        }),
        authored,
    );
    result.source.push_str(" ->");
    for variant in variants {
        result.source.push_str("\n    ");
        if variant.default {
            result.source.push('*');
        }
        match &variant.key {
            VariantKey::Identifier { name } => {
                result.source.push('[');
                result.source.push_str(name.as_ref());
                result.source.push_str("] ");
            }
            VariantKey::NumberLiteral { value } => {
                let normalized = normalized_decimal(value.as_ref())
                    .expect("exact selector values were validated above");
                let (_, generated_key) = exact
                    .iter()
                    .find(|(candidate, _)| candidate == &normalized)
                    .expect("exact selector mapping was built above");
                result.source.push('[');
                result.source.push_str(generated_key);
                result.source.push_str("] ");
            }
        }
        result.push_nested(render_pattern(
            &variant.value,
            key,
            catalog_index,
            graph,
            linker,
            contract,
        )?);
    }
    result.source.push('\n');
    Ok(result)
}

fn compile_request(
    state: &mut CompilerState,
    mut request: CompileRequest,
) -> Result<CompileResult, Failure> {
    if request.schema_version != SCHEMA_VERSION {
        return Err(Failure::new(
            "I18N_SCHEMA_VERSION",
            format!(
                "expected schema_version {SCHEMA_VERSION}, got {}",
                request.schema_version
            ),
        ));
    }
    if request.active_locales.is_empty() {
        return Err(Failure::new(
            "I18N_NO_ACTIVE_LOCALES",
            "active_locales must not be empty",
        ));
    }
    let linked_catalogs = expand_link_units(&mut request)?;
    validate_request_locales(&request, &linked_catalogs)?;
    let format_registry = FormatRegistry::new(request.formats.clone())?;
    let request_paths: BTreeSet<_> = request.catalogs.iter().map(source_unit_identity).collect();
    let before_paths: BTreeSet<_> = state.cache.keys().cloned().collect();
    state.cache.retain(|path, _| request_paths.contains(path));
    let evicted_catalogs = before_paths.difference(&request_paths).count();

    let mut parsed_catalogs = 0;
    let mut reused_catalogs = 0;
    let mut invalidated_catalogs = 0;
    let mut specs = request.catalogs.clone();
    specs.sort_by(|left, right| {
        (
            left.package.as_str(),
            left.locale.as_str(),
            left.precedence,
            left.layer.as_str(),
            left.path.as_str(),
        )
            .cmp(&(
                right.package.as_str(),
                right.locale.as_str(),
                right.precedence,
                right.layer.as_str(),
                right.path.as_str(),
            ))
    });
    let mut catalogs = linked_catalogs;
    for mut spec in specs {
        let digest = digest_text(&spec.source);
        let source_unit_id = source_unit_identity(&spec);
        let parsed = match state.cache.get(&source_unit_id) {
            Some(cached) if cached.digest == digest => {
                reused_catalogs += 1;
                Arc::clone(cached)
            }
            previous => {
                if previous.is_some() {
                    invalidated_catalogs += 1;
                }
                parsed_catalogs += 1;
                let parsed = Arc::new(parse_catalog(&spec)?);
                state.cache.insert(source_unit_id, Arc::clone(&parsed));
                parsed
            }
        };
        if spec.entry_spans.is_empty() {
            spec.entry_spans = catalog_entry_spans(&parsed);
        }
        catalogs.push(LoadedCatalog { spec, parsed });
    }

    let linker = Linker::new(&request, catalogs)?;
    let diagnostics = missing_param_diagnostics(&linker)?;
    let outputs = linker.public_outputs();
    let mut bundles = BTreeMap::<String, BTreeMap<String, String>>::new();
    let mut manifest = BTreeMap::<String, BTreeMap<String, ManifestEntry>>::new();
    let mut pending_maps = vec![];
    let mut linked_outputs = 0;

    let mut active_locales = request.active_locales.clone();
    active_locales.sort();
    active_locales.dedup();
    for active_locale in active_locales {
        let mut locale_manifest = BTreeMap::new();
        for root in &outputs {
            let interface = linker.source_interface(root)?;
            let contract: Contract = interface
                .iter()
                .map(|(name, metadata)| (name.clone(), metadata.type_name.clone()))
                .collect();
            let graph = linker.resolve(&active_locale, root)?;
            linker.validate_graph_contract(root, &graph, &contract)?;
            linker.validate_slots(root, &graph, &contract)?;
            for (key, definition) in &graph.messages {
                let catalog = &linker.catalogs[definition.catalog];
                let key_contract = linker.source_contract(key)?;
                let pattern = pattern_for(catalog, key).expect("linked pattern");
                let generated = render_pattern(
                    pattern,
                    key,
                    definition.catalog,
                    &graph,
                    &linker,
                    &key_contract,
                )?;
                let id = internal_id(&graph.locale, key, catalog);
                let source = format!("{id} = {}\n", generated.source);
                let previous = bundles
                    .entry(graph.locale.clone())
                    .or_default()
                    .insert(id.clone(), source.clone());
                if previous.as_ref().is_some_and(|item| item != &source) {
                    return Err(Failure::new(
                        "I18N_INTERNAL_ID_COLLISION",
                        format!("internal ID {id:?} identifies different messages"),
                    ));
                }
                pending_maps.extend(generated.operations.into_iter().map(|operation| {
                    PendingSourceMap {
                        output: key.token(),
                        internal_id: id.clone(),
                        authored_path: catalog.spec.path.clone(),
                        authored_source: catalog.spec.source.clone(),
                        generated_locale: graph.locale.clone(),
                        operation,
                    }
                }));
            }
            for (catalog_index, term) in &graph.terms {
                let catalog = &linker.catalogs[*catalog_index];
                let term_node = &catalog.parsed.terms[term];
                let id = term_internal_id(&graph.locale, term, catalog);
                let generated = render_pattern(
                    &term_node.value,
                    root,
                    *catalog_index,
                    &graph,
                    &linker,
                    &Contract::new(),
                )?;
                let source = format!("{id} = {}\n", generated.source);
                let previous = bundles
                    .entry(graph.locale.clone())
                    .or_default()
                    .insert(id.clone(), source.clone());
                if previous.as_ref().is_some_and(|item| item != &source) {
                    return Err(Failure::new(
                        "I18N_INTERNAL_ID_COLLISION",
                        format!("internal term ID {id:?} identifies different terms"),
                    ));
                }
                pending_maps.extend(generated.operations.into_iter().map(|operation| {
                    PendingSourceMap {
                        output: root.token(),
                        internal_id: id.clone(),
                        authored_path: catalog.spec.path.clone(),
                        authored_source: catalog.spec.source.clone(),
                        generated_locale: graph.locale.clone(),
                        operation,
                    }
                }));
            }
            let root_definition = graph.messages[root];
            let selected = &linker.catalogs[root_definition.catalog];
            let owner = linker.owners[&root.message_id].clone();
            let source_definition = linker.owner_source_definition(root)?;
            let source_catalog = &linker.catalogs[source_definition.catalog];
            let definition_span = output_span(source_catalog, root);
            let (definition_line, definition_column) =
                line_column(&source_catalog.spec.source, definition_span.start);
            locale_manifest.insert(
                root.token(),
                ManifestEntry {
                    owner_source_locale: linker.packages[&owner].source_locale.clone(),
                    owner,
                    definition_path: source_catalog.spec.path.clone(),
                    definition_start: definition_span.start,
                    definition_end: definition_span.end,
                    definition_line,
                    definition_column,
                    bundle_locale: graph.locale.clone(),
                    internal_id: internal_id(&graph.locale, root, selected),
                    contract,
                    interface,
                    selected_layer: selected.spec.layer.clone(),
                    selected_path: selected.spec.path.clone(),
                },
            );
            linked_outputs += 1;
        }
        manifest.insert(active_locale, locale_manifest);
    }

    let mut artifacts = BTreeMap::new();
    for (locale, entries) in bundles {
        artifacts.insert(locale, entries.values().cloned().collect::<String>());
    }
    let mut source_maps = vec![];
    let mut seen_maps = BTreeSet::new();
    for pending in pending_maps {
        format_registry.validate_message_operation(
            pending.operation.kind,
            pending.operation.detail.as_deref(),
        )?;
        let identity = (
            pending.internal_id.clone(),
            pending.authored_path.clone(),
            pending.generated_locale.clone(),
            pending.operation.kind,
            pending.operation.authored.start,
            pending.operation.authored.end,
            pending.operation.generated.start,
            pending.operation.generated.end,
        );
        if !seen_maps.insert(identity) {
            continue;
        }
        let generated = &artifacts[&pending.generated_locale];
        let entry_start = generated
            .find(&format!("{} =", pending.internal_id))
            .ok_or_else(|| {
                Failure::new(
                    "I18N_INTERNAL_SOURCE_MAP",
                    format!("generated entry {:?} is missing", pending.internal_id),
                )
            })?;
        let value_start = entry_start + pending.internal_id.len() + 3;
        let generated_start = value_start + pending.operation.generated.start;
        let generated_end = value_start + pending.operation.generated.end;
        if generated.get(generated_start..generated_end).is_none() {
            return Err(Failure::new(
                "I18N_INTERNAL_SOURCE_MAP",
                format!("generated operation range {generated_start}..{generated_end} is invalid"),
            ));
        }
        let (authored_line, authored_column) =
            line_column(&pending.authored_source, pending.operation.authored.start);
        let (generated_line, generated_column) = line_column(generated, generated_start);
        source_maps.push(SourceMapEntry {
            output: pending.output,
            internal_id: pending.internal_id,
            authored_path: pending.authored_path,
            authored_start: pending.operation.authored.start,
            authored_end: pending.operation.authored.end,
            authored_line,
            authored_column,
            generated_locale: pending.generated_locale,
            generated_start,
            generated_end,
            generated_line,
            generated_column,
            kind: pending.operation.kind.to_owned(),
            detail: pending.operation.detail,
        });
    }
    source_maps.sort_by(|left, right| {
        (
            &left.generated_locale,
            &left.internal_id,
            &left.authored_path,
            left.authored_start,
            left.generated_start,
        )
            .cmp(&(
                &right.generated_locale,
                &right.internal_id,
                &right.authored_path,
                right.authored_start,
                right.generated_start,
            ))
    });

    let compiler_version = env!("CARGO_PKG_VERSION").to_owned();
    let revision_payload = serde_json::to_string(&(
        &compiler_version,
        &artifacts,
        &manifest,
        &source_maps,
        &diagnostics,
        &request.formats,
        format_registry.revision(),
    ))
    .map_err(|error| Failure::new("I18N_INTERNAL_JSON", error.to_string()))?;
    Ok(CompileResult {
        schema_version: SCHEMA_VERSION,
        compiler_version,
        revision: digest_text(&revision_payload),
        artifacts,
        manifest,
        source_maps,
        stats: CompileStats {
            parsed_catalogs,
            reused_catalogs,
            invalidated_catalogs,
            evicted_catalogs,
            linked_outputs,
        },
        formats: request.formats,
        formats_revision: format_registry.revision().to_owned(),
        diagnostics,
    })
}

/// Incremental checked catalog compiler.
pub struct CatalogCompiler {
    state: Mutex<CompilerState>,
}

impl CatalogCompiler {
    /// Create an empty compiler cache.
    pub fn new() -> Self {
        Self {
            state: Mutex::new(CompilerState::default()),
        }
    }

    /// Compile one complete project topology from strict JSON.
    pub fn compile(&self, request_json: &str) -> Result<String, Failure> {
        let request: CompileRequest = serde_json::from_str(request_json).map_err(|error| {
            Failure::new(
                "I18N_REQUEST_JSON",
                format!("invalid compile request: {error}"),
            )
        })?;
        let mut state = self.state.lock().map_err(|_| {
            Failure::new(
                "I18N_COMPILER_POISONED",
                "i18n compiler state mutex is poisoned",
            )
        })?;
        let result = compile_request(&mut state, request)?;
        serde_json::to_string(&result)
            .map_err(|error| Failure::new("I18N_INTERNAL_JSON", error.to_string()))
    }

    /// Compile authored package sources into checked, source-free linker input.
    pub fn compile_link_unit(&self, request_json: &str) -> Result<String, Failure> {
        let request: CompileRequest = serde_json::from_str(request_json).map_err(|error| {
            Failure::new(
                "I18N_REQUEST_JSON",
                format!("invalid compile request: {error}"),
            )
        })?;
        if !request.link_units.is_empty() {
            return Err(Failure::new(
                "I18N_LINK_UNIT_NESTED",
                "a package link unit must be compiled directly from authored catalogs",
            ));
        }
        let mut state = self.state.lock().map_err(|_| {
            Failure::new(
                "I18N_COMPILER_POISONED",
                "i18n compiler state mutex is poisoned",
            )
        })?;
        compile_request(&mut state, request.clone())?;
        let mut catalogs = request.catalogs;
        catalogs.sort_by_key(source_unit_identity);
        let catalogs = catalogs
            .into_iter()
            .map(|spec| {
                let parsed = state
                    .cache
                    .get(&source_unit_identity(&spec))
                    .ok_or_else(|| {
                        Failure::new(
                            "I18N_LINK_UNIT_CACHE",
                            format!("checked catalog {:?} was not retained", spec.path),
                        )
                    })?;
                Ok(LinkCatalog {
                    path: spec.path,
                    package: spec.package,
                    locale: spec.locale,
                    source_digest: parsed.digest.clone(),
                    diagnostic_layout: diagnostic_layout(&spec.source),
                    missing_param_type: spec.missing_param_type,
                    parsed: parsed.as_ref().clone(),
                })
            })
            .collect::<Result<Vec<_>, Failure>>()?;
        let revision = link_unit_revision(&request.packages, &catalogs)?;
        serde_json::to_string(&LinkUnit {
            schema_version: SCHEMA_VERSION,
            compiler_version: env!("CARGO_PKG_VERSION").to_owned(),
            revision,
            packages: request.packages,
            catalogs,
        })
        .map_err(|error| Failure::new("I18N_LINK_UNIT_JSON", error.to_string()))
    }

    /// Parse and validate one source unit for interactive editor tooling.
    pub fn analyze_source(&self, path: &str, source: &str) -> Result<String, Failure> {
        let mut spec = CatalogSpec {
            path: path.to_owned(),
            package: "citry-editor".to_owned(),
            layer: "citry-editor".to_owned(),
            precedence: 0,
            locale: "en-US".to_owned(),
            source: source.to_owned(),
            missing_param_type: MissingParamType::Warning,
            entry_spans: BTreeMap::new(),
        };
        let parsed = parse_catalog(&spec)?;
        spec.entry_spans = catalog_entry_spans(&parsed);

        let mut definitions = vec![];
        let mut references = vec![];
        for (message_id, message) in &parsed.messages {
            let declarations = parse_params(message, &spec)?;
            validate_message_annotations(message, &declarations, &spec)?;
            definitions.push(source_symbol(
                "message",
                message_id.clone(),
                message.id.name.range(),
            ));
            if let Some(value) = &message.value {
                collect_source_references(value, &mut references);
            }
            for attribute in &message.attributes {
                definitions.push(source_symbol(
                    "attribute",
                    format!("{message_id}.{}", text(&attribute.id.name)),
                    attribute.id.name.range(),
                ));
                collect_source_references(&attribute.value, &mut references);
            }
        }
        for (term_id, term) in &parsed.terms {
            definitions.push(source_symbol(
                "term",
                format!("-{term_id}"),
                term.id.name.range(),
            ));
            collect_source_references(&term.value, &mut references);
            for attribute in &term.attributes {
                collect_source_references(&attribute.value, &mut references);
            }
        }
        definitions.sort_by_key(|item| (item.start, item.end, item.token.clone()));
        references.sort_by_key(|item| (item.start, item.end, item.token.clone()));
        serde_json::to_string(&SourceAnalysis {
            schema_version: SCHEMA_VERSION,
            definitions,
            references,
        })
        .map_err(|error| Failure::new("I18N_INTERNAL_JSON", error.to_string()))
    }

    /// Clear every parsed-source cache entry.
    pub fn clear(&self) -> Result<(), Failure> {
        let mut state = self.state.lock().map_err(|_| {
            Failure::new(
                "I18N_COMPILER_POISONED",
                "i18n compiler state mutex is poisoned",
            )
        })?;
        state.cache.clear();
        Ok(())
    }
}

fn source_symbol(kind: &str, token: String, span: Range<usize>) -> SourceSymbol {
    SourceSymbol {
        kind: kind.to_owned(),
        token,
        start: span.start,
        end: span.end,
    }
}

fn collect_source_references(pattern: &Pattern<SpannedSlice>, result: &mut Vec<SourceSymbol>) {
    walk_pattern(pattern, &mut |inline| match inline {
        InlineExpression::MessageReference { id, attribute } => {
            let mut token = text(&id.name).to_owned();
            let mut span = id.name.range();
            if let Some(attribute) = attribute {
                token.push('.');
                token.push_str(text(&attribute.name));
                span.end = attribute.name.range().end;
            }
            result.push(source_symbol("message", token, span));
        }
        InlineExpression::TermReference { id, .. } => result.push(source_symbol(
            "term",
            format!("-{}", text(&id.name)),
            id.name.range(),
        )),
        _ => {}
    });
}

impl Default for CatalogCompiler {
    fn default() -> Self {
        Self::new()
    }
}

type RuntimeBundle = FluentBundle<Arc<FluentResource>>;

fn fluent_text(value: &FluentValue<'_>) -> Option<String> {
    match value {
        FluentValue::String(value) => Some(value.to_string()),
        FluentValue::Number(value) => Some(value.value.to_string()),
        _ => None,
    }
}

fn named_text(named: &FluentArgs<'_>, name: &str) -> Option<String> {
    named.get(name).and_then(fluent_text)
}

fn valid_integer(value: &str) -> bool {
    let unsigned = value.strip_prefix('-').unwrap_or(value);
    !unsigned.is_empty()
        && unsigned.bytes().all(|byte| byte.is_ascii_digit())
        && (unsigned == "0" || !unsigned.starts_with('0'))
        && value != "-0"
}

fn valid_decimal(value: &str) -> bool {
    let unsigned = value.strip_prefix('-').unwrap_or(value);
    let mut parts = unsigned.split('.');
    let integer = parts.next().unwrap_or("");
    let fraction = parts.next();
    parts.next().is_none()
        && !integer.is_empty()
        && integer.bytes().all(|byte| byte.is_ascii_digit())
        && (integer == "0" || !integer.starts_with('0'))
        && fraction
            .is_none_or(|part| !part.is_empty() && part.bytes().all(|byte| byte.is_ascii_digit()))
}

fn normalized_decimal(value: &str) -> Option<String> {
    if !valid_decimal(value) {
        return None;
    }
    let unsigned = value.strip_prefix('-').unwrap_or(value);
    let negative = value.starts_with('-');
    let (integer, fraction) = unsigned.split_once('.').unwrap_or((unsigned, ""));
    let fraction = fraction.trim_end_matches('0');
    let zero = integer == "0" && fraction.is_empty();
    let mut result = String::new();
    if negative && !zero {
        result.push('-');
    }
    result.push_str(integer);
    if !fraction.is_empty() {
        result.push('.');
        result.push_str(fraction);
    }
    Some(result)
}

fn plural_category(
    cardinal: &PluralRules,
    ordinal: &PluralRules,
    value: &str,
    exact: Option<&str>,
    mode: &str,
) -> Option<String> {
    let normalized = normalized_decimal(value)?;
    if let Some(exact) = exact {
        for candidate in exact.split(',') {
            let (candidate_value, generated_key) = candidate.split_once(':')?;
            if normalized_decimal(candidate_value).as_ref() == Some(&normalized) {
                return Some(generated_key.to_owned());
            }
        }
    }
    let decimal = value.parse::<Decimal>().ok()?;
    let category = match mode {
        "cardinal" => cardinal.category_for(&decimal),
        "ordinal" => ordinal.category_for(&decimal),
        _ => return None,
    };
    Some(
        match category {
            PluralCategory::Zero => "zero",
            PluralCategory::One => "one",
            PluralCategory::Two => "two",
            PluralCategory::Few => "few",
            PluralCategory::Many => "many",
            PluralCategory::Other => "other",
        }
        .to_owned(),
    )
}

fn register_runtime_functions(
    bundle: &mut RuntimeBundle,
    locale: &Locale,
    formats: &FormatRegistry,
) -> Result<(), Failure> {
    bundle
        .add_function("CITRY_TEXT", |positional, named| {
            if named.iter().next().is_some() {
                return FluentValue::Error;
            }
            match positional.first().and_then(fluent_text) {
                Some(value)
                    if !contains_bidi_control(&value) && !contains_paragraph_boundary(&value) =>
                {
                    format!("{FSI}{value}{PDI}").into()
                }
                _ => FluentValue::Error,
            }
        })
        .expect("CITRY_TEXT registration failed");
    bundle
        .add_function("SLOT", |positional, named| {
            if named.iter().next().is_some() {
                return FluentValue::Error;
            }
            match positional.first().and_then(fluent_text) {
                Some(value) if value.starts_with("__CITRY_SLOT_") && value.ends_with("__") => {
                    value.into()
                }
                _ => FluentValue::Error,
            }
        })
        .expect("SLOT registration failed");
    let number_formats = formats.clone();
    let number_locale = locale.to_string();
    bundle
        .add_function("NUMBER", move |positional, named| {
            let Some(value) = positional.first().and_then(fluent_text) else {
                return FluentValue::Error;
            };
            let Some(profile) = named_text(named, "profile") else {
                return FluentValue::Error;
            };
            if named.iter().count() != 1 {
                return FluentValue::Error;
            }
            number_formats
                .number(&number_locale, &profile, &value)
                .map(|result| FluentValue::from(format!("{FSI}{result}{PDI}")))
                .unwrap_or(FluentValue::Error)
        })
        .expect("NUMBER registration failed");
    let cardinal = PluralRules::try_new_cardinal(locale.clone().into()).map_err(|error| {
        Failure::new(
            "I18N_PLURAL_DATA",
            format!("could not load cardinal plural rules for {locale}: {error}"),
        )
    })?;
    let ordinal = PluralRules::try_new_ordinal(locale.clone().into()).map_err(|error| {
        Failure::new(
            "I18N_PLURAL_DATA",
            format!("could not load ordinal plural rules for {locale}: {error}"),
        )
    })?;
    bundle
        .add_function("CITRY_PLURAL", move |positional, named| {
            if named
                .iter()
                .any(|(name, _)| !matches!(name, "exact" | "mode"))
            {
                return FluentValue::Error;
            }
            let Some(value) = positional.first().and_then(fluent_text) else {
                return FluentValue::Error;
            };
            let exact = named_text(named, "exact");
            let mode = named_text(named, "mode").unwrap_or_else(|| "cardinal".to_owned());
            plural_category(&cardinal, &ordinal, &value, exact.as_deref(), &mode)
                .map(FluentValue::from)
                .unwrap_or(FluentValue::Error)
        })
        .expect("CITRY_PLURAL registration failed");
    Ok(())
}

#[derive(Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct TaggedArg {
    #[serde(rename = "type")]
    type_name: String,
    value: String,
}

fn expected_wire_tag(type_name: &str) -> Option<&'static str> {
    match type_name {
        "str" => Some("str"),
        "int" => Some("int"),
        "Decimal" => Some("decimal"),
        "datetime" => Some("datetime"),
        "Slot" => Some("slot"),
        "scalar" => Some("scalar"),
        _ => None,
    }
}

fn validate_tagged_arg(name: &str, type_name: &str, argument: &TaggedArg) -> Result<(), Failure> {
    let expected = expected_wire_tag(type_name).ok_or_else(|| {
        Failure::new(
            "I18N_ARGUMENT_TYPE_UNSUPPORTED",
            format!("unsupported source type {type_name:?} for ${name}"),
        )
    })?;
    if expected == "scalar" && !matches!(argument.type_name.as_str(), "str" | "int" | "decimal") {
        return Err(Failure::new(
            "I18N_ARGUMENT_TAG",
            format!(
                "${name} expects a safe scalar wire type, got {:?}",
                argument.type_name
            ),
        ));
    }
    if expected != "scalar" && argument.type_name != expected {
        return Err(Failure::new(
            "I18N_ARGUMENT_TAG",
            format!(
                "${name} expects wire type {expected:?}, got {:?}",
                argument.type_name
            ),
        ));
    }
    if contains_bidi_control(&argument.value) {
        return Err(Failure::new(
            "I18N_ARGUMENT_BIDI",
            format!("${name} contains a prohibited bidi-control character"),
        ));
    }
    if contains_paragraph_boundary(&argument.value) {
        return Err(Failure::new(
            "I18N_ARGUMENT_PARAGRAPH",
            format!("${name} contains a paragraph boundary"),
        ));
    }
    let validation_type = if type_name == "scalar" {
        argument.type_name.as_str()
    } else {
        type_name
    };
    let valid = match validation_type {
        "str" => true,
        "int" => valid_integer(&argument.value),
        "Decimal" | "decimal" => valid_decimal(&argument.value),
        "datetime" => {
            argument.value.is_ascii()
                && argument.value.contains('T')
                && (argument.value.ends_with('Z')
                    || argument
                        .value
                        .rsplit_once('T')
                        .is_some_and(|(_, tail)| tail.contains('+') || tail.contains('-')))
        }
        "Slot" => argument.value.starts_with("__CITRY_SLOT_") && argument.value.ends_with("__"),
        _ => false,
    };
    if !valid {
        return Err(Failure::new(
            "I18N_ARGUMENT_VALUE",
            format!("${name} has an invalid {type_name} wire value"),
        ));
    }
    Ok(())
}

/// Immutable checked runtime built from one compiled artifact.
pub struct I18nRuntime {
    revision: String,
    manifest: BTreeMap<String, BTreeMap<String, ManifestEntry>>,
    artifacts: BTreeMap<String, String>,
    bundles: BTreeMap<String, RuntimeBundle>,
    collision_text: String,
    formats: FormatRegistry,
}

/// Metadata and text produced by one checked resolution.
#[derive(Debug, Serialize)]
struct ResolvedMessage<'a> {
    text: String,
    requested_locale: &'a str,
    selected_locale: &'a str,
    owner: &'a str,
    owner_source_locale: &'a str,
    selected_layer: &'a str,
    selected_path: &'a str,
    used_fallback: bool,
}

/// One escaped-text or structural-Slot part of a rich message.
#[derive(Debug, Serialize)]
#[serde(tag = "type", rename_all = "snake_case")]
enum RichSegment {
    Text { value: String },
    Slot { name: String },
}

#[derive(Debug, Serialize)]
struct ResolvedRichMessage<'a> {
    segments: Vec<RichSegment>,
    requested_locale: &'a str,
    selected_locale: &'a str,
    owner: &'a str,
    owner_source_locale: &'a str,
    selected_layer: &'a str,
    selected_path: &'a str,
    used_fallback: bool,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct BrowserArtifactRequest {
    #[serde(default)]
    outputs: Vec<String>,
    #[serde(default)]
    messages: Vec<String>,
}

#[derive(Debug, Serialize)]
struct BrowserArtifact {
    schema_version: u32,
    runtime: &'static str,
    catalog_revision: String,
    formats_revision: String,
    requested_locale: String,
    messages: BTreeMap<String, BrowserMessageEntry>,
    bundles: BTreeMap<String, String>,
    revision: String,
}

#[derive(Debug, Serialize)]
struct BrowserMessageEntry {
    bundle_locale: String,
    internal_id: String,
    contract: Contract,
}

#[derive(Debug)]
struct CompiledBrowserEntry {
    id: String,
    start: usize,
    end: usize,
    references: BTreeSet<String>,
}

fn browser_bundle_subset(source: &str, roots: &BTreeSet<String>) -> Result<String, Failure> {
    let resource = fluent_syntax::parser::parse(SpannedSlice::root(source)).map_err(
        |(_resource, errors)| {
            Failure::new(
                "I18N_BROWSER_BUNDLE",
                format!("could not parse checked browser bundle: {errors:?}"),
            )
        },
    )?;
    let mut raw = Vec::<(String, usize, BTreeSet<String>)>::new();
    for entry in resource.body {
        let Entry::Message(message) = entry else {
            return Err(Failure::new(
                "I18N_BROWSER_BUNDLE",
                "checked browser bundle contains a non-message entry",
            ));
        };
        let mut references = BTreeSet::new();
        let mut inspect = |inline: &InlineExpression<SpannedSlice>| {
            if let InlineExpression::MessageReference { id, .. } = inline {
                references.insert(text(&id.name).to_owned());
            }
        };
        if let Some(value) = &message.value {
            walk_pattern(value, &mut inspect);
        }
        for attribute in &message.attributes {
            walk_pattern(&attribute.value, &mut inspect);
        }
        raw.push((
            text(&message.id.name).to_owned(),
            message.id.name.range().start,
            references,
        ));
    }
    raw.sort_by_key(|(_, start, _)| *start);
    let mut entries = Vec::with_capacity(raw.len());
    for (index, (id, start, references)) in raw.iter().enumerate() {
        let end = raw
            .get(index + 1)
            .map_or(source.len(), |(_, next, _)| *next);
        entries.push(CompiledBrowserEntry {
            id: id.clone(),
            start: *start,
            end,
            references: references.clone(),
        });
    }
    let by_id = entries
        .iter()
        .enumerate()
        .map(|(index, entry)| (entry.id.as_str(), index))
        .collect::<BTreeMap<_, _>>();
    let mut selected = BTreeSet::new();
    let mut pending = roots.iter().cloned().collect::<Vec<_>>();
    while let Some(id) = pending.pop() {
        if !selected.insert(id.clone()) {
            continue;
        }
        let entry = by_id.get(id.as_str()).ok_or_else(|| {
            Failure::new(
                "I18N_BROWSER_BUNDLE",
                format!("browser bundle closure refers to missing internal message {id:?}"),
            )
        })?;
        pending.extend(entries[*entry].references.iter().cloned());
    }
    let mut result = String::new();
    for entry in entries {
        if selected.contains(&entry.id) {
            result.push_str(&source[entry.start..entry.end]);
        }
    }
    Ok(result)
}

impl I18nRuntime {
    /// Decode and validate one compiled artifact.
    pub fn new(compiled_json: &str) -> Result<Self, Failure> {
        let compiled: CompileResult = serde_json::from_str(compiled_json).map_err(|error| {
            Failure::new(
                "I18N_ARTIFACT_JSON",
                format!("invalid compiled artifact: {error}"),
            )
        })?;
        if compiled.schema_version != SCHEMA_VERSION {
            return Err(Failure::new(
                "I18N_ARTIFACT_VERSION",
                format!(
                    "expected compiled schema {}, got {}",
                    SCHEMA_VERSION, compiled.schema_version
                ),
            ));
        }
        if compiled.compiler_version != env!("CARGO_PKG_VERSION") {
            return Err(Failure::new(
                "I18N_COMPILER_VERSION",
                format!(
                    "artifact compiler version {:?} does not match runtime version {:?}",
                    compiled.compiler_version,
                    env!("CARGO_PKG_VERSION")
                ),
            ));
        }
        let formats = FormatRegistry::new(compiled.formats.clone())?;
        if formats.revision() != compiled.formats_revision {
            return Err(Failure::new(
                "I18N_FORMAT_REVISION",
                "compiled format registry revision does not match its contents",
            ));
        }
        let revision_payload = serde_json::to_string(&(
            &compiled.compiler_version,
            &compiled.artifacts,
            &compiled.manifest,
            &compiled.source_maps,
            &compiled.diagnostics,
            &compiled.formats,
            formats.revision(),
        ))
        .map_err(|error| Failure::new("I18N_INTERNAL_JSON", error.to_string()))?;
        let expected_revision = digest_text(&revision_payload);
        if compiled.revision != expected_revision {
            return Err(Failure::new(
                "I18N_ARTIFACT_REVISION",
                "compiled artifact revision does not match its semantic contents",
            ));
        }
        for (active_locale, outputs) in &compiled.manifest {
            validate_locale(active_locale, "artifact manifest locale")?;
            for (token, entry) in outputs {
                if !compiled.artifacts.contains_key(&entry.bundle_locale) {
                    return Err(Failure::new(
                        "I18N_ARTIFACT_MANIFEST",
                        format!(
                            "manifest output {token:?} selects missing bundle {:?}",
                            entry.bundle_locale
                        ),
                    ));
                }
                let interface_contract = entry
                    .interface
                    .iter()
                    .map(|(name, metadata)| (name.clone(), metadata.type_name.clone()))
                    .collect::<Contract>();
                if interface_contract != entry.contract {
                    return Err(Failure::new(
                        "I18N_ARTIFACT_INTERFACE",
                        format!("manifest output {token:?} has conflicting contract metadata"),
                    ));
                }
                if entry.owner.is_empty()
                    || entry.owner_source_locale.is_empty()
                    || entry.definition_path.is_empty()
                    || entry.definition_start >= entry.definition_end
                    || entry.internal_id.is_empty()
                    || entry.selected_layer.is_empty()
                    || entry.selected_path.is_empty()
                {
                    return Err(Failure::new(
                        "I18N_ARTIFACT_MANIFEST",
                        format!("manifest output {token:?} has incomplete ownership metadata"),
                    ));
                }
            }
        }
        let artifacts = compiled.artifacts.clone();
        let mut bundles = BTreeMap::new();
        let collision_text = compiled
            .artifacts
            .values()
            .cloned()
            .collect::<Vec<_>>()
            .join("\n");
        for (locale, source) in compiled.artifacts {
            let locale_id: Locale = locale.parse().map_err(|error| {
                Failure::new(
                    "I18N_ARTIFACT_LOCALE",
                    format!("invalid artifact locale {locale:?}: {error}"),
                )
            })?;
            let language: LanguageIdentifier =
                locale_id.id.to_string().parse().map_err(|error| {
                    Failure::new(
                        "I18N_ARTIFACT_LOCALE",
                        format!("invalid Fluent locale {locale:?}: {error}"),
                    )
                })?;
            let mut bundle = FluentBundle::new_concurrent(vec![language]);
            bundle.set_use_isolating(false);
            register_runtime_functions(&mut bundle, &locale_id, &formats)?;
            let resource = FluentResource::try_new(source).map_err(|(_, errors)| {
                Failure::new(
                    "I18N_ARTIFACT_SOURCE",
                    format!("invalid linked artifact: {errors:?}"),
                )
            })?;
            bundle.add_resource(Arc::new(resource)).map_err(|errors| {
                Failure::new(
                    "I18N_ARTIFACT_CONFLICT",
                    format!("artifact resource conflict: {errors:?}"),
                )
            })?;
            bundles.insert(locale, bundle);
        }
        for (active_locale, outputs) in &compiled.manifest {
            for (token, entry) in outputs {
                let bundle = bundles
                    .get(&entry.bundle_locale)
                    .expect("bundle checked above");
                if bundle
                    .get_message(&entry.internal_id)
                    .and_then(|message| message.value())
                    .is_none()
                {
                    return Err(Failure::new(
                        "I18N_ARTIFACT_MANIFEST",
                        format!(
                            "manifest output {token:?} for {active_locale:?} selects missing internal message {:?}",
                            entry.internal_id
                        ),
                    ));
                }
            }
        }
        Ok(Self {
            revision: compiled.revision,
            manifest: compiled.manifest,
            artifacts,
            bundles,
            collision_text,
            formats,
        })
    }

    /// Content revision for topology, manifest, and generated sources.
    pub fn revision(&self) -> &str {
        &self.revision
    }

    /// Revision of the checked named formatter registry.
    pub fn formats_revision(&self) -> &str {
        self.formats.revision()
    }

    /// Build locale-specific records for the checked browser parsers.
    pub fn browser_parser_artifact_json(&self, locale: &str) -> Result<String, Failure> {
        self.formats.browser_parser_artifact_json(locale)
    }

    /// Build one exact browser message partition for a requested locale.
    pub fn browser_artifact_json(
        &self,
        locale: &str,
        request_json: &str,
    ) -> Result<String, Failure> {
        let request: BrowserArtifactRequest =
            serde_json::from_str(request_json).map_err(|error| {
                Failure::new(
                    "I18N_BROWSER_REQUEST_JSON",
                    format!("invalid browser artifact request: {error}"),
                )
            })?;
        let locale_manifest = self.manifest.get(locale).ok_or_else(|| {
            Failure::new(
                "I18N_BROWSER_LOCALE",
                format!("browser artifact locale {locale:?} is not compiled"),
            )
        })?;
        let mut requested = BTreeSet::new();
        for output in request.outputs {
            if output.is_empty() || !requested.insert(output.clone()) {
                return Err(Failure::new(
                    "I18N_BROWSER_OUTPUT",
                    format!("browser output {output:?} is empty or repeated"),
                ));
            }
        }
        let mut groups = BTreeSet::new();
        for message in request.messages {
            if message.is_empty() || !groups.insert(message.clone()) {
                return Err(Failure::new(
                    "I18N_BROWSER_MESSAGE",
                    format!("browser message {message:?} is empty or repeated"),
                ));
            }
            let matches = locale_manifest
                .keys()
                .filter(|token| *token == &message || token.starts_with(&format!("{message}.")))
                .cloned()
                .collect::<Vec<_>>();
            if matches.is_empty() {
                return Err(Failure::new(
                    "I18N_BROWSER_MESSAGE",
                    format!("unknown browser message {message:?} for locale {locale:?}"),
                ));
            }
            requested.extend(matches);
        }
        let mut browser_messages = BTreeMap::new();
        let mut roots_by_locale = BTreeMap::<String, BTreeSet<String>>::new();
        for token in requested {
            let entry = locale_manifest.get(&token).ok_or_else(|| {
                Failure::new(
                    "I18N_BROWSER_OUTPUT",
                    format!("unknown browser output {token:?} for locale {locale:?}"),
                )
            })?;
            roots_by_locale
                .entry(entry.bundle_locale.clone())
                .or_default()
                .insert(entry.internal_id.clone());
            browser_messages.insert(
                token,
                BrowserMessageEntry {
                    bundle_locale: entry.bundle_locale.clone(),
                    internal_id: entry.internal_id.clone(),
                    contract: entry.contract.clone(),
                },
            );
        }
        let mut browser_bundles = BTreeMap::new();
        for (bundle_locale, roots) in roots_by_locale {
            let source = self.artifacts.get(&bundle_locale).ok_or_else(|| {
                Failure::new(
                    "I18N_BROWSER_BUNDLE",
                    format!("browser partition refers to missing bundle {bundle_locale:?}"),
                )
            })?;
            browser_bundles.insert(bundle_locale, browser_bundle_subset(source, &roots)?);
        }
        let revision_payload = serde_json::to_string(&(
            SCHEMA_VERSION,
            "@fluent/bundle@0.19.1",
            &self.revision,
            self.formats.revision(),
            locale,
            &browser_messages,
            &browser_bundles,
        ))
        .map_err(|error| Failure::new("I18N_INTERNAL_JSON", error.to_string()))?;
        let artifact = BrowserArtifact {
            schema_version: SCHEMA_VERSION,
            runtime: "@fluent/bundle@0.19.1",
            catalog_revision: self.revision.clone(),
            formats_revision: self.formats.revision().to_owned(),
            requested_locale: locale.to_owned(),
            messages: browser_messages,
            bundles: browser_bundles,
            revision: digest_text(&revision_payload),
        };
        serde_json::to_string(&artifact)
            .map_err(|error| Failure::new("I18N_INTERNAL_JSON", error.to_string()))
    }

    /// Format an exact integer or decimal through a named number profile.
    pub fn format_number(
        &self,
        locale: &str,
        profile: &str,
        value: &str,
    ) -> Result<String, Failure> {
        self.formats.number(locale, profile, value)
    }

    /// Parse one localized number edit through the same named number profile.
    pub fn parse_number_json(
        &self,
        locale: &str,
        profile: &str,
        input: &str,
    ) -> Result<String, Failure> {
        self.formats.parse_number_json(locale, profile, input)
    }

    /// Format an exact ratio through a named percent profile.
    pub fn format_percent(
        &self,
        locale: &str,
        profile: &str,
        value: &str,
    ) -> Result<String, Failure> {
        self.formats.percent(locale, profile, value)
    }

    /// Parse one localized percent edit into its canonical ratio.
    pub fn parse_percent_json(
        &self,
        locale: &str,
        profile: &str,
        input: &str,
    ) -> Result<String, Failure> {
        self.formats.parse_percent_json(locale, profile, input)
    }

    /// Format an exact amount and explicit ISO currency code.
    pub fn format_currency(
        &self,
        locale: &str,
        profile: &str,
        value: &str,
        currency: &str,
    ) -> Result<String, Failure> {
        self.formats.currency(locale, profile, value, currency)
    }

    /// Format one calendar date through a named date profile.
    pub fn format_date(
        &self,
        locale: &str,
        profile: &str,
        year: i32,
        month: u8,
        day: u8,
    ) -> Result<String, Failure> {
        self.formats.date(locale, profile, year, month, day)
    }

    /// Parse one strict localized numeric date edit.
    pub fn parse_date_json(
        &self,
        locale: &str,
        profile: &str,
        input: &str,
    ) -> Result<String, Failure> {
        self.formats.parse_date_json(locale, profile, input)
    }

    /// Parse named localized year, month, and day edit segments.
    pub fn parse_date_segments_json(
        &self,
        locale: &str,
        profile: &str,
        year: &str,
        month: &str,
        day: &str,
    ) -> Result<String, Failure> {
        self.formats
            .parse_date_segments_json(locale, profile, year, month, day)
    }

    /// Format one wall-clock time through a named profile.
    pub fn format_time(
        &self,
        locale: &str,
        profile: &str,
        hour: u8,
        minute: u8,
        second: u8,
        nanosecond: u32,
    ) -> Result<String, Failure> {
        self.formats
            .time(locale, profile, hour, minute, second, nanosecond)
    }

    /// Parse one strict localized wall-clock time edit.
    pub fn parse_time_json(
        &self,
        locale: &str,
        profile: &str,
        input: &str,
    ) -> Result<String, Failure> {
        self.formats.parse_time_json(locale, profile, input)
    }

    /// Parse named localized wall-clock time edit segments.
    #[allow(clippy::too_many_arguments)]
    pub fn parse_time_segments_json(
        &self,
        locale: &str,
        profile: &str,
        hour: &str,
        minute: &str,
        second: Option<&str>,
        day_period: Option<&str>,
    ) -> Result<String, Failure> {
        self.formats
            .parse_time_segments_json(locale, profile, hour, minute, second, day_period)
    }

    /// Format one already-resolved local datetime and its explicit zone facts.
    #[allow(clippy::too_many_arguments)]
    pub fn format_datetime(
        &self,
        locale: &str,
        profile: &str,
        year: i32,
        month: u8,
        day: u8,
        hour: u8,
        minute: u8,
        second: u8,
        nanosecond: u32,
        time_zone: &str,
        offset_seconds: i32,
        epoch_seconds: i64,
    ) -> Result<String, Failure> {
        self.formats.datetime(
            locale,
            profile,
            year,
            month,
            day,
            hour,
            minute,
            second,
            nanosecond,
            time_zone,
            offset_seconds,
            epoch_seconds,
        )
    }

    /// Parse one strict localized local datetime edit.
    pub fn parse_datetime_json(
        &self,
        locale: &str,
        profile: &str,
        input: &str,
    ) -> Result<String, Failure> {
        self.formats.parse_datetime_json(locale, profile, input)
    }

    /// Parse named localized date and time edit segments.
    #[allow(clippy::too_many_arguments)]
    pub fn parse_datetime_segments_json(
        &self,
        locale: &str,
        profile: &str,
        year: &str,
        month: &str,
        day: &str,
        hour: &str,
        minute: &str,
        second: Option<&str>,
        day_period: Option<&str>,
    ) -> Result<String, Failure> {
        self.formats.parse_datetime_segments_json(
            locale, profile, year, month, day, hour, minute, second, day_period,
        )
    }

    /// Format a relative value through a named checked profile.
    pub fn format_relative_time(
        &self,
        locale: &str,
        profile: &str,
        value: &str,
        unit: &str,
    ) -> Result<String, Failure> {
        self.formats.relative_time(locale, profile, value, unit)
    }

    /// Format a string list through a named checked profile.
    pub fn format_list(
        &self,
        locale: &str,
        profile: &str,
        values: &[String],
    ) -> Result<String, Failure> {
        self.formats.list(locale, profile, values)
    }

    /// Format one exact value with an explicit CLDR unit ID.
    pub fn format_unit(
        &self,
        locale: &str,
        profile: &str,
        value: &str,
        unit: &str,
    ) -> Result<String, Failure> {
        self.formats.unit(locale, profile, value, unit)
    }

    /// Resolve and format one public output.
    pub fn format(
        &self,
        active_locale: &str,
        message_id: &str,
        args_json: &str,
        attribute: Option<&str>,
    ) -> Result<String, Failure> {
        Ok(self
            .resolve(active_locale, message_id, args_json, attribute)?
            .text)
    }

    /// Resolve text and return selected-language and ownership metadata as JSON.
    pub fn resolve_json(
        &self,
        active_locale: &str,
        message_id: &str,
        args_json: &str,
        attribute: Option<&str>,
    ) -> Result<String, Failure> {
        let resolved = self.resolve(active_locale, message_id, args_json, attribute)?;
        serde_json::to_string(&resolved)
            .map_err(|error| Failure::new("I18N_INTERNAL_JSON", error.to_string()))
    }

    fn resolve<'a>(
        &'a self,
        active_locale: &'a str,
        message_id: &str,
        args_json: &str,
        attribute: Option<&str>,
    ) -> Result<ResolvedMessage<'a>, Failure> {
        let token = attribute.map_or_else(
            || message_id.to_owned(),
            |item| format!("{message_id}.{item}"),
        );
        let entry = self
            .manifest
            .get(active_locale)
            .and_then(|entries| entries.get(&token))
            .ok_or_else(|| {
                Failure::new(
                    "I18N_OUTPUT_MISSING",
                    format!("no compiled output {token:?} for {active_locale:?}"),
                )
            })?;
        let raw_args: BTreeMap<String, TaggedArg> =
            serde_json::from_str(args_json).map_err(|error| {
                Failure::new(
                    "I18N_ARGUMENT_JSON",
                    format!("invalid message args: {error}"),
                )
            })?;
        let expected: BTreeSet<_> = entry.contract.keys().cloned().collect();
        let actual: BTreeSet<_> = raw_args.keys().cloned().collect();
        if actual != expected {
            return Err(Failure::new(
                "I18N_ARGUMENT_SET",
                format!("message {token:?} expected args {expected:?}, got {actual:?}"),
            ));
        }
        let mut args = FluentArgs::new();
        for (name, type_name) in &entry.contract {
            let argument = &raw_args[name];
            validate_tagged_arg(name, type_name, argument)?;
            args.set(name.clone(), argument.value.clone());
        }
        let bundle = self.bundles.get(&entry.bundle_locale).ok_or_else(|| {
            Failure::new(
                "I18N_ARTIFACT_BUNDLE",
                "manifest points to a missing bundle",
            )
        })?;
        let message = bundle.get_message(&entry.internal_id).ok_or_else(|| {
            Failure::new(
                "I18N_ARTIFACT_MESSAGE",
                "manifest points to a missing message",
            )
        })?;
        let pattern = message.value().ok_or_else(|| {
            Failure::new(
                "I18N_ARTIFACT_VALUE",
                "linked internal message has no value",
            )
        })?;
        let mut errors = vec![];
        let value = bundle
            .format_pattern(pattern, Some(&args), &mut errors)
            .into_owned();
        if !errors.is_empty() {
            return Err(Failure::new(
                "I18N_FORMAT",
                format!("message format failed: {errors:?}"),
            ));
        }
        Ok(ResolvedMessage {
            text: value,
            requested_locale: active_locale,
            selected_locale: &entry.bundle_locale,
            owner: &entry.owner,
            owner_source_locale: &entry.owner_source_locale,
            selected_layer: &entry.selected_layer,
            selected_path: &entry.selected_path,
            used_fallback: entry.bundle_locale != active_locale,
        })
    }

    /// Resolve a rich message and return text/Slot segments as strict JSON.
    pub fn resolve_rich_json(
        &self,
        active_locale: &str,
        message_id: &str,
        args_json: &str,
        slot_names_json: &str,
        attribute: Option<&str>,
    ) -> Result<String, Failure> {
        let token = attribute.map_or_else(
            || message_id.to_owned(),
            |item| format!("{message_id}.{item}"),
        );
        let entry = self
            .manifest
            .get(active_locale)
            .and_then(|entries| entries.get(&token))
            .ok_or_else(|| {
                Failure::new(
                    "I18N_OUTPUT_MISSING",
                    format!("no compiled output {token:?} for {active_locale:?}"),
                )
            })?;
        let expected_slots = entry
            .contract
            .iter()
            .filter(|(_, type_name)| type_name.as_str() == "Slot")
            .map(|(name, _)| name.clone())
            .collect::<BTreeSet<_>>();
        let supplied_slots: BTreeSet<String> =
            serde_json::from_str(slot_names_json).map_err(|error| {
                Failure::new(
                    "I18N_SLOT_NAMES_JSON",
                    format!("invalid Slot-name set: {error}"),
                )
            })?;
        if supplied_slots != expected_slots {
            return Err(Failure::new(
                "I18N_SLOT_SET",
                format!(
                    "message {token:?} expected Slots {expected_slots:?}, got {supplied_slots:?}"
                ),
            ));
        }
        let mut raw_args: BTreeMap<String, TaggedArg> =
            serde_json::from_str(args_json).map_err(|error| {
                Failure::new(
                    "I18N_ARGUMENT_JSON",
                    format!("invalid message args: {error}"),
                )
            })?;
        if raw_args.keys().any(|name| expected_slots.contains(name)) {
            return Err(Failure::new(
                "I18N_SLOT_ARGUMENT_COLLISION",
                "Slot names must not also appear in scalar message arguments",
            ));
        }
        let mut markers = BTreeMap::new();
        for name in &expected_slots {
            let marker = self.fresh_slot_marker(name, &raw_args)?;
            raw_args.insert(
                name.clone(),
                TaggedArg {
                    type_name: "slot".to_owned(),
                    value: marker.clone(),
                },
            );
            markers.insert(name.clone(), marker);
        }
        let encoded_args = serde_json::to_string(&raw_args)
            .map_err(|error| Failure::new("I18N_INTERNAL_JSON", error.to_string()))?;
        let resolved = self.resolve(active_locale, message_id, &encoded_args, attribute)?;
        let segments = split_rich_segments(&resolved.text, &markers)?;
        serde_json::to_string(&ResolvedRichMessage {
            segments,
            requested_locale: resolved.requested_locale,
            selected_locale: resolved.selected_locale,
            owner: resolved.owner,
            owner_source_locale: resolved.owner_source_locale,
            selected_layer: resolved.selected_layer,
            selected_path: resolved.selected_path,
            used_fallback: resolved.used_fallback,
        })
        .map_err(|error| Failure::new("I18N_INTERNAL_JSON", error.to_string()))
    }

    fn fresh_slot_marker(
        &self,
        name: &str,
        args: &BTreeMap<String, TaggedArg>,
    ) -> Result<String, Failure> {
        for _ in 0..32 {
            let mut random = [0_u8; 16];
            getrandom::fill(&mut random).map_err(|error| {
                Failure::new(
                    "I18N_RANDOM",
                    format!("could not create a Slot marker: {error}"),
                )
            })?;
            let random = random
                .iter()
                .map(|byte| format!("{byte:02x}"))
                .collect::<String>();
            let marker = format!("__CITRY_SLOT_{random}_{}__", digest_text(name));
            let collides = self.collision_text.contains(&marker)
                || args
                    .values()
                    .any(|argument| argument.value.contains(&marker));
            if !collides {
                return Ok(marker);
            }
        }
        Err(Failure::new(
            "I18N_SLOT_MARKER_COLLISION",
            "could not create a collision-free Slot marker",
        ))
    }
}

fn split_rich_segments(
    value: &str,
    markers: &BTreeMap<String, String>,
) -> Result<Vec<RichSegment>, Failure> {
    let mut segments = Vec::new();
    let mut counts = BTreeMap::<String, usize>::new();
    let mut remaining = value;
    while !remaining.is_empty() {
        let next = markers
            .iter()
            .filter_map(|(name, marker)| {
                remaining.find(marker).map(|offset| (offset, name, marker))
            })
            .min_by_key(|(offset, name, _)| (*offset, name.as_str()));
        let Some((offset, name, marker)) = next else {
            segments.push(RichSegment::Text {
                value: remaining.to_owned(),
            });
            break;
        };
        if offset > 0 {
            segments.push(RichSegment::Text {
                value: remaining[..offset].to_owned(),
            });
        }
        segments.push(RichSegment::Slot { name: name.clone() });
        *counts.entry(name.clone()).or_default() += 1;
        remaining = &remaining[offset + marker.len()..];
    }
    for name in markers.keys() {
        if counts.get(name).copied().unwrap_or(0) == 0 {
            return Err(Failure::new(
                "I18N_REQUIRED_SLOT_MISSING",
                format!("resolved rich message omitted required Slot ${name}"),
            ));
        }
    }
    Ok(segments)
}

#[cfg(test)]
mod tests {
    use serde_json::{Value, json};

    use super::{CatalogCompiler, I18nRuntime, SCHEMA_VERSION};

    fn request(active_locales: &[&str], catalogs: Vec<Value>, exports: &[&str]) -> Value {
        json!({
            "schema_version": SCHEMA_VERSION,
            "active_locales": active_locales,
            "fallbacks": {},
            "packages": [{
                "name": "app",
                "source_locale": "en-US",
                "exports": exports,
            }],
            "catalogs": catalogs,
        })
    }

    #[test]
    fn browser_artifact_keeps_only_requested_outputs_and_their_closure() {
        let compiler = CatalogCompiler::new();
        let artifact = compiler
            .compile(
                &request(
                    &["en-US"],
                    vec![json!({
                        "path": "app.ftl",
                        "package": "app",
                        "layer": "app",
                        "precedence": 0,
                        "locale": "en-US",
                        "source": concat!(
                            "target = Target\n",
                            "root = Root { target }\n",
                            "unused = Unused\n",
                            "card = Card\n",
                            "    .aria-label = Card label\n",
                        ),
                    })],
                    &[],
                )
                .to_string(),
            )
            .unwrap();
        let runtime = I18nRuntime::new(&artifact).unwrap();
        let complete: Value = serde_json::from_str(&artifact).unwrap();
        let browser: Value = serde_json::from_str(
            &runtime
                .browser_artifact_json("en-US", r#"{"outputs":["root"],"messages":["card"]}"#)
                .unwrap(),
        )
        .unwrap();

        assert_eq!(browser["runtime"], "@fluent/bundle@0.19.1");
        assert_eq!(
            browser["messages"]
                .as_object()
                .unwrap()
                .keys()
                .cloned()
                .collect::<Vec<_>>(),
            ["card", "card.aria-label", "root"]
        );
        let linked = browser["bundles"]["en-US"].as_str().unwrap();
        for token in ["root", "card", "card.aria-label"] {
            let internal = complete["manifest"]["en-US"][token]["internal_id"]
                .as_str()
                .unwrap();
            assert!(linked.contains(internal));
        }
        let target = complete["manifest"]["en-US"]["target"]["internal_id"]
            .as_str()
            .unwrap();
        assert!(linked.contains(target));
        let unused = complete["manifest"]["en-US"]["unused"]["internal_id"]
            .as_str()
            .unwrap();
        assert!(!linked.contains(unused));
        assert_eq!(browser["catalog_revision"], runtime.revision());
        assert_eq!(browser["requested_locale"], "en-US");
        assert_eq!(browser["revision"].as_str().unwrap().len(), 64);
    }

    #[test]
    fn browser_artifact_rejects_unknown_and_duplicate_roots() {
        let compiler = CatalogCompiler::new();
        let artifact = compiler
            .compile(
                &request(
                    &["en-US"],
                    vec![json!({
                        "path": "app.ftl",
                        "package": "app",
                        "layer": "app",
                        "precedence": 0,
                        "locale": "en-US",
                        "source": "hello = Hello\n",
                    })],
                    &[],
                )
                .to_string(),
            )
            .unwrap();
        let runtime = I18nRuntime::new(&artifact).unwrap();

        let unknown = runtime
            .browser_artifact_json("en-US", r#"{"outputs":["missing"],"messages":[]}"#)
            .unwrap_err();
        assert_eq!(unknown.code(), "I18N_BROWSER_OUTPUT");
        let duplicate = runtime
            .browser_artifact_json("en-US", r#"{"outputs":["hello","hello"],"messages":[]}"#)
            .unwrap_err();
        assert_eq!(duplicate.code(), "I18N_BROWSER_OUTPUT");
    }

    #[test]
    fn source_free_link_unit_is_checked_and_does_not_reparse_package_ftl() {
        let compiler = CatalogCompiler::new();
        let package_request = request(
            &["en-US", "cs-CZ"],
            vec![
                json!({
                    "path": "demo:locales/en-US/common.ftl",
                    "package": "app",
                    "layer": "package",
                    "precedence": 0,
                    "locale": "en-US",
                    "source": "title = Title\n",
                }),
                json!({
                    "path": "demo:locales/cs-CZ/common.ftl",
                    "package": "app",
                    "layer": "package",
                    "precedence": 0,
                    "locale": "cs-CZ",
                    "source": "title = Titulek\n",
                }),
            ],
            &["title"],
        );
        let link_unit = compiler
            .compile_link_unit(&package_request.to_string())
            .unwrap();
        assert!(!link_unit.contains("title = Title"));

        let project_request = json!({
            "schema_version": SCHEMA_VERSION,
            "active_locales": ["en-US", "cs-CZ"],
            "fallbacks": {},
            "packages": [],
            "catalogs": [],
            "link_units": [{
                "artifact_json": link_unit,
                "layer": "package:0:app",
                "precedence": 0,
            }],
        });
        let artifact = compiler.compile(&project_request.to_string()).unwrap();
        let value: Value = serde_json::from_str(&artifact).unwrap();
        assert_eq!(value["stats"]["parsed_catalogs"], 0);
        let runtime = I18nRuntime::new(&artifact).unwrap();
        assert_eq!(
            runtime.format("cs-CZ", "title", "{}", None).unwrap(),
            "Titulek"
        );
    }

    fn catalog(path: &str, locale: &str, source: &str) -> Value {
        json!({
            "path": path,
            "package": "app",
            "layer": "app",
            "precedence": 0,
            "locale": locale,
            "source": source,
        })
    }

    fn compile(value: &Value) -> String {
        CatalogCompiler::new()
            .compile(&serde_json::to_string(value).unwrap())
            .unwrap()
    }

    #[test]
    fn compiles_typed_text_string_selectors_and_icu_plurals() {
        let source = concat!(
            "# @param {str} $name\n",
            "greeting = Welcome, { $name }.\n",
            "# @param {str} $kind\n",
            "choice = { $kind ->\n    [yes] Yes\n   *[other] Other\n}\n",
            "# @param {Decimal} $count\n",
            "count = { $count ->\n    [one] one\n    [few] few\n    [many] many\n   *[other] other\n}\n",
        );
        let translation = source
            .lines()
            .filter(|line| !line.starts_with("# @param"))
            .collect::<Vec<_>>()
            .join("\n");
        let compiled = compile(&request(
            &["cs-CZ"],
            vec![
                catalog("app/en-US.ftl", "en-US", source),
                catalog("app/cs-CZ.ftl", "cs-CZ", &translation),
            ],
            &["greeting", "choice", "count"],
        ));
        let runtime = I18nRuntime::new(&compiled).unwrap();
        assert_eq!(
            runtime
                .format(
                    "cs-CZ",
                    "greeting",
                    r#"{"name":{"type":"str","value":"Ada"}}"#,
                    None,
                )
                .unwrap(),
            "Welcome, \u{2068}Ada\u{2069}."
        );
        assert_eq!(
            runtime
                .format(
                    "cs-CZ",
                    "choice",
                    r#"{"kind":{"type":"str","value":"yes"}}"#,
                    None,
                )
                .unwrap(),
            "Yes"
        );
        assert_eq!(
            runtime
                .format(
                    "cs-CZ",
                    "count",
                    r#"{"count":{"type":"decimal","value":"1.5"}}"#,
                    None,
                )
                .unwrap(),
            "many"
        );
    }

    #[test]
    fn rich_resolution_repeats_one_slot_without_exposing_markers() {
        let source = "# @param {Slot} $link\nrich = Start { $link }, again { $link }.\n";
        let compiled = compile(&request(
            &["en-US"],
            vec![catalog("app/en-US.ftl", "en-US", source)],
            &["rich"],
        ));
        let runtime = I18nRuntime::new(&compiled).unwrap();
        let resolved: Value = serde_json::from_str(
            &runtime
                .resolve_rich_json("en-US", "rich", "{}", r#"["link"]"#, None)
                .unwrap(),
        )
        .unwrap();
        let slots = resolved["segments"]
            .as_array()
            .unwrap()
            .iter()
            .filter(|segment| segment["type"] == "slot")
            .count();
        assert_eq!(slots, 2);
        assert!(!resolved.to_string().contains("__CITRY_SLOT_"));
    }

    #[test]
    fn rich_slot_minimum_is_checked_across_selector_branches() {
        let valid = concat!(
            "# @param {Slot} $link\n",
            "# @param {str} $kind\n",
            "rich = { $kind ->\n",
            "    [one] Once { $link }\n",
            "   *[other] Twice { $link } and { $link }\n",
            "}\n",
        );
        compile(&request(
            &["en-US"],
            vec![catalog("app/en-US.ftl", "en-US", valid)],
            &["rich"],
        ));

        let invalid = valid.replace(
            "   *[other] Twice { $link } and { $link }",
            "   *[other] Never",
        );
        let error = CatalogCompiler::new()
            .compile(
                &serde_json::to_string(&request(
                    &["en-US"],
                    vec![catalog("app/en-US.ftl", "en-US", &invalid)],
                    &["rich"],
                ))
                .unwrap(),
            )
            .unwrap_err();
        assert_eq!(error.code(), "I18N_REQUIRED_SLOT_MISSING");
    }

    #[test]
    fn rich_slots_must_be_direct_standalone_placeables() {
        let source = "# @param {Slot} $link\nrich = Nested { { $link } }\n";
        let error = CatalogCompiler::new()
            .compile(
                &serde_json::to_string(&request(
                    &["en-US"],
                    vec![catalog("app/en-US.ftl", "en-US", source)],
                    &["rich"],
                ))
                .unwrap(),
            )
            .unwrap_err();
        assert_eq!(error.code(), "I18N_SLOT_NESTED");
    }

    #[test]
    fn intermediate_fallback_is_selected_before_owner_source() {
        let mut value = request(
            &["pl-PL"],
            vec![
                catalog("app/en-US.ftl", "en-US", "hello = English\n"),
                catalog("app/cs-CZ.ftl", "cs-CZ", "hello = Česky\n"),
            ],
            &["hello"],
        );
        value["fallbacks"] = json!({"pl-PL": ["cs-CZ"]});
        let runtime = I18nRuntime::new(&compile(&value)).unwrap();
        let resolved: Value =
            serde_json::from_str(&runtime.resolve_json("pl-PL", "hello", "{}", None).unwrap())
                .unwrap();
        assert_eq!(resolved["text"], "Česky");
        assert_eq!(resolved["selected_locale"], "cs-CZ");
        assert_eq!(resolved["owner_source_locale"], "en-US");
        assert_eq!(resolved["used_fallback"], true);
    }

    #[test]
    fn nested_private_terms_are_linked_inside_their_source_unit() {
        let source = "-inner = inside\n-outer = outside { -inner }\nhello = { -outer }\n";
        let compiled = compile(&request(
            &["en-US"],
            vec![catalog("app/en-US.ftl", "en-US", source)],
            &["hello"],
        ));
        let runtime = I18nRuntime::new(&compiled).unwrap();
        assert_eq!(
            runtime.format("en-US", "hello", "{}", None).unwrap(),
            "outside inside"
        );
    }

    #[test]
    fn private_term_cycles_fail_before_runtime_publication() {
        let source = "-one = { -two }\n-two = { -one }\nhello = { -one }\n";
        let error = CatalogCompiler::new()
            .compile(
                &serde_json::to_string(&request(
                    &["en-US"],
                    vec![catalog("app/en-US.ftl", "en-US", source)],
                    &["hello"],
                ))
                .unwrap(),
            )
            .unwrap_err();
        assert_eq!(error.code(), "I18N_REFERENCE_CYCLE");
    }

    #[test]
    fn same_layer_duplicate_reports_both_sources() {
        let value = request(
            &["en-US"],
            vec![
                catalog("app/one.ftl", "en-US", "same = One\n"),
                catalog("app/two.ftl", "en-US", "same = Two\n"),
            ],
            &["same"],
        );
        let error = CatalogCompiler::new()
            .compile(&serde_json::to_string(&value).unwrap())
            .unwrap_err();
        assert_eq!(error.code(), "I18N_DUPLICATE_LAYER_OUTPUT");
        let diagnostic: Value = serde_json::from_str(&error.diagnostic_json()).unwrap();
        assert_eq!(diagnostic["path"], "app/two.ftl");
        assert_eq!(diagnostic["related"][0]["path"], "app/one.ftl");
    }

    #[test]
    fn same_layer_message_id_cannot_be_split_across_source_units() {
        let value = request(
            &["en-US"],
            vec![
                catalog("app/one.ftl", "en-US", "button = Button\n"),
                catalog(
                    "app/two.ftl",
                    "en-US",
                    "button =\n    .aria-label = Close\n",
                ),
            ],
            &["button"],
        );
        let error = CatalogCompiler::new()
            .compile(&serde_json::to_string(&value).unwrap())
            .unwrap_err();
        assert_eq!(error.code(), "I18N_DUPLICATE_LAYER_OUTPUT");
    }

    #[test]
    fn translation_cannot_redeclare_source_parameters() {
        let value = request(
            &["cs-CZ"],
            vec![
                catalog(
                    "app/en-US.ftl",
                    "en-US",
                    "# @param {str} $name\nhello = Hello { $name }\n",
                ),
                catalog(
                    "app/cs-CZ.ftl",
                    "cs-CZ",
                    "# @param {str} $name\nhello = Ahoj { $name }\n",
                ),
            ],
            &["hello"],
        );
        let error = CatalogCompiler::new()
            .compile(&serde_json::to_string(&value).unwrap())
            .unwrap_err();
        assert_eq!(error.code(), "I18N_TRANSLATION_PARAM_DECLARATION");
    }

    #[test]
    fn source_locale_override_may_repeat_the_exact_owner_contract() {
        let value = json!({
            "schema_version": SCHEMA_VERSION,
            "active_locales": ["en-US"],
            "fallbacks": {},
            "packages": [
                {"name": "library", "source_locale": "en-US", "exports": []},
                {"name": "application", "source_locale": "en-US", "exports": []},
            ],
            "catalogs": [
                catalog(
                    "library/en-US.ftl",
                    "en-US",
                    "# @param {str} $name\nhello = Library { $name }\n",
                ),
                {
                    "path": "application/component.ftl",
                    "package": "application",
                    "layer": "application",
                    "precedence": 1,
                    "locale": "en-US",
                    "source": "# @param {str} $name\nhello = Application { $name }\n",
                },
            ],
        });
        let mut value = value;
        value["catalogs"][0]["package"] = json!("library");
        value["catalogs"][0]["layer"] = json!("library");

        let compiled = CatalogCompiler::new()
            .compile(&serde_json::to_string(&value).unwrap())
            .unwrap();
        let runtime = I18nRuntime::new(&compiled).unwrap();
        let args = r#"{"name":{"type":"str","value":"Ada"}}"#;
        assert_eq!(
            runtime.format("en-US", "hello", args, None).unwrap(),
            "Application \u{2068}Ada\u{2069}"
        );
    }

    #[test]
    fn source_locale_override_cannot_change_the_owner_contract() {
        let value = json!({
            "schema_version": SCHEMA_VERSION,
            "active_locales": ["en-US"],
            "fallbacks": {},
            "packages": [
                {"name": "library", "source_locale": "en-US", "exports": []},
                {"name": "application", "source_locale": "en-US", "exports": []},
            ],
            "catalogs": [
                catalog(
                    "library/en-US.ftl",
                    "en-US",
                    "# @param {str} $name\nhello = Library { $name }\n",
                ),
                {
                    "path": "application/component.ftl",
                    "package": "application",
                    "layer": "application",
                    "precedence": 1,
                    "locale": "en-US",
                    "source": "# @param {int} $name\nhello = Application { $name }\n",
                },
            ],
        });
        let mut value = value;
        value["catalogs"][0]["package"] = json!("library");
        value["catalogs"][0]["layer"] = json!("library");

        let error = CatalogCompiler::new()
            .compile(&serde_json::to_string(&value).unwrap())
            .unwrap_err();
        assert_eq!(error.code(), "I18N_TRANSLATION_PARAM_DECLARATION");
    }

    #[test]
    fn semantic_diagnostics_point_at_param_comments_with_valid_message_spacing() {
        let source = "### Heading\n# @param {unknown} $name\nhello   = Hello { $name }\n";
        let error = CatalogCompiler::new()
            .compile(
                &serde_json::to_string(&request(
                    &["en-US"],
                    vec![catalog("app/en-US.ftl", "en-US", source)],
                    &["hello"],
                ))
                .unwrap(),
            )
            .unwrap_err();
        let diagnostic: Value = serde_json::from_str(&error.diagnostic_json()).unwrap();
        assert_eq!(diagnostic["line"], 2);
        assert_eq!(diagnostic["start"], source.find("@param").unwrap());
    }

    #[test]
    fn missing_parameter_types_follow_the_catalog_lint_policy() {
        let warning_request = request(
            &["en-US"],
            vec![catalog(
                "app/en-US.ftl",
                "en-US",
                "hello = Hello { $name }\n",
            )],
            &["hello"],
        );
        let warning_artifact: Value = serde_json::from_str(&compile(&warning_request)).unwrap();
        assert_eq!(
            warning_artifact["diagnostics"][0]["code"],
            "citry.i18n.missing-param-type"
        );

        let runtime = I18nRuntime::new(&compile(&warning_request)).unwrap();
        assert_eq!(
            runtime
                .format(
                    "en-US",
                    "hello",
                    r#"{"name":{"type":"str","value":"Ada"}}"#,
                    None,
                )
                .unwrap(),
            "Hello \u{2068}Ada\u{2069}"
        );

        let mut error_request = warning_request.clone();
        error_request["catalogs"][0]["missing_param_type"] = json!("error");
        let error = CatalogCompiler::new()
            .compile(&serde_json::to_string(&error_request).unwrap())
            .unwrap_err();
        assert_eq!(error.code(), "I18N_PARAM_MISSING");

        let mut ignored_request = warning_request;
        ignored_request["catalogs"][0]["missing_param_type"] = json!("ignore");
        let ignored_artifact: Value = serde_json::from_str(&compile(&ignored_request)).unwrap();
        assert_eq!(ignored_artifact["diagnostics"], json!([]));
    }

    #[test]
    fn manifest_keeps_parameter_descriptions_spans_and_transitive_origin() {
        let source = concat!(
            "# @param {str} $name - User name.\n",
            "target = Hello { $name }\n",
            "wrapper = { target }\n",
        );
        let artifact: Value = serde_json::from_str(&compile(&request(
            &["en-US"],
            vec![catalog("app/en-US.ftl", "en-US", source)],
            &["target", "wrapper"],
        )))
        .unwrap();
        let parameter = &artifact["manifest"]["en-US"]["wrapper"]["interface"]["name"];
        assert_eq!(parameter["type_name"], "str");
        assert_eq!(parameter["direct"], false);
        assert_eq!(parameter["declarations"][0]["description"], "User name.");
        assert_eq!(parameter["declarations"][0]["path"], "app/en-US.ftl");
        assert_eq!(parameter["declarations"][0]["line"], 1);
        assert_eq!(parameter["declarations"][0]["annotated"], true);
        let wrapper = &artifact["manifest"]["en-US"]["wrapper"];
        assert_eq!(wrapper["definition_path"], "app/en-US.ftl");
        assert_eq!(wrapper["definition_line"], 3);
        assert_eq!(wrapper["definition_column"], 1);
        assert_eq!(
            &source[wrapper["definition_start"].as_u64().unwrap() as usize
                ..wrapper["definition_end"].as_u64().unwrap() as usize],
            "wrapper"
        );
    }

    #[test]
    fn attribute_only_messages_compile_as_public_outputs() {
        let source = "button =\n    .aria-label = Close\n";
        let compiled = compile(&request(
            &["en-US"],
            vec![catalog("app/en-US.ftl", "en-US", source)],
            &["button"],
        ));
        let artifact: Value = serde_json::from_str(&compiled).unwrap();
        assert!(artifact["manifest"]["en-US"].get("button").is_none());
        assert_eq!(
            artifact["manifest"]["en-US"]["button.aria-label"]["bundle_locale"],
            "en-US"
        );
        assert_eq!(
            I18nRuntime::new(&compiled)
                .unwrap()
                .format("en-US", "button", "{}", Some("aria-label"))
                .unwrap(),
            "Close"
        );
    }

    #[test]
    fn one_message_param_comment_types_its_value_and_attributes() {
        let source = concat!(
            "# @param {str} $name - User name.\n",
            "actions = Actions for { $name }\n",
            "    .aria-label = Available actions for { $name }\n",
        );
        let compiled = compile(&request(
            &["en-US"],
            vec![catalog("app/en-US.ftl", "en-US", source)],
            &["actions"],
        ));
        let artifact: Value = serde_json::from_str(&compiled).unwrap();
        for output in ["actions", "actions.aria-label"] {
            let parameter = &artifact["manifest"]["en-US"][output]["interface"]["name"];
            assert_eq!(parameter["type_name"], "str");
            assert_eq!(parameter["declarations"][0]["description"], "User name.");
        }
    }

    #[test]
    fn translation_cannot_add_arguments_through_a_public_reference() {
        let value = request(
            &["cs-CZ"],
            vec![
                catalog(
                    "app/en-US.ftl",
                    "en-US",
                    "# @param {str} $x\ntarget = Target { $x }\nroot = Source\n",
                ),
                catalog(
                    "app/cs-CZ.ftl",
                    "cs-CZ",
                    "target = Cíl { $x }\nroot = { target }\n",
                ),
            ],
            &["target", "root"],
        );
        let error = CatalogCompiler::new()
            .compile(&serde_json::to_string(&value).unwrap())
            .unwrap_err();
        assert_eq!(error.code(), "I18N_TRANSLATION_REFERENCE_ARGUMENT_ADDED");
    }

    #[test]
    fn added_translation_variable_points_at_the_variable() {
        let source = "hello = { $other }\n";
        let value = request(
            &["cs-CZ"],
            vec![
                catalog("app/en-US.ftl", "en-US", "hello = Hello\n"),
                catalog("app/cs-CZ.ftl", "cs-CZ", source),
            ],
            &["hello"],
        );
        let error = CatalogCompiler::new()
            .compile(&serde_json::to_string(&value).unwrap())
            .unwrap_err();
        let diagnostic: Value = serde_json::from_str(&error.diagnostic_json()).unwrap();
        assert_eq!(error.code(), "I18N_TRANSLATION_VARIABLE_ADDED");
        assert_eq!(diagnostic["start"], source.find("other").unwrap());
        assert_eq!(
            diagnostic["end"],
            source.find("other").unwrap() + "other".len()
        );
    }

    #[test]
    fn private_terms_can_reference_public_messages_with_a_checked_interface() {
        let source = concat!(
            "# @param {str} $name\n",
            "target = Hello { $name }\n",
            "-private = { target }\n",
            "root = { -private }\n",
        );
        let compiled = compile(&request(
            &["en-US"],
            vec![catalog("app/en-US.ftl", "en-US", source)],
            &["target", "root"],
        ));
        let runtime = I18nRuntime::new(&compiled).unwrap();
        assert_eq!(
            runtime
                .format(
                    "en-US",
                    "root",
                    r#"{"name":{"type":"str","value":"Ada"}}"#,
                    None,
                )
                .unwrap(),
            "Hello \u{2068}Ada\u{2069}"
        );
    }

    #[test]
    fn source_analysis_uses_the_production_parser_and_indexes_private_terms() {
        let source = concat!(
            "# @param {str} $name\n",
            "account-title = { -product } for { $name }\n",
            "    .aria-label = { account-label }\n",
            "account-label = Account\n",
            "-product = Citry\n",
        );
        let analysis: Value = serde_json::from_str(
            &CatalogCompiler::new()
                .analyze_source("app.py::Account.messages", source)
                .unwrap(),
        )
        .unwrap();
        assert_eq!(analysis["schema_version"], 1);
        for collection in ["definitions", "references"] {
            let item = analysis[collection]
                .as_array()
                .unwrap()
                .iter()
                .find(|item| item["kind"] == "term" && item["token"] == "-product")
                .unwrap();
            let start = item["start"].as_u64().unwrap() as usize;
            let end = item["end"].as_u64().unwrap() as usize;
            assert_eq!(&source[start..end], "product");
        }
    }

    #[test]
    fn source_analysis_rejects_unsupported_param_types_at_the_comment() {
        let source = "# @param {Slot1} $link\nhello = { $link }\n";
        let error = CatalogCompiler::new()
            .analyze_source("app.py::Card.messages", source)
            .unwrap_err();
        let diagnostic: Value = serde_json::from_str(&error.diagnostic_json()).unwrap();
        assert_eq!(error.code(), "I18N_PARAM_TYPE_UNSUPPORTED");
        assert_eq!(diagnostic["start"], source.find("@param").unwrap());
        assert_eq!(diagnostic["end"], source.find("\nhello").unwrap());
    }

    #[test]
    fn duplicate_identifier_selector_variants_are_rejected() {
        for source in [
            "# @param {str} $x\nroot = { $x ->\n [a] A\n [a] B\n*[other] C\n}\n",
            "# @param {int} $x\nroot = { $x ->\n [one] A\n [one] B\n*[other] C\n}\n",
        ] {
            let error = CatalogCompiler::new()
                .compile(
                    &serde_json::to_string(&request(
                        &["en-US"],
                        vec![catalog("app/en-US.ftl", "en-US", source)],
                        &["root"],
                    ))
                    .unwrap(),
                )
                .unwrap_err();
            assert_eq!(error.code(), "I18N_SELECTOR_VARIANT_DUPLICATE");
        }
    }

    #[test]
    fn compile_request_rejects_invalid_and_noncanonical_locales() {
        for locale in ["not_a_locale", "iw-IL"] {
            let error = CatalogCompiler::new()
                .compile(
                    &serde_json::to_string(&request(
                        &[locale],
                        vec![catalog("app/en-US.ftl", "en-US", "root = Text\n")],
                        &["root"],
                    ))
                    .unwrap(),
                )
                .unwrap_err();
            assert!(matches!(
                error.code(),
                "I18N_LOCALE_INVALID" | "I18N_LOCALE_NONCANONICAL"
            ));
        }
    }

    #[test]
    fn compile_request_rejects_unknown_fallback_nodes() {
        let mut value = request(
            &["en-US"],
            vec![catalog("app/en-US.ftl", "en-US", "root = Text\n")],
            &["root"],
        );
        value["fallbacks"] = json!({"en-US": ["fr"]});
        let error = CatalogCompiler::new()
            .compile(&serde_json::to_string(&value).unwrap())
            .unwrap_err();
        assert_eq!(error.code(), "I18N_FALLBACK_UNKNOWN_LOCALE");
    }

    #[test]
    fn duplicate_terms_and_param_errors_point_at_the_exact_authored_span() {
        let duplicate_source = "title = T\n-term = A\n-term = B\n";
        let duplicate = CatalogCompiler::new()
            .compile(
                &serde_json::to_string(&request(
                    &["en-US"],
                    vec![catalog("app/en-US.ftl", "en-US", duplicate_source)],
                    &["title"],
                ))
                .unwrap(),
            )
            .unwrap_err();
        let diagnostic: Value = serde_json::from_str(&duplicate.diagnostic_json()).unwrap();
        assert_eq!(diagnostic["line"], 3);
        assert_eq!(diagnostic["start"], duplicate_source.rfind("term").unwrap());
        assert_eq!(diagnostic["related"][0]["line"], 2);

        let param_source = "# @param {unknown} $name\nhello = Hello { $name }\n";
        let param = CatalogCompiler::new()
            .compile(
                &serde_json::to_string(&request(
                    &["en-US"],
                    vec![catalog("app/en-US.ftl", "en-US", param_source)],
                    &["hello"],
                ))
                .unwrap(),
            )
            .unwrap_err();
        let diagnostic: Value = serde_json::from_str(&param.diagnostic_json()).unwrap();
        assert_eq!(diagnostic["line"], 1);
        assert_eq!(diagnostic["start"], 2);
    }

    #[test]
    fn runtime_rejects_an_artifact_with_a_stale_semantic_revision() {
        let mut artifact: Value = serde_json::from_str(&compile(&request(
            &["en-US"],
            vec![catalog("app/en-US.ftl", "en-US", "root = Text\n")],
            &["root"],
        )))
        .unwrap();
        artifact["manifest"]["en-US"]["root"]["selected_layer"] = json!("tampered");
        let error = I18nRuntime::new(&serde_json::to_string(&artifact).unwrap())
            .err()
            .expect("tampered artifact must fail");
        assert_eq!(error.code(), "I18N_ARTIFACT_REVISION");
    }
}
