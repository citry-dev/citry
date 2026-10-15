# Citry project board

This application uses Citry 0.5.0's typed server events, signed component state,
HTML rendering and normal browser update path. The `Board` event component owns
the forms and nests layout, provider, tab, detail, phase and output components.
The page shell owns an independent Alpine disclosure. It uses
the published wheel, with no local runtime patches or transport replacements.

Citry serves its manager, bundled Alpine and event runtime from local mounted
routes. The shared scenario serves the stylesheet; `assets/readiness.js`
observes lifecycle events. No navigation requires a CDN.

At the 14-output workload, the browser component graph contains 29 component
instances and 7 native fill records: one Page, Board, ProjectLayout, Layout,
provider, ProjectTabs and ProjectInfo, plus 3 note panels, 5 phase groups and
14 keyed outputs. The fixed shell has five mounted tab panels and five open
phase groups. The 14/140/1400 output sizes replicate the canonical nested
cohorts to 4/40/400 notes, 8/80/800 comments, 2/20/200 roles, 1/10/100
bookmarks, 1/10/100 attachments and 2/20/200 dependencies.

Install the exact dependencies with `uv sync --frozen --python 3.12` from this
directory, then launch with the command in `adapter.toml`. Open
`/?count=14&session=manual`. The benchmark runner supplies unique hidden operation IDs; manual actions
use the default `manual` ID.

See the shared scenario README for action semantics, readiness and limits.

## Server HTML render timing

The render span covers `CitryElement.render` plus `CitryRender.serialize` and
`serialize_result`, counting nested calls once. It includes component template-data callbacks,
ownership/dependency processing and HTML serialization.

A request-scoped `Server-Timing: render` metric reports the sum of these spans. It excludes
action mutation, CSRF checks, network transfer and browser work. Static responses and failed
responses have no render metric. The existing `application` metric remains a broader, separate
measurement. These hooks are benchmark instrumentation against the pinned release, not
framework changes.
