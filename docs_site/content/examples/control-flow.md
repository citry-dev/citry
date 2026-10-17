---
title: Control flow
description: Render conditions, loops, and empty states in a Citry template.
---

# Control flow

Use this pattern to render a list that can be empty, with each item drawn
one of two ways. The task list repeats a row for each task with
`<c-for>`, picks how a row looks with `<c-if>` and `<c-else>`, and shows
a message with `<c-empty>` when there are no tasks.

<c-example name="control_flow" />

`<c-empty>` goes right after the `<c-for>` it belongs to. The page renders
the list twice: once with three tasks and once with none, so you can see
both branches.

For every option of these tags, see
[Conditions and loops](/syntax/control-flow/).
