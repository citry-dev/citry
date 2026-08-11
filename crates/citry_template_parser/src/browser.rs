//! Portable JavaScript analysis for Citry-owned Alpine expression hosts.
//!
//! OXC owns JavaScript syntax and lexical scope resolution here. Citry wraps
//! authored fragments in a generated async function, then maps only exact
//! unresolved identifier references back to authored UTF-8 byte offsets. The
//! wrapper makes Alpine statement contexts parseable without pretending that
//! the template language is a complete JavaScript module.

use std::str::FromStr;

use oxc_allocator::Allocator;
use oxc_ast::ast::{
    Argument, ArrowFunctionBody, AssignmentExpression, AssignmentTarget, CallExpression,
    Expression, FormalParameters, Function, ObjectExpression, ObjectPropertyKind,
};
use oxc_ast_visit::{walk, Visit};
use oxc_parser::Parser;
use oxc_semantic::{Scoping, SemanticBuilder, SymbolId};
use oxc_span::{GetSpan, SourceType};
use oxc_syntax::{operator::AssignmentOperator, scope::ScopeFlags};

/// The grammar expected for one authored browser-expression host.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum BrowserAnalysisMode {
    Expression,
    Statement,
}

impl FromStr for BrowserAnalysisMode {
    type Err = String;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        match value {
            "expression" => Ok(Self::Expression),
            "statement" => Ok(Self::Statement),
            _ => Err(format!("unknown browser analysis mode: {value:?}")),
        }
    }
}

/// One free JavaScript identifier in authored source.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BrowserReference {
    pub name: String,
    pub start: usize,
    pub end: usize,
}

/// Parser and scope result with generated wrapper details removed.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BrowserAnalysis {
    pub valid: bool,
    pub references: Vec<BrowserReference>,
}

/// One direct synchronous write to the `$component` callback's scope object.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BrowserScopeWrite {
    pub name: String,
    pub name_start: usize,
    pub name_end: usize,
    pub value_start: usize,
    pub value_end: usize,
}

/// One name destructured from the `$component` initializer context.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BrowserComponentBinding {
    pub name: String,
    pub local_name: String,
    pub start: usize,
    pub end: usize,
    pub references: Vec<(usize, usize)>,
}

/// Source facts proven inside runtime `$component` initializers.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BrowserComponentAnalysis {
    pub valid: bool,
    pub references: Vec<BrowserReference>,
    pub bindings: Vec<BrowserComponentBinding>,
    pub scope_writes: Vec<BrowserScopeWrite>,
}

/// Parse one Alpine expression/statement and return its exact free roots.
pub fn analyze_browser_source(source: &str, mode: BrowserAnalysisMode) -> BrowserAnalysis {
    let (prefix, suffix) = match mode {
        BrowserAnalysisMode::Expression => (
            "async function __citry_browser_expression__() { return (\n",
            "\n); }",
        ),
        BrowserAnalysisMode::Statement => {
            ("async function __citry_browser_expression__() {\n", "\n}")
        }
    };
    let mut wrapped = String::with_capacity(prefix.len() + source.len() + suffix.len());
    wrapped.push_str(prefix);
    wrapped.push_str(source);
    wrapped.push_str(suffix);

    let allocator = Allocator::default();
    let parsed = Parser::new(&allocator, &wrapped, SourceType::default()).parse();
    if !parsed.diagnostics.is_empty() {
        return BrowserAnalysis {
            valid: false,
            references: Vec::new(),
        };
    }
    let built = SemanticBuilder::new_compiler()
        .with_build_nodes(true)
        .with_check_syntax_error(true)
        .build(&parsed.program);
    if !built.diagnostics.is_empty() {
        return BrowserAnalysis {
            valid: false,
            references: Vec::new(),
        };
    }

    let semantic = built.semantic;
    let source_start = prefix.len();
    let source_end = source_start + source.len();
    let mut references = Vec::new();
    for (name, reference_ids) in semantic.scoping().root_unresolved_references() {
        for reference_id in reference_ids {
            let reference = semantic.scoping().get_reference(*reference_id);
            let span = semantic.nodes().get_node(reference.node_id()).span();
            let start = span.start as usize;
            let end = span.end as usize;
            if start < source_start || end > source_end || start >= end {
                continue;
            }
            references.push(BrowserReference {
                name: name.to_string(),
                start: start - source_start,
                end: end - source_start,
            });
        }
    }
    references.sort_by(|left, right| {
        (left.start, left.end, &left.name).cmp(&(right.start, right.end, &right.name))
    });
    BrowserAnalysis {
        valid: true,
        references,
    }
}

/// Analyze runtime `$component` initializers without executing their source.
pub fn analyze_component_source(source: &str) -> BrowserComponentAnalysis {
    let allocator = Allocator::default();
    let parsed = Parser::new(&allocator, source, SourceType::default()).parse();
    if !parsed.diagnostics.is_empty() {
        return BrowserComponentAnalysis {
            valid: false,
            references: Vec::new(),
            bindings: Vec::new(),
            scope_writes: Vec::new(),
        };
    }
    let built = SemanticBuilder::new_compiler()
        .with_build_nodes(true)
        .with_check_syntax_error(true)
        .build(&parsed.program);
    if !built.diagnostics.is_empty() {
        return BrowserComponentAnalysis {
            valid: false,
            references: Vec::new(),
            bindings: Vec::new(),
            scope_writes: Vec::new(),
        };
    }
    let semantic = built.semantic;
    let mut visitor = ComponentVisitor::new(semantic.scoping());
    visitor.visit_program(&parsed.program);
    visitor.scope_writes.sort_by(|left, right| {
        (left.name_start, left.name_end, &left.name).cmp(&(
            right.name_start,
            right.name_end,
            &right.name,
        ))
    });
    visitor.scope_writes.dedup();
    let mut bindings = visitor
        .bindings
        .into_iter()
        .map(|candidate| {
            let mut references = semantic
                .scoping()
                .get_resolved_references(candidate.symbol_id)
                .map(|reference| semantic.nodes().get_node(reference.node_id()).span())
                .map(|span| (span.start as usize, span.end as usize))
                .collect::<Vec<_>>();
            references.sort_unstable();
            references.dedup();
            BrowserComponentBinding {
                name: candidate.name,
                local_name: candidate.local_name,
                start: candidate.start,
                end: candidate.end,
                references,
            }
        })
        .collect::<Vec<_>>();
    bindings.sort_by(|left, right| {
        (left.start, left.end, &left.local_name).cmp(&(right.start, right.end, &right.local_name))
    });
    bindings.dedup();

    // Root-unresolved references are already scope-aware. Keeping only spans
    // inside a proven initializer excludes the helper call and file-level JS.
    let mut references = Vec::new();
    for (name, reference_ids) in semantic.scoping().root_unresolved_references() {
        for reference_id in reference_ids {
            let reference = semantic.scoping().get_reference(*reference_id);
            let span = semantic.nodes().get_node(reference.node_id()).span();
            let start = span.start as usize;
            let end = span.end as usize;
            if start >= end
                || !visitor
                    .initializer_ranges
                    .iter()
                    .any(|(range_start, range_end)| start >= *range_start && end <= *range_end)
            {
                continue;
            }
            references.push(BrowserReference {
                name: name.to_string(),
                start,
                end,
            });
        }
    }
    references.sort_by(|left, right| {
        (left.start, left.end, &left.name).cmp(&(right.start, right.end, &right.name))
    });
    references.dedup();

    BrowserComponentAnalysis {
        valid: true,
        references,
        bindings,
        scope_writes: visitor.scope_writes,
    }
}

/// Find static top-level scope properties written during `$component` init.
pub fn analyze_component_scope_writes(source: &str) -> Vec<BrowserScopeWrite> {
    analyze_component_source(source).scope_writes
}

struct ComponentVisitor<'semantic> {
    scoping: &'semantic Scoping,
    initializer_ranges: Vec<(usize, usize)>,
    bindings: Vec<ComponentBindingCandidate>,
    scope_writes: Vec<BrowserScopeWrite>,
}

impl<'a> Visit<'a> for ComponentVisitor<'_> {
    fn visit_call_expression(&mut self, call: &CallExpression<'a>) {
        if self.is_unresolved_identifier(&call.callee, "$component") {
            if let Some(argument) = call.arguments.first().and_then(Argument::as_expression) {
                self.collect_initializer(argument);
            }
        }
        walk::walk_call_expression(self, call);
    }
}

impl<'semantic> ComponentVisitor<'semantic> {
    fn new(scoping: &'semantic Scoping) -> Self {
        Self {
            scoping,
            initializer_ranges: Vec::new(),
            bindings: Vec::new(),
            scope_writes: Vec::new(),
        }
    }

    fn is_unresolved_identifier(&self, expression: &Expression<'_>, name: &str) -> bool {
        expression
            .get_identifier_reference()
            .is_some_and(|identifier| {
                identifier.name == name
                    && self
                        .scoping
                        .get_reference(identifier.reference_id())
                        .symbol_id()
                        .is_none()
            })
    }

    fn collect_initializer<'a>(&mut self, expression: &Expression<'a>) {
        match expression.without_parentheses() {
            Expression::ArrowFunctionExpression(function) => {
                self.collect_arrow(function);
            }
            Expression::FunctionExpression(function) => {
                self.collect_function(function);
            }
            Expression::ObjectExpression(object) => {
                for property in &object.properties {
                    let Some(property) = property.as_property() else {
                        continue;
                    };
                    if property.key.is_specific_static_name("init") {
                        self.collect_initializer(&property.value);
                    }
                }
            }
            _ => {}
        }
    }

    fn collect_arrow<'a>(&mut self, function: &oxc_ast::ast::ArrowFunctionExpression<'a>) {
        let span = function.span();
        self.initializer_ranges
            .push((span.start as usize, span.end as usize));
        self.bindings
            .extend(component_context_bindings(&function.params));
        if let Some((scope_name, scope_symbol)) = scope_parameter(&function.params) {
            let mut visitor = ScopeWriteVisitor::new(scope_name, scope_symbol, self.scoping);
            match &function.body {
                ArrowFunctionBody::FunctionBody(body) => visitor.visit_function_body(body),
                body => visitor.visit_expression(body.to_expression()),
            }
            visitor.discard_writes_after_rebind();
            self.scope_writes.extend(visitor.writes);
        }
    }

    fn collect_function<'a>(&mut self, function: &Function<'a>) {
        let span = function.span();
        self.initializer_ranges
            .push((span.start as usize, span.end as usize));
        self.bindings
            .extend(component_context_bindings(&function.params));
        if let (Some((scope_name, scope_symbol)), Some(body)) =
            (scope_parameter(&function.params), &function.body)
        {
            let mut visitor = ScopeWriteVisitor::new(scope_name, scope_symbol, self.scoping);
            visitor.visit_function_body(body);
            visitor.discard_writes_after_rebind();
            self.scope_writes.extend(visitor.writes);
        }
    }
}

struct ComponentBindingCandidate {
    name: String,
    local_name: String,
    start: usize,
    end: usize,
    symbol_id: SymbolId,
}

fn component_context_bindings(params: &FormalParameters<'_>) -> Vec<ComponentBindingCandidate> {
    let Some(first) = params.items.first() else {
        return Vec::new();
    };
    let oxc_ast::ast::BindingPattern::ObjectPattern(pattern) = &first.pattern else {
        return Vec::new();
    };
    pattern
        .properties
        .iter()
        .filter_map(|property| {
            let name = property.key.static_name()?;
            let identifier = property.value.get_binding_identifier()?;
            let span = identifier.span();
            Some(ComponentBindingCandidate {
                name: name.into_owned(),
                local_name: identifier.name.to_string(),
                start: span.start as usize,
                end: span.end as usize,
                symbol_id: identifier.symbol_id(),
            })
        })
        .collect()
}

fn scope_parameter<'a>(params: &'a FormalParameters<'a>) -> Option<(&'a str, SymbolId)> {
    let first = params.items.first()?;
    let oxc_ast::ast::BindingPattern::ObjectPattern(pattern) = &first.pattern else {
        return None;
    };
    pattern.properties.iter().find_map(|property| {
        if !property.key.is_specific_static_name("scope") {
            return None;
        }
        let identifier = property.value.get_binding_identifier()?;
        Some((identifier.name.as_str(), identifier.symbol_id()))
    })
}

struct ScopeWriteVisitor<'name, 'semantic> {
    scope_name: &'name str,
    scope_symbol: SymbolId,
    scoping: &'semantic Scoping,
    rebound_at: Option<usize>,
    writes: Vec<BrowserScopeWrite>,
}

impl<'name, 'semantic> ScopeWriteVisitor<'name, 'semantic> {
    fn new(scope_name: &'name str, scope_symbol: SymbolId, scoping: &'semantic Scoping) -> Self {
        Self {
            scope_name,
            scope_symbol,
            scoping,
            rebound_at: None,
            writes: Vec::new(),
        }
    }

    fn is_scope_reference(&self, expression: &Expression<'_>) -> bool {
        expression
            .get_identifier_reference()
            .is_some_and(|identifier| self.identifier_is_scope(identifier))
    }

    fn identifier_is_scope(&self, identifier: &oxc_ast::ast::IdentifierReference<'_>) -> bool {
        identifier.name == self.scope_name
            && self
                .scoping
                .get_reference(identifier.reference_id())
                .symbol_id()
                == Some(self.scope_symbol)
    }

    fn discard_writes_after_rebind(&mut self) {
        if let Some(rebound_at) = self.rebound_at {
            self.writes.retain(|write| write.name_start < rebound_at);
        }
    }

    fn push_member_write(
        &mut self,
        member: &oxc_ast::ast::MemberExpression<'_>,
        value: &Expression<'_>,
    ) {
        if !self.is_scope_reference(member.object()) {
            return;
        }
        let Some((name_span, name)) = member.static_property_info() else {
            return;
        };
        let value_span = value.span();
        self.writes.push(BrowserScopeWrite {
            name: name.to_string(),
            name_start: name_span.start as usize,
            name_end: name_span.end as usize,
            value_start: value_span.start as usize,
            value_end: value_span.end as usize,
        });
    }

    fn collect_assign_object(&mut self, object: &ObjectExpression<'_>) {
        for property in &object.properties {
            let ObjectPropertyKind::ObjectProperty(property) = property else {
                continue;
            };
            let Some(name) = property.key.static_name() else {
                continue;
            };
            let name_span = property.key.span();
            let value_span = property.value.span();
            self.writes.push(BrowserScopeWrite {
                name: name.into_owned(),
                name_start: name_span.start as usize,
                name_end: name_span.end as usize,
                value_start: value_span.start as usize,
                value_end: value_span.end as usize,
            });
        }
    }
}

impl<'a> Visit<'a> for ScopeWriteVisitor<'_, '_> {
    fn visit_assignment_expression(&mut self, assignment: &AssignmentExpression<'a>) {
        if assignment.operator == AssignmentOperator::Assign {
            if let AssignmentTarget::AssignmentTargetIdentifier(identifier) = &assignment.left {
                if self.identifier_is_scope(identifier) {
                    let start = assignment.span.start as usize;
                    self.rebound_at =
                        Some(self.rebound_at.map_or(start, |current| current.min(start)));
                }
            }
            if let Some(member) = assignment
                .left
                .as_simple_assignment_target()
                .and_then(|target| target.as_member_expression())
            {
                self.push_member_write(member, &assignment.right);
            }
        }
        walk::walk_assignment_expression(self, assignment);
    }

    fn visit_call_expression(&mut self, call: &CallExpression<'a>) {
        if call.callee.is_specific_member_access("Object", "assign")
            && call
                .arguments
                .first()
                .and_then(Argument::as_expression)
                .is_some_and(|argument| self.is_scope_reference(argument))
        {
            if let Some(Expression::ObjectExpression(object)) =
                call.arguments.get(1).and_then(Argument::as_expression)
            {
                self.collect_assign_object(object);
            }
        }
        walk::walk_call_expression(self, call);
    }

    // Writes scheduled inside another function do not happen synchronously
    // during component initialization, so they cannot prove Alpine bindings.
    fn visit_function(&mut self, _function: &Function<'a>, _flags: ScopeFlags) {}

    fn visit_arrow_function_expression(
        &mut self,
        _function: &oxc_ast::ast::ArrowFunctionExpression<'a>,
    ) {
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn expression_analysis_reports_only_free_identifiers() {
        let source = "items.map((item) => item.name + suffix)";
        let analysis = analyze_browser_source(source, BrowserAnalysisMode::Expression);

        assert!(analysis.valid);
        assert_eq!(
            analysis.references,
            vec![
                BrowserReference {
                    name: "items".to_string(),
                    start: 0,
                    end: 5,
                },
                BrowserReference {
                    name: "suffix".to_string(),
                    start: 32,
                    end: 38,
                },
            ]
        );
    }

    #[test]
    fn statement_analysis_resolves_local_declarations() {
        let source = "const local = source; target = local";
        let analysis = analyze_browser_source(source, BrowserAnalysisMode::Statement);

        assert!(analysis.valid);
        assert_eq!(
            analysis
                .references
                .iter()
                .map(|reference| reference.name.as_str())
                .collect::<Vec<_>>(),
            ["source", "target"]
        );
    }

    #[test]
    fn invalid_source_never_returns_partial_references() {
        let analysis = analyze_browser_source("value(", BrowserAnalysisMode::Expression);

        assert!(!analysis.valid);
        assert!(analysis.references.is_empty());
    }

    #[test]
    fn component_scope_writes_cover_direct_static_forms_but_not_rebinding_or_later_work() {
        let source = r#"
$component(({ scope: alpineScope }) => {
  alpineScope.title = data.title;
  alpineScope["count"] = 2;
  Object.assign(alpineScope, { active: true, "display-name": label, ...other });
  alpineScope = other;
  alpineScope.afterRebind = false;
  { const alpineScope = {}; alpineScope.shadowed = true; }
  queueMicrotask(() => { alpineScope.late = true; });
});
"#;

        let writes = analyze_component_scope_writes(source);

        assert_eq!(
            writes
                .iter()
                .map(|write| write.name.as_str())
                .collect::<Vec<_>>(),
            ["title", "count", "active", "display-name"]
        );
        assert!(writes.iter().all(|write| {
            source.get(write.name_start..write.name_end).is_some()
                && source.get(write.value_start..write.value_end).is_some()
        }));
    }

    #[test]
    fn component_scope_writes_require_the_runtime_component_helper() {
        let source = r#"
const $component = (callback) => callback({ scope: {} });
$component(({ scope }) => { scope.fake = true; });
"#;

        assert!(analyze_component_scope_writes(source).is_empty());
    }

    #[test]
    fn component_config_init_is_analyzed_but_dynamic_scope_keys_are_not() {
        let source = r#"
$component({
  props: {},
  init({ scope }) {
    scope.ready = true;
    scope[key] = false;
  },
});
"#;

        assert_eq!(
            analyze_component_scope_writes(source)
                .iter()
                .map(|write| write.name.as_str())
                .collect::<Vec<_>>(),
            ["ready"]
        );
    }

    #[test]
    fn component_analysis_reports_context_bindings_and_only_initializer_free_names() {
        let source = r#"
const outside = missingOutside;
$component(({ scope: alpineScope, data, props: clientProps }) => {
  const local = data.title;
  alpineScope.ready = local;
  console.log(clientProps, missingInside);
});
"#;

        let analysis = analyze_component_source(source);

        assert!(analysis.valid);
        assert_eq!(
            analysis
                .bindings
                .iter()
                .map(|binding| (binding.name.as_str(), binding.local_name.as_str()))
                .collect::<Vec<_>>(),
            [
                ("scope", "alpineScope"),
                ("data", "data"),
                ("props", "clientProps")
            ]
        );
        assert!(analysis
            .bindings
            .iter()
            .all(|binding| binding.references.len() == 1));
        assert_eq!(
            analysis
                .references
                .iter()
                .map(|reference| reference.name.as_str())
                .collect::<Vec<_>>(),
            ["console", "missingInside"]
        );
        assert_eq!(
            analysis
                .scope_writes
                .iter()
                .map(|write| write.name.as_str())
                .collect::<Vec<_>>(),
            ["ready"]
        );
    }

    #[test]
    fn shadowed_component_helpers_do_not_create_initializer_facts() {
        let source = r#"
const $component = (callback) => callback({});
$component(({ scope }) => { console.log(scope, missing); });
"#;

        let analysis = analyze_component_source(source);

        assert!(analysis.valid);
        assert!(analysis.references.is_empty());
        assert!(analysis.bindings.is_empty());
        assert!(analysis.scope_writes.is_empty());
    }
}
