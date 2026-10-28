# Security review records

Some changes alter how a value reaches the browser, or how Citry's server
reads a request that anyone can send. Before such a change merges, a
separate reviewer checks its security, as the security pass in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser)
asks (Mechanism 7; `CLAUDE.md` holds the working rules for contributors and
for the AI agents that work on Citry). The reviewer is usually an AI agent
other than the one that wrote the change. It lists every way the new input
can reach the page or the server, and tries to defeat each check.

This folder keeps a short public record of each such review that found no
security hole still open when the change merged, so anyone can see what
was checked, how, and what was left untested.

## When to write a record

Write a record for every such review that finds no open hole. Add it once
the change has merged, so the record can name the merge date and commit.

A problem that the review finds and the pull request fixes before it merges
never reached a release. List it under "Fixed during the review".

A hole in a released version is different. It stays private until its fix
ships, as [`SECURITY.md`](../../../SECURITY.md) describes, and it gets no
record here until the fix is released and the problem is disclosed. Date
that record by the disclosure, and add it in its own pull request.

## What a record says

A record says what was checked, never how to exploit anything. Name the
kinds of input that were tried, such as "values that name another host" or
"quote and script-tag breakouts", not working attack strings. Leave out any
detail that would help someone attack an older release.

Name each file `YYYY-MM-DD-<short-topic>-<PR number>.md`, using the date the
pull request merged.

## Template

```markdown
# <What was reviewed, in a few words> (#<PR>)

- **Pull request:** [#<PR>](https://github.com/citry-dev/citry/pull/<PR>),
  merged <YYYY-MM-DD> (<commit>)
- **Reviewer:** <who checked it, for example "a separate reviewing
  agent">
- **Code:** <the files or functions that handle the new input, and the
  test files>

## Who controls the input

<Who supplies which input: the template author, the app's Python code,
or anyone who can send a request. Then what is at risk: what the browser
does with it (shows it as text, parses it as markup, applies it as CSS,
runs it, or navigates to it), or what it costs the server.>

## How it was checked

<A code read, a real browser, which servers and versions, how many
inputs and of what kind, and every way each one was sent to the page or
the server.>

## Ruled out

<Each risk that was checked, and why it does not happen. When the app
author's own setup decides the risk, say so and say what the docs tell
them.>

## Fixed during the review

<Problems the review found that the pull request fixed before it
merged. Write "Nothing recorded." if the review records none.>

## Not tested

<Servers, browsers, versions, or setups the review did not cover. Write
"Nothing." only if that is true.>

## Follow-ups

<Open issues and documented limits, with links. Write "None." if there
are none.>
```
