---
title: Diagnostic reference
description: Look up a Citry error or warning code to see what went wrong, how to fix it, and which tools report it.
---

# Diagnostic reference

Every error and warning Citry reports has a code, such as
`citry.template.unknown-variable`. The editor shows it next to the message,
and `citry check` prints it with each finding. Find the code below to see what
went wrong and how to fix it.

The code always names the same mistake in every tool: the editor, `citry
check`, `citry format`, and the template parser. The message can add details,
such as the name you misspelled.

Some rules can be made stricter or turned off. Those entries say "Your
application can change this severity". For the template lint rules, see
[Template linting](/ide/template-linting/#change-how-strict-a-rule-is).

Codes that start with `citry.python.` or `citry.typescript.` come from the
Python and TypeScript type checkers. They are listed at the end of this page.

<c-diagnostic-catalog />
