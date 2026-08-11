"""Render the versioned Citry diagnostic catalog into public documentation."""

from __future__ import annotations

import json
from typing import Any

from markupsafe import Markup, escape

from citry import Component
from docs_site._internal.project import current_docs_project

_SURFACE_LABELS = {
    "parser": "template parser APIs",
    "formatter": "<code>citry format</code>",
    "check": "<code>citry check</code>",
    "lsp": "<code>citry-lsp</code>",
    "vscode": "the Citry VS Code extension",
}
_MESSAGE_VARIANT_LABELS = {
    "closed": "Closed template data",
    "allow-extra": "Template data allows extra names",
    "unknown": "Template data could not be inspected",
    "inline": "Inline template",
    "file": "Template file",
}


class DiagnosticCatalog(Component):
    """``<c-diagnostic-catalog />`` renders every catalog entry and provider prefix."""

    transparent = True

    class Kwargs:
        pass

    class Slots:
        pass

    template = "{{ rendered }}"

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        catalog_path = current_docs_project().runtime.repo_root / "packages/protocol/diagnostics/v1/catalog.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        blocks = [_diagnostic_block(item) for item in catalog["diagnostics"]]
        external = [_external_prefix_block(item) for item in catalog["externalCodePrefixes"]]
        rendered = "\n".join(
            [
                '<div class="diagnostic-catalog">',
                *blocks,
                '<h2 id="provider-owned-diagnostics" class="toc-heading">Provider-owned diagnostics</h2>',
                *external,
                "</div>",
            ]
        )
        # Every value interpolated into the HTML was escaped below. Markup keeps
        # the catalog cards as HTML for the Markdown pass rather than prose text.
        return {"rendered": Markup(rendered)}  # noqa: S704


def _diagnostic_block(item: dict[str, Any]) -> str:
    code = escape(item["code"])
    title = escape(item["title"])
    summary = escape(item["summary"])
    severity = escape(item["defaultSeverity"])
    reported_by = ", ".join(_SURFACE_LABELS[surface] for surface in item["surfaces"])
    when = escape(item["when"])
    configurable = " The application can configure this severity." if item.get("configurableSeverity") else ""
    return (
        f'<section class="diagnostic-reference" aria-labelledby="{code}">'
        f'<h2 id="{code}" class="toc-heading"><code>{code}</code></h2>'
        f"<p><strong>{title}.</strong> {summary}</p>"
        f"<p><strong>When this appears:</strong> {when}</p>"
        f"<p><strong>Default severity:</strong> <code>{severity}</code>.{configurable}</p>"
        f"{_messages_block(item['messages'])}"
        f"{_examples_block(item.get('examples', []))}"
        f"<p><strong>Reported by:</strong> {reported_by}.</p>"
        "</section>"
    )


def _messages_block(messages: dict[str, str]) -> str:
    """Show stable user-facing messages, but not provider detail placeholders."""
    visible = [(variant, template) for variant, template in messages.items() if template != "{detail}"]
    if not visible:
        return ""
    if len(visible) == 1 and visible[0][0] == "default":
        return "<p><strong>Message:</strong></p>" + _message_code_block(visible[0][1])
    items = "".join(
        '<li class="diagnostic-message">'
        f"<p><strong>{escape(_MESSAGE_VARIANT_LABELS.get(variant, variant))}:</strong></p>"
        f"{_message_code_block(template)}"
        "</li>"
        for variant, template in visible
    )
    return f'<p><strong>Messages:</strong></p><ul class="diagnostic-messages">{items}</ul>'


def _message_code_block(message: str) -> str:
    """Give long diagnostic text a scrollable block instead of inline no-wrap styling."""
    return f'<div class="highlight"><pre><code>{escape(message)}</code></pre></div>'


def _examples_block(examples: list[dict[str, str]]) -> str:
    """Render optional catalog examples without treating authored code as HTML."""
    blocks: list[str] = []
    for example in examples:
        title = escape(example["title"])
        language = escape(example["language"])
        source = escape(example["source"])
        description = example.get("description")
        description_html = f"<p>{escape(description)}</p>" if description else ""
        blocks.append(
            '<div class="diagnostic-example">'
            f"<p><strong>Example: {title}</strong></p>"
            f"{description_html}"
            '<div class="highlight">'
            f'<pre><code class="language-{language}">{source}</code></pre>'
            "</div>"
            "</div>"
        )
    return "".join(blocks)


def _external_prefix_block(item: dict[str, Any]) -> str:
    prefix = escape(item["prefix"])
    provider = escape(item["provider"])
    summary = escape(item["summary"])
    return (
        '<section class="diagnostic-reference">'
        f"<h3><code>{prefix}*</code></h3>"
        f"<p><strong>Provider:</strong> {provider}. {summary}</p>"
        "</section>"
    )
