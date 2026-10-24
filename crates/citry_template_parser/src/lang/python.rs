use std::collections::HashSet;
use std::ops::Range;

use python_safe_eval::transformer::{
    parse_expression_with_adjusted_error_ranges, transform_expression_string,
    Comment as SafeEvalComment, Token as SafeEvalToken,
};
use ruff_python_ast::Expr as PythonAstExpr;
use ruff_text_size::Ranged;

use crate::ast::{Comment, Token};
use crate::lang::lang::{ForLoopVars, LangImpl, LangSpecArgument, ParseExprResult};

/// Python language implementation
#[derive(Copy, Clone)]
pub struct PythonLang;

/// Static instance of PythonLang for use as a default
pub static PYTHON_LANG: PythonLang = PythonLang;

impl LangImpl for PythonLang {
    fn parse_expression(&self, source: &str) -> Result<ParseExprResult, String> {
        // Delegate to python_safe_eval to parse the expression and get metadata about
        // used variables, assigned variables, and comments.
        let transform_result = transform_expression_string(source)?;

        // Convert SafeEvalToken to citry_template_parser Token
        let convert_token = |safe_token: SafeEvalToken| -> Token {
            Token {
                content: safe_token.content,
                start_index: safe_token.start_index,
                end_index: safe_token.end_index,
                line_col: (safe_token.line_col.0, safe_token.line_col.1),
            }
        };

        // Convert SafeEvalComment to citry_template_parser Comment
        let convert_comment = |comment: SafeEvalComment| -> Comment {
            Comment {
                token: convert_token(comment.token),
                value: convert_token(comment.value),
            }
        };

        Ok(ParseExprResult {
            used_vars: transform_result
                .used_vars
                .into_iter()
                .map(convert_token)
                .collect(),
            assigned_vars: transform_result
                .assigned_vars
                .into_iter()
                .map(convert_token)
                .collect(),
            comments: transform_result
                .comments
                .into_iter()
                .map(convert_comment)
                .collect(),
        })
    }

    fn parse_forloop_variables(&self, source: &str) -> Result<ForLoopVars, String> {
        // `a, b in items` is not a valid expression on its own, so we wrap it in a
        // generator and analyse that: `(None for a, b in items)`. Both halves of
        // the result come from this one wrapped clause.
        let prefix = "(None for ";
        let prefix_len = prefix.len();
        // The physical newline keeps a trailing Python comment in the authored
        // clause from swallowing the synthetic closing parenthesis.
        let wrapped_expr = format!("{}{}\n)", prefix, source);

        // --- Introduced (loop target) variables ---
        // Parse the comprehension and walk each generator's target. (Parsing
        // errors are reported against the ORIGINAL source, hence the prefix-aware
        // helper.)
        let ast = parse_expression_with_adjusted_error_ranges(&wrapped_expr, source, prefix_len)?;

        // Extract the expression from the module
        let module = ast.syntax();

        // Check if it's a generator expression
        let generators = match module.body.as_ref() {
            PythonAstExpr::Generator(expr_gen) => {
                // Must have at least one generator
                if expr_gen.generators.is_empty() {
                    return Err(
                        "Tag '<c-for>' 'each' attribute must contain at least one 'for ... in ...' clause."
                            .to_string(),
                    );
                }
                &expr_gen.generators
            }
            _ => {
                return Err(
                    "Tag '<c-for>' 'each' attribute must be a comprehension expression (e.g., 'target in iterable' or 'x in range(3) for y in range(2) if x > y')."
                        .to_string(),
                );
            }
        };

        // Extract variable tokens from all generators
        let mut introduced = Vec::new();
        let mut introduced_by_generator = Vec::new();
        for comprehension in generators {
            let var_tokens = _extract_variable_names_from_comp_target(
                &comprehension.target,
                source,
                prefix_len,
            )?;
            // NOTE: This should never raise, because Ruff would error first.
            if var_tokens.is_empty() {
                return Err(
                    "Tag '<c-for>' 'each' attribute: each 'for ... in ...' clause must have at least one loop variable."
                        .to_string(),
                );
            }
            introduced.extend(var_tokens.clone());
            introduced_by_generator.push(var_tokens);
        }
        // If no variables were found, raise error
        // NOTE: This should never raise, because Ruff would error first.
        if introduced.is_empty() {
            return Err(
                "Tag '<c-for>' 'each' attribute must have at least one loop variable.".to_string(),
            );
        }

        // --- Used (free) variables ---
        // Analyse every iterable before binding that generator's target. Python
        // comprehension scope starts only after `in`, so `x in x` reads an outer
        // `x` and must not be erased as though the target already existed. Prior
        // generator targets are in scope for later iterables and conditions.
        let mut used = Vec::new();
        let mut bound_names = HashSet::new();
        for (comprehension, target_tokens) in generators.iter().zip(introduced_by_generator.iter())
        {
            used.extend(_extract_free_variables_from_comp_expr(
                self,
                &comprehension.iter,
                &wrapped_expr,
                source,
                prefix_len,
                &bound_names,
            )?);

            bound_names.extend(target_tokens.iter().map(|token| token.content.clone()));
            for condition in &comprehension.ifs {
                used.extend(_extract_free_variables_from_comp_expr(
                    self,
                    condition,
                    &wrapped_expr,
                    source,
                    prefix_len,
                    &bound_names,
                )?);
            }
        }

        Ok(ForLoopVars { introduced, used })
    }

    // Generate code for a Python function that returns a list of node objects (TextNode, ExprNode, etc.)
    // that represent the template structure.
    //
    // ```python
    // def generate_template():
    //     body = [
    //         """Hello, \"John\"!""",
    //         ExprNode(source, (14, 19), """a + b""", ("a", "b")),
    //         ComponentNode(source, (14, 19), (HtmlAttr(...), ...),
    //         """<a href=\"""",
    //         ExprNode(source, (14, 19), """base + 'foo'""", ("base",)),
    //         """\">Click me!</a>""",
    //         ...
    //     ]
    //     return body
    // ```
    //
    // The body is kept as a list, so it can be optimized at runtime by replacing
    // nodes with their result as text, if we find that they are static.
    //
    // A template whose single statement would nest more than
    // `BRACKET_BUDGET` brackets also gets earlier `_nN = ...` statements;
    // see `compile_with_bracket_budget`.
    fn compile(&self, args: Vec<LangSpecArgument>) -> Result<String, String> {
        compile_with_bracket_budget(args, BRACKET_BUDGET)
    }
}

/// Extract free variables from one comprehension iterable/condition and map
/// their positions from the synthetic wrapped generator back to `source`.
fn _extract_free_variables_from_comp_expr(
    lang: &PythonLang,
    expr: &PythonAstExpr,
    wrapped_source: &str,
    source: &str,
    prefix_len: usize,
    bound_names: &HashSet<String>,
) -> Result<Vec<Token>, String> {
    let range = expr.range();
    let wrapped_start = range.start().to_usize();
    let wrapped_end = range.end().to_usize();
    if wrapped_start < prefix_len || wrapped_end > wrapped_source.len() {
        return Err("Internal error while mapping for-loop variable ranges.".to_string());
    }
    let expr_source = &wrapped_source[wrapped_start..wrapped_end];
    let source_start = wrapped_start - prefix_len;

    Ok(lang
        .parse_expression(expr_source)?
        .used_vars
        .into_iter()
        .filter(|token| !bound_names.contains(&token.content))
        .map(|mut token| {
            token.start_index += source_start;
            token.end_index += source_start;
            token.line_col = _byte_offset_to_line_col(source, token.start_index);
            token
        })
        .collect())
}

// #########################################################
// PRINTING THE GENERATED FUNCTION
// #########################################################
//
// The compiler hands the printer one tree of `LangSpecArgument` values, and
// that tree nests as deep as the template does: every `<c-if>` adds four
// open brackets (the `IfNode(` call, the branches tuple, the branch tuple
// and the body list). CPython refuses to compile a statement that holds more
// than 200 open brackets at once, so a single `body = [...]` assignment
// cannot hold a deep template.
//
// The printer therefore keeps every statement within a bracket budget. A
// template whose deepest point fits the budget prints as the single
// `body = [...]` assignment. For a deeper template, the printer
// moves some subtrees into local variables (`_n1`, `_n2`, ...) that earlier
// statements assign, and writes the variable's name where the subtree was.
// Each new statement starts again at zero open brackets.
//
// The passes below walk the tree with loops over a flat node list and
// explicit work lists, not recursion, so walking a deeper template needs no
// more Rust stack. (Dropping the tree afterwards still recurses, as the
// derived `Drop` of `LangSpecArgument` does everywhere.)

/// The most open brackets one generated statement may hold.
///
/// CPython's tokenizer rejects the 201st nested bracket ("too many nested
/// parentheses"). Half of that leaves room for a later change to the node
/// shapes, and still lets templates up to about 24 nested `<c-if>` print as
/// one `body = [...]` statement.
const BRACKET_BUDGET: usize = 100;

/// CPython's own limit, checked once more on every finished statement.
const PYTHON_MAX_OPEN_BRACKETS: usize = 200;

/// One node of the `LangSpecArgument` tree, with what the printer learned
/// about it.
struct PrintNode<'a> {
    arg: &'a LangSpecArgument,
    /// The node's children. They sit next to each other in the node list,
    /// in source order, and always after their parent.
    children: Range<usize>,
    /// The most brackets this subtree holds open at once inside its
    /// statement, once the moves already chosen below it are applied.
    depth: usize,
    /// True when the subtree calls a constructor (holds a `Struct`).
    /// Python runs constructors, which can raise, so their order matters.
    calls_constructor: bool,
    /// True when some node below this one, in the same statement, moves out.
    holds_move: bool,
    /// True when this subtree is assigned to a local variable in an
    /// earlier statement.
    moves_out: bool,
    /// The `_nN` number of the local variable, once one is given.
    local_number: usize,
}

impl<'a> PrintNode<'a> {
    fn new(arg: &'a LangSpecArgument) -> Self {
        PrintNode {
            arg,
            children: 0..0,
            depth: 0,
            calls_constructor: false,
            holds_move: false,
            moves_out: false,
            local_number: 0,
        }
    }
}

/// The child values of a container argument, in the order Python evaluates
/// them. Leaves have none.
fn child_args(arg: &LangSpecArgument) -> &[LangSpecArgument] {
    match arg {
        LangSpecArgument::Tuple(elements) | LangSpecArgument::List(elements) => elements,
        LangSpecArgument::Struct(struct_arg) => &struct_arg.arguments,
        LangSpecArgument::Variable(_)
        | LangSpecArgument::UnsafeString(_)
        | LangSpecArgument::SafeString(_)
        | LangSpecArgument::Int(_)
        | LangSpecArgument::Bool(_) => &[],
    }
}

/// Print the `generate_template()` function for `args`, keeping each
/// statement within `budget` open brackets.
///
/// `PythonLang::compile` always passes [`BRACKET_BUDGET`]. Tests pass small
/// budgets to see the moved-out form on small templates.
pub(crate) fn compile_with_bracket_budget(
    args: Vec<LangSpecArgument>,
    budget: usize,
) -> Result<String, String> {
    // A budget of zero could not even hold the `body` list itself.
    let budget = budget.max(1);
    let root = LangSpecArgument::List(args);
    let mut nodes = flatten(&root);
    choose_moves_by_depth(&mut nodes, budget);
    keep_construction_order(&mut nodes);
    let statements = statement_order(&mut nodes);

    let mut code = String::from("def generate_template():\n");
    for &statement_root in &statements {
        // The root node is the `body` list. Every other statement assigns
        // one moved-out subtree to its local variable.
        if statement_root == 0 {
            code.push_str("    body = ");
        } else {
            code.push_str("    _n");
            code.push_str(&nodes[statement_root].local_number.to_string());
            code.push_str(" = ");
        }
        write_statement(&nodes, statement_root, &mut code)?;
        code.push('\n');
    }
    code.push_str("    return body\n");
    Ok(code)
}

/// List every node of the tree, each parent before its children, so the
/// later passes can walk it by index.
fn flatten(root: &LangSpecArgument) -> Vec<PrintNode<'_>> {
    let mut nodes = vec![PrintNode::new(root)];
    // Visiting nodes in list order and appending each one's children at the
    // end keeps every family of siblings together, in source order.
    let mut next = 0;
    while next < nodes.len() {
        let first_child = nodes.len();
        for child in child_args(nodes[next].arg) {
            nodes.push(PrintNode::new(child));
        }
        nodes[next].children = first_child..nodes.len();
        next += 1;
    }
    nodes
}

/// Pass 1, part one: decide which subtrees must move out so that no statement opens
/// more than `budget` brackets.
///
/// The pass works from the leaves up. A child that already opens `budget`
/// brackets would push its parent past the budget, so it moves out and
/// counts as a plain name (no brackets) in the parent. Deciding bottom-up
/// moves the fewest subtrees: a top-down rule would move every ancestor on
/// the deep path.
fn choose_moves_by_depth(nodes: &mut [PrintNode<'_>], budget: usize) {
    // Children always come after their parent, so walking the list
    // backwards finishes every child before its parent.
    for index in (0..nodes.len()).rev() {
        let children = nodes[index].children.clone();
        let mut calls_constructor = matches!(nodes[index].arg, LangSpecArgument::Struct(_));
        if children.is_empty() {
            // A node with no children opens no brackets, except an empty
            // `()`, `[]` or argument-less call, which opens one.
            nodes[index].depth = usize::from(!matches!(
                nodes[index].arg,
                LangSpecArgument::Variable(_)
                    | LangSpecArgument::UnsafeString(_)
                    | LangSpecArgument::SafeString(_)
                    | LangSpecArgument::Int(_)
                    | LangSpecArgument::Bool(_)
            ));
            nodes[index].calls_constructor = calls_constructor;
            continue;
        }
        let mut deepest_child = 0;
        let mut holds_move = false;
        for child in children {
            calls_constructor |= nodes[child].calls_constructor;
            // This node adds one bracket around its children, so a child at
            // the budget is one too many.
            if nodes[child].depth >= budget {
                nodes[child].moves_out = true;
            }
            if nodes[child].moves_out {
                holds_move = true;
            } else {
                deepest_child = deepest_child.max(nodes[child].depth);
                holds_move |= nodes[child].holds_move;
            }
        }
        nodes[index].depth = deepest_child + 1;
        nodes[index].calls_constructor = calls_constructor;
        nodes[index].holds_move = holds_move;
    }
}

/// Pass 1, part two: move out the earlier constructor calls that a move
/// would otherwise reorder.
///
/// Python builds a nested expression from the inside out and from left to
/// right, and some node constructors raise (`ComponentNode` rejects a
/// malformed `<c-mark>`, for example). A moved-out subtree now runs before
/// the statement that uses it. So every sibling to its left that calls a
/// constructor, at every level of the same statement, must also move out,
/// or it would run too late. Values that only hold numbers, strings and
/// names can stay, because building them has no effect anyone can see.
fn keep_construction_order(nodes: &mut [PrintNode<'_>]) {
    let mut pending = vec![0];
    while let Some(index) = pending.pop() {
        if !nodes[index].holds_move {
            continue;
        }
        let children = nodes[index].children.clone();
        // Everything left of the last child that moves out (or holds a
        // move) runs before that move in the original single statement.
        let Some(last_with_move) = children
            .clone()
            .rev()
            .find(|&child| nodes[child].moves_out || nodes[child].holds_move)
        else {
            continue;
        };
        for sibling in &mut nodes[children.start..last_with_move] {
            // The whole sibling moves, even when it holds moves of its own:
            // its own constructor must also run before the later move.
            if sibling.calls_constructor {
                sibling.moves_out = true;
            }
        }
        // A moved child starts its own statement, which needs the same
        // rule, and a child that holds a move needs it one level down.
        for child in children {
            if nodes[child].moves_out || nodes[child].holds_move {
                pending.push(child);
            }
        }
    }
}

/// Pass 2, part one: put the statements in the order Python must run them,
/// and number the local variables in that order.
///
/// A moved-out subtree is assigned before the statement that uses it, and
/// moved-out subtrees of the same statement keep their left-to-right order.
/// Moves nested inside a moved subtree come right before that subtree's own
/// statement. The order depends only on the tree, so the output is the same
/// on every run.
fn statement_order(nodes: &mut [PrintNode<'_>]) -> Vec<usize> {
    let mut order = Vec::new();
    // Each entry is a statement whose earlier statements are still being
    // written: its root, its moved-out subtrees, and how many are done.
    let mut open_statements = vec![(0, moves_in_statement(nodes, 0), 0)];
    while let Some((root, moves, done)) = open_statements.last_mut() {
        if let Some(&next_move) = moves.get(*done) {
            *done += 1;
            let nested_moves = moves_in_statement(nodes, next_move);
            open_statements.push((next_move, nested_moves, 0));
        } else {
            order.push(*root);
            open_statements.pop();
        }
    }
    // The `body` statement comes last and keeps its own name.
    for (number, &root) in order.iter().enumerate() {
        if root != 0 {
            nodes[root].local_number = number + 1;
        }
    }
    order
}

/// The subtrees that move out of the statement rooted at `root`, from left
/// to right. Subtrees nested inside one of them belong to its statement.
fn moves_in_statement(nodes: &[PrintNode<'_>], root: usize) -> Vec<usize> {
    let mut moves = Vec::new();
    let mut pending = vec![root];
    while let Some(index) = pending.pop() {
        if index != root && nodes[index].moves_out {
            moves.push(index);
            continue;
        }
        if nodes[index].holds_move {
            // Pushed in reverse, so the leftmost child is visited first.
            pending.extend(nodes[index].children.clone().rev());
        }
    }
    moves
}

/// One piece of a statement still to be written.
enum Step {
    Node(usize),
    Separator,
    Close(&'static str),
}

/// Pass 2, part two: write the expression of one statement into `code`.
///
/// Moved-out subtrees are written as their `_nN` name. For a template that
/// needs no moves, the text is the same, byte for byte, as printing every
/// child inline in one `body = [...]` statement.
fn write_statement(nodes: &[PrintNode<'_>], root: usize, code: &mut String) -> Result<(), String> {
    let mut open_brackets = 0;
    let mut most_open_brackets = 0;
    let mut steps = vec![Step::Node(root)];
    while let Some(step) = steps.pop() {
        let index = match step {
            Step::Node(index) => index,
            Step::Separator => {
                code.push_str(", ");
                continue;
            }
            Step::Close(text) => {
                code.push_str(text);
                open_brackets -= 1;
                continue;
            }
        };
        let node = &nodes[index];
        if index != root && node.moves_out {
            code.push_str("_n");
            code.push_str(&node.local_number.to_string());
            continue;
        }
        // Non-empty lists and tuples end with a trailing comma, so a tuple
        // with one item stays a tuple: `(a,)`, not `(a)`.
        let (open, close) = match node.arg {
            LangSpecArgument::Tuple(elements) if elements.is_empty() => ("()", ""),
            LangSpecArgument::List(elements) if elements.is_empty() => ("[]", ""),
            LangSpecArgument::Tuple(_) => ("(", ",)"),
            LangSpecArgument::List(_) => ("[", ",]"),
            LangSpecArgument::Struct(struct_arg) => {
                // A call such as `IfNode(source, ..., ("x",))`.
                code.push_str(&struct_arg.name);
                ("(", ")")
            }
            leaf => {
                code.push_str(&format_leaf(leaf));
                continue;
            }
        };
        code.push_str(open);
        most_open_brackets = most_open_brackets.max(open_brackets + 1);
        if close.is_empty() {
            continue;
        }
        open_brackets += 1;
        steps.push(Step::Close(close));
        // Pushed in reverse, so the children come out in source order with
        // a separator between each pair.
        for (position, child) in node.children.clone().enumerate().rev() {
            steps.push(Step::Node(child));
            if position > 0 {
                steps.push(Step::Separator);
            }
        }
    }
    // Pass 1 keeps every statement within the budget, so with the real
    // budget this only fires on a bug in this printer. Failing here names the bug, instead of
    // handing Python code it would reject with a confusing message.
    if most_open_brackets > PYTHON_MAX_OPEN_BRACKETS {
        return Err(format!(
            "internal error: a generated statement nests {most_open_brackets} \
             brackets, more than the {PYTHON_MAX_OPEN_BRACKETS} CPython allows. \
             This is a Citry bug; please report it with the template."
        ));
    }
    Ok(())
}

/// Format an argument that holds no other arguments.
pub(crate) fn format_leaf(arg: &LangSpecArgument) -> String {
    match arg {
        LangSpecArgument::Variable(name) => name.clone(),
        LangSpecArgument::UnsafeString(content) => escape_text_in_triple_quotes(content),
        // The compiler builds these from names the parser already checked, so
        // escaping changes nothing for them. It still runs, because one value,
        // a foreign span's provider name, reaches the parser from the host
        // with only a check that it is not empty, and an unescaped quote in it
        // would end the literal early.
        LangSpecArgument::SafeString(content) => {
            format!("\"{}\"", escape_python_string_content(content, true))
        }
        LangSpecArgument::Int(value) => value.to_string(),
        LangSpecArgument::Bool(value) => {
            if *value {
                "True".to_string()
            } else {
                "False".to_string()
            }
        }
        LangSpecArgument::Tuple(_) | LangSpecArgument::List(_) | LangSpecArgument::Struct(_) => {
            unreachable!("containers are written by write_statement")
        }
    }
}

/// Extract variable tokens from a Python AST comprehension target.
///
/// AKA the `x, y, z` part in `(... for x, y, z in ...)`
///
/// Handles:
/// - `ExprName` → `x, y, z for my_list`
/// - `ExprTuple` → `(x, y, z) for my_tuple`
/// - `ExprStarred` → `a, *my_list for my_list`
///
/// Returns a vector of Tokens with positions relative to the source string.
///
/// **Errors:**
/// - If the expression type is not a valid target (e.g., attribute access, calls, etc.)
fn _extract_variable_names_from_comp_target(
    expr: &PythonAstExpr,
    source: &str,
    prefix_len: usize,
) -> Result<Vec<Token>, String> {
    match expr {
        PythonAstExpr::Name(expr_name) => {
            // Get the range from the AST (relative to the wrapped expression)
            let range = expr_name.range;
            let ast_start = range.start().to_usize();
            let ast_end = range.end().to_usize();

            // Adjust positions: subtract prefix_len to get position in original expression
            let adjusted_start = ast_start.saturating_sub(prefix_len);
            let adjusted_end = ast_end.saturating_sub(prefix_len);

            // Calculate line and column from the adjusted byte offset
            let (line, col) = _byte_offset_to_line_col(source, adjusted_start);
            let content = expr_name.id.as_str().to_string();

            Ok(vec![Token {
                content,
                start_index: adjusted_start,
                end_index: adjusted_end,
                line_col: (line, col),
            }])
        }
        PythonAstExpr::Tuple(expr_tuple) => {
            let mut tokens = Vec::new();
            for elt in &expr_tuple.elts {
                tokens.extend(_extract_variable_names_from_comp_target(
                    elt, source, prefix_len,
                )?);
            }
            Ok(tokens)
        }
        PythonAstExpr::Starred(expr_starred) => {
            _extract_variable_names_from_comp_target(&expr_starred.value, source, prefix_len)
        }
        // Other expression types are not valid targets
        _ => Err(format!(
            "Invalid expression type in loop variable: expected variable name, tuple, or starred expression, but found: {:?}",
            std::mem::discriminant(expr)
        )),
    }
}

/// Calculate line and column from a byte offset in a string
///
/// Returns (line, column) where both are 1-indexed.
fn _byte_offset_to_line_col(source: &str, byte_offset: usize) -> (usize, usize) {
    // Clamp offset to source length
    let offset = byte_offset.min(source.len());

    // Count newlines up to the offset
    let mut line = 1;
    let mut last_newline_pos = 0;

    // Iterate through the string up to the offset, counting newlines
    for (pos, ch) in source.char_indices() {
        if pos >= offset {
            break;
        }
        if ch == '\n' {
            line += 1;
            last_newline_pos = pos + 1; // +1 to skip the newline itself
        }
    }

    // Columns count Unicode scalar values, matching Pest's character columns.
    let column = source
        .get(last_newline_pos..offset)
        .map_or(1, |line_prefix| line_prefix.chars().count() + 1);

    (line, column)
}

/// Escape text content for use in Python triple-quoted strings.
///
/// This escapes backslashes, double quotes (including triple-quote sequences),
/// carriage returns, and NUL characters. Always uses triple double quotes `"""`
/// for consistency.
///
/// A literal newline is left as-is: it is legal inside a triple-quoted string and
/// round-trips faithfully. A carriage return must be escaped as `\r`, because
/// Python applies universal-newline normalization to *source* before tokenizing,
/// so a raw `\r` (or `\r\n`) inside a literal would be silently rewritten to `\n`,
/// losing the original bytes. Every other character Rust can hold in a `&str`
/// survives a triple-quoted literal unchanged, except NUL, which Python refuses
/// anywhere in source code.
fn escape_text_in_triple_quotes(text: &str) -> String {
    format!("\"\"\"{}\"\"\"", escape_python_string_content(text, false))
}

/// Escape the characters a Python string literal cannot hold as written.
///
/// Set `escape_newlines` for a one-line `"..."` literal, which a raw newline
/// would end. Every character is visited once, so a backslash added
/// by one rule is never escaped again by another.
fn escape_python_string_content(text: &str, escape_newlines: bool) -> String {
    let mut escaped = String::with_capacity(text.len());
    for ch in text.chars() {
        match ch {
            // A raw backslash would start an escape sequence, and a trailing
            // one would escape the closing quote.
            '\\' => escaped.push_str("\\\\"),
            // Escaping every quote keeps even `"""` from ending the literal.
            '"' => escaped.push_str("\\\""),
            // Python rewrites a raw `\r` to `\n` before it reads the source.
            '\r' => escaped.push_str("\\r"),
            '\n' if escape_newlines => escaped.push_str("\\n"),
            // Python rejects source that contains a NUL byte. `\x00` rather
            // than `\0`, because a following digit would turn `\0` into a
            // longer octal escape.
            '\0' => escaped.push_str("\\x00"),
            _ => escaped.push(ch),
        }
    }
    escaped
}
