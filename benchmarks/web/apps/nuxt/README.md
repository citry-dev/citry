# Nuxt canonical project board

This app uses Nuxt 4.5.2 with Vue 3.5.42 in universal SSR mode. The initial board is
loaded through Nuxt's SSR-friendly `useFetch`; its payload is hydrated into the
client without a second initial-data request. Subsequent mutations use a native
Nitro server API and `$fetch`, then update the reactive Vue state.

The app uses the pinned Node.js 22.22.0 runtime, records application and
acknowledgement timing through Nitro headers, and does not depend on system
Node. It is a hybrid app: the initial document is SSR HTML, while actions
use a JSON response from a native Nitro API. The current native toolchain pin
supports macOS ARM64. The page follows the shared project-board DOM contract at
14, 140 and 1,400 outputs.
