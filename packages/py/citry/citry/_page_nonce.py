"""
Read the CSP nonce a page sends with its request, so the HTML Citry sends back carries it.

Under a nonce-based CSP the browser runtime starts a Vue fragment only when
the fragment carries the nonce of the page it lands in. The server that
answers an htmx or ``fetch()`` request cannot tell which page sent it, and
with several tabs open each page has its own nonce. So the page says: the
runtime gives its nonce to page code through ``Citry.pageNonce()``, page code
sends it in the ``X-Citry-Page-Nonce`` request header, and the server writes
that value into its answer: the host through ``page_nonce_from_headers()``,
and an Events ``Render`` on its own when the app set no ``_csp_nonce``.

A request can say anything in a header, but the value only ever reaches the
answer to that same request, so a made-up value changes only what its sender
gets back. The one way it could reach someone else is a shared cache, so an
answer to a request that sent the header gets ``Cache-Control: no-store``,
and every answer that could carry the nonce lists the header in ``Vary``.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = ["PAGE_NONCE_HEADER", "page_nonce_from_headers"]

PAGE_NONCE_HEADER = "X-Citry-Page-Nonce"
"""
The request header that carries the CSP nonce of the page that sent the request.

Experimental: the name and the rules for reading it may change in a 1.x
minor release.
"""

# The CSP Level 3 base64-value syntax. `serialize(csp_nonce=)` refuses a value
# of another shape; here such a value (a comma from a repeated header, a quote,
# a space) is ignored instead: it comes from the request, and the answer
# without a nonce is what the page would get without the header.
CSP_NONCE_SHAPE = re.compile(r"[A-Za-z0-9+/_-]+={0,2}")
# Real nonces are 16 to 64 characters. The cap keeps a forged header from
# making every tag of the answer much larger.
_MAX_NONCE_LENGTH = 256


def page_nonce_from_headers(headers: Mapping[str, str]) -> str | None:
    """
    Return the CSP nonce a request says its page has, or `None`.

    Under a nonce-based Content Security Policy, the browser starts a Vue
    fragment only when it carries the nonce of the page it lands in. When
    page code loads a fragment with its own request (htmx, `fetch()`), it
    sends that nonce in the `X-Citry-Page-Nonce` header, from
    `Citry.pageNonce()` in the browser. Pass the result as `csp_nonce` when
    you serialize the fragment, so it carries the nonce of the tab that
    asked for it.

    The answer depends on the header, so list `X-Citry-Page-Nonce` in its
    `Vary` header, and when the result is not `None` also send
    `Cache-Control: no-store`. A shared cache could otherwise give one
    visitor's nonce to another.

    Experimental:
        The header name and this function may change in a 1.x minor
        release without a deprecation period.

    Args:
        headers: The request headers, such as Django's `request.headers`.
            Header names match without regard to case.

    Returns:
        The header's value when it has the shape of a CSP nonce (letters,
        digits, `+`, `/`, `-`, `_`, and at most two trailing `=`, at most
        256 characters); `None` when the header is missing or has another
        shape.

    Example:
        ```python
        nonce = page_nonce_from_headers(request.headers)
        html = card.render().serialize(
            deps_strategy="fragment",
            csp_nonce=nonce,
        )
        ```

    """
    value = headers.get(PAGE_NONCE_HEADER)
    if value is None:
        # A plain dict keeps the case the host wrote, so look again ignoring it.
        wanted = PAGE_NONCE_HEADER.lower()
        value = next((item for name, item in headers.items() if name.lower() == wanted), None)
    if type(value) is not str or len(value) > _MAX_NONCE_LENGTH or CSP_NONCE_SHAPE.fullmatch(value) is None:
        return None
    return value
