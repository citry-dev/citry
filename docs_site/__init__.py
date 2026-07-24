"""
The Citry documentation site.

A static documentation site that renders its own pages with Citry components
(dogfooding the engine), ported from the django-components docs site. The
build is a three-pass pipeline (see ``_internal.pipeline.render_page``):
1. Expand the custom ``<c-*>`` tags,
2. Convert markdown to HTML,
3. Then wrap the result in the ``DocPage`` layout component.

This is internal tooling, not a shipped package. Its optional dependencies
live in the root ``pyproject.toml`` ``docs`` extra.
"""
