"""Real-browser semantic probes for the structural template formatter."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry_core.template_formatter import format_template

pytestmark = pytest.mark.e2e


def _browser_source(source: str) -> str:
    return source.replace("{# fmt: off #}", "").replace("{# fmt: on #}", "")


def _snapshot(page: Any, source: str) -> dict[str, object]:
    page.set_content(_browser_source(source))
    return page.evaluate(
        """() => ({
          innerText: document.body.innerText,
          elements: [...document.body.querySelectorAll('*')].map((element) => element.localName),
          sensitiveText: [...document.body.querySelectorAll(
            'p, span, strong, x-panel, c-card, c-raw, pre, textarea'
          )].map((element) => ({
            tag: element.localName,
            textContent: element.textContent,
            directTextNodes: [...element.childNodes]
              .filter((node) => node.nodeType === Node.TEXT_NODE)
              .map((node) => node.data),
          })),
          pre: [...document.querySelectorAll('pre')].map((element) => element.textContent),
          textarea: [...document.querySelectorAll('textarea')].map((element) => element.value),
        })"""
    )


@pytest.mark.parametrize(
    "source",
    [
        "<p><span>A</span><span>B</span></p>",
        "<p><span>A</span> <span>B</span></p>",
        "<main><section>A</section><footer>B</footer></main>",
        "<main><x-panel>A</x-panel><section>B</section></main>",
        "<main><c-card>A</c-card><section>B</section></main>",
        "<main><pre>  first\n second</pre><section>B</section></main>",
        "<main><textarea>  first\n second</textarea><section>B</section></main>",
        "<main><c-raw>  A <div>B</div></c-raw><section>C</section></main>",
        "<main><section>A</section><!-- note --><footer>B</footer></main>",
        ("<style>div { display: inline; }</style><main>{# fmt: off #}<div>A</div><div>B</div>{# fmt: on #}</main>"),
    ],
)
def test_structural_formatting_preserves_browser_observables(page: Any, source: str) -> None:
    formatted = format_template(source)

    assert _snapshot(page, formatted) == _snapshot(page, source)


def test_inline_no_gap_and_one_space_remain_distinct_text_nodes(page: Any) -> None:
    compact = "<p><span>A</span><span>B</span></p>"
    spaced = "<p><span>A</span> <span>B</span></p>"

    page.set_content(format_template(compact))
    compact_text = page.locator("p").evaluate("element => element.textContent")
    compact_nodes = page.locator("p").evaluate("element => [...element.childNodes].map(node => node.textContent)")
    page.set_content(format_template(spaced))
    spaced_text = page.locator("p").evaluate("element => element.textContent")
    spaced_nodes = page.locator("p").evaluate("element => [...element.childNodes].map(node => node.textContent)")

    assert compact_text == "AB"
    assert spaced_text == "A B"
    assert compact_nodes == ["A", "B"]
    assert spaced_nodes == ["A", " ", "B"]
