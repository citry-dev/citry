//! Portable JavaScript analysis for Citry-owned Vue expression hosts.
//!
//! OXC owns JavaScript syntax and lexical scope resolution here. Citry wraps
//! authored fragments in a generated async function, then maps only exact
//! unresolved identifier references back to authored UTF-8 byte offsets. The
//! wrapper makes Vue statement contexts parseable without pretending that
//! the template language is a complete JavaScript module.

use std::str::FromStr;

use oxc_allocator::Allocator;
use oxc_ast::ast::{
    Argument, ArrowFunctionBody, AssignmentExpression, AssignmentTarget, CallExpression,
    ComputedMemberExpression, Expression, FormalParameters, Function, ObjectExpression,
    ObjectPropertyKind, Statement, StaticMemberExpression,
};
use oxc_ast_visit::{walk, Visit};
use oxc_parser::Parser;
use oxc_semantic::{Scoping, SemanticBuilder, SymbolId};
use oxc_span::{GetSpan, SourceType, Span};
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

/// Parser and scope result for one Vue slot-props parameter pattern or list.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BrowserBindingPatternAnalysis {
    pub valid: bool,
    pub bindings: Vec<BrowserReference>,
    pub references: Vec<BrowserReference>,
}

/// Parse one Vue slot-props parameter list through a synchronous arrow function.
pub fn analyze_browser_binding_pattern(source: &str) -> BrowserBindingPatternAnalysis {
    let prefix = "(";
    let suffix = ") => {}";
    let wrapped = format!("{prefix}{source}{suffix}");
    let invalid = || BrowserBindingPatternAnalysis {
        valid: false,
        bindings: Vec::new(),
        references: Vec::new(),
    };

    let allocator = Allocator::default();
    let parsed = Parser::new(&allocator, &wrapped, SourceType::script()).parse();
    if !parsed.diagnostics.is_empty() {
        return invalid();
    }
    let built = SemanticBuilder::new_compiler()
        .with_build_nodes(true)
        .with_check_syntax_error(true)
        .build(&parsed.program);
    if !built.diagnostics.is_empty() {
        return invalid();
    }
    let [Statement::ExpressionStatement(statement)] = parsed.program.body.as_slice() else {
        return invalid();
    };
    let Expression::ArrowFunctionExpression(function) = statement.expression.without_parentheses()
    else {
        return invalid();
    };
    let function_span = function.span();
    let params_span = function.params.span();
    let body_span = function.body.span();
    let ArrowFunctionBody::FunctionBody(body) = &function.body else {
        return invalid();
    };
    if function.r#async
        || function_span.start != 0
        || function_span.end as usize != wrapped.len()
        || params_span.start != 0
        || params_span.end as usize != source.len() + 2
        || body_span.start as usize != wrapped.len() - 2
        || body_span.end as usize != wrapped.len()
        || !body.directives.is_empty()
        || !body.statements.is_empty()
    {
        return invalid();
    }

    let source_start = prefix.len();
    let source_end = source_start + source.len();
    let identifiers = function
        .params
        .items
        .iter()
        .flat_map(|parameter| parameter.pattern.get_binding_identifiers())
        .chain(
            function
                .params
                .rest
                .iter()
                .flat_map(|rest| rest.rest.argument.get_binding_identifiers()),
        );
    let mut bindings = identifiers
        .filter_map(|identifier| {
            let span = identifier.span();
            let start = span.start as usize;
            let end = span.end as usize;
            (start >= source_start && end <= source_end && start < end).then(|| BrowserReference {
                name: identifier.name.to_string(),
                start: start - source_start,
                end: end - source_start,
            })
        })
        .collect::<Vec<_>>();
    bindings.sort_by(|left, right| {
        (left.start, left.end, &left.name).cmp(&(right.start, right.end, &right.name))
    });

    let semantic = built.semantic;
    let mut references = Vec::new();
    for (name, reference_ids) in semantic.scoping().root_unresolved_references() {
        for reference_id in reference_ids {
            let reference = semantic.scoping().get_reference(*reference_id);
            let span = semantic.nodes().get_node(reference.node_id()).span();
            let start = span.start as usize;
            let end = span.end as usize;
            if start >= source_start && end <= source_end && start < end {
                references.push(BrowserReference {
                    name: name.to_string(),
                    start: start - source_start,
                    end: end - source_start,
                });
            }
        }
    }
    references.sort_by(|left, right| {
        (left.start, left.end, &left.name).cmp(&(right.start, right.end, &right.name))
    });
    BrowserBindingPatternAnalysis {
        valid: true,
        bindings,
        references,
    }
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

/// One root-unresolved `$component` call authenticated by OXC semantics.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BrowserComponentCall {
    pub call_start: usize,
    pub call_end: usize,
    pub callee_start: usize,
    pub callee_end: usize,
    pub open_paren_end: usize,
    pub argument_start: Option<usize>,
    pub argument_end: Option<usize>,
}

/// One statically named public binding declared by Vue Options.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BrowserPublicName {
    pub authored_name: String,
    pub exposed_name: String,
    pub origin: String,
    pub name_start: usize,
    pub name_end: usize,
    pub value_start: Option<usize>,
    pub value_end: Option<usize>,
    pub required: Option<bool>,
    pub has_default: Option<bool>,
    pub default_is_null: Option<bool>,
    pub type_source: Option<String>,
}

/// Conservative knowledge for one Vue Options namespace.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BrowserOptionsSection {
    pub name: String,
    pub state: String,
    pub start: Option<usize>,
    pub end: Option<usize>,
    pub unknown_reason: Option<String>,
}

/// One component-instance member reference with a proven receiver.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BrowserComponentMemberReference {
    pub receiver: String,
    pub name: String,
    pub start: usize,
    pub end: usize,
}

/// Source facts proven inside runtime `$component` initializers.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BrowserComponentAnalysis {
    pub valid: bool,
    pub references: Vec<BrowserReference>,
    pub bindings: Vec<BrowserComponentBinding>,
    pub scope_writes: Vec<BrowserScopeWrite>,
    pub component_calls: Vec<BrowserComponentCall>,
    pub public_names: Vec<BrowserPublicName>,
    pub sections: Vec<BrowserOptionsSection>,
    pub member_references: Vec<BrowserComponentMemberReference>,
}

/// One static member of a proven, unreassigned component context binding.
#[derive(Clone, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub struct BrowserComponentMember {
    pub context_name: String,
    pub member_name: String,
    pub owner_start: usize,
    pub owner_end: usize,
    pub member_start: usize,
    pub member_end: usize,
}

/// Static component members with exact authored UTF-8 byte ranges.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BrowserComponentMemberAnalysis {
    pub valid: bool,
    pub members: Vec<BrowserComponentMember>,
}

/// Find direct context members, including references captured by closures.
///
/// Invalid JavaScript returns no records. Dynamic keys, escaped bracket keys,
/// defaulted context bindings, and bindings assigned anywhere are omitted
/// because their target or exact authored key cannot be established here.
pub fn analyze_component_members(source: &str) -> BrowserComponentMemberAnalysis {
    let invalid = || BrowserComponentMemberAnalysis {
        valid: false,
        members: Vec::new(),
    };
    let allocator = Allocator::default();
    let parsed = Parser::new(&allocator, source, SourceType::default()).parse();
    if !parsed.diagnostics.is_empty() {
        return invalid();
    }
    let built = SemanticBuilder::new_compiler()
        .with_build_nodes(true)
        .with_check_syntax_error(true)
        .build(&parsed.program);
    if !built.diagnostics.is_empty() {
        return invalid();
    }
    let scoping = built.semantic.scoping();
    let mut initializers = MemberInitializerVisitor {
        scoping,
        bindings: Vec::new(),
    };
    initializers.visit_program(&parsed.program);
    // A symbol's writes may run in another closure or branch. Exclude the
    // entire binding rather than infer execution order from source positions.
    initializers.bindings.retain(|binding| {
        binding.direct
            && matches!(
                binding.context_name.as_str(),
                "data" | "scope" | "state" | "props"
            )
            && !scoping
                .get_resolved_references(binding.symbol_id)
                .any(|reference| reference.is_write())
    });
    let mut visitor = ComponentMemberVisitor {
        source,
        scoping,
        bindings: &initializers.bindings,
        members: Vec::new(),
    };
    visitor.visit_program(&parsed.program);
    visitor
        .members
        .sort_by_key(|member| (member.owner_start, member.member_start, member.member_end));
    visitor.members.dedup();
    BrowserComponentMemberAnalysis {
        valid: true,
        members: visitor.members,
    }
}

/// Parse one browser expression/statement and return its exact free roots.
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
            component_calls: Vec::new(),
            public_names: Vec::new(),
            sections: Vec::new(),
            member_references: Vec::new(),
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
            component_calls: Vec::new(),
            public_names: Vec::new(),
            sections: Vec::new(),
            member_references: Vec::new(),
        };
    }
    let semantic = built.semantic;
    let mut visitor = ComponentVisitor::new(source, semantic.scoping());
    visitor.visit_program(&parsed.program);
    visitor.scope_writes.sort_by(|left, right| {
        (left.name_start, left.name_end, &left.name).cmp(&(
            right.name_start,
            right.name_end,
            &right.name,
        ))
    });
    visitor.scope_writes.dedup();
    let component_symbols = visitor
        .bindings
        .iter()
        .filter(|binding| binding.name == "component")
        .map(|binding| binding.symbol_id)
        .collect::<Vec<_>>();
    let mut alias_members = AliasMemberVisitor {
        scoping: semantic.scoping(),
        component_symbols: &component_symbols,
        references: Vec::new(),
    };
    alias_members.visit_program(&parsed.program);
    visitor.member_references.extend(alias_members.references);
    visitor
        .component_calls
        .sort_by_key(|call| (call.call_start, call.call_end));
    visitor.component_calls.dedup();
    visitor
        .public_names
        .sort_by_key(|name| (name.name_start, name.name_end));
    visitor
        .member_references
        .sort_by_key(|reference| (reference.start, reference.end));
    visitor.member_references.dedup();
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
        component_calls: visitor.component_calls,
        public_names: visitor.public_names,
        sections: visitor.sections,
        member_references: visitor.member_references,
    }
}

/// Find static top-level scope properties written during `$component` init.
pub fn analyze_component_scope_writes(source: &str) -> Vec<BrowserScopeWrite> {
    analyze_component_source(source).scope_writes
}

struct ComponentVisitor<'semantic> {
    source: &'semantic str,
    scoping: &'semantic Scoping,
    initializer_ranges: Vec<(usize, usize)>,
    bindings: Vec<ComponentBindingCandidate>,
    scope_writes: Vec<BrowserScopeWrite>,
    component_calls: Vec<BrowserComponentCall>,
    public_names: Vec<BrowserPublicName>,
    sections: Vec<BrowserOptionsSection>,
    member_references: Vec<BrowserComponentMemberReference>,
}

impl<'a> Visit<'a> for ComponentVisitor<'_> {
    fn visit_call_expression(&mut self, call: &CallExpression<'a>) {
        if self.is_unresolved_identifier(&call.callee, "$component") {
            let callee = call.callee.span();
            let call_span = call.span();
            let search_end = call
                .arguments
                .first()
                .map_or(call_span.end as usize, |argument| {
                    argument.span().start as usize
                });
            let open_paren_end = self.source[callee.end as usize..search_end]
                .find('(')
                .map_or(callee.end as usize, |offset| {
                    callee.end as usize + offset + 1
                });
            let argument_span = call.arguments.first().map(GetSpan::span);
            self.component_calls.push(BrowserComponentCall {
                call_start: call_span.start as usize,
                call_end: call_span.end as usize,
                callee_start: callee.start as usize,
                callee_end: callee.end as usize,
                open_paren_end,
                argument_start: argument_span.map(|span| span.start as usize),
                argument_end: argument_span.map(|span| span.end as usize),
            });
            if let Some(argument) = call.arguments.first().and_then(Argument::as_expression) {
                if let Expression::ObjectExpression(options) = argument.without_parentheses() {
                    self.collect_initializer(argument, false);
                    let span = options.span();
                    self.initializer_ranges
                        .push((span.start as usize, span.end as usize));
                    self.collect_options(options);
                } else {
                    self.collect_initializer(argument, true);
                    self.collect_unknown_options(argument.span());
                }
            }
        }
        walk::walk_call_expression(self, call);
    }
}

impl<'semantic> ComponentVisitor<'semantic> {
    fn new(source: &'semantic str, scoping: &'semantic Scoping) -> Self {
        Self {
            source,
            scoping,
            initializer_ranges: Vec::new(),
            bindings: Vec::new(),
            scope_writes: Vec::new(),
            component_calls: Vec::new(),
            public_names: Vec::new(),
            sections: Vec::new(),
            member_references: Vec::new(),
        }
    }

    fn collect_options(&mut self, options: &ObjectExpression<'_>) {
        const SECTIONS: [&str; 6] = ["props", "methods", "computed", "inject", "data", "setup"];
        let options_start = options.span.start as usize;
        for section_name in SECTIONS {
            let mut state = BrowserOptionsSection {
                name: section_name.to_string(),
                state: "absent".to_string(),
                start: None,
                end: None,
                unknown_reason: None,
            };
            for item in &options.properties {
                let Some(property) = item.as_property() else {
                    state.state = "unknown".to_string();
                    state.unknown_reason = Some("top-level-spread".to_string());
                    self.public_names.retain(|name| {
                        name.origin != section_name || name.name_start < options_start
                    });
                    continue;
                };
                if property.computed {
                    state.state = "unknown".to_string();
                    state.unknown_reason = Some("computed-top-level-key".to_string());
                    self.public_names.retain(|name| {
                        name.origin != section_name || name.name_start < options_start
                    });
                    continue;
                }
                if !property.key.is_specific_static_name(section_name) {
                    continue;
                }
                self.public_names
                    .retain(|name| name.origin != section_name || name.name_start < options_start);
                if let (Some(start), Some(end)) = (state.start, state.end) {
                    self.member_references
                        .retain(|reference| reference.start < start || reference.end > end);
                }
                let span = property.span();
                state.start = Some(span.start as usize);
                state.end = Some(span.end as usize);
                state.unknown_reason = None;
                if let Some(object) = section_object(section_name, &property.value) {
                    state.state = "complete".to_string();
                    self.collect_section_names(section_name, object, &mut state);
                } else if section_name == "props" || section_name == "inject" {
                    if let Expression::ArrayExpression(array) = property.value.without_parentheses()
                    {
                        state.state = "complete".to_string();
                        for element in &array.elements {
                            let Some(expression) = element.as_expression() else {
                                state.state = "unknown".to_string();
                                state.unknown_reason = Some("non-literal-entry".to_string());
                                continue;
                            };
                            if let Expression::StringLiteral(literal) =
                                expression.without_parentheses()
                            {
                                let span = literal.span();
                                let authored = literal.value.to_string();
                                self.public_names.push(public_name(
                                    authored,
                                    section_name,
                                    span.start as usize,
                                    span.end as usize,
                                    None,
                                    None,
                                ));
                            } else {
                                state.state = "unknown".to_string();
                                state.unknown_reason = Some("non-literal-entry".to_string());
                            }
                        }
                    } else {
                        state.state = "unknown".to_string();
                        state.unknown_reason = Some("non-literal-section".to_string());
                    }
                } else {
                    state.state = "unknown".to_string();
                    state.unknown_reason = Some("indirect-section".to_string());
                }
                if matches!(section_name, "methods" | "computed" | "data") {
                    self.member_references
                        .extend(bound_instance_members(section_name, &property.value));
                }
            }
            self.sections.push(state);
        }
    }

    fn collect_unknown_options(&mut self, span: oxc_span::Span) {
        for name in ["props", "methods", "computed", "inject", "data", "setup"] {
            self.sections.push(BrowserOptionsSection {
                name: name.to_owned(),
                state: "unknown".to_owned(),
                start: Some(span.start as usize),
                end: Some(span.end as usize),
                unknown_reason: Some("indirect-options".to_owned()),
            });
        }
    }

    fn collect_section_names(
        &mut self,
        section_name: &str,
        object: &ObjectExpression<'_>,
        state: &mut BrowserOptionsSection,
    ) {
        for item in &object.properties {
            let Some(property) = item.as_property() else {
                state.state = "unknown".to_string();
                state.unknown_reason = Some("object-spread".to_string());
                continue;
            };
            if property.computed {
                state.state = "unknown".to_string();
                state.unknown_reason = Some("computed-key".to_string());
                continue;
            }
            let Some(name) = property.key.static_name() else {
                state.state = "unknown".to_string();
                state.unknown_reason = Some("dynamic-key".to_string());
                continue;
            };
            let key_span = property.key.span();
            let details = if section_name == "props" {
                prop_details(&property.value, self.source)
            } else {
                None
            };
            self.public_names.push(public_name(
                name.into_owned(),
                section_name,
                key_span.start as usize,
                key_span.end as usize,
                Some(property.value.span()),
                details,
            ));
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

    fn collect_initializer<'a>(&mut self, expression: &Expression<'a>, authenticate_context: bool) {
        match expression.without_parentheses() {
            Expression::ArrowFunctionExpression(function) => {
                self.collect_arrow(function, authenticate_context);
            }
            Expression::FunctionExpression(function) => {
                self.collect_function(function, authenticate_context);
            }
            Expression::ObjectExpression(object) => {
                for property in &object.properties {
                    let Some(property) = property.as_property() else {
                        continue;
                    };
                    if property.key.is_specific_static_name("init") {
                        self.collect_initializer(&property.value, false);
                    } else if property.key.is_specific_static_name("onServerRender") {
                        self.collect_initializer(&property.value, true);
                    }
                }
            }
            _ => {}
        }
    }

    fn collect_arrow<'a>(
        &mut self,
        function: &oxc_ast::ast::ArrowFunctionExpression<'a>,
        authenticate_context: bool,
    ) {
        let span = function.span();
        self.initializer_ranges
            .push((span.start as usize, span.end as usize));
        if authenticate_context {
            self.bindings
                .extend(component_context_bindings(&function.params));
        }
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

    fn collect_function<'a>(&mut self, function: &Function<'a>, authenticate_context: bool) {
        let span = function.span();
        self.initializer_ranges
            .push((span.start as usize, span.end as usize));
        if authenticate_context {
            self.bindings
                .extend(component_context_bindings(&function.params));
        }
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
            if !matches!(name.as_ref(), "component" | "revision") {
                return None;
            }
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
    // during component initialization, so they cannot prove server bindings.
    fn visit_function(&mut self, _function: &Function<'a>, _flags: ScopeFlags) {}

    fn visit_arrow_function_expression(
        &mut self,
        _function: &oxc_ast::ast::ArrowFunctionExpression<'a>,
    ) {
    }
}

struct MemberBindingCandidate {
    context_name: String,
    symbol_id: SymbolId,
    direct: bool,
}

struct MemberInitializerVisitor<'semantic> {
    scoping: &'semantic Scoping,
    bindings: Vec<MemberBindingCandidate>,
}

impl<'a> Visit<'a> for MemberInitializerVisitor<'_> {
    fn visit_call_expression(&mut self, call: &CallExpression<'a>) {
        if self.is_unresolved_identifier(&call.callee, "$component") {
            if let Some(argument) = call.arguments.first().and_then(Argument::as_expression) {
                self.collect_initializer(argument);
            }
        }
        walk::walk_call_expression(self, call);
    }
}

impl<'semantic> MemberInitializerVisitor<'semantic> {
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
                self.bindings
                    .extend(member_context_bindings(&function.params));
            }
            Expression::FunctionExpression(function) => {
                self.bindings
                    .extend(member_context_bindings(&function.params));
            }
            Expression::ObjectExpression(object) => {
                // A later duplicate, spread, or computed key can replace init.
                // Member errors require one statically selected callback.
                let mut init_count = 0;
                for item in &object.properties {
                    let Some(property) = item.as_property() else {
                        return;
                    };
                    let Some(name) = property.key.static_name() else {
                        return;
                    };
                    if name == "init" {
                        init_count += 1;
                        if property.kind != oxc_ast::ast::PropertyKind::Init {
                            return;
                        }
                    }
                }
                if init_count != 1 {
                    return;
                }
                for item in &object.properties {
                    let Some(property) = item.as_property() else {
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
}

fn member_context_bindings(params: &FormalParameters<'_>) -> Vec<MemberBindingCandidate> {
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
            let context_name = property.key.static_name()?.into_owned();
            let identifier = property.value.get_binding_identifier()?;
            Some(MemberBindingCandidate {
                context_name,
                symbol_id: identifier.symbol_id(),
                direct: matches!(
                    property.value,
                    oxc_ast::ast::BindingPattern::BindingIdentifier(_)
                ),
            })
        })
        .collect()
}

struct ComponentMemberVisitor<'source, 'semantic, 'bindings> {
    source: &'source str,
    scoping: &'semantic Scoping,
    bindings: &'bindings [MemberBindingCandidate],
    members: Vec<BrowserComponentMember>,
}

impl ComponentMemberVisitor<'_, '_, '_> {
    fn push(&mut self, object: &Expression<'_>, name: &str, span: Span) {
        let Some(identifier) = object.without_parentheses().get_identifier_reference() else {
            return;
        };
        let symbol = self
            .scoping
            .get_reference(identifier.reference_id())
            .symbol_id();
        let Some(binding) = self
            .bindings
            .iter()
            .find(|binding| Some(binding.symbol_id) == symbol)
        else {
            return;
        };
        self.members.push(BrowserComponentMember {
            context_name: binding.context_name.clone(),
            member_name: name.to_string(),
            owner_start: identifier.span.start as usize,
            owner_end: identifier.span.end as usize,
            member_start: span.start as usize,
            member_end: span.end as usize,
        });
    }
}

impl<'a> Visit<'a> for ComponentMemberVisitor<'_, '_, '_> {
    fn visit_static_member_expression(&mut self, member: &StaticMemberExpression<'a>) {
        self.push(
            &member.object,
            member.property.name.as_str(),
            member.property.span,
        );
        walk::walk_static_member_expression(self, member);
    }

    fn visit_computed_member_expression(&mut self, member: &ComputedMemberExpression<'a>) {
        // Only unescaped string keys have a one-to-one key range suitable for
        // editor diagnostics; computed expressions remain the JS provider's job.
        if let Expression::StringLiteral(literal) = &member.expression {
            let span = Span::new(literal.span.start + 1, literal.span.end - 1);
            if self.source.get(span.start as usize..span.end as usize)
                == Some(literal.value.as_str())
            {
                self.push(&member.object, literal.value.as_str(), span);
            }
        }
        walk::walk_computed_member_expression(self, member);
    }
}

fn section_object<'a>(
    section: &str,
    value: &'a Expression<'a>,
) -> Option<&'a ObjectExpression<'a>> {
    if section != "data" && section != "setup" {
        return match value.without_parentheses() {
            Expression::ObjectExpression(object) => Some(object),
            _ => None,
        };
    }
    match value.without_parentheses() {
        Expression::ArrowFunctionExpression(function) => match &function.body {
            ArrowFunctionBody::FunctionBody(body) => direct_return_object(&body.statements),
            body => match body.to_expression().without_parentheses() {
                Expression::ObjectExpression(object) => Some(object),
                _ => None,
            },
        },
        Expression::FunctionExpression(function) => function
            .body
            .as_ref()
            .and_then(|body| direct_return_object(&body.statements)),
        _ => None,
    }
}

fn direct_return_object<'a>(
    statements: &'a oxc_allocator::Vec<'a, oxc_ast::ast::Statement<'a>>,
) -> Option<&'a ObjectExpression<'a>> {
    if statements.len() != 1 {
        return None;
    }
    let oxc_ast::ast::Statement::ReturnStatement(statement) = &statements[0] else {
        return None;
    };
    match statement.argument.as_ref()?.without_parentheses() {
        Expression::ObjectExpression(object) => Some(object),
        _ => None,
    }
}

fn public_name(
    authored_name: String,
    origin: &str,
    name_start: usize,
    name_end: usize,
    value_span: Option<oxc_span::Span>,
    prop_details: Option<(bool, bool, bool, Option<String>)>,
) -> BrowserPublicName {
    let exposed_name = if origin == "props" {
        camelize_prop(&authored_name)
    } else {
        authored_name.clone()
    };
    BrowserPublicName {
        authored_name,
        exposed_name,
        origin: origin.to_string(),
        name_start,
        name_end,
        value_start: value_span.map(|span| span.start as usize),
        value_end: value_span.map(|span| span.end as usize),
        required: prop_details.as_ref().map(|details| details.0),
        has_default: prop_details.as_ref().map(|details| details.1),
        default_is_null: prop_details.as_ref().map(|details| details.2),
        type_source: prop_details.and_then(|details| details.3),
    }
}

fn prop_details(
    value: &Expression<'_>,
    source: &str,
) -> Option<(bool, bool, bool, Option<String>)> {
    let Expression::ObjectExpression(object) = value.without_parentheses() else {
        return Some((
            false,
            false,
            false,
            Some(source[value.span().start as usize..value.span().end as usize].to_string()),
        ));
    };
    let mut required = false;
    let mut has_default = false;
    let mut default_is_null = false;
    let mut type_source = None;
    for item in &object.properties {
        let property = item.as_property()?;
        if property.computed || property.key.static_name().is_none() {
            return None;
        }
        if property.key.is_specific_static_name("required") {
            required = matches!(property.value.without_parentheses(), Expression::BooleanLiteral(value) if value.value);
        } else if property.key.is_specific_static_name("default") {
            has_default = true;
            default_is_null = matches!(
                property.value.without_parentheses(),
                Expression::NullLiteral(_)
            );
        } else if property.key.is_specific_static_name("type") {
            let span = property.value.span();
            type_source = Some(source[span.start as usize..span.end as usize].to_string());
        }
    }
    Some((required, has_default, default_is_null, type_source))
}

fn camelize_prop(name: &str) -> String {
    let mut result = String::with_capacity(name.len());
    let mut characters = name.chars().peekable();
    while let Some(character) = characters.next() {
        if character == '-'
            && characters
                .peek()
                .is_some_and(|next| next.is_ascii_alphanumeric() || *next == '_')
        {
            result.push(characters.next().unwrap().to_ascii_uppercase());
        } else {
            result.push(character);
        }
    }
    result
}

fn bound_instance_members(
    section: &str,
    value: &Expression<'_>,
) -> Vec<BrowserComponentMemberReference> {
    let mut visitor = InstanceMemberVisitor::default();
    match (section, value.without_parentheses()) {
        ("methods" | "computed", Expression::ObjectExpression(object)) => {
            for item in &object.properties {
                let Some(property) = item.as_property() else {
                    continue;
                };
                if matches!(
                    property.value.without_parentheses(),
                    Expression::FunctionExpression(_)
                ) {
                    visitor.visit_expression(&property.value);
                } else if section == "computed" {
                    if let Expression::ObjectExpression(descriptor) =
                        property.value.without_parentheses()
                    {
                        for descriptor_item in &descriptor.properties {
                            let Some(descriptor_property) = descriptor_item.as_property() else {
                                continue;
                            };
                            if !descriptor_property.computed
                                && (descriptor_property.key.is_specific_static_name("get")
                                    || descriptor_property.key.is_specific_static_name("set"))
                                && matches!(
                                    descriptor_property.value.without_parentheses(),
                                    Expression::FunctionExpression(_)
                                )
                            {
                                visitor.visit_expression(&descriptor_property.value);
                            }
                        }
                    }
                }
            }
        }
        ("data", Expression::FunctionExpression(_)) => visitor.visit_expression(value),
        _ => {}
    }
    visitor.references
}

#[derive(Default)]
struct InstanceMemberVisitor {
    ordinary_function_depth: usize,
    references: Vec<BrowserComponentMemberReference>,
}

struct AliasMemberVisitor<'symbols, 'semantic> {
    scoping: &'semantic Scoping,
    component_symbols: &'symbols [SymbolId],
    references: Vec<BrowserComponentMemberReference>,
}

impl<'a> Visit<'a> for AliasMemberVisitor<'_, '_> {
    fn visit_static_member_expression(
        &mut self,
        member: &oxc_ast::ast::StaticMemberExpression<'a>,
    ) {
        if let Some(identifier) = member.object.get_identifier_reference() {
            let symbol = self
                .scoping
                .get_reference(identifier.reference_id())
                .symbol_id();
            if symbol.is_some_and(|symbol| self.component_symbols.contains(&symbol)) {
                let span = member.property.span();
                self.references.push(BrowserComponentMemberReference {
                    receiver: "component".to_string(),
                    name: member.property.name.to_string(),
                    start: span.start as usize,
                    end: span.end as usize,
                });
            }
        }
        walk::walk_static_member_expression(self, member);
    }
}

impl<'a> Visit<'a> for InstanceMemberVisitor {
    fn visit_function(&mut self, function: &Function<'a>, flags: ScopeFlags) {
        self.ordinary_function_depth += 1;
        if self.ordinary_function_depth == 1 {
            walk::walk_function(self, function, flags);
        }
        self.ordinary_function_depth -= 1;
    }

    fn visit_static_member_expression(
        &mut self,
        member: &oxc_ast::ast::StaticMemberExpression<'a>,
    ) {
        if self.ordinary_function_depth <= 1
            && matches!(
                member.object.without_parentheses(),
                Expression::ThisExpression(_)
            )
        {
            let span = member.property.span();
            self.references.push(BrowserComponentMemberReference {
                receiver: "this".to_string(),
                name: member.property.name.to_string(),
                start: span.start as usize,
                end: span.end as usize,
            });
        }
        walk::walk_static_member_expression(self, member);
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
    fn binding_pattern_reports_nested_bindings_and_initializer_references() {
        let source = "{ item: local = fallback, nested: [first, ...rest], [key]: computed }";
        let analysis = analyze_browser_binding_pattern(source);

        assert!(analysis.valid);
        assert_eq!(
            analysis
                .bindings
                .iter()
                .map(|item| item.name.as_str())
                .collect::<Vec<_>>(),
            ["local", "first", "rest", "computed"]
        );
        assert_eq!(
            analysis
                .references
                .iter()
                .map(|item| item.name.as_str())
                .collect::<Vec<_>>(),
            ["fallback", "key"]
        );
        for item in analysis.bindings.iter().chain(&analysis.references) {
            assert_eq!(
                &source.as_bytes()[item.start..item.end],
                item.name.as_bytes()
            );
        }
    }

    #[test]
    fn binding_pattern_offsets_are_authored_utf8_bytes_and_invalid_is_empty() {
        let source = "{ café: résumé = fallback }";
        let analysis = analyze_browser_binding_pattern(source);
        assert!(analysis.valid);
        assert_eq!(analysis.bindings[0].name, "résumé");
        assert_eq!(
            &source.as_bytes()[analysis.bindings[0].start..analysis.bindings[0].end],
            "résumé".as_bytes()
        );
        assert_eq!(analysis.references[0].name, "fallback");

        let invalid = analyze_browser_binding_pattern("{ item:");
        assert!(!invalid.valid);
        assert!(invalid.bindings.is_empty());
        assert!(invalid.references.is_empty());

        for escaped in ["x) => {}; (y", "x) => ((y"] {
            let escaped = analyze_browser_binding_pattern(escaped);
            assert!(!escaped.valid);
            assert!(escaped.bindings.is_empty());
            assert!(escaped.references.is_empty());
        }
    }

    #[test]
    fn binding_pattern_accepts_vue_parameter_lists_and_top_level_rest() {
        let parameters = analyze_browser_binding_pattern("x, y = fallback");
        assert!(parameters.valid);
        assert_eq!(
            parameters
                .bindings
                .iter()
                .map(|item| item.name.as_str())
                .collect::<Vec<_>>(),
            ["x", "y"]
        );
        assert_eq!(parameters.references[0].name, "fallback");

        let rest = analyze_browser_binding_pattern("...args");
        assert!(rest.valid);
        assert_eq!(rest.bindings[0].name, "args");
        assert!(rest.references.is_empty());

        let empty = analyze_browser_binding_pattern("");
        assert!(empty.valid);
        assert!(empty.bindings.is_empty());
        assert!(empty.references.is_empty());

        for classic_name in ["await", "yield", "eval", "arguments"] {
            let classic = analyze_browser_binding_pattern(classic_name);
            assert!(classic.valid, "classic Vue parameter {classic_name}");
            assert_eq!(classic.bindings[0].name, classic_name);
        }
    }

    #[test]
    fn component_analysis_reports_context_bindings_and_only_initializer_free_names() {
        let source = r#"
const outside = missingOutside;
$component({ onServerRender({ component: current, revision, data }) {
  const local = data.title;
  current.ready = local;
  console.log(revision, missingInside);
} });
"#;

        let analysis = analyze_component_source(source);

        assert!(analysis.valid);
        assert_eq!(
            analysis
                .bindings
                .iter()
                .map(|binding| (binding.name.as_str(), binding.local_name.as_str()))
                .collect::<Vec<_>>(),
            [("component", "current"), ("revision", "revision")]
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
    }

    #[test]
    fn component_options_report_authenticated_calls_sections_and_public_names() {
        let source = r#"const prefix = 1;
$component /* kept */ ({
  props: ["display-name", "count"],
  methods: { save() {}, ...extraMethods },
  computed: { total() { return this.$i18n.locale.length } },
  inject: { service: "service" },
  data() { return { ready: true } },
  setup: () => ({ selected: prefix }),
});"#;
        let analysis = analyze_component_source(source);

        assert!(analysis.valid);
        assert_eq!(analysis.component_calls.len(), 1);
        let call = &analysis.component_calls[0];
        assert_eq!(&source[call.callee_start..call.callee_end], "$component");
        assert_eq!(&source[call.open_paren_end - 1..call.open_paren_end], "(");
        assert_eq!(
            analysis
                .public_names
                .iter()
                .map(|name| (name.origin.as_str(), name.exposed_name.as_str()))
                .collect::<Vec<_>>(),
            [
                ("props", "displayName"),
                ("props", "count"),
                ("methods", "save"),
                ("computed", "total"),
                ("inject", "service"),
                ("data", "ready"),
                ("setup", "selected"),
            ]
        );
        assert_eq!(
            analysis
                .sections
                .iter()
                .find(|section| section.name == "methods")
                .map(|section| (section.state.as_str(), section.unknown_reason.as_deref())),
            Some(("unknown", Some("object-spread")))
        );
        assert_eq!(
            analysis
                .member_references
                .iter()
                .map(|reference| (reference.receiver.as_str(), reference.name.as_str()))
                .collect::<Vec<_>>(),
            [("this", "$i18n")]
        );
    }

    #[test]
    fn later_top_level_spread_invalidates_sections_until_explicitly_restored() {
        let analysis = analyze_component_source(
            "$component({ props: { first: Number }, ...other, props: { final: Number } })",
        );
        let props = analysis
            .sections
            .iter()
            .find(|section| section.name == "props")
            .unwrap();
        assert_eq!(props.state, "complete");
        assert_eq!(
            analysis
                .public_names
                .iter()
                .filter(|name| name.origin == "props")
                .map(|name| name.authored_name.as_str())
                .collect::<Vec<_>>(),
            ["final"]
        );
    }

    #[test]
    fn computed_top_level_key_invalidates_every_earlier_section() {
        let analysis = analyze_component_source(
            "$component({ props: { first: Number }, methods: { save() {} }, [section]: replacement })",
        );
        assert!(analysis.public_names.is_empty());
        assert!(analysis.sections.iter().all(|section| {
            section.state == "unknown"
                && section.unknown_reason.as_deref() == Some("computed-top-level-key")
        }));
    }

    #[test]
    fn prop_descriptor_dynamic_members_keep_name_but_invalidate_details() {
        for source in [
            "$component({ props: { value: { type: String, ...details } } })",
            "$component({ props: { value: { type: String, [key]: option } } })",
        ] {
            let analysis = analyze_component_source(source);
            let value = analysis
                .public_names
                .iter()
                .find(|name| name.authored_name == "value")
                .unwrap();
            assert_eq!(
                (
                    value.required,
                    value.has_default,
                    value.type_source.as_deref()
                ),
                (None, None, None)
            );
        }
    }

    #[test]
    fn vue_prop_camelization_preserves_repeated_hyphen() {
        let analysis = analyze_component_source(
            "$component({ props: ['foo--bar', 'foo-_bar', 'plain_name'] })",
        );
        assert_eq!(
            analysis
                .public_names
                .iter()
                .map(|name| name.exposed_name.as_str())
                .collect::<Vec<_>>(),
            ["foo-Bar", "foo_bar", "plain_name"]
        );
    }

    #[test]
    fn indirect_options_keep_every_namespace_unknown() {
        let analysis = analyze_component_source("$component(options)");

        assert!(analysis.public_names.is_empty());
        assert!(analysis.sections.iter().all(|section| {
            section.state == "unknown"
                && section.unknown_reason.as_deref() == Some("indirect-options")
        }));
    }

    #[test]
    fn duplicate_sections_keep_only_the_effective_names_and_member_references() {
        let analysis = analyze_component_source(
            "$component({ methods: { old() { return this.oldValue } }, methods: { current() { return this.currentValue } } })",
        );

        assert_eq!(
            analysis
                .public_names
                .iter()
                .map(|name| name.authored_name.as_str())
                .collect::<Vec<_>>(),
            ["current"]
        );
        assert_eq!(
            analysis
                .member_references
                .iter()
                .map(|reference| reference.name.as_str())
                .collect::<Vec<_>>(),
            ["currentValue"]
        );
    }

    #[test]
    fn this_is_authenticated_only_in_vue_bound_options_functions() {
        let analysis = analyze_component_source(
            "$component({ setup() { return { value: this.setupValue } }, onServerRender() { return this.serverValue }, computed: { doubled: { get() { return this.getValue }, set(value) { this.setValue = value } } } })",
        );

        assert_eq!(
            analysis
                .member_references
                .iter()
                .map(|reference| reference.name.as_str())
                .collect::<Vec<_>>(),
            ["getValue", "setValue"]
        );
    }

    #[test]
    fn only_on_server_render_authenticates_context_aliases() {
        let analysis = analyze_component_source(
            "$component({ onServerRender({ component: direct }) { direct.x } }); $component({ onServerRender({ component: current }) { current.z } })",
        );
        assert_eq!(
            analysis
                .bindings
                .iter()
                .map(|binding| binding.local_name.as_str())
                .collect::<Vec<_>>(),
            ["direct", "current"]
        );
    }

    #[test]
    fn server_callback_component_alias_members_are_scope_authenticated() {
        let analysis = analyze_component_source(
            "$component({ onServerRender({ component: instance, revision }) { instance.$i18n.resolve(revision); { const instance = other; instance.$i18n; } } })",
        );

        assert_eq!(
            analysis
                .bindings
                .iter()
                .map(|binding| (binding.name.as_str(), binding.local_name.as_str()))
                .collect::<Vec<_>>(),
            [("component", "instance"), ("revision", "revision")]
        );
        assert_eq!(
            analysis
                .member_references
                .iter()
                .map(|reference| (reference.receiver.as_str(), reference.name.as_str()))
                .collect::<Vec<_>>(),
            [("component", "$i18n")]
        );
    }

    #[test]
    fn options_this_and_helper_selection_follow_javascript_scope() {
        let source = r#"
const $component = value => value;
$component({ methods: { fake() { return this.$i18n } } });
if (enabled) globalThis.$component({ methods: { property() { return this.$i18n } } });
if (enabled) realComponent({});
"#;
        let shadowed = analyze_component_source(source);
        assert!(shadowed.component_calls.is_empty());
        assert!(shadowed.member_references.is_empty());

        let source = r#"if (enabled) $component({
  props: { "naïve-name": { type: String } },
  data: () => ({ lexical: this.$i18n }),
  methods: {
    regular() { (() => this.$i18n)(); function nested() { return this.$i18n } },
  },
});"#;
        let analysis = analyze_component_source(source);
        assert_eq!(analysis.component_calls.len(), 1);
        assert_eq!(
            analysis
                .public_names
                .iter()
                .find(|name| name.origin == "props")
                .map(|name| name.exposed_name.as_str()),
            Some("naïveName")
        );
        assert_eq!(
            analysis
                .member_references
                .iter()
                .map(|reference| reference.name.as_str())
                .collect::<Vec<_>>(),
            ["$i18n"]
        );
    }
}
