---
title: Recursion
description: Render a tree by letting a component call itself.
---

# Recursion

Use this pattern to draw nested data, such as a file tree,
comment threads, or a menu. `TreeNode` renders one node's label, then
renders `<c-TreeNode>` again for each child.

<c-example name="recursion" />

The recursion stops on its own. A leaf has no children, so the `c-if` on
the child list is false and no further `TreeNode` renders. Your own data
needs the same end.

## Stop endless recursion

A node that appears again inside its own children never reaches a leaf. Citry stops
such a render with a `RecursionError` once components are nested more
than 2,000 levels deep. The message starts with the component that
repeats:

```text
Component TreeNode is nested more than 2000 components deep
(TreeNode > TreeNode > ... > TreeNode > TreeNode > TreeNode).
```

[`<c-error-fallback>`](/concepts/error-boundaries/) does not catch this
error, so the whole render fails. Fix the data so every branch ends in a
leaf. If your page really nests deeper than 2,000 components, raise the
limit with the
[`max_component_depth`][citry.CitrySettings.max_component_depth]
setting:

```python
app = Citry(max_component_depth=5_000)
```
