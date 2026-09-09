//! Check decisions that can discard selected output or its later slot placement.

use std::collections::HashSet;

use citry_ownership::{Call, Edge, Fill, Graph, Instance, Region};

fn call(id: u64, order: u64, source: usize, target: usize) -> Call {
    Call {
        id,
        order,
        source,
        target: Some(target),
        region: None,
        selectors: Vec::new(),
    }
}

fn instance(id: usize, parent: Option<usize>) -> Instance {
    Instance {
        id,
        parent,
        order: 1,
        active: true,
    }
}

#[test]
fn selected_descendants_keep_ancestry_while_cutoff_protects_later_calls() {
    let mut graph = Graph::default();
    graph.instances = vec![
        instance(0, None),
        instance(1, Some(0)),
        instance(2, Some(1)),
        instance(3, Some(0)),
        instance(4, Some(0)),
    ];
    graph.calls = vec![
        call(100, 2, 0, 1),
        call(200, 3, 1, 2),
        call(300, 4, 0, 3),
        call(400, 11, 0, 4),
    ];
    graph.edges = vec![Edge {
        order: 5,
        invocation: 300,
        parent: 0,
        child: 3,
    }];
    graph.index().unwrap();
    let direct = HashSet::from([2]);
    let selection = graph.selection(0, 10, &direct, HashSet::new());
    assert_eq!(selection.preserved, HashSet::from([0, 1, 2]));
    let plan = graph.plan(0, 10, &direct, &selection, Vec::new());
    assert_eq!(plan.calls, vec![2]);
    assert_eq!(plan.instances, vec![3]);
    assert_eq!(plan.edges, vec![0]);
}

#[test]
fn explicit_nested_region_preserves_its_containing_placement() {
    let mut graph = Graph::default();
    graph.instances = vec![instance(0, None), instance(1, Some(0))];
    graph.calls = vec![call(100, 2, 0, 1)];
    graph.fills = vec![Fill {
        id: 10,
        order: 3,
        owner: Some(0),
        receiver: Some(1),
    }];
    graph.regions = vec![
        Region {
            id: 20,
            order: 4,
            fill: 10,
            receiver: Some(1),
            containing: None,
            captured: true,
        },
        Region {
            id: 30,
            order: 5,
            fill: 10,
            receiver: Some(1),
            containing: Some(20),
            captured: true,
        },
    ];
    graph.index().unwrap();
    let direct = HashSet::new();
    // An unknown explicit region must not prevent selection of a known one.
    let selection = graph.selection(0, 10, &direct, HashSet::from([30, 999]));
    let plan = graph.plan(0, 10, &direct, &selection, Vec::new());
    assert!(plan.calls.is_empty());
    assert!(plan.instances.is_empty());
    assert!(plan.fills.is_empty());
    assert!(plan.regions.is_empty());
}

#[test]
fn later_fill_placement_moves_to_surviving_owner_when_receiver_retires() {
    let mut graph = Graph::default();
    graph.instances = vec![instance(0, None), instance(1, Some(0))];
    graph.calls = vec![call(100, 2, 0, 1)];
    graph.fills = vec![Fill {
        id: 10,
        order: 3,
        owner: Some(0),
        receiver: Some(1),
    }];
    graph.regions = vec![
        Region {
            id: 20,
            order: 4,
            fill: 10,
            receiver: Some(1),
            containing: None,
            captured: true,
        },
        Region {
            id: 30,
            order: 11,
            fill: 10,
            receiver: Some(1),
            containing: None,
            captured: true,
        },
    ];
    graph.index().unwrap();
    let direct = HashSet::new();
    let selection = graph.selection(0, 10, &direct, HashSet::new());
    let plan = graph.plan(0, 10, &direct, &selection, Vec::new());
    assert_eq!(plan.calls, vec![0]);
    assert_eq!(plan.instances, vec![1]);
    assert!(plan.fills.is_empty());
    assert_eq!(plan.regions, vec![0]);
    assert_eq!(plan.fill_promotions, vec![(0, 0, Some(0))]);
    assert_eq!(plan.region_promotions, vec![(1, 0)]);
}

#[test]
fn cyclic_ancestry_terminates_and_includes_selectors_and_initialization() {
    let mut graph = Graph::default();
    graph.instances = vec![instance(0, Some(1)), instance(1, Some(0))];
    let mut invocation = call(100, 2, 2, 1);
    invocation.selectors = vec![3];
    graph.calls.push(invocation);
    graph.edges.push(Edge {
        order: 3,
        invocation: 100,
        parent: 4,
        child: 1,
    });
    graph.index().unwrap();
    let direct = HashSet::from([1]);
    let selection = graph.selection(0, 10, &direct, HashSet::new());
    assert_eq!(selection.preserved, HashSet::from([0, 1, 2, 3, 4]));
    assert_eq!(selection.ancestors, selection.preserved);
}

#[test]
fn duplicate_record_identifiers_reject_indexing() {
    let mut graph = Graph::default();
    graph.calls = vec![call(100, 2, 0, 1), call(100, 3, 0, 2)];
    assert_eq!(graph.index(), Err("duplicate invocation ID"));

    let mut graph = Graph::default();
    graph.fills = (0..2)
        .map(|_| Fill {
            id: 10,
            order: 3,
            owner: None,
            receiver: None,
        })
        .collect();
    assert_eq!(graph.index(), Err("duplicate fill ID"));

    let mut graph = Graph::default();
    graph.regions = (0..2)
        .map(|_| Region {
            id: 20,
            order: 4,
            fill: 10,
            receiver: None,
            containing: None,
            captured: true,
        })
        .collect();
    assert_eq!(graph.index(), Err("duplicate region ID"));
}
