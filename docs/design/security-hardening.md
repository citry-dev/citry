# Security hardening audit

**Status (2026-07-24): placeholder and audit reminder. The project-wide audit
has not started. This document does not claim that unlisted surfaces are safe
or that listed controls are complete.**

Citry moves Python values and authored source through several parsers,
serializers, caches, HTTP routes, and browser runtimes. Local fixes are not a
substitute for reviewing those boundaries as one security model. This document
holds the scope and evidence requirements for that later hardening pass.

The first finding that prompted this placeholder was CSS-data stylesheet
injection. That class is fixed and regression-tested, but similar contextual
serialization mistakes must be searched for across the entire project.

---

## 1. Prior art and current control points

The audit starts from implementation, tests, and external security standards.
The following files are initial routing pointers, not endorsements:

- Template parsing, source positions, and compiler contracts:
  [`crates/citry_template_parser/src/`](../../crates/citry_template_parser/src/).
- Sandboxed expression evaluation:
  [`packages/py/citry_core/citry_core/safe_eval/`](../../packages/py/citry_core/citry_core/safe_eval/)
  and its tests.
- HTML attribute and render serialization:
  [`attrs.py`](../../packages/py/citry/citry/attrs.py),
  [`serialize.py`](../../packages/py/citry/citry/serialize.py), and
  [`citry_render.py`](../../packages/py/citry/citry/citry_render.py).
- Inline script/style construction and closing-tag rejection:
  [`ext/dependencies/types.py`](../../packages/py/citry/citry/ext/dependencies/types.py).
- JS/CSS data hashing, caching, and emission:
  [`ext/dependencies/scripts.py`](../../packages/py/citry/citry/ext/dependencies/scripts.py),
  [`ext/dependencies/emission.py`](../../packages/py/citry/citry/ext/dependencies/emission.py),
  and [`util/css.py`](../../packages/py/citry/citry/util/css.py).
- Dependency and event HTTP endpoints:
  [`ext/dependencies/routes.py`](../../packages/py/citry/citry/ext/dependencies/routes.py)
  and [`ext/events/routes.py`](../../packages/py/citry/citry/ext/events/routes.py).
- Event tokens, request decoding, dispatch, and browser transport:
  [`ext/events/tokens.py`](../../packages/py/citry/citry/ext/events/tokens.py),
  [`ext/events/dispatcher.py`](../../packages/py/citry/citry/ext/events/dispatcher.py),
  and [`ext/events/client/`](../../packages/py/citry/citry/ext/events/client/).
- Cache artifact encoding, validation, and replay:
  [`ext/cache/artifact.py`](../../packages/py/citry/citry/ext/cache/artifact.py)
  and [`ext/cache/replay.py`](../../packages/py/citry/citry/ext/cache/replay.py).
- Asset resolution and filesystem access:
  [`assets.py`](../../packages/py/citry/citry/assets.py).
- Extension trust and mutable lifecycle contexts:
  [`extension.py`](../../packages/py/citry/citry/extension.py).
- Debug and introspection output:
  [`ext/debug.py`](../../packages/py/citry/citry/ext/debug.py),
  [`introspection.py`](../../packages/py/citry/citry/introspection.py), and the
  inspect/command surfaces.

Existing tests around these files are part of the evidence corpus. The audit
must also consult the relevant OWASP cheat sheets, browser specifications,
Python security guidance, and dependency advisories current at audit time.

---

## 2. Threat model to write first

The hardening work begins by classifying actors and trust levels:

- component-library author;
- application developer;
- extension author;
- template or asset author;
- application user supplying ordinary data;
- authenticated and unauthenticated HTTP clients;
- cache or artifact storage operator;
- compromised dependency or build input;
- host application embedding Citry output;
- browser runtime, including CSP and third-party scripts.

For each boundary, record which inputs are trusted code, trusted configuration,
untrusted data, signed data, or opaque external content. Security diagnostics
must not imply that an extension or component source is sandboxed when it is
intentionally trusted Python code.

---

## 3. Audit workstreams

| Workstream | Questions and attack classes | Required evidence |
|---|---|---|
| Contextual output encoding | HTML text, attributes, URLs, inline JSON, JS, CSS, comments, raw/safe-string escape hatches, closing tags, double encoding | Sink inventory, adversarial corpus, unit and browser tests |
| Template and expression sandbox | Attribute access, calls, dunder reachability, object capabilities, resource exhaustion, parser/compiler disagreement | Rust/Python cross-binding tests, sandbox escape review, fuzzing |
| JS/CSS data transport | Key validation, scalar/type contracts, serialization ambiguity, script/style breakout, client reconstruction | Fresh render, inline, URL, fragment, and cache-replay tests |
| HTTP and Events | Authentication, authorization, CSRF, replay, signature scope, expiry, method/content type, origin, request size, concurrency | Route matrix, threat cases, integration tests |
| Files and URLs | Path traversal, symlinks, search roots, URL schemes, redirects, content types, cache headers | Filesystem harnesses and route tests |
| Cache and artifacts | Untrusted backend data, tampering, cross-version replay, type confusion, decompression/size bombs, partial mutation | Canonical encoding tests, rejection atomicity, size/depth limits |
| Extension system | Trust declaration, hook mutation, source transforms, effect contracts, exception isolation, ordering | Hook capability matrix and malicious-extension harnesses |
| Autodiscovery/imports | Import side effects, path confusion, duplicate names, package boundaries | Discovery corpus and explicit trust documentation |
| Browser runtime | DOM injection, event payload handling, prototype pollution, selector construction, CSP, nonces, cleanup and replay | TypeScript review, browser tests, dependency scan |
| Observability | Secrets and user data in errors, traces, debug output, manifests, logs, source snippets | Redaction policy and snapshot tests |
| Availability | Deep trees, large templates, recursive slots, oversized payloads, regex behavior, cache amplification, event floods | Benchmarks, explicit limits, timeout and memory tests |
| Supply chain and release | Locked dependencies, generated assets, provenance, package contents, vulnerability response | SBOM/advisory process and release checks |

The audit must sweep for the whole vulnerability class after every confirmed
finding. A fix at one sink is incomplete until sibling sinks and replay paths
are classified.

---

## 4. Proposed audit sequence

1. Freeze the threat model, supported deployment assumptions, and trust
   vocabulary.
2. Build a source-to-sink inventory for HTML, JSON, JS, CSS, URLs, files,
   caches, and HTTP responses.
3. Audit contextual encoding and serialization first because one Python value
   may cross several output contexts.
4. Audit sandbox and parser/compiler boundaries with fuzzers and differential
   tests.
5. Audit Events and all HTTP routes, including authorization and replay.
6. Audit filesystem, caches, artifact replay, and cross-worker behavior.
7. Audit extension capabilities, debugging output, and operational defaults.
8. Run independent security review, resolve or explicitly accept findings,
   and publish the supported security model and reporting process.

Each stage should produce a small ledger with the source, transformations,
sink, trust level, existing controls, bypass attempts, tests, severity, and
owner. Findings that need embargoed handling should move to the project's
private security-reporting process rather than remain in this public file.

---

## 5. Acceptance floor

The audit is complete only when:

- every externally reachable route and every contextual serializer is in the
  ledger;
- raw-output escape hatches are explicit, named, and documented as trusted;
- all confirmed classes have sibling sweeps and regression tests;
- cache replay and alternate emission strategies enforce the same validation;
- size, depth, recursion, and concurrency assumptions are explicit;
- parser, compiler, PyO3, Python, and browser contracts agree where data
  crosses them;
- clean and tampered artifacts fail atomically without partial state changes;
- production defaults for debug output, CSP integration, secrets, and error
  detail are documented;
- dependency scanning and vulnerability-response ownership are defined;
- an independent reviewer has challenged both the threat model and the fixes.

---

## 6. Landed finding: CSS-data containment

The initial CSS-data issue came from interpolating mapping keys directly into
custom-property names and placing values into declaration text without
structural validation or complete string escaping.

The landed containment contract is:

- keys are non-empty custom-property suffixes containing ASCII letters,
  digits, `-`, `_`, or non-ASCII identifier characters;
- values are strings, integers, finite JSON-compatible floats, or `None`;
- booleans and structured JSON values are rejected rather than converted with
  Python `str()` representations;
- Citry-quoted strings follow CSSOM-style escaping;
- raw strings cannot contain an HTML style end tag, a top-level semicolon,
  unmatched blocks or quotes, unclosed comments, nulls, or Unicode surrogates;
- the cache-artifact reconstruction path re-runs the same validation.

This prevents stylesheet and HTML-context breakout. It is not full CSS grammar
validation and does not prove that a value is meaningful for the property that
eventually consumes `var(--name)`. That later work remains C1 in
[`early_validation_plan.md`](early_validation_plan.md).
