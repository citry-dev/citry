from __future__ import annotations

from docs_site._internal.components.diagnostic_catalog import _diagnostic_block, _messages_block
from docs_site._internal.pipeline import render_page


def test_diagnostic_catalog_component_populates_toc_and_provider_prefix() -> None:
    result = render_page(
        "---\ntitle: Diagnostics\ndescription: Diagnostic reference.\n---\n\n<c-diagnostic-catalog />\n",
    )
    rendered = result.html

    assert 'id="citry.template.unknown-variable"' in rendered
    assert "citry.python.*" in rendered
    assert "Provider:</strong> ty" in rendered
    assert 'class="djc-toc"' in rendered
    assert 'href="#citry.template.unknown-variable"' in rendered
    assert any(item["id"] == "citry.template.unknown-variable" for item in result.toc_tokens)
    assert any(item["id"] == "provider-owned-diagnostics" for item in result.toc_tokens)


def test_diagnostic_block_explains_reporting_conditions_without_internal_placeholders() -> None:
    rendered = _diagnostic_block(
        {
            "code": "citry.example.failure",
            "title": "Example failure",
            "summary": "Something failed.",
            "when": "A focused test triggers the condition.",
            "defaultSeverity": "warning",
            "configurableSeverity": True,
            "surfaces": ["check", "vscode"],
            "messages": {"default": "{detail}"},
            "examples": [
                {
                    "title": "Unsafe-looking source stays escaped",
                    "language": "citry-html",
                    "source": "<c-missing />",
                }
            ],
        }
    )

    assert "Default severity:</strong> <code>warning</code>" in rendered
    assert "Reported by:</strong> <code>citry check</code>, the Citry VS Code extension" in rendered
    assert "When this appears:</strong> A focused test triggers the condition." in rendered
    assert "default" not in rendered
    assert "{detail}" not in rendered
    assert "&lt;c-missing /&gt;" in rendered


def test_diagnostic_messages_render_as_code_blocks() -> None:
    rendered = _messages_block(
        {
            "closed": "A long diagnostic message that should not use inline code.",
            "default": "{detail}",
        }
    )

    assert '<div class="highlight"><pre><code>' in rendered
    assert "A long diagnostic message that should not use inline code.</code></pre></div>" in rendered
    assert "<p><code>" not in rendered
    assert "{detail}" not in rendered
