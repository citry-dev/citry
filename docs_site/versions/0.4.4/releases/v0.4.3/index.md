---
title: v0.4.3 (2026-08-22)
url: https://citry.dev/v/0.4.4/releases/v0.4.3/
description: "What changed in citry v0.4.3 (2026-08-22)."
---
# v0.4.3 (2026-08-22)

## Added

- Template-engine adapters can declare provider-owned UTF-8 source spans,
  resolve them through owner-dispatched compile hooks, and render protected
  compiled bodies without using Citry's private render functions.
- `Citry.render_template()` renders standalone Citry source with variables,
  slots, globals, provides, source origins, and provider compile contexts
  through a bounded per-engine cache.

## Changed

- App-aware `citry check` treats extension-owned template ranges as unknown
  source and avoids unresolved-variable findings when a host range may
  introduce body bindings.
- Host-selected Citry segments remain structured until the enclosing render is
  serialized, preserving page-wide dependencies, ownership, events, and CSP
  processing.