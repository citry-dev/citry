//! Citry-owned facade over the pinned native Vue template compiler.

use std::collections::{HashMap, HashSet};

use oxc_allocator::Allocator as OxcAllocator;
use oxc_ast::ast::{Argument, Expression, Statement};
use oxc_parser::Parser;
use oxc_span::SourceType;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use vize_atelier_core::{
    ElementNode, ExpressionNode, PropNode, TemplateChildNode,
    options::{CodegenOptions, CustomElementMatcher, ParserOptions, TemplateSyntaxMode},
    parser::parse_with_options_and_template_syntax,
};
use vize_atelier_dom::{
    Allocator, DomCompilerOptions,
    compile_template_with_custom_elements_and_template_syntax_and_codegen_options,
};

const SCHEMA: &str = "citry-vue-compiler/1";
const TARGET: &str = "ordinary-vnodes/1";

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct CompileRequest {
    pub template: String,
    #[serde(default)]
    pub local_calls: Vec<LocalCall>,
    #[serde(default)]
    pub local_call_runs: Vec<LocalCallRun>,
    #[serde(default)]
    pub element_bindings: Vec<ElementBinding>,
    #[serde(default)]
    pub dynamic_elements: Vec<DynamicElement>,
}

#[derive(Debug, Clone, Deserialize, Serialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct DynamicElement {
    pub alias: String,
    pub tag: String,
    pub source_start: u32,
    pub source_end: u32,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct LocalCallRun {
    pub run_id: String,
    pub type_key: String,
    pub component_tag: String,
    pub source_start: u32,
    pub source_end: u32,
    pub loop_source_start: u32,
    pub loop_source_end: u32,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct LocalCall {
    pub local_id: String,
    pub type_key: String,
    pub component_tag: String,
    pub source_start: u32,
    pub source_end: u32,
    #[serde(default)]
    pub bindings: Vec<ComponentCallBinding>,
}

#[derive(Debug, Clone, Deserialize, Serialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ComponentCallBinding {
    pub kind: String,
    pub name: String,
    pub value: String,
    pub source_start: u32,
    pub source_end: u32,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ElementBinding {
    pub source_start: u32,
    pub source_end: u32,
    pub attrs_binding_key: Option<String>,
    pub key_binding_key: Option<String>,
    #[serde(default)]
    pub runtime_events_binding_key: Option<String>,
    #[serde(default)]
    pub browser_binding_keys: Vec<String>,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CompileArtifact {
    pub schema: &'static str,
    pub compiler: CompilerIdentity,
    pub target: &'static str,
    pub options: CompilerOptions,
    pub source_sha256: String,
    pub transformed_source_sha256: String,
    pub code_sha256: String,
    pub transformed_template: String,
    pub preamble: String,
    pub code: String,
    pub helpers: Vec<String>,
    pub diagnostics: Vec<Diagnostic>,
    pub local_call_runs: Vec<ValidatedLocalCallRun>,
    pub elements: Vec<ElementMetadata>,
    pub dynamic_elements: Vec<DynamicElement>,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CompilerIdentity {
    pub name: &'static str,
    pub version: &'static str,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CompilerOptions {
    pub prefix_identifiers: bool,
    pub hoist_static: bool,
    pub cache_handlers: bool,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Diagnostic {
    pub stage: &'static str,
    pub code: String,
    pub message: String,
    pub start: Option<u32>,
    pub end: Option<u32>,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ElementMetadata {
    pub site_id: String,
    pub path: Vec<String>,
    pub tag: String,
    pub source_start: u32,
    pub source_end: u32,
    pub lifecycle_signature: String,
    pub replacement_key: Option<String>,
    pub runtime_events_binding_key: Option<String>,
    pub directives: Vec<DirectiveMetadata>,
    pub local_call: Option<ValidatedLocalCall>,
    pub local_descendants: Vec<String>,
    pub local_descendant_runs: Vec<String>,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct DirectiveMetadata {
    pub ordinal: usize,
    pub name: String,
    pub argument: Option<String>,
    pub modifiers: Vec<String>,
    pub source_start: u32,
    pub source_end: u32,
    pub runtime_lifecycle: bool,
    pub runtime_implementation: Option<String>,
    pub static_input_type: Option<String>,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ValidatedLocalCall {
    pub local_id: String,
    pub type_key: String,
    pub id_expression: String,
    pub key_expression: String,
    pub bindings: Vec<ComponentCallBinding>,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ValidatedLocalCallRun {
    pub run_id: String,
    pub type_key: String,
    pub component_tag: String,
    pub source_start: u32,
    pub source_end: u32,
    pub loop_source_start: u32,
    pub loop_source_end: u32,
    pub collection_expression: String,
    pub id_expression: String,
    pub key_expression: String,
}

#[derive(Debug)]
struct Edit {
    start: usize,
    end: usize,
    replacement: String,
}

pub fn compile(request: CompileRequest) -> CompileArtifact {
    let allocator = Allocator::new();
    let (root, parse_errors) = parse_with_options_and_template_syntax(
        &allocator,
        &request.template,
        ParserOptions::default(),
        TemplateSyntaxMode::Standard,
    );
    let mut diagnostics = parse_errors
        .into_iter()
        .map(|error| Diagnostic {
            stage: "parse",
            code: format!("{:?}", error.code),
            message: error.message.to_string(),
            start: error.loc.as_ref().map(|loc| loc.span.start),
            end: error.loc.as_ref().map(|loc| loc.span.end),
        })
        .collect::<Vec<_>>();
    let mut dynamic_spans = HashSet::new();
    let mut dynamic_by_start = HashMap::new();
    for item in &request.dynamic_elements {
        let exact = source_span(&request.template, item.source_start, item.source_end)
            .is_some_and(|source| source.starts_with(&format!("<{}", item.alias)));
        if !item.alias.starts_with("citry-dynamic-")
            || !safe_tag(&item.alias)
            || !safe_html_tag(&item.tag)
            || matches!(
                item.tag.to_ascii_lowercase().as_str(),
                "script" | "style" | "template"
            )
            || !dynamic_spans.insert((item.source_start, item.source_end))
            || !exact
        {
            diagnostics.push(diag(
                "metadata",
                "DYNAMIC_ELEMENT_MISMATCH",
                "dynamic element declaration does not match generated source",
                item.source_start,
                item.source_end,
            ));
        } else if dynamic_by_start.insert(item.source_start, item).is_some() {
            diagnostics.push(diag(
                "metadata",
                "DYNAMIC_ELEMENT_MISMATCH",
                "multiple dynamic element declarations claim one generated source site",
                item.source_start,
                item.source_end,
            ));
        }
    }
    let mut elements = Vec::new();
    let mut edits = Vec::new();
    let mut calls_by_span: HashMap<(u32, u32), Vec<&LocalCall>> = HashMap::new();
    for call in &request.local_calls {
        calls_by_span
            .entry((call.source_start, call.source_end))
            .or_default()
            .push(call);
    }
    let mut runs_by_loop_span: HashMap<(u32, u32), Vec<&LocalCallRun>> = HashMap::new();
    let mut runs_by_child_span: HashMap<(u32, u32), Vec<&LocalCallRun>> = HashMap::new();
    for run in &request.local_call_runs {
        runs_by_loop_span
            .entry((run.loop_source_start, run.loop_source_end))
            .or_default()
            .push(run);
        runs_by_child_span
            .entry((run.source_start, run.source_end))
            .or_default()
            .push(run);
    }
    let mut bindings_by_span: HashMap<(u32, u32), Vec<&ElementBinding>> = HashMap::new();
    for binding in &request.element_bindings {
        bindings_by_span
            .entry((binding.source_start, binding.source_end))
            .or_default()
            .push(binding);
    }
    let mut walk_state = WalkState {
        source: &request.template,
        calls_by_span: &calls_by_span,
        runs_by_loop_span: &runs_by_loop_span,
        runs_by_child_span: &runs_by_child_span,
        bindings_by_span: &bindings_by_span,
        dynamic_by_start: &dynamic_by_start,
        matched_dynamic_aliases: HashSet::new(),
        validated_runs: Vec::new(),
        run_paths: Vec::new(),
        output: &mut elements,
        edits: &mut edits,
        diagnostics: &mut diagnostics,
    };
    walk(&root.children, &[], false, &mut walk_state);
    for item in &request.dynamic_elements {
        if !walk_state.matched_dynamic_aliases.contains(&item.alias) {
            walk_state.diagnostics.push(diag(
                "metadata",
                "DYNAMIC_ELEMENT_MISMATCH",
                "dynamic element declaration does not match one parsed generated element",
                item.source_start,
                item.source_end,
            ));
        }
    }
    let validated_runs = std::mem::take(&mut walk_state.validated_runs);
    let run_paths = std::mem::take(&mut walk_state.run_paths);
    drop(walk_state);
    let local_paths = elements
        .iter()
        .filter_map(|element| {
            element
                .local_call
                .as_ref()
                .map(|call| (element.path.clone(), call.local_id.clone()))
        })
        .collect::<Vec<_>>();
    for element in &mut elements {
        element.local_descendants = local_paths
            .iter()
            .filter(|(path, _)| path.len() > element.path.len() && path.starts_with(&element.path))
            .map(|(_, id)| id.clone())
            .collect();
        element.local_descendant_runs = run_paths
            .iter()
            .filter(|(path, _)| path.len() > element.path.len() && path.starts_with(&element.path))
            .map(|(_, id)| id.clone())
            .collect();
    }
    let validated_ids = elements
        .iter()
        .filter_map(|element| {
            element
                .local_call
                .as_ref()
                .map(|call| call.local_id.as_str())
        })
        .collect::<Vec<_>>();
    for call in &request.local_calls {
        if validated_ids
            .iter()
            .filter(|id| **id == call.local_id)
            .count()
            != 1
        {
            diagnostics.push(diag(
                "metadata",
                "UNMATCHED_LOCAL_CALL",
                "each declared local call must match exactly one component element",
                call.source_start,
                call.source_end,
            ));
        }
    }
    for run in &request.local_call_runs {
        if validated_runs
            .iter()
            .filter(|item| item.run_id == run.run_id)
            .count()
            != 1
        {
            diagnostics.push(diag(
                "metadata",
                "UNMATCHED_LOCAL_CALL_RUN",
                "each declared local call run must match exactly one loop wrapper and child",
                run.loop_source_start,
                run.loop_source_end,
            ));
        }
    }
    for binding in &request.element_bindings {
        let element_count = elements
            .iter()
            .filter(|element| {
                element.source_start == binding.source_start
                    && element.source_end == binding.source_end
            })
            .count();
        let declaration_count = request
            .element_bindings
            .iter()
            .filter(|candidate| {
                candidate.source_start == binding.source_start
                    && candidate.source_end == binding.source_end
            })
            .count();
        if element_count != 1 || declaration_count != 1 {
            diagnostics.push(diag(
                "metadata",
                "UNMATCHED_ELEMENT_BINDING",
                "each element binding must claim exactly one element and span",
                binding.source_start,
                binding.source_end,
            ));
        }
    }
    edits.sort_by_key(|edit| edit.start);
    for pair in edits.windows(2) {
        if pair[0].end > pair[1].start {
            diagnostics.push(diag(
                "metadata",
                "OVERLAPPING_SOURCE_EDITS",
                "generated source edits overlap",
                pair[1].start as u32,
                pair[0].end as u32,
            ));
        }
    }
    let applied_edits = diagnostics.is_empty();
    let transformed_template = if applied_edits {
        apply_edits(&request.template, &edits)
    } else {
        request.template.clone()
    };
    let compiler_allocator = Allocator::new();
    let matcher = CustomElementMatcher::from_patterns(
        request
            .dynamic_elements
            .iter()
            .map(|item| item.alias.clone().into())
            .collect(),
    );
    let (_, compile_errors, result) =
        compile_template_with_custom_elements_and_template_syntax_and_codegen_options(
            &compiler_allocator,
            &transformed_template,
            DomCompilerOptions {
                prefix_identifiers: true,
                hoist_static: false,
                cache_handlers: false,
                ..DomCompilerOptions::default()
            },
            TemplateSyntaxMode::Standard,
            matcher,
            CodegenOptions::default(),
        );
    diagnostics.extend(compile_errors.into_iter().map(|error| Diagnostic {
        stage: "compile",
        code: format!("{:?}", error.code),
        message: error.message.to_string(),
        start: error.loc.as_ref().map(|loc| {
            map_transformed_offset(loc.span.start, if applied_edits { &edits } else { &[] })
        }),
        end: error.loc.as_ref().map(|loc| {
            map_transformed_offset(loc.span.end, if applied_edits { &edits } else { &[] })
        }),
    }));
    let mut preamble = result.preamble.to_string();
    let mut code = result.code.to_string();
    if !normalize_model_helpers(&mut preamble, &mut code, &elements) {
        diagnostics.push(Diagnostic {
            stage: "audit",
            code: "MODEL_HELPER_MISMATCH".to_owned(),
            message: "generated v-model helper calls do not match parsed runtime directives"
                .to_owned(),
            start: None,
            end: None,
        });
    }
    let helpers = emitted_helpers(&preamble);
    let allowed = [
        "Fragment",
        "createBlock",
        "createCommentVNode",
        "createElementBlock",
        "createElementVNode",
        "createVNode",
        "createTextVNode",
        "guardReactiveProps",
        "mergeProps",
        "normalizeClass",
        "normalizeProps",
        "normalizeStyle",
        "openBlock",
        "renderList",
        "renderSlot",
        "resolveComponent",
        "resolveDynamicComponent",
        "resolveDirective",
        "toDisplayString",
        "vModelCheckbox",
        "vModelDynamic",
        "vModelRadio",
        "vModelSelect",
        "vModelText",
        "vShow",
        "withCtx",
        "withDirectives",
        "withKeys",
        "withModifiers",
    ];
    for helper in &helpers {
        if !allowed.contains(&helper.as_str()) {
            diagnostics.push(Diagnostic {
                stage: "audit",
                code: "UNSUPPORTED_HELPER".to_owned(),
                message: format!("unsupported Vue helper {helper}"),
                start: None,
                end: None,
            });
        }
    }
    for forbidden in [
        "_cache[",
        "createStaticVNode",
        "setBlockTracking",
        "withMemo",
    ] {
        if preamble.contains(forbidden) || code.contains(forbidden) {
            diagnostics.push(Diagnostic {
                stage: "audit",
                code: "OPTIMIZED_STATEFUL_OUTPUT".to_owned(),
                message: format!("compiler emitted forbidden construct {forbidden}"),
                start: None,
                end: None,
            });
        }
    }
    CompileArtifact {
        schema: SCHEMA,
        compiler: CompilerIdentity {
            name: "vize_atelier_dom",
            version: "0.420.0+citry.1",
        },
        target: TARGET,
        options: CompilerOptions {
            prefix_identifiers: true,
            hoist_static: false,
            cache_handlers: false,
        },
        source_sha256: hash(&request.template),
        transformed_source_sha256: hash(&transformed_template),
        code_sha256: hash(&(preamble.clone() + &code)),
        transformed_template,
        preamble,
        code,
        helpers,
        diagnostics,
        local_call_runs: validated_runs,
        elements,
        dynamic_elements: request.dynamic_elements,
    }
}

struct WalkState<'a> {
    source: &'a str,
    calls_by_span: &'a HashMap<(u32, u32), Vec<&'a LocalCall>>,
    runs_by_loop_span: &'a HashMap<(u32, u32), Vec<&'a LocalCallRun>>,
    runs_by_child_span: &'a HashMap<(u32, u32), Vec<&'a LocalCallRun>>,
    bindings_by_span: &'a HashMap<(u32, u32), Vec<&'a ElementBinding>>,
    dynamic_by_start: &'a HashMap<u32, &'a DynamicElement>,
    matched_dynamic_aliases: HashSet<String>,
    validated_runs: Vec<ValidatedLocalCallRun>,
    run_paths: Vec<(Vec<String>, String)>,
    output: &'a mut Vec<ElementMetadata>,
    edits: &'a mut Vec<Edit>,
    diagnostics: &'a mut Vec<Diagnostic>,
}

fn directive_runtime_identity(
    element: &ElementNode<'_>,
    directive: &str,
) -> (Option<String>, Option<String>) {
    if directive == "show" {
        return (Some("vShow".to_owned()), None);
    }
    if directive == "c-tr" {
        return (Some("resolveDirective:c-tr".to_owned()), None);
    }
    if directive == "citry-control" {
        return (Some("resolveDirective:citry-control".to_owned()), None);
    }
    if directive == "citry-event-timing" {
        return (Some("resolveDirective:citry-event-timing".to_owned()), None);
    }
    if directive == "citry-runtime-events" {
        return (
            Some("resolveDirective:citry-runtime-events".to_owned()),
            None,
        );
    }
    if directive != "model" {
        return (None, None);
    }
    if element.tag == "select" {
        return (Some("vModelSelect".to_owned()), None);
    }
    if element.tag != "input" {
        return (Some("vModelText".to_owned()), None);
    }
    let dynamic_type = element.props.iter().any(|prop| {
        matches!(prop, PropNode::Directive(value)
            if value.name == "bind"
                && (value.arg.is_none()
                    || matches!(value.arg.as_ref(), Some(ExpressionNode::Simple(arg)) if arg.content == "type")))
    });
    if dynamic_type {
        return (Some("vModelDynamic".to_owned()), None);
    }
    let static_type = element.props.iter().find_map(|prop| match prop {
        PropNode::Attribute(value) if value.name == "type" => value
            .value
            .as_ref()
            .map(|item| item.content.to_ascii_lowercase()),
        _ => None,
    });
    let implementation = match static_type.as_deref() {
        Some("checkbox") => "vModelCheckbox",
        Some("radio") => "vModelRadio",
        _ => "vModelText",
    };
    (Some(implementation.to_owned()), static_type)
}

fn normalize_model_helpers(
    preamble: &mut String,
    code: &mut String,
    elements: &[ElementMetadata],
) -> bool {
    const MODEL_HELPERS: [&str; 5] = [
        "vModelText",
        "vModelCheckbox",
        "vModelRadio",
        "vModelSelect",
        "vModelDynamic",
    ];
    let expected = elements
        .iter()
        .flat_map(|element| &element.directives)
        .filter_map(|directive| directive.runtime_implementation.as_deref())
        .filter(|implementation| MODEL_HELPERS.contains(implementation))
        .collect::<Vec<_>>();
    let mut cursor = 0;
    for implementation in expected {
        let Some((start, current)) = MODEL_HELPERS
            .iter()
            .filter_map(|helper| {
                code[cursor..]
                    .find(&format!("_{helper},"))
                    .map(|offset| (cursor + offset + 1, *helper))
            })
            .min_by_key(|(start, _)| *start)
        else {
            return false;
        };
        if current != implementation {
            code.replace_range(start..start + current.len(), implementation);
        }
        cursor = start + implementation.len();
        let declaration = format!("{implementation}: _{implementation}");
        if !preamble.contains(&declaration) {
            let Some(open) = preamble.find("const { ") else {
                return false;
            };
            preamble.insert_str(open + "const { ".len(), &format!("{declaration}, "));
        }
    }
    true
}

fn walk(
    children: &[TemplateChildNode<'_>],
    parent: &[String],
    inside_v_for: bool,
    state: &mut WalkState<'_>,
) {
    let mut ordinal = 0;
    for child in children {
        let TemplateChildNode::Element(element) = child else {
            continue;
        };
        let static_key = element.props.iter().find_map(|prop| match prop {
            PropNode::Attribute(item) if item.name == "key" => {
                item.value.as_ref().map(|value| value.content.to_owned())
            }
            _ => None,
        });
        let mut path = parent.to_vec();
        path.push(match &static_key {
            Some(key) => format!("k:{}:{}", hex(key.as_bytes()), hex(element.tag.as_bytes())),
            None => format!("i:{ordinal}:{}", hex(element.tag.as_bytes())),
        });
        ordinal += 1;
        if element.tag.starts_with("citry-dynamic-") {
            let declared = state.dynamic_by_start.get(&element.loc.span.start).copied();
            // `>` is valid inside a quoted Vue directive expression (for
            // example, the `>` in an arrow function).  The parser already
            // recorded the exact opening-tag span, so use that instead of
            // searching the source text for the first greater-than sign.
            let opening_end = Some(element.loc.span.end);
            if let Some(item) = declared
                .filter(|item| item.alias == element.tag && opening_end == Some(item.source_end))
            {
                if !state.matched_dynamic_aliases.insert(item.alias.clone()) {
                    state.diagnostics.push(diag(
                        "metadata",
                        "DYNAMIC_ELEMENT_MISMATCH",
                        "one dynamic element alias may identify only one parsed generated element",
                        item.source_start,
                        item.source_end,
                    ));
                }
            } else {
                state.diagnostics.push(diag(
                    "metadata",
                    "DYNAMIC_ELEMENT_MISMATCH",
                    "reserved dynamic element source has no exact declaration",
                    element.loc.span.start,
                    opening_end.unwrap_or(element.loc.span.end),
                ));
            }
        }
        let site_id = format!(
            "citryDirective{}",
            hex(&Sha256::digest(path.join("/").as_bytes()))
        );
        let directives = element
            .props
            .iter()
            .filter_map(|prop| {
                if let PropNode::Directive(d) = prop {
                    Some(d)
                } else {
                    None
                }
            })
            .enumerate()
            .map(|(ordinal, d)| {
                let (runtime_implementation, static_input_type) =
                    directive_runtime_identity(element, d.name);
                DirectiveMetadata {
                    ordinal,
                    name: d.name.to_owned(),
                    argument: expression_text(d.arg.as_ref()),
                    modifiers: d
                        .modifiers
                        .iter()
                        .map(|item| item.content.to_owned())
                        .collect(),
                    source_start: d.loc.span.start,
                    source_end: d.loc.span.end,
                    runtime_lifecycle: runtime_implementation.is_some(),
                    runtime_implementation,
                    static_input_type,
                }
            })
            .collect::<Vec<_>>();
        let element_v_for = directives.iter().any(|directive| directive.name == "for");
        let dynamic_component = element.tag == "component"
            && element.props.iter().any(|prop| {
                matches!(prop, PropNode::Directive(d)
                    if d.name == "bind"
                    && matches!(d.arg.as_ref(), Some(ExpressionNode::Simple(arg)) if arg.content == "is"))
            });
        if dynamic_component
            && state
                .runs_by_child_span
                .get(&(element.loc.span.start, element.loc.span.end))
                .is_none_or(Vec::is_empty)
        {
            state.diagnostics.push(diag(
                "metadata",
                "DYNAMIC_COMPONENT_UNSUPPORTED",
                "dynamic Vue components are only supported for declared local call runs",
                element.loc.span.start,
                element.loc.span.end,
            ));
        }
        let matching_runs = state
            .runs_by_loop_span
            .get(&(element.loc.span.start, element.loc.span.end))
            .map(Vec::as_slice)
            .unwrap_or(&[]);
        if matching_runs.len() > 1 {
            state.diagnostics.push(diag(
                "metadata",
                "DUPLICATE_LOCAL_CALL_RUN",
                "multiple local call runs claim one loop wrapper",
                element.loc.span.start,
                element.loc.span.end,
            ));
        }
        if let Some(run) = (matching_runs.len() == 1)
            .then(|| matching_runs[0])
            .and_then(|run| validate_local_call_run(element, run, inside_v_for, state))
        {
            state.run_paths.push((path.clone(), run.run_id.clone()));
            state.validated_runs.push(run);
        }
        let lifecycle = serde_json::to_string(
            &directives
                .iter()
                .filter(|d| d.runtime_lifecycle)
                .map(|d| {
                    (
                        &d.name,
                        &d.argument,
                        &d.modifiers,
                        &d.runtime_implementation,
                        &d.static_input_type,
                    )
                })
                .collect::<Vec<_>>(),
        )
        .expect("directive metadata serializes");
        let replacement_key = directives.iter().any(|d| d.runtime_lifecycle).then(|| {
            let identity = format!(
                "{site_id}\0{}\0{lifecycle}",
                static_key.as_deref().unwrap_or("")
            );
            format!(
                "citryReplacement{}",
                hex(&Sha256::digest(identity.as_bytes()))
            )
        });
        let matching_binding = state
            .bindings_by_span
            .get(&(element.loc.span.start, element.loc.span.end))
            .map(Vec::as_slice)
            .unwrap_or(&[]);
        if matching_binding.len() > 1 {
            state.diagnostics.push(diag(
                "metadata",
                "DUPLICATE_ELEMENT_BINDING",
                "multiple element bindings claim one element",
                element.loc.span.start,
                element.loc.span.end,
            ));
        }
        if matching_binding.is_empty() && element.props.iter().any(|prop| matches!(prop, PropNode::Directive(d) if (d.name=="bind" && matches!(d.exp.as_ref(),Some(ExpressionNode::Simple(exp)) if exp.content.starts_with("preparedData.citryAttrs") || exp.content.starts_with("preparedData.citryKey"))) || d.name=="citry-runtime-events")) {
            state.diagnostics.push(diag("metadata", "UNDECLARED_ELEMENT_BINDING", "generated element binding has no matching metadata record", element.loc.span.start, element.loc.span.end));
        }
        let binding = matching_binding.first().copied();
        if let Some(binding) = binding {
            validate_element_binding(element, binding, state.diagnostics);
        }
        if let Some(key) = &replacement_key {
            plan_key_edit(
                element,
                state.source,
                key,
                binding.and_then(|item| item.key_binding_key.as_deref()),
                state.edits,
                state.diagnostics,
            );
        }
        if directives
            .iter()
            .any(|directive| directive.runtime_implementation.as_deref() == Some("vModelDynamic"))
        {
            plan_dynamic_model_marker(
                element,
                state.source,
                &site_id,
                state.edits,
                state.diagnostics,
            );
        }
        let matching = state
            .calls_by_span
            .get(&(element.loc.span.start, element.loc.span.end))
            .map(Vec::as_slice)
            .unwrap_or(&[]);
        let local_call = if matching.len() == 1 {
            validate_local_call(element, matching[0], state.source, state.diagnostics)
        } else {
            if matching.len() > 1 {
                state.diagnostics.push(diag(
                    "metadata",
                    "DUPLICATE_LOCAL_CALL",
                    "multiple local calls claim one element",
                    element.loc.span.start,
                    element.loc.span.end,
                ));
            }
            None
        };
        if local_call.is_some() && (inside_v_for || element_v_for) {
            state.diagnostics.push(diag(
                "metadata",
                "CITRY_COMPONENT_IN_V_FOR",
                "v-for cannot create server-prepared Citry components; use c-for",
                element.loc.span.start,
                element.loc.span.end,
            ));
        }
        if local_call.is_some()
            && directives
                .iter()
                .any(|directive| directive.runtime_lifecycle)
        {
            state.diagnostics.push(diag(
                "metadata",
                "COMPONENT_RUNTIME_DIRECTIVE_UNSUPPORTED",
                "runtime directives on Citry component calls are unsupported",
                element.loc.span.start,
                element.loc.span.end,
            ));
        }
        if matching.is_empty()
            && element.props.iter().any(|prop| {
                matches!(prop, PropNode::Directive(d)
                    if d.name == "bind"
                    && matches!(d.arg.as_ref(), Some(ExpressionNode::Simple(arg)) if arg.content == "citry-id")
                    && matches!(d.exp.as_ref(), Some(ExpressionNode::Simple(exp))
                        if exp.content.starts_with("preparedData.calls.")
                            || exp.content.starts_with("preparedData.calls[")
                            || matches!(exp.content, "citryOccurrenceId" | "citryLocalId")))
            })
            && state
                .runs_by_child_span
                .get(&(element.loc.span.start, element.loc.span.end))
                .is_none_or(Vec::is_empty)
        {
            state.diagnostics.push(diag(
                "metadata",
                "UNDECLARED_LOCAL_CALL",
                "generated local call binding has no matching metadata record",
                element.loc.span.start,
                element.loc.span.end,
            ));
        }
        state.output.push(ElementMetadata {
            site_id,
            path: path.clone(),
            tag: element.tag.to_owned(),
            source_start: element.loc.span.start,
            source_end: element.loc.span.end,
            lifecycle_signature: lifecycle,
            replacement_key,
            runtime_events_binding_key: binding
                .and_then(|item| item.runtime_events_binding_key.clone()),
            directives,
            local_call,
            local_descendants: Vec::new(),
            local_descendant_runs: Vec::new(),
        });
        walk(
            &element.children,
            &path,
            inside_v_for || element_v_for,
            state,
        );
    }
}

fn plan_dynamic_model_marker(
    element: &ElementNode<'_>,
    source: &str,
    site_id: &str,
    edits: &mut Vec<Edit>,
    diagnostics: &mut Vec<Diagnostic>,
) {
    const MARKER: &str = "__citryInputModelSite";
    let authored_marker = element.props.iter().find_map(|prop| match prop {
        PropNode::Attribute(attribute) if attribute.name == MARKER => Some(attribute.loc.span),
        PropNode::Directive(directive)
            if directive.name == "bind"
                && matches!(directive.arg.as_ref(), Some(ExpressionNode::Simple(arg)) if arg.content == MARKER) =>
        {
            Some(directive.loc.span)
        }
        _ => None,
    });
    if let Some(span) = authored_marker {
        diagnostics.push(diag(
            "metadata",
            "RESERVED_MODEL_SITE_MARKER",
            "the dynamic input model marker is compiler-owned",
            span.start,
            span.end,
        ));
        return;
    }

    // Appending after every authored prop makes generic spreads unable to
    // replace the authenticated site marker before the VNode wrapper sees it.
    let search_start = element.props.last().map_or(
        element.loc.span.start as usize + 1 + element.tag.len(),
        |prop| prop.loc().span.end as usize,
    );
    let Some(relative_end) = source[search_start..element.loc.span.end as usize].find('>') else {
        diagnostics.push(diag(
            "metadata",
            "TAG_SPAN_MISMATCH",
            "dynamic model element has no opening-tag terminator",
            element.loc.span.start,
            element.loc.span.end,
        ));
        return;
    };
    let mut insertion = search_start + relative_end;
    if source.as_bytes().get(insertion.wrapping_sub(1)) == Some(&b'/') {
        insertion -= 1;
    }
    edits.push(Edit {
        start: insertion,
        end: insertion,
        replacement: format!(r#" :{MARKER}="'{site_id}'""#),
    });
}

fn plan_key_edit(
    element: &vize_atelier_core::ElementNode<'_>,
    source: &str,
    key: &str,
    prepared_key: Option<&str>,
    edits: &mut Vec<Edit>,
    diagnostics: &mut Vec<Diagnostic>,
) {
    for prop in &element.props {
        if let PropNode::Directive(d) = prop
            && d.name == "bind"
            && match d.arg.as_ref() {
                Some(ExpressionNode::Simple(arg)) => !arg.is_static || arg.content == "key",
                Some(ExpressionNode::Compound(_)) => true,
                None => false,
            }
        {
            let expected = prepared_key.map(|name| format!("preparedData.{name}"));
            let authorized = matches!(d.exp.as_ref(), Some(ExpressionNode::Simple(exp)) if expected.as_deref() == Some(exp.content));
            if authorized {
                continue;
            }
            diagnostics.push(diag(
                "metadata",
                "DYNAMIC_KEY_UNSUPPORTED",
                "user-authored dynamic keys are unsupported",
                d.loc.span.start,
                d.loc.span.end,
            ));
            return;
        }
    }
    let static_key = element.props.iter().find_map(|prop| {
        if let PropNode::Attribute(a) = prop
            && a.name == "key"
        {
            Some(a)
        } else {
            None
        }
    });
    let prepared_key_attr = prepared_key.and_then(|name| {
        let expected = format!("preparedData.{name}");
        element.props.iter().find_map(|prop| match prop {
            PropNode::Directive(d)
                if d.name == "bind"
                    && matches!(d.arg.as_ref(), Some(ExpressionNode::Simple(arg)) if arg.content == "key")
                    && matches!(d.exp.as_ref(), Some(ExpressionNode::Simple(exp)) if exp.content == expected) => Some(d),
            _ => None,
        })
    });
    // The key is a compiler-owned ASCII digest; no user value enters JavaScript source.
    let attribute = prepared_key.map_or_else(
        || format!(r#"key="{key}""#),
        |name| format!(r#":key="JSON.stringify(['{key}', preparedData.{name}])""#),
    );
    let replacement = if static_key.is_some() || prepared_key.is_some() {
        attribute
    } else {
        format!(" {attribute}")
    };
    if let Some((start, end)) = static_key
        .map(|attr| (attr.loc.span.start, attr.loc.span.end))
        .or_else(|| prepared_key_attr.map(|attr| (attr.loc.span.start, attr.loc.span.end)))
    {
        edits.push(Edit {
            start: start as usize,
            end: end as usize,
            replacement,
        });
        return;
    }
    let start = element.loc.span.start as usize + 1 + element.tag.len();
    if source
        .as_bytes()
        .get(element.loc.span.start as usize + 1..start)
        != Some(element.tag.as_bytes())
    {
        diagnostics.push(diag(
            "metadata",
            "TAG_SPAN_MISMATCH",
            "AST tag span does not match source bytes",
            element.loc.span.start,
            element.loc.span.end,
        ));
        return;
    }
    edits.push(Edit {
        start,
        end: start,
        replacement,
    });
}

fn validate_element_binding(
    element: &vize_atelier_core::ElementNode<'_>,
    binding: &ElementBinding,
    diagnostics: &mut Vec<Diagnostic>,
) {
    let runtime_directives = element
        .props
        .iter()
        .filter(|prop| {
            matches!(
                prop,
                PropNode::Directive(d) if d.name == "citry-runtime-events"
            )
        })
        .count();
    if binding.runtime_events_binding_key.is_none() && runtime_directives != 0 {
        diagnostics.push(diag(
            "metadata",
            "UNDECLARED_RUNTIME_EVENTS_BINDING",
            "runtime events directive has no matching binding key",
            binding.source_start,
            binding.source_end,
        ));
    }
    for key in [
        binding.attrs_binding_key.as_deref(),
        binding.key_binding_key.as_deref(),
    ]
    .into_iter()
    .flatten()
    {
        if !safe(key) || !(key.starts_with("citryAttrs") || key.starts_with("citryKey")) {
            diagnostics.push(diag(
                "metadata",
                "UNSAFE_ELEMENT_BINDING",
                "element binding key is not generated-safe",
                binding.source_start,
                binding.source_end,
            ));
            return;
        }
    }
    for key in &binding.browser_binding_keys {
        if !safe(key) || !key.starts_with("citryBinding") {
            diagnostics.push(diag(
                "metadata",
                "UNSAFE_BROWSER_BINDING",
                "browser binding key is not generated-safe",
                binding.source_start,
                binding.source_end,
            ));
            return;
        }
        let matched = element.props.iter().any(|prop| matches!(prop, PropNode::Directive(d) if matches!(d.exp.as_ref(), Some(ExpressionNode::Simple(value)) if browser_binding_expression(value.content, key))));
        if !matched {
            diagnostics.push(diag(
                "metadata",
                "BROWSER_BINDING_MISMATCH",
                "browser binding does not match preparedData metadata",
                binding.source_start,
                binding.source_end,
            ));
        }
    }
    let has = |arg: Option<&str>, expected: &str| {
        element.props.iter().any(|prop| matches!(prop, PropNode::Directive(d) if d.name=="bind" && match (arg,d.arg.as_ref()) { (None,None)=>true,(Some(want),Some(ExpressionNode::Simple(value)))=>value.content==want,_=>false } && matches!(d.exp.as_ref(),Some(ExpressionNode::Simple(value)) if value.content==expected)))
    };
    if let Some(key) = &binding.attrs_binding_key
        && !has(None, &format!("preparedData.{key}"))
    {
        diagnostics.push(diag(
            "metadata",
            "ELEMENT_ATTRS_BINDING_MISMATCH",
            "element attrs binding does not match preparedData metadata",
            binding.source_start,
            binding.source_end,
        ));
    }
    if let Some(key) = &binding.key_binding_key
        && !has(Some("key"), &format!("preparedData.{key}"))
    {
        diagnostics.push(diag(
            "metadata",
            "ELEMENT_KEY_BINDING_MISMATCH",
            "element key binding does not match preparedData metadata",
            binding.source_start,
            binding.source_end,
        ));
    }
    if let Some(key) = &binding.runtime_events_binding_key {
        if !key
            .strip_prefix("citryRuntimeEvents")
            .is_some_and(|suffix| {
                !suffix.is_empty() && suffix.bytes().all(|byte| byte.is_ascii_alphanumeric())
            })
        {
            diagnostics.push(diag(
                "metadata",
                "UNSAFE_RUNTIME_EVENTS_BINDING",
                "runtime events binding key is not generated-safe",
                binding.source_start,
                binding.source_end,
            ));
            return;
        }
        let expected = format!("$citryEvents.runtimeEvents(preparedData.{key})");
        let matches = element.props.iter().filter(|prop| matches!(prop,
            PropNode::Directive(d)
                if d.name == "citry-runtime-events"
                && d.arg.is_none()
                && d.modifiers.is_empty()
                && matches!(d.exp.as_ref(), Some(ExpressionNode::Simple(value)) if value.content == expected)
        )).count();
        if matches != 1 || runtime_directives != 1 {
            diagnostics.push(diag(
                "metadata",
                "RUNTIME_EVENTS_BINDING_MISMATCH",
                "runtime events directive does not match preparedData metadata",
                binding.source_start,
                binding.source_end,
            ));
        }
    }
}

fn browser_binding_expression(content: &str, key: &str) -> bool {
    let allocator = OxcAllocator::default();
    let parsed = Parser::new(&allocator, content, SourceType::default()).parse();
    if !parsed.diagnostics.is_empty() || parsed.program.body.len() != 1 {
        return false;
    }
    let Statement::ExpressionStatement(statement) = &parsed.program.body[0] else {
        return false;
    };
    let Expression::CallExpression(call) = &statement.expression else {
        return false;
    };
    let Expression::Identifier(helper) = &call.callee else {
        return false;
    };
    if !helper.name.starts_with('$') || helper.name.len() < 2 || call.optional {
        return false;
    }
    let Some(Argument::StaticMemberExpression(first)) = call.arguments.first() else {
        return false;
    };
    if first.optional || first.property.name != key {
        return false;
    }
    let Expression::Identifier(object) = &first.object else {
        return false;
    };
    if object.name != "preparedData" {
        return false;
    }
    match call.arguments.as_slice() {
        [_] => true,
        [_, Argument::ArrowFunctionExpression(thunk)] => {
            !thunk.r#async && thunk.params.items.is_empty() && thunk.params.rest.is_none()
        }
        _ => false,
    }
}

fn validate_local_call_run(
    element: &vize_atelier_core::ElementNode<'_>,
    run: &LocalCallRun,
    inside_v_for: bool,
    state: &mut WalkState<'_>,
) -> Option<ValidatedLocalCallRun> {
    if !safe(&run.run_id) || !safe(&run.type_key) || !safe_tag(&run.component_tag) {
        state.diagnostics.push(diag(
            "metadata",
            "UNSAFE_LOCAL_CALL_RUN",
            "runId and typeKey must be generated-safe identifiers and componentTag must be a safe tag",
            run.loop_source_start,
            run.loop_source_end,
        ));
        return None;
    }
    if inside_v_for {
        state.diagnostics.push(diag(
            "metadata",
            "CITRY_COMPONENT_IN_V_FOR",
            "a generated local call run cannot be nested in an authored v-for",
            run.loop_source_start,
            run.loop_source_end,
        ));
        return None;
    }
    let child_claims = state
        .runs_by_child_span
        .get(&(run.source_start, run.source_end))
        .map(Vec::as_slice)
        .unwrap_or(&[]);
    if child_claims.len() != 1 || !std::ptr::eq(child_claims[0], run) {
        state.diagnostics.push(diag(
            "metadata",
            "DUPLICATE_LOCAL_CALL_RUN_CHILD",
            "a local call run child span must be claimed by exactly one declaration",
            run.source_start,
            run.source_end,
        ));
        return None;
    }
    let collection_expression = format!("preparedData.callRuns.{}", run.run_id);
    let id_expression = "citryOccurrenceId".to_owned();
    let key_expression = "citryOccurrenceId".to_owned();
    let run_source = format!(
        "<component v-for=\"citryOccurrenceId in {collection_expression}\" :is=\"'{}'\" :citry-id=\"{id_expression}\" :key=\"{key_expression}\">",
        run.component_tag
    );
    if run.source_start != run.loop_source_start
        || run.source_end != run.loop_source_end
        || element.tag != "component"
        || element.loc.span.start != run.source_start
        || element.loc.span.end != run.source_end
        || source_span(state.source, run.source_start, run.source_end) != Some(run_source.as_str())
        || element.props.len() != 4
        || !element.children.is_empty()
    {
        state.diagnostics.push(diag(
            "metadata",
            "LOCAL_CALL_RUN_CHILD_MISMATCH",
            "local call run does not match its generated empty component loop and shared span",
            run.source_start,
            run.source_end,
        ));
        return None;
    }
    Some(ValidatedLocalCallRun {
        run_id: run.run_id.clone(),
        type_key: run.type_key.clone(),
        component_tag: run.component_tag.clone(),
        source_start: run.source_start,
        source_end: run.source_end,
        loop_source_start: run.loop_source_start,
        loop_source_end: run.loop_source_end,
        collection_expression,
        id_expression,
        key_expression,
    })
}

fn source_span(source: &str, start: u32, end: u32) -> Option<&str> {
    source.get(start as usize..end as usize)
}

fn validate_local_call(
    element: &vize_atelier_core::ElementNode<'_>,
    call: &LocalCall,
    source: &str,
    diagnostics: &mut Vec<Diagnostic>,
) -> Option<ValidatedLocalCall> {
    if !safe(&call.local_id)
        || !safe(&call.type_key)
        || !safe_tag(&call.component_tag)
        || element.tag != call.component_tag
    {
        diagnostics.push(diag(
            "metadata",
            "UNSAFE_LOCAL_CALL",
            "localId and typeKey must be generated-safe identifiers",
            call.source_start,
            call.source_end,
        ));
        return None;
    }
    let id = format!("preparedData.calls.{}.id", call.local_id);
    let key = format!("preparedData.calls.{}.key", call.local_id);
    let has = |name: &str, expected: &str| {
        element.props.iter().any(|p| matches!(p,PropNode::Directive(d) if d.name=="bind" && matches!(d.arg.as_ref(),Some(ExpressionNode::Simple(a)) if a.content==name) && matches!(d.exp.as_ref(),Some(ExpressionNode::Simple(e)) if e.content==expected)))
    };
    if !has("citry-id", &id) || !has("key", &key) {
        diagnostics.push(diag(
            "metadata",
            "LOCAL_CALL_BINDING_MISMATCH",
            "local call bindings do not match declared preparedData call",
            call.source_start,
            call.source_end,
        ));
        return None;
    }
    let valid_binding_kinds = [
        "prop",
        "props-object",
        "event",
        "ref-static",
        "ref-expression",
    ];
    let mut claimed_spans = HashSet::new();
    for binding in &call.bindings {
        let within_call = binding.source_start >= call.source_start
            && binding.source_end <= call.source_end
            && binding.source_start < binding.source_end;
        let expected = format!("{}=\"{}\"", binding.name, html_escape_attr(&binding.value));
        let parsed_match = element
            .props
            .iter()
            .filter(|prop| match prop {
                PropNode::Attribute(attr) => {
                    binding.kind == "ref-static"
                        && binding.name == "ref"
                        && attr.name == "ref"
                        && attr
                            .value
                            .as_ref()
                            .is_some_and(|value| value.content == binding.value)
                        && attr.loc.span.start == binding.source_start
                        && attr.loc.span.end == binding.source_end
                }
                PropNode::Directive(directive) => {
                    let argument = directive.arg.as_ref().and_then(|arg| match arg {
                        ExpressionNode::Simple(value) => Some(value.content),
                        ExpressionNode::Compound(_) => None,
                    });
                    let expression = directive.exp.as_ref().and_then(|exp| match exp {
                        ExpressionNode::Simple(value) => Some(value.content),
                        ExpressionNode::Compound(_) => None,
                    });
                    let semantic = match binding.kind.as_str() {
                        "props-object" => directive.name == "bind" && argument.is_none(),
                        "prop" => {
                            directive.name == "bind" && argument.is_some_and(|name| name != "ref")
                        }
                        "event" => directive.name == "on" && argument.is_some(),
                        "ref-expression" => directive.name == "bind" && argument == Some("ref"),
                        _ => false,
                    };
                    semantic
                        && expression == Some(binding.value.as_str())
                        && directive.loc.span.start == binding.source_start
                        && directive.loc.span.end == binding.source_end
                }
            })
            .count()
            == 1;
        if !within_call
            || !valid_binding_kinds.contains(&binding.kind.as_str())
            || !claimed_spans.insert((binding.source_start, binding.source_end))
            || source_span(source, binding.source_start, binding.source_end)
                != Some(expected.as_str())
            || !parsed_match
        {
            diagnostics.push(diag(
                "metadata",
                "LOCAL_CALL_CLIENT_BINDING_MISMATCH",
                "component call binding does not match its declared generated source",
                binding.source_start,
                binding.source_end,
            ));
            return None;
        }
    }
    let private_binding = |prop: &PropNode<'_>, name: &str, expected: &str| {
        matches!(prop, PropNode::Directive(d)
            if d.name == "bind"
            && matches!(d.arg.as_ref(), Some(ExpressionNode::Simple(arg)) if arg.content == name)
            && matches!(d.exp.as_ref(), Some(ExpressionNode::Simple(exp)) if exp.content == expected))
    };
    let exact_shape = element.props.len() == call.bindings.len() + 2
        && element.props.len() >= 2
        && element.props[..element.props.len() - 2].iter().all(|prop| {
            let span = match prop {
                PropNode::Attribute(value) => value.loc.span,
                PropNode::Directive(value) => value.loc.span,
            };
            claimed_spans.contains(&(span.start, span.end))
        })
        && private_binding(&element.props[element.props.len() - 2], "citry-id", &id)
        && private_binding(&element.props[element.props.len() - 1], "key", &key);
    if !exact_shape {
        diagnostics.push(diag(
            "metadata",
            "LOCAL_CALL_CLIENT_BINDING_MISMATCH",
            "component call source must contain exactly the declared authored bindings followed by Citry identity",
            call.source_start,
            call.source_end,
        ));
        return None;
    }
    Some(ValidatedLocalCall {
        local_id: call.local_id.clone(),
        type_key: call.type_key.clone(),
        id_expression: id,
        key_expression: key,
        bindings: call.bindings.clone(),
    })
}

fn html_escape_attr(value: &str) -> String {
    value
        .replace('&', "&amp;")
        .replace('"', "&quot;")
        .replace('\'', "&#x27;")
}

fn apply_edits(source: &str, edits: &[Edit]) -> String {
    let mut s = source.to_owned();
    for e in edits.iter().rev() {
        s.replace_range(e.start..e.end, &e.replacement)
    }
    s
}
fn map_transformed_offset(offset: u32, edits: &[Edit]) -> u32 {
    let offset = offset as i64;
    let mut delta = 0i64;
    for edit in edits {
        let transformed_start = edit.start as i64 + delta;
        let transformed_end = transformed_start + edit.replacement.len() as i64;
        if offset < transformed_start {
            break;
        }
        if offset <= transformed_end {
            return edit.start as u32;
        }
        delta += edit.replacement.len() as i64 - (edit.end - edit.start) as i64;
    }
    (offset - delta).max(0) as u32
}
fn safe(s: &str) -> bool {
    !s.is_empty()
        && s.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'_')
        && !s.as_bytes()[0].is_ascii_digit()
}
fn safe_tag(value: &str) -> bool {
    value.contains('-')
        && value
            .bytes()
            .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit() || byte == b'-')
        && value.as_bytes().first().is_some_and(u8::is_ascii_lowercase)
}
fn safe_html_tag(value: &str) -> bool {
    value
        .as_bytes()
        .first()
        .is_some_and(u8::is_ascii_alphabetic)
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_' | b'.'))
}
fn expression_text(value: Option<&ExpressionNode<'_>>) -> Option<String> {
    match value? {
        ExpressionNode::Simple(item) => Some(item.content.to_owned()),
        ExpressionNode::Compound(item) => Some(format!("{item:?}")),
    }
}
fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}
fn hash(s: &str) -> String {
    hex(&Sha256::digest(s.as_bytes()))
}
fn diag(stage: &'static str, code: &str, message: &str, start: u32, end: u32) -> Diagnostic {
    Diagnostic {
        stage,
        code: code.to_owned(),
        message: message.to_owned(),
        start: Some(start),
        end: Some(end),
    }
}

fn emitted_helpers(preamble: &str) -> Vec<String> {
    let mut helpers = Vec::new();
    for entry in preamble.split(['{', '}', ',', '\n']) {
        if let Some((name, alias)) = entry.split_once(':')
            && alias.trim_start().starts_with('_')
        {
            let name = name.trim();
            if !name.is_empty() {
                helpers.push(name.to_owned());
            }
        }
    }
    helpers.sort();
    helpers.dedup();
    helpers
}

#[cfg(test)]
mod tests {
    use super::*;

    fn call_run_request(template: &str) -> CompileRequest {
        let source_start = template.find("<component").unwrap();
        let source_end = source_start + template[source_start..].find('>').unwrap() + 1;
        CompileRequest {
            template: template.to_owned(),
            local_calls: vec![],
            local_call_runs: vec![LocalCallRun {
                run_id: "citryRun0".to_owned(),
                type_key: "Row".to_owned(),
                component_tag: "citry-row".to_owned(),
                source_start: source_start as u32,
                source_end: source_end as u32,
                loop_source_start: source_start as u32,
                loop_source_end: source_end as u32,
            }],
            element_bindings: vec![],
            dynamic_elements: vec![],
        }
    }

    const CALL_RUN: &str = "<component v-for=\"citryOccurrenceId in preparedData.callRuns.citryRun0\" :is=\"'citry-row'\" :citry-id=\"citryOccurrenceId\" :key=\"citryOccurrenceId\"></component>";

    #[test]
    fn validates_exact_local_call_run_and_reports_it_to_stable_ancestor() {
        let template = format!("<div title=\"ž\" v-show=\"shown\">{CALL_RUN}</div>");
        let artifact = compile(call_run_request(&template));
        assert!(
            artifact.diagnostics.is_empty(),
            "{:?}",
            artifact.diagnostics
        );
        assert_eq!(artifact.local_call_runs.len(), 1);
        let run = &artifact.local_call_runs[0];
        assert_eq!(run.collection_expression, "preparedData.callRuns.citryRun0");
        assert_eq!(run.id_expression, "citryOccurrenceId");
        assert_eq!(run.key_expression, "citryOccurrenceId");
        assert_eq!(artifact.elements[0].local_descendant_runs, ["citryRun0"]);
        assert!(
            artifact
                .helpers
                .contains(&"resolveDynamicComponent".to_owned())
        );
        assert!(!artifact.helpers.contains(&"resolveComponent".to_owned()));
        let render_list = artifact.code.find("_renderList").unwrap();
        let resolution = artifact.code.find("_resolveDynamicComponent").unwrap();
        assert!(resolution > render_list);
        assert!(artifact.code.contains("128 /* KEYED_FRAGMENT */"));
        assert!(!artifact.code.contains("64 /* STABLE_FRAGMENT */"));
    }

    #[test]
    fn rejects_unclaimed_bracket_call_and_authored_loop_ancestry() {
        let unclaimed = compile(CompileRequest {
            template: CALL_RUN.to_owned(),
            local_calls: vec![],
            local_call_runs: vec![],
            element_bindings: vec![],
            dynamic_elements: vec![],
        });
        assert!(
            unclaimed
                .diagnostics
                .iter()
                .any(|item| item.code == "UNDECLARED_LOCAL_CALL")
        );
        let named = compile(CompileRequest {
            template:
                "<citry-row :citry-id=\"citryOccurrenceId\" :key=\"citryOccurrenceId\"></citry-row>"
                    .to_owned(),
            local_calls: vec![],
            local_call_runs: vec![],
            element_bindings: vec![],
            dynamic_elements: vec![],
        });
        assert!(
            named
                .diagnostics
                .iter()
                .any(|item| item.code == "UNDECLARED_LOCAL_CALL")
        );

        let nested = format!("<div v-for=\"item in items\">{CALL_RUN}</div>");
        let artifact = compile(call_run_request(&nested));
        assert!(
            artifact
                .diagnostics
                .iter()
                .any(|item| item.code == "CITRY_COMPONENT_IN_V_FOR")
        );
        assert!(artifact.local_call_runs.is_empty());
    }

    #[test]
    fn rejects_noncanonical_local_call_run_shapes_and_duplicate_claims() {
        for malformed in [
            CALL_RUN.replace("citryOccurrenceId in", "(citryOccurrenceId, index) in"),
            CALL_RUN.replace("citryOccurrenceId", "citryLocalId"),
            CALL_RUN.replace(" v-for=", " data-extra=\"x\" v-for="),
            CALL_RUN.replace(":is=\"'citry-row'\"", ":is=\"rowTag\""),
            CALL_RUN.replace(" :key=\"citryOccurrenceId\"", ""),
            CALL_RUN.replace(
                ":key=\"citryOccurrenceId\"",
                ":key=\"preparedData.calls[citryOccurrenceId].key\"",
            ),
            CALL_RUN.replace(":citry-id=\"citryOccurrenceId\"", ":citry-id=\"wrong\""),
            CALL_RUN.replace(" :key=", " data-extra=\"x\" :key="),
            CALL_RUN.replace("></component>", ">text</component>"),
            CALL_RUN.replace("</component>", "<i v-for=\"x in xs\"></i></component>"),
        ] {
            let artifact = compile(call_run_request(&malformed));
            assert!(!artifact.diagnostics.is_empty(), "accepted {malformed:?}");
            assert!(artifact.local_call_runs.is_empty());
        }

        let mut split_span = call_run_request(CALL_RUN);
        split_span.local_call_runs[0].loop_source_end -= 1;
        let artifact = compile(split_span);
        assert!(
            artifact
                .diagnostics
                .iter()
                .any(|item| item.code == "UNMATCHED_LOCAL_CALL_RUN")
        );
        assert!(artifact.local_call_runs.is_empty());

        let mut duplicate = call_run_request(CALL_RUN);
        let type_key = duplicate.local_call_runs[0].type_key.clone();
        let component_tag = duplicate.local_call_runs[0].component_tag.clone();
        let source_start = duplicate.local_call_runs[0].source_start;
        let source_end = duplicate.local_call_runs[0].source_end;
        let loop_source_start = duplicate.local_call_runs[0].loop_source_start;
        let loop_source_end = duplicate.local_call_runs[0].loop_source_end;
        duplicate.local_call_runs.push(LocalCallRun {
            run_id: "citryRun1".to_owned(),
            type_key,
            component_tag,
            source_start,
            source_end,
            loop_source_start,
            loop_source_end,
        });
        let artifact = compile(duplicate);
        assert!(
            artifact
                .diagnostics
                .iter()
                .any(|item| item.code == "DUPLICATE_LOCAL_CALL_RUN")
        );
        assert!(
            artifact
                .diagnostics
                .iter()
                .any(|item| item.code == "UNMATCHED_LOCAL_CALL_RUN")
        );
    }

    #[test]
    fn does_not_enable_authored_dynamic_components() {
        for template in [
            "<component :is=\"tag\"></component>",
            "<div v-for=\"item in items\"><component :is=\"item.tag\"></component></div>",
        ] {
            let artifact = compile(CompileRequest {
                template: template.to_owned(),
                local_calls: vec![],
                local_call_runs: vec![],
                element_bindings: vec![],
                dynamic_elements: vec![],
            });
            assert!(
                artifact
                    .diagnostics
                    .iter()
                    .any(|item| item.code == "DYNAMIC_COMPONENT_UNSUPPORTED"),
                "accepted {template:?}"
            );
        }
    }

    #[test]
    fn injects_primitive_lifecycle_keys_and_compiles_canonical_directives() {
        let artifact = compile(CompileRequest {
            template: "<section><input v-model.lazy=\"name\"><p key=\"user's\" v-show=\"shown\" @click.prevent=\"toggle\">x</p><button v-citry-event-timing=\"timing\">save</button><textarea v-text=\"note\"></textarea></section>".to_owned(),
            local_calls: vec![],
            local_call_runs: vec![],
            element_bindings: vec![],
        dynamic_elements: vec![],
        });
        assert!(
            artifact.diagnostics.is_empty(),
            "{:?}\n{}\n{}",
            artifact.diagnostics,
            artifact.preamble,
            artifact.code
        );
        assert_eq!(
            artifact
                .elements
                .iter()
                .filter(|item| item.replacement_key.is_some())
                .count(),
            3
        );
        assert_eq!(
            artifact
                .transformed_template
                .matches("key=\"citryReplacement")
                .count(),
            3
        );
        assert!(!artifact.transformed_template.contains("user's"));
        assert!(artifact.helpers.contains(&"vModelText".to_owned()));
        assert!(artifact.helpers.contains(&"vShow".to_owned()));
        assert!(artifact.helpers.contains(&"resolveDirective".to_owned()));
        assert!(artifact.elements.iter().any(|element| {
            element.directives.iter().any(|directive| {
                directive.name == "citry-event-timing"
                    && directive.runtime_lifecycle
                    && directive.runtime_implementation.as_deref()
                        == Some("resolveDirective:citry-event-timing")
            })
        }));
    }

    #[test]
    fn validates_runtime_event_directives_against_their_declared_binding_key() {
        let template = r#"<button v-citry-runtime-events="$citryEvents.runtimeEvents(preparedData.citryRuntimeEventsA)">save</button>"#;
        let source_end = template.find('>').unwrap() + 1;
        let compile_with_key = |runtime_events_binding_key: Option<&str>| {
            compile(CompileRequest {
                template: template.to_owned(),
                local_calls: vec![],
                local_call_runs: vec![],
                element_bindings: vec![ElementBinding {
                    source_start: 0,
                    source_end: source_end as u32,
                    attrs_binding_key: None,
                    key_binding_key: None,
                    runtime_events_binding_key: runtime_events_binding_key.map(str::to_owned),
                    browser_binding_keys: vec![],
                }],
                dynamic_elements: vec![],
            })
        };

        let valid = compile_with_key(Some("citryRuntimeEventsA"));
        assert!(valid.diagnostics.is_empty(), "{:?}", valid.diagnostics);
        assert_eq!(
            valid.elements[0].runtime_events_binding_key.as_deref(),
            Some("citryRuntimeEventsA")
        );
        let directive = valid.elements[0]
            .directives
            .iter()
            .find(|item| item.name == "citry-runtime-events")
            .unwrap();
        assert!(directive.runtime_lifecycle);
        assert_eq!(
            directive.runtime_implementation.as_deref(),
            Some("resolveDirective:citry-runtime-events")
        );

        let missing_key = compile_with_key(None);
        assert!(
            missing_key
                .diagnostics
                .iter()
                .any(|item| { item.code == "UNDECLARED_RUNTIME_EVENTS_BINDING" })
        );
        let mismatched_key = compile_with_key(Some("citryRuntimeEventsB"));
        assert!(
            mismatched_key
                .diagnostics
                .iter()
                .any(|item| { item.code == "RUNTIME_EVENTS_BINDING_MISMATCH" })
        );
        let unsafe_key = compile_with_key(Some("citryRuntimeEvents"));
        assert!(
            unsafe_key
                .diagnostics
                .iter()
                .any(|item| { item.code == "UNSAFE_RUNTIME_EVENTS_BINDING" })
        );

        let missing_declaration = compile(CompileRequest {
            template: template.to_owned(),
            local_calls: vec![],
            local_call_runs: vec![],
            element_bindings: vec![],
            dynamic_elements: vec![],
        });
        assert!(
            missing_declaration
                .diagnostics
                .iter()
                .any(|item| { item.code == "UNDECLARED_ELEMENT_BINDING" })
        );
    }

    #[test]
    fn keeps_supported_directives_on_single_children_of_template_v_for() {
        let template = concat!(
            "<template v-if=\"preparedData.citryIf0 === 0\">",
            "<template v-for=\"preparedData in preparedData.citryLoop0\">",
            "<input v-show=\"preparedData.visible\" ",
            "v-model=\"preparedData.value\" ",
            "v-citry-event-timing.debounce.30ms=\"$citryEvents.dispatch\" ",
            "v-citry-runtime-events=\"$citryEvents.runtimeEvents(preparedData.citryRuntimeEvents0)\" ",
            "v-citry-control=\"$citryEvents.control\" ",
            "v-bind=\"preparedData.citryAttrs0\">",
            "</template></template>"
        );
        let source_start = template.find("<input").unwrap();
        let source_end = source_start + template[source_start..].find('>').unwrap() + 1;
        let artifact = compile(CompileRequest {
            template: template.to_owned(),
            local_calls: vec![],
            local_call_runs: vec![],
            element_bindings: vec![ElementBinding {
                source_start: source_start as u32,
                source_end: source_end as u32,
                attrs_binding_key: Some("citryAttrs0".to_owned()),
                key_binding_key: None,
                runtime_events_binding_key: Some("citryRuntimeEvents0".to_owned()),
                browser_binding_keys: vec![],
            }],
            dynamic_elements: vec![],
        });

        assert!(
            artifact.diagnostics.is_empty(),
            "{:?}\n{}\n{}",
            artifact.diagnostics,
            artifact.preamble,
            artifact.code
        );
        for helper in ["withDirectives", "vShow", "vModelText", "resolveDirective"] {
            assert!(
                artifact.helpers.contains(&helper.to_owned()),
                "missing {helper}"
            );
        }
        assert!(artifact.code.contains("_withDirectives("));
        assert!(artifact.code.contains("(preparedData) => {"));
        let runtime_tuple = "runtimeEvents(preparedData.citryRuntimeEvents0)";
        let with_directives = artifact.code.find("_withDirectives(").unwrap();
        let runtime_expression = artifact.code.find(runtime_tuple).unwrap();
        assert!(
            runtime_expression > with_directives,
            "runtime directive expression must remain in the v-for child's directive tuple: {}",
            artifact.code
        );
        for expression in ["preparedData.visible", "preparedData.value"] {
            assert!(
                artifact.code.contains(expression),
                "missing loop-scoped directive expression {expression}: {}",
                artifact.code
            );
        }

        let javascript = format!("{}\n{}", artifact.preamble, artifact.code);
        let allocator = OxcAllocator::default();
        let parsed = Parser::new(&allocator, &javascript, SourceType::default()).parse();
        assert!(
            parsed.diagnostics.is_empty(),
            "generated JavaScript is not parseable: {:?}\n{}",
            parsed.diagnostics,
            javascript
        );
    }

    #[test]
    fn validates_local_calls_without_absolute_occurrence_ids() {
        let template = "<citry-child :citry-id=\"preparedData.calls.citryCallA.id\" :key=\"preparedData.calls.citryCallA.key\"></citry-child>";
        let artifact = compile(CompileRequest {
            template: template.to_owned(),
            local_calls: vec![LocalCall {
                local_id: "citryCallA".to_owned(),
                type_key: "Child".to_owned(),
                component_tag: "citry-child".to_owned(),
                source_start: 0,
                source_end: (template.find('>').unwrap() + 1) as u32,
                bindings: vec![],
            }],
            local_call_runs: vec![],
            element_bindings: vec![],
            dynamic_elements: vec![],
        });
        assert!(
            artifact.diagnostics.is_empty(),
            "{:?}",
            artifact.diagnostics
        );
        assert_eq!(
            artifact.elements[0].local_call.as_ref().unwrap().local_id,
            "citryCallA"
        );
        assert!(
            !serde_json::to_string(&artifact)
                .unwrap()
                .contains("occurrence")
        );
    }

    #[test]
    fn validates_declared_native_component_call_bindings() {
        let template = "<citry-child :disabled=\"blocked\" :citry-id=\"preparedData.calls.citryCallA.id\" :key=\"preparedData.calls.citryCallA.key\"></citry-child>";
        let binding_start = template.find(":disabled").unwrap();
        let binding_end = binding_start + ":disabled=\"blocked\"".len();
        let artifact = compile(CompileRequest {
            template: template.to_owned(),
            local_calls: vec![LocalCall {
                local_id: "citryCallA".to_owned(),
                type_key: "Child".to_owned(),
                component_tag: "citry-child".to_owned(),
                source_start: 0,
                source_end: (template.find('>').unwrap() + 1) as u32,
                bindings: vec![ComponentCallBinding {
                    kind: "prop".to_owned(),
                    name: ":disabled".to_owned(),
                    value: "blocked".to_owned(),
                    source_start: binding_start as u32,
                    source_end: binding_end as u32,
                }],
            }],
            local_call_runs: vec![],
            element_bindings: vec![],
            dynamic_elements: vec![],
        });
        assert!(
            artifact.diagnostics.is_empty(),
            "{:?}",
            artifact.diagnostics
        );
        let call = artifact
            .elements
            .iter()
            .find_map(|item| item.local_call.as_ref())
            .unwrap();
        assert_eq!(call.bindings[0].name, ":disabled");
    }

    #[test]
    fn preserves_comparison_operators_in_declared_component_bindings() {
        let template = "<citry-child @input=\"value = value < 3\" :citry-id=\"preparedData.calls.citryCallA.id\" :key=\"preparedData.calls.citryCallA.key\"></citry-child>";
        let binding_start = template.find("@input").unwrap();
        let binding_end = binding_start + "@input=\"value = value < 3\"".len();
        let artifact = compile(CompileRequest {
            template: template.to_owned(),
            local_calls: vec![LocalCall {
                local_id: "citryCallA".to_owned(),
                type_key: "Child".to_owned(),
                component_tag: "citry-child".to_owned(),
                source_start: 0,
                source_end: (template.find('>').unwrap() + 1) as u32,
                bindings: vec![ComponentCallBinding {
                    kind: "event".to_owned(),
                    name: "@input".to_owned(),
                    value: "value = value < 3".to_owned(),
                    source_start: binding_start as u32,
                    source_end: binding_end as u32,
                }],
            }],
            local_call_runs: vec![],
            element_bindings: vec![],
            dynamic_elements: vec![],
        });
        assert!(
            artifact.diagnostics.is_empty(),
            "comparison binding must remain valid Vue source: {:?}",
            artifact.diagnostics
        );
    }

    #[test]
    fn rejects_extra_or_reordered_local_call_props() {
        let compile_case = |template: &str| {
            let binding_start = template.find(":disabled").unwrap();
            let binding_end = binding_start + ":disabled=\"blocked\"".len();
            compile(CompileRequest {
                template: template.to_owned(),
                local_calls: vec![LocalCall {
                    local_id: "citryCallA".to_owned(),
                    type_key: "Child".to_owned(),
                    component_tag: "citry-child".to_owned(),
                    source_start: 0,
                    source_end: (template.find('>').unwrap() + 1) as u32,
                    bindings: vec![ComponentCallBinding {
                        kind: "prop".to_owned(),
                        name: ":disabled".to_owned(),
                        value: "blocked".to_owned(),
                        source_start: binding_start as u32,
                        source_end: binding_end as u32,
                    }],
                }],
                local_call_runs: vec![],
                element_bindings: vec![],
                dynamic_elements: vec![],
            })
        };
        let extra = compile_case(
            "<citry-child :disabled=\"blocked\" v-bind=\"evil\" :citry-id=\"preparedData.calls.citryCallA.id\" :key=\"preparedData.calls.citryCallA.key\"></citry-child>",
        );
        assert!(
            extra
                .diagnostics
                .iter()
                .any(|item| item.code == "LOCAL_CALL_CLIENT_BINDING_MISMATCH")
        );
        let reordered = compile_case(
            "<citry-child :citry-id=\"preparedData.calls.citryCallA.id\" :disabled=\"blocked\" :key=\"preparedData.calls.citryCallA.key\"></citry-child>",
        );
        assert!(
            reordered
                .diagnostics
                .iter()
                .any(|item| item.code == "LOCAL_CALL_CLIENT_BINDING_MISMATCH")
        );
    }

    #[test]
    fn validates_definition_scoped_dynamic_element_alias() {
        let template = "<citry-dynamic-0123456789abcdef v-on:click=\"$x(($el) => ({value: 7}))\">x</citry-dynamic-0123456789abcdef>";
        let artifact = compile(CompileRequest {
            template: template.to_owned(),
            local_calls: vec![],
            local_call_runs: vec![],
            element_bindings: vec![],
            dynamic_elements: vec![DynamicElement {
                alias: "citry-dynamic-0123456789abcdef".to_owned(),
                tag: "section".to_owned(),
                source_start: 0,
                source_end: template.find("\">").unwrap() as u32 + 2,
            }],
        });
        assert!(
            artifact.diagnostics.is_empty(),
            "{:?}",
            artifact.diagnostics
        );
        assert!(
            artifact
                .code
                .contains("_createElementBlock(\"citry-dynamic-0123456789abcdef\"")
        );
        assert!(!artifact.code.contains("resolveComponent"));
        assert_eq!(artifact.dynamic_elements[0].tag, "section");
    }

    #[test]
    fn rejects_unclaimed_or_misplaced_reserved_dynamic_elements() {
        let template =
            "<div></div><citry-dynamic-0123456789abcdef></citry-dynamic-0123456789abcdef>";
        let unclaimed = compile(CompileRequest {
            template: template.to_owned(),
            local_calls: vec![],
            local_call_runs: vec![],
            element_bindings: vec![],
            dynamic_elements: vec![],
        });
        assert!(
            unclaimed
                .diagnostics
                .iter()
                .any(|item| item.code == "DYNAMIC_ELEMENT_MISMATCH")
        );

        let misplaced = compile(CompileRequest {
            template: template.to_owned(),
            local_calls: vec![],
            local_call_runs: vec![],
            element_bindings: vec![],
            dynamic_elements: vec![DynamicElement {
                alias: "citry-dynamic-0123456789abcdef".to_owned(),
                tag: "section".to_owned(),
                source_start: 0,
                source_end: 5,
            }],
        });
        assert!(
            misplaced
                .diagnostics
                .iter()
                .any(|item| item.code == "DYNAMIC_ELEMENT_MISMATCH")
        );
    }

    #[test]
    fn rejects_a_dynamic_key_after_an_unrelated_binding() {
        let artifact = compile(CompileRequest {
            template: "<input :title=\"x\" :key=\"item.id\" v-model=\"name\">".to_owned(),
            local_calls: vec![],
            local_call_runs: vec![],
            element_bindings: vec![],
            dynamic_elements: vec![],
        });
        assert!(
            artifact
                .diagnostics
                .iter()
                .any(|item| item.code == "DYNAMIC_KEY_UNSUPPORTED")
        );
    }

    #[test]
    fn composes_a_declared_prepared_key_with_the_lifecycle_digest() {
        let template = "<input v-bind=\"preparedData.citryAttrsA\" :key=\"preparedData.citryKeyA\" v-model=\"name\">";
        let artifact = compile(CompileRequest {
            template: template.to_owned(),
            local_calls: vec![],
            local_call_runs: vec![],
            element_bindings: vec![ElementBinding {
                source_start: 0,
                source_end: template.len() as u32,
                attrs_binding_key: Some("citryAttrsA".to_owned()),
                key_binding_key: Some("citryKeyA".to_owned()),
                runtime_events_binding_key: None,
                browser_binding_keys: vec![],
            }],
            dynamic_elements: vec![],
        });
        assert!(
            artifact.diagnostics.is_empty(),
            "{:?}",
            artifact.diagnostics
        );
        assert!(
            artifact
                .transformed_template
                .contains("JSON.stringify(['citryReplacement")
        );
        assert!(
            artifact
                .transformed_template
                .contains("preparedData.citryKeyA")
        );
    }

    #[test]
    fn template_v_if_fragment_keeps_a_prepared_child_lifecycle_key() {
        let template = concat!(
            "<template v-if=\"ready\">",
            "<input v-bind=\"preparedData.citryAttrsA\" ",
            ":key=\"preparedData.citryKeyA\" v-model=\"name\">",
            "</template>"
        );
        let source_start = template.find("<input").unwrap();
        let source_end = source_start + template[source_start..].find('>').unwrap() + 1;
        let artifact = compile(CompileRequest {
            template: template.to_owned(),
            local_calls: vec![],
            local_call_runs: vec![],
            element_bindings: vec![ElementBinding {
                source_start: source_start as u32,
                source_end: source_end as u32,
                attrs_binding_key: Some("citryAttrsA".to_owned()),
                key_binding_key: Some("citryKeyA".to_owned()),
                runtime_events_binding_key: None,
                browser_binding_keys: vec![],
            }],
            dynamic_elements: vec![],
        });
        assert!(
            artifact.diagnostics.is_empty(),
            "{:?}",
            artifact.diagnostics
        );
        assert!(artifact.code.contains("_Fragment"), "{}", artifact.code);
        assert!(artifact.code.contains("key: 0"), "{}", artifact.code);
        assert!(
            artifact.code.contains("preparedData.citryKeyA"),
            "{}",
            artifact.code
        );
    }

    #[test]
    fn template_v_if_fragment_keeps_a_native_local_call_key() {
        let template = concat!(
            "<template v-if=\"ready\">",
            "<citry-child :citry-id=\"preparedData.calls.citryCallA.id\" ",
            ":key=\"preparedData.calls.citryCallA.key\"></citry-child>",
            "</template>"
        );
        let source_start = template.find("<citry-child").unwrap();
        let source_end = source_start + template[source_start..].find('>').unwrap() + 1;
        let artifact = compile(CompileRequest {
            template: template.to_owned(),
            local_calls: vec![LocalCall {
                local_id: "citryCallA".to_owned(),
                type_key: "Child".to_owned(),
                component_tag: "citry-child".to_owned(),
                source_start: source_start as u32,
                source_end: source_end as u32,
                bindings: vec![],
            }],
            local_call_runs: vec![],
            element_bindings: vec![],
            dynamic_elements: vec![],
        });

        assert!(
            artifact.diagnostics.is_empty(),
            "{:?}",
            artifact.diagnostics
        );
        assert!(artifact.code.contains("_Fragment"), "{}", artifact.code);
        assert!(artifact.code.contains("key: 0"), "{}", artifact.code);
        assert!(
            artifact.code.contains("preparedData.calls.citryCallA.key"),
            "{}",
            artifact.code
        );
        let matching_calls = artifact
            .elements
            .iter()
            .filter(|element| element.tag == "citry-child")
            .collect::<Vec<_>>();
        assert_eq!(matching_calls.len(), 1, "{:?}", artifact.elements);
        assert_eq!(
            matching_calls[0]
                .local_call
                .as_ref()
                .map(|call| call.local_id.as_str()),
            Some("citryCallA")
        );
    }

    #[test]
    fn lifecycle_tuple_changes_the_primitive_key_and_removal_restores_authored_key() {
        let compile_one = |directive: &str| {
            compile(CompileRequest {
                template: format!(r#"<input key="row" {directive}="name">"#),
                local_calls: vec![],
                local_call_runs: vec![],
                element_bindings: vec![],
                dynamic_elements: vec![],
            })
        };
        let plain = compile(CompileRequest {
            template: r#"<input key="row">"#.to_owned(),
            local_calls: vec![],
            local_call_runs: vec![],
            element_bindings: vec![],
            dynamic_elements: vec![],
        });
        let eager = compile_one("v-model");
        let lazy = compile_one("v-model.lazy");
        assert!(plain.transformed_template.contains(r#"key="row""#));
        assert_ne!(eager.transformed_template, lazy.transformed_template);
        assert!(
            eager
                .transformed_template
                .contains(r#"key="citryReplacement"#)
        );
    }

    #[test]
    fn template_v_for_fragments_scope_child_lifecycle_revisions_per_row() {
        let compile_one = |directive: &str| {
            compile(CompileRequest {
                template: format!(
                    r#"<template v-if="ready"><template v-for="row in rows"><input {directive}="row.value"></template></template>"#
                ),
                local_calls: vec![],
                local_call_runs: vec![],
                element_bindings: vec![],
                dynamic_elements: vec![],
            })
        };
        let eager = compile_one("v-model");
        let lazy = compile_one("v-model.lazy");
        for artifact in [&eager, &lazy] {
            assert!(
                artifact.diagnostics.is_empty(),
                "{:?}",
                artifact.diagnostics
            );
            let replacement_key = artifact
                .elements
                .iter()
                .find(|element| element.tag == "input")
                .and_then(|element| element.replacement_key.as_deref())
                .expect("input has a lifecycle replacement key");
            assert!(artifact.code.contains("_Fragment"), "{}", artifact.code);
            assert!(
                artifact
                    .code
                    .contains(&format!(r#"key: "{replacement_key}""#)),
                "{}",
                artifact.code
            );
        }
        assert_ne!(
            eager.elements.last().unwrap().replacement_key,
            lazy.elements.last().unwrap().replacement_key
        );
    }

    #[test]
    fn model_and_translation_runtime_identity_matches_element_behavior() {
        let artifact = compile(CompileRequest {
            template: concat!(
                "<input type=\"text\" v-model=\"text\">",
                "<input type=\"checkbox\" v-model=\"checked\">",
                "<input type=\"radio\" v-model=\"picked\">",
                "<input :type=\"kind\" v-model=\"dynamic\">",
                "<input v-bind=\"attrs\" v-model=\"spread\">",
                "<select v-model=\"selected\"></select>",
                "<p v-c-tr=\"message\"></p>"
            )
            .to_owned(),
            local_calls: vec![],
            local_call_runs: vec![],
            element_bindings: vec![],
            dynamic_elements: vec![],
        });
        assert!(
            artifact.diagnostics.is_empty(),
            "{:?}",
            artifact.diagnostics
        );
        let identities = artifact
            .elements
            .iter()
            .flat_map(|element| &element.directives)
            .filter_map(|directive| directive.runtime_implementation.as_deref())
            .collect::<Vec<_>>();
        assert_eq!(
            identities,
            [
                "vModelText",
                "vModelCheckbox",
                "vModelRadio",
                "vModelDynamic",
                "vModelDynamic",
                "vModelSelect",
                "resolveDirective:c-tr"
            ]
        );
        for helper in [
            "vModelText",
            "vModelCheckbox",
            "vModelRadio",
            "vModelDynamic",
            "vModelSelect",
            "resolveDirective",
        ] {
            assert!(
                artifact.helpers.iter().any(|value| value == helper),
                "missing {helper}: {:?}",
                artifact.helpers
            );
        }
        let dynamic_markers = artifact
            .transformed_template
            .match_indices(":__citryInputModelSite=")
            .map(|(start, _)| start)
            .collect::<Vec<_>>();
        assert_eq!(dynamic_markers.len(), 2);
        let spread_start = artifact
            .transformed_template
            .find("v-bind=\"attrs\"")
            .unwrap();
        assert!(dynamic_markers[1] > spread_start);
    }

    #[test]
    fn rejects_an_authored_dynamic_model_site_marker() {
        let artifact = compile(CompileRequest {
            template: "<input :type=\"kind\" v-model=\"value\" :__citryInputModelSite=\"fake\">"
                .to_owned(),
            local_calls: vec![],
            local_call_runs: vec![],
            element_bindings: vec![],
            dynamic_elements: vec![],
        });

        assert!(
            artifact
                .diagnostics
                .iter()
                .any(|item| item.code == "RESERVED_MODEL_SITE_MARKER")
        );
    }

    #[test]
    fn rejects_direct_and_nested_local_calls_created_by_v_for() {
        let template = "<div v-for=\"item in items\"><template #default><citry-child :citry-id=\"preparedData.calls.citryCallA.id\" :key=\"preparedData.calls.citryCallA.key\"></citry-child></template></div>";
        let start = template.find("<citry-child").unwrap();
        let end = start + template[start..].find('>').unwrap() + 1;
        let artifact = compile(CompileRequest {
            template: template.to_owned(),
            local_calls: vec![LocalCall {
                local_id: "citryCallA".to_owned(),
                type_key: "Child".to_owned(),
                component_tag: "citry-child".to_owned(),
                source_start: start as u32,
                source_end: end as u32,
                bindings: vec![],
            }],
            local_call_runs: vec![],
            element_bindings: vec![],
            dynamic_elements: vec![],
        });
        assert!(
            artifact
                .diagnostics
                .iter()
                .any(|item| item.code == "CITRY_COMPONENT_IN_V_FOR")
        );
    }

    #[test]
    fn supports_empty_fragment_and_component_only_roots() {
        for template in ["", "<p>A</p><p>B</p>", "<citry-child></citry-child>"] {
            let artifact = compile(CompileRequest {
                template: template.to_owned(),
                local_calls: vec![],
                local_call_runs: vec![],
                element_bindings: vec![],
                dynamic_elements: vec![],
            });
            assert!(
                artifact.diagnostics.is_empty(),
                "{template:?}: {:?}",
                artifact.diagnostics
            );
        }
    }

    #[test]
    fn allows_audited_ordinary_expression_helpers() {
        let artifact = compile(CompileRequest {
            template: r#"<div :class="{active: yes}" :style="{display: mode}"><i v-for="item in items" :key="item">{{ item }}</i><button @keyup.enter="go">go</button></div>"#.to_owned(),
            local_calls: vec![],
            local_call_runs: vec![],
            element_bindings: vec![],
        dynamic_elements: vec![],
        });
        assert!(
            artifact.diagnostics.is_empty(),
            "{:?}",
            artifact.diagnostics
        );
        for helper in ["normalizeClass", "normalizeStyle", "renderList", "withKeys"] {
            assert!(
                artifact.helpers.contains(&helper.to_owned()),
                "missing {helper}"
            );
        }
    }
}
