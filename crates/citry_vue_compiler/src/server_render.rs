//! Server HTML that Vue adopts in the browser, written by running the
//! compiled render functions against the page's prepared data.
//!
//! When a page hydrates, Vue walks the server's HTML beside the vnodes its
//! own render functions create and adopts each DOM node instead of building
//! it. Every comment marker, element, attribute and text node must therefore
//! be exactly what Vue's first client render produces. Citry already sends
//! the browser each component's compiled render function and the data it
//! reads (`$citryPrepared`, the instance property that exposes each
//! occurrence's `preparedData`, and the `js_data` values in `serverData`). This
//! module reads each render function once into a small program and, per
//! request, runs those programs over the same data on the server, writing
//! what Vue would create:
//!
//! - elements with the attributes Vue's client render sets, including the
//!   values Python computed (`true` becomes `"true"` on a custom attribute,
//!   `checked` becomes a boolean attribute);
//! - `<!--[-->`/`<!--]-->` around every Fragment (lists, slots, multi-root
//!   renders) and `<!--v-if-->`/`<!---->` placeholders;
//! - text exactly as the compiled render emits it, so whitespace is what the
//!   compiler decided for each piece of text inside its real ancestors;
//! - HTML Python hands over as a finished string (`<c-raw>`, trusted
//!   `Markup`) unchanged between Fragment comments, which Vue adopts as one
//!   static vnode.
//!
//! Some values exist only in the browser: component state from `data()` or
//! `setup()`, injected values, event handlers. A value that hydration sets
//! itself (an event listener, a key the render marks as dynamic, `value` on
//! an input, `v-show`) is left out. Any other browser-only value, or a
//! construct this module does not evaluate, makes the nearest enclosing
//! element a "shell": it is written with `data-allow-mismatch="children"`
//! and Vue builds its contents in the browser inside the same app. The shell
//! carries HTML for those contents written from the values the server has
//! ([`StaticWriter`]) until the browser runtime removes it right before Vue
//! hydrates. With no enclosing element, the page mounts in the browser
//! instead.
//!
//! The browser's parser must then keep every written node where it was
//! written. The writer records its tags, texts and comments as a token
//! stream, and [`tokens_nest_in_browser`] checks it against html5ever
//! answers stored per list of open elements, so a request only pays for
//! parsing the element nestings it has not met before. When that check
//! cannot show the page is kept as written (an attribute outside the
//! checked rules, or a nesting the parser repairs),
//! the page is written again with its expected nodes and the whole HTML is
//! parsed with html5ever in the host's `div` context
//! ([`browser_fragment_matches_nodes`]), whose answer is final.
//!
//! `docs/design/vue_ssr_selected_tree_plan.md` lists the render code this
//! module runs. When you change what this module reads or writes, update
//! that list and run `scripts/vue_render_parity/check.py`: it renders every
//! page the non-browser Python tests prepare with this module and with
//! Vue's own `renderToString`, and compares the HTML.

use std::borrow::Cow;
use std::cell::Cell;
use std::collections::HashMap;
use std::rc::Rc;
use std::sync::LazyLock;

use citry_html_transform::{
    ExpectedNodeEvent, NestingToken, StaticHtmlUse, browser_fragment_matches_nodes,
    static_html_in_context, tokens_nest_in_browser,
};
use oxc_allocator::Allocator as OxcAllocator;
use oxc_ast::ast::{
    Argument, ArrayExpressionElement, ArrowFunctionBody, BinaryOperator, BindingPattern,
    Expression, LogicalOperator, ObjectPropertyKind, PropertyKey, PropertyKind, Statement,
    UnaryOperator,
};
use oxc_parser::Parser;
use oxc_span::SourceType;
use serde::Deserialize;
use serde_json::Value as Json;

// ---------------------------------------------------------------------------
// Programs: one compiled render function, read once per definition
// ---------------------------------------------------------------------------

/// One compiled render function, read into the shapes the server can run.
///
/// Built once per compiled definition. Parts the reader does not recognize
/// become [`Node::Unsupported`] so the rest of the render still runs; at
/// request time such a part turns its enclosing element into a shell.
#[derive(Debug)]
pub struct ServerRenderProgram {
    root: Node,
}

impl ServerRenderProgram {
    /// Whether the whole render function was read (used by tests and
    /// diagnostics; a partly read program is still usable).
    pub fn fully_supported(&self) -> bool {
        self.root.fully_supported()
    }
}

#[derive(Debug)]
enum Node {
    /// `return null`: Vue renders an empty comment in its place.
    Null,
    Element {
        tag: String,
        props: Option<PropsExpr>,
        dynamic_props: Option<Vec<String>>,
        children: Children,
        directives: Directives,
    },
    Component {
        tag: String,
        props: Option<PropsExpr>,
        slots: Result<Vec<SlotDef>, &'static str>,
    },
    Fragment(Vec<Node>),
    /// `Fragment(renderList(source, (item, index) => node))`.
    List {
        source: Expr,
        params: Vec<String>,
        item: Box<Node>,
    },
    /// One `v-if` step: the test, its branch, and what follows it.
    Cond {
        test: Expr,
        then: Box<Node>,
        otherwise: Box<Node>,
    },
    Comment(String),
    Text(Expr),
    /// `renderSlot($slots, name, props, fallback)`.
    Slot {
        name: String,
        fallback: Option<Vec<Node>>,
    },
    Unsupported(&'static str),
}

impl Node {
    fn fully_supported(&self) -> bool {
        match self {
            Node::Unsupported(_) => false,
            Node::Element {
                props,
                children,
                directives,
                ..
            } => {
                props.as_ref().is_none_or(PropsExpr::fully_supported)
                    && !matches!(directives, Directives::Unsupported(_))
                    && match children {
                        Children::None => true,
                        Children::Text(expr) => expr.fully_supported(),
                        Children::Nodes(nodes) => nodes.iter().all(Node::fully_supported),
                    }
            }
            Node::Component { props, slots, .. } => {
                props.as_ref().is_none_or(PropsExpr::fully_supported)
                    && slots.as_ref().is_ok_and(|slots| {
                        slots
                            .iter()
                            .all(|slot| slot.body.iter().all(Node::fully_supported))
                    })
            }
            Node::Fragment(nodes) => nodes.iter().all(Node::fully_supported),
            Node::List { source, item, .. } => source.fully_supported() && item.fully_supported(),
            Node::Cond {
                test,
                then,
                otherwise,
            } => test.fully_supported() && then.fully_supported() && otherwise.fully_supported(),
            Node::Text(expr) => expr.fully_supported(),
            Node::Slot { fallback, .. } => fallback
                .as_ref()
                .is_none_or(|nodes| nodes.iter().all(Node::fully_supported)),
            Node::Null | Node::Comment(_) => true,
        }
    }
}

#[derive(Debug)]
enum Children {
    None,
    /// Text-only children, passed to the vnode as one string.
    Text(Expr),
    Nodes(Vec<Node>),
}

#[derive(Debug)]
enum Directives {
    None,
    /// `withDirectives(vnode, [[vShow, value]])`.
    Show(Expr),
    Unsupported(&'static str),
}

#[derive(Debug)]
struct SlotDef {
    name: String,
    /// Number of slot-prop parameters; scoped slots are not evaluated.
    params: usize,
    body: Vec<Node>,
}

/// A props argument: an object literal, a data object spread with `v-bind`,
/// or Vue's helpers that merge and normalize them.
#[derive(Debug)]
enum PropsExpr {
    Object(Vec<PropEntry>),
    Merge(Vec<PropsExpr>),
    /// `normalizeProps(...)` / `guardReactiveProps(...)`.
    Normalize(Box<PropsExpr>),
    Spread(Expr),
    Unsupported(&'static str),
}

impl PropsExpr {
    fn fully_supported(&self) -> bool {
        match self {
            PropsExpr::Object(entries) => entries.iter().all(|entry| match &entry.value {
                PropValue::Value(expr) => expr.fully_supported(),
                PropValue::Listener => true,
            }),
            PropsExpr::Merge(items) => items.iter().all(PropsExpr::fully_supported),
            PropsExpr::Normalize(inner) => inner.fully_supported(),
            PropsExpr::Spread(expr) => expr.fully_supported(),
            PropsExpr::Unsupported(_) => false,
        }
    }
}

#[derive(Debug)]
struct PropEntry {
    key: String,
    value: PropValue,
}

#[derive(Debug)]
enum PropValue {
    Value(Expr),
    /// An `on*` key. Its function is never evaluated: hydration attaches it.
    Listener,
}

#[derive(Debug)]
enum Expr {
    Undefined,
    Null,
    Bool(bool),
    Num(f64),
    Str(String),
    /// The component instance (`_ctx`).
    Ctx,
    /// A `renderList` or slot parameter.
    Local(String),
    Member(Box<Expr>, String),
    Not(Box<Expr>),
    StrictEq(Box<Expr>, Box<Expr>, bool),
    Add(Box<Expr>, Box<Expr>),
    And(Box<Expr>, Box<Expr>),
    Or(Box<Expr>, Box<Expr>),
    Cond(Box<Expr>, Box<Expr>, Box<Expr>),
    /// `toDisplayString(value)`.
    Display(Box<Expr>),
    /// `normalizeClass(value)` for a `:class` binding.
    NormalizeClass(Box<Expr>),
    /// `normalizeStyle(value)` for a `:style` binding.
    NormalizeStyle(Box<Expr>),
    /// An array literal, such as the `["card", { open: isOpen }]` Vue
    /// compiles a static `class` beside a `:class` binding into.
    Array(Vec<Expr>),
    /// An object literal, such as `{ open: isOpen }` in a `:class` or the
    /// `{"color":"red"}` a static `style` compiles to. Keys stay in source
    /// order; [`js_object_order`] puts them in JavaScript's order.
    Object(Vec<(String, Expr)>),
    Unsupported(&'static str),
}

impl Expr {
    fn fully_supported(&self) -> bool {
        match self {
            Expr::Unsupported(_) => false,
            Expr::Member(object, _)
            | Expr::Not(object)
            | Expr::Display(object)
            | Expr::NormalizeClass(object)
            | Expr::NormalizeStyle(object) => object.fully_supported(),
            Expr::StrictEq(left, right, _)
            | Expr::Add(left, right)
            | Expr::And(left, right)
            | Expr::Or(left, right) => left.fully_supported() && right.fully_supported(),
            Expr::Cond(test, then, otherwise) => {
                test.fully_supported() && then.fully_supported() && otherwise.fully_supported()
            }
            Expr::Array(items) => items.iter().all(Expr::fully_supported),
            Expr::Object(entries) => entries.iter().all(|(_, value)| value.fully_supported()),
            _ => true,
        }
    }
}

/// Read one compiled render function (`code` as the native compiler emits
/// it) into a program. `dynamic_elements` maps the compiler's tag aliases
/// for `<component :is>` elements back to their real tags.
pub fn read_program(
    code: &str,
    dynamic_elements: &[(String, String)],
) -> Result<ServerRenderProgram, &'static str> {
    let allocator = OxcAllocator::default();
    let parsed = Parser::new(&allocator, code, SourceType::default()).parse();
    if !parsed.diagnostics.is_empty() {
        return Err("render-parse");
    }
    let mut components = HashMap::new();
    let mut ctx_name = None;
    let mut returned = None;
    for statement in &parsed.program.body {
        let Statement::FunctionDeclaration(function) = statement else {
            continue;
        };
        if function.id.as_ref().is_none_or(|id| id.name != "render") {
            continue;
        }
        // The first parameter is the component instance; every template
        // reference reads through it (`prefixIdentifiers`).
        ctx_name = match function.params.items.first().map(|param| &param.pattern) {
            Some(BindingPattern::BindingIdentifier(id)) => Some(id.name.to_string()),
            _ => return Err("render-shape"),
        };
        let body = function.body.as_ref().ok_or("render-shape")?;
        for statement in &body.statements {
            match statement {
                Statement::VariableDeclaration(declaration) => {
                    for declarator in &declaration.declarations {
                        let BindingPattern::BindingIdentifier(id) = &declarator.id else {
                            return Err("render-shape");
                        };
                        // `const _component_x = _resolveComponent("x")`.
                        match &declarator.init {
                            Some(Expression::CallExpression(call))
                                if callee(&call.callee) == Some("_resolveComponent") =>
                            {
                                let Some(Argument::StringLiteral(tag)) = call.arguments.first()
                                else {
                                    return Err("render-shape");
                                };
                                components.insert(id.name.to_string(), tag.value.to_string());
                            }
                            // Custom directives resolve here; reading them
                            // is left to the element that uses them.
                            Some(Expression::CallExpression(call))
                                if callee(&call.callee) == Some("_resolveDirective") => {}
                            _ => return Err("render-shape"),
                        }
                    }
                }
                Statement::ReturnStatement(statement) => {
                    returned = statement.argument.as_ref();
                }
                _ => return Err("render-shape"),
            }
        }
    }
    let ctx_name = ctx_name.ok_or("render-shape")?;
    let returned = returned.ok_or("render-shape")?;
    let reader = Reader {
        components,
        ctx_name,
        aliases: dynamic_elements.iter().cloned().collect(),
        depth: Cell::new(0),
    };
    let root = match strip(returned) {
        Expression::NullLiteral(_) => Node::Null,
        other => reader.node(other, &[]),
    };
    Ok(ServerRenderProgram { root })
}

fn callee<'a>(expression: &Expression<'a>) -> Option<&'a str> {
    match expression {
        Expression::Identifier(id) => Some(id.name.as_str()),
        _ => None,
    }
}

/// Skip parentheses and `(_openBlock(), vnode)`: the block call only records
/// dynamic children, and the last expression is the vnode.
fn strip<'b, 'a>(mut expression: &'b Expression<'a>) -> &'b Expression<'a> {
    loop {
        match expression {
            Expression::ParenthesizedExpression(inner) => expression = &inner.expression,
            Expression::SequenceExpression(sequence) => match sequence.expressions.last() {
                Some(last) => expression = last,
                None => return expression,
            },
            _ => return expression,
        }
    }
}

fn argument<'b, 'a>(arguments: &'b [Argument<'a>], index: usize) -> Option<&'b Expression<'a>> {
    arguments.get(index).and_then(Argument::as_expression)
}

fn is_listener_key(key: &str) -> bool {
    // Vue's `isOn`: `on` followed by anything but a lowercase ASCII letter.
    let bytes = key.as_bytes();
    bytes.len() > 2 && bytes[0] == b'o' && bytes[1] == b'n' && !bytes[2].is_ascii_lowercase()
}

struct Reader {
    components: HashMap<String, String>,
    ctx_name: String,
    aliases: HashMap<String, String>,
    /// How deep the reader is in nested vnode and expression calls.
    depth: Cell<usize>,
}

/// Deeper render code (a long chain of interpolations or `v-else-if`
/// branches) is left unread, so neither reading nor running a program can
/// overflow a thread's stack; the part is built in the browser.
const MAX_READ_DEPTH: usize = 200;

impl Reader {
    /// Read one vnode-producing expression. `locals` are the parameters of
    /// the enclosing `renderList` and slot functions, innermost last.
    fn node(&self, expression: &Expression<'_>, locals: &[String]) -> Node {
        if self.depth.get() >= MAX_READ_DEPTH {
            return Node::Unsupported("nesting-depth");
        }
        self.depth.set(self.depth.get() + 1);
        let node = self.read_node(expression, locals);
        self.depth.set(self.depth.get() - 1);
        node
    }

    fn read_node(&self, expression: &Expression<'_>, locals: &[String]) -> Node {
        let expression = strip(expression);
        match expression {
            Expression::ConditionalExpression(conditional) => Node::Cond {
                test: self.expr(&conditional.test, locals),
                then: Box::new(self.node(&conditional.consequent, locals)),
                otherwise: Box::new(self.node(&conditional.alternate, locals)),
            },
            Expression::CallExpression(call) => {
                let Some(name) = callee(&call.callee) else {
                    return Node::Unsupported("render-shape");
                };
                let arguments = call.arguments.as_slice();
                match name {
                    "_withDirectives" => self.directives(arguments, locals),
                    "_createElementVNode"
                    | "_createElementBlock"
                    | "_createVNode"
                    | "_createBlock" => self.vnode(arguments, locals, Directives::None),
                    "_createCommentVNode" => match argument(arguments, 0) {
                        Some(Expression::StringLiteral(text)) => {
                            Node::Comment(text.value.to_string())
                        }
                        None => Node::Comment(String::new()),
                        Some(_) => Node::Unsupported("render-shape"),
                    },
                    "_createTextVNode" => match argument(arguments, 0) {
                        Some(text) => Node::Text(self.expr(text, locals)),
                        None => Node::Text(Expr::Str(" ".to_owned())),
                    },
                    "_renderSlot" => self.render_slot(arguments, locals),
                    "_toDisplayString" => Node::Text(self.expr(expression, locals)),
                    _ => Node::Unsupported("render-helper"),
                }
            }
            Expression::StringLiteral(_) | Expression::BinaryExpression(_) => {
                Node::Text(self.expr(expression, locals))
            }
            _ => Node::Unsupported("render-shape"),
        }
    }

    fn directives(&self, arguments: &[Argument<'_>], locals: &[String]) -> Node {
        let Some(Expression::ArrayExpression(list)) = argument(arguments, 1).map(strip) else {
            return Node::Unsupported("render-shape");
        };
        let mut directives = Directives::None;
        for entry in &list.elements {
            let Some(Expression::ArrayExpression(entry)) = entry.as_expression().map(strip) else {
                return Node::Unsupported("render-shape");
            };
            let first = entry
                .elements
                .first()
                .and_then(ArrayExpressionElement::as_expression);
            let value = entry
                .elements
                .get(1)
                .and_then(ArrayExpressionElement::as_expression);
            // The native-control ownership marker only records, in the
            // browser, which properties Vue owns; it writes nothing into the
            // HTML, so the server can render its element as if it were absent.
            if first.and_then(callee) == Some("_directive_citry_vue_owned") {
                continue;
            }
            directives = match (first.and_then(callee), value, &directives) {
                // Only one `v-show` per element, with no argument or modifiers.
                (Some("_vShow"), Some(value), Directives::None) if entry.elements.len() == 2 => {
                    Directives::Show(self.expr(value, locals))
                }
                _ => Directives::Unsupported("unsupported-directive"),
            };
        }
        match argument(arguments, 0).map(strip) {
            Some(Expression::CallExpression(call))
                if matches!(
                    callee(&call.callee),
                    Some(
                        "_createElementVNode"
                            | "_createElementBlock"
                            | "_createVNode"
                            | "_createBlock"
                    )
                ) =>
            {
                self.vnode(&call.arguments, locals, directives)
            }
            _ => Node::Unsupported("render-shape"),
        }
    }

    fn vnode(&self, arguments: &[Argument<'_>], locals: &[String], directives: Directives) -> Node {
        let Some(tag) = argument(arguments, 0) else {
            return Node::Unsupported("render-shape");
        };
        let props = argument(arguments, 1).map(|props| self.props(props, locals));
        let dynamic_props = match argument(arguments, 4).map(strip) {
            None | Some(Expression::NullLiteral(_)) => None,
            Some(Expression::ArrayExpression(array)) => {
                let mut keys = Vec::new();
                for element in &array.elements {
                    match element {
                        ArrayExpressionElement::StringLiteral(key) => {
                            keys.push(key.value.to_string())
                        }
                        _ => return Node::Unsupported("render-shape"),
                    }
                }
                Some(keys)
            }
            Some(_) => return Node::Unsupported("render-shape"),
        };
        match strip(tag) {
            Expression::Identifier(id) if id.name == "_Fragment" => {
                if !matches!(directives, Directives::None) {
                    return Node::Unsupported("unsupported-directive");
                }
                match argument(arguments, 2).map(strip) {
                    Some(Expression::CallExpression(call))
                        if callee(&call.callee) == Some("_renderList") =>
                    {
                        self.list(&call.arguments, locals)
                    }
                    Some(Expression::ArrayExpression(array)) => {
                        Node::Fragment(self.array(&array.elements, locals))
                    }
                    _ => Node::Unsupported("render-shape"),
                }
            }
            Expression::StringLiteral(tag) => {
                let tag = self
                    .aliases
                    .get(tag.value.as_str())
                    .cloned()
                    .unwrap_or_else(|| tag.value.to_string());
                Node::Element {
                    tag,
                    props,
                    dynamic_props,
                    children: self.children(argument(arguments, 2), locals),
                    directives,
                }
            }
            Expression::Identifier(id) => match self.components.get(id.name.as_str()) {
                Some(tag) if matches!(directives, Directives::None) => Node::Component {
                    tag: tag.clone(),
                    props,
                    slots: self.slots(argument(arguments, 2), locals),
                },
                Some(_) => Node::Unsupported("unsupported-directive"),
                None => Node::Unsupported("render-shape"),
            },
            Expression::CallExpression(call)
                if callee(&call.callee) == Some("_resolveDynamicComponent") =>
            {
                // Citry passes the resolved tag as a string literal; any
                // other `:is` value is only known in the browser.
                match argument(&call.arguments, 0).map(strip) {
                    Some(Expression::StringLiteral(tag))
                        if matches!(directives, Directives::None) =>
                    {
                        Node::Component {
                            tag: tag.value.to_string(),
                            props,
                            slots: self.slots(argument(arguments, 2), locals),
                        }
                    }
                    _ => Node::Unsupported("dynamic-component"),
                }
            }
            _ => Node::Unsupported("render-shape"),
        }
    }

    fn list(&self, arguments: &[Argument<'_>], locals: &[String]) -> Node {
        let Some(source) = argument(arguments, 0) else {
            return Node::Unsupported("render-shape");
        };
        let Some(function) = argument(arguments, 1) else {
            return Node::Unsupported("render-shape");
        };
        let Some((params, body)) = arrow(function) else {
            return Node::Unsupported("render-shape");
        };
        let mut inner = locals.to_vec();
        inner.extend(params.iter().cloned());
        Node::List {
            source: self.expr(source, locals),
            params,
            item: Box::new(self.node(body, &inner)),
        }
    }

    fn array(&self, elements: &[ArrayExpressionElement<'_>], locals: &[String]) -> Vec<Node> {
        let mut nodes = Vec::with_capacity(elements.len());
        for element in elements {
            nodes.push(match element.as_expression() {
                Some(expression) => self.node(expression, locals),
                None => Node::Unsupported("render-shape"),
            });
        }
        nodes
    }

    fn children(&self, children: Option<&Expression<'_>>, locals: &[String]) -> Children {
        match children.map(strip) {
            None | Some(Expression::NullLiteral(_)) => Children::None,
            Some(Expression::ArrayExpression(array)) => {
                Children::Nodes(self.array(&array.elements, locals))
            }
            // Text-only children arrive as one string expression.
            Some(other) => Children::Text(self.expr(other, locals)),
        }
    }

    fn render_slot(&self, arguments: &[Argument<'_>], locals: &[String]) -> Node {
        // `renderSlot(_ctx.$slots, "name", props?, fallback?)`: the slots of
        // this component instance, a literal name, and ignored vnode props.
        let slots_object = argument(arguments, 0).map(strip);
        let own_slots = matches!(
            slots_object,
            Some(Expression::StaticMemberExpression(member))
                if member.property.name == "$slots"
                    && matches!(&member.object, Expression::Identifier(id) if id.name == self.ctx_name.as_str())
        );
        let Some(Expression::StringLiteral(name)) = argument(arguments, 1).map(strip) else {
            return Node::Unsupported("render-shape");
        };
        if !own_slots {
            return Node::Unsupported("render-shape");
        }
        let fallback = match argument(arguments, 3) {
            None => None,
            Some(function) => match arrow(function) {
                Some((params, body)) if params.is_empty() => match strip(body) {
                    Expression::ArrayExpression(array) => Some(self.array(&array.elements, locals)),
                    _ => return Node::Unsupported("render-shape"),
                },
                _ => return Node::Unsupported("render-shape"),
            },
        };
        Node::Slot {
            name: name.value.to_string(),
            fallback,
        }
    }

    fn slots(
        &self,
        slots: Option<&Expression<'_>>,
        locals: &[String],
    ) -> Result<Vec<SlotDef>, &'static str> {
        let object = match slots.map(strip) {
            None | Some(Expression::NullLiteral(_)) => return Ok(Vec::new()),
            Some(Expression::ObjectExpression(object)) => object,
            // `createSlots` builds conditional or looped slots at render time.
            _ => return Err("dynamic-slots"),
        };
        let mut output = Vec::new();
        for property in &object.properties {
            let ObjectPropertyKind::ObjectProperty(property) = property else {
                return Err("render-shape");
            };
            let name = property_name(&property.key, property.computed).ok_or("render-shape")?;
            // `_` is Vue's slot stability flag, not a slot.
            if name == "_" {
                continue;
            }
            let Expression::CallExpression(call) = strip(&property.value) else {
                return Err("render-shape");
            };
            if callee(&call.callee) != Some("_withCtx") {
                return Err("render-shape");
            }
            let function = argument(&call.arguments, 0).ok_or("render-shape")?;
            let (params, body) = arrow(function).ok_or("render-shape")?;
            let mut inner = locals.to_vec();
            inner.extend(params.iter().cloned());
            let Expression::ArrayExpression(array) = strip(body) else {
                return Err("render-shape");
            };
            output.push(SlotDef {
                name,
                params: params.len(),
                body: self.array(&array.elements, &inner),
            });
        }
        Ok(output)
    }

    fn props(&self, props: &Expression<'_>, locals: &[String]) -> PropsExpr {
        match strip(props) {
            Expression::NullLiteral(_) => PropsExpr::Object(Vec::new()),
            Expression::ObjectExpression(object) => {
                let mut entries = Vec::new();
                for property in &object.properties {
                    let ObjectPropertyKind::ObjectProperty(property) = property else {
                        return PropsExpr::Unsupported("render-shape");
                    };
                    let Some(key) = property_name(&property.key, property.computed) else {
                        return PropsExpr::Unsupported("dynamic-attribute-name");
                    };
                    let value = if is_listener_key(&key) {
                        PropValue::Listener
                    } else {
                        PropValue::Value(self.expr(&property.value, locals))
                    };
                    entries.push(PropEntry { key, value });
                }
                PropsExpr::Object(entries)
            }
            Expression::CallExpression(call) => match callee(&call.callee) {
                Some("_mergeProps") => PropsExpr::Merge(
                    call.arguments
                        .iter()
                        .map(|argument| match argument.as_expression() {
                            Some(expression) => self.props(expression, locals),
                            None => PropsExpr::Unsupported("render-shape"),
                        })
                        .collect(),
                ),
                Some("_normalizeProps" | "_guardReactiveProps") => {
                    match argument(&call.arguments, 0) {
                        Some(inner) if call.arguments.len() == 1 => {
                            PropsExpr::Normalize(Box::new(self.props(inner, locals)))
                        }
                        _ => PropsExpr::Unsupported("render-shape"),
                    }
                }
                // `toHandlers` and other helpers build props only the
                // browser can evaluate.
                _ => PropsExpr::Unsupported("render-helper"),
            },
            other => PropsExpr::Spread(self.expr(other, locals)),
        }
    }

    fn expr(&self, expression: &Expression<'_>, locals: &[String]) -> Expr {
        if self.depth.get() >= MAX_READ_DEPTH {
            return Expr::Unsupported("nesting-depth");
        }
        self.depth.set(self.depth.get() + 1);
        let expr = self.read_expr(expression, locals);
        self.depth.set(self.depth.get() - 1);
        expr
    }

    fn read_expr(&self, expression: &Expression<'_>, locals: &[String]) -> Expr {
        match strip(expression) {
            Expression::StringLiteral(value) => Expr::Str(value.value.to_string()),
            Expression::NumericLiteral(value) => Expr::Num(value.value),
            Expression::BooleanLiteral(value) => Expr::Bool(value.value),
            Expression::NullLiteral(_) => Expr::Null,
            Expression::Identifier(id) => {
                let name = id.name.as_str();
                if locals.iter().rev().any(|local| local == name) {
                    Expr::Local(name.to_owned())
                } else if name == self.ctx_name {
                    Expr::Ctx
                } else if name == "undefined" {
                    Expr::Undefined
                } else {
                    Expr::Unsupported("browser-value")
                }
            }
            Expression::StaticMemberExpression(member) if !member.optional => Expr::Member(
                Box::new(self.expr(&member.object, locals)),
                member.property.name.to_string(),
            ),
            Expression::ComputedMemberExpression(member) if !member.optional => {
                match strip(&member.expression) {
                    Expression::StringLiteral(key) => Expr::Member(
                        Box::new(self.expr(&member.object, locals)),
                        key.value.to_string(),
                    ),
                    _ => Expr::Unsupported("browser-value"),
                }
            }
            Expression::UnaryExpression(unary) => match unary.operator {
                UnaryOperator::LogicalNot => {
                    Expr::Not(Box::new(self.expr(&unary.argument, locals)))
                }
                UnaryOperator::Void => Expr::Undefined,
                UnaryOperator::UnaryNegation => match strip(&unary.argument) {
                    Expression::NumericLiteral(value) => Expr::Num(-value.value),
                    _ => Expr::Unsupported("browser-value"),
                },
                _ => Expr::Unsupported("browser-value"),
            },
            Expression::BinaryExpression(binary) => {
                let left = Box::new(self.expr(&binary.left, locals));
                let right = Box::new(self.expr(&binary.right, locals));
                match binary.operator {
                    BinaryOperator::StrictEquality => Expr::StrictEq(left, right, false),
                    BinaryOperator::StrictInequality => Expr::StrictEq(left, right, true),
                    BinaryOperator::Addition => Expr::Add(left, right),
                    _ => Expr::Unsupported("browser-value"),
                }
            }
            Expression::LogicalExpression(logical) => {
                let left = Box::new(self.expr(&logical.left, locals));
                let right = Box::new(self.expr(&logical.right, locals));
                match logical.operator {
                    LogicalOperator::And => Expr::And(left, right),
                    LogicalOperator::Or => Expr::Or(left, right),
                    LogicalOperator::Coalesce => Expr::Unsupported("browser-value"),
                }
            }
            Expression::ConditionalExpression(conditional) => Expr::Cond(
                Box::new(self.expr(&conditional.test, locals)),
                Box::new(self.expr(&conditional.consequent, locals)),
                Box::new(self.expr(&conditional.alternate, locals)),
            ),
            Expression::CallExpression(call)
                if callee(&call.callee) == Some("_toDisplayString") =>
            {
                match argument(&call.arguments, 0) {
                    Some(value) => Expr::Display(Box::new(self.expr(value, locals))),
                    None => Expr::Unsupported("render-shape"),
                }
            }
            Expression::CallExpression(call)
                if matches!(
                    callee(&call.callee),
                    Some("_normalizeClass" | "_normalizeStyle")
                ) && call.arguments.len() == 1 =>
            {
                let Some(value) = argument(&call.arguments, 0) else {
                    return Expr::Unsupported("render-shape");
                };
                let value = Box::new(self.expr(value, locals));
                if callee(&call.callee) == Some("_normalizeClass") {
                    Expr::NormalizeClass(value)
                } else {
                    Expr::NormalizeStyle(value)
                }
            }
            Expression::ArrayExpression(array) => {
                let mut items = Vec::with_capacity(array.elements.len());
                for element in &array.elements {
                    // A spread or a hole needs JavaScript's iteration, so
                    // the whole literal is left to the browser.
                    let Some(item) = element.as_expression() else {
                        return Expr::Unsupported("browser-value");
                    };
                    items.push(self.expr(item, locals));
                }
                Expr::Array(items)
            }
            Expression::ObjectExpression(object) => {
                let mut entries = Vec::with_capacity(object.properties.len());
                for property in &object.properties {
                    // Spreads, getters, setters and methods are left to the
                    // browser; only `key: value` entries are read.
                    let ObjectPropertyKind::ObjectProperty(property) = property else {
                        return Expr::Unsupported("browser-value");
                    };
                    if property.kind != PropertyKind::Init || property.method {
                        return Expr::Unsupported("browser-value");
                    }
                    let Some(key) = property_name(&property.key, property.computed) else {
                        return Expr::Unsupported("browser-value");
                    };
                    entries.push((key, self.expr(&property.value, locals)));
                }
                Expr::Object(entries)
            }
            _ => Expr::Unsupported("browser-value"),
        }
    }
}

fn property_name(key: &PropertyKey<'_>, computed: bool) -> Option<String> {
    if computed {
        return match key.as_expression().map(strip) {
            Some(Expression::StringLiteral(literal)) => Some(literal.value.to_string()),
            _ => None,
        };
    }
    key.static_name().map(|name| name.to_string())
}

/// The parameter names and returned expression of `(a, b) => value` or
/// `(a) => { return value }`.
fn arrow<'b, 'a>(function: &'b Expression<'a>) -> Option<(Vec<String>, &'b Expression<'a>)> {
    let Expression::ArrowFunctionExpression(arrow) = strip(function) else {
        return None;
    };
    if arrow.params.rest.is_some() {
        return None;
    }
    let mut params = Vec::new();
    for param in &arrow.params.items {
        let BindingPattern::BindingIdentifier(id) = &param.pattern else {
            return None;
        };
        if param.initializer.is_some() {
            return None;
        }
        params.push(id.name.to_string());
    }
    let body = match &arrow.body {
        ArrowFunctionBody::FunctionBody(body) => match body.statements.as_slice() {
            [Statement::ReturnStatement(statement)] => statement.argument.as_ref()?,
            _ => return None,
        },
        body => body.as_expression()?,
    };
    Some((params, body))
}

// ---------------------------------------------------------------------------
// Request data
// ---------------------------------------------------------------------------

/// The part of the prepared manifest the renderer reads: each component
/// occurrence with its definition and data.
#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ManifestInput {
    root_id: String,
    occurrences: Vec<OccurrenceInput>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct OccurrenceInput {
    id: String,
    type_key: String,
    definition_id: String,
    #[serde(default)]
    prepared_data: Json,
    #[serde(default)]
    server_data: Json,
}

// ---------------------------------------------------------------------------
// Values
// ---------------------------------------------------------------------------

/// A JavaScript value the render reads, or the reason it is only known in
/// the browser.
#[derive(Clone, Debug)]
enum Val<'a> {
    Undefined,
    Null,
    Bool(bool),
    Num(f64),
    Str(Cow<'a, str>),
    /// An object or array from the prepared data.
    Data(&'a Json),
    /// An array the render code builds. An item may be browser-only while
    /// the array itself is known.
    Array(Rc<Vec<Val<'a>>>),
    /// An object the render code builds, its entries in JavaScript's
    /// enumeration order (see [`js_object_order`]).
    Object(Rc<Vec<(Cow<'a, str>, Val<'a>)>>),
    /// The component instance (`_ctx`).
    Ctx,
    Unknown(&'static str),
}

impl<'a> Val<'a> {
    fn from_json(value: &'a Json) -> Self {
        match value {
            Json::Null => Val::Null,
            Json::Bool(value) => Val::Bool(*value),
            Json::Number(number) => number
                .as_f64()
                .map_or(Val::Unknown("browser-value"), Val::Num),
            Json::String(value) => Val::Str(Cow::Borrowed(value)),
            Json::Array(_) | Json::Object(_) => Val::Data(value),
        }
    }

    /// JavaScript truthiness, or `None` when the value is browser-only.
    fn truthy(&self) -> Option<bool> {
        Some(match self {
            Val::Undefined | Val::Null => false,
            Val::Bool(value) => *value,
            Val::Num(value) => *value != 0.0 && !value.is_nan(),
            Val::Str(value) => !value.is_empty(),
            Val::Data(_) | Val::Array(_) | Val::Object(_) | Val::Ctx => true,
            Val::Unknown(_) => return None,
        })
    }
}

/// JavaScript's `String(number)` for the numbers JSON data carries safely.
fn js_number(value: f64) -> Option<String> {
    // Integers print the same in Python, JSON and JavaScript. Other numbers
    // would need JavaScript's exact shortest-form printing, so they are
    // treated as browser-only rather than guessed.
    if value.fract() == 0.0 && value.abs() < 9_007_199_254_740_992.0 {
        #[allow(clippy::cast_possible_truncation)]
        return Some((value as i64).to_string());
    }
    None
}

/// Vue's `toDisplayString`.
fn display<'a>(value: &Val<'a>) -> Result<Cow<'a, str>, &'static str> {
    match value {
        Val::Str(text) => Ok(text.clone()),
        Val::Undefined | Val::Null => Ok(Cow::Borrowed("")),
        Val::Bool(true) => Ok(Cow::Borrowed("true")),
        Val::Bool(false) => Ok(Cow::Borrowed("false")),
        Val::Num(number) => js_number(*number).map(Cow::Owned).ok_or("browser-text"),
        // Objects print as indented JSON through Vue's own replacer.
        Val::Data(_) | Val::Array(_) | Val::Object(_) | Val::Ctx => Err("browser-text"),
        Val::Unknown(reason) => Err(reason),
    }
}

/// The empty object `$citryPrepared` returns for an occurrence without `preparedData`.
static EMPTY_OBJECT: LazyLock<Json> = LazyLock::new(|| Json::Object(serde_json::Map::new()));

/// Properties every JavaScript object inherits from `Object.prototype`.
const OBJECT_PROTOTYPE_NAMES: [&str; 12] = [
    "constructor",
    "toString",
    "toLocaleString",
    "valueOf",
    "hasOwnProperty",
    "isPrototypeOf",
    "propertyIsEnumerable",
    "__proto__",
    "__defineGetter__",
    "__defineSetter__",
    "__lookupGetter__",
    "__lookupSetter__",
];

/// Local names (`renderList` and slot parameters), innermost first.
#[derive(Debug)]
struct Locals<'a> {
    name: &'a str,
    value: Val<'a>,
    parent: Scope<'a>,
}

type Scope<'a> = Option<Rc<Locals<'a>>>;

fn lookup<'a>(mut scope: Option<&Rc<Locals<'a>>>, name: &str) -> Val<'a> {
    while let Some(locals) = scope {
        if locals.name == name {
            return locals.value.clone();
        }
        scope = locals.parent.as_ref();
    }
    Val::Unknown("browser-value")
}

/// One component instance being rendered.
struct Instance<'a> {
    occurrence: &'a OccurrenceInput,
    slots: Vec<SlotBinding<'a>>,
}

/// A slot supplied to an instance, with the instance and scope that wrote it.
struct SlotBinding<'a> {
    def: &'a SlotDef,
    owner: Rc<Instance<'a>>,
    locals: Scope<'a>,
}

fn eval<'a>(expr: &'a Expr, instance: &Instance<'a>, locals: &Scope<'a>) -> Val<'a> {
    match expr {
        Expr::Undefined => Val::Undefined,
        Expr::Null => Val::Null,
        Expr::Bool(value) => Val::Bool(*value),
        Expr::Num(value) => Val::Num(*value),
        Expr::Str(value) => Val::Str(Cow::Borrowed(value)),
        Expr::Ctx => Val::Ctx,
        Expr::Local(name) => lookup(locals.as_ref(), name),
        Expr::Member(object, key) => match eval(object, instance, locals) {
            // The instance exposes the occurrence's `preparedData` as
            // `$citryPrepared`, plus every `js_data` key; data(), setup(),
            // props, methods, computed values and injections exist only in the
            // browser. No `js_data` key can
            // share the `$citryPrepared` name, because `render_for_hydration`
            // declines a page with a `$` or `_` key before writing.
            Val::Ctx => {
                if key == "$citryPrepared" {
                    // The client's getter falls back to an empty object.
                    match &instance.occurrence.prepared_data {
                        Json::Null => Val::Data(&EMPTY_OBJECT),
                        data => Val::from_json(data),
                    }
                } else {
                    instance
                        .occurrence
                        .server_data
                        .get(key)
                        .map_or(Val::Unknown("browser-value"), Val::from_json)
                }
            }
            Val::Data(Json::Object(map)) => match map.get(key) {
                Some(value) => Val::from_json(value),
                // Names every JavaScript object inherits read as functions.
                None if OBJECT_PROTOTYPE_NAMES.contains(&key.as_str()) => {
                    Val::Unknown("browser-value")
                }
                None => Val::Undefined,
            },
            Val::Data(Json::Array(items)) => match key.parse::<usize>() {
                // Only the canonical spelling ("1", not "01") is an index.
                Ok(index) if index.to_string() == *key => {
                    items.get(index).map_or(Val::Undefined, Val::from_json)
                }
                Err(_) if key == "length" => Val::Num(items.len() as f64),
                _ => Val::Unknown("browser-value"),
            },
            Val::Object(entries) => match entries.iter().find(|(name, _)| name == key) {
                Some((_, value)) => value.clone(),
                None if OBJECT_PROTOTYPE_NAMES.contains(&key.as_str()) => {
                    Val::Unknown("browser-value")
                }
                None => Val::Undefined,
            },
            Val::Array(items) => match key.parse::<usize>() {
                Ok(index) if index.to_string() == *key => {
                    items.get(index).cloned().unwrap_or(Val::Undefined)
                }
                Err(_) if key == "length" => Val::Num(items.len() as f64),
                _ => Val::Unknown("browser-value"),
            },
            Val::Str(text) if key == "length" => Val::Num(text.encode_utf16().count() as f64),
            Val::Unknown(reason) => Val::Unknown(reason),
            // Other property reads (including of null, which throws) are
            // left to the browser.
            _ => Val::Unknown("browser-value"),
        },
        Expr::Not(value) => match eval(value, instance, locals).truthy() {
            Some(value) => Val::Bool(!value),
            None => Val::Unknown("browser-value"),
        },
        Expr::StrictEq(left, right, negate) => {
            let left = eval(left, instance, locals);
            let right = eval(right, instance, locals);
            match strict_equal(&left, &right) {
                Some(equal) => Val::Bool(equal != *negate),
                None => Val::Unknown("browser-value"),
            }
        }
        Expr::Add(left, right) => {
            let left = eval(left, instance, locals);
            let right = eval(right, instance, locals);
            // Only string concatenation: numeric addition and object
            // coercion would need JavaScript's number printing.
            let (left, right) = match (&left, &right) {
                (Val::Unknown(reason), _) | (_, Val::Unknown(reason)) => {
                    return Val::Unknown(reason);
                }
                (Val::Str(a), Val::Str(b)) => (a.to_string(), b.to_string()),
                (Val::Str(a), Val::Num(b)) => match js_number(*b) {
                    Some(b) => (a.to_string(), b),
                    None => return Val::Unknown("browser-value"),
                },
                (Val::Num(a), Val::Str(b)) => match js_number(*a) {
                    Some(a) => (a, b.to_string()),
                    None => return Val::Unknown("browser-value"),
                },
                _ => return Val::Unknown("browser-value"),
            };
            Val::Str(Cow::Owned(left + &right))
        }
        Expr::And(left, right) => {
            let left = eval(left, instance, locals);
            match left.truthy() {
                Some(true) => eval(right, instance, locals),
                _ => left,
            }
        }
        Expr::Or(left, right) => {
            let left = eval(left, instance, locals);
            match left.truthy() {
                Some(false) => eval(right, instance, locals),
                _ => left,
            }
        }
        Expr::Cond(test, then, otherwise) => match eval(test, instance, locals).truthy() {
            Some(true) => eval(then, instance, locals),
            Some(false) => eval(otherwise, instance, locals),
            None => Val::Unknown("browser-value"),
        },
        Expr::Display(value) => match display(&eval(value, instance, locals)) {
            Ok(text) => Val::Str(text),
            Err(reason) => Val::Unknown(reason),
        },
        Expr::NormalizeClass(value) => {
            match normalize_class(&eval(value, instance, locals), Parts::All) {
                Ok(text) => Val::Str(Cow::Owned(text)),
                Err(reason) => Val::Unknown(reason),
            }
        }
        Expr::NormalizeStyle(value) => normalize_style(eval(value, instance, locals)),
        Expr::Array(items) => Val::Array(Rc::new(
            items
                .iter()
                .map(|item| eval(item, instance, locals))
                .collect(),
        )),
        Expr::Object(entries) => Val::Object(Rc::new(js_object_order(
            entries
                .iter()
                .map(|(key, value)| (Cow::Borrowed(key.as_str()), eval(value, instance, locals)))
                .collect(),
        ))),
        Expr::Unsupported(reason) => Val::Unknown(reason),
    }
}

fn strict_equal(left: &Val<'_>, right: &Val<'_>) -> Option<bool> {
    Some(match (left, right) {
        (Val::Unknown(_), _) | (_, Val::Unknown(_)) => return None,
        (Val::Undefined, Val::Undefined) | (Val::Null, Val::Null) | (Val::Ctx, Val::Ctx) => true,
        (Val::Bool(a), Val::Bool(b)) => a == b,
        #[allow(clippy::float_cmp)]
        (Val::Num(a), Val::Num(b)) => a == b,
        (Val::Str(a), Val::Str(b)) => a == b,
        // Two data objects are equal only when they are the same object.
        (Val::Data(a), Val::Data(b)) => std::ptr::eq(*a, *b),
        _ => false,
    })
}

// ---------------------------------------------------------------------------
// Attributes: what Vue's first client render leaves on each element
// ---------------------------------------------------------------------------

/// Vue's `isSpecialBooleanAttr`: attributes Vue writes as `""` or removes.
const SPECIAL_BOOLEAN_ATTRIBUTES: [&str; 7] = [
    "itemscope",
    "allowfullscreen",
    "formnovalidate",
    "ismap",
    "nomodule",
    "novalidate",
    "readonly",
];

/// Lowercase attribute names that are not DOM properties of any element
/// (`key in el` is false), so Vue sets them with `setAttribute`.
const ATTRIBUTE_ONLY: [&str; 18] = [
    "for",
    "colspan",
    "rowspan",
    "tabindex",
    "maxlength",
    "minlength",
    "accesskey",
    "contenteditable",
    "enterkeyhint",
    "inputmode",
    "datetime",
    "formaction",
    "crossorigin",
    // The DOM property is `fetchPriority`, so the lowercase key is not in
    // the element and Vue writes the attribute.
    "fetchpriority",
    "referrerpolicy",
    "usemap",
    "itemprop",
    "itemtype",
];

/// How a DOM property Vue sets reaches the element's attributes.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum Reflect {
    /// A string property that mirrors its attribute.
    String,
    /// A boolean property present as `""` when true.
    Boolean,
}

/// Properties Vue sets with `el[key] = value` because `key in el` is true
/// for this element, and how each mirrors its attribute. A key missing here
/// and from [`ATTRIBUTE_ONLY`] is not written, because the server cannot
/// tell which of Vue's two paths the browser takes for it.
fn dom_property(tag: &str, key: &str) -> Option<Reflect> {
    use Reflect::{Boolean, String};
    match key {
        "id" | "title" | "lang" | "dir" | "slot" | "role" => return Some(String),
        "inert" | "autofocus" => return Some(Boolean),
        _ => {}
    }
    match (tag, key) {
        ("a", "href" | "target" | "rel" | "download" | "hreflang" | "type" | "ping" | "name")
        | ("area", "href" | "target" | "rel" | "download" | "alt" | "coords" | "shape")
        | ("button", "name" | "type")
        | (
            "input",
            "name" | "type" | "placeholder" | "min" | "max" | "step" | "pattern" | "accept" | "alt"
            | "src" | "autocomplete",
        )
        | ("textarea", "name" | "placeholder" | "wrap" | "autocomplete")
        | ("select", "name" | "autocomplete")
        | ("option" | "optgroup", "label")
        | ("form", "action" | "method" | "enctype" | "target" | "name" | "autocomplete" | "rel")
        | ("fieldset" | "output", "name")
        | ("img", "src" | "alt" | "srcset" | "sizes" | "loading" | "decoding")
        | ("ol", "type")
        | ("td" | "th", "headers")
        | ("th", "abbr" | "scope")
        | ("blockquote" | "q" | "del" | "ins", "cite")
        | ("source", "src" | "type" | "srcset" | "sizes" | "media")
        | ("track", "kind" | "src" | "srclang" | "label")
        | ("video" | "audio", "src" | "preload")
        | ("video", "poster")
        | ("object", "data" | "type" | "name") => Some(String),
        (
            "button" | "fieldset" | "optgroup" | "option" | "select" | "textarea" | "input",
            "disabled",
        )
        | ("input", "required" | "multiple")
        | ("textarea" | "select", "required")
        | ("select", "multiple")
        | ("details" | "dialog", "open")
        | ("ol", "reversed")
        | ("track", "default")
        | ("video" | "audio", "controls" | "autoplay" | "loop") => Some(Boolean),
        _ => None,
    }
}

/// The attribute value Vue's `setAttribute` path writes for a value, or
/// `None` when Vue removes the attribute.
fn attribute_text(value: &Val<'_>, boolean: bool) -> Result<Option<String>, &'static str> {
    if boolean {
        // Vue's `includeBooleanAttr`: truthy values and "" keep it.
        let present = match value {
            Val::Str(text) if text.is_empty() => true,
            other => other.truthy().ok_or("browser-value")?,
        };
        return Ok(present.then(String::new));
    }
    match value {
        Val::Undefined | Val::Null => Ok(None),
        Val::Str(text) => Ok(Some(text.to_string())),
        Val::Bool(value) => Ok(Some(value.to_string())),
        Val::Num(number) => js_number(*number).map(Some).ok_or("unsupported-attribute"),
        Val::Unknown(reason) => Err(reason),
        // Objects and arrays print through JavaScript's own coercion.
        Val::Data(_) | Val::Array(_) | Val::Object(_) | Val::Ctx => Err("unsupported-attribute"),
    }
}

/// Which parts of a class or style value the caller needs.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum Parts {
    /// Every part: one the server cannot read makes the whole value
    /// unknown, because Vue's first render would differ from a guess.
    All,
    /// Only the parts the server can read. Shell contents show these until
    /// Vue builds the shell's children, so a static `class="card"` next to a
    /// browser-only `:class` still styles the element before Vue runs.
    Known,
}

/// Vue's `normalizeClass`: a string as it is, the normalized items of an
/// array, or the keys of an object whose values are truthy, joined with
/// spaces and trimmed.
fn normalize_class(value: &Val<'_>, parts: Parts) -> Result<String, &'static str> {
    // Vue builds the text with a space after every non-empty part and trims
    // the result, so a part's own surrounding spaces survive in the middle.
    let mut output = String::new();
    let mut push = |text: &str| {
        if !text.is_empty() {
            output.push_str(text);
            output.push(' ');
        }
    };
    match value {
        Val::Str(text) => push(text),
        Val::Undefined | Val::Null | Val::Bool(_) | Val::Num(_) => {}
        Val::Data(Json::Array(items)) => {
            for item in items {
                push(&normalize_class(&Val::from_json(item), parts)?);
            }
        }
        Val::Array(items) => {
            for item in items.iter() {
                push(&normalize_class(item, parts)?);
            }
        }
        Val::Data(Json::Object(map)) => {
            for (name, enabled) in js_data_order(map) {
                match (Val::from_json(enabled).truthy(), parts) {
                    (Some(true), _) => push(name),
                    (Some(false), _) | (None, Parts::Known) => {}
                    (None, Parts::All) => return Err("browser-value"),
                }
            }
        }
        Val::Object(entries) => {
            for (name, enabled) in entries.iter() {
                match (enabled.truthy(), parts) {
                    (Some(true), _) => push(name),
                    (Some(false), _) | (None, Parts::Known) => {}
                    (None, Parts::All) => return Err("browser-value"),
                }
            }
        }
        Val::Data(_) | Val::Ctx | Val::Unknown(_) if parts == Parts::Known => {}
        Val::Data(_) | Val::Ctx => return Err("unsupported-attribute"),
        Val::Unknown(reason) => return Err(reason),
    }
    Ok(js_trim(&output).to_owned())
}

/// Vue's `normalizeStyle` for a `:style` value: a string or an object is
/// returned as it is, and an array becomes one object holding every item's
/// declarations, a later item replacing an earlier one's value.
fn normalize_style(value: Val<'_>) -> Val<'_> {
    match value {
        Val::Array(_) | Val::Data(Json::Array(_)) => match style_entries(&value, Parts::All) {
            Ok(Some(entries)) => Val::Object(Rc::new(entries)),
            Ok(None) => Val::Undefined,
            Err(reason) => Val::Unknown(reason),
        },
        Val::Str(_) | Val::Object(_) | Val::Data(Json::Object(_)) | Val::Unknown(_) => value,
        // Vue returns nothing for any other value, which removes the
        // attribute.
        _ => Val::Undefined,
    }
}

/// Style declarations as `normalizeStyle` leaves them: property name and
/// value, in JavaScript's key order.
type StyleEntries<'a> = Vec<(Cow<'a, str>, Val<'a>)>;

/// The declarations `normalizeStyle` gives a value, in JavaScript's key
/// order, or `None` when it gives nothing (a number, `null`).
fn style_entries<'a>(
    value: &Val<'a>,
    parts: Parts,
) -> Result<Option<StyleEntries<'a>>, &'static str> {
    let mut output = Vec::new();
    match value {
        Val::Str(text) => output = parse_string_style(text),
        Val::Object(entries) => output = entries.as_ref().clone(),
        Val::Data(Json::Object(map)) => {
            output = js_data_order(map)
                .into_iter()
                .map(|(key, value)| (Cow::Borrowed(key), Val::from_json(value)))
                .collect();
        }
        Val::Array(_) | Val::Data(Json::Array(_)) => {
            let items: Vec<Val<'a>> = match value {
                Val::Array(items) => items.as_ref().clone(),
                Val::Data(Json::Array(items)) => items.iter().map(Val::from_json).collect(),
                _ => unreachable!("matched an array above"),
            };
            for item in &items {
                // An item's declarations replace earlier values in place,
                // like assigning to a JavaScript object.
                for (key, value) in style_entries(item, parts)?.unwrap_or_default() {
                    match output.iter_mut().find(|(name, _)| *name == key) {
                        Some(existing) => existing.1 = value,
                        None => output.push((key, value)),
                    }
                }
            }
            output = js_object_order(output);
        }
        Val::Unknown(_) | Val::Ctx if parts == Parts::Known => return Ok(None),
        Val::Unknown(reason) => return Err(reason),
        Val::Ctx | Val::Data(_) => return Err("unsupported-attribute"),
        Val::Undefined | Val::Null | Val::Bool(_) | Val::Num(_) => return Ok(None),
    }
    Ok(Some(output))
}

/// Vue's `parseStringStyle`: split a style string into declarations,
/// ignoring comments and semicolons inside parentheses.
fn parse_string_style(text: &str) -> Vec<(Cow<'static, str>, Val<'static>)> {
    // Comments are removed first, as `/\/\*[^]*?\*\//g` does.
    let mut without_comments = String::with_capacity(text.len());
    let mut rest = text;
    while let Some(start) = rest.find("/*") {
        without_comments.push_str(&rest[..start]);
        match rest[start + 2..].find("*/") {
            Some(end) => rest = &rest[start + 2 + end + 2..],
            None => {
                // An unclosed comment is not matched, so it stays.
                without_comments.push_str(&rest[start..]);
                rest = "";
            }
        }
    }
    without_comments.push_str(rest);
    let mut output: Vec<(Cow<'static, str>, Val<'static>)> = Vec::new();
    // `;(?![^(]*\))`: a semicolon splits unless a `)` follows before any `(`.
    let bytes = without_comments.as_bytes();
    let mut start = 0;
    let mut items = Vec::new();
    for (index, byte) in bytes.iter().enumerate() {
        if *byte != b';' {
            continue;
        }
        let after = &without_comments[index + 1..];
        let inside_parentheses = after
            .find([')', '('])
            .is_some_and(|at| after.as_bytes()[at] == b')');
        if !inside_parentheses {
            items.push(&without_comments[start..index]);
            start = index + 1;
        }
    }
    items.push(&without_comments[start..]);
    for item in items {
        // `split(/:([^]+)/)` keeps the text before the first colon and
        // everything after it; an item without a colon is dropped.
        let Some((key, value)) = item.split_once(':') else {
            continue;
        };
        if value.is_empty() {
            continue;
        }
        let key = Cow::Owned(js_trim(key).to_owned());
        let value = Val::Str(Cow::Owned(js_trim(value).to_owned()));
        match output.iter_mut().find(|(name, _)| *name == key) {
            Some(existing) => existing.1 = value,
            None => output.push((key, value)),
        }
    }
    js_object_order(output)
}

/// The style attribute text for normalized style declarations, as Vue's
/// server renderer (`stringifyStyle`) writes them: `name:value;` with
/// camelCase names hyphenated. The browser reads the same declarations from
/// it as from the style Vue's client render sets, which is all hydration
/// compares. `None` when no declaration is written.
fn stringify_style(
    entries: &[(Cow<'_, str>, Val<'_>)],
    parts: Parts,
) -> Result<Option<String>, &'static str> {
    let mut output = String::new();
    for (key, value) in entries {
        let text = match value {
            // Vue skips these values, and the client sets nothing for them.
            Val::Undefined | Val::Null => continue,
            // The client removes an empty value while the server renderer
            // writes `name:;`, and a semicolon inside a value makes the
            // browser read the server's text as two declarations, so both
            // are left to the browser.
            Val::Str(text) if !text.is_empty() && !text.contains(';') => text.to_string(),
            Val::Num(number) => match js_number(*number) {
                Some(text) => text,
                None if parts == Parts::Known => continue,
                None => return Err("unsupported-attribute"),
            },
            // Other values are skipped by the server renderer but given to
            // the browser's style object by the client, which can keep them.
            _ if parts == Parts::Known => continue,
            Val::Unknown(reason) => return Err(reason),
            _ => return Err("unsupported-attribute"),
        };
        let name = if key.starts_with("--") {
            key.to_string()
        } else {
            // A name that starts with a capital, such as `WebkitTransition`,
            // is a vendor-prefixed property the client sets through the
            // browser's style object, while the server renderer's
            // `webkit-transition` is a name the browser ignores.
            match hyphenate(key).filter(|_| !key.starts_with(|c: char| c.is_ascii_uppercase())) {
                Some(name) => name,
                None if parts == Parts::Known => continue,
                None => return Err("unsupported-attribute"),
            }
        };
        output.push_str(&name);
        output.push(':');
        output.push_str(&text);
        output.push(';');
    }
    Ok((!output.is_empty()).then_some(output))
}

/// Vue's `hyphenate`: a dash before every capital that follows a letter,
/// digit or underscore, then the whole name in lowercase. `None` for a
/// name with non-ASCII characters, whose lowercase form JavaScript and
/// Rust may spell differently.
fn hyphenate(name: &str) -> Option<String> {
    if !name.is_ascii() {
        return None;
    }
    let mut output = String::with_capacity(name.len() + 4);
    let mut previous_is_word = false;
    for character in name.chars() {
        // `\B([A-Z])`: not at a word boundary, so the previous character
        // is a word character too.
        if character.is_ascii_uppercase() && previous_is_word {
            output.push('-');
        }
        output.push(character.to_ascii_lowercase());
        previous_is_word = character.is_ascii_alphanumeric() || character == '_';
    }
    Some(output)
}

/// JavaScript's `String.prototype.trim`, whose whitespace differs from
/// Rust's (it includes U+FEFF and excludes U+0085).
fn js_trim(text: &str) -> &str {
    text.trim_matches(|character: char| {
        matches!(
            character,
            '\t' | '\n' | '\u{b}' | '\u{c}' | '\r' | ' ' | '\u{a0}' | '\u{1680}' | '\u{2000}'
                ..='\u{200a}'
                    | '\u{2028}'
                    | '\u{2029}'
                    | '\u{202f}'
                    | '\u{205f}'
                    | '\u{3000}'
                    | '\u{feff}'
        )
    })
}

/// Whether JavaScript treats an object key as an array index, which it
/// lists before every other key, in numeric order.
fn is_array_index(key: &str) -> bool {
    let bytes = key.as_bytes();
    if key == "0" {
        return true;
    }
    if bytes.is_empty()
        || bytes.len() > 10
        || bytes[0] == b'0'
        || !bytes.iter().all(u8::is_ascii_digit)
    {
        return false;
    }
    key.parse::<u64>()
        .is_ok_and(|value| value < u64::from(u32::MAX))
}

/// Put an object literal's entries in the order JavaScript enumerates them:
/// array-index keys first in numeric order, then the others in the order
/// they were first written. A repeated key keeps its first position and its
/// last value.
fn js_object_order<'a>(entries: Vec<(Cow<'a, str>, Val<'a>)>) -> Vec<(Cow<'a, str>, Val<'a>)> {
    let mut unique: Vec<(Cow<'a, str>, Val<'a>)> = Vec::with_capacity(entries.len());
    for (key, value) in entries {
        match unique.iter_mut().find(|(name, _)| *name == key) {
            Some(existing) => existing.1 = value,
            None => unique.push((key, value)),
        }
    }
    let (mut indexes, others): (Vec<_>, Vec<_>) =
        unique.into_iter().partition(|(key, _)| is_array_index(key));
    indexes.sort_by_key(|(key, _)| key.parse::<u64>().unwrap_or(u64::MAX));
    indexes.extend(others);
    indexes
}

/// The entries of an object from the prepared data in the order the
/// browser enumerates them. Python writes the page's JSON with sorted keys,
/// which is also this map's order, and `JSON.parse` keeps that order except
/// that array-index keys come first, in numeric order.
fn js_data_order(map: &serde_json::Map<String, Json>) -> Vec<(&str, &Json)> {
    let (mut indexes, others): (Vec<_>, Vec<_>) = map
        .iter()
        .map(|(key, value)| (key.as_str(), value))
        .partition(|(key, _)| is_array_index(key));
    indexes.sort_by_key(|(key, _)| key.parse::<u64>().unwrap_or(u64::MAX));
    indexes.extend(others);
    indexes
}

/// The attribute one prop leaves on the element after Vue's first client
/// render (`None`: no attribute), following `patchProp` in `runtime-dom`.
fn client_attribute(tag: &str, key: &str, value: &Val<'_>) -> Result<Option<String>, &'static str> {
    if let Val::Unknown(reason) = value {
        return Err(reason);
    }
    if key == "class" {
        // Vue normalizes a class only when it is truthy and not a string,
        // then sets `el.className`, which prints `false` or `0` as is; null
        // or undefined removes the attribute.
        return match value {
            Val::Undefined | Val::Null => Ok(None),
            Val::Str(text) => Ok(Some(text.to_string())),
            Val::Bool(false) => Ok(Some("false".to_owned())),
            Val::Num(number) if *number == 0.0 => Ok(Some("0".to_owned())),
            other => normalize_class(other, Parts::All).map(Some),
        };
    }
    if key == "style" {
        // A style string is written as authored and a style object as Vue's
        // server renderer writes it. Hydration leaves either in place and
        // the browser reads the same declarations; only the attribute text
        // differs from the browser's normalized form that client mount
        // leaves.
        return match value {
            Val::Undefined | Val::Null => Ok(None),
            Val::Str(text) => Ok(Some(text.to_string())),
            Val::Object(entries) => stringify_style(entries, Parts::All),
            // `createVNode` runs `normalizeStyle` on a style object or array
            // the render did not normalize itself (the compiler leaves a
            // constant one as it is).
            Val::Data(Json::Object(_)) | Val::Array(_) | Val::Data(Json::Array(_)) => {
                match style_entries(value, Parts::All)? {
                    Some(entries) => stringify_style(&entries, Parts::All),
                    None => Ok(None),
                }
            }
            _ => Err("unsupported-attribute"),
        };
    }
    let bytes = key.as_bytes();
    if key.is_empty()
        || !bytes[0].is_ascii_lowercase()
        || !bytes.iter().all(|byte| {
            byte.is_ascii_lowercase() || byte.is_ascii_digit() || matches!(byte, b'-' | b'_' | b':')
        })
    {
        // Upper case (`tabIndex`), `.prop`/`^attr` modifiers and unusual
        // names take paths the server does not model.
        return Err("unsupported-attribute");
    }
    match (tag, key) {
        // Vue sets `value`, `checked` and `selected` as properties and then
        // also as attributes (runtime-dom #6007), so the attribute remains.
        // `output.value` sets the element's text, which hydration does not
        // re-apply, so it falls to the unsupported arm below.
        ("input" | "button" | "option" | "data", "value") => attribute_text(value, false),
        ("input", "checked") | ("option", "selected") => attribute_text(value, true),
        // Properties whose attribute does not follow them.
        (_, "value" | "checked" | "selected" | "muted" | "indeterminate" | "text") => {
            Err("unsupported-attribute")
        }
        // `el.hidden = value` accepts more than booleans; only the values
        // whose attribute is certain are written.
        (_, "hidden") => match value {
            Val::Undefined | Val::Null | Val::Bool(false) => Ok(None),
            Val::Bool(true) => Ok(Some(String::new())),
            Val::Str(text) if text.is_empty() => Ok(Some(String::new())),
            _ => Err("unsupported-attribute"),
        },
        _ if key.contains(['-', ':', '_']) || ATTRIBUTE_ONLY.contains(&key) => {
            attribute_text(value, SPECIAL_BOOLEAN_ATTRIBUTES.contains(&key))
        }
        // Vue's `shouldSetAsProp` sends these to `setAttribute` explicitly.
        (_, "spellcheck" | "draggable" | "translate" | "autocorrect" | "form")
        | ("input", "list")
        | ("textarea", "type")
        | ("img" | "video" | "canvas" | "source", "width" | "height") => {
            attribute_text(value, false)
        }
        _ if SPECIAL_BOOLEAN_ATTRIBUTES.contains(&key) => attribute_text(value, true),
        _ => match dom_property(tag, key) {
            // A mirrored string property ends as `String(value)`, and null
            // or undefined removes it: the same as `setAttribute`.
            Some(Reflect::String) => attribute_text(value, false),
            // `el[key] = value` coerces with JavaScript truthiness, and ""
            // counts as true (Vue's `includeBooleanAttr`).
            Some(Reflect::Boolean) => attribute_text(value, true),
            None => Err("unsupported-attribute"),
        },
    }
}

/// Keys Vue never writes to the DOM (`isReservedProp`).
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

/// One evaluated prop.
#[derive(Debug)]
enum PropVal<'a> {
    Value(Val<'a>),
    Listener,
}

type Props<'a> = Vec<(Cow<'a, str>, PropVal<'a>)>;

/// The attributes written for one element, and its `textContent` prop.
type ElementAttributes<'a> = (Vec<(String, String)>, Option<TextContent<'a>>);

/// An element's `textContent` prop (what `v-text` compiles to).
#[derive(Debug)]
struct TextContent<'a> {
    value: Val<'a>,
    /// Whether hydration sets it (the render lists it as a dynamic prop).
    patched: bool,
}

fn set_prop<'a>(output: &mut Props<'a>, key: Cow<'a, str>, value: PropVal<'a>) {
    // A repeated key keeps the first key's position, like a JavaScript object.
    match output.iter_mut().find(|(name, _)| *name == key) {
        Some(existing) => existing.1 = value,
        None => output.push((key, value)),
    }
}

/// Merge one argument of `mergeProps` into the props merged so far, with
/// Vue's rules: every `class` is normalized and joined unless it is the same
/// string, `style` values are combined, and other keys are replaced.
fn merge_prop<'a>(output: &mut Props<'a>, key: Cow<'a, str>, value: PropVal<'a>) {
    if key == "class" {
        let before = output
            .iter()
            .find(|(name, _)| name == "class")
            .map(|(_, value)| value);
        let merged = match (before, &value) {
            (Some(PropVal::Value(Val::Str(a))), PropVal::Value(Val::Str(b))) if a == b => return,
            (before, PropVal::Value(after)) => {
                let before = match before {
                    Some(PropVal::Value(before)) => normalize_class(before, Parts::All),
                    _ => Ok(String::new()),
                };
                match (before, normalize_class(after, Parts::All)) {
                    (Ok(a), Ok(b)) => Val::Str(Cow::Owned(format!("{a} {b}").trim().to_owned())),
                    (Err(reason), _) | (_, Err(reason)) => Val::Unknown(reason),
                }
            }
            (_, PropVal::Listener) => Val::Unknown("unsupported-attribute"),
        };
        set_prop(output, key, PropVal::Value(merged));
        return;
    }
    if key == "style" {
        // Vue sets `normalizeStyle([before, after])`: one object with both
        // values' declarations, the later value winning. With no earlier
        // style that object holds exactly the declarations of the value on
        // its own, so a string is kept as authored, as outside `mergeProps`.
        let merged = match (output.iter().find(|(name, _)| name == "style"), value) {
            (_, PropVal::Listener) | (Some((_, PropVal::Listener)), _) => {
                Val::Unknown("unsupported-attribute")
            }
            (None, PropVal::Value(after)) => normalize_style(after),
            (Some((_, PropVal::Value(before))), PropVal::Value(after)) => {
                normalize_style(Val::Array(Rc::new(vec![before.clone(), after])))
            }
        };
        set_prop(output, key, PropVal::Value(merged));
        return;
    }
    set_prop(output, key, value);
}

/// Evaluate a props argument with Vue's `mergeProps`/`normalizeProps` rules.
fn eval_props<'a>(
    props: &'a PropsExpr,
    instance: &Instance<'a>,
    locals: &Scope<'a>,
    output: &mut Props<'a>,
) -> Result<(), &'static str> {
    match props {
        PropsExpr::Object(entries) => {
            for entry in entries {
                let value = match &entry.value {
                    PropValue::Listener => PropVal::Listener,
                    PropValue::Value(expr) => PropVal::Value(eval(expr, instance, locals)),
                };
                set_prop(output, Cow::Borrowed(&entry.key), value);
            }
            Ok(())
        }
        PropsExpr::Merge(items) => {
            for item in items {
                let mut part = Vec::new();
                eval_props(item, instance, locals, &mut part)?;
                for (key, value) in part {
                    merge_prop(output, key, value);
                }
            }
            Ok(())
        }
        PropsExpr::Normalize(inner) => eval_props(inner, instance, locals, output),
        PropsExpr::Spread(expr) => match eval(expr, instance, locals) {
            Val::Undefined | Val::Null => Ok(()),
            Val::Data(Json::Object(map)) => {
                for (key, value) in js_data_order(map) {
                    // A function never arrives in JSON data, so a listener
                    // key here would carry the wrong kind of value.
                    if is_listener_key(key) {
                        return Err("unsupported-attribute");
                    }
                    set_prop(
                        output,
                        Cow::Borrowed(key),
                        PropVal::Value(Val::from_json(value)),
                    );
                }
                Ok(())
            }
            // An object literal written in the render code, such as the
            // argument of `v-bind="{ ... }"` outside `normalizeProps`.
            Val::Object(entries) => {
                for (key, value) in entries.iter() {
                    // Listeners are functions, which the server never runs.
                    if is_listener_key(key) {
                        return Err("unsupported-attribute");
                    }
                    set_prop(output, key.clone(), PropVal::Value(value.clone()));
                }
                Ok(())
            }
            Val::Unknown(reason) => Err(reason),
            _ => Err("unsupported-attribute"),
        },
        PropsExpr::Unsupported(reason) => Err(reason),
    }
}

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------

/// Why part of the page was not written for Vue to adopt.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Decline {
    /// A kebab-case reason code; the Python `HydrationDecline` lists them.
    pub code: &'static str,
    /// The tag, attribute or construct the code refers to.
    pub detail: String,
    /// The type key of the component whose render held the declined part.
    pub component: Option<String>,
    /// The element written in its place for Vue to fill, or `None` when no
    /// element separated the part from the page root.
    pub shell_tag: Option<String>,
    /// Whether that element carries HTML for its contents, which
    /// the browser runtime removes before Vue fills it. `false` when the
    /// element is written empty.
    pub shell_content: bool,
}

/// What rendering one page produced.
#[derive(Debug, Default)]
pub struct HydrationRender {
    /// The host's inner HTML, when the page hydrates.
    pub html: Option<String>,
    /// The elements written for Vue to adopt, shells included.
    pub element_count: usize,
    pub shell_count: usize,
    pub declines: Vec<Decline>,
    /// Why the page mounts in the browser, when it does.
    pub reason: Option<&'static str>,
}

/// Programs by compiled definition id, the prepared manifest JSON, the
/// component tag registered for each type key, and the page-size rule.
pub struct RenderRequest<'a> {
    pub programs: &'a HashMap<String, &'a ServerRenderProgram>,
    pub manifest_json: &'a str,
    pub tags: &'a HashMap<String, String>,
    /// Only a page with more elements than this is checked and returned.
    pub threshold: usize,
    /// Always parse the whole written HTML instead of first checking the
    /// token stream against stored answers. The two checks must agree; tests
    /// and the render parity check use this to compare them.
    pub full_parse_check: bool,
}

/// Render a page's host content for hydration and check how the browser
/// parses it.
pub fn render_for_hydration(request: &RenderRequest<'_>) -> HydrationRender {
    let Ok(manifest) = serde_json::from_str::<ManifestInput>(request.manifest_json) else {
        return HydrationRender {
            reason: Some("manifest"),
            ..HydrationRender::default()
        };
    };
    // The browser runtime refuses a `js_data` key that starts with `$` or `_`
    // (`installServerKey` in client.js), because those names belong to Vue and
    // Citry, `$citryPrepared` among them. The page mounts in the browser so the
    // runtime reports that error, rather than the server writing HTML the
    // browser would never adopt.
    let reserved_server_key = manifest.occurrences.iter().any(|occurrence| {
        occurrence.server_data.as_object().is_some_and(|data| {
            data.keys()
                .any(|key| key.starts_with('$') || key.starts_with('_'))
        })
    });
    if reserved_server_key {
        return HydrationRender {
            reason: Some("manifest"),
            ..HydrationRender::default()
        };
    }
    let occurrences = manifest
        .occurrences
        .iter()
        .map(|occurrence| (occurrence.id.as_str(), occurrence))
        .collect::<HashMap<_, _>>();
    // The first pass records only the token stream; expected nodes with
    // their attributes are built only if the full parse has to run.
    let (mut writer, result) = write_page(
        request,
        &occurrences,
        &manifest.root_id,
        request.full_parse_check,
    );
    let shell_count = writer
        .declines
        .iter()
        .filter(|decline| decline.shell_tag.is_some())
        .count();
    let mut output = HydrationRender {
        element_count: writer.element_count,
        shell_count,
        declines: std::mem::take(&mut writer.declines),
        ..HydrationRender::default()
    };
    if let Err(fail) = result {
        output.declines.push(Decline {
            code: fail.code,
            detail: fail.detail,
            component: fail.component,
            shell_tag: None,
            shell_content: false,
        });
        output.reason = Some("host-root");
        return output;
    }
    if writer.element_count <= request.threshold {
        // Below this size the browser mounts faster than it parses the
        // extra HTML and then hydrates it, so the parse check is skipped.
        output.reason = Some("below-threshold");
        return output;
    }
    let kept_as_written = !request.full_parse_check
        && !writer.needs_full_parse
        && tokens_nest_in_browser(&writer.tokens);
    if !kept_as_written {
        if !writer.record_events {
            // Writing is deterministic, so the second pass produces the same
            // HTML, now with the nodes the full parse compares.
            (writer, _) = write_page(request, &occurrences, &manifest.root_id, true);
        }
        // Raw HTML blocks and shell contents were each checked where they
        // sit, and leave the parser as they found it, so the page's parse
        // leaves them out (see `static_html_in_context`).
        let checked_html = without_ranges(&writer.html, &writer.checked_ranges);
        if writer.events.is_empty()
            || !browser_fragment_matches_nodes(&checked_html, "div", &writer.events)
        {
            output.reason = Some("browser-structure");
            return output;
        }
    }
    output.html = Some(writer.html);
    output
}

/// `html` with the byte ranges `ranges` (in order, not overlapping) removed.
fn without_ranges<'h>(html: &'h str, ranges: &[(usize, usize)]) -> Cow<'h, str> {
    if ranges.is_empty() {
        return Cow::Borrowed(html);
    }
    let mut output = String::with_capacity(html.len());
    let mut position = 0;
    for &(start, end) in ranges {
        output.push_str(&html[position..start]);
        position = end;
    }
    output.push_str(&html[position..]);
    Cow::Owned(output)
}

/// Write the page from its root occurrence. `record_events` also builds the
/// expected nodes the full parse compares.
fn write_page<'a>(
    request: &'a RenderRequest<'a>,
    occurrences: &'a HashMap<&'a str, &'a OccurrenceInput>,
    root_id: &str,
    record_events: bool,
) -> (Writer<'a>, Result<bool, Fail>) {
    let mut writer = Writer {
        programs: request.programs,
        tags: request.tags,
        occurrences,
        html: String::with_capacity(request.manifest_json.len()),
        tokens: Vec::new(),
        record_events,
        events: Vec::new(),
        needs_full_parse: false,
        checked_ranges: Vec::new(),
        nodes_written: 0,
        element_count: 0,
        declines: Vec::new(),
        depth: 0,
        open: Vec::new(),
    };
    let result = match occurrences.get(root_id) {
        None => Err(Fail::new("component-lookup", "root", None)),
        Some(occurrence) => writer.occurrence(occurrence, Vec::new(), Cx { at_root: true }),
    };
    (writer, result)
}

/// A part the server cannot write, travelling up to the nearest element.
#[derive(Debug)]
struct Fail {
    code: &'static str,
    detail: String,
    component: Option<String>,
}

impl Fail {
    fn new(code: &'static str, detail: impl Into<String>, component: Option<&str>) -> Self {
        Fail {
            code,
            detail: detail.into(),
            component: component.map(str::to_owned),
        }
    }
}

/// Where a node is written.
///
/// Vue hydrates every node here in its full (not optimized) mode: Citry's
/// runtime creates vnodes with patch flag 0, and a slot's Fragment uses
/// Vue's bail flag because hydration never keeps a slot's stable marker
/// (`initSlots` in runtime-core). So every listener and dynamic key is
/// applied, and adjacent text vnodes sharing one DOM text node are split.
#[derive(Clone, Copy)]
struct Cx {
    /// Directly in the host, outside any element.
    at_root: bool,
}

/// Deep nesting would recurse past a small thread stack; a part nested
/// deeper is declined like any other, so its nearest element becomes a
/// shell (or the page mounts in the browser when there is none).
const MAX_DEPTH: usize = 256;

const VOID_TAGS: [&str; 14] = [
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source",
    "track", "wbr",
];

/// Tags whose contents the parser reads as raw text, or that belong to
/// another namespace or to the document itself; the server leaves them to
/// the browser.
const UNWRITTEN_TAGS: [&str; 15] = [
    "script",
    "style",
    "xmp",
    "iframe",
    "noembed",
    "noframes",
    "noscript",
    "plaintext",
    "template",
    "svg",
    "math",
    "html",
    "head",
    "body",
    "frameset",
];

/// The parser drops one newline right after these opening tags.
const LEADING_NEWLINE_TAGS: [&str; 3] = ["pre", "textarea", "listing"];

/// Start tags that close an open `<p>` (the HTML parser's "close a p
/// element" step for these tags).
const CLOSES_P: [&str; 39] = [
    "address",
    "article",
    "aside",
    "blockquote",
    "center",
    "details",
    "dialog",
    "dir",
    "div",
    "dl",
    "fieldset",
    "figcaption",
    "figure",
    "footer",
    "header",
    "hgroup",
    "main",
    "menu",
    "nav",
    "ol",
    "p",
    "search",
    "section",
    "summary",
    "ul",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "pre",
    "listing",
    "form",
    "table",
    "hr",
    "li",
    "dd",
    "dt",
];

/// Elements that stop the parser's "button scope" search for an open `<p>`.
const BUTTON_SCOPE: [&str; 10] = [
    "applet", "caption", "html", "table", "td", "th", "marquee", "object", "template", "button",
];

const HEADINGS: [&str; 6] = ["h1", "h2", "h3", "h4", "h5", "h6"];

/// Whether the browser's HTML parser would close, move or drop `tag` when
/// it starts inside the open elements `open` (innermost last), so the tree
/// it builds would differ from the vnodes. These are the tree-construction
/// rules markup nested the way a template writes it can trigger; the parse
/// check after writing stays the final word.
fn parser_moves(open: &[&str], tag: &str) -> bool {
    let parent = open.last().copied().unwrap_or("div");
    let nearest = |names: &[&str]| open.iter().rev().find(|name| names.contains(name)).copied();
    if CLOSES_P.contains(&tag) {
        for name in open.iter().rev() {
            if *name == "p" {
                return true;
            }
            if BUTTON_SCOPE.contains(name) {
                break;
            }
        }
    }
    // Table parts only stay where the table model puts them.
    let table_child = match parent {
        "table" => Some(&["caption", "colgroup", "thead", "tbody", "tfoot"][..]),
        "thead" | "tbody" | "tfoot" => Some(&["tr"][..]),
        "tr" => Some(&["td", "th"][..]),
        "colgroup" => Some(&["col"][..]),
        "select" => Some(&["option", "optgroup", "hr"][..]),
        "optgroup" => Some(&["option"][..]),
        _ => None,
    };
    if let Some(allowed) = table_child {
        return !allowed.contains(&tag);
    }
    match tag {
        "caption" | "colgroup" | "thead" | "tbody" | "tfoot" | "tr" | "td" | "th" | "col" => true,
        _ if HEADINGS.contains(&tag) => HEADINGS.contains(&parent),
        "a" | "form" | "button" | "select" | "nobr" => open.contains(&tag),
        "li" => nearest(&["li", "ul", "ol"]) == Some("li"),
        "dd" | "dt" => matches!(nearest(&["dd", "dt", "dl"]), Some("dd" | "dt")),
        "option" | "optgroup" => matches!(parent, "option" | "optgroup"),
        "rb" | "rt" | "rp" | "rtc" => parent != "ruby",
        "image" | "frame" | "frameset" | "isindex" => true,
        _ => false,
    }
}

/// Elements whose non-whitespace text the parser moves out of the table.
const TABLE_TEXT_MOVED: [&str; 6] = ["table", "thead", "tbody", "tfoot", "tr", "colgroup"];

struct Writer<'a> {
    programs: &'a HashMap<String, &'a ServerRenderProgram>,
    tags: &'a HashMap<String, String>,
    occurrences: &'a HashMap<&'a str, &'a OccurrenceInput>,
    html: String,
    /// The written nodes as tokens for [`tokens_nest_in_browser`].
    tokens: Vec<NestingToken<'a>>,
    /// Whether `events` is built (only for the full parse).
    record_events: bool,
    events: Vec<ExpectedNodeEvent>,
    /// Set when something was written that the token check does not cover.
    /// It is never cleared by a rollback, which at worst runs the full parse
    /// for nothing.
    needs_full_parse: bool,
    /// Byte ranges of `html` holding raw HTML blocks and shell contents,
    /// which are checked where they are written and left out of the full
    /// parse.
    checked_ranges: Vec<(usize, usize)>,
    /// Elements and comments written, which tells a
    /// component whose render wrote only text.
    nodes_written: usize,
    element_count: usize,
    declines: Vec<Decline>,
    depth: usize,
    /// The DOM elements currently open around the write position.
    open: Vec<&'a str>,
}

/// A position to roll the writer back to when a subtree cannot be written.
struct Mark {
    html: usize,
    tokens: usize,
    events: usize,
    checked_ranges: usize,
    nodes_written: usize,
    element_count: usize,
    declines: usize,
}

impl<'a> Writer<'a> {
    fn mark(&self) -> Mark {
        Mark {
            html: self.html.len(),
            tokens: self.tokens.len(),
            events: self.events.len(),
            checked_ranges: self.checked_ranges.len(),
            nodes_written: self.nodes_written,
            element_count: self.element_count,
            declines: self.declines.len(),
        }
    }

    fn rollback(&mut self, mark: &Mark) {
        self.html.truncate(mark.html);
        self.tokens.truncate(mark.tokens);
        self.events.truncate(mark.events);
        self.checked_ranges.truncate(mark.checked_ranges);
        self.nodes_written = mark.nodes_written;
        self.element_count = mark.element_count;
        self.declines.truncate(mark.declines);
    }

    fn comment(&mut self, data: &'a str) {
        self.html.push_str("<!--");
        self.html.push_str(data);
        self.html.push_str("-->");
        self.tokens.push(NestingToken::Comment(data));
        self.nodes_written += 1;
        if self.record_events {
            self.events.push(ExpectedNodeEvent::Comment {
                data: data.to_owned(),
            });
        }
    }

    /// Record a written text for the token check; an empty text writes no
    /// node.
    fn text_token(&mut self, text: &str) {
        if !text.is_empty() {
            if text.chars().any(tokenizer_reports) {
                self.needs_full_parse = true;
            }
            self.tokens.push(NestingToken::Text {
                whitespace: is_whitespace(text),
                starts_with_newline: text.starts_with('\n'),
            });
        }
    }

    /// Render one occurrence's definition as a component instance.
    fn occurrence(
        &mut self,
        occurrence: &'a OccurrenceInput,
        slots: Vec<SlotBinding<'a>>,
        cx: Cx,
    ) -> Result<bool, Fail> {
        let component = Some(occurrence.type_key.as_str());
        let program = self
            .programs
            .get(&occurrence.definition_id)
            .copied()
            .ok_or_else(|| Fail::new("component-lookup", "definition", component))?;
        if self.depth >= MAX_DEPTH {
            return Err(Fail::new("nesting-depth", "component", component));
        }
        self.depth += 1;
        let instance = Rc::new(Instance { occurrence, slots });
        let nodes_before = self.nodes_written;
        let result = self.node(&program.root, &instance, &None, cx);
        self.depth -= 1;
        result?;
        if self.nodes_written == nodes_before {
            // The render's root is a text vnode. Vue hydrates a component by
            // stepping over one DOM node, so text merged with a neighbour,
            // or an empty text with no node of its own, would shift every
            // sibling after it.
            return Err(Fail::new("component-text-root", "text", component));
        }
        // A component vnode always counts as content for `renderSlot`.
        Ok(true)
    }

    /// Write one node. Returns whether it is content in the sense of Vue's
    /// `ensureValidVNode` (anything but comments and empty Fragments).
    fn node(
        &mut self,
        node: &'a Node,
        instance: &Rc<Instance<'a>>,
        locals: &Scope<'a>,
        cx: Cx,
    ) -> Result<bool, Fail> {
        let component = Some(instance.occurrence.type_key.as_str());
        if self.depth >= MAX_DEPTH {
            return Err(Fail::new("nesting-depth", "render", component));
        }
        self.depth += 1;
        let result = self.write_node(node, instance, locals, cx);
        self.depth -= 1;
        result
    }

    fn write_node(
        &mut self,
        node: &'a Node,
        instance: &Rc<Instance<'a>>,
        locals: &Scope<'a>,
        cx: Cx,
    ) -> Result<bool, Fail> {
        let component = Some(instance.occurrence.type_key.as_str());
        match node {
            // `return null` becomes an empty comment vnode.
            Node::Null => {
                self.comment("");
                Ok(false)
            }
            Node::Comment(text) => {
                // Hydration accepts any comment for a comment vnode, but the
                // parse check only knows Vue's own placeholders.
                if text != "v-if" && !text.is_empty() {
                    return Err(Fail::new("unsupported-comment", text.clone(), component));
                }
                self.comment(text);
                Ok(false)
            }
            Node::Text(expr) => {
                let text = display(&eval(expr, instance, locals))
                    .map_err(|reason| Fail::new(reason, "text", component))?;
                self.text(&text, cx, component)?;
                Ok(true)
            }
            Node::Fragment(children) => {
                self.comment("[");
                let mut valid = false;
                for child in children {
                    valid |= self.node(child, instance, locals, cx)?;
                }
                self.comment("]");
                Ok(valid)
            }
            Node::List {
                source,
                params,
                item,
            } => self.list(source, params, item, instance, locals, cx),
            Node::Cond {
                test,
                then,
                otherwise,
            } => match eval(test, instance, locals).truthy() {
                Some(true) => self.node(then, instance, locals, cx),
                Some(false) => self.node(otherwise, instance, locals, cx),
                None => Err(Fail::new("browser-condition", "v-if", component)),
            },
            Node::Element {
                tag,
                props,
                dynamic_props,
                children,
                directives,
            } => self.element(
                tag,
                props.as_ref(),
                dynamic_props.as_deref(),
                children,
                directives,
                instance,
                locals,
            ),
            Node::Component { tag, props, slots } => {
                self.component(tag, props.as_ref(), slots, instance, locals, cx)
            }
            Node::Slot { name, fallback } => {
                self.slot(name, fallback.as_deref(), instance, locals, cx)
            }
            Node::Unsupported(reason) => Err(Fail::new(reason, "render", component)),
        }
    }

    fn list(
        &mut self,
        source: &'a Expr,
        params: &'a [String],
        item: &'a Node,
        instance: &Rc<Instance<'a>>,
        locals: &Scope<'a>,
        cx: Cx,
    ) -> Result<bool, Fail> {
        let component = Some(instance.occurrence.type_key.as_str());
        let items = match eval(source, instance, locals) {
            // Vue's `renderList` renders nothing for these.
            Val::Undefined | Val::Null => &[][..],
            Val::Data(Json::Array(items)) => items.as_slice(),
            Val::Unknown(reason) => return Err(Fail::new(reason, "v-for", component)),
            // Numbers, strings and objects iterate differently; prepared
            // data only ever loops over arrays.
            _ => return Err(Fail::new("browser-list", "v-for", component)),
        };
        if params.len() > 2 {
            return Err(Fail::new("browser-list", "v-for", component));
        }
        self.comment("[");
        let mut valid = false;
        for (index, value) in items.iter().enumerate() {
            let mut scope = locals.clone();
            let bound = [Val::from_json(value), Val::Num(index as f64)];
            for (name, value) in params.iter().zip(bound) {
                scope = Some(Rc::new(Locals {
                    name,
                    value,
                    parent: scope,
                }));
            }
            valid |= self.node(item, instance, &scope, cx)?;
        }
        self.comment("]");
        Ok(valid)
    }

    fn text(&mut self, text: &str, cx: Cx, component: Option<&str>) -> Result<(), Fail> {
        if cx.at_root && !text.is_empty() {
            // Vue expects a vnode directly in the host where text would
            // sit, so the page is left to the browser.
            return Err(Fail::new("host-root", "text", component));
        }
        if !is_whitespace(text)
            && self
                .open
                .last()
                .is_some_and(|parent| TABLE_TEXT_MOVED.contains(parent))
        {
            return Err(Fail::new("parser-repair", "text", component));
        }
        escape_text(&mut self.html, text).map_err(|reason| Fail::new(reason, "text", component))?;
        self.text_token(text);
        Ok(())
    }

    #[allow(clippy::too_many_arguments)]
    fn element(
        &mut self,
        tag: &'a str,
        props: Option<&'a PropsExpr>,
        dynamic_props: Option<&'a [String]>,
        children: &'a Children,
        directives: &'a Directives,
        instance: &Rc<Instance<'a>>,
        locals: &Scope<'a>,
    ) -> Result<bool, Fail> {
        let component = Some(instance.occurrence.type_key.as_str());
        let valid_tag = tag.as_bytes().first().is_some_and(u8::is_ascii_lowercase)
            && tag
                .bytes()
                .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit());
        if !valid_tag || UNWRITTEN_TAGS.contains(&tag) {
            return Err(Fail::new("unsupported-tag", tag, component));
        }
        if self.depth >= MAX_DEPTH {
            return Err(Fail::new("nesting-depth", tag, component));
        }
        if parser_moves(&self.open, tag) {
            // The parent becomes a shell instead, and Vue builds this part
            // with DOM calls, which the parser's repairs do not affect.
            return Err(Fail::new("parser-repair", tag, component));
        }
        // `v-show` is applied by Vue while hydrating (its `beforeMount`
        // hook). Only a value the server knows is false is written, the
        // way the client leaves it.
        let hidden_by_show = match directives {
            Directives::None => false,
            Directives::Show(expr) => eval(expr, instance, locals).truthy() == Some(false),
            Directives::Unsupported(reason) => return Err(Fail::new(reason, tag, component)),
        };
        let (attributes, text_content) = self
            .attributes(tag, props, dynamic_props, hidden_by_show, instance, locals)
            .map_err(|(reason, detail)| Fail::new(reason, detail, component))?;
        let void = VOID_TAGS.contains(&tag);
        if void && !matches!(children, Children::None) {
            // A void element cannot be written with children or as a shell:
            // either would need an end tag, which the parser reads as another
            // element. The parent becomes a shell instead.
            return Err(Fail::new("unsupported-tag", tag, component));
        }
        let v_text = match text_content {
            None => None,
            // An element with no children of its own shows `v-text` as its
            // only content. Hydration neither reads nor compares that text
            // (`hydrateElement` in runtime-core checks children only when
            // the vnode has some), so writing the text Vue sets gives the
            // first paint its content without any mismatch.
            Some(content) if !void && matches!(children, Children::None) => {
                match display(&content.value) {
                    Ok(text) if text_kept_as_written(tag, &text) => Some(text),
                    // For a dynamic key, hydration sets the text itself, so
                    // text the parser would change (a carriage return, text
                    // inside a table part, a leading newline it drops) and
                    // values only the browser knows are left empty.
                    _ if content.patched => None,
                    // A key from a `v-bind` object is not dynamic, and
                    // hydration keeps whatever the server wrote, so the
                    // parent becomes the shell and Vue builds this element.
                    Ok(_) => return Err(Fail::new("text-value", "textContent", component)),
                    Err(reason) => return Err(Fail::new(reason, "textContent", component)),
                }
            }
            // With authored children, hydration either compares the DOM with
            // them (text children, or an empty value) or skips them (element
            // children with a non-empty value), then sets `textContent`, so
            // writing the children is safe either way.
            Some(content) if content.patched => None,
            // Hydration does not set a `textContent` the render does not
            // list as dynamic, and the server cannot write both that text
            // and the children.
            Some(_) => return Err(Fail::new("unsupported-attribute", "textContent", component)),
        };
        let mark = self.mark();
        self.open_tag(tag, &attributes, false);
        let content_start = self.html.len();
        if self.record_events {
            self.events.push(ExpectedNodeEvent::Open {
                tag: tag.to_owned(),
                attributes: attributes
                    .iter()
                    .map(|(name, value)| (name.clone(), Some(value.clone())))
                    .collect(),
            });
        }
        self.element_count += 1;
        self.depth += 1;
        self.open.push(tag);
        let inner = Cx { at_root: false };
        let mut result = match children {
            Children::None => match &v_text {
                Some(text) => self.element_text(tag, text, component),
                None => Ok(()),
            },
            Children::Text(expr) => display(&eval(expr, instance, locals))
                .map_err(|reason| Fail::new(reason, "text", component))
                .and_then(|text| self.element_text(tag, &text, component)),
            Children::Nodes(nodes) => nodes
                .iter()
                .try_for_each(|child| self.node(child, instance, locals, inner).map(|_| ())),
        };
        self.depth -= 1;
        self.open.pop();
        if result.is_ok()
            && LEADING_NEWLINE_TAGS.contains(&tag)
            && self.html[content_start..].starts_with('\n')
        {
            // The browser would drop that newline, while Vue keeps it.
            result = Err(Fail::new("text-value", tag, component));
        }
        match result {
            Ok(()) => {
                if !void {
                    self.html.push_str("</");
                    self.html.push_str(tag);
                    self.html.push('>');
                }
                self.tokens.push(NestingToken::Close);
                if self.record_events {
                    self.events.push(ExpectedNodeEvent::Close {
                        tag: tag.to_owned(),
                    });
                }
            }
            Err(fail) => {
                // The element's own opening is certain; Vue builds what the
                // server could not write inside it in the browser.
                self.rollback(&mark);
                self.open_tag(tag, &attributes, true);
                let shell_content = self.shell_content(tag, children, instance, locals);
                self.html.push_str("</");
                self.html.push_str(tag);
                self.html.push('>');
                // For the parser a shell is an element with no children.
                self.tokens.push(NestingToken::Close);
                if self.record_events {
                    let mut marked = attributes
                        .into_iter()
                        .map(|(name, value)| (name, Some(value)))
                        .collect::<Vec<_>>();
                    marked.push((
                        "data-allow-mismatch".to_owned(),
                        Some("children".to_owned()),
                    ));
                    self.events.push(ExpectedNodeEvent::Shell {
                        tag: tag.to_owned(),
                        attributes: marked,
                    });
                }
                self.element_count += 1;
                self.declines.push(Decline {
                    code: fail.code,
                    detail: fail.detail,
                    component: fail.component,
                    shell_tag: Some(tag.to_owned()),
                    shell_content,
                });
            }
        }
        Ok(true)
    }

    /// Write an element's text content, whether it comes from text children
    /// or from `v-text`.
    fn element_text(&mut self, tag: &str, text: &str, component: Option<&str>) -> Result<(), Fail> {
        if TABLE_TEXT_MOVED.contains(&tag) && !is_whitespace(text) {
            // The parser would move this text out of the table.
            return Err(Fail::new("parser-repair", "text", component));
        }
        escape_text(&mut self.html, text).map_err(|reason| Fail::new(reason, "text", component))?;
        self.text_token(text);
        Ok(())
    }

    fn open_tag(&mut self, tag: &'a str, attributes: &[(String, String)], shell: bool) {
        self.check_attributes(attributes);
        if shell && VOID_TAGS.contains(&tag) {
            // The shell's end tag would be read as another element; `element`
            // never makes a void shell, and the full parse would catch one.
            self.needs_full_parse = true;
        }
        self.tokens.push(NestingToken::Open {
            tag,
            hidden_input: tag == "input"
                && attributes
                    .iter()
                    .any(|(name, value)| name == "type" && value.eq_ignore_ascii_case("hidden")),
        });
        self.nodes_written += 1;
        self.html.push('<');
        self.html.push_str(tag);
        for (name, value) in attributes {
            self.html.push(' ');
            self.html.push_str(name);
            self.html.push_str("=\"");
            escape_attribute(&mut self.html, value);
            self.html.push('"');
        }
        if shell {
            self.html.push_str(" data-allow-mismatch=\"children\"");
        }
        self.html.push('>');
    }

    /// Apply, per request, the attribute rules the token check relies on:
    /// every name is one the tokenizer reads as written and appears once, the
    /// mismatch marker is only the one `open_tag` adds to a shell (after
    /// these attributes), and no value holds a
    /// character the parser changes. Anything else sends the page to the
    /// full parse, which compares every attribute.
    fn check_attributes(&mut self, attributes: &[(String, String)]) {
        for (index, (name, value)) in attributes.iter().enumerate() {
            let bytes = name.as_bytes();
            let plain_name = bytes.first().is_some_and(u8::is_ascii_lowercase)
                && bytes.iter().all(|byte| {
                    byte.is_ascii_lowercase()
                        || byte.is_ascii_digit()
                        || matches!(byte, b'-' | b'_' | b':')
                });
            if !plain_name
                || name == "data-allow-mismatch"
                || value.contains(['\0', '\r'])
                || value.chars().any(tokenizer_reports)
                || attributes[..index]
                    .iter()
                    .any(|(earlier, _)| earlier == name)
            {
                self.needs_full_parse = true;
            }
        }
    }

    /// The attributes the server writes for one element: what Vue's client
    /// render leaves, minus values only the browser knows that hydration
    /// sets itself. The element's `textContent` prop (what `v-text`
    /// compiles to) is not an attribute, so it is returned beside them for
    /// [`Writer::element`] to write as the element's text.
    #[allow(clippy::too_many_arguments)]
    fn attributes(
        &self,
        tag: &str,
        props: Option<&'a PropsExpr>,
        dynamic_props: Option<&'a [String]>,
        hidden_by_show: bool,
        instance: &Instance<'a>,
        locals: &Scope<'a>,
    ) -> Result<ElementAttributes<'a>, (&'static str, String)> {
        let mut values = Vec::new();
        if let Some(props) = props {
            eval_props(props, instance, locals, &mut values)
                .map_err(|reason| (reason, tag.to_owned()))?;
        }
        // Keys hydration applies itself instead of trusting the HTML
        // (`hydrateElement` in runtime-core).
        let force_patch = matches!(tag, "input" | "option");
        let mut attributes = Vec::with_capacity(values.len());
        let mut text_content = None;
        for (key, value) in &values {
            let key = key.as_ref();
            if is_reserved(key) {
                continue;
            }
            let value = match value {
                // Hydration attaches every listener itself.
                PropVal::Listener => continue,
                PropVal::Value(value) => value,
            };
            if is_listener_key(key) {
                continue;
            }
            if key == "data-allow-mismatch" {
                // This attribute would hide mismatches the server claims to
                // have checked.
                return Err(("unsupported-attribute", key.to_owned()));
            }
            let patched = (force_patch && (key.ends_with("value") || key == "indeterminate"))
                || dynamic_props.is_some_and(|keys| keys.iter().any(|name| name == key));
            if key == "textContent" {
                // Vue sets this as the element's text, never as an
                // attribute; the caller decides whether the server can
                // write that text.
                text_content = Some(TextContent {
                    value: value.clone(),
                    patched,
                });
                continue;
            }
            match client_attribute(tag, key, value) {
                Ok(Some(text)) if text.contains(['\0', '\r']) => {
                    return Err(("text-value", key.to_owned()));
                }
                Ok(Some(text)) => attributes.push((key.to_owned(), text)),
                Ok(None) => {}
                // Hydration sets a patched key itself, so a value the server
                // cannot write is left out.
                Err(_) if patched => {}
                Err(reason) => return Err((reason, key.to_owned())),
            }
        }
        if hidden_by_show {
            if attributes.iter().any(|(name, _)| name == "style") {
                return Err(("unsupported-attribute", "style".to_owned()));
            }
            attributes.push(("style".to_owned(), "display: none;".to_owned()));
        }
        Ok((attributes, text_content))
    }

    fn component(
        &mut self,
        tag: &str,
        props: Option<&'a PropsExpr>,
        slots: &'a Result<Vec<SlotDef>, &'static str>,
        instance: &Rc<Instance<'a>>,
        locals: &Scope<'a>,
        cx: Cx,
    ) -> Result<bool, Fail> {
        let component = Some(instance.occurrence.type_key.as_str());
        let mut values = Vec::new();
        if let Some(props) = props {
            eval_props(props, instance, locals, &mut values)
                .map_err(|reason| Fail::new(reason, tag, component))?;
        }
        if tag == "citry-opaque-html" {
            return self.opaque_html(&values, component);
        }
        let mut id = None;
        for (key, value) in &values {
            match (key.as_ref(), value) {
                ("citry-id", PropVal::Value(Val::Str(value))) => id = Some(value.clone()),
                ("key", _) => {}
                // Anything else falls through to the child's root element
                // as attributes or listeners, which is not modelled.
                _ => return Err(Fail::new("component-attrs", key.as_ref(), component)),
            }
        }
        let id = id.ok_or_else(|| Fail::new("component-lookup", tag, component))?;
        let occurrence = self
            .occurrences
            .get(id.as_ref())
            .copied()
            .ok_or_else(|| Fail::new("component-lookup", tag, component))?;
        if self.tags.get(&occurrence.type_key).map(String::as_str) != Some(tag) {
            return Err(Fail::new("component-lookup", tag, component));
        }
        let slots = slots
            .as_ref()
            .map_err(|reason| Fail::new(reason, tag, component))?;
        let bindings = slots
            .iter()
            .map(|def| SlotBinding {
                def,
                owner: Rc::clone(instance),
                locals: locals.clone(),
            })
            .collect();
        self.occurrence(occurrence, bindings, cx)
    }

    /// Write a raw HTML block (`<c-raw>` contents or trusted `Markup` with
    /// tags) for Vue to adopt.
    ///
    /// In the browser the block is a Fragment holding one static vnode with
    /// the record's `nodeCount` (`citry-opaque-html` in client.js). Vue
    /// hydrates a static vnode by stepping over that many DOM nodes without
    /// reading them, so the server writes the block's HTML unchanged between
    /// the Fragment's comments, after checking that the browser's parse of
    /// the page gives the block exactly the nodes Vue would insert.
    fn opaque_html(&mut self, values: &Props<'a>, component: Option<&str>) -> Result<bool, Fail> {
        let fail = || Fail::new("opaque-html", "citry-opaque-html", component);
        let mut record = None;
        for (key, value) in values {
            match (key.as_ref(), value) {
                ("record", PropVal::Value(Val::Data(Json::Object(map)))) => record = Some(map),
                ("key", _) => {}
                _ => return Err(fail()),
            }
        }
        let record = record.ok_or_else(fail)?;
        // A `#c-ignore` element's contents arrive as a record with
        // `"pinned": true`, which only tells the browser to keep the first
        // nodes it has; the server writes them the same way.
        let pinned = match record.get("pinned") {
            None => false,
            Some(Json::Bool(true)) => true,
            Some(_) => return Err(fail()),
        };
        let (Some(Json::String(html)), Some(node_count), true) = (
            record.get("html"),
            record.get("nodeCount").and_then(Json::as_u64),
            record.len() == 2 + usize::from(pinned),
        ) else {
            return Err(fail());
        };
        let facts = static_html_in_context(&self.open, html, StaticHtmlUse::Adopted)
            .filter(|facts| facts.node_count as u64 == node_count)
            .ok_or_else(fail)?;
        self.comment("[");
        let start = self.html.len();
        self.html.push_str(html);
        self.checked_ranges.push((start, self.html.len()));
        self.comment("]");
        self.element_count += facts.element_count;
        Ok(true)
    }

    /// Write HTML for a shell's contents from the values the server has, so
    /// the served page shows them before the browser runtime starts. Returns
    /// whether it was written.
    ///
    /// Vue does not correct attributes on elements it adopts inside a shell,
    /// so the browser runtime removes these contents right before Vue
    /// hydrates, and Vue builds the shell's children anew. The contents come
    /// from the same render code (see [`StaticWriter`]). They are
    /// left out when the browser's parse would move them, or when they hold
    /// something that would run or load a second time once Vue rebuilds
    /// them (see [`StaticHtmlUse::Replaced`]).
    fn shell_content(
        &mut self,
        tag: &'a str,
        children: &'a Children,
        instance: &Rc<Instance<'a>>,
        locals: &Scope<'a>,
    ) -> bool {
        let mut writer = StaticWriter {
            programs: self.programs,
            tags: self.tags,
            occurrences: self.occurrences,
            html: String::new(),
            depth: self.depth,
        };
        // `v-text` text never makes its own element a shell (it is written
        // or left out before the element opens), so only children remain.
        writer.children(tag, children, instance, locals);
        if writer.html.is_empty() || writer.html.len() > MAX_SHELL_CONTENT {
            return false;
        }
        self.open.push(tag);
        let facts = static_html_in_context(&self.open, &writer.html, StaticHtmlUse::Replaced);
        self.open.pop();
        if facts.is_none() {
            return false;
        }
        let start = self.html.len();
        self.html.push_str(&writer.html);
        self.checked_ranges.push((start, self.html.len()));
        true
    }

    fn slot(
        &mut self,
        name: &str,
        fallback: Option<&'a [Node]>,
        instance: &Rc<Instance<'a>>,
        locals: &Scope<'a>,
        cx: Cx,
    ) -> Result<bool, Fail> {
        let component = Some(instance.occurrence.type_key.as_str());
        // `renderSlot` always returns a Fragment.
        self.comment("[");
        let inner = cx;
        let mut valid = false;
        if let Some(binding) = instance
            .slots
            .iter()
            .find(|binding| binding.def.name == name)
        {
            if binding.def.params != 0 {
                return Err(Fail::new("slot-props", name, component));
            }
            let mark = self.mark();
            for child in &binding.def.body {
                valid |= self.node(child, &binding.owner, &binding.locals, inner)?;
            }
            if !valid {
                // Only comments or empty Fragments: `ensureValidVNode`
                // treats the slot as not supplied.
                self.rollback(&mark);
            }
        }
        if !valid && let Some(fallback) = fallback {
            for child in fallback {
                valid |= self.node(child, instance, locals, inner)?;
            }
        }
        self.comment("]");
        Ok(valid)
    }
}

/// A shell whose contents grow past this many bytes is written empty.
/// Every branch of a condition only the browser can test is written, so
/// conditions nested in each other around a slot could otherwise multiply the
/// same content many times.
const MAX_SHELL_CONTENT: usize = 1 << 20;

/// The class or style text a shell's contents show for an element whose
/// value has a browser-only part: Vue's rules applied to the parts the
/// server can read, the others left out. `None` when nothing is known.
fn known_class_or_style<'a>(
    key: &str,
    props: &'a PropsExpr,
    instance: &Instance<'a>,
    locals: &Scope<'a>,
) -> Option<String> {
    let mut parts = Vec::new();
    known_parts(key, props, instance, locals, &mut parts);
    let parts = Val::Array(Rc::new(parts));
    let text = if key == "class" {
        normalize_class(&parts, Parts::Known).ok()?
    } else {
        stringify_style(&style_entries(&parts, Parts::Known).ok()??, Parts::Known).ok()??
    };
    (!text.is_empty()).then_some(text)
}

/// Collect every value a props expression gives `key`, in the order
/// `mergeProps` combines them. Vue normalizes a class or style the same way
/// whether its parts arrive one by one or as one array, so the caller
/// normalizes the list once.
fn known_parts<'a>(
    key: &str,
    props: &'a PropsExpr,
    instance: &Instance<'a>,
    locals: &Scope<'a>,
    parts: &mut Vec<Val<'a>>,
) {
    match props {
        PropsExpr::Object(entries) => {
            // In one object literal the last value for a key wins.
            if let Some(PropValue::Value(expr)) = entries
                .iter()
                .rev()
                .find(|entry| entry.key == key)
                .map(|entry| &entry.value)
            {
                // Read the value inside `normalizeClass(...)` or
                // `normalizeStyle(...)`, which would otherwise turn a
                // partly known value into an unknown one.
                let expr = match expr {
                    Expr::NormalizeClass(inner) | Expr::NormalizeStyle(inner) => inner,
                    other => other,
                };
                parts.push(eval(expr, instance, locals));
            }
        }
        PropsExpr::Merge(items) => {
            for item in items {
                known_parts(key, item, instance, locals, parts);
            }
        }
        PropsExpr::Normalize(inner) => known_parts(key, inner, instance, locals, parts),
        PropsExpr::Spread(expr) => match eval(expr, instance, locals) {
            Val::Data(Json::Object(map)) => {
                if let Some(value) = map.get(key) {
                    parts.push(Val::from_json(value));
                }
            }
            Val::Object(entries) => {
                if let Some((_, value)) = entries.iter().find(|(name, _)| name == key) {
                    parts.push(value.clone());
                }
            }
            _ => {}
        },
        PropsExpr::Unsupported(_) => {}
    }
}

/// Writes a shell's contents from the same render code and data, showing
/// what the server can know before Vue runs.
///
/// These contents are only shown until the browser runtime removes them and
/// Vue builds the shell's children, so they need not match Vue's first
/// render: a condition the server can test shows its branch and one only the
/// browser can test shows every branch, a list or text only the browser
/// knows is left out, listeners and directives other than a `v-show` known
/// to be false are ignored, and attributes are written from the values the
/// server has. Anything the server cannot read is left out rather than
/// guessed.
struct StaticWriter<'a> {
    programs: &'a HashMap<String, &'a ServerRenderProgram>,
    tags: &'a HashMap<String, String>,
    occurrences: &'a HashMap<&'a str, &'a OccurrenceInput>,
    html: String,
    depth: usize,
}

impl<'a> StaticWriter<'a> {
    /// Write an element's children.
    fn children(
        &mut self,
        tag: &str,
        children: &'a Children,
        instance: &Rc<Instance<'a>>,
        locals: &Scope<'a>,
    ) {
        match children {
            Children::None => {}
            Children::Text(expr) => {
                if let Ok(text) = display(&eval(expr, instance, locals)) {
                    self.text(tag, &text);
                }
            }
            Children::Nodes(nodes) => {
                for node in nodes {
                    self.node(node, instance, locals);
                }
            }
        }
    }

    /// Write an element's text content.
    fn text(&mut self, tag: &str, text: &str) {
        // The parser drops a newline right after these tags, and Vue's
        // client keeps it, so write the one Vue would show.
        if LEADING_NEWLINE_TAGS.contains(&tag) && text.starts_with('\n') {
            self.html.push('\n');
        }
        static_text(&mut self.html, text);
    }

    fn node(&mut self, node: &'a Node, instance: &Rc<Instance<'a>>, locals: &Scope<'a>) {
        // Same depth limit as the writer: deeper content is left out. Past
        // the size limit the contents are dropped anyway, so writing stops.
        if self.depth >= MAX_DEPTH || self.html.len() > MAX_SHELL_CONTENT {
            return;
        }
        self.depth += 1;
        self.write_node(node, instance, locals);
        self.depth -= 1;
    }

    fn write_node(&mut self, node: &'a Node, instance: &Rc<Instance<'a>>, locals: &Scope<'a>) {
        match node {
            Node::Null | Node::Comment(_) | Node::Unsupported(_) => {}
            Node::Text(expr) => {
                if let Ok(text) = display(&eval(expr, instance, locals)) {
                    static_text(&mut self.html, &text);
                }
            }
            Node::Fragment(children) => {
                for child in children {
                    self.node(child, instance, locals);
                }
            }
            Node::List {
                source,
                params,
                item,
            } => {
                // A list only the browser knows is left out.
                let Val::Data(Json::Array(items)) = eval(source, instance, locals) else {
                    return;
                };
                for (index, value) in items.iter().enumerate() {
                    let mut scope = locals.clone();
                    let bound = [Val::from_json(value), Val::Num(index as f64)];
                    for (name, value) in params.iter().zip(bound) {
                        scope = Some(Rc::new(Locals {
                            name,
                            value,
                            parent: scope,
                        }));
                    }
                    self.node(item, instance, &scope);
                }
            }
            Node::Cond {
                test,
                then,
                otherwise,
            } => match eval(test, instance, locals).truthy() {
                Some(true) => self.node(then, instance, locals),
                Some(false) => self.node(otherwise, instance, locals),
                // Citry's static HTML shows every branch of a condition only
                // the browser can test.
                None => {
                    self.node(then, instance, locals);
                    self.node(otherwise, instance, locals);
                }
            },
            Node::Element {
                tag,
                props,
                children,
                directives,
                ..
            } => self.element(tag, props.as_ref(), children, directives, instance, locals),
            Node::Component { tag, props, slots } => {
                self.component(tag, props.as_ref(), slots, instance, locals);
            }
            Node::Slot { name, fallback } => {
                let before = self.html.len();
                if let Some(binding) = instance
                    .slots
                    .iter()
                    .find(|binding| binding.def.name == *name)
                {
                    // A scoped slot's parameters are only known in the
                    // browser, so what reads them is left out.
                    for child in &binding.def.body {
                        self.node(child, &binding.owner, &binding.locals);
                    }
                }
                if self.html.len() == before
                    && let Some(fallback) = fallback
                {
                    for child in fallback {
                        self.node(child, instance, locals);
                    }
                }
            }
        }
    }

    fn element(
        &mut self,
        tag: &'a str,
        props: Option<&'a PropsExpr>,
        children: &'a Children,
        directives: &'a Directives,
        instance: &Rc<Instance<'a>>,
        locals: &Scope<'a>,
    ) {
        // SVG and MathML tags keep their capital letters; anything that is
        // not a plain tag name is left out.
        let bytes = tag.as_bytes();
        if !bytes.first().is_some_and(u8::is_ascii_alphabetic)
            || !bytes
                .iter()
                .all(|byte| byte.is_ascii_alphanumeric() || *byte == b'-')
        {
            return;
        }
        let mut values = Vec::new();
        if let Some(props) = props {
            // A spread only the browser knows leaves the keys read so far.
            let _ = eval_props(props, instance, locals, &mut values);
        }
        self.html.push('<');
        self.html.push_str(tag);
        let mut style = None;
        for (key, value) in &values {
            let PropVal::Value(value) = value else {
                continue;
            };
            let key = key.as_ref();
            if is_reserved(key)
                || is_listener_key(key)
                || !is_static_attribute_name(key)
                || matches!(key, "innerHTML" | "textContent" | "data-allow-mismatch")
            {
                continue;
            }
            let text = match (static_attribute(tag, key, value), key, props) {
                (Some(text), _, _) => text,
                // A class or style with a browser-only part still shows the
                // parts the server knows, such as a static `class` beside a
                // `:class` that reads `data()`, so the element is styled
                // before Vue runs.
                (None, "class" | "style", Some(props)) => {
                    match known_class_or_style(key, props, instance, locals) {
                        Some(text) => text,
                        None => continue,
                    }
                }
                (None, _, _) => continue,
            };
            if key == "style" {
                style = Some(text);
                continue;
            }
            push_attribute(&mut self.html, key, &text);
        }
        // `v-show` with a value the server knows is false hides the element,
        // as Vue will.
        let hidden = matches!(directives, Directives::Show(expr)
            if eval(expr, instance, locals).truthy() == Some(false));
        match (style, hidden) {
            (Some(style), true) => {
                // A style written as Vue's server renderer writes it already
                // ends with a semicolon.
                let style = style.trim_end().trim_end_matches(';');
                push_attribute(&mut self.html, "style", &format!("{style};display: none;"))
            }
            (None, true) => push_attribute(&mut self.html, "style", "display: none;"),
            (Some(style), false) => push_attribute(&mut self.html, "style", &style),
            (None, false) => {}
        }
        self.html.push('>');
        if VOID_TAGS.contains(&tag) {
            return;
        }
        // `v-text` on an element with no children of its own is its text,
        // shown when the server knows the value.
        let v_text = values.iter().find_map(|(key, value)| match value {
            PropVal::Value(value) if key == "textContent" => display(value).ok(),
            _ => None,
        });
        match (children, v_text) {
            (Children::None, Some(text)) => self.text(tag, &text),
            _ => self.children(tag, children, instance, locals),
        }
        self.html.push_str("</");
        self.html.push_str(tag);
        self.html.push('>');
    }

    fn component(
        &mut self,
        tag: &str,
        props: Option<&'a PropsExpr>,
        slots: &'a Result<Vec<SlotDef>, &'static str>,
        instance: &Rc<Instance<'a>>,
        locals: &Scope<'a>,
    ) {
        let mut values = Vec::new();
        if let Some(props) = props
            && eval_props(props, instance, locals, &mut values).is_err()
        {
            return;
        }
        let value = |name: &str| {
            values.iter().find_map(|(key, value)| match value {
                PropVal::Value(value) if key == name => Some(value.clone()),
                _ => None,
            })
        };
        if tag == "citry-opaque-html" {
            // The record's HTML, as the page shows it.
            if let Some(Val::Data(Json::Object(record))) = value("record")
                && let Some(Json::String(html)) = record.get("html")
            {
                self.html.push_str(html);
            }
            return;
        }
        let Some(Val::Str(id)) = value("citry-id") else {
            return;
        };
        let Some(occurrence) = self.occurrences.get(id.as_ref()).copied() else {
            return;
        };
        if self.tags.get(&occurrence.type_key).map(String::as_str) != Some(tag) {
            return;
        }
        let Some(program) = self.programs.get(&occurrence.definition_id).copied() else {
            return;
        };
        let bindings = slots
            .as_ref()
            .map(|slots| {
                slots
                    .iter()
                    .map(|def| SlotBinding {
                        def,
                        owner: Rc::clone(instance),
                        locals: locals.clone(),
                    })
                    .collect()
            })
            .unwrap_or_default();
        let child = Rc::new(Instance {
            occurrence,
            slots: bindings,
        });
        self.node(&program.root, &child, &None);
    }
}

/// Whether the HTML tokenizer reads `name` as one attribute name exactly as
/// written (SVG attributes such as `viewBox` keep their capital letters).
fn is_static_attribute_name(name: &str) -> bool {
    let bytes = name.as_bytes();
    bytes.first().is_some_and(u8::is_ascii_alphabetic)
        && bytes
            .iter()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_' | b':' | b'.'))
}

/// The attribute text Citry's static HTML shows for one prop, or `None`
/// when the server does not know it or the attribute is absent.
fn static_attribute(tag: &str, key: &str, value: &Val<'_>) -> Option<String> {
    match client_attribute(tag, key, value) {
        Ok(text) => text,
        // A name Vue sets through a path the hydration writer does not
        // model still shows its plain value here.
        Err(_) => match value {
            Val::Str(text) => Some(text.to_string()),
            Val::Num(number) => js_number(*number),
            Val::Bool(true) => Some(String::new()),
            _ => None,
        },
    }
}

fn push_attribute(output: &mut String, name: &str, value: &str) {
    output.push(' ');
    output.push_str(name);
    output.push_str("=\"");
    escape_attribute(output, value);
    output.push('"');
}

/// Escape text for shell contents. A carriage return changes the contents'
/// own parse the same way as the page's, which the check in
/// [`static_html_in_context`] compares, so it is kept.
fn static_text(output: &mut String, text: &str) {
    for character in text.chars() {
        match character {
            '&' => output.push_str("&amp;"),
            '<' => output.push_str("&lt;"),
            '>' => output.push_str("&gt;"),
            // The parser drops NUL from text anyway.
            '\0' => {}
            other => output.push(other),
        }
    }
}

/// Whether the tokenizer of the full parse reports this character as an
/// error (a control character other than whitespace and NUL, or a Unicode
/// noncharacter). The browser keeps such text, but the full parse rejects
/// the page, so the token check leaves that decision to it.
fn tokenizer_reports(character: char) -> bool {
    let code = u32::from(character);
    matches!(code, 0x01..=0x08 | 0x0B | 0x0E..=0x1F | 0x7F..=0x9F)
        || (0xFDD0..=0xFDEF).contains(&code)
        || (code & 0xFFFE) == 0xFFFE
}

/// Whether text is only HTML whitespace, which the parser keeps in place
/// inside table parts.
fn is_whitespace(text: &str) -> bool {
    text.chars()
        .all(|character| matches!(character, '\t' | '\n' | '\u{c}' | '\r' | ' '))
}

/// Whether the parser keeps `text` written as the only content of `tag`
/// exactly as Vue sets it: the checks [`Writer::element`] and
/// [`Writer::element_text`] apply to text content, made before anything
/// is written.
fn text_kept_as_written(tag: &str, text: &str) -> bool {
    !text.contains(['\r', '\0'])
        && !(TABLE_TEXT_MOVED.contains(&tag) && !is_whitespace(text))
        && !(LEADING_NEWLINE_TAGS.contains(&tag) && text.starts_with('\n'))
}

/// Escape text content. The parser turns a raw carriage return into a
/// newline and drops NUL, so text holding either is left to the browser.
fn escape_text(output: &mut String, text: &str) -> Result<(), &'static str> {
    for character in text.chars() {
        match character {
            '&' => output.push_str("&amp;"),
            '<' => output.push_str("&lt;"),
            '>' => output.push_str("&gt;"),
            '\r' | '\0' => return Err("text-value"),
            other => output.push(other),
        }
    }
    Ok(())
}

/// Escape an attribute value; callers reject carriage returns and NUL first.
fn escape_attribute(output: &mut String, value: &str) {
    for character in value.chars() {
        match character {
            '&' => output.push_str("&amp;"),
            '"' => output.push_str("&quot;"),
            other => output.push(other),
        }
    }
}

#[cfg(test)]
mod tests {
    use std::collections::HashMap;

    use serde_json::{Value, json};

    use super::{
        HydrationRender, RenderRequest, ServerRenderProgram, Val, client_attribute, parser_moves,
        read_program, render_for_hydration,
    };
    use crate::{CompileRequest, compile};

    type Component<'a> = (&'a str, &'a str, Value, Value);

    fn program(template: &str) -> ServerRenderProgram {
        let artifact = compile(CompileRequest {
            template: template.to_owned(),
            local_calls: Vec::new(),
            local_call_runs: Vec::new(),
            element_bindings: Vec::new(),
            dynamic_elements: Vec::new(),
        });
        assert!(
            artifact.diagnostics.is_empty(),
            "{:?}",
            artifact.diagnostics
        );
        read_program(&artifact.code, &[]).expect("render function reads")
    }

    /// Render a page of `(type key, template, preparedData, serverData)`
    /// components; the first is the root. Occurrence ids are `occ-<type>`
    /// and each type's tag is `citry-<type in lower case>`.
    fn render(components: &[Component<'_>], threshold: usize) -> HydrationRender {
        let programs = components
            .iter()
            .map(|(type_key, template, _, _)| ((*type_key).to_owned(), program(template)))
            .collect::<Vec<_>>();
        let program_refs = programs
            .iter()
            .map(|(id, program)| (format!("def-{id}"), program))
            .collect::<HashMap<_, _>>();
        let occurrences = components
            .iter()
            .map(|(type_key, _, prepared, server)| {
                json!({
                    "id": format!("occ-{type_key}"),
                    "typeKey": type_key,
                    "definitionId": format!("def-{type_key}"),
                    "preparedData": prepared,
                    "serverData": server,
                })
            })
            .collect::<Vec<_>>();
        let manifest =
            json!({"rootId": format!("occ-{}", components[0].0), "occurrences": occurrences})
                .to_string();
        let tags = components
            .iter()
            .map(|(type_key, _, _, _)| {
                (
                    (*type_key).to_owned(),
                    format!("citry-{}", type_key.to_lowercase()),
                )
            })
            .collect::<HashMap<_, _>>();
        let request = |full_parse_check| RenderRequest {
            programs: &program_refs,
            manifest_json: &manifest,
            tags: &tags,
            threshold,
            full_parse_check,
        };
        let result = render_for_hydration(&request(false));
        // The token check must reach the same answer as parsing the whole
        // written HTML, on every page these tests write.
        let full = render_for_hydration(&request(true));
        assert_eq!(result.html, full.html);
        assert_eq!(result.reason, full.reason);
        assert_eq!(result.element_count, full.element_count);
        assert_eq!(result.declines, full.declines);
        result
    }

    fn root(template: &str, prepared: Value) -> HydrationRender {
        render(&[("Root", template, prepared, json!({}))], 0)
    }

    fn with_child(template: &str, prepared: Value, child: &str) -> HydrationRender {
        render(
            &[
                ("Root", template, prepared, json!({})),
                ("Child", child, json!({}), json!({})),
            ],
            0,
        )
    }

    fn html(result: &HydrationRender) -> &str {
        result
            .html
            .as_deref()
            .unwrap_or_else(|| panic!("the page hydrates: {:?}", result.declines))
    }

    fn declines(result: &HydrationRender) -> Vec<(&str, &str, Option<&str>)> {
        result
            .declines
            .iter()
            .map(|decline| {
                (
                    decline.code,
                    decline.detail.as_str(),
                    decline.shell_tag.as_deref(),
                )
            })
            .collect()
    }

    const LIST: &str = r#"<ul><li v-for="item in $citryPrepared.items">{{ item }}</li></ul>"#;

    #[test]
    fn lists_write_one_fragment_around_all_items_even_when_empty() {
        assert_eq!(
            html(&root(LIST, json!({"items": []}))),
            "<ul><!--[--><!--]--></ul>"
        );
        assert_eq!(
            html(&root(LIST, json!({"items": ["only"]}))),
            "<ul><!--[--><li>only</li><!--]--></ul>"
        );
        let many = root(LIST, json!({"items": ["a", "b", "c"]}));
        assert_eq!(
            html(&many),
            "<ul><!--[--><li>a</li><li>b</li><li>c</li><!--]--></ul>"
        );
        assert_eq!(many.element_count, 4);
    }

    #[test]
    fn template_loop_items_and_multi_root_renders_get_their_own_fragments() {
        let rows = root(
            r#"<div><template v-for="row in $citryPrepared.rows"><b>{{ row.a }}</b><i>{{ row.b }}</i></template></div>"#,
            json!({"rows": [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]}),
        );
        assert_eq!(
            html(&rows),
            "<div><!--[--><!--[--><b>1</b><i>2</i><!--]--><!--[--><b>3</b><i>4</i><!--]--><!--]--></div>"
        );
        assert_eq!(
            html(&root("<p>a</p><p>b</p>", json!({}))),
            "<!--[--><p>a</p><p>b</p><!--]-->"
        );
        let branch = root(
            r#"<div><template v-if="$citryPrepared.on"><b>a</b><i>b</i></template></div>"#,
            json!({"on": true}),
        );
        assert_eq!(html(&branch), "<div><!--[--><b>a</b><i>b</i><!--]--></div>");
    }

    #[test]
    fn empty_conditions_and_empty_renders_write_vue_placeholders() {
        let chain = root(
            r#"<div><p v-if="$citryPrepared.n === 0">zero</p><p v-else-if="$citryPrepared.n === 1">one</p></div>"#,
            json!({"n": 2}),
        );
        assert_eq!(html(&chain), "<div><!--v-if--></div>");
        let tag = r#"<main><citry-child :citry-id="$citryPrepared.child"></citry-child></main>"#;
        let child = json!({"child": "occ-Child"});
        assert_eq!(
            html(&with_child(tag, child.clone(), "")),
            "<main><!----></main>"
        );
        assert_eq!(
            html(&with_child(
                tag,
                child,
                r#"<p v-if="$citryPrepared.never">x</p>"#
            )),
            "<main><!--v-if--></main>"
        );
    }

    #[test]
    fn python_values_become_the_attributes_vue_sets() {
        // Spread names vary per row; `true` becomes "true" on a custom
        // attribute, null removes it, and numbers print as JavaScript does.
        let rows = root(
            r#"<div><article v-for="row in $citryPrepared.rows" v-bind="row.attrs">{{ row.t }}</article></div>"#,
            json!({"rows": [
                {"attrs": {"id": "a", "data-on": true, "data-n": 0, "data-gone": null}, "t": "x"},
                {"attrs": {"data-other": false, "title": "t"}, "t": "y"},
            ]}),
        );
        assert_eq!(
            html(&rows),
            r#"<div><!--[--><article data-n="0" data-on="true" id="a">x</article><article data-other="false" title="t">y</article><!--]--></div>"#
        );
        let classes = root(
            r#"<p class="a" v-bind="$citryPrepared.attrs">x</p>"#,
            json!({"attrs": {"class": ["b", {"c": true, "d": false}]}}),
        );
        assert_eq!(html(&classes), r#"<p class="a b c">x</p>"#);
        // Vue also writes `value`, `checked` and `selected` as attributes.
        let inputs = root(
            r#"<form><input value="typed"><input type="hidden" value="h"><input type="checkbox" :checked="$citryPrepared.c" value="on"></form>"#,
            json!({"c": true}),
        );
        assert_eq!(
            html(&inputs),
            r#"<form><input value="typed"><input type="hidden" value="h"><input type="checkbox" checked="" value="on"></form>"#
        );
        let server_data = render(
            &[(
                "Root",
                r#"<p :data-tab="tab_id">x</p>"#,
                json!({}),
                json!({"tab_id": "one"}),
            )],
            0,
        );
        assert_eq!(html(&server_data), r#"<p data-tab="one">x</p>"#);
        // An image's loading hints are written, so the server image matches
        // the one Vue would create.
        let image = root(
            r#"<img alt="" v-bind="$citryPrepared.attrs">"#,
            json!({"attrs": {"fetchpriority": "high", "loading": "lazy"}}),
        );
        assert_eq!(
            html(&image),
            r#"<img alt="" fetchpriority="high" loading="lazy">"#
        );
    }

    #[test]
    fn values_hydration_sets_itself_are_left_out() {
        // Listeners, keys the render marks dynamic and `v-show` are applied
        // by Vue while it hydrates, so browser-only values there are fine.
        let toggle = root(
            r#"<div><button @click="open = !open" :aria-expanded="open">Toggle</button><p :hidden="!open" v-show="open">x</p></div>"#,
            json!({}),
        );
        assert_eq!(html(&toggle), "<div><button>Toggle</button><p>x</p></div>");
        assert!(toggle.declines.is_empty());
        // A v-show the server knows is false is written the way Vue leaves it.
        let shown = root(
            r#"<div><p v-show="$citryPrepared.on">x</p><p v-show="!$citryPrepared.on">y</p></div>"#,
            json!({"on": false}),
        );
        assert_eq!(
            html(&shown),
            r#"<div><p style="display: none;">x</p><p>y</p></div>"#
        );
    }

    #[test]
    fn browser_only_content_turns_the_nearest_element_into_a_shell() {
        let text = root("<main><span>{{ open }}</span><p>kept</p></main>", json!({}));
        assert_eq!(
            html(&text),
            r#"<main><span data-allow-mismatch="children"></span><p>kept</p></main>"#
        );
        assert_eq!(declines(&text), [("browser-value", "text", Some("span"))]);
        assert_eq!(text.shell_count, 1);
        let condition = root(
            r#"<main><section><p v-if="open">x</p></section><p>kept</p></main>"#,
            json!({}),
        );
        assert_eq!(
            html(&condition),
            r#"<main><section data-allow-mismatch="children"><p>x</p></section><p>kept</p></main>"#
        );
        assert_eq!(
            declines(&condition),
            [("browser-condition", "v-if", Some("section"))]
        );
        // A dynamic key is patched by hydration, so a browser value there is
        // left out; a browser-only spread is not, so the parent is the shell.
        let patched = root(r#"<main><p :title="label">x</p></main>"#, json!({}));
        assert_eq!(html(&patched), "<main><p>x</p></main>");
        let spread = root(r#"<main><p v-bind="extra">x</p></main>"#, json!({}));
        assert_eq!(
            html(&spread),
            r#"<main data-allow-mismatch="children"><p>x</p></main>"#
        );
        assert_eq!(declines(&spread), [("browser-value", "p", Some("main"))]);
        // With no element around it, the page mounts in the browser.
        let page = root("<p>{{ open }}</p><p>b</p>", json!({}));
        assert_eq!(
            html(&page),
            r#"<!--[--><p data-allow-mismatch="children"></p><p>b</p><!--]-->"#
        );
        let host = root("text<p>x</p>", json!({}));
        assert_eq!(host.html, None);
        assert_eq!(host.reason, Some("host-root"));
        assert_eq!(declines(&host), [("host-root", "text", None)]);
    }

    #[test]
    fn text_is_escaped_and_characters_html_cannot_carry_are_left_to_the_browser() {
        let entities = root(
            r#"<p title="a &amp; &quot;b&quot;">{{ $citryPrepared.t }}</p>"#,
            json!({"t": "<b>&amp;</b>"}),
        );
        assert_eq!(
            html(&entities),
            r#"<p title="a &amp; &quot;b&quot;">&lt;b&gt;&amp;amp;&lt;/b&gt;</p>"#
        );
        // The shell's contents show the text as the parser keeps it.
        for (value, shown) in [("a\u{0}b", "ab"), ("a\rb", "a\rb")] {
            let result = root(
                "<main><p>{{ $citryPrepared.t }}</p></main>",
                json!({"t": value}),
            );
            assert_eq!(
                html(&result),
                format!(r#"<main><p data-allow-mismatch="children">{shown}</p></main>"#)
            );
            assert_eq!(declines(&result), [("text-value", "text", Some("p"))]);
        }
        // The parser drops a newline right after <textarea>; Vue keeps it.
        let textarea = root(
            "<form><textarea>{{ $citryPrepared.t }}</textarea></form>",
            json!({"t": "\nfirst"}),
        );
        assert_eq!(
            html(&textarea),
            r#"<form><textarea data-allow-mismatch="children"></textarea></form>"#
        );
        let plain = root(
            "<label>Description <textarea>{{ $citryPrepared.t }}</textarea></label>",
            json!({"t": "a < b"}),
        );
        assert_eq!(
            html(&plain),
            "<label>Description <textarea>a &lt; b</textarea></label>"
        );
        let void = root(r#"<p>a<br>b<img src="/x.png" alt=""></p>"#, json!({}));
        assert_eq!(html(&void), r#"<p>a<br>b<img src="/x.png" alt=""></p>"#);
        assert_eq!(void.element_count, 3);
    }

    #[test]
    fn slots_write_a_fragment_around_supplied_or_fallback_content() {
        let result = with_child(
            r#"<main><citry-child :citry-id="$citryPrepared.child"><template #default><b>fill {{ $citryPrepared.x }}</b></template><template #other><template v-if="$citryPrepared.never"><i>no</i></template></template></citry-child></main>"#,
            json!({"child": "occ-Child", "x": "X", "never": false}),
            r#"<section><slot></slot><slot name="other"><u>fallback</u></slot><slot name="missing"></slot></section>"#,
        );
        // The fill reads its writer's data; a fill that renders only a
        // placeholder counts as not supplied, so the fallback shows.
        assert_eq!(
            html(&result),
            "<main><section><!--[--><b>fill X</b><!--]--><!--[--><u>fallback</u><!--]--><!--[--><!--]--></section></main>"
        );
    }

    #[test]
    fn component_calls_with_extra_attributes_are_shells() {
        let result = with_child(
            r#"<main><citry-child :citry-id="$citryPrepared.child" class="x"></citry-child></main>"#,
            json!({"child": "occ-Child"}),
            "<em>c</em>",
        );
        // The shell shows the child's own HTML until Vue builds the call.
        assert_eq!(
            html(&result),
            r#"<main data-allow-mismatch="children"><em>c</em></main>"#
        );
        assert_eq!(
            declines(&result),
            [("component-attrs", "class", Some("main"))]
        );
    }

    #[test]
    fn component_calls_with_v_show_are_shells() {
        // The server does not apply a caller's `v-show` to the child's root,
        // even for a value it knows, so Vue builds the call in the browser.
        let result = with_child(
            r#"<main><citry-child v-show="$citryPrepared.open" :citry-id="$citryPrepared.child"></citry-child></main>"#,
            json!({"child": "occ-Child", "open": false}),
            "<em>c</em>",
        );
        assert_eq!(
            html(&result),
            r#"<main data-allow-mismatch="children"></main>"#
        );
        assert_eq!(
            declines(&result),
            [("unsupported-directive", "render", Some("main"))]
        );
    }

    #[test]
    fn parser_repairs_make_the_parent_a_shell() {
        let result = with_child(
            r#"<main><p><span>a</span><citry-child :citry-id="$citryPrepared.child"></citry-child></p></main>"#,
            json!({"child": "occ-Child"}),
            "<div>b</div>",
        );
        assert_eq!(
            html(&result),
            r#"<main><p data-allow-mismatch="children"></p></main>"#
        );
        assert_eq!(declines(&result), [("parser-repair", "div", Some("p"))]);
        // The rules follow the HTML parser's tree construction.
        assert!(parser_moves(&["main", "p"], "div"));
        assert!(!parser_moves(&["p", "button"], "div"));
        assert!(parser_moves(&["h3"], "h4"));
        assert!(!parser_moves(&["button"], "h3"));
        assert!(parser_moves(&["a", "span"], "a"));
        assert!(parser_moves(&["form", "div"], "form"));
        assert!(parser_moves(&["ul", "li"], "li"));
        assert!(!parser_moves(&["ul", "li", "ul"], "li"));
        assert!(parser_moves(&["table"], "tr"));
        assert!(!parser_moves(&["table", "tbody"], "tr"));
        assert!(parser_moves(&["table", "tbody"], "div"));
        assert!(parser_moves(&["div"], "td"));
        assert!(!parser_moves(&["table", "tbody", "tr"], "th"));
        assert!(parser_moves(&["select"], "div"));
        assert!(!parser_moves(&["details"], "summary"));
    }

    #[test]
    fn attributes_follow_vues_property_and_attribute_paths() {
        let text = |value: &str| Val::Str(value.to_owned().into());
        assert_eq!(
            client_attribute("div", "data-x", &Val::Bool(true)),
            Ok(Some("true".to_owned()))
        );
        assert_eq!(
            client_attribute("form", "novalidate", &Val::Bool(true)),
            Ok(Some(String::new()))
        );
        assert_eq!(
            client_attribute("form", "novalidate", &Val::Bool(false)),
            Ok(None)
        );
        assert_eq!(
            client_attribute("input", "disabled", &text("false")),
            Ok(Some(String::new()))
        );
        assert_eq!(
            client_attribute("input", "disabled", &Val::Num(0.0)),
            Ok(None)
        );
        assert_eq!(client_attribute("a", "href", &Val::Null), Ok(None));
        assert_eq!(
            client_attribute("label", "for", &text("q")),
            Ok(Some("q".to_owned()))
        );
        assert_eq!(
            client_attribute("div", "id", &Val::Num(3.0)),
            Ok(Some("3".to_owned()))
        );
        assert!(client_attribute("div", "id", &Val::Num(0.5)).is_err());
        assert_eq!(
            client_attribute("div", "style", &text("color: red")),
            Ok(Some("color: red".to_owned()))
        );
        // A style object is written as Vue's server renderer writes it.
        assert_eq!(
            client_attribute("div", "style", &Val::Data(&json!({"color": "red"}))),
            Ok(Some("color:red;".to_owned()))
        );
        assert!(client_attribute("div", "style", &Val::Data(&json!({"color": 0.5}))).is_err());
        assert!(client_attribute("div", "tabIndex", &Val::Num(1.0)).is_err());
        assert!(client_attribute("textarea", "value", &text("x")).is_err());
        assert!(client_attribute("div", "unknownprop", &text("x")).is_err());
    }

    /// The anchors the server writes are the ones the compiler's hydration
    /// plan reports for the same render function. The plan lists every
    /// anchor a construct can create, so the data variants of each case
    /// together take every branch.
    #[test]
    fn written_anchors_match_the_compiler_hydration_plan() {
        let cases = [
            (LIST, vec![json!({"items": ["a"]})]),
            (
                r#"<div><template v-for="row in $citryPrepared.rows"><b>{{ row.a }}</b><i>x</i></template></div>"#,
                vec![json!({"rows": [{"a": "1"}]})],
            ),
            (
                r#"<div><p v-if="$citryPrepared.n === 0">zero</p></div>"#,
                vec![json!({"n": 0}), json!({"n": 1})],
            ),
            (
                r#"<div><template v-if="$citryPrepared.on"><b>a</b><i>b</i></template></div>"#,
                vec![json!({"on": true}), json!({"on": false})],
            ),
            ("<p>a</p><p>b</p>", vec![json!({})]),
        ];
        for (template, variants) in cases {
            let artifact = compile(CompileRequest {
                template: template.to_owned(),
                local_calls: Vec::new(),
                local_call_runs: Vec::new(),
                element_bindings: Vec::new(),
                dynamic_elements: Vec::new(),
            });
            let mut planned = HashMap::new();
            for anchor in &artifact.hydration_plan.anchors {
                let comments = match anchor.kind {
                    "fragment" => vec!["[", "]"],
                    _ => vec![anchor.comment.unwrap_or("")],
                };
                for comment in comments {
                    *planned.entry(comment.to_owned()).or_insert(0) += 1;
                }
            }
            // Each anchor's largest count over the variants.
            let mut written: HashMap<String, usize> = HashMap::new();
            for prepared in variants {
                let result = root(template, prepared);
                let mut counts: HashMap<String, usize> = HashMap::new();
                for piece in html(&result).split("<!--").skip(1) {
                    *counts
                        .entry(piece.split("-->").next().unwrap_or_default().to_owned())
                        .or_insert(0) += 1;
                }
                for (comment, count) in counts {
                    let entry = written.entry(comment).or_insert(0);
                    *entry = (*entry).max(count);
                }
            }
            assert_eq!(written, planned, "{template}");
        }
    }

    #[test]
    fn js_data_keys_the_browser_refuses_mount_the_page_in_the_browser() {
        // The browser throws for these keys, so the server must not write
        // HTML that reads them (for example `$citryPrepared` from `js_data`
        // instead of the occurrence's prepared data).
        for key in ["$citryPrepared", "$el", "_private"] {
            let result = render(
                &[(
                    "Root",
                    "<p>{{ $citryPrepared.t }}</p>",
                    json!({"t": "prepared"}),
                    json!({key: {"t": "js_data"}}),
                )],
                0,
            );
            assert_eq!(result.html, None, "{key}");
            assert_eq!(result.reason, Some("manifest"), "{key}");
        }
        // A child occurrence's key declines the whole page the same way.
        let nested = render(
            &[
                (
                    "Root",
                    r#"<main><citry-child :citry-id="$citryPrepared.child"></citry-child></main>"#,
                    json!({"child": "occ-Child"}),
                    json!({}),
                ),
                ("Child", "<p>x</p>", json!({}), json!({"$citryPrepared": 1})),
            ],
            0,
        );
        assert_eq!(nested.reason, Some("manifest"));
        // An ordinary `js_data` key still hydrates beside `$citryPrepared`.
        let result = render(
            &[(
                "Root",
                "<p>{{ $citryPrepared.t }}</p>",
                json!({"t": "prepared"}),
                json!({"citryPrepared": 1}),
            )],
            0,
        );
        assert_eq!(html(&result), "<p>prepared</p>");
    }

    #[test]
    fn small_pages_stay_below_the_threshold_and_skip_the_parse_check() {
        let result = render(
            &[("Root", LIST, json!({"items": ["a", "b"]}), json!({}))],
            3,
        );
        assert_eq!(result.html, None);
        assert_eq!(result.reason, Some("below-threshold"));
        assert_eq!(result.element_count, 3);
    }

    #[test]
    fn opaque_html_is_written_between_fragment_comments_for_vue_to_adopt() {
        let tag = r#"<main><citry-opaque-html :record="$citryPrepared.record"></citry-opaque-html></main>"#;
        let render = |record: Value| root(tag, json!({ "record": record }));
        // The block is written unchanged; Vue adopts `nodeCount` nodes.
        for (block, count) in [
            ("lead <b>x</b> tail", 3),
            ("<b>x</b><!-- note --><i>y</i>", 3),
            ("   ", 1),
            ("a &amp; b &lt;c&gt;", 1),
            (r#"<span><em>a<b>b</b></em></span>"#, 1),
        ] {
            let result = render(json!({"html": block, "nodeCount": count}));
            assert_eq!(
                html(&result),
                format!("<main><!--[-->{block}<!--]--></main>")
            );
            assert_eq!(declines(&result), []);
        }
        // A pinned record is written the same way.
        let pinned = render(json!({"html": "<b>x</b>", "nodeCount": 1, "pinned": true}));
        assert_eq!(html(&pinned), "<main><!--[--><b>x</b><!--]--></main>");
        assert_eq!(declines(&pinned), []);
        let empty = render(json!({"html": "", "nodeCount": 0}));
        assert_eq!(html(&empty), "<main><!--[--><!--]--></main>");
        // Elements inside the block count toward the page size.
        let counted = render(json!({"html": "<b>x</b><i>y</i>", "nodeCount": 2}));
        assert_eq!(counted.element_count, 3);
        // A record whose count differs from the browser's parse, a record
        // of another shape, a first comment Vue cannot start at, and a
        // script the served page would run are left to the browser. The
        // shell then shows the block, unless it holds the script.
        for (record, shown) in [
            (json!({"html": "<b>x</b>", "nodeCount": 2}), "<b>x</b>"),
            (json!({"html": "<b>x</b>"}), "<b>x</b>"),
            (
                json!({"html": "<b>x</b>", "nodeCount": 1, "extra": true}),
                "<b>x</b>",
            ),
            (
                json!({"html": "<b>x</b>", "nodeCount": 1, "pinned": false}),
                "<b>x</b>",
            ),
            (
                json!({"html": "<!-- c --><b>x</b>", "nodeCount": 2}),
                "<!-- c --><b>x</b>",
            ),
            (
                json!({"html": "<b>x</b><script>f()</script>", "nodeCount": 2}),
                "",
            ),
        ] {
            let result = render(record);
            assert_eq!(
                html(&result),
                format!(r#"<main data-allow-mismatch="children">{shown}</main>"#)
            );
            assert_eq!(
                declines(&result),
                [("opaque-html", "citry-opaque-html", Some("main"))]
            );
        }
        // A block the page's parser would repair: a paragraph inside a
        // paragraph. The shell stays empty, because its contents would be
        // repaired the same way.
        let nested = root(
            r#"<main><p><citry-opaque-html :record="$citryPrepared.record"></citry-opaque-html></p></main>"#,
            json!({"record": {"html": "<p>inner</p>", "nodeCount": 1}}),
        );
        assert_eq!(
            html(&nested),
            r#"<main><p data-allow-mismatch="children"></p></main>"#
        );
    }

    #[test]
    fn shell_contents_past_the_size_limit_are_left_out() {
        let big = "x".repeat(super::MAX_SHELL_CONTENT + 1);
        let result = root(
            "<main><b v-if=\"open\">a</b><span>{{ $citryPrepared.big }}</span></main>",
            json!({ "big": big }),
        );
        assert_eq!(
            html(&result),
            r#"<main data-allow-mismatch="children"></main>"#
        );
        let small = root(
            "<main><b v-if=\"open\">a</b><span>{{ $citryPrepared.big }}</span></main>",
            json!({ "big": "y" }),
        );
        assert_eq!(
            html(&small),
            r#"<main data-allow-mismatch="children"><b>a</b><span>y</span></main>"#
        );
    }

    #[test]
    fn component_text_roots_are_left_to_the_browser() {
        // Vue steps over one DOM node per component, so a text root merged
        // with its neighbour, or an empty one, would shift later siblings.
        let merged = with_child(
            r#"<div>a<citry-child :citry-id="$citryPrepared.child"></citry-child></div>"#,
            json!({"child": "occ-Child"}),
            "{{ 'hello' }}",
        );
        assert_eq!(
            html(&merged),
            r#"<div data-allow-mismatch="children">ahello</div>"#
        );
        assert_eq!(
            declines(&merged),
            [("component-text-root", "text", Some("div"))]
        );
        let empty = with_child(
            r#"<div><citry-child :citry-id="$citryPrepared.child"></citry-child><b>z</b></div>"#,
            json!({"child": "occ-Child"}),
            "{{ '' }}",
        );
        assert_eq!(
            html(&empty),
            r#"<div data-allow-mismatch="children"><b>z</b></div>"#
        );
    }

    #[test]
    fn classes_and_styles_follow_create_vnode_and_merge_props() {
        let spread =
            |value: Value| root(r#"<p v-bind="$citryPrepared.o">x</p>"#, json!({"o": value}));
        // Outside `mergeProps`, a falsy class is printed as it is.
        assert_eq!(
            html(&spread(json!({"class": false}))),
            r#"<p class="false">x</p>"#
        );
        assert_eq!(html(&spread(json!({"class": 0}))), r#"<p class="0">x</p>"#);
        // `mergeProps` joins every class that is not the same string.
        let merged = |value: Value| {
            root(
                r#"<p class="a" v-bind="$citryPrepared.o">x</p>"#,
                json!({"o": value}),
            )
        };
        assert_eq!(
            html(&merged(json!({"class": ["a"]}))),
            r#"<p class="a a">x</p>"#
        );
        assert_eq!(
            html(&merged(json!({"class": "a"}))),
            r#"<p class="a">x</p>"#
        );
        let bound = root(
            r#"<p :class="$citryPrepared.c" :style="$citryPrepared.s">x</p>"#,
            json!({"c": {"on": true, "off": false}, "s": "color: red"}),
        );
        assert_eq!(html(&bound), r#"<p class="on" style="color: red">x</p>"#);
        // Two styles meeting in `mergeProps` combine into one object, which
        // is written as Vue's server renderer writes it.
        let styles = root(
            r#"<main><p v-bind="$citryPrepared.o" style="color: red">x</p></main>"#,
            json!({"o": {"style": "font-weight: bold"}}),
        );
        assert_eq!(
            html(&styles),
            r#"<main><p style="font-weight:bold;color:red;">x</p></main>"#
        );
        assert!(declines(&styles).is_empty());
    }

    #[test]
    fn a_static_class_or_style_merges_with_its_binding() {
        // Vue compiles `class` beside `:class` into one array and `style`
        // beside `:style` into an array of objects; both are written the
        // way Vue's first render leaves them.
        let merged = root(
            concat!(
                r#"<p class="card" :class="{ open: $citryPrepared.on, shut: $citryPrepared.off }""#,
                r#" style="color: red" :style="{ fontWeight: $citryPrepared.w, '--gap': 2 }">x</p>"#,
            ),
            json!({"on": true, "off": false, "w": "bold"}),
        );
        assert_eq!(
            html(&merged),
            r#"<p class="card open" style="color:red;font-weight:bold;--gap:2;">x</p>"#
        );
        // Arrays nest, strings are trimmed, and a falsy item adds nothing.
        let nested = root(
            r#"<p :class="['  a ', [$citryPrepared.b, { c: 1 }], 0, null, '']">x</p>"#,
            json!({"b": "b"}),
        );
        assert_eq!(html(&nested), r#"<p class="a b c">x</p>"#);
        // A `:style` array reads its strings as declarations, a later value
        // replacing an earlier one in place.
        let styles = root(
            r#"<p :style="['color: red; margin: 0 /* x */', { color: 'blue', marginTop: 1 }]">x</p>"#,
            json!({}),
        );
        assert_eq!(
            html(&styles),
            r#"<p style="color:blue;margin:0;margin-top:1;">x</p>"#
        );
    }

    #[test]
    fn object_class_keys_follow_the_browser_order() {
        // JavaScript lists array-index keys first, in numeric order, then
        // the others in the order they were written, or for the page's
        // JSON, in its sorted order.
        let literal = root(
            r#"<p :class="{ z: 1, 10: 1, a: 1, 2: 1, z: 0, b: 1 }">x</p>"#,
            json!({}),
        );
        assert_eq!(html(&literal), r#"<p class="2 10 a b">x</p>"#);
        let data = root(
            r#"<p :class="$citryPrepared.c">x</p>"#,
            json!({"c": {"z": true, "10": true, "a": true, "2": true, "01": true}}),
        );
        assert_eq!(html(&data), r#"<p class="2 10 01 a z">x</p>"#);
    }

    #[test]
    fn a_browser_only_class_or_style_part_leaves_the_known_parts_in_the_shell() {
        // `open` is component state only the browser has, so Vue builds the
        // element; until then the shell shows the classes and styles the
        // server knows, so the element is styled before Vue runs.
        let partial = root(
            concat!(
                r#"<main><p class="card" :class="{ open: open, done: $citryPrepared.done }""#,
                r#" style="color: red" :style="{ width: size }">x</p></main>"#,
            ),
            json!({"done": true}),
        );
        assert_eq!(
            html(&partial),
            r#"<main data-allow-mismatch="children"><p class="card done" style="color:red;">x</p></main>"#
        );
        assert_eq!(
            declines(&partial),
            [("browser-value", "class", Some("main"))]
        );
    }

    #[test]
    fn style_values_the_browser_could_read_differently_are_left_to_it() {
        // A fraction would need JavaScript's number printing, an empty
        // value is removed by the client but written by the server
        // renderer, and a semicolon would split the declaration.
        for style in [
            "{ width: 1.5 }",
            "{ color: '' }",
            "{ color: 'red;' }",
            "{ color: true }",
            "{ color: ['red'] }",
            "{ WebkitTransition: 'none' }",
        ] {
            let page = root(
                &format!(r#"<main><p :style="{style}">x</p></main>"#),
                json!({}),
            );
            assert_eq!(
                declines(&page),
                [("unsupported-attribute", "style", Some("main"))],
                "{style}"
            );
        }
        // Null and undefined values are skipped by both renderers.
        let skipped = root(r#"<p :style="{ color: null, margin: 0 }">x</p>"#, json!({}));
        assert_eq!(html(&skipped), r#"<p style="margin:0;">x</p>"#);
    }

    #[test]
    fn values_hydration_does_not_reapply_or_the_parser_moves_are_shells() {
        // `output.value` replaces the element's text and is not re-applied.
        let output = root(r#"<form><output value="hi">z</output></form>"#, json!({}));
        assert_eq!(
            html(&output),
            r#"<form data-allow-mismatch="children"><output value="hi">z</output></form>"#
        );
        let table = root(
            r#"<table><tbody><tr>{{ $citryPrepared.t }}</tr></tbody></table>"#,
            json!({"t": "moved"}),
        );
        assert_eq!(
            html(&table),
            r#"<table><tbody><tr data-allow-mismatch="children"></tr></tbody></table>"#
        );
        assert_eq!(declines(&table), [("parser-repair", "text", Some("tr"))]);
        // Inherited object names and non-canonical indexes read differently
        // in JavaScript, so they are left to the browser.
        let inherited = root(
            "<p>{{ $citryPrepared.o.constructor }}</p>",
            json!({"o": {}}),
        );
        assert_eq!(
            html(&inherited),
            r#"<p data-allow-mismatch="children"></p>"#
        );
    }

    #[test]
    fn deep_render_code_is_left_unread_instead_of_overflowing_the_stack() {
        let template = format!("<p>{}</p>", "{{ $citryPrepared.t }}".repeat(2_000));
        let result = root(&template, json!({"t": "x"}));
        assert_eq!(html(&result), r#"<p data-allow-mismatch="children"></p>"#);
        assert_eq!(declines(&result), [("nesting-depth", "text", Some("p"))]);
    }

    /// Render one root template whose dynamic element aliases map to real
    /// tags, running both parse checks like `render` does.
    fn root_with_aliases(template: &str, aliases: &[(&str, &str)]) -> HydrationRender {
        let artifact = compile(CompileRequest {
            template: template.to_owned(),
            local_calls: Vec::new(),
            local_call_runs: Vec::new(),
            element_bindings: Vec::new(),
            dynamic_elements: aliases
                .iter()
                .map(|(alias, tag)| crate::DynamicElement {
                    alias: (*alias).to_owned(),
                    tag: (*tag).to_owned(),
                    source_start: 0,
                    source_end: u32::try_from(template.len()).expect("short template"),
                })
                .collect(),
        });
        let aliases = aliases
            .iter()
            .map(|(alias, tag)| ((*alias).to_owned(), (*tag).to_owned()))
            .collect::<Vec<_>>();
        let program = read_program(&artifact.code, &aliases).expect("render function reads");
        let programs = HashMap::from([("def-Root".to_owned(), &program)]);
        let manifest = json!({
            "rootId": "occ-Root",
            "occurrences": [{"id": "occ-Root", "typeKey": "Root", "definitionId": "def-Root"}],
        })
        .to_string();
        let tags = HashMap::from([("Root".to_owned(), "citry-root".to_owned())]);
        let request = |full_parse_check| RenderRequest {
            programs: &programs,
            manifest_json: &manifest,
            tags: &tags,
            threshold: 0,
            full_parse_check,
        };
        let result = render_for_hydration(&request(false));
        let full = render_for_hydration(&request(true));
        assert_eq!(result.html, full.html);
        assert_eq!(result.reason, full.reason);
        assert_eq!(result.declines, full.declines);
        result
    }

    #[test]
    fn a_void_element_with_children_makes_its_parent_the_shell() {
        // An alias can stand for a void tag while the template gives it
        // children. Writing it as a shell would need `</br>`, which the
        // parser reads as a second `<br>`.
        let result = root_with_aliases(
            "<div><p>kept</p><citry-dynamic-a1>x</citry-dynamic-a1></div>",
            &[("citry-dynamic-a1", "br")],
        );
        // The shell's contents write the void element without children.
        assert_eq!(
            html(&result),
            r#"<div data-allow-mismatch="children"><p>kept</p><br></div>"#
        );
        assert_eq!(
            declines(&result),
            vec![("unsupported-tag", "br", Some("div"))]
        );
    }

    #[test]
    fn text_the_full_parse_reports_is_left_to_it() {
        // Control characters and noncharacters are kept by the browser but
        // reported by the full parse's tokenizer, so the page is decided by
        // the full parse (the shared helper compares both checks).
        for text in ["a\u{1}b", "a\u{7f}b", "a\u{fffe}b"] {
            let result = root("<p>{{ $citryPrepared.t }}</p>", json!({"t": text}));
            assert_eq!(result.reason, Some("browser-structure"), "{text:?}");
            let result = root(r#"<p :title="$citryPrepared.t">x</p>"#, json!({"t": text}));
            assert_eq!(result.reason, Some("browser-structure"), "{text:?}");
        }
    }
    #[test]
    fn v_text_with_a_value_the_server_knows_is_written_as_the_element_text() {
        // Hydration does not compare an element's text when the vnode has no
        // children, and it sets `textContent` itself, so the text Vue will
        // set is written for the first paint.
        let known = root(
            r#"<div><p v-text="$citryPrepared.msg"></p><b v-text="'Hi ' + $citryPrepared.name"></b></div>"#,
            json!({"msg": "a <b> & c", "name": "Ann"}),
        );
        assert_eq!(
            html(&known),
            "<div><p>a &lt;b&gt; &amp; c</p><b>Hi Ann</b></div>"
        );
        assert!(known.declines.is_empty());
        let server_data = render(
            &[(
                "Root",
                r#"<div><output v-text="count"></output></div>"#,
                json!({}),
                json!({"count": 3}),
            )],
            0,
        );
        assert_eq!(html(&server_data), "<div><output>3</output></div>");
        // Values print as Vue's `toDisplayString` does; null and undefined
        // print nothing.
        let values = root(
            r#"<div><p v-text="$citryPrepared.n"></p><p v-text="$citryPrepared.t"></p><p v-text="$citryPrepared.none"></p><p v-text="$citryPrepared.missing"></p></div>"#,
            json!({"n": 42, "t": false, "none": null}),
        );
        assert_eq!(
            html(&values),
            "<div><p>42</p><p>false</p><p></p><p></p></div>"
        );
    }

    #[test]
    fn v_text_the_server_cannot_print_exactly_is_left_for_hydration_to_set() {
        // Browser-only values, fractions (JavaScript's number printing),
        // objects and arrays (Vue's JSON formatting), and text the parser
        // would change stay empty without a shell: hydration sets the text.
        let result = root(
            r#"<div><p v-text="open"></p><p v-text="$citryPrepared.f"></p><p v-text="$citryPrepared.o"></p><p v-text="$citryPrepared.a"></p><p v-text="$citryPrepared.cr"></p><pre v-text="$citryPrepared.nl"></pre></div>"#,
            json!({"f": 1.5, "o": {"x": 1}, "a": [1], "cr": "a\rb", "nl": "\nx"}),
        );
        assert_eq!(
            html(&result),
            "<div><p></p><p></p><p></p><p></p><p></p><pre></pre></div>"
        );
        assert!(result.declines.is_empty());
        let table = root(
            r#"<table><tr v-text="$citryPrepared.msg"></tr></table>"#,
            json!({"msg": "x"}),
        );
        assert_eq!(html(&table), "<table><tbody><tr></tr></tbody></table>");
        assert!(table.declines.is_empty());
    }

    #[test]
    fn v_text_with_authored_children_keeps_writing_the_children() {
        // Hydration compares the DOM text with the authored children before
        // it sets `textContent`, so the children stay the server's text.
        for template in [
            r#"<div><p v-text="$citryPrepared.msg">fallback</p></div>"#,
            r#"<div><p v-text="open">fallback</p></div>"#,
        ] {
            let result = root(template, json!({"msg": "real"}));
            assert_eq!(html(&result), "<div><p>fallback</p></div>");
            assert!(result.declines.is_empty());
        }
        // Element children are skipped by hydration when the text is not
        // empty, and are still written for the first paint.
        let elements = root(
            r#"<div><p v-text="$citryPrepared.msg"><b>fallback</b></p></div>"#,
            json!({"msg": "real"}),
        );
        assert_eq!(html(&elements), "<div><p><b>fallback</b></p></div>");
        assert!(elements.declines.is_empty());
    }

    #[test]
    fn v_text_follows_conditions_lists_and_v_show() {
        let result = root(
            r#"<div><p v-if="$citryPrepared.on" v-text="$citryPrepared.msg"></p><ul><li v-for="item in $citryPrepared.items" v-text="item"></li></ul><b v-show="$citryPrepared.on" v-text="$citryPrepared.msg"></b></div>"#,
            json!({"on": false, "msg": "m", "items": ["x", "y"]}),
        );
        assert_eq!(
            html(&result),
            r#"<div><!--v-if--><ul><!--[--><li>x</li><li>y</li><!--]--></ul><b style="display: none;">m</b></div>"#
        );
        // A loop over browser-only values leaves the list to the browser.
        let browser_list = root(
            r#"<ul><li v-for="item in items" v-text="item"></li></ul>"#,
            json!({}),
        );
        assert_eq!(
            declines(&browser_list),
            [("browser-value", "v-for", Some("ul"))]
        );
    }

    #[test]
    fn v_text_from_a_spread_is_written_because_hydration_keeps_it() {
        // A `textContent` key from `v-bind` is not a dynamic prop, so
        // hydration leaves the server's text in place: it must be exact.
        let result = root(
            r#"<div><p v-bind="$citryPrepared.attrs"></p></div>"#,
            json!({"attrs": {"textContent": "spread", "id": "i"}}),
        );
        assert_eq!(html(&result), r#"<div><p id="i">spread</p></div>"#);
        // Text the parser would change cannot be written exactly, so the
        // parent becomes the shell and Vue builds the element.
        for (template, value) in [
            (
                r#"<div><p v-bind="$citryPrepared.attrs"></p></div>"#,
                "a\r\nb",
            ),
            (
                r#"<div><pre v-bind="$citryPrepared.attrs"></pre></div>"#,
                "\nx",
            ),
        ] {
            let result = root(template, json!({"attrs": {"textContent": value}}));
            assert_eq!(
                declines(&result),
                [("text-value", "textContent", Some("div"))]
            );
        }
    }

    #[test]
    fn shell_contents_show_v_text_the_server_knows() {
        let result = root(
            r#"<main><span>{{ open }}<b v-text="$citryPrepared.msg"></b></span></main>"#,
            json!({"msg": "shown"}),
        );
        // The shell's contents are only shown until Vue builds them.
        assert_eq!(
            html(&result),
            r#"<main><span data-allow-mismatch="children"><b>shown</b></span></main>"#
        );
    }
}
