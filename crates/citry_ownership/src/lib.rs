//! Relationship calculation, independent of Python and its record objects.

use std::collections::{HashMap, HashSet};

pub type RenderId = usize;
pub type RecordId = u64;

pub struct Call {
    pub id: RecordId,
    pub order: u64,
    pub source: RenderId,
    pub target: Option<RenderId>,
    pub region: Option<RecordId>,
    pub selectors: Vec<RenderId>,
}
pub struct Instance {
    pub order: u64,
    pub id: RenderId,
    pub parent: Option<RenderId>,
    pub active: bool,
}
pub struct Edge {
    pub order: u64,
    pub invocation: RecordId,
    pub parent: RenderId,
    pub child: RenderId,
}
pub struct Fill {
    pub id: RecordId,
    pub order: u64,
    pub owner: Option<RenderId>,
    pub receiver: Option<RenderId>,
}
pub struct Region {
    pub id: RecordId,
    pub order: u64,
    pub fill: RecordId,
    pub receiver: Option<RenderId>,
    pub containing: Option<RecordId>,
    pub captured: bool,
}

#[derive(Default)]
pub struct Graph {
    pub calls: Vec<Call>,
    pub instances: Vec<Instance>,
    pub edges: Vec<Edge>,
    pub fills: Vec<Fill>,
    pub regions: Vec<Region>,
    parent: HashMap<RenderId, RenderId>,
    calls_source: HashMap<RenderId, Vec<usize>>,
    calls_target: HashMap<RenderId, Vec<usize>>,
    calls_region: HashMap<RecordId, Vec<usize>>,
    init_parents: HashMap<RenderId, Vec<RenderId>>,
    regions_receiver: HashMap<RenderId, Vec<usize>>,
    regions_containing: HashMap<RecordId, Vec<usize>>,
    regions_fill: HashMap<RecordId, Vec<usize>>,
    region_index: HashMap<RecordId, usize>,
}

pub struct Selection {
    pub preserved: HashSet<RenderId>,
    pub ancestors: HashSet<RenderId>,
    regions: HashSet<RecordId>,
}

#[derive(Default)]
pub struct Plan {
    // Discovery order is needed to reconstruct Python's queue-set iteration.
    pub calls: Vec<usize>,
    pub instances: Vec<usize>,
    pub edges: Vec<usize>,
    pub fills: Vec<usize>,
    pub regions: Vec<usize>,
    pub fill_promotions: Vec<(usize, RenderId, Option<usize>)>,
    pub region_promotions: Vec<(usize, RenderId)>,
}

impl Graph {
    pub fn index(&mut self) -> Result<(), &'static str> {
        // Historical relationships deliberately participate in ancestry.
        for instance in &self.instances {
            if let Some(parent) = instance.parent {
                self.parent.insert(instance.id, parent);
            }
        }
        let mut ids = HashSet::new();
        for (index, call) in self.calls.iter().enumerate() {
            if !ids.insert(call.id) {
                return Err("duplicate invocation ID");
            }
            self.calls_source
                .entry(call.source)
                .or_default()
                .push(index);
            if let Some(target) = call.target {
                self.calls_target.entry(target).or_default().push(index);
            }
            if let Some(region) = call.region {
                self.calls_region.entry(region).or_default().push(index);
            }
        }
        for edge in &self.edges {
            self.init_parents
                .entry(edge.child)
                .or_default()
                .push(edge.parent);
        }
        ids.clear();
        for fill in &self.fills {
            if !ids.insert(fill.id) {
                return Err("duplicate fill ID");
            }
        }
        for (index, region) in self.regions.iter().enumerate() {
            if self.region_index.insert(region.id, index).is_some() {
                return Err("duplicate region ID");
            }
            self.regions_fill
                .entry(region.fill)
                .or_default()
                .push(index);
            if let Some(receiver) = region.receiver {
                self.regions_receiver
                    .entry(receiver)
                    .or_default()
                    .push(index);
            }
            if let Some(containing) = region.containing {
                self.regions_containing
                    .entry(containing)
                    .or_default()
                    .push(index);
            }
        }
        Ok(())
    }

    fn ancestors(&self, mut closed: HashSet<RenderId>) -> HashSet<RenderId> {
        let mut pending: Vec<_> = closed.iter().copied().collect();
        while let Some(id) = pending.pop() {
            let mut additions = Vec::new();
            if let Some(parent) = self.parent.get(&id) {
                additions.push(*parent);
            }
            for &index in self.calls_target.get(&id).into_iter().flatten() {
                let call = &self.calls[index];
                additions.push(call.source);
                additions.extend(&call.selectors);
            }
            additions.extend(self.init_parents.get(&id).into_iter().flatten());
            for addition in additions {
                if closed.insert(addition) {
                    pending.push(addition);
                }
            }
        }
        closed
    }

    pub fn selection(
        &self,
        owner: RenderId,
        through: u64,
        direct: &HashSet<RenderId>,
        mut regions: HashSet<RecordId>,
    ) -> Selection {
        let mut seeds = direct.clone();
        for id in &regions {
            // Explicit unknown region IDs are optional, as in the reference.
            if let Some(&index) = self.region_index.get(id) {
                let region = &self.regions[index];
                if region.order <= through {
                    seeds.extend(region.receiver);
                }
            }
        }
        let preserved = self.ancestors(seeds);
        for id in &preserved {
            for &index in self.calls_target.get(id).into_iter().flatten() {
                let call = &self.calls[index];
                if call.order <= through {
                    regions.extend(call.region);
                }
            }
        }
        let mut pending: Vec<_> = regions.iter().copied().collect();
        while let Some(id) = pending.pop() {
            if let Some(&index) = self.region_index.get(&id)
                && let Some(parent) = self.regions[index].containing
                && regions.insert(parent)
            {
                pending.push(parent);
            }
        }
        Selection {
            preserved,
            ancestors: self.ancestors(HashSet::from([owner])),
            regions,
        }
    }

    pub fn plan(
        &self,
        owner: RenderId,
        through: u64,
        direct: &HashSet<RenderId>,
        selection: &Selection,
        initial_retired: Vec<RenderId>,
    ) -> Plan {
        let mut walk = Walk {
            graph: self,
            through,
            selection,
            renders: initial_retired.iter().copied().collect(),
            regions: HashSet::new(),
            calls: HashSet::new(),
            discovered: Vec::new(),
            sources: std::iter::once(owner)
                .chain(initial_retired.iter().copied())
                .collect(),
            targets: initial_retired,
            pending_regions: Vec::new(),
        };
        let mut expanded_sources = HashSet::new();
        let mut expanded_targets = HashSet::new();
        let mut expanded_regions = HashSet::new();
        // These three LIFO phases preserve the reference's discovery sequence.
        while !walk.sources.is_empty()
            || !walk.targets.is_empty()
            || !walk.pending_regions.is_empty()
        {
            while let Some(id) = walk.sources.pop() {
                if !expanded_sources.insert(id) {
                    continue;
                }
                for &index in self.regions_receiver.get(&id).into_iter().flatten() {
                    walk.region(index);
                }
                for &index in self.calls_source.get(&id).into_iter().flatten() {
                    walk.call(index);
                }
            }
            while let Some(id) = walk.targets.pop() {
                if !expanded_targets.insert(id) {
                    continue;
                }
                for &index in self.calls_target.get(&id).into_iter().flatten() {
                    walk.call(index);
                }
            }
            while let Some(id) = walk.pending_regions.pop() {
                if !expanded_regions.insert(id) {
                    continue;
                }
                for &index in self.regions_containing.get(&id).into_iter().flatten() {
                    walk.region(index);
                }
                for &index in self.calls_region.get(&id).into_iter().flatten() {
                    walk.call(index);
                }
            }
        }
        let mut plan = Plan {
            calls: walk.discovered,
            ..Plan::default()
        };
        let mut active = HashMap::new();
        for (index, instance) in self.instances.iter().enumerate() {
            if instance.order <= through && walk.renders.contains(&instance.id) {
                plan.instances.push(index);
            } else if instance.active {
                // Duplicate render IDs have the reference's last-active-row behavior.
                active.insert(instance.id, index);
            }
        }
        for (index, edge) in self.edges.iter().enumerate() {
            if edge.order <= through
                && (walk.calls.contains(&edge.invocation) || walk.renders.contains(&edge.child))
            {
                plan.edges.push(index);
            }
        }
        let mut retired_fills = HashSet::new();
        for (index, fill) in self.fills.iter().enumerate() {
            if fill.order > through {
                continue;
            }
            let regions = self
                .regions_fill
                .get(&fill.id)
                .map_or(&[][..], Vec::as_slice);
            let selected: Vec<_> = regions
                .iter()
                .copied()
                .filter(|&i| self.regions[i].order > through && self.regions[i].captured)
                .collect();
            let preserved = regions
                .iter()
                .any(|&i| selection.regions.contains(&self.regions[i].id));
            if !selected.is_empty() {
                // Receiver eligibility is evaluated after planned instance retirement.
                let receiver = fill
                    .receiver
                    .filter(|id| active.contains_key(id))
                    .or_else(|| {
                        selected.iter().find_map(|&i| {
                            self.regions[i]
                                .receiver
                                .filter(|id| active.contains_key(id))
                        })
                    })
                    .unwrap_or(owner);
                plan.fill_promotions
                    .push((index, receiver, active.get(&receiver).copied()));
                for i in selected {
                    if !self.regions[i]
                        .receiver
                        .is_some_and(|id| active.contains_key(&id))
                    {
                        plan.region_promotions.push((i, receiver));
                    }
                }
                continue;
            }
            if preserved
                || (regions.is_empty() && fill.receiver.is_some_and(|id| direct.contains(&id)))
            {
                continue;
            }
            if fill.owner == Some(owner)
                || fill.owner.is_some_and(|id| walk.renders.contains(&id))
                || fill.receiver.is_some_and(|id| walk.renders.contains(&id))
            {
                retired_fills.insert(fill.id);
                plan.fills.push(index);
            }
        }
        for (index, region) in self.regions.iter().enumerate() {
            if region.order <= through
                && (walk.regions.contains(&region.id) || retired_fills.contains(&region.fill))
            {
                plan.regions.push(index);
            }
        }
        plan
    }
}

struct Walk<'a> {
    graph: &'a Graph,
    through: u64,
    selection: &'a Selection,
    renders: HashSet<RenderId>,
    regions: HashSet<RecordId>,
    calls: HashSet<RecordId>,
    discovered: Vec<usize>,
    sources: Vec<RenderId>,
    targets: Vec<RenderId>,
    pending_regions: Vec<RecordId>,
}
impl Walk<'_> {
    fn region(&mut self, index: usize) {
        let region = &self.graph.regions[index];
        if self.selection.regions.contains(&region.id) || region.order > self.through {
            return;
        }
        if self.regions.insert(region.id) {
            self.pending_regions.push(region.id);
        }
    }
    fn call(&mut self, index: usize) {
        let call = &self.graph.calls[index];
        if call.order > self.through
            || call
                .target
                .is_some_and(|id| self.selection.preserved.contains(&id))
        {
            return;
        }
        if self.calls.insert(call.id) {
            self.discovered.push(index);
            if let Some(target) = call.target
                && self.renders.insert(target)
            {
                self.sources.push(target);
                self.targets.push(target);
            }
        }
    }
}
