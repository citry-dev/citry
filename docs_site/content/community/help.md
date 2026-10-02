---
title: Getting help
description: Where to ask questions about Citry, how to search before posting, and where to report bugs and security issues.
---

# Getting help

You have a question about Citry, or hit something that looks like a bug.
Questions and bug reports both go to the GitHub repository at
[{{ repo_full_name }}]({{ repo_url }}){: target="_blank" rel="noopener"}.
This page shows where to post and what to include.

## Search first { #search-before-you-post }

Someone may have hit the same thing already. Before you post, search:

- The
  [existing issues and discussions]({{ repo_issues_url }}?q=){: target="_blank" rel="noopener"}
  for your question or the exact error message.
- This documentation, with the [search](/community/help/?q=help) at the top
  of the page.

## Ask a question

If you cannot find an answer,
[open a new issue]({{ repo_issues_url }}/new){: target="_blank" rel="noopener"}.
Usage questions are welcome there, not only bug reports.

To get a useful answer quickly, include:

- What you are trying to do.
- A short component or template that shows the problem.
- What you expected to happen, and what happened instead.

## Report a bug

[Open a bug report]({{ repo_issues_url }}/new/choose){: target="_blank" rel="noopener"}
with enough detail for someone else to reproduce the problem:

- The `citry` and `citry-core` versions. `pip show citry citry-core`
  prints both.
- Your Python version and operating system.
- The smallest component and render call that triggers the problem.
- The full error message and traceback.

A small example that we can run is the biggest single thing that speeds up
a fix.

## Report a security issue

Do **not** open a public issue for a security problem. Report it privately
through GitHub's
[private vulnerability reporting]({{ repo_url }}/security/advisories/new){: target="_blank" rel="noopener"}.
