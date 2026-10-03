//! Hydration facts read from the compiled render function.
//!
//! When the server writes HTML that Vue later adopts in the browser
//! ("hydration"), the HTML must contain the comment markers Vue's render
//! output expects, and every attribute that hydration does not rewrite must
//! already hold the exact value Vue would render. Both depend on what the
//! compiled render function does, not on the template text alone: the patched
//! compiler keeps some keyed children inside a Fragment, and a constant
//! binding such as `:data-x="1"` is treated as static.
//!
//! So this module reads the emitted render function, walks it side by side
//! with the parsed template that produced it, and reports:
//!
//! - each place the render function creates a Vue Fragment (the server
//!   writes `<!--[-->` before and `<!--]-->` after its content) or a
//!   placeholder comment (`<!--v-if-->` for a `v-if` chain with no matching
//!   branch, `<!---->` for a render that returns nothing);
//! - for each element and component call, how hydration treats each authored
//!   attribute.
//!
//! When the two walks disagree anywhere, the whole plan is reported as
//! unsupported instead of partially right; the browser then mounts the
//! component instead of hydrating it, as it does without a plan.
//!
//! Both lists follow the order in which the render function creates its
//! nodes (named slots before the default slot, a chain's branches before its
//! placeholder), not source order; consumers look records up by position.

use std::collections::HashMap;

use oxc_allocator::Allocator as OxcAllocator;
use oxc_ast::ast::{
    Argument, ArrayExpressionElement, ArrowFunctionBody, BindingPattern, Expression,
    ObjectPropertyKind, Statement, UnaryOperator,
};
use oxc_parser::Parser;
use oxc_span::SourceType;
use serde::Serialize;
use vize_atelier_core::{
    DirectiveNode, ElementNode, ExpressionNode, PropNode, TemplateChildNode,
    options::{ParserOptions, TemplateSyntaxMode},
    parser::parse_with_options_and_template_syntax,
};
use vize_atelier_dom::Allocator;

use crate::{
    DynamicElement, Edit, ElementMetadata, UnchangedSourceSpan, hash, map_action_to_original,
    unchanged_source_spans,
};

#[derive(Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum HydrationPlanStatus {
    Complete,
    Unsupported,
}

/// Where the render function creates Fragments and placeholder comments, and
/// how hydration treats each attribute, keyed to template byte positions.
#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct HydrationPlan {
    /// The spans below index this artifact field's UTF-8 bytes.
    pub source: &'static str,
    pub source_sha256: String,
    pub original_source_sha256: String,
    pub status: HydrationPlanStatus,
    pub anchors: Vec<HydrationAnchor>,
    pub elements: Vec<HydrationElement>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub reason_code: Option<&'static str>,
}

/// One Fragment or placeholder comment the render function creates.
#[derive(Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct HydrationAnchor {
    /// `fragment` writes `<!--[-->` and `<!--]-->` around the content;
    /// `comment` writes `<!--{comment}-->` in place of any content.
    pub kind: &'static str,
    /// The construct that creates it: `root`, `v-for`, `v-for-item`,
    /// `v-if-branch`, `slot`, `v-if`, or `empty-render`.
    pub origin: &'static str,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub comment: Option<&'static str>,
    pub source_start: u32,
    pub source_end: u32,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub original_start: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub original_end: Option<u32>,
    /// The `elements[].path` of the element that carries the construct, or
    /// an empty path for the template root, or null when the position has
    /// no element path.
    pub path: Option<Vec<String>>,
}

/// One element or component call and how hydration treats its attributes.
#[derive(Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct HydrationElement {
    /// `element` for a native element, `component` for a component call.
    pub vnode: &'static str,
    /// The tag Vue receives at runtime (a declared dynamic element alias is
    /// replaced by its declared tag).
    pub tag: String,
    pub source_start: u32,
    pub source_end: u32,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub original_start: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub original_end: Option<u32>,
    pub path: Option<Vec<String>>,
    pub patch_flag: i64,
    pub dynamic_props: Option<Vec<String>>,
    pub attributes: Vec<HydrationAttribute>,
}

#[derive(Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct HydrationAttribute {
    pub kind: &'static str,
    /// The static attribute name or the directive argument, when static.
    pub name: Option<String>,
    /// The key in the vnode props object that hydration iterates.
    pub prop_key: Option<String>,
    /// `patched`: hydration rewrites the DOM value. `checked`: hydration
    /// keeps the server value, so the server must write exactly what Vue's
    /// first render would. `per-key`: the key is only known per render, and
    /// the same runtime rules apply to each key. `directive`: a runtime
    /// directive sets the DOM state. `component`: the child component
    /// decides. `none`: nothing reaches the DOM as an attribute.
    pub hydration: &'static str,
    pub source_start: u32,
    pub source_end: u32,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub original_start: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub original_end: Option<u32>,
}

/// Build the plan for one compiled template.
pub(crate) fn hydration_plan(
    transformed: &str,
    original: &str,
    edits: &[Edit],
    code: &str,
    elements: &[ElementMetadata],
    dynamic_elements: &[DynamicElement],
) -> HydrationPlan {
    let mut plan = HydrationPlan {
        source: "transformedTemplate",
        source_sha256: hash(transformed),
        original_source_sha256: hash(original),
        status: HydrationPlanStatus::Complete,
        anchors: Vec::new(),
        elements: Vec::new(),
        reason_code: None,
    };
    if let Err(reason) = build(
        transformed,
        original,
        edits,
        code,
        elements,
        dynamic_elements,
        &mut plan,
    ) {
        // A partly matched plan would let the server write some markers and
        // miss others, so an unsupported plan carries no facts at all.
        plan.status = HydrationPlanStatus::Unsupported;
        plan.reason_code = Some(reason);
        plan.anchors.clear();
        plan.elements.clear();
    }
    plan
}

fn build(
    transformed: &str,
    original: &str,
    edits: &[Edit],
    code: &str,
    elements: &[ElementMetadata],
    dynamic_elements: &[DynamicElement],
    plan: &mut HydrationPlan,
) -> Result<(), &'static str> {
    // Position mapping needs non-overlapping edits; the compiler already
    // reports overlaps as diagnostics, and this plan refuses them too.
    let unchanged = unchanged_source_spans(original, edits).ok_or("source_edit_overlap")?;

    let oxc = OxcAllocator::default();
    let parsed = Parser::new(&oxc, code, SourceType::default()).parse();
    if !parsed.diagnostics.is_empty() {
        return Err("unsupported_render_shape");
    }
    let (components, root_expression) = render_body(&parsed.program.body)?;
    let reader = JsReader { components };
    let js_root = reader.root(root_expression)?;

    // Parse the exact source the render function was compiled from with the
    // same parser settings as the element walk, so spans line up with the
    // transformed template bytes.
    let allocator = Allocator::new();
    let (root, _) = parse_with_options_and_template_syntax(
        &allocator,
        transformed,
        ParserOptions::default(),
        TemplateSyntaxMode::Standard,
    );
    let aliases = dynamic_elements
        .iter()
        .map(|item| (item.alias.as_str(), item.tag.as_str()))
        .collect::<HashMap<_, _>>();
    let mut walk = CoWalk {
        aliases: &aliases,
        anchors: Vec::new(),
        elements: Vec::new(),
    };
    let template_root = root.children.iter().collect::<Vec<_>>();
    let root_end = u32::try_from(transformed.len()).map_err(|_| "source_too_large")?;
    match js_root {
        JsNode::Null => {
            // An empty render returns null; Vue normalizes that to an empty
            // comment vnode, which the server writes as `<!---->`.
            walk.children(&template_root, &[])?;
            walk.anchors
                .push(RawAnchor::comment("empty-render", "", 0, root_end).at_root());
        }
        JsNode::Fragment(children) => {
            // Several root nodes: the render wraps them in one Fragment.
            walk.anchors
                .push(RawAnchor::fragment("root", 0, root_end).at_root());
            walk.children(&template_root, &children)?;
        }
        other => walk.children(&template_root, std::slice::from_ref(&other))?,
    }

    // The parser can imply two elements at one offset (a `tbody` and a `tr`
    // around a table's direct cell), so an implied element's key also
    // carries its tag. Implied tags are never dynamic-element aliases.
    let paths = elements
        .iter()
        .map(|element| {
            let implied_tag =
                (element.source_start == element.source_end).then_some(element.tag.as_str());
            ((element.source_start, implied_tag), &element.path)
        })
        .collect::<HashMap<_, _>>();
    let original_end = u32::try_from(original.len()).map_err(|_| "source_too_large")?;
    for anchor in walk.anchors {
        let (original_start, original_end, path) = if anchor.root {
            // The root span covers the whole template in both coordinate
            // systems, and the root has no element path.
            (Some(0), Some(original_end), Some(Vec::new()))
        } else {
            element_position(anchor.start, anchor.end, None, &unchanged, &paths)
        };
        plan.anchors.push(HydrationAnchor {
            kind: anchor.kind,
            origin: anchor.origin,
            comment: anchor.comment,
            source_start: anchor.start,
            source_end: anchor.end,
            original_start,
            original_end,
            path,
        });
    }
    for element in walk.elements {
        let (original_start, original_end, path) = element_position(
            element.start,
            element.end,
            Some(&element.tag),
            &unchanged,
            &paths,
        );
        let attributes = element
            .attributes
            .into_iter()
            .map(|attribute| {
                // An attribute the compiler inserted or rewrote has no
                // authored bytes, so it keeps only its transformed span.
                let mapped = map_action_to_original(
                    transformed,
                    original,
                    attribute.start,
                    attribute.end,
                    &unchanged,
                );
                HydrationAttribute {
                    kind: attribute.kind,
                    name: attribute.name,
                    prop_key: attribute.prop_key,
                    hydration: attribute.hydration,
                    source_start: attribute.start,
                    source_end: attribute.end,
                    original_start: mapped.map(|(start, _)| start),
                    original_end: mapped.map(|(_, end)| end),
                }
            })
            .collect();
        plan.elements.push(HydrationElement {
            vnode: element.vnode,
            tag: element.tag,
            source_start: element.start,
            source_end: element.end,
            original_start,
            original_end,
            path,
            patch_flag: element.patch_flag,
            dynamic_props: element.dynamic_props,
            attributes,
        });
    }
    Ok(())
}

/// Map an element's transformed span to compiler-input bytes and find the
/// matching `elements[].path`.
///
/// Compiler edits only touch attributes inside an opening tag, so the first
/// `<` and the byte after the element's end stay in unchanged source even
/// when the span as a whole contains an edit.
///
/// An element the template parser implies (the `tbody` it adds around a
/// table's direct rows, or the `tr` around direct cells) has no authored tag,
/// so the parser gives it an empty span inside the tag that follows it. That
/// position is not an opening tag in the compiler input, so the element keeps
/// its path but has no compiler-input span. `tag` names the element for that
/// path lookup; anchors pass `None`.
fn element_position(
    start: u32,
    end: u32,
    tag: Option<&str>,
    unchanged: &[UnchangedSourceSpan],
    paths: &HashMap<(u32, Option<&str>), &Vec<String>>,
) -> (Option<u32>, Option<u32>, Option<Vec<String>>) {
    // Every authored element spans at least `<` and its tag name.
    let implied = start == end;
    let mapped_start = map_point(start, unchanged);
    let path = mapped_start
        .and_then(|offset| paths.get(&(offset, tag.filter(|_| implied))))
        .map(|path| (*path).clone());
    if implied {
        return (None, None, path);
    }
    (mapped_start, map_point(end, unchanged), path)
}

fn map_point(offset: u32, unchanged: &[UnchangedSourceSpan]) -> Option<u32> {
    let offset = offset as usize;
    let span = unchanged
        .iter()
        .find(|span| span.transformed_start <= offset && offset <= span.transformed_end)?;
    u32::try_from(span.original_start + (offset - span.transformed_start)).ok()
}

// ---------------------------------------------------------------------------
// Reading the render function
// ---------------------------------------------------------------------------

/// The part of the render function's output that decides DOM shape.
#[derive(Debug)]
enum JsNode {
    /// `return null`: nothing rendered.
    Null,
    /// Text, a text vnode, or an interpolation. Carries no markers.
    Text,
    Element {
        tag: String,
        props: JsProps,
        patch_flag: i64,
        dynamic_props: Option<Vec<String>>,
        children: Vec<JsNode>,
    },
    Component {
        /// The resolved tag, or `None` for `<component :is>`.
        name: Option<String>,
        props: JsProps,
        patch_flag: i64,
        dynamic_props: Option<Vec<String>>,
        slots: Vec<(String, Vec<JsNode>)>,
    },
    /// `createElementBlock(Fragment, ..., [children])`.
    Fragment(Vec<JsNode>),
    /// `createElementBlock(Fragment, null, renderList(source, item))`.
    List(Box<JsNode>),
    /// A `v-if` chain: the branches in order, then the final alternate.
    Conditional(Vec<JsNode>, Box<JsNode>),
    Comment(String),
    /// `renderSlot(...)`, with its fallback content when the template has one.
    Slot(Vec<JsNode>),
}

#[derive(Debug, Default)]
struct JsProps {
    /// Static keys in emission order.
    keys: Vec<String>,
}

/// Find the `render` function, its component bindings, and its return value.
fn render_body<'a, 'b>(
    body: &'b [Statement<'a>],
) -> Result<(HashMap<String, String>, &'b Expression<'a>), &'static str> {
    let function = body
        .iter()
        .find_map(|statement| match statement {
            Statement::FunctionDeclaration(function)
                if function.id.as_ref().is_some_and(|id| id.name == "render") =>
            {
                Some(function)
            }
            _ => None,
        })
        .ok_or("unsupported_render_shape")?;
    let statements = &function
        .body
        .as_ref()
        .ok_or("unsupported_render_shape")?
        .statements;
    let mut components = HashMap::new();
    let mut returned = None;
    for statement in statements {
        match statement {
            Statement::VariableDeclaration(declaration) => {
                for declarator in &declaration.declarations {
                    let BindingPattern::BindingIdentifier(id) = &declarator.id else {
                        return Err("unsupported_render_shape");
                    };
                    // `const _component_x = _resolveComponent("x")` names
                    // the tag each component identifier stands for.
                    if let Some(Expression::CallExpression(call)) = &declarator.init
                        && callee_name(&call.callee) == Some("_resolveComponent")
                        && let Some(Argument::StringLiteral(tag)) = call.arguments.first()
                    {
                        components.insert(id.name.to_string(), tag.value.to_string());
                    }
                }
            }
            Statement::ReturnStatement(statement) => {
                returned = statement.argument.as_ref();
            }
            _ => return Err("unsupported_render_shape"),
        }
    }
    Ok((components, returned.ok_or("unsupported_render_shape")?))
}

fn callee_name<'a>(callee: &Expression<'a>) -> Option<&'a str> {
    match callee {
        Expression::Identifier(id) => Some(id.name.as_str()),
        _ => None,
    }
}

fn unwrap_expression<'b, 'a>(mut expression: &'b Expression<'a>) -> &'b Expression<'a> {
    loop {
        match expression {
            Expression::ParenthesizedExpression(inner) => expression = &inner.expression,
            // `(_openBlock(), createX(...))`: the block call only records
            // dynamic children; the last expression is the vnode.
            Expression::SequenceExpression(sequence) => match sequence.expressions.last() {
                Some(last) => expression = last,
                None => return expression,
            },
            _ => return expression,
        }
    }
}

fn argument_expression<'b, 'a>(
    arguments: &'b [Argument<'a>],
    index: usize,
) -> Option<&'b Expression<'a>> {
    arguments.get(index).and_then(Argument::as_expression)
}

/// What a compiled render function returns at its root, for a caller that
/// applies `v-show` to this component.
///
/// Vue hands a component call's directives to the vnode its render returns
/// and runs them only when that vnode mounts an element. The shapes are:
///
/// - `element`: one element, or a `v-if` chain whose branches are elements
///   or its placeholder comment. `v-show` works.
/// - `component`: another component (or such a chain). Vue passes the
///   directive on, so that component's own root decides.
/// - `empty`: `null` or a comment. Nothing is shown either way.
/// - `fragment`: several roots, a `v-for`, or a slot outlet. Vue skips the
///   directive without an error.
/// - `text`: text only. Vue skips the directive without an error.
/// - `opaque-html`: HTML Python hands over as a finished string, which Vue
///   inserts as one fixed block and never runs directives on.
/// - `unknown`: the render function has a shape this reader does not model.
pub(crate) fn root_shape(code: &str) -> &'static str {
    let oxc = OxcAllocator::default();
    let parsed = Parser::new(&oxc, code, SourceType::default()).parse();
    if !parsed.diagnostics.is_empty() {
        return "unknown";
    }
    let Ok((components, root_expression)) = render_body(&parsed.program.body) else {
        return "unknown";
    };
    match (JsReader { components }).root(root_expression) {
        Ok(node) => node_shape(&node),
        Err(_) => "unknown",
    }
}

fn node_shape(node: &JsNode) -> &'static str {
    match node {
        JsNode::Element { .. } => "element",
        JsNode::Component { name, .. } if name.as_deref() == Some("citry-opaque-html") => {
            "opaque-html"
        }
        JsNode::Component { .. } => "component",
        JsNode::Null | JsNode::Comment(_) => "empty",
        JsNode::Text => "text",
        JsNode::Fragment(_) | JsNode::List(_) | JsNode::Slot(_) => "fragment",
        JsNode::Conditional(branches, otherwise) => {
            // Only one branch renders at a time, so the chain is as weak as
            // its weakest branch: an unusable branch wins over a component
            // branch, which wins over element and empty branches.
            let shapes = branches
                .iter()
                .chain(std::iter::once(otherwise.as_ref()))
                .map(node_shape)
                .collect::<Vec<_>>();
            [
                "fragment",
                "text",
                "opaque-html",
                "unknown",
                "component",
                "element",
            ]
            .into_iter()
            .find(|shape| shapes.contains(shape))
            .unwrap_or("empty")
        }
    }
}

struct JsReader {
    components: HashMap<String, String>,
}

impl JsReader {
    fn root(&self, expression: &Expression<'_>) -> Result<JsNode, &'static str> {
        match unwrap_expression(expression) {
            Expression::NullLiteral(_) => Ok(JsNode::Null),
            other => self.node(other),
        }
    }

    fn node(&self, expression: &Expression<'_>) -> Result<JsNode, &'static str> {
        let expression = unwrap_expression(expression);
        match expression {
            Expression::ConditionalExpression(_) => {
                let mut branches = Vec::new();
                let mut current = expression;
                // Flatten `a ? A : b ? B : C` into branches and the final
                // alternate, which is either `v-else` or the placeholder.
                while let Expression::ConditionalExpression(conditional) = current {
                    branches.push(self.node(&conditional.consequent)?);
                    current = unwrap_expression(&conditional.alternate);
                }
                Ok(JsNode::Conditional(branches, Box::new(self.node(current)?)))
            }
            Expression::CallExpression(call) => {
                let name = callee_name(&call.callee).ok_or("unsupported_render_shape")?;
                let arguments = call.arguments.as_slice();
                match name {
                    "_withDirectives" => self
                        .node(argument_expression(arguments, 0).ok_or("unsupported_render_shape")?),
                    "_createElementVNode"
                    | "_createElementBlock"
                    | "_createVNode"
                    | "_createBlock" => self.vnode(arguments),
                    "_createCommentVNode" => {
                        Ok(JsNode::Comment(match argument_expression(arguments, 0) {
                            Some(Expression::StringLiteral(text)) => text.value.to_string(),
                            None => String::new(),
                            Some(_) => return Err("unsupported_render_shape"),
                        }))
                    }
                    "_createTextVNode" | "_toDisplayString" => Ok(JsNode::Text),
                    "_renderSlot" => {
                        let fallback = match argument_expression(arguments, 3) {
                            Some(function) => self.function_children(function)?,
                            None => Vec::new(),
                        };
                        Ok(JsNode::Slot(fallback))
                    }
                    _ => Err("unsupported_render_shape"),
                }
            }
            Expression::StringLiteral(_)
            | Expression::TemplateLiteral(_)
            | Expression::BinaryExpression(_) => Ok(JsNode::Text),
            _ => Err("unsupported_render_shape"),
        }
    }

    fn vnode(&self, arguments: &[Argument<'_>]) -> Result<JsNode, &'static str> {
        let tag = argument_expression(arguments, 0).ok_or("unsupported_render_shape")?;
        let props = || props(argument_expression(arguments, 1));
        let patch_flag = patch_flag(argument_expression(arguments, 3))?;
        let dynamic_props = dynamic_props(argument_expression(arguments, 4))?;
        match tag {
            Expression::Identifier(id) if id.name == "_Fragment" => {
                match argument_expression(arguments, 2).map(unwrap_expression) {
                    Some(Expression::CallExpression(call))
                        if callee_name(&call.callee) == Some("_renderList") =>
                    {
                        let item = argument_expression(&call.arguments, 1)
                            .ok_or("unsupported_render_shape")?;
                        Ok(JsNode::List(Box::new(self.function_result(item)?)))
                    }
                    Some(Expression::ArrayExpression(array)) => {
                        Ok(JsNode::Fragment(self.array(&array.elements)?))
                    }
                    _ => Err("unsupported_render_shape"),
                }
            }
            Expression::StringLiteral(tag) => Ok(JsNode::Element {
                tag: tag.value.to_string(),
                props: props()?,
                patch_flag,
                dynamic_props,
                children: self.children(argument_expression(arguments, 2))?,
            }),
            Expression::Identifier(id) => {
                let name = self
                    .components
                    .get(id.name.as_str())
                    .ok_or("unsupported_render_shape")?;
                Ok(JsNode::Component {
                    name: Some(name.clone()),
                    props: props()?,
                    patch_flag,
                    dynamic_props,
                    slots: self.slots(argument_expression(arguments, 2))?,
                })
            }
            Expression::CallExpression(call)
                if callee_name(&call.callee) == Some("_resolveDynamicComponent") =>
            {
                Ok(JsNode::Component {
                    name: None,
                    props: props()?,
                    patch_flag,
                    dynamic_props,
                    slots: self.slots(argument_expression(arguments, 2))?,
                })
            }
            _ => Err("unsupported_render_shape"),
        }
    }

    fn array(&self, elements: &[ArrayExpressionElement<'_>]) -> Result<Vec<JsNode>, &'static str> {
        let mut nodes = Vec::with_capacity(elements.len());
        for element in elements {
            nodes.push(self.node(element.as_expression().ok_or("unsupported_render_shape")?)?);
        }
        Ok(nodes)
    }

    fn children(&self, children: Option<&Expression<'_>>) -> Result<Vec<JsNode>, &'static str> {
        match children.map(unwrap_expression) {
            None | Some(Expression::NullLiteral(_)) => Ok(Vec::new()),
            Some(Expression::ArrayExpression(array)) => self.array(&array.elements),
            // Text-only children are passed as a string expression.
            Some(other) => match self.node(other)? {
                JsNode::Text => Ok(vec![JsNode::Text]),
                _ => Err("unsupported_render_shape"),
            },
        }
    }

    /// The value an arrow function returns (a `renderList` item).
    fn function_result(&self, function: &Expression<'_>) -> Result<JsNode, &'static str> {
        self.node(returned_expression(function)?)
    }

    /// The array an arrow function returns (slot content or slot fallback).
    fn function_children(&self, function: &Expression<'_>) -> Result<Vec<JsNode>, &'static str> {
        match unwrap_expression(returned_expression(function)?) {
            Expression::ArrayExpression(array) => self.array(&array.elements),
            _ => Err("unsupported_render_shape"),
        }
    }

    fn slots(
        &self,
        slots: Option<&Expression<'_>>,
    ) -> Result<Vec<(String, Vec<JsNode>)>, &'static str> {
        let object = match slots.map(unwrap_expression) {
            None | Some(Expression::NullLiteral(_)) => return Ok(Vec::new()),
            Some(Expression::ObjectExpression(object)) => object,
            // `createSlots` (conditional or looped slots) is outside the
            // audited helper set, so it never reaches a complete plan.
            _ => return Err("unsupported_render_shape"),
        };
        let mut output = Vec::new();
        for property in &object.properties {
            let ObjectPropertyKind::ObjectProperty(property) = property else {
                return Err("unsupported_render_shape");
            };
            // Citry names slots with a quoted literal in brackets, which
            // the render emits as a computed string key.
            let name = match (&property.key, property.computed) {
                (key, false) => key.static_name(),
                (key, true) => match key.as_expression().map(unwrap_expression) {
                    Some(Expression::StringLiteral(literal)) => Some(literal.value.as_str().into()),
                    _ => None,
                },
            }
            .ok_or("unsupported_render_shape")?;
            // `_` is Vue's slot stability flag, not a slot.
            if name == "_" {
                continue;
            }
            let Expression::CallExpression(call) = unwrap_expression(&property.value) else {
                return Err("unsupported_render_shape");
            };
            if callee_name(&call.callee) != Some("_withCtx") {
                return Err("unsupported_render_shape");
            }
            let function =
                argument_expression(&call.arguments, 0).ok_or("unsupported_render_shape")?;
            output.push((name.to_string(), self.function_children(function)?));
        }
        Ok(output)
    }
}

fn returned_expression<'b, 'a>(
    function: &'b Expression<'a>,
) -> Result<&'b Expression<'a>, &'static str> {
    let Expression::ArrowFunctionExpression(arrow) = unwrap_expression(function) else {
        return Err("unsupported_render_shape");
    };
    match &arrow.body {
        ArrowFunctionBody::FunctionBody(body) => match body.statements.as_slice() {
            [Statement::ReturnStatement(statement)] => statement
                .argument
                .as_ref()
                .ok_or("unsupported_render_shape"),
            _ => Err("unsupported_render_shape"),
        },
        // `() => [...]` returns its expression body directly.
        body => body.as_expression().ok_or("unsupported_render_shape"),
    }
}

/// Collect the static prop keys. Spreads and computed keys are not listed:
/// their names are only known when the render runs.
fn props(props: Option<&Expression<'_>>) -> Result<JsProps, &'static str> {
    let mut output = JsProps::default();
    collect_props(props, &mut output)?;
    Ok(output)
}

fn collect_props(props: Option<&Expression<'_>>, output: &mut JsProps) -> Result<(), &'static str> {
    let Some(props) = props.map(unwrap_expression) else {
        return Ok(());
    };
    match props {
        Expression::NullLiteral(_) => {}
        Expression::ObjectExpression(object) => {
            for property in &object.properties {
                if let ObjectPropertyKind::ObjectProperty(property) = property
                    && !property.computed
                    && let Some(name) = property.key.static_name()
                {
                    output.keys.push(name.to_string());
                }
            }
        }
        Expression::CallExpression(call)
            if matches!(
                callee_name(&call.callee),
                Some("_mergeProps" | "_normalizeProps" | "_guardReactiveProps")
            ) =>
        {
            for argument in &call.arguments {
                collect_props(argument.as_expression(), output)?;
            }
        }
        // Any other expression is a `v-bind` object spread evaluated at
        // render time; its keys are not static.
        _ => {}
    }
    Ok(())
}

fn patch_flag(flag: Option<&Expression<'_>>) -> Result<i64, &'static str> {
    match flag.map(unwrap_expression) {
        None | Some(Expression::NullLiteral(_)) => Ok(0),
        Some(Expression::NumericLiteral(value)) => Ok(value.value as i64),
        Some(Expression::UnaryExpression(unary))
            if unary.operator == UnaryOperator::UnaryNegation =>
        {
            match unwrap_expression(&unary.argument) {
                Expression::NumericLiteral(value) => Ok(-(value.value as i64)),
                _ => Err("unsupported_render_shape"),
            }
        }
        Some(_) => Err("unsupported_render_shape"),
    }
}

fn dynamic_props(value: Option<&Expression<'_>>) -> Result<Option<Vec<String>>, &'static str> {
    match value.map(unwrap_expression) {
        None | Some(Expression::NullLiteral(_)) => Ok(None),
        Some(Expression::ArrayExpression(array)) => array
            .elements
            .iter()
            .map(|element| match element {
                ArrayExpressionElement::StringLiteral(key) => Ok(key.value.to_string()),
                _ => Err("unsupported_render_shape"),
            })
            .collect::<Result<Vec<_>, _>>()
            .map(Some),
        Some(_) => Err("unsupported_render_shape"),
    }
}

// ---------------------------------------------------------------------------
// Walking the template beside the render output
// ---------------------------------------------------------------------------

struct RawAnchor {
    /// Set only for the template-root anchors; an element whose opening tag
    /// is the whole template must not be mistaken for the root.
    root: bool,
    kind: &'static str,
    origin: &'static str,
    comment: Option<&'static str>,
    start: u32,
    end: u32,
}

impl RawAnchor {
    fn fragment(origin: &'static str, start: u32, end: u32) -> Self {
        Self {
            root: false,
            kind: "fragment",
            origin,
            comment: None,
            start,
            end,
        }
    }

    fn at_root(mut self) -> Self {
        self.root = true;
        self
    }

    fn comment(origin: &'static str, comment: &'static str, start: u32, end: u32) -> Self {
        Self {
            root: false,
            kind: "comment",
            origin,
            comment: Some(comment),
            start,
            end,
        }
    }
}

struct RawElement {
    vnode: &'static str,
    tag: String,
    start: u32,
    end: u32,
    patch_flag: i64,
    dynamic_props: Option<Vec<String>>,
    attributes: Vec<RawAttribute>,
}

struct RawAttribute {
    kind: &'static str,
    name: Option<String>,
    prop_key: Option<String>,
    hydration: &'static str,
    start: u32,
    end: u32,
}

/// One template construct that becomes one render output node.
enum Unit<'t, 'a> {
    Element(&'t ElementNode<'a>),
    /// A `v-if` element and its `v-else-if`/`v-else` siblings.
    Chain(Vec<&'t ElementNode<'a>>),
}

/// Walks the parsed template and the render output side by side, collecting
/// anchors and elements.
struct CoWalk<'m> {
    aliases: &'m HashMap<&'m str, &'m str>,
    anchors: Vec<RawAnchor>,
    elements: Vec<RawElement>,
}

fn directive<'t, 'a>(element: &'t ElementNode<'a>, name: &str) -> Option<&'t DirectiveNode<'a>> {
    element.props.iter().find_map(|prop| match prop {
        PropNode::Directive(directive) if directive.name == name => Some(&**directive),
        _ => None,
    })
}

fn has_directive(element: &ElementNode<'_>, name: &str) -> bool {
    directive(element, name).is_some()
}

impl CoWalk<'_> {
    /// Match template children to render output children in order.
    ///
    /// Text and comments carry no markers (comments are not emitted by this
    /// compiler), so both sides drop them before pairing.
    fn children(
        &mut self,
        template: &[&TemplateChildNode<'_>],
        output: &[JsNode],
    ) -> Result<(), &'static str> {
        let units = units(template)?;
        let output = output
            .iter()
            .filter(|node| !matches!(node, JsNode::Text))
            .collect::<Vec<_>>();
        if units.len() != output.len() {
            return Err("unsupported_render_shape");
        }
        for (unit, node) in units.into_iter().zip(output) {
            match unit {
                Unit::Element(element) => self.element(element, false, node)?,
                Unit::Chain(branches) => self.chain(&branches, node)?,
            }
        }
        Ok(())
    }

    fn chain(&mut self, branches: &[&ElementNode<'_>], node: &JsNode) -> Result<(), &'static str> {
        let JsNode::Conditional(consequents, alternate) = node else {
            return Err("unsupported_render_shape");
        };
        let head = branches[0];
        let has_else = branches
            .last()
            .is_some_and(|branch| has_directive(branch, "else"));
        let expected = if has_else {
            branches.len() - 1
        } else {
            branches.len()
        };
        if consequents.len() != expected {
            return Err("unsupported_render_shape");
        }
        for (branch, consequent) in branches.iter().zip(consequents) {
            self.element(branch, true, consequent)?;
        }
        if has_else {
            self.element(branches[expected], true, alternate)?;
        } else {
            // No branch matched: Vue renders `createCommentVNode("v-if")`.
            match &**alternate {
                JsNode::Comment(text) if text == "v-if" => {}
                _ => return Err("unsupported_render_shape"),
            }
            self.anchors.push(RawAnchor::comment(
                "v-if",
                "v-if",
                head.loc.span.start,
                head.loc.span.end,
            ));
        }
        Ok(())
    }

    /// Match one element (already stripped of its `v-if` role when
    /// `in_branch` is set) to its render output node.
    fn element(
        &mut self,
        element: &ElementNode<'_>,
        in_branch: bool,
        node: &JsNode,
    ) -> Result<(), &'static str> {
        let span = element.loc.span;
        if has_directive(element, "for") {
            // `v-if` binds tighter than `v-for` on one element, so a branch
            // can still hold the whole list.
            let JsNode::List(item) = node else {
                return Err("unsupported_render_shape");
            };
            self.anchors
                .push(RawAnchor::fragment("v-for", span.start, span.end));
            if element.tag == "template" {
                return self.template_body(element, "v-for-item", item);
            }
            return self.vnode(element, item);
        }
        if element.tag == "template" && in_branch {
            return self.template_body(element, "v-if-branch", node);
        }
        self.vnode(element, node)
    }

    /// A `<template v-for>` item or `<template v-if>` branch: either one
    /// Fragment around the children, or its single child directly.
    fn template_body(
        &mut self,
        element: &ElementNode<'_>,
        origin: &'static str,
        node: &JsNode,
    ) -> Result<(), &'static str> {
        let children = element.children.iter().collect::<Vec<_>>();
        if let JsNode::Fragment(output) = node {
            self.anchors.push(RawAnchor::fragment(
                origin,
                element.loc.span.start,
                element.loc.span.end,
            ));
            return self.children(&children, output);
        }
        self.children(&children, std::slice::from_ref(node))
    }

    fn vnode(&mut self, element: &ElementNode<'_>, node: &JsNode) -> Result<(), &'static str> {
        let span = element.loc.span;
        match node {
            JsNode::Slot(fallback) if element.tag == "slot" => {
                // `renderSlot` always returns a Fragment around the supplied
                // content or, when nothing is supplied, the fallback.
                self.anchors
                    .push(RawAnchor::fragment("slot", span.start, span.end));
                let children = element.children.iter().collect::<Vec<_>>();
                self.children(&children, fallback)
            }
            JsNode::Element {
                tag,
                props,
                patch_flag,
                dynamic_props,
                children,
            } if *tag == element.tag => {
                let runtime_tag = self
                    .aliases
                    .get(element.tag)
                    .copied()
                    .unwrap_or(element.tag);
                let attributes =
                    element_attributes(element, runtime_tag, props, dynamic_props.as_deref())?;
                self.elements.push(RawElement {
                    vnode: "element",
                    tag: runtime_tag.to_owned(),
                    start: span.start,
                    end: span.end,
                    patch_flag: *patch_flag,
                    dynamic_props: dynamic_props.clone(),
                    attributes,
                });
                let template_children = element.children.iter().collect::<Vec<_>>();
                self.children(&template_children, children)
            }
            JsNode::Component {
                name,
                props,
                patch_flag,
                dynamic_props,
                slots,
            } if name
                .as_deref()
                .map_or(element.tag == "component", |name| name == element.tag) =>
            {
                let attributes = component_attributes(element, props)?;
                self.elements.push(RawElement {
                    vnode: "component",
                    tag: element.tag.to_owned(),
                    start: span.start,
                    end: span.end,
                    patch_flag: *patch_flag,
                    dynamic_props: dynamic_props.clone(),
                    attributes,
                });
                self.slots(element, slots)
            }
            _ => Err("unsupported_render_shape"),
        }
    }

    /// Pair each supplied slot's content with its template group by name.
    /// Vue emits named slots before the implicit default slot, so pairing
    /// by position would be wrong.
    fn slots(
        &mut self,
        element: &ElementNode<'_>,
        slots: &[(String, Vec<JsNode>)],
    ) -> Result<(), &'static str> {
        let mut groups: Vec<(String, Vec<&TemplateChildNode<'_>>)> = Vec::new();
        let mut default = Vec::new();
        for child in element.children.iter() {
            if let TemplateChildNode::Element(template) = child
                && template.tag == "template"
                && let Some(slot) = directive(template, "slot")
            {
                let name = match slot.arg.as_ref() {
                    None => "default".to_owned(),
                    Some(ExpressionNode::Simple(arg)) if arg.is_static => arg.content.to_owned(),
                    Some(ExpressionNode::Simple(arg)) => {
                        quoted_literal(arg.content).ok_or("unsupported_render_shape")?
                    }
                    Some(_) => return Err("unsupported_render_shape"),
                };
                groups.push((name, template.children.iter().collect()));
            } else {
                default.push(child);
            }
        }
        groups.push(("default".to_owned(), default));
        let mut matched = vec![false; groups.len()];
        for (name, output) in slots {
            let index = groups
                .iter()
                .position(|(group, _)| group == name)
                .ok_or("unsupported_render_shape")?;
            if matched[index] {
                return Err("unsupported_render_shape");
            }
            matched[index] = true;
            self.children(&groups[index].1, output)?;
        }
        // A group the render dropped may hold only text (for example the
        // whitespace around named slot templates).
        for (index, (_, children)) in groups.iter().enumerate() {
            if !matched[index] && !units(children)?.is_empty() {
                return Err("unsupported_render_shape");
            }
        }
        Ok(())
    }
}

/// The text of a `'name'` or `"name"` literal with no escapes or quotes
/// inside, which is the only dynamic slot name form a plan accepts.
fn quoted_literal(content: &str) -> Option<String> {
    let content = content.trim();
    let quote = content
        .chars()
        .next()
        .filter(|quote| matches!(quote, '\'' | '"'))?;
    let inner = content.strip_prefix(quote)?.strip_suffix(quote)?;
    (!inner.contains(['\\', '\'', '"'])).then(|| inner.to_owned())
}

/// Group template children into render units, dropping text and comments.
fn units<'t, 'a>(
    children: &[&'t TemplateChildNode<'a>],
) -> Result<Vec<Unit<'t, 'a>>, &'static str> {
    let mut output: Vec<Unit<'t, 'a>> = Vec::new();
    for child in children {
        match child {
            TemplateChildNode::Text(_)
            | TemplateChildNode::Interpolation(_)
            | TemplateChildNode::Comment(_) => {}
            TemplateChildNode::Element(element) => {
                let element: &'t ElementNode<'a> = element;
                if has_directive(element, "if") {
                    output.push(Unit::Chain(vec![element]));
                } else if has_directive(element, "else-if") || has_directive(element, "else") {
                    match output.last_mut() {
                        Some(Unit::Chain(branches))
                            if !branches
                                .last()
                                .is_some_and(|last| has_directive(last, "else")) =>
                        {
                            branches.push(element);
                        }
                        _ => return Err("unsupported_render_shape"),
                    }
                } else {
                    output.push(Unit::Element(element));
                }
            }
            // A transformed tree (If/For nodes) means the template came
            // through a different compiler stage than this walk expects.
            _ => return Err("unsupported_render_shape"),
        }
    }
    Ok(output)
}

// ---------------------------------------------------------------------------
// Attribute classification
// ---------------------------------------------------------------------------

/// Vue's `isOn`: `on` followed by a character outside `a`-`z`.
fn is_on(key: &str) -> bool {
    let bytes = key.as_bytes();
    bytes.len() > 2 && bytes[0] == b'o' && bytes[1] == b'n' && !bytes[2].is_ascii_lowercase()
}

/// Vue's `isReservedProp`, including the empty key.
fn is_reserved(key: &str) -> bool {
    matches!(
        key,
        "" | "key"
            | "ref"
            | "ref_for"
            | "ref_key"
            | "onVnodeBeforeMount"
            | "onVnodeMounted"
            | "onVnodeBeforeUpdate"
            | "onVnodeUpdated"
            | "onVnodeBeforeUnmount"
            | "onVnodeUnmounted"
    )
}

fn camelize(value: &str) -> String {
    let mut output = String::with_capacity(value.len());
    let mut upper = false;
    for character in value.chars() {
        if character == '-' {
            upper = true;
        } else if upper {
            output.extend(character.to_uppercase());
            upper = false;
        } else {
            output.push(character);
        }
    }
    output
}

/// How one authored prop reaches the vnode, before hydration rules apply.
struct PropShape {
    kind: &'static str,
    name: Option<String>,
    prop_key: Option<String>,
}

/// Directives that change structure or scope and never become a prop.
const STRUCTURAL_DIRECTIVES: [&str; 9] = [
    "if", "else-if", "else", "for", "slot", "once", "memo", "pre", "cloak",
];

/// The marker the compiler adds for dynamic `v-model` inputs; the Citry
/// runtime removes it from the props before Vue sees them.
const MODEL_SITE_MARKER: &str = "__citryInputModelSite";

fn prop_shape(prop: &PropNode<'_>) -> PropShape {
    match prop {
        PropNode::Attribute(attribute) => {
            let name = attribute.name.to_owned();
            let kind = if is_reserved(&name) {
                "reserved"
            } else {
                "static"
            };
            PropShape {
                kind,
                name: Some(name.clone()),
                prop_key: Some(name),
            }
        }
        PropNode::Directive(directive) => {
            let argument = match directive.arg.as_ref() {
                Some(ExpressionNode::Simple(arg)) if arg.is_static => Some(arg.content.to_owned()),
                _ => None,
            };
            let dynamic_argument = directive.arg.is_some() && argument.is_none();
            let has_modifier = |name: &str| {
                directive
                    .modifiers
                    .iter()
                    .any(|modifier| modifier.content == name)
            };
            let shape = |kind, prop_key| PropShape {
                kind,
                name: argument.clone(),
                prop_key,
            };
            match directive.name {
                name if STRUCTURAL_DIRECTIVES.contains(&name) => shape("structural", None),
                // `@vue:mounted` and `@vnode-*` become reserved
                // `onVnode*` hooks, which never reach the DOM.
                "on" if argument
                    .as_deref()
                    .is_some_and(|name| name.starts_with("vue:") || name.starts_with("vnode-")) =>
                {
                    shape("reserved", None)
                }
                "on" => shape("listener", None),
                "model" => shape("model", None),
                "show" => shape("show", None),
                "html" => shape("content", Some("innerHTML".to_owned())),
                "text" => shape("content", Some("textContent".to_owned())),
                "bind" if directive.arg.is_none() => shape("spread", None),
                // Every key a dynamic `.prop` name produces starts with `.`,
                // which hydration always patches.
                "bind" if dynamic_argument && has_modifier("prop") => shape("prop", None),
                "bind" if dynamic_argument => shape("dynamic-name", None),
                "bind" => {
                    let raw = argument.clone().unwrap_or_default();
                    let base = if has_modifier("camel") {
                        camelize(&raw)
                    } else {
                        raw.clone()
                    };
                    if raw == MODEL_SITE_MARKER {
                        shape("compiler", None)
                    } else if has_modifier("prop") {
                        shape("prop", Some(format!(".{base}")))
                    } else if has_modifier("attr") {
                        shape("attr", Some(format!("^{base}")))
                    } else if is_reserved(&base) {
                        shape("reserved", Some(base))
                    } else if base == "class" || base == "style" {
                        shape(if base == "class" { "class" } else { "style" }, Some(base))
                    } else {
                        shape("bind", Some(base))
                    }
                }
                _ => shape("directive", None),
            }
        }
    }
}

fn prop_span(prop: &PropNode<'_>) -> (u32, u32) {
    match prop {
        PropNode::Attribute(attribute) => (attribute.loc.span.start, attribute.loc.span.end),
        PropNode::Directive(directive) => (directive.loc.span.start, directive.loc.span.end),
    }
}

/// Classify a native element's attributes with the rules Vue 3.5.42's
/// `hydrateElement` applies (`runtime-core` `hydration.ts`): a prop is
/// patched when it is a listener, a `.prop` binding, `value`/`indeterminate`
/// on `input`/`option`, any non-reserved prop of a custom element, or listed
/// in the vnode's `dynamicProps`. Every other rendered prop is only compared.
fn element_attributes(
    element: &ElementNode<'_>,
    runtime_tag: &str,
    props: &JsProps,
    dynamic_props: Option<&[String]>,
) -> Result<Vec<RawAttribute>, &'static str> {
    let force_value = matches!(runtime_tag, "input" | "option");
    let custom_element = runtime_tag.contains('-');
    let patched = |key: &str| {
        key.starts_with('.')
            || (is_on(key) && !is_reserved(key))
            || (force_value && (key.ends_with("value") || key == "indeterminate"))
            || (custom_element && !is_reserved(key))
            || dynamic_props.is_some_and(|keys| keys.iter().any(|item| item == key))
    };
    let mut attributes = Vec::new();
    for prop in element.props.iter() {
        let shape = prop_shape(prop);
        let hydration = match shape.kind {
            "structural" | "reserved" | "compiler" => "none",
            "listener" => "patched",
            // A dynamic `.prop` name: its keys are unknown but all patched.
            "prop" if shape.prop_key.is_none() => "patched",
            "model" | "show" | "directive" => "directive",
            "spread" | "dynamic-name" => {
                if custom_element {
                    "patched"
                } else {
                    "per-key"
                }
            }
            _ => {
                let key = shape.prop_key.as_deref().ok_or("attribute_key_mismatch")?;
                // The key must be one the render function actually emits,
                // or the rules above were applied to a guessed name.
                if !props.keys.iter().any(|item| item == key) {
                    return Err("attribute_key_mismatch");
                }
                if patched(key) { "patched" } else { "checked" }
            }
        };
        let (start, end) = prop_span(prop);
        attributes.push(RawAttribute {
            kind: shape.kind,
            name: shape.name,
            prop_key: shape.prop_key,
            hydration,
            start,
            end,
        });
    }
    // Every non-listener key the render marks dynamic must belong to an
    // authored attribute, so no patched prop goes unreported.
    for key in dynamic_props.unwrap_or_default() {
        if !is_on(key)
            && !attributes
                .iter()
                .any(|attribute| attribute.prop_key.as_deref() == Some(key.as_str()))
        {
            return Err("attribute_key_mismatch");
        }
    }
    Ok(attributes)
}

/// A component's attributes are its props and fallthrough attributes; the
/// child component's own root element decides how they hydrate.
fn component_attributes(
    element: &ElementNode<'_>,
    props: &JsProps,
) -> Result<Vec<RawAttribute>, &'static str> {
    let mut attributes = Vec::new();
    for prop in element.props.iter() {
        let mut shape = prop_shape(prop);
        // `<component :is>` consumes `is` to pick the component.
        if element.tag == "component" && shape.name.as_deref() == Some("is") {
            shape.kind = "structural";
            shape.prop_key = None;
        }
        let hydration = match shape.kind {
            "structural" | "reserved" | "compiler" => "none",
            _ => "component",
        };
        if matches!(
            shape.kind,
            "static" | "bind" | "class" | "style" | "prop" | "attr"
        ) && shape.prop_key.is_some()
            && !shape
                .prop_key
                .as_deref()
                .is_some_and(|key| props.keys.iter().any(|item| item == key))
        {
            return Err("attribute_key_mismatch");
        }
        let (start, end) = prop_span(prop);
        attributes.push(RawAttribute {
            kind: shape.kind,
            name: shape.name,
            prop_key: shape.prop_key,
            hydration,
            start,
            end,
        });
    }
    Ok(attributes)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{CompileArtifact, CompileRequest, compile};

    fn compiled(template: &str) -> CompileArtifact {
        compile(CompileRequest {
            template: template.to_owned(),
            local_calls: vec![],
            local_call_runs: vec![],
            element_bindings: vec![],
            dynamic_elements: vec![],
        })
    }

    /// Anchors as `(kind, origin, comment, opening tag text)`, so a locked
    /// expectation reads as template text rather than byte offsets.
    fn anchors(template: &str) -> Vec<(&'static str, &'static str, Option<&'static str>, String)> {
        let artifact = compiled(template);
        let plan = artifact.hydration_plan;
        assert_eq!(plan.status, HydrationPlanStatus::Complete, "{template:?}");
        plan.anchors
            .iter()
            .map(|anchor| {
                let text = if anchor.path.as_ref().is_some_and(Vec::is_empty) {
                    "<root>".to_owned()
                } else {
                    artifact.transformed_template
                        [anchor.source_start as usize..anchor.source_end as usize]
                        .to_owned()
                };
                (anchor.kind, anchor.origin, anchor.comment, text)
            })
            .collect()
    }

    /// Attributes per element as `(authored text, kind, prop key, hydration)`.
    type AttributeRow = (String, &'static str, Option<String>, &'static str);

    fn attributes(template: &str) -> Vec<(String, Vec<AttributeRow>)> {
        let artifact = compiled(template);
        let plan = artifact.hydration_plan;
        assert_eq!(plan.status, HydrationPlanStatus::Complete, "{template:?}");
        let source = &artifact.transformed_template;
        plan.elements
            .into_iter()
            .map(|element| {
                let rows = element
                    .attributes
                    .into_iter()
                    .map(|attribute| {
                        (
                            source[attribute.source_start as usize..attribute.source_end as usize]
                                .to_owned(),
                            attribute.kind,
                            attribute.prop_key,
                            attribute.hydration,
                        )
                    })
                    .collect();
                (format!("{} {}", element.vnode, element.tag), rows)
            })
            .collect()
    }

    fn row(
        text: &str,
        kind: &'static str,
        key: Option<&str>,
        hydration: &'static str,
    ) -> AttributeRow {
        (text.to_owned(), kind, key.map(str::to_owned), hydration)
    }

    #[test]
    fn loops_report_the_list_fragment_and_per_row_fragments_the_render_creates() {
        // A loop over elements: one list Fragment, rows are the elements.
        assert_eq!(
            anchors(
                r#"<ul><li v-for="row in $citryPrepared.rows" :key="row.id">{{ row.label }}</li></ul>"#
            ),
            [(
                "fragment",
                "v-for",
                None,
                r#"<li v-for="row in $citryPrepared.rows" :key="row.id">"#.to_owned()
            )]
        );
        // A loop over components: the same list Fragment; the component's
        // own root shape is reported by its own definition.
        assert_eq!(
            anchors(
                r#"<div><row-card v-for="row in $citryPrepared.rows" :key="row.id" :row="row"><template #title><b>t</b></template><i>body</i></row-card></div>"#
            ),
            [(
                "fragment",
                "v-for",
                None,
                r#"<row-card v-for="row in $citryPrepared.rows" :key="row.id" :row="row">"#
                    .to_owned()
            )]
        );
        // Several children per row: each row is its own Fragment.
        let multi = r#"<template v-for="row in $citryPrepared.rows"><dt>{{ row.term }}</dt><dd>{{ row.detail }}</dd></template>"#;
        let opening = r#"<template v-for="row in $citryPrepared.rows">"#.to_owned();
        assert_eq!(
            anchors(multi),
            [
                ("fragment", "v-for", None, opening.clone()),
                ("fragment", "v-for-item", None, opening.clone()),
            ]
        );
        // A keyed `<template v-for>` with one element child renders the
        // child directly, as upstream Vue does.
        assert_eq!(
            anchors(
                r#"<template v-for="row in $citryPrepared.rows" :key="row.id"><p>{{ row.label }}</p></template>"#
            ),
            [(
                "fragment",
                "v-for",
                None,
                r#"<template v-for="row in $citryPrepared.rows" :key="row.id">"#.to_owned()
            )]
        );
        // The patched compiler keeps a child that carries its own key inside
        // a per-row Fragment; the plan follows the emitted code, not the
        // upstream rule.
        assert_eq!(
            anchors(
                r#"<template v-for="row in $citryPrepared.rows"><p :key="row.id">{{ row.label }}</p></template>"#
            ),
            [
                ("fragment", "v-for", None, opening.clone()),
                ("fragment", "v-for-item", None, opening),
            ]
        );
    }

    #[test]
    fn roots_slots_and_conditionals_report_their_markers() {
        // Several roots (a multi-root component): one root Fragment.
        assert_eq!(
            anchors("<header>top</header><main>body</main>"),
            [("fragment", "root", None, "<root>".to_owned())]
        );
        // Mixed text at the root is also several root nodes.
        assert_eq!(
            anchors("only text {{ $citryPrepared.label }}"),
            [("fragment", "root", None, "<root>".to_owned())]
        );
        // An empty render returns null, which Vue renders as `<!---->`.
        assert_eq!(
            anchors(""),
            [("comment", "empty-render", Some(""), "<root>".to_owned())]
        );
        // Slot outlets always create a Fragment, with or without fallback.
        assert_eq!(
            anchors(r#"<aside><slot name="side"><p>fallback</p></slot><slot></slot></aside>"#),
            [
                ("fragment", "slot", None, r#"<slot name="side">"#.to_owned()),
                ("fragment", "slot", None, "<slot>".to_owned()),
            ]
        );
        // A chain ending in `v-else` never renders a placeholder; a chain
        // without one renders `<!--v-if-->` when no branch matches.
        assert_eq!(
            anchors(
                r#"<div><p v-if="$citryPrepared.a">a</p><p v-else-if="$citryPrepared.b">b</p><p v-else>c</p><span v-if="$citryPrepared.c">c</span></div>"#
            ),
            [(
                "comment",
                "v-if",
                Some("v-if"),
                r#"<span v-if="$citryPrepared.c">"#.to_owned()
            )]
        );
        assert_eq!(
            anchors(r#"<p v-if="$citryPrepared.a">root branch</p>"#),
            [(
                "comment",
                "v-if",
                Some("v-if"),
                r#"<p v-if="$citryPrepared.a">"#.to_owned()
            )]
        );
        // A `<template>` branch with several children is a Fragment; one
        // with a single element child renders that child directly.
        assert_eq!(
            anchors(
                r#"<div><template v-if="$citryPrepared.a"><p>1</p><p>2</p></template><template v-else><p>only</p></template></div>"#
            ),
            [(
                "fragment",
                "v-if-branch",
                None,
                r#"<template v-if="$citryPrepared.a">"#.to_owned()
            )]
        );
    }

    #[test]
    fn attributes_follow_the_hydration_patch_rules() {
        assert_eq!(
            attributes(
                r#"<ul><li v-for="row in $citryPrepared.rows" :key="row.id" class="row" :aria-expanded="row.open" @click="row.toggle">{{ row.label }}</li></ul>"#
            ),
            [
                ("element ul".to_owned(), vec![]),
                (
                    "element li".to_owned(),
                    vec![
                        row(
                            r#"v-for="row in $citryPrepared.rows""#,
                            "structural",
                            None,
                            "none"
                        ),
                        row(r#":key="row.id""#, "reserved", Some("key"), "none"),
                        row(r#"class="row""#, "static", Some("class"), "checked"),
                        row(
                            r#":aria-expanded="row.open""#,
                            "bind",
                            Some("aria-expanded"),
                            "patched"
                        ),
                        row(r#"@click="row.toggle""#, "listener", None, "patched"),
                    ]
                ),
            ]
        );
        // `v-show` makes the compiler insert a lifecycle key; that inserted
        // attribute has no authored bytes and is reported as reserved.
        let spread = attributes(
            r#"<div v-show="$citryPrepared.open" :aria-expanded="$citryPrepared.open" @click="$citryPrepared.toggle" v-bind="$citryPrepared.attrs"><b :hidden.prop="$citryPrepared.hidden" :data-mode.attr="$citryPrepared.mode" :tab-index.camel="$citryPrepared.tab" :[$citryPrepared.name]="$citryPrepared.value"></b></div>"#,
        );
        assert_eq!(spread[0].1[0].1, "reserved");
        assert!(spread[0].1[0].0.starts_with("key=\"citryReplacement"));
        assert_eq!(
            spread[0].1[1..],
            [
                row(r#"v-show="$citryPrepared.open""#, "show", None, "directive"),
                row(
                    r#":aria-expanded="$citryPrepared.open""#,
                    "bind",
                    Some("aria-expanded"),
                    "patched"
                ),
                row(
                    r#"@click="$citryPrepared.toggle""#,
                    "listener",
                    None,
                    "patched"
                ),
                row(
                    r#"v-bind="$citryPrepared.attrs""#,
                    "spread",
                    None,
                    "per-key"
                ),
            ]
        );
        assert_eq!(
            spread[1].1,
            [
                row(
                    r#":hidden.prop="$citryPrepared.hidden""#,
                    "prop",
                    Some(".hidden"),
                    "patched"
                ),
                row(
                    r#":data-mode.attr="$citryPrepared.mode""#,
                    "attr",
                    Some("^data-mode"),
                    "patched"
                ),
                row(
                    r#":tab-index.camel="$citryPrepared.tab""#,
                    "bind",
                    Some("tabIndex"),
                    "patched"
                ),
                row(
                    r#":[$citryPrepared.name]="$citryPrepared.value""#,
                    "dynamic-name",
                    None,
                    "per-key"
                ),
            ]
        );
        // `value` is always patched on `input` and `option`, even static.
        let form = attributes(
            r#"<form><input :value="$citryPrepared.text"><input type="checkbox" value="yes" :checked="$citryPrepared.on"><select><option :value="$citryPrepared.choice" selected>x</option></select></form>"#,
        );
        assert_eq!(
            form.iter()
                .map(|(element, rows)| (element.as_str(), rows.as_slice()))
                .collect::<Vec<_>>(),
            [
                ("element form", &[][..]),
                (
                    "element input",
                    &[row(
                        r#":value="$citryPrepared.text""#,
                        "bind",
                        Some("value"),
                        "patched"
                    )][..]
                ),
                (
                    "element input",
                    &[
                        row(r#"type="checkbox""#, "static", Some("type"), "checked"),
                        row(r#"value="yes""#, "static", Some("value"), "patched"),
                        row(
                            r#":checked="$citryPrepared.on""#,
                            "bind",
                            Some("checked"),
                            "patched"
                        ),
                    ][..]
                ),
                ("element select", &[][..]),
                (
                    "element option",
                    &[
                        row(
                            r#":value="$citryPrepared.choice""#,
                            "bind",
                            Some("value"),
                            "patched"
                        ),
                        row("selected", "static", Some("selected"), "checked"),
                    ][..]
                ),
            ]
        );
        // Class and style are never listed as dynamic props on elements, and
        // a constant binding is compiled as static, so all are only checked.
        assert_eq!(
            attributes(r#"<p class="a" :class="$citryPrepared.cls" style="color: red" :style="$citryPrepared.sty" :title="'constant'" data-id="7" v-text="$citryPrepared.text"></p>"#)[0].1,
            [
                row(r#"class="a""#, "static", Some("class"), "checked"),
                row(r#":class="$citryPrepared.cls""#, "class", Some("class"), "checked"),
                row(r#"style="color: red""#, "static", Some("style"), "checked"),
                row(r#":style="$citryPrepared.sty""#, "style", Some("style"), "checked"),
                row(r#":title="'constant'""#, "bind", Some("title"), "checked"),
                row(r#"data-id="7""#, "static", Some("data-id"), "checked"),
                row(r#"v-text="$citryPrepared.text""#, "content", Some("textContent"), "patched"),
            ]
        );
        // Component attributes are decided by the child's root element.
        assert_eq!(
            attributes(
                r#"<my-card v-bind="$citryPrepared.props" class="card" :title="$citryPrepared.title" @close="$citryPrepared.close"></my-card>"#
            ),
            [(
                "component my-card".to_owned(),
                vec![
                    row(
                        r#"v-bind="$citryPrepared.props""#,
                        "spread",
                        None,
                        "component"
                    ),
                    row(r#"class="card""#, "static", Some("class"), "component"),
                    row(
                        r#":title="$citryPrepared.title""#,
                        "bind",
                        Some("title"),
                        "component"
                    ),
                    row(
                        r#"@close="$citryPrepared.close""#,
                        "listener",
                        None,
                        "component"
                    ),
                ]
            )]
        );
    }

    #[test]
    fn model_inputs_report_the_directive_and_the_compiler_marker() {
        let artifact = compiled(
            r#"<input v-model="$citryPrepared.model"><input :type="$citryPrepared.kind" v-model="$citryPrepared.model">"#,
        );
        let plan = artifact.hydration_plan;
        assert_eq!(plan.status, HydrationPlanStatus::Complete);
        let dynamic = &plan.elements[1];
        let kinds = dynamic
            .attributes
            .iter()
            .map(|attribute| {
                (
                    attribute.kind,
                    attribute.hydration,
                    attribute.original_start.is_some(),
                )
            })
            .collect::<Vec<_>>();
        // The dynamic-type model gets a lifecycle key and the model-site
        // marker; neither has authored bytes nor reaches the DOM.
        assert_eq!(
            kinds,
            [
                ("reserved", "none", false),
                // A dynamic `:type` is a dynamic prop, so hydration patches it.
                ("bind", "patched", true),
                ("model", "directive", true),
                ("compiler", "none", false),
            ]
        );
    }

    #[test]
    fn positions_map_to_compiler_input_bytes_and_element_paths() {
        let template = r#"<section><p v-show="$citryPrepared.open">é</p><template v-for="item in $citryPrepared.items"><b>1</b><i>2</i></template></section>"#;
        let artifact = compiled(template);
        let plan = &artifact.hydration_plan;
        assert_eq!(plan.status, HydrationPlanStatus::Complete);
        // `v-show` inserted a key before the loop, so transformed and
        // original offsets differ for everything after it.
        assert_ne!(artifact.transformed_template, template);
        let loop_start = template.find("<template").unwrap() as u32;
        for anchor in &plan.anchors {
            assert_eq!(anchor.original_start, Some(loop_start));
            assert_eq!(
                &template[anchor.original_start.unwrap() as usize
                    ..anchor.original_end.unwrap() as usize],
                r#"<template v-for="item in $citryPrepared.items">"#
            );
            let element = artifact
                .elements
                .iter()
                .find(|element| element.source_start == loop_start)
                .unwrap();
            assert_eq!(anchor.path.as_ref(), Some(&element.path));
        }
        // Every element maps back to the element walk's path.
        for element in &plan.elements {
            let start = element.original_start.unwrap();
            let expected = artifact
                .elements
                .iter()
                .find(|item| item.source_start == start)
                .unwrap();
            assert_eq!(element.path.as_ref(), Some(&expected.path));
        }
        // An authored attribute maps to its exact bytes in the input.
        let show = &plan.elements[1].attributes[1];
        assert_eq!(
            &template[show.original_start.unwrap() as usize..show.original_end.unwrap() as usize],
            r#"v-show="$citryPrepared.open""#
        );
    }

    #[test]
    fn parser_implied_table_elements_have_paths_but_no_compiler_input_span() {
        // The parser adds a `tbody` around the direct row and a `tr` around
        // the direct cell; the render creates both, and neither was authored.
        let template = r#"<div><table><tr><td>a</td></tr></table><table><tbody><td>b</td></tbody></table><table><td>c</td></table></div>"#;
        let artifact = compiled(template);
        let plan = &artifact.hydration_plan;
        assert_eq!(plan.status, HydrationPlanStatus::Complete);
        let tags = plan
            .elements
            .iter()
            .map(|element| (element.tag.as_str(), element.original_start.is_some()))
            .collect::<Vec<_>>();
        assert_eq!(
            tags,
            [
                ("div", true),
                ("table", true),
                ("tbody", false),
                ("tr", true),
                ("td", true),
                ("table", true),
                ("tbody", true),
                ("tr", false),
                ("td", true),
                ("table", true),
                ("tbody", false),
                ("tr", false),
                ("td", true),
            ]
        );
        // The last table implies a `tbody` and a `tr` at one offset; each
        // still gets its own path, the one the element walk recorded.
        let expected_paths = artifact
            .elements
            .iter()
            .map(|element| Some(element.path.clone()))
            .collect::<Vec<_>>();
        let paths = plan
            .elements
            .iter()
            .map(|element| element.path.clone())
            .collect::<Vec<_>>();
        assert_eq!(paths, expected_paths);
        for element in &plan.elements {
            // Every compiler-input position is an opening tag, which the
            // Python validator requires.
            if let Some(start) = element.original_start {
                assert_eq!(&template[start as usize..start as usize + 1], "<");
            } else {
                assert_eq!(element.original_end, None);
            }
        }
    }

    #[test]
    fn dynamic_element_aliases_are_classified_with_their_declared_tag() {
        let template = r#"<citry-dynamic-a1 :value="$citryPrepared.v"></citry-dynamic-a1>"#;
        let artifact = compile(CompileRequest {
            template: template.to_owned(),
            local_calls: vec![],
            local_call_runs: vec![],
            element_bindings: vec![],
            dynamic_elements: vec![DynamicElement {
                alias: "citry-dynamic-a1".to_owned(),
                tag: "input".to_owned(),
                source_start: 0,
                source_end: 44,
            }],
        });
        assert!(
            artifact.diagnostics.is_empty(),
            "{:?}",
            artifact.diagnostics
        );
        let plan = artifact.hydration_plan;
        assert_eq!(plan.status, HydrationPlanStatus::Complete);
        assert_eq!(plan.elements[0].tag, "input");
        assert_eq!(plan.elements[0].attributes[0].hydration, "patched");
    }

    #[test]
    fn an_element_spanning_the_whole_template_is_not_the_root() {
        // Each opening tag here is the entire template, so only an explicit
        // root marker can tell the construct apart from the template root.
        for (template, origin) in [
            (
                r#"<my-card v-for="x in $citryPrepared.xs" :key="x" />"#,
                "v-for",
            ),
            ("<slot/>", "slot"),
            (r#"<input v-if="$citryPrepared.a">"#, "v-if"),
        ] {
            let artifact = compiled(template);
            let plan = artifact.hydration_plan;
            assert_eq!(plan.status, HydrationPlanStatus::Complete, "{template:?}");
            assert_eq!(plan.anchors.len(), 1, "{template:?}");
            let anchor = &plan.anchors[0];
            assert_eq!(anchor.origin, origin);
            assert_eq!(anchor.path.as_ref(), Some(&artifact.elements[0].path));
            assert!(!artifact.elements[0].path.is_empty());
        }
    }

    #[test]
    fn vnode_hooks_and_dynamic_prop_names_are_classified_by_their_keys() {
        let rows = attributes(
            r#"<b @vue:mounted="$citryPrepared.m" :[$citryPrepared.n].prop="$citryPrepared.v"></b>"#,
        );
        assert_eq!(
            rows[0].1,
            [
                row(
                    r#"@vue:mounted="$citryPrepared.m""#,
                    "reserved",
                    None,
                    "none"
                ),
                row(
                    r#":[$citryPrepared.n].prop="$citryPrepared.v""#,
                    "prop",
                    None,
                    "patched"
                ),
            ]
        );
    }

    #[test]
    fn unsupported_shapes_report_no_partial_facts() {
        // Conditional slots compile to `createSlots`, which the plan does
        // not read (and the helper audit already rejects).
        let artifact = compiled(
            r#"<my-card><template v-if="$citryPrepared.a" #head><b>h</b></template></my-card>"#,
        );
        let plan = artifact.hydration_plan;
        assert_eq!(plan.status, HydrationPlanStatus::Unsupported);
        assert_eq!(plan.reason_code, Some("unsupported_render_shape"));
        assert!(plan.anchors.is_empty() && plan.elements.is_empty());
    }

    #[test]
    fn the_plan_serializes_deterministically_with_the_documented_shape() {
        let template = r#"<ul><li v-for="row in $citryPrepared.rows" :key="row.id" :aria-expanded="row.open">{{ row.label }}</li></ul><p v-if="$citryPrepared.a">a</p>"#;
        let first = serde_json::to_value(&compiled(template).hydration_plan).unwrap();
        let second = serde_json::to_value(&compiled(template).hydration_plan).unwrap();
        assert_eq!(first, second);
        assert_eq!(
            first,
            serde_json::json!({
                "source": "transformedTemplate",
                "sourceSha256": hash(template),
                "originalSourceSha256": hash(template),
                "status": "complete",
                "anchors": [
                    {"kind": "fragment", "origin": "root", "sourceStart": 0, "sourceEnd": 140,
                     "originalStart": 0, "originalEnd": 140, "path": []},
                    {"kind": "fragment", "origin": "v-for", "sourceStart": 4, "sourceEnd": 83,
                     "originalStart": 4, "originalEnd": 83, "path": ["i:0:756c", "i:0:6c69"]},
                    {"kind": "comment", "origin": "v-if", "comment": "v-if", "sourceStart": 108,
                     "sourceEnd": 135, "originalStart": 108, "originalEnd": 135, "path": ["i:1:70"]},
                ],
                "elements": [
                    {"vnode": "element", "tag": "ul", "sourceStart": 0, "sourceEnd": 4,
                     "originalStart": 0, "originalEnd": 4, "path": ["i:0:756c"], "patchFlag": 0,
                     "dynamicProps": null, "attributes": []},
                    {"vnode": "element", "tag": "li", "sourceStart": 4, "sourceEnd": 83,
                     "originalStart": 4, "originalEnd": 83, "path": ["i:0:756c", "i:0:6c69"],
                     "patchFlag": 9, "dynamicProps": ["aria-expanded"], "attributes": [
                        {"kind": "structural", "name": null, "propKey": null, "hydration": "none",
                         "sourceStart": 8, "sourceEnd": 42, "originalStart": 8, "originalEnd": 42},
                        {"kind": "reserved", "name": "key", "propKey": "key", "hydration": "none",
                         "sourceStart": 43, "sourceEnd": 56, "originalStart": 43, "originalEnd": 56},
                        {"kind": "bind", "name": "aria-expanded", "propKey": "aria-expanded",
                         "hydration": "patched", "sourceStart": 57, "sourceEnd": 82,
                         "originalStart": 57, "originalEnd": 82},
                    ]},
                    {"vnode": "element", "tag": "p", "sourceStart": 108, "sourceEnd": 135,
                     "originalStart": 108, "originalEnd": 135, "path": ["i:1:70"], "patchFlag": 0,
                     "dynamicProps": null, "attributes": [
                        {"kind": "structural", "name": null, "propKey": null, "hydration": "none",
                         "sourceStart": 111, "sourceEnd": 134, "originalStart": 111, "originalEnd": 134},
                    ]},
                ],
            })
        );
    }
}
