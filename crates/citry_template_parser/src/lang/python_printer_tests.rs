//! Tests for the Python printer's bracket budget.
//!
//! A template whose generated `body = [...]` statement would nest more
//! brackets than the budget gets some subtrees moved into `_nN` local
//! variables. These tests lock that moved-out form on small templates with
//! small budgets, and check its rules on generated deep trees: every
//! statement stays within the budget, putting the moved subtrees back gives
//! the single-statement output, Python runs the constructors in the same
//! order, and a template within the budget prints exactly as it would with
//! no budget at all.

use crate::compiler::{compile_template_body_with_mode, CompileMode};
use crate::lang::lang::LangSpecArgument;
use crate::lang::python::{compile_with_bracket_budget, format_leaf};
use crate::parser::parse_template;

/// Parse and compile `source`, printing with the given bracket budget.
fn compile_at(source: &str, budget: usize, mode: CompileMode) -> String {
    let template = parse_template(source, None, None)
        .unwrap_or_else(|error| panic!("parse failed for {source:?}: {error:?}"));
    let args = compile_template_body_with_mode(template, mode)
        .unwrap_or_else(|error| panic!("compile failed for {source:?}: {error:?}"));
    compile_with_bracket_budget(args, budget)
        .unwrap_or_else(|error| panic!("print failed for {source:?}: {error}"))
}

fn compile_html_at(source: &str, budget: usize) -> String {
    compile_at(source, budget, CompileMode::Html)
}

// =============================================================================
// SCANNING GENERATED CODE
// =============================================================================

/// One statement of a generated function: the assigned name, the expression
/// text, and the most brackets the expression holds open at once.
#[derive(Debug)]
struct Statement {
    name: String,
    expression: String,
    most_open_brackets: usize,
}

/// Split generated code into its assignment statements.
///
/// The scanner skips string literals, so a bracket inside template text
/// does not count. A statement ends at a newline outside any string and
/// outside any bracket.
fn statements(code: &str) -> Vec<Statement> {
    let body = code
        .strip_prefix("def generate_template():\n")
        .and_then(|rest| rest.strip_suffix("    return body\n"))
        .unwrap_or_else(|| panic!("unexpected function shape:\n{code}"));
    let bytes = body.as_bytes();
    let mut found = Vec::new();
    let mut start = 0;
    let mut open = 0usize;
    let mut most_open = 0usize;
    let mut index = 0;
    while index < bytes.len() {
        match bytes[index] {
            b'"' => {
                // The printer writes text as `"""..."""` and names as
                // `"..."`, and escapes every quote inside both.
                let triple = bytes[index..].starts_with(b"\"\"\"");
                let quote: &[u8] = if triple { b"\"\"\"" } else { b"\"" };
                index += quote.len();
                while !bytes[index..].starts_with(quote) {
                    index += if bytes[index] == b'\\' { 2 } else { 1 };
                }
                index += quote.len();
                continue;
            }
            b'(' | b'[' | b'{' => {
                open += 1;
                most_open = most_open.max(open);
            }
            b')' | b']' | b'}' => open -= 1,
            b'\n' if open == 0 => {
                let line = &body[start..index];
                let (name, expression) = line
                    .trim_start()
                    .split_once(" = ")
                    .unwrap_or_else(|| panic!("not an assignment: {line}"));
                found.push(Statement {
                    name: name.to_string(),
                    expression: expression.to_string(),
                    most_open_brackets: most_open,
                });
                start = index + 1;
                most_open = 0;
            }
            _ => {}
        }
        index += 1;
    }
    found
}

/// What generated code builds, read back from its text.
struct Expanded {
    /// The `body` expression with every moved-out subtree put back where
    /// its name stands.
    body: String,
    /// Each constructor call, in the order Python runs them, given as the
    /// offset in `body` where the call starts. The offset identifies the
    /// call no matter which statement it was written in.
    call_order: Vec<usize>,
}

/// One statement after its local names are replaced by their text.
struct ExpandedStatement {
    name: String,
    text: String,
    /// Offsets in `text` of the calls this statement itself runs, in the
    /// order Python runs them: a call runs when its closing `)` is reached.
    own_calls: Vec<usize>,
    /// Each local used here, and the offset in `text` where its text went.
    locals_used: Vec<(String, usize)>,
}

/// Read generated code back into the single expression it stands for, and
/// the order in which it runs the constructors.
///
/// Each local is used exactly once, after it is assigned, and this panics
/// otherwise. Python runs statements top to bottom, and inside one
/// statement it runs a call once all its arguments are built. A local's
/// name is only a lookup, so the calls inside a moved-out subtree run when
/// its own statement runs.
fn expand(code: &str) -> Expanded {
    let mut done: Vec<ExpandedStatement> = Vec::new();
    for statement in statements(code) {
        done.push(expand_statement(&statement, &done));
    }
    let body_index = done
        .iter()
        .position(|statement| statement.name == "body")
        .expect("no body statement");
    assert_eq!(
        body_index,
        done.len() - 1,
        "body must be the last statement"
    );

    // Find where each statement's text sits in the body. A statement's text
    // goes into the one later statement that uses it, so walking backwards
    // finds every user before the statements it uses.
    let mut bases: Vec<Option<usize>> = vec![None; done.len()];
    bases[body_index] = Some(0);
    for index in (0..done.len()).rev() {
        let base = bases[index].unwrap_or_else(|| panic!("{} is never used", done[index].name));
        for (name, offset) in &done[index].locals_used {
            let used = done
                .iter()
                .position(|statement| &statement.name == name)
                .unwrap();
            assert!(bases[used].is_none(), "{name} is used twice");
            bases[used] = Some(base + offset);
        }
    }
    let call_order = done
        .iter()
        .zip(&bases)
        .flat_map(|(statement, base)| {
            let base = base.unwrap();
            statement.own_calls.iter().map(move |offset| base + offset)
        })
        .collect();
    Expanded {
        body: done.pop().unwrap().text,
        call_order,
    }
}

/// Replace each `_nN` name outside string literals with that local's text,
/// and list the calls the statement runs itself.
fn expand_statement(statement: &Statement, done: &[ExpandedStatement]) -> ExpandedStatement {
    let expression = &statement.expression;
    let bytes = expression.as_bytes();
    let mut text = String::with_capacity(expression.len());
    let mut own_calls = Vec::new();
    let mut locals_used = Vec::new();
    // For each open bracket: where its call starts in `text`, if it is a call.
    let mut open: Vec<Option<usize>> = Vec::new();
    let mut index = 0;
    while index < bytes.len() {
        let byte = bytes[index];
        if byte == b'"' {
            let triple = bytes[index..].starts_with(b"\"\"\"");
            let quote: &[u8] = if triple { b"\"\"\"" } else { b"\"" };
            let start = index;
            index += quote.len();
            while !bytes[index..].starts_with(quote) {
                index += if bytes[index] == b'\\' { 2 } else { 1 };
            }
            index += quote.len();
            text.push_str(&expression[start..index]);
            continue;
        }
        let starts_word = index == 0 || !is_name_byte(bytes[index - 1]);
        if starts_word && is_name_byte(byte) {
            let length = bytes[index..]
                .iter()
                .take_while(|&&b| is_name_byte(b))
                .count();
            let word = &expression[index..index + length];
            if word.starts_with("_n") {
                // A local name: its text goes here, and its calls already
                // ran in its own statement.
                let local = done
                    .iter()
                    .find(|statement| statement.name == word)
                    .unwrap_or_else(|| panic!("{word} is used before it is assigned"));
                locals_used.push((word.to_string(), text.len()));
                text.push_str(&local.text);
            } else if bytes.get(index + length) == Some(&b'(') {
                // A constructor call starts at its class name.
                open.push(Some(text.len()));
                text.push_str(word);
                text.push('(');
                index += length + 1;
                continue;
            } else {
                text.push_str(word);
            }
            index += length;
            continue;
        }
        match byte {
            b'(' | b'[' | b'{' => open.push(None),
            b')' | b']' | b'}' => {
                if let Some(call_start) = open.pop().unwrap() {
                    own_calls.push(call_start);
                }
            }
            _ => {}
        }
        let character = expression[index..].chars().next().unwrap();
        text.push(character);
        index += character.len_utf8();
    }
    ExpandedStatement {
        name: statement.name.clone(),
        text,
        own_calls,
        locals_used,
    }
}

fn is_name_byte(byte: u8) -> bool {
    byte.is_ascii_alphanumeric() || byte == b'_'
}

/// Print `args` the way the printer did before it had a budget: one
/// expression, every child inline.
///
/// This is the reference the moved-out form is checked against. It
/// recurses, which is fine for the depths these tests build.
fn reference_expression(arg: &LangSpecArgument) -> String {
    let join = |items: &[LangSpecArgument]| {
        items
            .iter()
            .map(reference_expression)
            .collect::<Vec<_>>()
            .join(", ")
    };
    match arg {
        LangSpecArgument::Tuple(items) if items.is_empty() => "()".to_string(),
        LangSpecArgument::List(items) if items.is_empty() => "[]".to_string(),
        LangSpecArgument::Tuple(items) => format!("({},)", join(items)),
        LangSpecArgument::List(items) => format!("[{},]", join(items)),
        LangSpecArgument::Struct(call) => format!("{}({})", call.name, join(&call.arguments)),
        leaf => format_leaf(leaf),
    }
}

/// The whole function as the reference printer writes it.
fn reference_code(args: &[LangSpecArgument]) -> String {
    let body = reference_expression(&LangSpecArgument::List(args.to_vec()));
    format!("def generate_template():\n    body = {body}\n    return body\n")
}

// =============================================================================
// BUILDING DEEP TREES WITHOUT PARSING
// =============================================================================

/// Nest a shape `depth` times by compiling `shape` once and putting the
/// level below where the text `HOLE` is.
///
/// This builds deep trees without parsing a deep template, so the test
/// checks the printer on its own. The innermost level holds the text
/// `deep`.
fn nested_args(shape: &str, depth: usize) -> Vec<LangSpecArgument> {
    let template = parse_template(shape, None, None).expect("shape parses");
    let shape_args =
        compile_template_body_with_mode(template, CompileMode::Html).expect("shape compiles");
    let mut level = vec![LangSpecArgument::UnsafeString("deep".to_string())];
    for _ in 0..depth {
        let mut next = shape_args.clone();
        let filled = fill_hole(&mut next, &mut level);
        assert!(filled, "shape {shape:?} has no HOLE text");
        level = next;
    }
    level
}

/// Find the list item whose text holds `HOLE` and splice `items` in its
/// place, keeping the text on either side. Returns whether it found one.
///
/// The shape is small, so recursing here is safe.
fn fill_hole(list: &mut Vec<LangSpecArgument>, items: &mut Vec<LangSpecArgument>) -> bool {
    for position in 0..list.len() {
        if let LangSpecArgument::UnsafeString(text) = &list[position] {
            if let Some((before, after)) = text.split_once("HOLE") {
                let (before, after) = (before.to_string(), after.to_string());
                let mut replacement = Vec::new();
                if !before.is_empty() {
                    replacement.push(LangSpecArgument::UnsafeString(before));
                }
                replacement.append(items);
                if !after.is_empty() {
                    replacement.push(LangSpecArgument::UnsafeString(after));
                }
                list.splice(position..=position, replacement);
                return true;
            }
        }
        let children = match &mut list[position] {
            LangSpecArgument::List(children) | LangSpecArgument::Tuple(children) => children,
            LangSpecArgument::Struct(struct_arg) => &mut struct_arg.arguments,
            _ => continue,
        };
        if fill_hole(children, items) {
            return true;
        }
    }
    false
}

/// The nested shapes the invariant tests build, one per kind of node that
/// adds brackets, plus the order cases: constructors before and after the
/// deep part, at the same level and one level up.
const SHAPES: &[&str] = &[
    r#"<c-if cond="a">HOLE</c-if><c-else>no</c-else>"#,
    r#"<c-for each="i in xs">HOLE</c-for><c-empty>none</c-empty>"#,
    r#"<c-Card><c-fill name="body"><c-slot name="inner">HOLE</c-slot></c-fill></c-Card>"#,
    r#"<c-if cond="x"><div c-class="cls" #c-key="k">HOLE</div></c-if>"#,
    r#"{{ a }}<c-if cond="x">HOLE</c-if>"#,
    r#"{{ a }}<c-if cond="x">{{ b }}<c-Card/>HOLE{{ c }}</c-if><c-else>{{ d }}</c-else>{{ e }}"#,
];

// =============================================================================
// INVARIANTS
// =============================================================================

/// Run `check` on a thread with a large stack.
///
/// The printer itself never recurses, but this file's reference printer and
/// the derived `Clone` and `Drop` of a deep tree do, once per bracket.
fn on_large_stack(check: impl FnOnce() + Send + 'static) {
    std::thread::Builder::new()
        .stack_size(256 * 1024 * 1024)
        .spawn(check)
        .unwrap()
        .join()
        .unwrap();
}

#[test]
fn every_statement_stays_within_the_budget_and_keeps_order() {
    on_large_stack(check_every_shape_and_depth);
}

fn check_every_shape_and_depth() {
    for shape in SHAPES {
        // Every depth up to 80 puts the moved subtrees at each part of the
        // shape, at both budgets, and reaches three moves along the deep
        // path at the real budget. Larger depths are sampled up to 600 to keep the
        // debug-build run short.
        for depth in (1..=80).chain((120..=600).step_by(60)) {
            let args = nested_args(shape, depth);
            let unlimited = reference_code(&args);
            let reference = expand(&unlimited);
            for budget in [100, 7] {
                let code = compile_with_bracket_budget(args.clone(), budget).unwrap();
                for statement in statements(&code) {
                    assert!(
                        statement.most_open_brackets <= budget,
                        "shape {shape:?} depth {depth} budget {budget}: {} opens {} brackets",
                        statement.name,
                        statement.most_open_brackets,
                    );
                }
                // Moving subtrees out must not change what the code
                // builds: putting them back gives the unlimited output.
                let expanded = expand(&code);
                assert_eq!(
                    expanded.body, reference.body,
                    "shape {shape:?} depth {depth} budget {budget}",
                );
                // Nor the order Python builds it in, because some
                // constructors raise.
                assert_eq!(
                    expanded.call_order, reference.call_order,
                    "call order, shape {shape:?} depth {depth} budget {budget}",
                );
                // A template that fits the budget keeps the one-statement
                // form, byte for byte.
                if statements(&unlimited)[0].most_open_brackets <= budget {
                    assert_eq!(code, unlimited, "shape {shape:?} depth {depth}");
                }
            }
        }
    }
}

#[test]
fn moved_out_code_is_the_same_on_every_run() {
    let source = r#"<c-if cond="x">"#.repeat(60) + "deep" + &"</c-if>".repeat(60);
    let first = compile_html_at(&source, 100);
    for _ in 0..5 {
        assert_eq!(compile_html_at(&source, 100), first);
    }
}

// =============================================================================
// THE MOVED-OUT FORM, LOCKED
// =============================================================================
//
// Each expected string was produced by the printer and checked by hand.
// Small budgets show the moved-out form on templates that are easy to read.

#[test]
fn nested_if_with_else_moves_the_deep_branch() {
    // The outer `<c-if>` branch reaches the budget, so it moves out whole. Its
    // `<c-else>` sibling comes after it, so Python builds it later either way
    // and it stays.
    let code = compile_at(
        r#"<c-if cond="a"><c-if cond="b">B</c-if><c-else>notb</c-else></c-if><c-else>nota</c-else>"#,
        8,
        CompileMode::Html,
    );
    assert_eq!(
        code,
        r##"def generate_template():
    _n1 = ((0, 66,), (ExprHtmlAttr(source, (6, 14,), """cond""", """a""", ("a",)),), [IfNode(source, (((15, 38,), (ExprHtmlAttr(source, (21, 29,), """cond""", """b""", ("b",)),), ["""B""",], (),), ((38, 59,), (), ["""notb""",], (),),), ("b",)),], (),)
    body = [IfNode(source, (_n1, ((66, 87,), (), ["""nota""",], (),),), ("b", "a",)),]
    return body
"##
    );
}

#[test]
fn nested_for_with_empty_moves_the_deep_branch() {
    // The `<c-empty>` branch sits inside the moved branch, so it moves with it.
    let code = compile_at(
        r#"<c-for each="i in xs"><c-for each="j in i">{{ j }}</c-for><c-empty>none</c-empty></c-for>"#,
        8,
        CompileMode::Html,
    );
    assert_eq!(
        code,
        r##"def generate_template():
    _n1 = ((0, 89,), (ExprHtmlAttr(source, (7, 21,), """each""", """i in xs""", ("xs",)),), [ForNode(source, (((22, 58,), (ExprHtmlAttr(source, (29, 42,), """each""", """j in i""", ("i",)),), [ExprNode(source, (43, 50,), """j """, ("j",)),], ("j",),), ((58, 81,), (), ["""none""",], (),),), ("i",)),], ("i",),)
    body = [ForNode(source, (_n1,), ("xs",)),]
    return body
"##
    );
}

#[test]
fn fill_holding_a_slot_moves_the_earlier_attributes_too() {
    // The slot reaches the budget and moves, and so does the fill around it.
    // The fill's attribute tuple sits left of the slot and builds a
    // `StaticHtmlAttr`, so it moves too, ahead of the slot.
    let code = compile_at(
        r#"<c-Card><c-fill name="body"><c-slot name="inner">dflt</c-slot></c-fill></c-Card>"#,
        4,
        CompileMode::Html,
    );
    assert_eq!(
        code,
        r##"def generate_template():
    _n1 = (StaticHtmlAttr(source, (16, 27,), """name""", """body""", ()),)
    _n2 = SlotNode(source, (28, 62,), (StaticHtmlAttr(source, (36, 48,), """name""", """inner""", ()),), ["""dflt""",], (), ())
    _n3 = FillNode(source, (8, 71,), _n1, [_n2,], (), ())
    body = [ComponentNode(source, (0, 80,), (), [_n3,], (), """card""", True),]
    return body
"##
    );
}

#[test]
fn element_attributes_and_key_move_with_their_branch() {
    // A plain element adds no brackets of its own, so its `ElementAttrsNode`
    // and `ElementKeyNode` stay in the body list of the moved branch.
    let code = compile_at(
        r#"<c-if cond="x"><div c-class="cls" #c-key="k">{{ y }}</div></c-if>"#,
        6,
        CompileMode::Html,
    );
    assert_eq!(
        code,
        r##"def generate_template():
    _n1 = ((0, 65,), (ExprHtmlAttr(source, (6, 14,), """cond""", """x""", ("x",)),), ["""<div""", ElementAttrsNode(source, (15, 45,), (ExprHtmlAttr(source, (20, 33,), """c-class""", """cls""", ("cls",)),), ("cls",)), ElementKeyNode(ExprHtmlAttr(source, (34, 44,), """#c-key""", """k""", ("k",))), """>""", ExprNode(source, (45, 52,), """y """, ("y",)), """</div>""",], (),)
    body = [IfNode(source, (_n1,), ("y", "cls", "k", "x",)),]
    return body
"##
    );
}

#[test]
fn prepared_mode_moves_the_same_way() {
    // Prepared mode writes element nodes instead of text, and the same rule
    // applies to them.
    let code = compile_at(
        r#"<c-if cond="x"><p c-title="t">{{ v }}</p></c-if>"#,
        6,
        CompileMode::Prepared,
    );
    assert_eq!(
        code,
        r##"def generate_template():
    _n1 = ((0, 48,), (ExprHtmlAttr(source, (6, 14,), """cond""", """x""", ("x",)),), [PreparedElementOpenNode(source, (15, 30,), """p""", (ExprHtmlAttr(source, (18, 29,), """c-title""", """t""", ("t",)),), ("t",), False, False, ()), PreparedExprNode(source, (30, 37,), """v """, ("v",)), PreparedElementCloseNode(source, (37, 41,), """p"""),], (),)
    body = [IfNode(source, (_n1,), ("v", "t", "x",)),]
    return body
"##
    );
}

#[test]
fn constructor_before_a_deep_sibling_moves_first() {
    // Only the `<c-if>` branch is too deep, but the `ExprNode` and the
    // `ComponentNode` before it are built first in the single statement, so
    // they move out first, in the same order.
    let code = compile_at(
        r#"{{ a }}<c-Card c-x="b"/><c-if cond="x"><c-if cond="y">deep</c-if></c-if>"#,
        8,
        CompileMode::Html,
    );
    assert_eq!(
        code,
        r##"def generate_template():
    _n1 = ExprNode(source, (0, 7,), """a """, ("a",))
    _n2 = ComponentNode(source, (7, 24,), (ExprHtmlAttr(source, (15, 22,), """c-x""", """b""", ("b",)),), [], ("b",), """card""", False)
    _n3 = ((24, 72,), (ExprHtmlAttr(source, (30, 38,), """cond""", """x""", ("x",)),), [IfNode(source, (((39, 65,), (ExprHtmlAttr(source, (45, 53,), """cond""", """y""", ("y",)),), ["""deep""",], (),),), ("y",)),], (),)
    body = [_n1, _n2, IfNode(source, (_n3,), ("y", "x",)),]
    return body
"##
    );
}

#[test]
fn thirty_nested_ifs_at_the_real_budget() {
    // 30 levels need 123 brackets in one statement. The printer moves the
    // branch that reaches 100, and the five attribute tuples to its left,
    // which build `ExprHtmlAttr` objects before it.
    let source = r#"<c-if cond="x">"#.repeat(30) + "deep" + &"</c-if>".repeat(30);
    let code = compile_html_at(&source, 100);
    assert_eq!(
        code,
        r##"def generate_template():
    _n1 = (ExprHtmlAttr(source, (6, 14,), """cond""", """x""", ("x",)),)
    _n2 = (ExprHtmlAttr(source, (21, 29,), """cond""", """x""", ("x",)),)
    _n3 = (ExprHtmlAttr(source, (36, 44,), """cond""", """x""", ("x",)),)
    _n4 = (ExprHtmlAttr(source, (51, 59,), """cond""", """x""", ("x",)),)
    _n5 = (ExprHtmlAttr(source, (66, 74,), """cond""", """x""", ("x",)),)
    _n6 = ((75, 629,), (ExprHtmlAttr(source, (81, 89,), """cond""", """x""", ("x",)),), [IfNode(source, (((90, 622,), (ExprHtmlAttr(source, (96, 104,), """cond""", """x""", ("x",)),), [IfNode(source, (((105, 615,), (ExprHtmlAttr(source, (111, 119,), """cond""", """x""", ("x",)),), [IfNode(source, (((120, 608,), (ExprHtmlAttr(source, (126, 134,), """cond""", """x""", ("x",)),), [IfNode(source, (((135, 601,), (ExprHtmlAttr(source, (141, 149,), """cond""", """x""", ("x",)),), [IfNode(source, (((150, 594,), (ExprHtmlAttr(source, (156, 164,), """cond""", """x""", ("x",)),), [IfNode(source, (((165, 587,), (ExprHtmlAttr(source, (171, 179,), """cond""", """x""", ("x",)),), [IfNode(source, (((180, 580,), (ExprHtmlAttr(source, (186, 194,), """cond""", """x""", ("x",)),), [IfNode(source, (((195, 573,), (ExprHtmlAttr(source, (201, 209,), """cond""", """x""", ("x",)),), [IfNode(source, (((210, 566,), (ExprHtmlAttr(source, (216, 224,), """cond""", """x""", ("x",)),), [IfNode(source, (((225, 559,), (ExprHtmlAttr(source, (231, 239,), """cond""", """x""", ("x",)),), [IfNode(source, (((240, 552,), (ExprHtmlAttr(source, (246, 254,), """cond""", """x""", ("x",)),), [IfNode(source, (((255, 545,), (ExprHtmlAttr(source, (261, 269,), """cond""", """x""", ("x",)),), [IfNode(source, (((270, 538,), (ExprHtmlAttr(source, (276, 284,), """cond""", """x""", ("x",)),), [IfNode(source, (((285, 531,), (ExprHtmlAttr(source, (291, 299,), """cond""", """x""", ("x",)),), [IfNode(source, (((300, 524,), (ExprHtmlAttr(source, (306, 314,), """cond""", """x""", ("x",)),), [IfNode(source, (((315, 517,), (ExprHtmlAttr(source, (321, 329,), """cond""", """x""", ("x",)),), [IfNode(source, (((330, 510,), (ExprHtmlAttr(source, (336, 344,), """cond""", """x""", ("x",)),), [IfNode(source, (((345, 503,), (ExprHtmlAttr(source, (351, 359,), """cond""", """x""", ("x",)),), [IfNode(source, (((360, 496,), (ExprHtmlAttr(source, (366, 374,), """cond""", """x""", ("x",)),), [IfNode(source, (((375, 489,), (ExprHtmlAttr(source, (381, 389,), """cond""", """x""", ("x",)),), [IfNode(source, (((390, 482,), (ExprHtmlAttr(source, (396, 404,), """cond""", """x""", ("x",)),), [IfNode(source, (((405, 475,), (ExprHtmlAttr(source, (411, 419,), """cond""", """x""", ("x",)),), [IfNode(source, (((420, 468,), (ExprHtmlAttr(source, (426, 434,), """cond""", """x""", ("x",)),), [IfNode(source, (((435, 461,), (ExprHtmlAttr(source, (441, 449,), """cond""", """x""", ("x",)),), ["""deep""",], (),),), ("x",)),], (),),), ("x",)),], (),),), ("x",)),], (),),), ("x",)),], (),),), ("x",)),], (),),), ("x",)),], (),),), ("x",)),], (),),), ("x",)),], (),),), ("x",)),], (),),), ("x",)),], (),),), ("x",)),], (),),), ("x",)),], (),),), ("x",)),], (),),), ("x",)),], (),),), ("x",)),], (),),), ("x",)),], (),),), ("x",)),], (),),), ("x",)),], (),),), ("x",)),], (),),), ("x",)),], (),),), ("x",)),], (),),), ("x",)),], (),),), ("x",)),], (),),), ("x",)),], (),)
    body = [IfNode(source, (((0, 664,), _n1, [IfNode(source, (((15, 657,), _n2, [IfNode(source, (((30, 650,), _n3, [IfNode(source, (((45, 643,), _n4, [IfNode(source, (((60, 636,), _n5, [IfNode(source, (_n6,), ("x",)),], (),),), ("x",)),], (),),), ("x",)),], (),),), ("x",)),], (),),), ("x",)),], (),),), ("x",)),]
    return body
"##
    );
    // The public entry point uses the same budget.
    let template = parse_template(&source, None, None).unwrap();
    assert_eq!(
        crate::compiler::compile_template(template, None).unwrap(),
        code
    );
}

#[test]
fn a_statement_past_python_limit_is_an_internal_error() {
    // A budget above CPython's limit lets a statement grow past 200
    // brackets, which only a printer bug could do with the real budget.
    // The self-check reports it instead of returning code Python rejects.
    let args = nested_args(SHAPES[0], 60);
    let error = compile_with_bracket_budget(args, 1_000).unwrap_err();
    assert_eq!(
        error,
        "internal error: a generated statement nests 243 brackets, more than the 200 \
         CPython allows. This is a Citry bug; please report it with the template."
    );
}
