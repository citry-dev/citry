# Changelog

## 0.1.6 - 2026-09-11

- Use Citry LSP 0.1.7 to complete and validate public State bindings and report
  unsupported controls
  ([#99](https://github.com/citry-dev/citry/issues/99)).
- Show and correctly insert JavaScript suggestions inside indented component
  strings.
- Keep JavaScript member completion available when Citry supplies hover or
  navigation for the same name, including `$component` callback data
  ([#113](https://github.com/citry-dev/citry/issues/113)).

## 0.1.3 - 2026-09-09

- Use Citry LSP 0.1.4 with Citry 0.5 projects.


## 0.1.2 - 2026-08-30

- Show native HTML hover information for Alpine `:attribute` bindings while
  preserving Citry's `:c-*` State-binding channel.
- Retrigger handler completion while typing `@c-*` and `:c-*` values, and show
  channel-specific Citry modifier suggestions and hover help.

## 0.1.1 - 2026-08-29

- Configure `citry.envFile` per workspace so app discovery can load dotenv
  values locally or over Remote SSH, refresh when that file changes, and show
  when the selected language server needs an upgrade.

## 0.1.0 - 2026-08-19

- Edit Citry components in place with highlighting for templates, Python
  expressions, HTML, CSS, JavaScript, Alpine, Events, and Fluent.
- Get diagnostics, completion, hover, signatures, symbols, references, and
  navigation from `citry-lsp`, with registry-backed help for components,
  inputs, slots, template/browser/CSS data, events, and i18n.
- Reuse VS Code's HTML, CSS, and JavaScript providers inside parser-proven
  embedded regions while keeping authored source locations intact.
- Format standalone templates or definite `template`, `js`, and `css` regions
  with document, cursor, standard formatter, and Python save-action entry
  points, with readable triple-quoted framing and deterministic embedded
  Prettier fallback.
- Configure each workspace folder independently through `citry.app` and
  `citry.python`, with syntax-only fallback and visible server status.
- Require desktop VS Code 1.101 or newer and a separately installed
  `citry-lsp` 0.1.x, with a clear setup action before an unavailable server is
  started.

## 0.0.1

- Add standalone and inline Citry template highlighting for the initial
  development build.
