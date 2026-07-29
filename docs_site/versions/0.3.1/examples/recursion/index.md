---
title: Recursion
url: https://citry.dev/v/0.3.1/examples/recursion/
description: "Render a tree by letting a component call itself."
---
# Recursion

A component that renders itself, to any depth.



### Component

````citry
"""A self-rendering tree, used as a live example in the docs.

TreeNode renders one node's label and then renders itself for each child,
so a nested structure of any depth is drawn with one component.
"""

from __future__ import annotations

from typing import Any, NotRequired, TypedDict

from citry import Component


class TreeNodeData(TypedDict):
    label: str
    children: NotRequired[list[TreeNodeData]]


class TreeNode(Component):
    """One node of a tree: its label, then itself for each child.

    The recursion stops on its own: a node with no children has an empty
    child list, so the ``<c-for>`` body (which is what recurses) runs zero
    times.
    """

    class Kwargs:
        node: TreeNodeData

    class Slots:
        pass

    template = """
      <div class="tree-node">
        <span class="tree-node__label">
          <span class="tree-node__icon">{{ icon }}</span>
          {{ label }}
        </span>
        <div c-if="has_children" class="tree-node__children">
          <c-TreeNode c-for="child in children" c-node="child" />
        </div>
      </div>
    """

    css = """
      .tree-node {
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: 0.95rem;
      }
      .tree-node__label {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.15rem 0;
        color: #1f2328;
      }
      .tree-node__icon {
        color: #6e7781;
      }
      .tree-node__children {
        margin-left: 1.1rem;
        padding-left: 0.75rem;
        border-left: 1px solid #d0d7de;
      }
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        node = kwargs.node
        children = node.get("children", [])
        has_children = len(children) > 0
        # Folder icon when there are children, file icon when it's a leaf.
        icon = "▾" if has_children else "•"
        return {
            "label": node["label"],
            "children": children,
            "has_children": has_children,
            "icon": icon,
        }
````

### Page

````citry
"""Standalone page that renders the recursion example (the live demo)."""

from typing import Any

from citry import Component


class RecursionPage(Component):
    """A full page showing a nested tree drawn by the self-rendering TreeNode."""

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Recursion example</title>
          <c-css />
        </head>
        <body
          style="margin: 0; padding: 1.5rem; font-family: system-ui, sans-serif;"
        >
          <c-TreeNode c-node="tree" />
          <c-js />
        </body>
      </html>
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        # A small folder tree, three levels deep, passed in one piece.
        tree = {
            "label": "project",
            "children": [
                {
                    "label": "src",
                    "children": [
                        {"label": "app.py"},
                        {"label": "utils.py"},
                    ],
                },
                {
                    "label": "docs",
                    "children": [
                        {
                            "label": "guide",
                            "children": [
                                {"label": "intro.md"},
                                {"label": "advanced.md"},
                            ],
                        },
                    ],
                },
                {"label": "README.md"},
            ],
        }
        return {"tree": tree}
````

[Open the live result](/v/0.3.1/examples/recursion/demo/)

