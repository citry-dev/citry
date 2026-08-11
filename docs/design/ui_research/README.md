# Research for the Citry UI component library

This directory contains the evidence behind the official `citry-ui` component
library. The controlling plan is [`../ui_library_plan.md`](../ui_library_plan.md).

## Status

| Phase | Status | Artifact |
|---|---|---|
| 0. Product charter | Ratified on 2026-07-23 | [`product-charter.md`](product-charter.md) |
| 1. Citry baseline | Complete; framework and release status refreshed 2026-08-08 | [`citry-baseline.md`](citry-baseline.md) |
| 2. Local prior art | Complete | [`local-prior-art.md`](local-prior-art.md) |
| 3. Breadth scan | Complete; independent gate passed 2026-07-23 | [`candidate-map.md`](candidate-map.md) |
| 4. Deep dives | Complete; independent evidence gate passed 2026-07-23 | [`complaint-register.md`](complaint-register.md) and the twelve `recon-*.md` dossiers |
| 5. Synthesis | Complete; independent synthesis gate passed 2026-07-23 | [`component-taxonomy.md`](component-taxonomy.md), [`customization-patterns.md`](customization-patterns.md), [`citry-fit-matrix.md`](citry-fit-matrix.md) |
| 6. Architecture hypotheses | Complete; fresh maintainer-revision gate passed 2026-07-23 | [`architecture-options.md`](architecture-options.md) |
| Phase 7 readiness | Complete enough to begin specifications; further interactive evidence is part of the slice | [`scenario-catalog.md`](scenario-catalog.md) |
| 7. Production vertical slice | Seven families implemented; human release qualification remains | [`../ui_library_plan.md`](../ui_library_plan.md#phase-7-production-vertical-slice) |
| 8. Decision and roadmap | Provisional inventory and dependency ordering started; final contract decision remains gated | [`../ui_component_inventory.md`](../ui_component_inventory.md) and future `decision-record.md` |

The 2026-08-09 deferred overlay-family refresh is recorded separately in
[`../ui_overlay_foundations.md`](../ui_overlay_foundations.md). It compares the
current platform, Vuetify, React Aria, Radix, Ark/Zag, Floating UI, Mantine,
Material UI, Web Awesome, and Bootstrap, and defines the prototype gates before
Menu, Tooltip, Popover, Drawer, or Toast implementation.

## Evidence rules

- Record the library version and research date for every external claim.
- Distinguish documentation claims, source observations, reproductions, user
  reports, and inference.
- Keep current defects separate from resolved history and preferences.
- Use standards as acceptance baselines, not as scored component libraries.
- Treat the local archives as design history and one application's needs
  evidence. Do not commit extracted files, private data, secrets, or copied
  implementation.
- Run independent adversarial reviews at corpus selection, synthesis, and the
  prototype-backed architecture decision.

Quality and release testing is routed through
[`quality-test-strategy.md`](quality-test-strategy.md). The
[`scenario catalog`](scenario-catalog.md), docs live-component host, and direct
quality tools form the transition into Phase 7. Client ambient context is now
implemented and browser-tested. The post-inventory localization research and
API proposal now lives in [`../i18n.md`](../i18n.md); its prototype gates remain
open.

Storybook is an optional extension, not a Citry UI phase gate. Its controlling
design and moved spike evidence live in
[`../extensions_storybook.md`](../extensions_storybook.md) and
[`../extensions_storybook/`](../extensions_storybook/).

## Phase 4 dossier index

- [Vuetify](recon-vuetify.md)
- [PrimeVue](recon-primevue.md)
- [Reka UI and Nuxt UI](recon-reka-nuxt.md)
- [Ant Design](recon-ant-design.md)
- [Mantine](recon-mantine.md)
- [Chakra UI, Ark UI, and Zag](recon-chakra-ark-zag.md)
- [React Aria Components](recon-react-aria.md)
- [Base UI, shadcn/ui, and Radix lineage](recon-base-shadcn.md)
- [Bootstrap](recon-bootstrap.md)
- [Web Awesome](recon-web-awesome.md)
- [Python component packaging](recon-python-component-packaging.md)
- [django-formset](recon-django-formset.md)
