---
title: Getting help
description: Where to ask questions about Citry, how to search before posting, and where to report bugs and security issues.
---

# Getting help

Have a question about Citry, or hit something that looks like a bug? Everything
happens on the GitHub repository at
[{{ repo_full_name }}]({{ repo_url }}){: target="_blank" rel="noopener"}. Here is where to go.

## Search before you post

Chances are someone has already run into the same thing. Before you open
anything, search:

- The
[existing isssues and discussions]({{ repo_issues_url }}?q=){: target="_blank" rel="noopener"} for your question or the exact error message.
- Use the [documentation search feature](/community/help/?q=help)
 feature.

## Ask a question

If you cannot find an answer, [open a new issue]({{ repo_issues_url }}/new){: target="_blank" rel="noopener"}. Usage questions are welcome there, not just
bug reports.

To get a useful answer quickly, include:

- What you are trying to do.
- A short component or template that shows the problem.
- What you expected to happen, and what happened instead.

## Report a bug

A bug report is an issue with enough detail for someone else to reproduce it.
[Open a bug report]({{ repo_issues_url }}/new){: target="_blank" rel="noopener"} and include:

- The Citry version. Run `citry --version` to get it.
- Your Python version and operating system.
- The smallest component and render call that triggers the problem.
- The full error message and traceback.

A minimal reproduction that we can run is the single biggest thing that speeds
up a fix.

## Report a security issue

Please **DO NOT** open a public issue for a security problem. Report it privately
through GitHub's
[private vulnerability reporting]({{ repo_url }}/security/advisories/new){: target="_blank" rel="noopener"}.
