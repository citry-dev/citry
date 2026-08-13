"""
The ``dependencies`` built-in extension: a component's secondary assets.

A component declares extra JS/CSS files in a nested ``Dependencies`` class::

    class Card(Component):
        class Dependencies:
            js = ["vendor/chart.js"]
            css = {"all": "theme.css", "print": "print.css"}
            extend = True   # inherit entries from base classes (the default)

This extension owns that whole concern:
- The nested class (through the extension system's per-component config mechanism,
  since the extension name ``dependencies`` derives the config class name ``Dependencies``),
- The normalization and path resolution of entries,
- The merge across the component's base classes.

The merged result is read through ``Card.get_dependencies()``,
which returns a :class:`CitryDependencies`.

Entries may also be :class:`Script`/:class:`Style` objects (see ``types.py``),
which say exactly what tag to emit and pass through resolution unchanged.
A ``Path`` or other ``PathLike`` entry always names a local filesystem value;
an existing file is inlined by default, and a missing one raises
``FileNotFoundError``. Plain strings may instead name URLs or unresolved static
routes, including strings beginning with ``/``.

What the entries *mean* in the rendered output (inline the file content, emit
a ``<script src>`` tag, ...) is the emission half, which is in ``emission.py``;
the extension class and the entry resolution are in ``extension.py``.
This is citry's realization of django-components #1144 ("media becomes an extension"),
built as an extension from the start.

Design: docs/design/asset_loading.md section 7.
"""

from citry.ext.dependencies.emission import OnDependenciesContext
from citry.ext.dependencies.extension import (
    CitryDependencies,
    DependenciesConfig,
    DependenciesExtension,
    get_dependencies,
)
from citry.ext.dependencies.types import Dependency, DependencyRecord, Script, Style

__all__ = [
    "CitryDependencies",
    "DependenciesConfig",
    "DependenciesExtension",
    "Dependency",
    "DependencyRecord",
    "OnDependenciesContext",
    "Script",
    "Style",
    "get_dependencies",
]
