# Research for the Citry UI component library

This directory contains the evidence behind the official `citry-ui` component
library. The controlling plan is [`../ui_library_plan.md`](../ui_library_plan.md).

## Status

| Phase | Status | Artifact |
|---|---|---|
| 0. Product charter | Ratified on 2026-07-23 | [`product-charter.md`](product-charter.md) |
| 1. Citry baseline | Complete for the 2026-07-23 snapshot | [`citry-baseline.md`](citry-baseline.md) |
| 2. Local prior art | Complete | [`local-prior-art.md`](local-prior-art.md) |
| 3. Breadth scan | Complete; independent gate passed 2026-07-23 | [`candidate-map.md`](candidate-map.md) |
| 4. Deep dives | Complete; independent evidence gate passed 2026-07-23 | [`complaint-register.md`](complaint-register.md) and the twelve `recon-*.md` dossiers |
| 5. Synthesis | Complete; independent synthesis gate passed 2026-07-23 | [`component-taxonomy.md`](component-taxonomy.md), [`customization-patterns.md`](customization-patterns.md), [`citry-fit-matrix.md`](citry-fit-matrix.md) |
| 6. Architecture hypotheses | Complete; fresh maintainer-revision gate passed 2026-07-23 | [`architecture-options.md`](architecture-options.md) |
| Phase 7 entry program | Contract and static adapter comparison complete; interactive readiness next | [`scenario-catalog.md`](scenario-catalog.md) and [`storybook-adapter-exploration.md`](storybook-adapter-exploration.md) |
| 7. Comparative prototype | Not started | `prototype-report.md` |
| 8. Decision and roadmap | Not started | `decision-record.md` |

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
[`scenario catalog`](scenario-catalog.md) and Storybook feasibility comparison
form the transition into Phase 7. Client ambient context is a named readiness
prerequisite before dependent browser and component cases. Localization remains
post-inventory follow-up research.

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
