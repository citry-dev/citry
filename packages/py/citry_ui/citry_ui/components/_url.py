"""
Shared URL scheme check for Citry UI inputs that become a link or an image source.

A Citry UI kwarg such as ``CButton.href`` or ``CAvatar.src`` often holds a URL
that comes from the app's records or from a request. Escaping keeps that value
from breaking out of its attribute, but the browser still acts on the scheme:
a ``javascript:`` link runs script when clicked. So every such kwarg goes
through one function here, which accepts a relative URL or an allowed scheme
and raises ``ValueError`` for anything else. The check reads the URL as the
browser will: for a ``Markup`` value, that is the text after Citry decodes
its character references, so ``Markup("java&#115;cript:x")`` is refused.

The scheme itself is read by ``citry._urls``, the reader every server-side
URL check in Citry shares. The CAvatar and CImage browser code repeats the
image rule for client props; ``tests/test_url_schemes.py`` runs both against
the same cases and against the shared table of URLs in
``crates/citry_html_transform/tests/fixtures/url_schemes.json``.
"""

from __future__ import annotations

import html

from citry._urls import url_scheme, url_scheme_and_rest
from citry.util.html import escape_attribute_value

# The data: URL processor strips this whitespace around the media type.
_ASCII_WHITESPACE = " \t\n\f\r"

# Links and form actions: the schemes a page commonly links to and that never
# run code in the page. Other schemes (javascript:, vbscript:, data:, file:,
# app-specific ones) are refused; write such a link as a plain <a> in the
# template instead.
LINK_SCHEMES = ("http", "https", "mailto", "sms", "tel")
# Image sources: an <img> never runs script, so blob: and data: image URLs
# stay usable. A data: URL must still name an image media type.
IMAGE_SCHEMES = ("http", "https", "blob", "data")

_LINK_RULE = "a relative URL or an http:, https:, mailto:, sms:, or tel: URL"
_IMAGE_RULE = "a relative URL or an http:, https:, blob:, or data:image/ URL"


def attribute_text(value: object) -> str:
    """
    Return the attribute value a browser reads once Citry writes ``value`` into an attribute.

    A ``Markup`` value (any object with ``__html__``) holds HTML, so Citry
    decodes its character references before it writes the attribute; any
    other value is written as its plain text.
    """
    # Run Citry's own attribute writer and undo only its escaping, so this
    # check cannot drift from what the page gets. Every "&" in the writer's
    # output starts one of its own escapes, so unescaping it gives back the
    # text the browser reads. The browser also turns NUL into U+FFFD and CR
    # into LF; neither can make a refused scheme read as an allowed one.
    return html.unescape(escape_attribute_value(value))


def check_link_url(label: str, url: str) -> str:
    """
    Return ``url`` unchanged if it is safe to use as a link or form action.

    Args:
        label: The component and input name for the error, such as ``"CButton href"``.
        url: The string the component will write into the attribute. A
            ``Markup`` value is read after decoding its character references,
            as Citry writes it.

    Raises:
        ValueError: If the URL has a scheme other than http, https, mailto,
            sms, or tel.

    """
    scheme = url_scheme(attribute_text(url))
    if scheme is not None and scheme not in LINK_SCHEMES:
        msg = f"{label} must be {_LINK_RULE}."
        raise ValueError(msg)
    return url


def is_image_url_allowed(url: str) -> bool:
    """Return whether ``url`` is a relative URL or an allowed image source, read as Citry writes it."""
    read = url_scheme_and_rest(attribute_text(url))
    if read is None:
        # No scheme: a relative URL loads from the page's own site.
        return True
    scheme, rest = read
    if scheme == "data":
        # The browser reads the media type from the text before the first comma;
        # only one that starts with image/ may load.
        return rest.lstrip(_ASCII_WHITESPACE)[:6].lower() == "image/"
    return scheme in IMAGE_SCHEMES


def check_image_url(label: str, url: str) -> str:
    """
    Return ``url`` unchanged if it is safe to use as an image source.

    Args:
        label: The component and input name for the error, such as ``"CAvatar src"``.
        url: The string the component will write into ``src`` or a ``srcset``
            candidate. A ``Markup`` value is read after decoding its character
            references, as Citry writes it.

    Raises:
        ValueError: If the URL has a scheme other than http, https, or blob, or is
            a data: URL whose media type is not an image.

    """
    if not is_image_url_allowed(url):
        msg = f"{label} must be {_IMAGE_RULE}."
        raise ValueError(msg)
    return url
