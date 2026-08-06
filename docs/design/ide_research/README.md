# Research behind the IDE integration design

Full research and design-panel reports underlying
[`../ide_integration.md`](../ide_integration.md). The design doc carries the
synthesized conclusions; these are the source materials. Produced by
multi-agent research runs on 2026-07-07; every report's web claims were
verified against live sources on that date (access dates in each report's
Sources section), and repo claims cite `file:line`.

Recon (the ground-truth sweeps feeding the design panel):

- [`recon-citry-tooling-surface.md`](recon-citry-tooling-surface.md): what
  citry's parser, AST, and bindings already provide for tooling (exact
  spans, variable tracking, `TagRules`), the gaps for editor use (fail-fast
  parsing, string-flattened errors, the unconditional PyO3 dependency), the
  templates-inside-Python-strings constraint, and the 7-item engine punch
  list.
- [`recon-vue-tooling.md`](recon-vue-tooling.md): the Vetur / Volar /
  JetBrains lineage; virtual code with source maps, takeover mode's
  failure, vue-tsc's internals-patching fragility, web-types, volar.js,
  and the lessons-for-citry distillation.
- [`recon-python-template-tooling.md`](recon-python-template-tooling.md):
  the Django template servers (djlsp, djls), linters and formatters,
  PyCharm's injection APIs, Pylance's closed surface, the second-server
  coexistence pattern (Ruff, Tailwind), highlighting inside Python strings
  today, and django-components' empty baseline.
- [`recon-lsp-architectures.md`](recon-lsp-architectures.md): the four
  server-runtime options with a decision table, the TextMate / tree-sitter
  split of the editor world, semantic-token support per editor, error
  tolerance patterns, and distribution channels per editor.
- [`recon-framework-tooling-field.md`](recon-framework-tooling-field.md):
  nine framework tooling stories (Svelte, Astro, templ, Blade, HEEx,
  Rails/ERB, htmx, Tailwind, django-components) with GitHub maintenance
  statistics; templ's proxy-LSP cost clusters; the cost-ordered ladder of
  rungs.

Design panel (three competing drafts, adversarially judged):

- [`design-A-ship-first.md`](design-A-ship-first.md): the ship-first
  ladder (publish Pygments, VS Code grammars, `citry check`, a thin pygls
  server, editor long tail), optimizing time-to-first-value.
- [`design-B-platform-first.md`](design-B-platform-first.md): the
  end-state platform (a Rust `citry-ls` on the feature-gated parser crate,
  both grammar families, bundled binaries, typed expressions as gated
  milestones), optimizing the destination.
- [`design-C-ecosystem-first.md`](design-C-ecosystem-first.md): the
  coverage-per-effort bet (tree-sitter as canonical artifact, a minimal
  Rust server, thin glue for six-plus editors), with the best-verified
  per-editor distribution mechanics of the three.
- [`judge-1-maintainer-cost.md`](judge-1-maintainer-cost.md),
  [`judge-2-user-experience.md`](judge-2-user-experience.md): the
  adversarial verdicts. Both rank design A first (on maintainer economics
  and on the adopting user's experience respectively); their graft
  recommendations, fact-check tables, and flip conditions shaped the
  synthesis and are recorded as decisions in
  [`../ide_integration.md`](../ide_integration.md) section 11.
