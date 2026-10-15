# Reflex canonical project page

This adapter uses Reflex 0.9.10.post2, its compiled React frontend and native
Socket.IO events. Python owns the shared canonical project model; Reflex state
sends its values to the browser, where React commits the rendered elements.
It is a browser-rendered Python UI entry, not a Python HTML renderer.

The production static export and Python backend share
`http://127.0.0.1:8917`. Reflex compiles this absolute API URL into the frontend,
so `adapter.toml` reserves that port. The runner fails if it is occupied.
Uvicorn serves both the exported files and Reflex's ordinary ASGI backend;
no Node process runs during measurement. Python startup skips compilation.
Reflex uses its supported in-memory state manager for this single-process,
nonpersistent scenario; persistence and Redis are separate configurations.

## Build and dependencies

The independent Python 3.12.13 environment installs published wheels from
`uv.lock`. `build.py` prepares Node 22.22.0 and Bun 1.3.14 under this adapter's
generated directories, checks their pinned archive and executable hashes,
and runs the normal production `reflex export` command. The first native
implementation supports macOS ARM64; other platforms fail explicitly until
their toolchain archives are pinned. It does not install global tools.

`frontend/bun.lock` retains the complete browser dependency resolution.
Reflex uses frozen-lockfile mode, and the build fails if its generated
package manifest or lock differs from the checked-in copies. Frontend
compilation and package downloads happen during preparation, before timing.
Generated frontend, toolchain, state and lock directories are excluded from
source copies. The runner records prepared outputs separately.

All browser files are local, including the bundled Socket.IO client and the
licensed Alpine 3.17.2 disclosure asset. Static responses use identity encoding
and `Cache-Control: no-store` in the current diagnostic profile.

Both entry points clear inherited `REFLEX_*` and `__REFLEX_*` settings before
importing the framework, including dotenv selectors and tool overrides. They
select the owned Node/Bun paths and check Reflex's effective configuration and
selected executables. Production launch sets the installed release's internal
compile-skip option; preparation enables compilation. The hostile-environment
regression checks both modes in fresh Python processes.

## Actions and readiness

Native Reflex forms collect their controls on submit. Editing a field sends
no server event. Empty referenced inputs arrive as JSON null in this release;
the adapter normalizes those to the empty strings expected by the shared
model. The server rejects a submitted board session that differs from its
connected Reflex state. Socket.IO retains its normal connection token and
state machinery, and the ASGI wrapper requires a matching browser Origin.

Reflex component functions compose the project shell, five mounted tab bodies,
phase and output expansion panels, notes, comments, roles, bookmarks, output
forms, dependencies and attachments. A local delegated listener switches tabs
without a server event; native `details` elements own panel expansion. The
Outputs tab is initially active.

The component's React effect observes the server-generated revision and
Reflex's completed hydration state. Initial readiness waits for both; an
update waits for React to commit its new revision. The effect then waits for
Alpine's next tick so the independent local disclosure is usable too.
The benchmark oracle checks the actual UI and repeats real native actions.

This component has one synchronous server handler per submitted action and
no application-generated follow-up events. The marker's pending value is
zero under that bounded contract; it is not a generic inspection of Reflex's
private event queue. Asynchronous callbacks, concurrent actions and reconnect
behavior need separate qualification. Instrumentation can affect timings;
semantic snapshot cost is reported separately, while residual event-loop effects
are not calibrated.

The ASGI observer retains raw Socket.IO message references and timestamps.
After the timed boundary, its audit endpoint decodes event packets and
matches operation IDs, revisions and message hashes with browser evidence.
Connection negotiation and hydration packets belong to initial readiness;
uncorrelated later protocol traffic fails the current accounting contract.
Server durations are ASGI message receive-to-send intervals, not an isolated
Python rendering measurement. HTTP timings end at response start.

Correlated state updates also record `prepare_ms`. The duration sums the
adapter's domain snapshot and Reflex-state projection, Reflex's synchronous
state-delta or hydration-dictionary construction, and the configured JSON
serializer used by Socket.IO. Event dispatch, the domain mutation, asynchronous
delta resolution, packet-wrapper construction, protocol framing and socket send
are outside this narrower boundary. Serializer strings are retained by reference
and matched to their connection's outgoing frames after readiness.

## Run locally

```sh
uv sync --frozen --no-build --python 3.12.13
uv run --no-sync python build.py
uv run --no-sync uvicorn app:application --port 8917 \
  --ws-per-message-deflate false
```

Open `/?count=14&session=manual`; 140 outputs exercise the linear 10x cohort,
and the optional 1400-output case exercises the 100x cohort. The fixed origin
is part of this build.

Sources checked on 10 September 2026:
[Reflex release metadata](https://pypi.org/pypi/reflex/0.9.10.post2/json),
[production self-hosting and static export](https://reflex.dev/docs/hosting/self-hosting/),
and the installed Reflex component, form, Socket.IO and hydration sources.
