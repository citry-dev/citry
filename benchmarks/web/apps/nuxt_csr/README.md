# Nuxt CSR canonical project board

This control is derived from the Nuxt 4.5.2 adapter and uses the same Vue
application, Nitro routes, pinned Node.js 22.22.0 runtime, readiness callback,
and project-board semantics. Its only rendering-mode change is
`ssr: false`: the initial document is a client shell, the browser fetches the
same `/api/initial` JSON payload, and the same `$fetch` action path updates the
reactive board.

The adapter is declared as browser-rendered, so initial readiness includes the
shell, local assets, initial JSON request, and Vue's `nextTick` commit. It is a
separate selectable control for isolating Nuxt SSR and hydration work from the
otherwise identical client-rendered path. The page follows the shared
project-board DOM contract at 14, 140 and 1,400 outputs.
