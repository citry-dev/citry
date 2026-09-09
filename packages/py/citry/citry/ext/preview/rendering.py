"""Compose preview templates, component layouts, and iframe galleries."""

from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING, Any
from urllib.parse import quote, urlencode

from citry.citry_element import CitryElement
from citry.component import Component
from citry.ext.preview.extension import PreviewExtension, Selection, _Preview
from citry.ext.preview.types import (
    Layout,
    PreviewComponent,
    PreviewError,
    PreviewGroup,
    PreviewItem,
    PreviewMetadata,
    PreviewPage,
    PreviewVariant,
    Variant,
)
from citry.slots import Slot, SlotContext

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry.citry_render import CitryRender

_PAGE = """
<!doctype html>
<html lang="en">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Component previews</title>
    </head>
    <body><c-slot name="content" /></body>
</html>
"""
_GALLERY = """
<main>
    <h1>Component previews</h1>
    <section c-for="group in preview.components">
        <h2>{{ group.component.name }}</h2>
        <p c-if="group.component.group">{{ group.component.group }}</p>
        <article c-for="item in group.items">
            <h3><a c-href="item.variant.url">{{ item.variant.label }}</a></h3>
            <p>{{ item.variant.description }}</p>
            <div style="max-width: 100%; overflow: auto;">{{ item.content }}</div>
        </article>
    </section>
    <p c-empty>No component previews are available.</p>
</main>
"""
_FRAME = """
<iframe
    c-title="preview.variant.label"
    c-src="preview.variant.url"
    c-width="preview.variant.viewport.width"
    c-height="preview.variant.viewport.height"
    style="display: block; border: 0; max-width: none;"
></iframe>
"""
_ITEMS = """
<c-for each="group in preview.components">
    <c-for each="item in group.items">{{ item.content }}</c-for>
</c-for>
"""


class PreviewNotFound(KeyError):
    """A requested identity is absent from the command selection."""


class PreviewRenderer:
    """Resolve command selections and compose their complete HTML pages."""

    def __init__(self, extension: PreviewExtension, selection: Selection | None = None) -> None:
        self.extension = extension
        self.citry = extension.citry
        self.selection = selection or Selection()

    def _metadata(self, row: _Preview, value: Variant, *, urls: bool = True) -> PreviewMetadata:
        path = f"ext/preview/render/{quote(row.info.class_id, safe='')}?{urlencode({'variant': value.slug})}"
        return PreviewMetadata(
            PreviewComponent(row.info.class_id, row.info.name, row.config.group),
            PreviewVariant(
                value.slug,
                value.label,
                value.description,
                value.viewport or row.config.viewport,
                self.citry.build_url(path) if urls else "",
            ),
        )

    def catalog(self, *, urls: bool = True) -> dict[str, Any]:
        """Return allowlisted metadata, excluding input values and source paths."""
        components = []
        for row in self.extension.previews(self.selection):
            variants = [asdict(self._metadata(row, value, urls=urls).variant) for value in row.variants]
            components.append(
                {"id": row.info.class_id, "name": row.info.name, "group": row.config.group, "variants": variants}
            )
        return {"service": "citry-preview", "version": 1, "components": components}

    def _source(self, row: _Preview | None, field: str, source: str | None, file: Any) -> tuple[str, str]:
        if file is None:
            return source or "", f"<preview:{row.info.name if row else 'page'}:{field}>"
        path = self.extension.file_path(row.component if row else None, field, file).resolve()
        try:
            return path.read_text(encoding="utf-8"), str(path)
        except (OSError, UnicodeError) as exc:
            raise PreviewError(f"Cannot read Preview.{field} at {path}: {exc}") from exc

    def _template_slot(
        self,
        source: str,
        variables: Mapping[str, Any],
        *,
        origin: str,
        slots: Mapping[str, Any] | None = None,
        template_globals: Mapping[str, Any] | None = None,
    ) -> Slot:
        def render(ctx: SlotContext) -> CitryRender:
            # A nested root explicitly receives the values active at its slot site.
            return self.citry.render_template(
                source,
                variables,
                slots=slots,
                provides=ctx.provides,
                template_globals=template_globals,
                origin=origin,
            )

        return Slot(render)

    def _layout(
        self,
        layout: Layout | None,
        row: _Preview | None,
        field: str,
        metadata: Any,
        content: Slot,
        template_globals: Mapping[str, Any] | None,
    ) -> Slot:
        if layout is None:
            return content
        if layout.component is not None:
            cls = layout.component
            if not issubclass(cls, Component) or cls.citry is not self.citry:
                raise PreviewError(f"Preview.{field} requires a component belonging to this Citry app.")

            def render(ctx: SlotContext) -> CitryRender:
                return CitryElement(cls, {"preview": metadata}, {"content": content}).render(
                    provides=ctx.provides,
                    template_globals=template_globals,
                )

            return Slot(render)
        source, origin = self._source(row, field, layout.template, layout.template_file)
        return self._template_slot(
            source,
            {"preview": metadata},
            origin=origin,
            slots={"content": content},
            template_globals=template_globals,
        )

    def _example(
        self, row: _Preview, value: Variant, metadata: PreviewMetadata, globals_: Mapping[str, Any] | None
    ) -> Slot:
        if row.config.template is not None or row.config.template_file is not None:
            source, origin = self._source(row, "template_file", row.config.template, row.config.template_file)
            content = self._template_slot(
                source,
                {"params": dict(value.params), "preview": metadata},
                origin=origin,
                template_globals=globals_,
            )
        else:

            def render(ctx: SlotContext) -> CitryRender:
                return CitryElement(row.component, dict(value.params)).render(
                    provides=ctx.provides, template_globals=globals_
                )

            content = Slot(render)
        return self._layout(row.config.variant_layout, row, "variant_layout", metadata, content, globals_)

    def _page(
        self,
        page: PreviewPage,
        row: _Preview | None,
        *,
        gallery: bool,
        provides: Mapping[str, Any] | None,
        template_globals: Mapping[str, Any] | None,
    ) -> CitryRender:
        body = self._template_slot(
            _GALLERY if gallery else _ITEMS,
            {"preview": page},
            origin="<preview:content>",
            template_globals=template_globals,
        )
        layout = (
            row.config.page_layout
            if row
            else self.citry.settings.extensions_defaults.get("preview", {}).get("page_layout")
        )
        if layout is None:
            layout = Layout(template=_PAGE)
        content = self._layout(layout, row, "page_layout", page, body, template_globals)
        # Keep the final result structured so dependency/security emission runs once.
        return self.citry.render_template(
            "{{ page }}",
            {"page": content},
            provides=provides,
            template_globals=template_globals,
            origin="<preview:root>",
        )

    def render_page(
        self,
        component: str,
        slug: str,
        *,
        provides: Mapping[str, Any] | None = None,
        template_globals: Mapping[str, Any] | None = None,
    ) -> CitryRender:
        """Render one selected component ID and variant slug as a complete page."""
        for row in self.extension.previews(self.selection):
            if row.info.class_id != component:
                continue
            for value in row.variants:
                if value.slug != slug:
                    continue
                metadata = self._metadata(row, value)
                item = PreviewItem(metadata.variant, self._example(row, value, metadata, template_globals))
                page = PreviewPage("variant", (PreviewGroup(metadata.component, (item,)),))
                return self._page(page, row, gallery=False, provides=provides, template_globals=template_globals)
        raise PreviewNotFound("Unknown or excluded preview component or variant.")

    def render_gallery(
        self,
        component: str | None = None,
        *,
        provides: Mapping[str, Any] | None = None,
        template_globals: Mapping[str, Any] | None = None,
    ) -> CitryRender:
        """Render selected variants in separate documents inside an iframe gallery."""
        rows = self.extension.previews(self.selection)
        if component is not None:
            rows = tuple(row for row in rows if row.info.class_id == component)
            if not rows:
                raise PreviewNotFound("Unknown or excluded preview component.")
        groups = []
        for row in rows:
            items = []
            for value in row.variants:
                metadata = self._metadata(row, value)
                content = self._template_slot(
                    _FRAME,
                    {"preview": metadata},
                    origin="<preview:frame>",
                    template_globals=template_globals,
                )
                items.append(PreviewItem(metadata.variant, content))
            groups.append(
                PreviewGroup(PreviewComponent(row.info.class_id, row.info.name, row.config.group), tuple(items))
            )
        page = PreviewPage("component" if component else "all", tuple(groups))
        return self._page(
            page,
            rows[0] if component else None,
            gallery=True,
            provides=provides,
            template_globals=template_globals,
        )
