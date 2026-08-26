---
title: v0.4.2 (2026-08-21)
url: https://citry.dev/v/0.4.4/releases/v0.4.2/
description: "What changed in citry v0.4.2 (2026-08-21)."
---
# v0.4.2 (2026-08-21)

## Added

- Components that declare source messages can translate them without engine
  i18n settings, can name their message language with `I18n.messages_locale`,
  and can use another component's source key through the same engine catalog.
- Browser translations can bind reactive text, attributes, and custom
  destinations through checked `$c-tr` directives and `i18n.bind()` callbacks.

## Performance

- Repeated equal instances of a component declared with `pure = True` can now reuse its side-effect-free body work within one root render.
- Large component trees render faster by batching Alpine analysis in Rust,
  canonicalizing client graphs in Rust, caching stable ownership metadata, and
  avoiding transient attribute and ownership records.
- Repeated large-tree renders avoid redundant attribute-name validation,
  Events dispatch, replacement selection, and ownership-tree traversals.

## Changed

- Rendered ownership comments now use readable eight-character revision aliases while manifests and browser APIs retain complete graph revisions.

## Fixed

- Source-free i18n link units retain the masked punctuation needed to validate
  formatter calls when package catalogs are linked into an application.