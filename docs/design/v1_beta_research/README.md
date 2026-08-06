# Citry v1 beta research

**Status (2026-07-23): Stages 0 and 1 complete; Stage 2 bounded pilot complete
and circuit breaker awaiting a maintainer scope decision; Stage 1 decisions
remain open for final resolution in Stage 10.**

This directory is the canonical home for sanitized artifacts produced by the
research charter in
[`v1_beta_launch_plan.md`](../v1_beta_launch_plan.md). The charter remains the
index and decision framework; findings belong here rather than accumulating in
that document.

Planned artifacts include the evidence log, working-tree change ledger, design
closure register, package and contract matrix, script/tooling register,
metadata/configuration register, technical-readiness dossier, live-project and
`demo/` acceptance plan, documentation/public-surface audit, GitHub audit,
benchmark charter, ecosystem/outreach report, and the resulting execution plan.

Artifacts are created only when their research stage begins. Potentially
exploitable findings, credentials, owner-only settings exports, proprietary
application data, and identifying cohort data must not be stored here; follow
the sensitive-evidence rules in the charter.

## Stage 0 artifacts

- [`evidence_log.md`](evidence_log.md): baseline identity, toolchain, commands,
  exclusions, movement, and verification evidence.
- [`change_ledger.tsv`](change_ledger.tsv): complete B0 dirty-path inventory
  with provisional path classifications.
- [`baseline_history.tsv`](baseline_history.tsv): timestamped baseline counts.
- [`baseline_delta.tsv`](baseline_delta.tsv): path/status movement after B0.
- [`review_baseline_fingerprints.tsv`](review_baseline_fingerprints.tsv):
  staging-aware content, index, and HEAD identities at the review cutoff.
- [`manifest_inventory.tsv`](manifest_inventory.tsv): first-party and vendored
  manifest/toolchain inventory.
- [`workflow_inventory.tsv`](workflow_inventory.tsv): working-tree workflows.
- [`design_artifact_inventory.tsv`](design_artifact_inventory.tsv): recursive
  B0 design/research inventory, including the tracked deletion state.
- [`public_service_snapshot.md`](public_service_snapshot.md): GitHub, PyPI, and
  documentation-domain observations.

## Stage 1 artifacts

- [`stage1_baseline.md`](stage1_baseline.md): moving-baseline identity and
  relation to the Stage 0 review cutoff.
- [`stage1_baseline_fingerprints.tsv`](stage1_baseline_fingerprints.tsv):
  staging-aware content, index, and HEAD identities at Stage 1 start.
- [`stage1_baseline_delta.tsv`](stage1_baseline_delta.tsv): path, status,
  worktree-content, index, and HEAD movement since the Stage 0 review cutoff.
- [`stage1_internal_contract.md`](stage1_internal_contract.md): current product,
  package, support, security, and contradiction evidence.
- [`stage1_external_norms.md`](stage1_external_norms.md): bounded standards and
  comparison-project policy research.
- [`product_beta_charter.md`](product_beta_charter.md): proposed product and beta
  hypotheses and the open Stage 10 decision register.

## Stage 2 pilot artifacts

- [`stage2_baseline.md`](stage2_baseline.md): moving-baseline identity and
  opening verification state.
- [`stage2_baseline_fingerprints.tsv`](stage2_baseline_fingerprints.tsv):
  staging-aware working-tree, index, and HEAD identities at pilot start.
- [`stage2_baseline_delta.tsv`](stage2_baseline_delta.tsv): content and path-set
  movement since B1.
- [`stage2_pilot_close_delta.tsv`](stage2_pilot_close_delta.tsv): four pilot
  inputs that moved after B2, their close hashes, and revalidation impact.
- [`stage2_change_graph_pilot.md`](stage2_change_graph_pilot.md): bounded
  `actions.ReplaceUrl` trace, focused verification, expansion estimate, and
  circuit-breaker decision.
- [`stage2_pilot_nodes.tsv`](stage2_pilot_nodes.tsv): the pilot's file and
  contract nodes.
- [`stage2_pilot_edges.tsv`](stage2_pilot_edges.tsv): observed, verified, and
  missing relationships between those nodes.

## Focused implementation baselines

- [`protocol_runtime_ownership_baseline.md`](protocol_runtime_ownership_baseline.md):
  moving, scope-limited evidence for the executable protocol ownership work in
  GitHub issue #39.
- [`protocol_runtime_stage1.md`](protocol_runtime_stage1.md): bounded schema
  inventory, explicit conformance-case foundation, commands, and opening
  coverage for issue #39.
- [`protocol_runtime_stage2.md`](protocol_runtime_stage2.md): Events Python
  runtime ownership, shipped-copy rules, focused compatibility evidence, and
  work held for the cross-language stage.
- [`protocol_runtime_stage3.md`](protocol_runtime_stage3.md): Events JavaScript
  runtime ownership, browser boundary migration, focused compatibility
  evidence, and the approved moving payload guard.
- [`protocol_runtime_stage4.md`](protocol_runtime_stage4.md): client-graph
  Python runtime ownership, server-writer migration, focused compatibility and
  Chromium evidence, and the bounded performance comparison.
- [`protocol_runtime_stage5.md`](protocol_runtime_stage5.md): client-graph
  JavaScript runtime ownership, generated core boundary, shared browser issue
  checks, DOM-only product boundary, and the approved payload guard.
- [`protocol_runtime_stage6.md`](protocol_runtime_stage6.md): complete schema
  constraint ownership, producer/consumer audit, distribution proof,
  cross-browser and performance evidence, release ordering, and the current
  repository-gate blockers.
- [`protocol_mutation_coverage_exploration.md`](protocol_mutation_coverage_exploration.md):
  bounded evaluation of issue #54's proposed exhaustive mutation expansion and
  the recommended change-driven coverage policy.
