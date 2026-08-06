"""Component-owned, build-rendered previews for Citry UI documentation."""

from __future__ import annotations

import ast
import base64
import hashlib
import importlib.util
import json
import re
import sys
import threading
from collections.abc import Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any

from citry import CitryElement, Component, ComponentLike
from citry import citry as default_citry
from docs_site._internal.fence_protection import protect_fences
from docs_site._internal.frontmatter import parse_page
from docs_site._internal.live_code import (
    UI_COMPONENTS_ROOT,
    LiveCodeValidationError,
    load_live_source,
)
from docs_site._internal.ui_library_projection import (
    UiLibraryCatalog,
    UiLibraryProjection,
    ui_library_source_path,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.config import DocsConfig

_PREVIEW_NAME_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_CONTROL_NAME_RE = re.compile(r"[a-z][a-z0-9_]*\Z")
_PROJECTION_BLOCK_RE = re.compile(
    r"<!-- docs-ui-preview:(?P<payload>[A-Za-z0-9_-]+):start -->.*?"
    r"<!-- docs-ui-preview:(?P=payload):end -->",
    re.DOTALL,
)
_loaded_previews: dict[Path, _LoadedUiPreview] = {}
_loaded_previews_lock = threading.Lock()


class UiPreviewError(ValueError):
    """An authored Citry UI preview does not meet the docs contract."""


@dataclass(frozen=True, slots=True)
class UiPreview:
    """One component-owned source module and its private rendered route."""

    family: str
    name: str
    title: str
    source: PurePosixPath
    public_path: str
    source_open: bool = False


@dataclass(frozen=True, slots=True)
class UiPreviewControlOption:
    value: str
    label: str


@dataclass(frozen=True, slots=True)
class UiPreviewControl:
    name: str
    label: str
    kind: str
    default: str | bool
    options: tuple[UiPreviewControlOption, ...] = ()


@dataclass(frozen=True, slots=True)
class _LoadedUiPreview:
    value: object
    controls: tuple[UiPreviewControl, ...]


@dataclass(slots=True)
class UiPreviewRenderContext:
    """Per-page state used while ``<c-ui-demo>`` directives render."""

    config: DocsConfig
    catalog: UiLibraryCatalog
    source_path: Path | None
    current_path: str
    version_prefix: str = ""


_context: ContextVar[UiPreviewRenderContext | None] = ContextVar(
    "docs_ui_preview_context",
    default=None,
)


@contextmanager
def use_ui_preview_context(context: UiPreviewRenderContext) -> Iterator[None]:
    """Expose one page's preview routing context to nested docs components."""
    token = _context.set(context)
    try:
        yield
    finally:
        _context.reset(token)


def get_ui_preview_context() -> UiPreviewRenderContext | None:
    """Return the active docs preview context, if a page is rendering."""
    return _context.get()


class _UiDemoParser(HTMLParser):
    """Collect authored ``<c-ui-demo>`` tags outside protected code blocks."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.directives: list[dict[str, str | None]] = []
        self._raw_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() == "c-raw":
            self._raw_depth += 1
            return
        self._collect(tag, attrs)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._collect(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == "c-raw" and self._raw_depth:
            self._raw_depth -= 1

    def _collect(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._raw_depth or tag.casefold() != "c-ui-demo":
            return
        values: dict[str, str | None] = {}
        for name, value in attrs:
            if name in values:
                raise UiPreviewError(f"<c-ui-demo> repeats the {name!r} attribute")
            values[name] = value
        self.directives.append(values)


def discover_ui_previews(
    catalog: UiLibraryCatalog,
    *,
    repo_root: Path,
) -> tuple[UiPreview, ...]:
    """Discover and validate previews declared by component API sources."""
    previews: list[UiPreview] = []
    routes: dict[str, UiPreview] = {}
    for projection in catalog.projections:
        try:
            api_source = ui_library_source_path(projection, repo_root=repo_root)
            parser = _UiDemoParser()
            parser.feed(protect_fences(parse_page(api_source.read_text(encoding="utf-8")).body))
            parser.close()
            for attrs in parser.directives:
                preview = _preview_from_attrs(
                    attrs,
                    projection=projection,
                    repo_root=repo_root,
                )
                existing = routes.get(preview.public_path)
                if existing is not None and (existing.source, existing.title) != (preview.source, preview.title):
                    raise UiPreviewError(f"Citry UI preview route {preview.public_path!r} is declared more than once")
                if existing is None:
                    routes[preview.public_path] = preview
                    previews.append(preview)
        except (OSError, UiPreviewError, LiveCodeValidationError) as error:
            raise UiPreviewError(f"{projection.source.as_posix()}: {error}") from error
    return tuple(previews)


def resolve_ui_preview_directive(
    *,
    path: str,
    title: str,
    source_open: bool,
) -> UiPreview:
    """Resolve one rendered directive against its component-owned API page."""
    context = get_ui_preview_context()
    if context is None or context.source_path is None:
        raise UiPreviewError("<c-ui-demo> requires an authored Citry UI component page")
    projection = _projection_for_source(
        context.catalog,
        source_path=context.source_path,
        repo_root=context.config.repo_root,
    )
    if projection is None:
        raise UiPreviewError("<c-ui-demo> may only be used in a catalog-declared Citry UI API source")
    preview = _preview_from_attrs(
        {
            "path": path,
            "title": title,
            **({"source_open": None} if source_open else {}),
        },
        projection=projection,
        repo_root=context.config.repo_root,
    )
    expected_page = projection.public_path.strip("/")
    if context.current_path.strip("/") != expected_page:
        raise UiPreviewError(f"<c-ui-demo> for {projection.family!r} rendered at the wrong page route")
    return preview


def ui_preview_for_public_path(
    catalog: UiLibraryCatalog,
    public_path: str,
    *,
    repo_root: Path,
) -> UiPreview | None:
    """Return the declared preview for one private clean URL."""
    clean = f"/{public_path.strip('/')}/"
    return next(
        (preview for preview in discover_ui_previews(catalog, repo_root=repo_root) if preview.public_path == clean),
        None,
    )


def load_ui_preview_source(preview: UiPreview, *, repo_root: Path) -> str:
    """Read a preview through the component-snippet validation contract."""
    return load_live_source(
        preview.source.as_posix(),
        repo_root=repo_root,
        title=preview.title,
        static=True,
        allow_citry_ui=True,
    )


def render_ui_preview_document(preview: UiPreview, *, repo_root: Path) -> str:
    """Execute one trusted preview module and serialize its standalone document."""
    loaded = _load_ui_preview(preview, repo_root=repo_root)
    return str(UiPreviewDocument(title=preview.title, content=loaded.value))


def load_ui_preview_controls(
    preview: UiPreview,
    *,
    repo_root: Path,
) -> tuple[UiPreviewControl, ...]:
    """Return explicitly authored host controls for one preview."""
    return _load_ui_preview(preview, repo_root=repo_root).controls


def encode_ui_preview_projection(preview: UiPreview) -> str:
    """Encode projection metadata without embedding source in rendered HTML."""
    payload = json.dumps(
        {
            "path": preview.source.as_posix(),
            "title": preview.title,
            "public_path": preview.public_path,
        },
        separators=(",", ":"),
    ).encode()
    return base64.urlsafe_b64encode(payload).decode().rstrip("=")


def project_ui_previews_for_text(source: str, *, repo_root: Path) -> str:
    """Replace rich preview cards with source-first Markdown."""

    def replace(match: re.Match[str]) -> str:
        path, title, public_path = _decode_ui_preview_projection(match.group("payload"))
        preview = UiPreview(
            family="",
            name="",
            title=title,
            source=PurePosixPath(path),
            public_path=public_path,
        )
        code = load_ui_preview_source(preview, repo_root=repo_root).rstrip()
        longest_run = max((len(run) for run in re.findall(r"`+", code)), default=0)
        fence = "`" * max(4, longest_run + 1)
        return f"### {title}\n\n[Open the rendered preview]({public_path})\n\n{fence}citry\n{code}\n{fence}"

    return _PROJECTION_BLOCK_RE.sub(replace, source)


def _preview_from_attrs(
    attrs: dict[str, str | None],
    *,
    projection: UiLibraryProjection,
    repo_root: Path,
) -> UiPreview:
    allowed = {"path", "title", "source_open"}
    unknown = sorted(set(attrs) - allowed)
    if unknown:
        raise UiPreviewError(f"<c-ui-demo> has unknown attribute(s): {', '.join(unknown)}")
    path = attrs.get("path")
    title = attrs.get("title")
    if not isinstance(path, str) or not path:
        raise UiPreviewError("<c-ui-demo> requires a non-empty path attribute")
    if not isinstance(title, str) or not title.strip() or title != title.strip() or "\n" in title:
        raise UiPreviewError("<c-ui-demo> requires a single-line title without surrounding whitespace")
    source_open_value = attrs.get("source_open", False)
    if source_open_value not in (False, None):
        raise UiPreviewError("<c-ui-demo> source_open is a boolean attribute")

    authored = PurePosixPath(path)
    prefix_length = len(UI_COMPONENTS_ROOT.parts)
    if (
        len(authored.parts) != prefix_length + 3
        or authored.parts[:prefix_length] != UI_COMPONENTS_ROOT.parts
        or authored.parts[prefix_length + 1] != "snippets"
        or authored.suffix != ".py"
    ):
        raise UiPreviewError(
            "<c-ui-demo> path must name a module in packages/py/citry_ui/citry_ui/components/<family>/snippets/"
        )
    source_owner = projection.source.parent.name
    snippet_owner = authored.parts[prefix_length]
    if not source_owner or snippet_owner != source_owner:
        raise UiPreviewError(f"<c-ui-demo> for {projection.family!r} may not use a snippet owned by {snippet_owner!r}")
    name = authored.stem.replace("_", "-")
    if not _PREVIEW_NAME_RE.fullmatch(name):
        raise UiPreviewError("<c-ui-demo> filenames must produce a lowercase kebab-case preview name")
    load_live_source(
        path,
        repo_root=repo_root,
        title=title,
        static=True,
        allow_citry_ui=True,
    )
    return UiPreview(
        family=projection.family,
        name=name,
        title=title,
        source=authored,
        public_path=f"{projection.public_path}_previews/{name}/",
        source_open=source_open_value is None,
    )


def _projection_for_source(
    catalog: UiLibraryCatalog,
    *,
    source_path: Path,
    repo_root: Path,
) -> UiLibraryProjection | None:
    resolved = source_path.resolve()
    return next(
        (
            projection
            for projection in catalog.projections
            if ui_library_source_path(projection, repo_root=repo_root).resolve() == resolved
        ),
        None,
    )


def _load_ui_preview(preview: UiPreview, *, repo_root: Path) -> _LoadedUiPreview:
    source_path = repo_root.joinpath(*preview.source.parts).resolve()
    with _loaded_previews_lock:
        existing = _loaded_previews.get(source_path)
        if existing is not None:
            return existing

        source = load_ui_preview_source(preview, repo_root=repo_root)
        tree = ast.parse(source, filename=preview.source.as_posix())
        if not tree.body or not isinstance(tree.body[-1], ast.Expr):
            raise UiPreviewError("preview modules must end with the expression `preview`")
        final_value = tree.body[-1].value
        if not isinstance(final_value, ast.Name) or final_value.id != "preview":
            raise UiPreviewError("preview modules must end with the expression `preview`")

        digest = hashlib.sha256(str(source_path).encode()).hexdigest()[:16]
        module_family = preview.family.replace("-", "_")
        module_name = f"docs_site.ui_previews.{module_family}.{preview.name.replace('-', '_')}_{digest}"
        spec = importlib.util.spec_from_file_location(module_name, source_path)
        if spec is None or spec.loader is None:
            raise UiPreviewError(f"could not load preview module {preview.source.as_posix()!r}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            sys.modules.pop(module_name, None)
            raise
        value = getattr(module, "preview", None)
        if not isinstance(value, (CitryElement, ComponentLike)):
            raise UiPreviewError("preview modules must expose `preview` as a Citry component-like value")
        if isinstance(value, CitryElement) and value.comp_cls.citry is not default_citry:
            raise UiPreviewError("preview elements must use Citry's default instance")
        controls = _parse_ui_preview_controls(getattr(module, "preview_controls", ()))
        loaded = _LoadedUiPreview(value=value, controls=controls)
        _loaded_previews[source_path] = loaded
        return loaded


def _parse_ui_preview_controls(value: object) -> tuple[UiPreviewControl, ...]:
    if not isinstance(value, (list, tuple)):
        raise UiPreviewError("`preview_controls` must be a list or tuple")

    controls: list[UiPreviewControl] = []
    names: set[str] = set()
    for index, raw_control in enumerate(value, start=1):
        prefix = f"preview_controls item {index}"
        if not isinstance(raw_control, Mapping):
            raise UiPreviewError(f"{prefix} must be a mapping")
        unknown = sorted(set(raw_control) - {"name", "label", "type", "default", "options"})
        if unknown:
            raise UiPreviewError(f"{prefix} has unknown field(s): {', '.join(unknown)}")

        name = raw_control.get("name")
        label = raw_control.get("label")
        kind = raw_control.get("type")
        default = raw_control.get("default")
        if not isinstance(name, str) or not _CONTROL_NAME_RE.fullmatch(name):
            raise UiPreviewError(f"{prefix} name must be a lowercase Python identifier")
        if name in names:
            raise UiPreviewError(f"`preview_controls` repeats the name {name!r}")
        names.add(name)
        if not isinstance(label, str) or not label or label != label.strip() or "\n" in label:
            raise UiPreviewError(f"{prefix} label must be a non-empty single line")

        if kind == "checkbox":
            if not isinstance(default, bool):
                raise UiPreviewError(f"{prefix} checkbox default must be a bool")
            if "options" in raw_control:
                raise UiPreviewError(f"{prefix} checkbox may not define options")
            controls.append(
                UiPreviewControl(
                    name=name,
                    label=label,
                    kind=kind,
                    default=default,
                )
            )
            continue

        if kind != "select":
            raise UiPreviewError(f"{prefix} type must be 'select' or 'checkbox'")
        if not isinstance(default, str):
            raise UiPreviewError(f"{prefix} select default must be a string")
        raw_options = raw_control.get("options")
        if not isinstance(raw_options, (list, tuple)) or not raw_options:
            raise UiPreviewError(f"{prefix} select options must be a non-empty list or tuple")
        options: list[UiPreviewControlOption] = []
        option_values: set[str] = set()
        for option_index, raw_option in enumerate(raw_options, start=1):
            if not isinstance(raw_option, (list, tuple)) or len(raw_option) != 2:
                raise UiPreviewError(f"{prefix} option {option_index} must be a (value, label) pair")
            option_value, option_label = raw_option
            if not isinstance(option_value, str) or not option_value:
                raise UiPreviewError(f"{prefix} option {option_index} value must be a string")
            if (
                not isinstance(option_label, str)
                or not option_label
                or option_label != option_label.strip()
                or "\n" in option_label
            ):
                raise UiPreviewError(f"{prefix} option {option_index} label must be a non-empty single line")
            if option_value in option_values:
                raise UiPreviewError(f"{prefix} repeats option value {option_value!r}")
            option_values.add(option_value)
            options.append(UiPreviewControlOption(value=option_value, label=option_label))
        if default not in option_values:
            raise UiPreviewError(f"{prefix} default must match one of its option values")
        controls.append(
            UiPreviewControl(
                name=name,
                label=label,
                kind=kind,
                default=default,
                options=tuple(options),
            )
        )
    return tuple(controls)


def _decode_ui_preview_projection(payload: str) -> tuple[str, str, str]:
    padded = payload + "=" * (-len(payload) % 4)
    try:
        value = json.loads(base64.urlsafe_b64decode(padded).decode())
        path = value["path"]
        title = value["title"]
        public_path = value["public_path"]
    except (ValueError, KeyError, TypeError, UnicodeDecodeError) as error:
        raise UiPreviewError("Citry UI preview projection marker is invalid") from error
    if not all(isinstance(item, str) for item in (path, title, public_path)):
        raise UiPreviewError("Citry UI preview projection marker is invalid")
    return path, title, public_path


_RESIZE_SCRIPT = """
  <script>
    (() => {
      const publish = () => {
        const height = Math.ceil(document.documentElement.scrollHeight);
        parent.postMessage({ type: "citry-ui-preview-height", height }, "*");
      };
      addEventListener("message", (event) => {
        if (event.source !== parent) return;
        if (
          event.data?.type === "citry-ui-preview-theme"
          && ["light", "dark"].includes(event.data.theme)
        ) {
          document.documentElement.style.colorScheme = event.data.theme;
          document.body.style.colorScheme = event.data.theme;
          publish();
          return;
        }
        if (
          event.data?.type === "citry-ui-preview-controls"
          && event.data.values
          && typeof event.data.values === "object"
          && !Array.isArray(event.data.values)
        ) {
          dispatchEvent(new CustomEvent("citry-ui-preview-controls", {
            detail: event.data.values,
          }));
          publish();
        }
      });
      addEventListener("load", publish);
      new ResizeObserver(publish).observe(document.documentElement);
      publish();
    })();
  </script>
"""


class UiPreviewDocument(Component):
    """Private standalone document wrapping one component preview."""

    class Kwargs:
        title: str
        content: object

    class Slots:
        pass

    template = f"""
      <!doctype html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <meta name="robots" content="noindex,nofollow" />
          <meta name="color-scheme" content="light dark" />
          <title>{{{{ title }}}}</title>
          <c-css />
        </head>
        <body>
          <main>{{{{ content }}}}</main>
          <c-js />
          {_RESIZE_SCRIPT}
        </body>
      </html>
    """

    css = """
      :where(*) {
        box-sizing: border-box;
      }

      :where(html, body) {
        min-width: 0;
        margin: 0;
        background: light-dark(
          oklch(92% 0.007 250),
          oklch(24% 0.01 250)
        );
        color: CanvasText;
      }

      :where(html) {
        font-size: 87.5%;
      }

      :where(body) {
        padding: 1.25rem;
      }

      :where(main) {
        min-width: 0;
      }
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {"title": kwargs.title, "content": kwargs.content}


__all__ = [
    "UiPreview",
    "UiPreviewControl",
    "UiPreviewControlOption",
    "UiPreviewError",
    "UiPreviewRenderContext",
    "discover_ui_previews",
    "encode_ui_preview_projection",
    "get_ui_preview_context",
    "load_ui_preview_controls",
    "load_ui_preview_source",
    "project_ui_previews_for_text",
    "render_ui_preview_document",
    "resolve_ui_preview_directive",
    "ui_preview_for_public_path",
    "use_ui_preview_context",
]
