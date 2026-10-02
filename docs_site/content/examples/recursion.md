---
title: Recursion
description: Render a tree by letting a component call itself.
---

# Recursion

Use this pattern to draw nested data of any depth, such as a file tree,
comment threads, or a menu. `TreeNode` renders one node's label, then
renders `<c-TreeNode>` again for each child.

<c-example name="recursion" />

The recursion stops on its own. A leaf has no children, so the `c-if` on
the child list is false and no further `TreeNode` renders. Your own data
needs the same end: a node that contains itself never reaches a leaf.
