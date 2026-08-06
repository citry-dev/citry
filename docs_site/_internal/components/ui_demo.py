"""Result-first component previews for Citry UI documentation pages."""

from __future__ import annotations

from typing import Any

from markupsafe import Markup
from pygments import highlight
from pygments.formatters import HtmlFormatter

from citry import Component
from docs_site._internal.components._live_code_markup import (
    LiveActivationControls,  # noqa: F401 - registered for the template below
    LiveWorkspace,  # noqa: F401 - registered for the template below
)
from docs_site._internal.live_code import get_live_code_context
from docs_site._internal.ui_previews import (
    UiPreviewControl,
    encode_ui_preview_projection,
    get_ui_preview_context,
    load_ui_preview_controls,
    load_ui_preview_source,
    resolve_ui_preview_directive,
)
from pygments_citry.lexers import CitryPythonLexer


class UiDemoControls(Component):
    """Render explicitly authored controls above one component preview."""

    transparent = True

    class Kwargs:
        controls: tuple[UiPreviewControl, ...]
        identifier: str
        title: str

    class Slots:
        pass

    template = """
      <details
        class="citry-ui-demo__controls"
        data-ui-preview-controls
        open
      >
        <summary>Customize example</summary>
        <form
          c-aria-label="title + ' controls'"
          autocomplete="off"
        >
          <c-for each="control in controls">
            <c-if cond="control.kind == 'checkbox'">
              <label class="citry-ui-demo__control citry-ui-demo__control--checkbox">
                <input
                  c-id="identifier + '-control-' + control.name"
                  type="checkbox"
                  c-name="control.name"
                  data-ui-preview-control
                  c-checked="control.default"
                />
                <span>{{ control.label }}</span>
              </label>
            </c-if>
            <c-else>
              <label
                class="citry-ui-demo__control"
                c-bind="{'for': identifier + '-control-' + control.name}"
              >
                <span>{{ control.label }}</span>
                <select
                  c-id="identifier + '-control-' + control.name"
                  c-name="control.name"
                  data-ui-preview-control
                >
                  <option
                    c-for="option in control.options"
                    c-value="option.value"
                    c-selected="option.value == control.default"
                  >{{ option.label }}</option>
                </select>
              </label>
            </c-else>
          </c-for>
        </form>
      </details>
    """

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        return {
            "controls": tuple(kwargs.controls),
            "identifier": str(kwargs.identifier),
            "title": str(kwargs.title),
        }


class UiDemo(Component):
    """Render a component preview before its collapsible canonical source."""

    transparent = True

    class Kwargs:
        path: str
        title: str
        source_open: bool = False

    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        path = str(kwargs.path)
        title = str(kwargs.title)
        source_open = bool(kwargs.source_open)
        preview = resolve_ui_preview_directive(
            path=path,
            title=title,
            source_open=source_open,
        )
        context = get_ui_preview_context()
        if context is None:  # The resolver above normally provides the clearer error.
            raise RuntimeError("Citry UI preview context was not initialized")
        repo_root = context.config.repo_root
        if repo_root is None:
            raise RuntimeError("Citry UI preview repository root was not configured")
        source = load_ui_preview_source(preview, repo_root=repo_root)
        preview_controls = load_ui_preview_controls(
            preview,
            repo_root=repo_root,
        )
        highlighted = highlight(
            source,
            CitryPythonLexer(stripnl=False, ensurenl=False),
            HtmlFormatter(cssclass="highlight", nowrap=False),
        )
        if not source.endswith("\n"):
            highlighted = highlighted.replace("\n</pre></div>\n", "</pre></div>\n")

        live_context = get_live_code_context()
        interactive = bool(live_context is not None and live_context.interactive and live_context.allow_citry_ui)
        if interactive and live_context is not None:
            live_context.has_live_code = True
            live_context.has_interactive = True

        payload = encode_ui_preview_projection(preview)
        identifier = f"citry-ui-demo-{self.id}"
        return {
            "projection_start": Markup(f"<!-- docs-ui-preview:{payload}:start -->"),  # noqa: S704
            "projection_end": Markup(f"<!-- docs-ui-preview:{payload}:end -->"),  # noqa: S704
            "root_class": "citry-ui-demo citry-live-code" if interactive else "citry-ui-demo",
            "root_attrs": {"data-citry-live-code": True} if interactive else {},
            "title": preview.title,
            "identifier": identifier,
            "interactive": interactive,
            "preview_controls": preview_controls,
            "frame_src": f"{context.version_prefix.rstrip('/')}{preview.public_path}",
            "frame_title": f"{preview.title} rendered preview",
            "source_open": preview.source_open,
            "highlighted": Markup(highlighted),  # noqa: S704 - trusted Pygments output
        }

    template = """
      {{ projection_start }}
      <figure
        c-class="root_class"
        data-citry-ui-demo
        data-pagefind-ignore
        c-bind="root_attrs"
      >
        <figcaption class="citry-ui-demo__title">
          <span>{{ title }}</span>
          <span
            c-if="interactive"
            class="citry-ui-demo__actions"
            data-pagefind-ignore
          >
            <c-LiveActivationControls />
          </span>
        </figcaption>
        <div data-live-static>
          <c-UiDemoControls
            c-if="preview_controls"
            c-controls="preview_controls"
            c-identifier="identifier"
            c-title="title"
          />
          <div class="citry-ui-demo__preview">
            <iframe
              class="example-demo-frame--theme-sync"
              c-src="frame_src"
              c-title="frame_title"
              data-ui-preview-frame
              sandbox="allow-forms allow-scripts"
              loading="lazy"
            ></iframe>
          </div>
          <details
            class="citry-ui-demo__source"
            c-open="source_open"
          >
            <summary>Show code</summary>
            {{ highlighted }}
          </details>
        </div>
        <c-LiveWorkspace
          c-if="interactive"
          c-identifier="identifier"
          c-title="title"
        />
      </figure>
      {{ projection_end }}
    """


__all__ = ["UiDemo"]
