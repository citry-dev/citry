# Django, HTMX and Alpine project board

Django renders the initial page and each updated board fragment. HTMX submits
ordinary forms, replaces the board with `outerHTML` and uses its default settle
delay. Alpine owns the independent local disclosure. Both initial and updated
forms include Django CSRF tokens.

The page and board templates decompose the canonical shell, project detail,
three note panels, five phase groups and repeated output partial structure. At
14 outputs this renders five mounted tab panels, five open phase groups, 4
notes, 8 comments, 2 roles, 1 bookmark, 1 attachment and 2 dependencies. The
140/1400 output sizes replicate those nested cohorts by 10x/100x while keeping
one shell and five groups.

HTMX 2.0.10 and Alpine 3.17.2 are vendored under `assets/`, with upstream URLs,
package integrity and individual file hashes in `assets/sources.json`. Their
license files are retained. All browser requests stay on the local app origin.
The application follows the official
[HTMX form and swap model](https://htmx.org/docs/) and
[Alpine installation instructions](https://alpinejs.dev/essentials/installation).
Package versions were checked on 2026-09-10 and are pinned for this application.

Install the exact dependencies with `uv sync --frozen --python 3.12` from this
directory, then launch with the command in `adapter.toml`. Open
`/?count=14&session=manual`. The benchmark runner supplies unique hidden operation IDs; manual actions
use the default `manual` ID.

See the shared scenario README for action semantics, readiness and limits.

## Server HTML render timing

The render span covers `django.template.Template.render`, counting nested templates once. The
board snapshot is prepared before this boundary and is excluded.

A request-scoped `Server-Timing: render` metric reports the sum of these spans. It excludes
action mutation, CSRF checks, network transfer and browser work. Static responses and failed
responses have no render metric. The existing `application` metric remains a broader, separate
measurement. These hooks are benchmark instrumentation against the pinned release, not
framework changes.
