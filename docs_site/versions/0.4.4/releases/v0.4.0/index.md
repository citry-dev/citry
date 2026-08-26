---
title: v0.4.0
url: https://citry.dev/v/0.4.4/releases/v0.4.0/
description: "What changed in citry v0.4.0."
---
# v0.4.0

_Beta release · 18 Aug 2026_

Citry v0.4.0 is the first beta release! 🎉

The Citry API is now mostly stable. There might be occasional bugs and minor API breakages.

## Added

- Configure CSP compatibility, JavaScript delivery, script integrity, and per-response nonces; strict mode ships an Alpine CSP runtime and rejects incompatible output.
- Build server and browser localization with Fluent catalogs, locale fallback, typed `tr()`/`fmt`, `<c-i18n>`, `<c-trans>`, `$i18n`, `$c-tr`, strict localized input, time-zone/DST handling, and coverage/extract/check/compile/inspect commands.
- Analyze Citry, Python, Alpine, JavaScript, CSS, and Fluent in editors through portable catalogs, source maps, diagnostics, completion, hover, and definition lookup.
- Run `citry check --static` or `citry --app module:attribute check` with stable finding codes and deterministic JSON output.
- Run `citry format` on Citry templates and conservatively discovered Python, JavaScript, and CSS assets, with check/diff modes and explicit Biome providers.
- Format definite inline component assets programmatically with `format_python_templates()`, `prepare_python_component_assets()`, `finish_python_component_assets()`, and `format_python_component_assets()`.
- Seed every component Alpine scope directly from `js_data()`; equal wire payloads still produce independent nested state per instance and refresh safely on rerender.
- Supply explicit root context with `render(provides=...)` and pass existing values unchanged with `provide(key, value)`.
- Configure shared and component-specific lint severity/types with `LintSettings` and `Component.Lint`.
- Use `citry.ext.i18n.make_context()`, `citry.Markup`, `citry.SecurityError`, and the typed public `Component.Events` contract.
- Inspect registry-complete component metadata with `Citry.template_analysis()`, portable catalog serialization, declaring-module provenance, and conservative asset ownership fingerprints.

## Changed

- Declared `TemplateData`, `JsData`, and `CssData` schemas now return their normalized defaults and coercions to templates and extensions.
- Inline `template`, `js`, and `css` declarations now remove shared Python indentation; file-backed assets remain byte-exact.
- Tag identity is now explicit: lowercase `c-`, case-insensitive component suffixes and HTML tag/attribute identity, but case-sensitive component inputs, slots, State fields, handlers, and custom events.
- Event modifiers follow dispatched-event capabilities: `.prevent` works for cancelable custom names and `.enter`/`.escape` filter any keyed event.
- `<select multiple>` State values are now `list[str]`, while custom-element State uses the element's typed `value` property in both directions.
- `:c-*` now accepts editable native controls or custom elements only; unsupported/unknown input types fail explicitly and recover safely after live type changes.
- Literal Events bindings are compiled from parser-proven attributes, so binding-shaped text in raw/comment/verbatim bodies stays literal.
- `<c-element>` validates State against its resolved HTML tag and attributes dynamic bindings to the lexical authoring component.
- `#c-key=None` now omits the key for that render; `False`, `0`, and `""` remain keys.
- Browser handler state is callable: `$error.message` becomes `$error()?.message`, with matching `error(name?)` and `loading(name?)` callback accessors.
- `actions.Data` always waits for its caller; `wait=False` now raises `ValueError` and the wire format omits `wait`.

## Fixed

- Component `#c-key` and `#c-ignore` now protect complete comment-delimited component ranges, including multi-root, rootless, transparent, keyed, and moved output.
- HTML `@c-*` bindings now receive non-bubbling native/custom events on their owning element with correct `.stop` and synchronous `$event.currentTarget`.
- Python 3.14 retains typed `TemplateData`/`Kwargs` source and C3-composed schema behavior.
- JavaScript/CSS formatting now handles final newlines, quote/escape variants, CRLF/lone-CR output, bounded streams, timeouts, and Windows cleanup without partial edits.
- Python comments inside `{{ ... }}` no longer consume apostrophes/braces or the host `}}` delimiter.
- `LibraryComponent` now exposes the complete public `Component` type surface in editors and static checkers.