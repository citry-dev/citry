# Next.js canonical project board

This app uses Next.js 16.3.5 with the production App Router and React
19.3.0. The page is
server-rendered from the canonical project model and hydrated by a Client
Component. Mutations call a native Next Server Action; the action returns the
new serialized board to the client and records its operation acknowledgement in
a response cookie consumed by the small custom production server wrapper.

The wrapper uses the pinned Node.js 22.22.0 runtime, adds the benchmark's
`Server-Timing` and no-store headers, and keeps the actual Next request handler
inside the measured Node process tree. No system Node installation is used.
This is a hybrid app: the initial document is server-rendered HTML, while
Server Action updates use Next's RSC/delta protocol. Because the App Router can
stream an RSC/HTML response, its `application`, `render`, and `prepare` spans
are measured to the first response chunk; they are time-to-first-chunk server
boundaries rather than a claim that every streamed byte has been serialized.
The app declares this explicitly as `timing_boundary = "first-chunk"`, and
`summary.json` lists it under `server_prepare_boundaries` so the value is read
as a first-chunk boundary, not full output preparation.
The current build is pinned to macOS ARM64, like the other apps that download
their own Node.js.

The page follows the shared project-board DOM contract at 14, 140 and 1,400
outputs. Initial data is part of the server-rendered document; subsequent
actions use the Server Action protocol and do not make a second initial-data
request.
