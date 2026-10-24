//! Deep expressions end in a clean error, never a crash.
//!
//! `nesting::check_nesting` rejects an expression whose tree could be deeper
//! than `MAX_NESTING`, before anything builds or walks the tree, and each
//! public entry point makes sure the passes have enough stack. These tests
//! check both halves on random expressions that mix most constructs that nest
//! the tree, and on a pure chain of each construct, because slack from other
//! constructs in a random mix can hide one that counts too low:
//!
//! - the bound is never smaller than the real depth of the tree Ruff builds,
//!   so the check cannot let a too-deep tree through;
//! - on a thread with a 256 KiB stack, every accepted expression goes through
//!   every pass without a crash, and every rejected one gets the clean error.
//!
//! A crash here aborts this test binary, which fails the test run.

use python_safe_eval::nesting::{MAX_NESTING, nesting_bound};
use python_safe_eval::{parse_expression, safe_eval, transform_expression_string};
use ruff_python_ast::AnyNodeRef;
use ruff_python_ast::visitor::source_order::{SourceOrderVisitor, TraversalSignal};

/// The clean error's wording, which callers show to template authors.
const TOO_DEEP: &str = "expression is nested too deeply";

/// A small random-number generator, so the test needs no extra crate and
/// every run checks the same expressions.
struct XorShift(u64);

impl XorShift {
    fn next(&mut self) -> u64 {
        self.0 ^= self.0 << 13;
        self.0 ^= self.0 >> 7;
        self.0 ^= self.0 << 17;
        self.0
    }

    fn below(&mut self, limit: usize) -> usize {
        (self.next() % limit as u64) as usize
    }
}

/// Build a random expression that nests about `depth` constructs deep.
///
/// One child carries the depth and the others stay small, so the text grows
/// with the depth rather than exponentially. Built in a loop from the inside
/// out, so the generator needs no recursion either.
fn random_expression(random: &mut XorShift, depth: usize) -> String {
    let leaves = ["x", "1", "'s'", "None", "a.b", "f()", "[]", "1.5"];
    let mut expression = leaves[random.below(leaves.len())].to_string();
    for _ in 0..depth {
        let small = leaves[random.below(leaves.len())];
        let inner = expression;
        // Parentheses make no tree node, so operands are wrapped in them:
        // that keeps low-precedence forms such as `lambda` and `not` valid
        // where an operator needs an operand.
        let operand = format!("({inner})");
        expression = match random.below(28) {
            0 => format!("{operand} + {small}"),
            1 => format!("{small} * {operand}"),
            2 => format!("{operand} ** {small}"),
            3 => format!("{small} < {operand} <= {small}"),
            4 => format!("{small} in {operand}"),
            5 => format!("-{operand}"),
            6 => format!("~{operand}"),
            7 => format!("not {operand}"),
            8 => format!("{operand}.attr"),
            9 => format!("f({small}, key={inner}, *args, **kwargs)"),
            10 => format!("{small}[{inner}]"),
            11 => format!("{small}[{inner}:{small}:2]"),
            12 => format!("[{small}, {inner}]"),
            13 => format!("({inner},)"),
            14 => format!("{{{small}: {inner}}}"),
            15 => format!("{{{inner}}}"),
            16 => format!("{small} if {operand} else {small}"),
            17 => format!("lambda q, r=1: {inner}"),
            18 => format!("(w := {inner})"),
            19 => format!("f'{{{inner}!r:>{{{small}}}}}'"),
            20 => format!("[q for q in {operand} if q]"),
            21 => format!("{small} and {operand} or {small}"),
            22 => format!("{operand} is not {small}"),
            23 => format!("(*{operand},)"),
            24 => format!("{operand} @ {small} // {small}"),
            // Calls and subscripts on the deep part nest with no operator
            // token between the levels. (Case 17 covers a lambda whose
            // parameter commas must not start a new part.)
            25 => format!("{operand}({small})"),
            26 => format!("{operand}[0]"),
            _ => operand,
        };
    }
    expression
}

/// The depth of the tree Ruff builds for `source`, counting every node.
fn tree_depth(source: &str) -> Option<usize> {
    struct Depth {
        current: usize,
        deepest: usize,
    }
    impl<'a> SourceOrderVisitor<'a> for Depth {
        fn enter_node(&mut self, _node: AnyNodeRef<'a>) -> TraversalSignal {
            self.current += 1;
            self.deepest = self.deepest.max(self.current);
            TraversalSignal::Traverse
        }
        fn leave_node(&mut self, _node: AnyNodeRef<'a>) {
            self.current -= 1;
        }
    }
    // Ruff's own parser, so the depth check does not reject the input first.
    let parsed = ruff_python_parser::parse_expression(source).ok()?;
    let mut depth = Depth {
        current: 0,
        deepest: 0,
    };
    depth.visit_expr(&parsed.syntax().body);
    Some(depth.deepest)
}

/// Run `check` on a thread with `stack` bytes of stack.
fn on_stack(stack: usize, check: impl FnOnce() + Send + 'static) {
    std::thread::Builder::new()
        .stack_size(stack)
        .spawn(check)
        .unwrap()
        .join()
        .unwrap();
}

/// Run every public pass on `source`, and check that a rejected expression
/// gets the clean error.
fn run_every_pass(source: &str) {
    let rejected = nesting_bound(source) > MAX_NESTING;
    let parsed = parse_expression(source)
        .map(|_| ())
        .map_err(|e| e.to_string());
    let transformed = transform_expression_string(source).map(|_| ());
    let evaluated = safe_eval(source).map(|_| ());
    if rejected {
        for result in [parsed, transformed, evaluated] {
            let error = result.expect_err("a rejected expression must fail");
            assert!(error.contains(TOO_DEEP), "unexpected error: {error}");
        }
    }
}

/// 26 common constructs that nest the tree, each repeated `n` times in a pure
/// chain.
///
/// A random mix hides a part that counts too low behind the slack of other
/// constructs, so each construct also gets a chain of its own.
fn chains(n: usize) -> Vec<String> {
    vec![
        "[".repeat(n) + &"]".repeat(n),
        "(".repeat(n) + "1" + &",)".repeat(n),
        "{1: ".repeat(n) + "1" + &"}".repeat(n),
        "{".repeat(n) + "1" + &"}".repeat(n),
        "1".to_string() + &"+1".repeat(n),
        "2".to_string() + &"**2".repeat(n),
        "not ".repeat(n) + "x",
        "-".repeat(n) + "1",
        "a".to_string() + &".b".repeat(n),
        "1 if x else ".repeat(n) + "2",
        "(x if ".repeat(n) + "y" + &" else z)".repeat(n),
        "f".to_string() + &"()".repeat(n),
        "f".to_string() + &"(1, 2)".repeat(n),
        "a".to_string() + &"[0]".repeat(n),
        "a".to_string() + &"[1:2]".repeat(n),
        "f(x=".repeat(n) + "1" + &")".repeat(n),
        "f(*".repeat(n) + "a" + &")".repeat(n),
        "lambda: ".repeat(n) + "1",
        "lambda a, b: ".repeat(n) + "x",
        "lambda a=1, *b, c=2, **d: ".repeat(n) + "x",
        "(w := ".repeat(n) + "1" + &")".repeat(n),
        "[x for x in ".repeat(n) + "y" + &"]".repeat(n),
        "{x: x for x in ".repeat(n) + "y" + &"}".repeat(n),
        "(x for x in ".repeat(n) + "y" + &")".repeat(n),
        {
            let mut nested = "x".to_string();
            for _ in 0..n {
                nested = format!("f'{{{nested}}}'");
            }
            nested
        },
        {
            let mut nested = "x".to_string();
            for _ in 0..n {
                nested = format!("f'{{x:{{{nested}}}}}'");
            }
            nested
        },
    ]
}

#[test]
fn bound_is_never_below_the_tree_depth_of_any_chain() {
    on_stack(256 * 1024 * 1024, || {
        for n in [1, 2, 3, 10, 50, 300] {
            for source in chains(n) {
                let tree = tree_depth(&source)
                    .unwrap_or_else(|| panic!("chain does not parse: {source:.80}"));
                let bound = nesting_bound(&source);
                assert!(
                    bound >= tree,
                    "bound {bound} is below the tree depth {tree} for {source:.80}"
                );
            }
        }
    });
}

#[test]
fn every_chain_finishes_or_fails_cleanly_on_a_small_stack() {
    on_stack(256 * 1024, || {
        for n in [10, 50, 100, 300, 3_000] {
            for source in chains(n) {
                run_every_pass(&source);
            }
        }
    });
}

#[test]
fn bound_is_never_below_the_tree_depth() {
    // The tree walker here recurses, so give it room.
    on_stack(256 * 1024 * 1024, || {
        let mut random = XorShift(0x9e37_79b9_7f4a_7c15);
        let mut checked = 0;
        for _ in 0..2_000 {
            let depth = 1 + random.below(120);
            let source = random_expression(&mut random, depth);
            let Some(tree) = tree_depth(&source) else {
                continue;
            };
            checked += 1;
            let bound = nesting_bound(&source);
            assert!(
                bound >= tree,
                "bound {bound} is below the tree depth {tree} for {source}"
            );
        }
        // Most generated expressions must parse, or the check proves little.
        assert!(checked > 1_500, "only {checked} expressions parsed");
    });
}

#[test]
fn every_expression_finishes_or_fails_cleanly_on_a_small_stack() {
    on_stack(256 * 1024, || {
        let mut random = XorShift(0x2545_f491_4f6c_dd1d);
        let mut accepted = 0;
        let mut rejected = 0;
        for _ in 0..400 {
            // Depths up to 150 constructs give bounds on both sides of the
            // limit.
            let depth = 1 + random.below(150);
            let source = random_expression(&mut random, depth);
            if nesting_bound(&source) > MAX_NESTING {
                rejected += 1;
            } else {
                accepted += 1;
            }
            run_every_pass(&source);
        }
        assert!(
            accepted > 50 && rejected > 50,
            "{accepted} accepted, {rejected} rejected"
        );
    });
}

/// Shapes that overflow the stack without the depth check, each nesting `n`
/// deep.
fn crash_shapes(n: usize) -> Vec<String> {
    vec![
        "[".repeat(n) + &"]".repeat(n),
        "1".to_string() + &"+1".repeat(n),
        "not ".repeat(n) + "x",
        "-".repeat(n) + "1",
        "a".to_string() + &".b".repeat(n),
        "1 if x else ".repeat(n) + "2",
    ]
}

#[test]
fn crash_shapes_finish_below_the_limit_and_fail_cleanly_above_it() {
    on_stack(256 * 1024, || {
        for n in [10, 40, 60, 66, 67, 99, 100, 101, 150, 10_000] {
            for source in crash_shapes(n) {
                run_every_pass(&source);
            }
        }
    });
}

#[test]
fn crash_shapes_at_the_limit_are_accepted() {
    // The largest of each shape that the check still accepts, found from the
    // bound itself, must run every pass on a small stack.
    on_stack(256 * 1024, || {
        for shape in 0..6 {
            let largest = (1..1_000)
                .take_while(|&n| nesting_bound(&crash_shapes(n)[shape]) <= MAX_NESTING)
                .last()
                .unwrap();
            let source = crash_shapes(largest)[shape].clone();
            assert!(parse_expression(&source).is_ok(), "{source}");
            run_every_pass(&source);
            let over = crash_shapes(largest + 1)[shape].clone();
            let error = parse_expression(&over).unwrap_err().to_string();
            assert!(error.contains(TOO_DEEP), "{error}");
        }
    });
}

#[test]
fn flat_expressions_with_many_brackets_are_accepted() {
    // Adjacent f-string fields and joined f-strings sit side by side in a flat
    // tree, so their count must not grow as if each were a call.
    for source in [
        "f'".to_string() + &"{a}".repeat(500) + "'",
        "f'{a}' ".repeat(500),
        "[".to_string() + &"{1: 2}, ".repeat(500) + "]",
    ] {
        assert!(
            nesting_bound(&source) < 40,
            "{source:.40}: {}",
            nesting_bound(&source)
        );
    }
}

#[test]
fn ordinary_expressions_stay_far_below_the_limit() {
    // The example in `MAX_NESTING`'s doc comment.
    assert_eq!(nesting_bound("a.b(c[d] + 1)"), 16);
    for source in [
        "a.b(c[d] + 1)",
        "user.name if user else 'guest'",
        "[item.price * item.count for item in cart.items if item.visible]",
        "f'{name!r:>{width}}'",
        "{'a': 1, 'b': [1, 2, 3], 'c': (x, y)}",
    ] {
        assert!(
            nesting_bound(source) < 40,
            "{source}: {}",
            nesting_bound(source)
        );
    }
}
