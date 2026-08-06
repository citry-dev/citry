---
title: Why language-agnostic tools matter
description: A shared core can give several language communities the same reliable behavior without forcing them into the same framework.
date: 2026-07-27T09:00:00+02:00
author: Citry maintainers
tags: Project updates, Architecture
---

Citry is a Python frontend framework today, backed by a Rust core. That split is
not an implementation detail we happened to end up with. It reflects a broader
idea: some developer tools become more useful when one carefully tested engine
can serve more than one language community.

This post explains why that direction matters to Citry, what the shared core
already gives us, and where we need to stay disciplined as the project grows.

## Share behavior, not just code

Template engines have to make many small decisions. They parse source, resolve
components, evaluate expressions, merge attributes, track dependencies, and
serialize a final document. If each host-language implementation makes those
decisions independently, subtle differences accumulate.

A shared core gives us one place to define and test the rules. The Python API
can feel natural to Python developers while relying on the same rendering
semantics that another binding could use. A bug fixed in the engine does not
need to be rediscovered in every host language.

That is more than code reuse. It is behavioral reuse. Users get a smaller set
of surprises when examples, diagnostics, and edge cases agree across bindings.

## Keep the host language familiar

Language-agnostic does not mean pretending every language is the same. A useful
binding should respect the conventions of its host language: its types, package
manager, framework integrations, error handling, and editor tools.

Citry's current Python API therefore uses ordinary Python classes and values.
Components can run with Django, FastAPI, and other web servers because rendering
produces a string instead of taking ownership of the application. The
[rendering guide](/concepts/rendering/) follows that path from a component call
to serialized output.

The boundary is deliberate:

- the core owns parsing and rendering rules;
- the binding presents those rules in the language's own idioms;
- framework adapters stay thin and explicit;
- browser behavior uses a documented protocol instead of hidden coupling.

This lets the engine stay consistent without making the surrounding developer
experience generic or awkward.

## A shared core raises the quality bar

Centralizing behavior also concentrates responsibility. A parser used by
several bindings must be conservative about compatibility, precise about
errors, and supported by tests that describe observable behavior rather than
one wrapper's internals.

Citry already benefits from that pressure. The documentation site uses Citry to
render itself, runnable examples exercise the same public APIs readers see, and
the repository checks multiple layers of the output. Those feedback loops make
it harder for the engine, binding, browser runtime, and documentation to drift
quietly.

The tradeoff is coordination. A shared engine can become a bottleneck if its
interfaces change casually or if host-specific needs are forced into a lowest
common denominator. The answer is not to move everything into the core. It is
to keep the core boundary small, version its contracts carefully, and leave
language-specific policy in the binding that understands it.

## What this means today

The practical product today remains the Python package described in the
[documentation](/). You do not need to think about bindings or core boundaries
to build a component. You write HTML-shaped templates, pass them Python data,
and render the result.

The architecture matters because it gives that straightforward API a stable
foundation. It also gives future work a testable question: can a new surface
reuse Citry's behavior while still feeling native to its own community?

That is the standard we want to hold. One reliable implementation should remove
duplicated effort, not erase the strengths of the languages around it.
