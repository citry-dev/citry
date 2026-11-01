"""
Shared URL scheme check for Citry UI inputs that become a link or an image source.

A Citry UI kwarg such as ``CButton.href`` or ``CAvatar.src`` often holds a URL
that comes from the app's records or from a request. Escaping keeps that value
from breaking out of its attribute, but the browser still acts on the scheme:
a ``javascript:`` link runs script when clicked. So every such kwarg goes
through one function here, which accepts a relative URL or an allowed scheme
and raises ``ValueError`` for anything else.

The CAvatar and CImage browser code repeats the image rule for client props;
``tests/test_url_schemes.py`` runs both against the same cases.
"""

from __future__ import annotations

import string

# The WHATWG URL parser strips these from both ends before it reads the scheme.
_C0_CONTROL_OR_SPACE = "".join(chr(code) for code in range(0x21))
# It removes tab, LF, and CR anywhere, so "java\tscript:" reads as "javascript:".
_ASCII_TAB_OR_NEWLINE = str.maketrans("", "", "\t\n\r")
_SCHEME_START_CHARS = frozenset(string.ascii_letters)
_SCHEME_CHARS = frozenset(string.ascii_letters + string.digits + "+-.")
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


def _read_scheme(url: str) -> tuple[str | None, str]:
    """
    Return the lowercase scheme a browser reads from ``url``, and the text after its colon.

    The scheme is ``None`` for a relative URL such as ``/orders``, ``?page=2``,
    ``#top``, or ``//example.com/x``. This follows the first steps of the URL
    parser browsers use (the WHATWG URL standard), so the answer matches what
    the browser will navigate to or load.
    """
    text = url.strip(_C0_CONTROL_OR_SPACE).translate(_ASCII_TAB_OR_NEWLINE)
    colon = text.find(":")
    # A scheme starts with a letter and runs up to the first colon. Any other
    # character before the colon (such as "/", "?", or "#") makes it relative.
    if colon < 1 or text[0] not in _SCHEME_START_CHARS:
        return None, text
    scheme = text[:colon]
    if not all(char in _SCHEME_CHARS for char in scheme):
        return None, text
    return scheme.lower(), text[colon + 1 :]


def check_link_url(label: str, url: str) -> str:
    """
    Return ``url`` unchanged if it is safe to use as a link or form action.

    Args:
        label: The component and input name for the error, such as ``"CButton href"``.
        url: The plain string the component will write into the attribute.

    Raises:
        ValueError: If the URL has a scheme other than http, https, mailto,
            sms, or tel.

    """
    scheme, _ = _read_scheme(url)
    if scheme is not None and scheme not in LINK_SCHEMES:
        msg = f"{label} must be {_LINK_RULE}."
        raise ValueError(msg)
    return url


def is_image_url_allowed(url: str) -> bool:
    """Return whether ``url`` is a relative URL or an allowed image source."""
    scheme, rest = _read_scheme(url)
    if scheme is None:
        return True
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
        url: The plain string the component will write into ``src`` or a ``srcset`` candidate.

    Raises:
        ValueError: If the URL has a scheme other than http, https, or blob, or is
            a data: URL whose media type is not an image.

    """
    if not is_image_url_allowed(url):
        msg = f"{label} must be {_IMAGE_RULE}."
        raise ValueError(msg)
    return url
