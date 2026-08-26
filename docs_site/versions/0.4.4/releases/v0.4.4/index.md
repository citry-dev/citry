---
title: v0.4.4 (2026-08-26)
url: https://citry.dev/v/0.4.4/releases/v0.4.4/
description: "What changed in citry v0.4.4 (2026-08-26)."
---
# v0.4.4 (2026-08-26)

## Added

- Inspect one registered component or alias with
  `citry --app module:engine inspect component --json`, retaining the versioned
  runtime catalog envelope.
- Inspect authored component dependencies and reverse references with
  `Citry.inspect_component_graph()`, including exact source locations,
  unresolved dynamic or unknown targets, partial-source problems, and
  deterministic versioned JSON.

## Fixed

- A component reintroduced by a fragment regains its class stylesheet after
  all earlier instances leave the page.
- Strict-CSP fragment stylesheets receive the loaded document's nonce.
- A fragment whose accepted CSS or JavaScript fails to load no longer replaces
  the live region or its ownership graph, and Citry removes styles introduced
  only by that failed transaction.