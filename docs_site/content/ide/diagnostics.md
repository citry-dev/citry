---
title: Diagnostic reference
description: Stable Citry diagnostic codes, messages, severities, and the tools that report them.
---

# Diagnostic reference

Citry-owned diagnostics use stable codes across the parser, `citry check`, the
language server, and editor formatting. The code identifies the condition even
when a message includes source-specific detail.

The entries below are rendered directly from the versioned
[`diagnostics/v1` catalog]({{ repo_url }}/tree/main/packages/protocol/diagnostics/v1).
Changing a code, message template, or documentation link requires changing that
catalog and regenerating its language bindings.

The editor may display a source label such as `citry` next to the code. The
source identifies the reporting tool; the code identifies the condition.
Each entry's **Reported by** line names the commands, APIs, or editor feature
that can produce it.

<c-diagnostic-catalog />
