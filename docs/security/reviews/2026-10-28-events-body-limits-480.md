# Events request body limits (#480)

- **Pull request:** [#480](https://github.com/citry-dev/citry/pull/480),
  merged 2026-10-28 (b86164d60)
- **Reviewer:** a separate reviewing agent, in two rounds
- **Code:** the request readers in Citry's server integrations
  (`contrib/asgi.py`, `contrib/wsgi.py`, `contrib/django.py`) and
  `URLRoute(max_body_bytes=...)`; tests in
  `packages/py/citry/tests/test_events_body_limits.py`

## Who controls the input

Anyone who can reach an app's Events URLs controls the request body: its
size, its `Content-Length` header, whether it is sent in chunks, and how
many form fields it holds. Citry already refused a request over 1 MiB or 16
calls, but only after its ASGI, WSGI or Django integration had read the
whole body. So a large body could use up the server's memory before the
check ran.

## How it was checked

The reviewer ran its own requests against each integration. It also broke
the new limit checks on purpose, to confirm the tests then fail. The new
tests count what each integration pulls from the client, rather than only
checking the answer it sends:

- **ASGI:** a chunked body far over the limit on each Events URL; a
  `Content-Length` smaller than the body; a body at the limit accepted and
  one byte over refused; a message that crosses the limit.
- **WSGI:** a 10 MB `Content-Length` on each Events URL; a chunked body
  without `Content-Length`; a `Content-Length` smaller than the body, which
  Citry reads no further than.
- **Django:** a 10 MB request on each Events URL; a body that middleware
  read first; an upload that middleware parsed first.

## Ruled out

- **Reading far past the limit:**
  - ASGI stops receiving after the message that takes the body past the
    limit, so it holds at most one message more than the limit.
  - WSGI reads at most the limit plus one byte, whatever `Content-Length`
    says.
  - Django reads from the stream and stops at the same point.
  - The WSGI and Django tests read exactly the limit plus one byte from a
    much larger request.
- **Waiting without end on a chunked WSGI body with no length:** Citry
  reads such a body only when the server says the stream ends with the body
  (`wsgi.input_terminated`), and even then stops at the limit plus one
  byte.
- **Django uploads that skip the check:** when middleware has already parsed
  an upload, Citry checks the upload's declared size and refuses it when that
  size is over the limit.
- **Too many form fields:** the new setting
  `extensions_defaults["events"]["_max_form_fields"]` (default 1,000) counts
  fields before parsing. `_max_body_bytes` in the same place sets the 1 MiB
  limit.

## Fixed during the review

Nothing recorded.

## Not tested

- What Django or middleware reads before Citry's own code runs. Citry
  cannot limit that; Django's own upload settings bound it.

## Follow-ups

- GET query strings are not counted as form fields. The server's URL
  length limit bounds them.
- A WSGI URL that sets no limit still reads no chunked body, as before.
