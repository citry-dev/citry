//! A template nested past the depth limits gets no plan, so Python's
//! evaluator renders it, and one at the limits still gets one.
//!
//! The limits bound how deep the plan's walks call themselves; see
//! `MAX_BODY_DEPTH` in `src/plan.rs`. These tests build each shape at the
//! limit and one level past it.

use citry_native_render::{
    ExprSpec, Kinds, MAX_BODY_DEPTH, MAX_READ_DEPTH, OpSpec, Plan, PlanSpec, ReadNodeSpec, Value,
};

fn path(root: &str, keys: &[&str]) -> ExprSpec {
    ExprSpec::Path {
        root: root.to_owned(),
        keys: keys.iter().map(|key| (*key).to_owned()).collect(),
    }
}

fn node(
    kinds: Kinds,
    children: Vec<(String, ReadNodeSpec)>,
    items: Option<ReadNodeSpec>,
) -> ReadNodeSpec {
    ReadNodeSpec {
        kinds,
        children,
        items: items.map(Box::new),
    }
}

fn spec(
    ops: Vec<OpSpec>,
    roots: Vec<(String, ReadNodeSpec)>,
    loop_targets: Vec<String>,
) -> PlanSpec {
    PlanSpec {
        ops,
        roots,
        loop_targets,
        js_safe_integer: 9_007_199_254_740_991,
    }
}

const SCALAR: Kinds = Kinds {
    scalar: true,
    list: false,
    truth: false,
    safe_attrs_or_none: false,
    safe_attrs: false,
};

const TRUTH: Kinds = Kinds {
    scalar: false,
    list: false,
    truth: true,
    safe_attrs_or_none: false,
    safe_attrs: false,
};

const LIST: Kinds = Kinds {
    scalar: false,
    list: true,
    truth: false,
    safe_attrs_or_none: false,
    safe_attrs: false,
};

/// `{{ n }}` inside `loops` nested `c-for`s, each over the item of the loop
/// around it, as in issue #422.
fn nested_loops(loops: usize) -> PlanSpec {
    let mut ops = vec![OpSpec::Text {
        key: "t".to_owned(),
        expr: path("n", &[]),
    }];
    // The innermost loop's items are only counted.
    let mut items = node(Kinds::default(), Vec::new(), None);
    let mut targets = Vec::new();
    for level in (0..loops).rev() {
        let target = format!("r{level}");
        let iterable = if level == 0 {
            path("rows", &[])
        } else {
            path(&format!("r{}", level - 1), &[])
        };
        ops = vec![OpSpec::For {
            key: format!("f{level}"),
            target: target.clone(),
            iterable,
            body: ops,
            empty: Vec::new(),
        }];
        targets.push(target);
        items = node(LIST, Vec::new(), Some(items));
    }
    spec(
        ops,
        vec![
            ("n".to_owned(), node(SCALAR, Vec::new(), None)),
            ("rows".to_owned(), items),
        ],
        targets,
    )
}

/// `{{ n }}` inside `levels` nested `c-if`s on one flag.
fn nested_ifs(levels: usize) -> PlanSpec {
    let mut ops = vec![OpSpec::Text {
        key: "t".to_owned(),
        expr: path("n", &[]),
    }];
    for level in 0..levels {
        ops = vec![OpSpec::If {
            key: format!("i{level}"),
            branches: vec![(Some(path("flag", &[])), ops)],
        }];
    }
    spec(
        ops,
        vec![
            ("flag".to_owned(), node(TRUTH, Vec::new(), None)),
            ("n".to_owned(), node(SCALAR, Vec::new(), None)),
        ],
        Vec::new(),
    )
}

/// `{{ n if flag else (n if flag else ...) }}` with `levels` conditionals.
fn nested_conditionals(levels: usize) -> PlanSpec {
    let mut expr = path("n", &[]);
    for _ in 0..levels {
        expr = ExprSpec::If {
            test: Box::new(path("flag", &[])),
            body: Box::new(path("n", &[])),
            otherwise: Box::new(expr),
        };
    }
    spec(
        vec![OpSpec::Text {
            key: "t".to_owned(),
            expr,
        }],
        vec![
            ("flag".to_owned(), node(TRUTH, Vec::new(), None)),
            ("n".to_owned(), node(SCALAR, Vec::new(), None)),
        ],
        Vec::new(),
    )
}

/// `{{ a['k']['k']... }}` with `keys` subscripts.
fn deep_path(keys: usize) -> PlanSpec {
    let mut read = node(SCALAR, Vec::new(), None);
    for _ in 0..keys {
        read = node(Kinds::default(), vec![("k".to_owned(), read)], None);
    }
    let subscripts = vec!["k"; keys];
    spec(
        vec![OpSpec::Text {
            key: "t".to_owned(),
            expr: path("a", &subscripts),
        }],
        vec![("a".to_owned(), read)],
        Vec::new(),
    )
}

/// `{{ rN['k']... }}` with `keys` subscripts inside `loops` nested loops.
/// Each loop's item and each subscript add a read level.
fn loops_with_path(loops: usize, keys: usize) -> PlanSpec {
    let mut items = node(SCALAR, Vec::new(), None);
    for _ in 0..keys {
        items = node(Kinds::default(), vec![("k".to_owned(), items)], None);
    }
    let subscripts = vec!["k"; keys];
    let mut ops = vec![OpSpec::Text {
        key: "t".to_owned(),
        expr: path(&format!("r{}", loops - 1), &subscripts),
    }];
    let mut targets = Vec::new();
    for level in (0..loops).rev() {
        let iterable = if level == 0 {
            path("rows", &[])
        } else {
            path(&format!("r{}", level - 1), &[])
        };
        ops = vec![OpSpec::For {
            key: format!("f{level}"),
            target: format!("r{level}"),
            iterable,
            body: ops,
            empty: Vec::new(),
        }];
        targets.push(format!("r{level}"));
        items = node(LIST, Vec::new(), Some(items));
    }
    spec(ops, vec![("rows".to_owned(), items)], targets)
}

fn refused_as_too_deep(spec: &PlanSpec) -> bool {
    match Plan::new(spec) {
        Ok(_) => false,
        Err(error) => {
            assert!(
                error.0.starts_with("too_deep: "),
                "unexpected refusal: {}",
                error.0
            );
            true
        }
    }
}

#[test]
fn nested_loops_plan_up_to_the_body_limit() {
    // The top level is level 1, each loop body adds one, and `{{ n }}`'s
    // expression is one more, so the deepest loop chain is two short.
    let deepest = MAX_BODY_DEPTH - 2;
    assert!(!refused_as_too_deep(&nested_loops(deepest)));
    assert!(refused_as_too_deep(&nested_loops(deepest + 1)));
}

#[test]
fn nested_ifs_plan_up_to_the_body_limit() {
    let deepest = MAX_BODY_DEPTH - 2;
    assert!(!refused_as_too_deep(&nested_ifs(deepest)));
    assert!(refused_as_too_deep(&nested_ifs(deepest + 1)));
}

#[test]
fn conditional_expressions_count_toward_the_body_limit() {
    // `{{ n }}` at the top level is level 2, and each conditional adds one.
    let deepest = MAX_BODY_DEPTH - 2;
    assert!(!refused_as_too_deep(&nested_conditionals(deepest)));
    assert!(refused_as_too_deep(&nested_conditionals(deepest + 1)));
}

#[test]
fn read_paths_plan_up_to_the_read_limit() {
    // The variable is level 1 and each subscript adds one.
    let deepest = MAX_READ_DEPTH - 1;
    assert!(!refused_as_too_deep(&deep_path(deepest)));
    assert!(refused_as_too_deep(&deep_path(deepest + 1)));
}

#[test]
fn loop_items_and_subscripts_both_count_toward_the_read_limit() {
    // `rows` is level 1, each loop's item adds one and each subscript adds
    // one, so three loops leave room for this many subscripts.
    let loops = 3.min(MAX_BODY_DEPTH - 2);
    let deepest = MAX_READ_DEPTH - 1 - loops;
    assert!(!refused_as_too_deep(&loops_with_path(loops, deepest)));
    assert!(refused_as_too_deep(&loops_with_path(loops, deepest + 1)));
}

#[test]
fn a_plan_at_the_limit_writes_its_row() {
    // The deepest accepted loop chain still evaluates: one item per level.
    let loops = MAX_BODY_DEPTH - 2;
    let plan = Plan::new(&nested_loops(loops)).expect("plan at the limit");
    let mut value = Value::Unread;
    for _ in 0..loops {
        value = Value::List {
            len: 1,
            items: vec![value],
        };
    }
    let json = plan
        .write_row(&[Value::Int(7), value], &[])
        .expect("row at the limit");
    assert!(json.contains("\"t\":\"7\""), "{json}");
}
