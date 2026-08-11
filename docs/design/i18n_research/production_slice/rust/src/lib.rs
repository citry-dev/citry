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
use pyo3::create_exception;
use pyo3::exceptions::{PyRuntimeError, PyValueError};
use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use unic_langid::LanguageIdentifier;

const SCHEMA_VERSION: u32 = 2;
const FSI: &str = "\u{2068}";
const PDI: &str = "\u{2069}";
const BIDI_CONTROLS: [char; 12] = [
    '\u{061c}', '\u{200e}', '\u{200f}', '\u{202a}', '\u{202b}', '\u{202c}', '\u{202d}', '\u{202e}',
    '\u{2066}', '\u{2067}', '\u{2068}', '\u{2069}',
];
const BIDI_PARAGRAPH_BOUNDARIES: [char; 7] = [
    '\n', '\r', '\u{001c}', '\u{001d}', '\u{001e}', '\u{0085}', '\u{2029}',
];

create_exception!(citry_i18n_phase0, I18nCompileError, PyValueError);

#[derive(Debug, Clone)]
struct Failure {
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
    fn new(code: &'static str, message: impl Into<String>) -> Self {
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

    fn into_pyerr(self, py: Python<'_>) -> PyErr {
        let err = I18nCompileError::new_err(self.message.clone());
        let value = err.value(py);
        let _ = value.setattr("code", self.code);
        let _ = value.setattr("path", self.path);
        let _ = value.setattr("start", self.start);
        let _ = value.setattr("end", self.end);
        let _ = value.setattr("line", self.line);
        let _ = value.setattr("column", self.column);
        let _ = value.setattr("message_id", self.message_id);
        let related_json = serde_json::to_string(&self.related).unwrap_or_else(|_| "[]".to_owned());
        let _ = value.setattr("related_json", related_json);
        err
    }
}

#[derive(Debug, Clone, Serialize)]
struct DiagnosticRelated {
    message: String,
    path: String,
    line: usize,
    column: usize,
}

fn line_column(source: &str, byte_offset: usize) -> (usize, usize) {
    let prefix = &source[..byte_offset.min(source.len())];
    let line = prefix.bytes().filter(|item| *item == b'\n').count() + 1;
    let column = prefix
        .rsplit_once('\n')
        .map_or(prefix.len() + 1, |(_, tail)| tail.len() + 1);
    (line, column)
}

fn digest_text(value: &str) -> String {
    format!("{:x}", Sha256::digest(value.as_bytes()))
}

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
        }
    }

    fn trim(&mut self) {
        let trimmed = self.as_ref().trim_end_matches([' ', '\r', '\n']);
        self.range.end = self.range.start + trimmed.len();
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
    packages: Vec<PackageSpec>,
    catalogs: Vec<CatalogSpec>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct PackageSpec {
    name: String,
    source_locale: String,
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
}

#[derive(Debug, Clone)]
struct ParsedCatalog {
    digest: String,
    messages: BTreeMap<String, ast::Message<SpannedSlice>>,
    terms: BTreeMap<String, ast::Term<SpannedSlice>>,
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

#[derive(Debug, Serialize, Deserialize)]
struct CompileResult {
    schema_version: u32,
    revision: String,
    artifacts: BTreeMap<String, String>,
    manifest: BTreeMap<String, BTreeMap<String, ManifestEntry>>,
    source_maps: Vec<SourceMapEntry>,
    stats: CompileStats,
}

#[derive(Debug, Serialize, Deserialize)]
struct ManifestEntry {
    owner: String,
    bundle_locale: String,
    internal_id: String,
    contract: BTreeMap<String, String>,
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
            for message_id in &package.exports {
                if let Some(previous) = owners.insert(message_id.clone(), package.name.clone()) {
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
        let linker = Self {
            packages,
            owners,
            catalogs,
        };
        linker.validate_owner_sources()?;
        Ok(linker)
    }

    fn validate_owner_sources(&self) -> Result<(), Failure> {
        for (message_id, owner) in &self.owners {
            let package = &self.packages[owner];
            if self
                .definition_in_package(&OutputKey::value(message_id), owner, &package.source_locale)
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
            if let Some(definition) = self.definition_in_package(
                &OutputKey::value(message_id),
                owner,
                &package.source_locale,
            ) {
                result.insert(OutputKey::value(message_id));
                let message = &self.catalogs[definition.catalog].parsed.messages[message_id];
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

    fn source_contract(&self, key: &OutputKey) -> Result<Contract, Failure> {
        self.source_contract_inner(key, &mut vec![])
    }

    fn source_contract_inner(
        &self,
        key: &OutputKey,
        stack: &mut Vec<OutputKey>,
    ) -> Result<Contract, Failure> {
        if stack.contains(key) {
            return Err(Failure::new(
                "I18N_REFERENCE_CYCLE",
                format!("public reference cycle reaches {:?}", key.token()),
            ));
        }
        stack.push(key.clone());
        let definition = self.owner_source_definition(key)?;
        let catalog = &self.catalogs[definition.catalog];
        let pattern = pattern_for(catalog, key).expect("owner source pattern checked");
        let message = &catalog.parsed.messages[&key.message_id];
        let params = parse_params(message, &catalog.spec)?;
        validate_message_annotations(message, &params, &catalog.spec)?;
        let mut contract = BTreeMap::new();
        for variable in direct_variables(pattern) {
            let type_name = params.get(&variable).ok_or_else(|| {
                semantic_failure(
                    "I18N_PARAM_MISSING",
                    format!(
                        "message {:?} uses ${variable} without an @param declaration",
                        key.message_id
                    ),
                    &catalog.spec,
                    &key.message_id,
                )
            })?;
            merge_type(
                &mut contract,
                &variable,
                type_name,
                &catalog.spec,
                &key.message_id,
            )?;
        }
        for reference in message_references(pattern) {
            let inherited = self.source_contract_inner(&reference, stack)?;
            for (name, type_name) in inherited {
                merge_type(
                    &mut contract,
                    &name,
                    &type_name,
                    &catalog.spec,
                    &key.message_id,
                )?;
            }
        }
        stack.pop();
        Ok(contract)
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
        if source_locale != active_locale {
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

    fn graph_for_locale(&self, locale: &str, key: &OutputKey) -> Result<ResolutionGraph, Failure> {
        let mut graph = ResolutionGraph {
            locale: locale.to_owned(),
            messages: BTreeMap::new(),
            terms: BTreeSet::new(),
        };
        self.add_message(locale, key, &mut graph, &mut vec![])?;
        Ok(graph)
    }

    fn add_message(
        &self,
        locale: &str,
        key: &OutputKey,
        graph: &mut ResolutionGraph,
        stack: &mut Vec<OutputKey>,
    ) -> Result<(), Failure> {
        if graph.messages.contains_key(key) {
            return Ok(());
        }
        if stack.contains(key) {
            return Err(Failure::new(
                "I18N_REFERENCE_CYCLE",
                format!("public reference cycle reaches {:?}", key.token()),
            ));
        }
        let definition = self.definition(key, locale).ok_or_else(|| {
            Failure::new(
                "I18N_CANDIDATE_INCOMPLETE",
                format!("locale {locale:?} is missing {:?}", key.token()),
            )
        })?;
        stack.push(key.clone());
        let catalog = &self.catalogs[definition.catalog];
        let pattern = pattern_for(catalog, key).expect("selected definition has pattern");
        let contract = self.source_contract(key)?;
        for variable in direct_variables(pattern) {
            if !contract.contains_key(&variable) {
                return Err(semantic_failure(
                    "I18N_TRANSLATION_VARIABLE_ADDED",
                    format!(
                        "translation of {:?} introduces undeclared variable ${variable}",
                        key.token()
                    ),
                    &catalog.spec,
                    &key.message_id,
                ));
            }
        }
        graph.messages.insert(key.clone(), definition);
        for reference in message_references(pattern) {
            self.add_message(locale, &reference, graph, stack)?;
        }
        for term in term_references(pattern) {
            if !catalog.parsed.terms.contains_key(&term) {
                return Err(Failure::new(
                    "I18N_CANDIDATE_INCOMPLETE",
                    format!(
                        "locale {locale:?} layer {:?} is missing private term -{term}",
                        catalog.spec.layer
                    ),
                ));
            }
            if pattern_has_variables(&catalog.parsed.terms[&term].value) {
                return Err(semantic_failure(
                    "I18N_UNSUPPORTED_TERM_VARIABLE",
                    format!("private term -{term} uses variables, outside this slice's subset"),
                    &catalog.spec,
                    &key.message_id,
                ));
            }
            graph.terms.insert((definition.catalog, term));
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
        let paths = self.slot_paths(root, graph, contract, &mut vec![])?;
        for slot in required {
            if paths
                .iter()
                .any(|counts| counts.get(&slot).copied().unwrap_or(0) == 0)
            {
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

    fn slot_paths(
        &self,
        key: &OutputKey,
        graph: &ResolutionGraph,
        contract: &Contract,
        stack: &mut Vec<OutputKey>,
    ) -> Result<Vec<BTreeMap<String, usize>>, Failure> {
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
        let paths = self.pattern_slot_paths(pattern, key, graph, contract, stack, catalog)?;
        stack.pop();
        Ok(paths)
    }

    fn pattern_slot_paths(
        &self,
        pattern: &Pattern<SpannedSlice>,
        key: &OutputKey,
        graph: &ResolutionGraph,
        contract: &Contract,
        stack: &mut Vec<OutputKey>,
        catalog: &LoadedCatalog,
    ) -> Result<Vec<BTreeMap<String, usize>>, Failure> {
        let mut paths = vec![BTreeMap::new()];
        for element in &pattern.elements {
            let PatternElement::Placeable { expression } = element else {
                continue;
            };
            let incoming =
                self.expression_slot_paths(expression, key, graph, contract, stack, catalog)?;
            let mut combined = vec![];
            for left in &paths {
                for right in &incoming {
                    let mut counts = left.clone();
                    for (name, count) in right {
                        *counts.entry(name.clone()).or_default() += count;
                    }
                    combined.push(counts);
                }
            }
            paths = combined;
        }
        Ok(paths)
    }

    fn expression_slot_paths(
        &self,
        expression: &Expression<SpannedSlice>,
        key: &OutputKey,
        graph: &ResolutionGraph,
        contract: &Contract,
        stack: &mut Vec<OutputKey>,
        catalog: &LoadedCatalog,
    ) -> Result<Vec<BTreeMap<String, usize>>, Failure> {
        match expression {
            Expression::Inline(InlineExpression::VariableReference { id }) => {
                let name = text(&id.name);
                if contract.get(name).is_some_and(|item| item == "Slot") {
                    Ok(vec![BTreeMap::from([(name.to_owned(), 1)])])
                } else {
                    Ok(vec![BTreeMap::new()])
                }
            }
            Expression::Inline(InlineExpression::MessageReference { id, attribute }) => self
                .slot_paths(
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
                Ok(vec![BTreeMap::new()])
            }
            Expression::Inline(InlineExpression::Placeable { expression }) => {
                self.expression_slot_paths(expression, key, graph, contract, stack, catalog)
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
                let mut paths = vec![];
                for variant in variants {
                    paths.extend(self.pattern_slot_paths(
                        &variant.value,
                        key,
                        graph,
                        contract,
                        stack,
                        catalog,
                    )?);
                }
                Ok(paths)
            }
            Expression::Inline(_) => Ok(vec![BTreeMap::new()]),
        }
    }
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

fn parse_params(
    message: &ast::Message<SpannedSlice>,
    spec: &CatalogSpec,
) -> Result<Contract, Failure> {
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
            return Err(semantic_failure(
                "I18N_PARAM_SYNTAX",
                format!("invalid @param declaration {line:?}"),
                spec,
                text(&message.id.name),
            ));
        };
        let Some((type_name, after_type)) = after_open.split_once('}') else {
            return Err(semantic_failure(
                "I18N_PARAM_SYNTAX",
                format!("invalid @param declaration {line:?}"),
                spec,
                text(&message.id.name),
            ));
        };
        if !matches!(type_name, "str" | "int" | "Decimal" | "datetime" | "Slot") {
            return Err(semantic_failure(
                "I18N_PARAM_TYPE_UNSUPPORTED",
                format!("unsupported Phase 0 type {type_name:?}"),
                spec,
                text(&message.id.name),
            ));
        }
        let variable_part = after_type.trim();
        let variable_token = variable_part.split_whitespace().next().unwrap_or("");
        let Some(name) = variable_token.strip_prefix('$') else {
            return Err(semantic_failure(
                "I18N_PARAM_SYNTAX",
                format!("invalid @param declaration {line:?}"),
                spec,
                text(&message.id.name),
            ));
        };
        if name.is_empty()
            || !name
                .chars()
                .all(|item| item == '_' || item.is_ascii_alphanumeric())
        {
            return Err(semantic_failure(
                "I18N_PARAM_SYNTAX",
                format!("invalid @param variable {variable_token:?}"),
                spec,
                text(&message.id.name),
            ));
        }
        if result
            .insert(name.to_owned(), type_name.to_owned())
            .is_some()
        {
            return Err(semantic_failure(
                "I18N_PARAM_DUPLICATE",
                format!("duplicate @param for ${name}"),
                spec,
                text(&message.id.name),
            ));
        }
    }
    Ok(result)
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
    for variable in &used {
        if !params.contains_key(variable) {
            return Err(semantic_failure(
                "I18N_PARAM_MISSING",
                format!(
                    "source message {:?} uses ${variable} without @param",
                    text(&message.id.name)
                ),
                spec,
                text(&message.id.name),
            ));
        }
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

fn merge_type(
    contract: &mut Contract,
    name: &str,
    type_name: &str,
    spec: &CatalogSpec,
    message_id: &str,
) -> Result<(), Failure> {
    if let Some(previous) = contract.get(name) {
        if previous != type_name {
            return Err(semantic_failure(
                "I18N_TRANSITIVE_TYPE_CONFLICT",
                format!("${name} is inherited as both {previous} and {type_name}"),
                spec,
                message_id,
            ));
        }
    } else {
        contract.insert(name.to_owned(), type_name.to_owned());
    }
    Ok(())
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
    let start = entry_offset(&spec.source, message_id, false).unwrap_or(0);
    Failure::new(code, message)
        .at(&spec.path, &spec.source, start, start + message_id.len())
        .for_message(message_id)
}

fn entry_offset(source: &str, id: &str, term: bool) -> Option<usize> {
    let needle = if term {
        format!("-{id} =")
    } else {
        format!("{id} =")
    };
    source
        .match_indices(&needle)
        .find(|(index, _)| *index == 0 || source.as_bytes().get(index - 1) == Some(&b'\n'))
        .map(|(index, _)| index)
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
    let mut messages = BTreeMap::new();
    let mut terms = BTreeMap::new();
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
                if messages.insert(id.clone(), message).is_some() {
                    return Err(semantic_failure(
                        "I18N_DUPLICATE_MESSAGE",
                        format!("message {id:?} is defined twice"),
                        spec,
                        &id,
                    ));
                }
            }
            Entry::Term(term) => {
                let id = text(&term.id.name).to_owned();
                validate_decoded_pattern(&term.value, spec, &format!("-{id}"))?;
                for attribute in &term.attributes {
                    validate_decoded_pattern(&attribute.value, spec, &format!("-{id}"))?;
                }
                if terms.insert(id.clone(), term).is_some() {
                    return Err(semantic_failure(
                        "I18N_DUPLICATE_TERM",
                        format!("term -{id} is defined twice"),
                        spec,
                        &id,
                    ));
                }
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
                result.push_nested(render_expression(expression, key, graph, linker, contract)?);
                result.source.push_str(" }");
            }
        }
    }
    Ok(result)
}

fn render_expression(
    expression: &Expression<SpannedSlice>,
    key: &OutputKey,
    graph: &ResolutionGraph,
    linker: &Linker,
    contract: &Contract,
) -> Result<RenderedPattern, Failure> {
    match expression {
        Expression::Inline(inline) => render_inline(inline, key, graph, linker, contract),
        Expression::Select { selector, variants } => {
            render_select(selector, variants, key, graph, linker, contract)
        }
    }
}

fn render_inline(
    inline: &InlineExpression<SpannedSlice>,
    key: &OutputKey,
    graph: &ResolutionGraph,
    linker: &Linker,
    contract: &Contract,
) -> Result<RenderedPattern, Failure> {
    let definition = graph.messages[key];
    let catalog = &linker.catalogs[definition.catalog];
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
                "str" => ("CITRY_TEXT", "scalar"),
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
            let definition = graph.messages[key];
            let name = text(&id.name);
            result.push_operation(
                term_internal_id(&graph.locale, name, &linker.catalogs[definition.catalog]),
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
            result.push_nested(render_expression(expression, key, graph, linker, contract)?);
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
    graph: &ResolutionGraph,
    linker: &Linker,
    contract: &Contract,
) -> Result<RenderedPattern, Failure> {
    let definition = graph.messages[key];
    let catalog = &linker.catalogs[definition.catalog];
    let authored = inline_span(selector, &catalog.spec.source)?;
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
    if !contract
        .get(variable)
        .is_some_and(|type_name| matches!(type_name.as_str(), "int" | "Decimal"))
    {
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
    let exact = variants
        .iter()
        .filter_map(|variant| match &variant.key {
            VariantKey::NumberLiteral { value } => Some(value.as_ref()),
            VariantKey::Identifier { .. } => None,
        })
        .collect::<Vec<_>>();
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
        selector_source.push_str(&format!(", exact: \"{}\"", exact.join(",")));
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
        (!exact.is_empty()).then(|| exact.join(",")),
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
                result.source.push_str("[exact-");
                result.source.push_str(value.as_ref());
                result.source.push_str("] ");
            }
        }
        result.push_nested(render_pattern(
            &variant.value,
            key,
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
    request: CompileRequest,
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
    let request_paths: BTreeSet<_> = request
        .catalogs
        .iter()
        .map(|item| item.path.clone())
        .collect();
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
    let mut catalogs = vec![];
    for spec in specs {
        let digest = digest_text(&spec.source);
        let parsed = match state.cache.get(&spec.path) {
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
                state.cache.insert(spec.path.clone(), Arc::clone(&parsed));
                parsed
            }
        };
        catalogs.push(LoadedCatalog { spec, parsed });
    }

    let linker = Linker::new(&request, catalogs)?;
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
            let contract = linker.source_contract(root)?;
            let graph = linker.resolve(&active_locale, root)?;
            linker.validate_slots(root, &graph, &contract)?;
            for (key, definition) in &graph.messages {
                let catalog = &linker.catalogs[definition.catalog];
                let key_contract = linker.source_contract(key)?;
                let pattern = pattern_for(catalog, key).expect("linked pattern");
                let generated = render_pattern(pattern, key, &graph, &linker, &key_contract)?;
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
                let generated =
                    render_pattern(&term_node.value, root, &graph, &linker, &Contract::new())?;
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
            locale_manifest.insert(
                root.token(),
                ManifestEntry {
                    owner,
                    bundle_locale: graph.locale.clone(),
                    internal_id: internal_id(&graph.locale, root, selected),
                    contract,
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

    let revision_payload = serde_json::to_string(&(&artifacts, &manifest, &source_maps))
        .map_err(|error| Failure::new("I18N_INTERNAL_JSON", error.to_string()))?;
    Ok(CompileResult {
        schema_version: SCHEMA_VERSION,
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
    })
}

#[pyclass]
struct CatalogCompiler {
    state: Mutex<CompilerState>,
}

#[pymethods]
impl CatalogCompiler {
    #[new]
    fn new() -> Self {
        Self {
            state: Mutex::new(CompilerState::default()),
        }
    }

    fn compile(&self, py: Python<'_>, request_json: &str) -> PyResult<String> {
        let request: CompileRequest = serde_json::from_str(request_json).map_err(|error| {
            Failure::new(
                "I18N_REQUEST_JSON",
                format!("invalid compile request: {error}"),
            )
            .into_pyerr(py)
        })?;
        let mut state = self
            .state
            .lock()
            .map_err(|_| PyRuntimeError::new_err("i18n compiler state mutex is poisoned"))?;
        let result = compile_request(&mut state, request).map_err(|error| error.into_pyerr(py))?;
        serde_json::to_string(&result).map_err(|error| PyRuntimeError::new_err(error.to_string()))
    }

    fn clear(&self) -> PyResult<()> {
        let mut state = self
            .state
            .lock()
            .map_err(|_| PyRuntimeError::new_err("i18n compiler state mutex is poisoned"))?;
        state.cache.clear();
        Ok(())
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

fn plural_category(locale: &str, value: &str, exact: Option<&str>, mode: &str) -> Option<String> {
    let normalized = normalized_decimal(value)?;
    if let Some(exact) = exact {
        for candidate in exact.split(',') {
            if normalized_decimal(candidate).as_ref() == Some(&normalized) {
                return Some(format!("exact-{candidate}"));
            }
        }
    }
    let unsigned = value.strip_prefix('-').unwrap_or(value);
    let (integer_text, fraction) = unsigned.split_once('.').unwrap_or((unsigned, ""));
    let integer = integer_text.parse::<i128>().ok()?;
    if mode == "ordinal" {
        if !fraction.is_empty() {
            return Some("other".to_owned());
        }
        if locale == "en-US" && !matches!(integer % 100, 11..=13) {
            return Some(
                match integer % 10 {
                    1 => "one",
                    2 => "two",
                    3 => "few",
                    _ => "other",
                }
                .to_owned(),
            );
        }
        return Some("other".to_owned());
    }
    if mode != "cardinal" {
        return None;
    }
    if locale == "cs-CZ" {
        if !fraction.is_empty() {
            Some("many".to_owned())
        } else if integer == 1 {
            Some("one".to_owned())
        } else if (2..=4).contains(&integer) {
            Some("few".to_owned())
        } else {
            Some("other".to_owned())
        }
    } else if fraction.is_empty() && integer == 1 {
        Some("one".to_owned())
    } else {
        Some("other".to_owned())
    }
}

fn register_runtime_functions(bundle: &mut RuntimeBundle, locale: &str) {
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
    bundle
        .add_function("NUMBER", |positional, named| {
            let Some(value) = positional.first().and_then(fluent_text) else {
                return FluentValue::Error;
            };
            let Some(profile) = named_text(named, "profile") else {
                return FluentValue::Error;
            };
            if named.iter().count() != 1 {
                return FluentValue::Error;
            }
            format!("{FSI}NUM[value={value},profile={profile}]{PDI}").into()
        })
        .expect("NUMBER registration failed");
    bundle
        .add_function("DATETIME", |positional, named| {
            let Some(value) = positional.first().and_then(fluent_text) else {
                return FluentValue::Error;
            };
            let Some(profile) = named_text(named, "profile") else {
                return FluentValue::Error;
            };
            if named.iter().count() != 1 {
                return FluentValue::Error;
            }
            format!("{FSI}DATE[value={value},profile={profile}]{PDI}").into()
        })
        .expect("DATETIME registration failed");
    let locale = locale.to_owned();
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
            plural_category(&locale, &value, exact.as_deref(), &mode)
                .map(FluentValue::from)
                .unwrap_or(FluentValue::Error)
        })
        .expect("CITRY_PLURAL registration failed");
}

#[derive(Debug, Deserialize)]
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
        _ => None,
    }
}

fn validate_tagged_arg(name: &str, type_name: &str, argument: &TaggedArg) -> PyResult<()> {
    let expected = expected_wire_tag(type_name).ok_or_else(|| {
        PyValueError::new_err(format!("unsupported source type {type_name:?} for ${name}"))
    })?;
    if argument.type_name != expected {
        return Err(PyValueError::new_err(format!(
            "${name} expects wire type {expected:?}, got {:?}",
            argument.type_name
        )));
    }
    if contains_bidi_control(&argument.value) {
        return Err(PyValueError::new_err(format!(
            "${name} contains a prohibited bidi-control character"
        )));
    }
    if contains_paragraph_boundary(&argument.value) {
        return Err(PyValueError::new_err(format!(
            "${name} contains a paragraph boundary"
        )));
    }
    let valid = match type_name {
        "str" => true,
        "int" => valid_integer(&argument.value),
        "Decimal" => valid_decimal(&argument.value),
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
        return Err(PyValueError::new_err(format!(
            "${name} has an invalid {type_name} wire value"
        )));
    }
    Ok(())
}

#[pyclass(unsendable)]
struct I18nRuntime {
    revision: String,
    manifest: BTreeMap<String, BTreeMap<String, ManifestEntry>>,
    bundles: BTreeMap<String, RuntimeBundle>,
}

#[pymethods]
impl I18nRuntime {
    #[new]
    fn new(compiled_json: &str) -> PyResult<Self> {
        let compiled: CompileResult = serde_json::from_str(compiled_json).map_err(|error| {
            PyValueError::new_err(format!("invalid compiled artifact: {error}"))
        })?;
        if compiled.schema_version != SCHEMA_VERSION {
            return Err(PyValueError::new_err(format!(
                "expected compiled schema {}, got {}",
                SCHEMA_VERSION, compiled.schema_version
            )));
        }
        let mut bundles = BTreeMap::new();
        for (locale, source) in compiled.artifacts {
            let language: LanguageIdentifier = locale.parse().map_err(|error| {
                PyValueError::new_err(format!("invalid artifact locale {locale:?}: {error}"))
            })?;
            let mut bundle = FluentBundle::new_concurrent(vec![language]);
            bundle.set_use_isolating(false);
            register_runtime_functions(&mut bundle, &locale);
            let resource = FluentResource::try_new(source).map_err(|(_, errors)| {
                PyValueError::new_err(format!("invalid linked artifact: {errors:?}"))
            })?;
            bundle.add_resource(Arc::new(resource)).map_err(|errors| {
                PyValueError::new_err(format!("artifact resource conflict: {errors:?}"))
            })?;
            bundles.insert(locale, bundle);
        }
        Ok(Self {
            revision: compiled.revision,
            manifest: compiled.manifest,
            bundles,
        })
    }

    #[getter]
    fn revision(&self) -> &str {
        &self.revision
    }

    #[pyo3(signature = (active_locale, message_id, args_json="{}", attribute=None))]
    fn format(
        &self,
        active_locale: &str,
        message_id: &str,
        args_json: &str,
        attribute: Option<&str>,
    ) -> PyResult<String> {
        let token = attribute.map_or_else(
            || message_id.to_owned(),
            |item| format!("{message_id}.{item}"),
        );
        let entry = self
            .manifest
            .get(active_locale)
            .and_then(|entries| entries.get(&token))
            .ok_or_else(|| {
                PyValueError::new_err(format!(
                    "no compiled output {token:?} for {active_locale:?}"
                ))
            })?;
        let raw_args: BTreeMap<String, TaggedArg> = serde_json::from_str(args_json)
            .map_err(|error| PyValueError::new_err(format!("invalid message args: {error}")))?;
        let expected: BTreeSet<_> = entry.contract.keys().cloned().collect();
        let actual: BTreeSet<_> = raw_args.keys().cloned().collect();
        if actual != expected {
            return Err(PyValueError::new_err(format!(
                "message {token:?} expected args {expected:?}, got {actual:?}"
            )));
        }
        let mut args = FluentArgs::new();
        for (name, type_name) in &entry.contract {
            let argument = &raw_args[name];
            validate_tagged_arg(name, type_name, argument)?;
            args.set(name.clone(), argument.value.clone());
        }
        let bundle = self
            .bundles
            .get(&entry.bundle_locale)
            .ok_or_else(|| PyRuntimeError::new_err("manifest points to a missing bundle"))?;
        let message = bundle
            .get_message(&entry.internal_id)
            .ok_or_else(|| PyRuntimeError::new_err("manifest points to a missing message"))?;
        let pattern = message
            .value()
            .ok_or_else(|| PyRuntimeError::new_err("linked internal message has no value"))?;
        let mut errors = vec![];
        let value = bundle
            .format_pattern(pattern, Some(&args), &mut errors)
            .into_owned();
        if !errors.is_empty() {
            return Err(PyValueError::new_err(format!(
                "message format failed: {errors:?}"
            )));
        }
        Ok(value)
    }
}

#[pymodule]
fn citry_i18n_phase0(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("SCHEMA_VERSION", SCHEMA_VERSION)?;
    m.add("I18nCompileError", m.py().get_type::<I18nCompileError>())?;
    m.add_class::<CatalogCompiler>()?;
    m.add_class::<I18nRuntime>()?;
    Ok(())
}
