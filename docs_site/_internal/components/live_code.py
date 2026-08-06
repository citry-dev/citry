"""Static-first, opt-in live Python examples for narrative documentation."""

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
from docs_site._internal.config import config as default_config
from docs_site._internal.live_code import (
    encode_live_projection,
    get_live_code_context,
    load_live_source,
)
from pygments_citry.lexers import CitryPythonLexer


class LiveCode(Component):
    """``<c-live-code>`` renders a validated static block with optional activation."""

    transparent = True

    class Kwargs:
        path: str
        title: str
        full_height: bool = False
        static: bool = False

    class Slots:
        pass

    # The component expands inside Markdown before the Markdown pass. Citry
    # normalizes the inline template's common indentation before compiling it.
    template = """

          {{ projection_start }}
          <figure
            c-class="root_class"
            c-bind="root_attrs"
          >
            <figcaption class="citry-live-code__caption">
              <span>{{ title }}</span>
              <span
                class="citry-live-code__caption-actions"
                data-pagefind-ignore
              >
                <c-LiveActivationControls c-if="interactive" />
                <a c-if="show_playground_link" href="/playground/">
                  Open the current playground
                </a>
              </span>
            </figcaption>
            <div
              class="citry-live-code__static"
              data-live-static
            >
              {{ highlighted }}
            </div>
            <c-LiveWorkspace
              c-if="interactive"
              c-identifier="identifier"
              c-title="title"
            />
          </figure>
          {{ projection_end }}

    """

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        path = str(kwargs.path)
        title = str(kwargs.title)
        full_height = bool(kwargs.full_height)
        authored_static = bool(kwargs.static)
        context = get_live_code_context()
        repo_root = context.config.repo_root if context is not None else default_config.repo_root
        if repo_root is None:
            raise RuntimeError("Live-code repository root was not configured")
        local_ui_runtime = context.allow_citry_ui if context is not None else False
        interactive = (context.interactive if context is not None else True) and (
            not authored_static or local_ui_runtime
        )
        source = load_live_source(
            path,
            repo_root=repo_root,
            title=title,
            static=authored_static,
            allow_citry_ui=local_ui_runtime,
        )
        highlighted = highlight(
            source,
            CitryPythonLexer(stripnl=False, ensurenl=False),
            HtmlFormatter(cssclass="highlight", nowrap=False),
        )
        if not source.endswith("\n"):
            highlighted = highlighted.replace("\n</pre></div>\n", "</pre></div>\n")

        if context is not None:
            context.has_live_code = True
        if interactive and context is not None:
            context.has_interactive = True

        payload = encode_live_projection(path, title, static=authored_static)
        identifier = f"citry-live-code-{self.id}"
        return {
            "projection_start": Markup(f"<!-- docs-live-code:{payload}:start -->"),  # noqa: S704
            "projection_end": Markup(f"<!-- docs-live-code:{payload}:end -->"),  # noqa: S704
            "root_class": ("citry-live-code citry-live-code--full-height" if full_height else "citry-live-code"),
            "root_attrs": {"data-citry-live-code": True} if interactive else {},
            "title": title,
            "identifier": identifier,
            "interactive": interactive,
            "show_playground_link": not interactive and not authored_static,
            "highlighted": Markup(highlighted),  # noqa: S704 - trusted Pygments output
        }


__all__ = ["LiveCode"]
